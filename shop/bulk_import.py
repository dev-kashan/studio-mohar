"""Bulk import of Products (custom + shop) and Shop Designs from a ZIP or CSV file.

The client fills two CSV files (the demo ZIP from the admin shows the format):
  products.csv      -> Product + Product Variations (colour x size) + Colour photos
  shop_designs.csv  -> Shop Design + its colours, gallery, text fields, occasions
Images go in an images/ folder inside the ZIP (CSV cell = file name) or as a full URL.

Everything runs inside one database transaction: if any row has an error,
nothing is saved. "Check" mode (dry_run) always rolls back and never writes files.
"""
import csv
import io
import os
import re
import urllib.request
import zipfile
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils.text import slugify

from .models import (
    Category,
    Color,
    Occasion,
    Product,
    ProductAttribute,
    ProductColor,
    ProductPhoto,
    ShopDesign,
    ShopDesignColor,
    ShopDesignImage,
    ShopDesignTextField,
    Size,
)

# ---------------- Column definitions (also used for the demo ZIP + README) ----------------
# (column, required, help text)
PRODUCT_COLUMNS = [
    ('product_name', 'yes', 'Product name. Every row with the same name (or slug) is ONE product - one row per colour + size.'),
    ('product_type', 'yes', '"custom" (customer designs it in the Design Lab) or "shop" (blank garment used as base for Shop Designs).'),
    ('slug', '', 'URL of the product, e.g. premium-tee. Empty = made from the name.'),
    ('category', '', 'Category name or slug - must already exist on the site (see list below).'),
    ('short_description', '', 'Short text.'),
    ('description', '', 'Full description (plain text or HTML).'),
    ('fabric_composition', '', 'e.g. 100% ringspun cotton'),
    ('softness', '', 'e.g. Soft'),
    ('fabric_weight', '', 'e.g. 180 GSM'),
    ('fit', '', 'e.g. Regular'),
    ('construction_quality', '', 'e.g. Premium'),
    ('durability', '', 'e.g. High'),
    ('promo_percent', '', 'Discount % for colours marked as promo (0 = none).'),
    ('display_order', '', 'Lower number shows first.'),
    ('live', '', 'yes / no (default no).'),
    ('meta_title', '', 'SEO title.'),
    ('meta_description', '', 'SEO description.'),
    ('size_chart_image', '', 'Size chart picture (file name in images/ or a full URL).'),
    ('extra_photos', '', 'Extra gallery photos separated by | e.g. model.jpg | fabric.jpg (replaces old extra photos).'),
    ('color', 'yes', 'Colour name - must exist on the site, OR fill color_code too and it will be created.'),
    ('color_code', '', 'Hex code for a NEW colour, e.g. #1f3a5f.'),
    ('size', 'yes', 'Size name - must exist on the site (see list below).'),
    ('price', 'yes', 'Price of this colour + size, e.g. 12.99'),
    ('discount_price', '', 'Sale price (lower than price). Empty = no discount.'),
    ('stock', '', 'Pieces in stock (default 0).'),
    ('color_is_promo', '', 'yes / no - show this colour under "Promo colours".'),
    ('front_image', '', 'Photo of this colour - front. Only needed on ONE row per colour.'),
    ('back_image', '', 'Photo of this colour - back.'),
    ('left_image', '', 'Photo of this colour - left sleeve.'),
    ('right_image', '', 'Photo of this colour - right sleeve.'),
]

DESIGN_COLUMNS = [
    ('design_name', 'yes', 'Design name. Every row with the same name (or slug) is ONE design - one row per colour.'),
    ('slug', '', 'URL of the design page, e.g. bride-crew-tee. Empty = made from the name.'),
    ('base_product', 'yes', 'Name or slug of a product with product_type = shop (can be in products.csv of the same upload).'),
    ('occasions', '', 'Occasion names or slugs separated by | (see list below).'),
    ('price', 'yes', 'Price per piece, e.g. 29.99'),
    ('discount_price', '', 'Sale price (lower than price). Empty = no discount.'),
    ('short_description', '', 'One line under the title.'),
    ('description', '', 'Full description (plain text or HTML).'),
    ('is_best_seller', '', 'yes / no'),
    ('live', '', 'yes / no (default no).'),
    ('order', '', 'Lower number shows first.'),
    ('is_personalizable', '', 'yes / no'),
    ('allow_image_upload', '', 'yes / no - customer can upload a photo.'),
    ('allow_text', '', 'yes / no - customer can type text.'),
    ('text_fields', '', 'Text boxes: Label:max letters:required separated by |  e.g. Name on front:12:required | Number:3'),
    ('meta_title', '', 'SEO title.'),
    ('meta_description', '', 'SEO description.'),
    ('gallery_images', '', 'Extra photos/GIFs separated by | (replaces old gallery).'),
    ('color', 'yes', 'Colour name - must be a colour of the base product.'),
    ('hero_image', 'yes', 'Main photo of the design in this colour (file name in images/ or a full URL).'),
    ('back_image', '', 'Back photo (only if printed on the back).'),
    ('is_default', '', 'yes on ONE colour = shown first.'),
]

IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif', '.bmp')
MAX_DOWNLOAD = 20 * 1024 * 1024  # 20 MB per image URL
TRUE_WORDS = {'yes', 'y', 'true', '1', 'on', 'x'}
FALSE_WORDS = {'no', 'n', 'false', '0', 'off', ''}


class ImportReport:
    def __init__(self):
        self.errors = []      # (file, row, message)
        self.warnings = []
        self.lines = []       # human readable summary lines
        self.counts = OrderedDict((k, 0) for k in (
            'products_created', 'products_updated', 'variations_created', 'variations_updated',
            'colour_photos', 'colours_created', 'designs_created', 'designs_updated', 'design_colours', 'images_saved'))
        self.items = []       # (kind, name, admin url or None, created?)

    @property
    def ok(self):
        return not self.errors

    @property
    def count_list(self):
        """[(label, number)] for the admin page, only numbers above 0."""
        return [(k.replace('_', ' '), v) for k, v in self.counts.items() if v]


class BulkImporter:
    def __init__(self, path, dry_run=True):
        self.path = path
        self.dry_run = dry_run
        self.report = ImportReport()
        self.zip = None
        self.images = {}          # lower basename -> zip member name
        self.saved_files = []     # storage names written in this run (deleted on rollback)
        self.file_cache = {}      # (source, upload_to) -> storage name
        self.bytes_cache = {}     # url -> bytes

    # ---------------- helpers ----------------
    def err(self, file, row, msg):
        self.report.errors.append((file, row, msg))

    def warn(self, file, row, msg):
        self.report.warnings.append((file, row, msg))

    @staticmethod
    def to_bool(value, default=False):
        v = (value or '').strip().lower()
        if v in TRUE_WORDS:
            return True
        if v in FALSE_WORDS:
            return default if v == '' else False
        return None  # invalid

    @staticmethod
    def to_dec(value):
        v = (value or '').strip().replace('$', '').replace(',', '').replace('CAD', '').strip()
        if not v:
            return None
        try:
            return Decimal(v).quantize(Decimal('0.01'))
        except InvalidOperation:
            raise ValueError(f'"{value}" is not a number')

    @staticmethod
    def to_int(value, default=0):
        v = (value or '').strip()
        if not v:
            return default
        try:
            return int(float(v))
        except ValueError:
            raise ValueError(f'"{value}" is not a whole number')

    @staticmethod
    def split_list(value):
        return [p.strip() for p in re.split(r'[|\n]', value or '') if p.strip()]

    # ---------------- reading the upload ----------------
    def read_csv(self, raw):
        for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        rows = []
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        for i, row in enumerate(reader, start=2):  # row 1 = header
            clean = {(k or '').strip().lower().replace(' ', '_'): (v or '').strip() for k, v in row.items() if k}
            if any(clean.values()):
                rows.append((i, clean))
        return rows

    def load(self):
        """Returns (product_rows, design_rows) or None on a fatal error."""
        products, designs = None, None
        name = self.path.lower()
        if name.endswith('.csv'):
            with open(self.path, 'rb') as f:
                rows = self.read_csv(f.read())
            headers = set(rows[0][1].keys()) if rows else set()
            if 'design_name' in headers:
                designs = rows
            else:
                products = rows
            return products or [], designs or []
        try:
            self.zip = zipfile.ZipFile(self.path)
        except zipfile.BadZipFile:
            self.err('upload', '', 'This is not a valid ZIP or CSV file.')
            return None
        for member in self.zip.namelist():
            base = os.path.basename(member)
            if not base or member.startswith('__MACOSX') or base.startswith('.'):
                continue
            low = base.lower()
            if low.endswith('.csv'):
                rows = self.read_csv(self.zip.read(member))
                headers = set(rows[0][1].keys()) if rows else set()
                if 'design_name' in headers:
                    designs = (designs or []) + rows
                elif 'product_name' in headers:
                    products = (products or []) + rows
                elif rows:
                    self.warn(base, '', 'Skipped: no "product_name" or "design_name" column.')
            elif low.endswith(IMAGE_EXTS):
                self.images[low] = member
        if products is None and designs is None:
            self.err('upload', '', 'No products.csv or shop_designs.csv found inside the ZIP.')
            return None
        return products or [], designs or []

    # ---------------- images ----------------
    def resolve_file(self, value, upload_to, file, row, image_only=True):
        """Return a storage name for the CSV cell (or None). Writes the file unless dry run."""
        value = (value or '').strip()
        if not value:
            return None
        key = (value, upload_to)
        if key in self.file_cache:
            return self.file_cache[key]

        data, base = None, None
        if value.lower().startswith(('http://', 'https://')):
            parsed = urlparse(value)
            path = unquote(parsed.path)
            # A link to this site's own /media/... -> reuse the file, no copy
            if path.startswith(settings.MEDIA_URL):
                rel = path[len(settings.MEDIA_URL):]
                if default_storage.exists(rel):
                    self.file_cache[key] = rel
                    return rel
            base = os.path.basename(path) or 'image.jpg'
            try:
                if value not in self.bytes_cache:
                    req = urllib.request.Request(value, headers={'User-Agent': 'Mozilla/5.0 (bulk-import)'})
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        self.bytes_cache[value] = resp.read(MAX_DOWNLOAD + 1)
                data = self.bytes_cache[value]
            except Exception as e:  # noqa: BLE001 - any network problem is a row error
                self.err(file, row, f'Could not download image "{value}" ({e}).')
                return None
            if len(data) > MAX_DOWNLOAD:
                self.err(file, row, f'Image "{value}" is bigger than 20 MB.')
                return None
        else:
            base = os.path.basename(value.replace('\\', '/'))
            member = self.images.get(base.lower())
            if member:
                data = self.zip.read(member)
            elif default_storage.exists(value.lstrip('/')):
                # already on the server, e.g. shop/images/x.jpg
                self.file_cache[key] = value.lstrip('/')
                return self.file_cache[key]
            else:
                where = 'in the images/ folder of the ZIP' if self.zip else '(upload a ZIP with an images/ folder, or use a full URL)'
                self.err(file, row, f'Image "{value}" not found {where}.')
                return None

        if image_only and not base.lower().endswith(('.svg',)):
            try:
                from PIL import Image
                Image.open(io.BytesIO(data)).verify()
            except Exception:  # noqa: BLE001
                self.err(file, row, f'"{value}" is not a valid image file.')
                return None

        if self.dry_run:
            name = f'{upload_to}/{base}'
        else:
            name = default_storage.save(f'{upload_to}/{base}', ContentFile(data))
            self.saved_files.append(name)
            self.report.counts['images_saved'] += 1
        self.file_cache[key] = name
        return name

    @staticmethod
    def upload_to(model, field):
        return str(model._meta.get_field(field).upload_to).rstrip('/')

    # ---------------- lookups ----------------
    def find_category(self, value):
        return (Category.objects.filter(slug__iexact=value).first()
                or Category.objects.filter(category_name__iexact=value).first()
                or Category.objects.filter(category__iexact=value).first())

    def find_color(self, name, code, file, row, allow_create=True):
        color = Color.objects.filter(color_name__iexact=name).first()
        if color:
            return color
        if allow_create and code:
            if not re.fullmatch(r'#?[0-9a-fA-F]{6}', code):
                self.err(file, row, f'color_code "{code}" must look like #1f3a5f.')
                return None
            color = Color.objects.create(color_name=name, color_code='#' + code.lstrip('#'))
            self.report.counts['colours_created'] += 1
            self.warn(file, row, f'New colour "{name}" ({color.color_code}) will be created - set its colour group in 08. Colors later.')
            return color
        self.err(file, row, f'Colour "{name}" does not exist on the site. Use one from the list or add color_code to create it.')
        return None

    def find_size(self, name):
        return Size.objects.filter(Size_name__iexact=name).first()

    def find_base_product(self, value):
        qs = Product.objects.filter(product_type='shop')
        return qs.filter(Slug__iexact=value).first() or qs.filter(product_name__iexact=value).first()

    def find_occasion(self, value):
        return Occasion.objects.filter(slug__iexact=value).first() or Occasion.objects.filter(name__iexact=value).first()

    # ---------------- grouping ----------------
    @staticmethod
    def group(rows, name_col):
        groups = OrderedDict()
        for rownum, row in rows:
            key = slugify(row.get('slug') or row.get(name_col, ''))
            groups.setdefault(key, []).append((rownum, row))
        return groups

    @staticmethod
    def first(rows, col):
        return next((r.get(col, '') for _, r in rows if r.get(col, '')), '')

    # ---------------- products ----------------
    def import_products(self, rows):
        F = 'products.csv'
        for rownum, row in rows:
            for col in ('product_name', 'color', 'size', 'price'):
                if not row.get(col):
                    self.err(F, rownum, f'"{col}" is empty.')
        if self.report.errors:
            return
        for key, grows in self.group(rows, 'product_name').items():
            r0 = grows[0][0]
            name = self.first(grows, 'product_name')
            ptype = (self.first(grows, 'product_type') or 'custom').lower()
            if ptype not in ('custom', 'shop'):
                self.err(F, r0, f'product_type must be "custom" or "shop", not "{ptype}".')
                continue
            cat = None
            cat_value = self.first(grows, 'category')
            if cat_value:
                cat = self.find_category(cat_value)
                if not cat:
                    self.err(F, r0, f'Category "{cat_value}" does not exist on the site.')
                    continue
            elif ptype == 'custom':
                self.warn(F, r0, f'"{name}" has no category - it will not show on a style page.')

            product = Product.objects.filter(Slug=key, categories=cat).first()
            created = product is None
            if created:
                product = Product(Slug=key, user=None, categories=cat)

            def setv(attr, col, conv=None):
                v = self.first(grows, col)
                if v or created:
                    try:
                        setattr(product, attr, conv(v) if conv else v)
                    except ValueError as e:
                        self.err(F, r0, f'{col}: {e}')

            setv('product_name', 'product_name')
            product.product_type = ptype
            for attr, col in (('short_desc', 'short_description'), ('desc', 'description'),
                              ('fabric_composition', 'fabric_composition'), ('softness', 'softness'),
                              ('fabric_weight', 'fabric_weight'), ('fit', 'fit'),
                              ('construction_quality', 'construction_quality'), ('durability', 'durability'),
                              ('Meta_title', 'meta_title'), ('Meta_description', 'meta_description')):
                setv(attr, col)
            setv('promo_percent', 'promo_percent', lambda v: self.to_dec(v) or Decimal(0))
            setv('display_order', 'display_order', lambda v: self.to_int(v, 0))
            live = self.to_bool(self.first(grows, 'live'), default=product.live if not created else False)
            if live is None:
                self.err(F, r0, 'live must be yes or no.')
            else:
                product.live = live
            chart = self.resolve_file(self.first(grows, 'size_chart_image'), self.upload_to(Product, 'size_chart_img'), F, r0)
            if chart:
                product.size_chart_img = chart
            product.save()
            self.report.counts['products_created' if created else 'products_updated'] += 1
            self.report.items.append(('Product', product, created))

            # variations: one row = colour + size
            colors = OrderedDict()
            for rownum, row in grows:
                color = self.find_color(row['color'], row.get('color_code', ''), F, rownum)
                size = self.find_size(row['size'])
                if not size:
                    self.err(F, rownum, f'Size "{row["size"]}" does not exist on the site.')
                if not color or not size:
                    continue
                try:
                    price = self.to_dec(row['price'])
                    discount = self.to_dec(row.get('discount_price'))
                    stock = self.to_int(row.get('stock'), 0)
                except ValueError as e:
                    self.err(F, rownum, str(e))
                    continue
                if discount is not None and not (0 < discount <= price):
                    self.err(F, rownum, 'discount_price must be above 0 and not more than price.')
                    continue
                # The site uses discount_price as the selling price, so "no discount" = same as price
                discount = discount if discount is not None else price
                attr = ProductAttribute.objects.filter(product=product, color=color, size=size).first()
                if attr:
                    self.report.counts['variations_updated'] += 1
                else:
                    attr = ProductAttribute(product=product, color=color, size=size)
                    self.report.counts['variations_created'] += 1
                attr.price, attr.discount_price, attr.Availibility = price, discount, stock
                attr.save()
                colors.setdefault(color, []).append((rownum, row))

            # colour photos: one per colour, images taken from any row of that colour
            for idx, (color, crows) in enumerate(colors.items()):
                cr0 = crows[0][0]
                imgs = {f: self.resolve_file(self.first(crows, f), self.upload_to(ProductColor, f), F, cr0)
                        for f in ('front_image', 'back_image', 'left_image', 'right_image')}
                promo = self.to_bool(self.first(crows, 'color_is_promo'))
                if promo is None:
                    self.err(F, cr0, 'color_is_promo must be yes or no.')
                    continue
                pc = ProductColor.objects.filter(product=product, color=color).first()
                if not pc and not any(imgs.values()):
                    if ptype == 'custom':
                        self.warn(F, cr0, f'"{name}" - {color}: no front_image, so this colour shows without a photo.')
                    continue
                if not pc:
                    pc = ProductColor(product=product, color=color, order=idx)
                for f, v in imgs.items():
                    if v:
                        setattr(pc, f, v)
                if self.first(crows, 'color_is_promo'):
                    pc.is_promo = promo
                pc.save()
                self.report.counts['colour_photos'] += 1

            extra = self.split_list(self.first(grows, 'extra_photos'))
            if extra:
                product.photos.all().delete()
                for i, value in enumerate(extra):
                    img = self.resolve_file(value, self.upload_to(ProductPhoto, 'image'), F, r0)
                    if img:
                        ProductPhoto.objects.create(product=product, image=img, order=i)

    # ---------------- shop designs ----------------
    def import_designs(self, rows):
        F = 'shop_designs.csv'
        for rownum, row in rows:
            for col in ('design_name', 'base_product', 'color'):
                if not row.get(col):
                    self.err(F, rownum, f'"{col}" is empty.')
        if self.report.errors:
            return
        for key, grows in self.group(rows, 'design_name').items():
            r0 = grows[0][0]
            base_value = self.first(grows, 'base_product')
            base = self.find_base_product(base_value)
            if not base:
                hint = ' (it exists but its product_type is not "shop")' if Product.objects.filter(product_name__iexact=base_value).exists() else ''
                self.err(F, r0, f'Base product "{base_value}" not found{hint}.')
                continue
            design = ShopDesign.objects.filter(slug=key).first()
            created = design is None
            if created:
                design = ShopDesign(slug=key)
            design.base_product = base
            design.name = self.first(grows, 'design_name')
            try:
                price = self.to_dec(self.first(grows, 'price'))
                discount = self.to_dec(self.first(grows, 'discount_price'))
                order = self.first(grows, 'order')
                order = self.to_int(order) if order else None
            except ValueError as e:
                self.err(F, r0, str(e))
                continue
            if price is not None:
                design.price = price
            elif created:
                self.err(F, r0, '"price" is empty.')
                continue
            if discount is not None or created:
                design.discount_price = discount
            if design.discount_price is not None and not (0 < design.discount_price < design.price):
                self.err(F, r0, 'discount_price must be above 0 and lower than price (or empty).')
                continue
            if order is not None:
                design.order = order
            for attr, col in (('short_description', 'short_description'), ('description', 'description'),
                              ('meta_title', 'meta_title'), ('meta_description', 'meta_description')):
                v = self.first(grows, col)
                if v or created:
                    setattr(design, attr, v)
            bad = False
            for attr in ('is_best_seller', 'live', 'is_personalizable', 'allow_image_upload', 'allow_text'):
                v = self.first(grows, attr)
                if v or created:
                    b = self.to_bool(v)
                    if b is None:
                        self.err(F, r0, f'{attr} must be yes or no.')
                        bad = True
                    else:
                        setattr(design, attr, b)
            if bad:
                continue
            if design.is_personalizable and not (design.allow_image_upload or design.allow_text):
                self.err(F, r0, 'is_personalizable = yes needs allow_image_upload or allow_text = yes.')
                continue
            design.save()
            self.report.counts['designs_created' if created else 'designs_updated'] += 1
            self.report.items.append(('Shop design', design, created))

            occ_values = self.split_list(self.first(grows, 'occasions'))
            if occ_values:
                occs = []
                for v in occ_values:
                    o = self.find_occasion(v)
                    if o:
                        occs.append(o)
                    else:
                        self.err(F, r0, f'Occasion "{v}" does not exist on the site.')
                design.occasions.set(occs)

            allowed = set(ProductAttribute.objects.filter(product=base).values_list('color_id', flat=True))
            defaults = [rn for rn, r in grows if self.to_bool(r.get('is_default'))]
            if len(defaults) > 1:
                self.err(F, defaults[1], 'Only one colour can be is_default = yes.')
            for idx, (rownum, row) in enumerate(grows):
                color = self.find_color(row['color'], '', F, rownum, allow_create=False)
                if not color:
                    continue
                if color.id not in allowed:
                    self.err(F, rownum, f'"{color}" is not a colour of base product "{base}". Add it to the base product first.')
                    continue
                dc = ShopDesignColor.objects.filter(design=design, color=color).first()
                hero = self.resolve_file(row.get('hero_image'), self.upload_to(ShopDesignColor, 'hero_image'), F, rownum)
                back = self.resolve_file(row.get('back_image'), self.upload_to(ShopDesignColor, 'back_image'), F, rownum)
                if not dc and not hero:
                    if row.get('hero_image', '') == '':
                        self.err(F, rownum, f'hero_image is needed for new colour "{color}".')
                    continue
                if not dc:
                    dc = ShopDesignColor(design=design, color=color, order=idx)
                if hero:
                    dc.hero_image = hero
                if back:
                    dc.back_image = back
                if defaults:
                    dc.is_default = rownum == defaults[0]
                elif created:
                    dc.is_default = idx == 0
                dc.save()
                self.report.counts['design_colours'] += 1

            gallery = self.split_list(self.first(grows, 'gallery_images'))
            if gallery:
                design.gallery.all().delete()
                for i, value in enumerate(gallery):
                    img = self.resolve_file(value, self.upload_to(ShopDesignImage, 'image'), F, r0)
                    if img:
                        ShopDesignImage.objects.create(design=design, image=img, alt_text=design.name, order=i)

            text_spec = self.split_list(self.first(grows, 'text_fields'))
            if text_spec:
                design.text_fields.all().delete()
                for i, spec in enumerate(text_spec):
                    parts = [p.strip() for p in spec.split(':')]
                    label = parts[0]
                    try:
                        max_len = self.to_int(parts[1], 12) if len(parts) > 1 else 12
                    except ValueError as e:
                        self.err(F, r0, f'text_fields: {e}')
                        continue
                    required = len(parts) > 2 and parts[2].lower() in ('required', 'yes', 'true')
                    ShopDesignTextField.objects.create(design=design, label=label, max_length=max_len,
                                                       required=required, order=i)

    # ---------------- run ----------------
    def run(self):
        loaded = self.load()
        if loaded is None:
            return self.report
        products, designs = loaded
        if not products and not designs:
            self.err('upload', '', 'The CSV files are empty.')
            return self.report
        try:
            with transaction.atomic():
                if products:
                    self.import_products(products)
                if designs and not self.report.errors:
                    self.import_designs(designs)
                if self.dry_run or self.report.errors:
                    transaction.set_rollback(True)
        except Exception as e:  # noqa: BLE001 - show any unexpected problem instead of a 500 page
            self.err('upload', '', f'Unexpected error: {e}')
        if self.report.errors and not self.dry_run:
            for name in self.saved_files:  # nothing was saved -> remove the copied images too
                default_storage.delete(name)
            self.report.counts['images_saved'] = 0
        if self.zip:
            self.zip.close()
        return self.report


# ---------------- Demo ZIP for the client ----------------
def _demo_image(label, rgb):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (800, 800), rgb)
    d = ImageDraw.Draw(img)
    text_rgb = (30, 30, 30) if sum(rgb) > 380 else (240, 240, 240)
    d.rectangle((40, 40, 760, 760), outline=text_rgb, width=4)
    d.text((80, 380), label, fill=text_rgb)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=80)
    return buf.getvalue()


def _hex_to_rgb(code, fallback=(200, 200, 200)):
    code = (code or '').lstrip('#')
    try:
        return tuple(int(code[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return fallback


def build_template_zip():
    """Demo ZIP with real values from this site (categories, sizes, colours, occasions)."""
    cats = list(Category.objects.order_by('display_order', 'category_name'))
    sizes = list(Size.objects.filter(Available='Yes').order_by('order', 'id')) or list(Size.objects.all())
    colors = list(Color.objects.filter(Available='Yes').exclude(color_name='').exclude(color_name__isnull=True)) or list(Color.objects.all())
    occs = list(Occasion.objects.order_by('order', 'name'))
    shop_bases = list(Product.objects.filter(product_type='shop').order_by('product_name'))

    def pick_cat(pattern, fallback):
        for c in cats:
            if re.search(pattern, c.category_name.lower()):
                return c.category_name
        return fallback

    cat = pick_cat(r'\bt-?shirt|\btees?\b', cats[0].category_name if cats else '')
    cat2 = pick_cat(r'hood', cat)
    s = [x.Size_name for x in sizes[:3]] or ['Small', 'Medium', 'Large']
    c = colors[:2] or []
    c1, c2 = (c[0].color_name, c[1].color_name) if len(c) > 1 else ('White', 'Black')
    rgb1 = _hex_to_rgb(c[0].color_code) if c else (245, 245, 245)
    rgb2 = _hex_to_rgb(c[1].color_code) if len(c) > 1 else (30, 30, 30)
    occ = occs[0].name if occs else ''

    files = {}
    # products.csv: a custom product (2 colours x 3 sizes) and a shop base product
    prows = []
    for color, front, back in ((c1, 'premium-tee-1-front.jpg', 'premium-tee-1-back.jpg'),
                               (c2, 'premium-tee-2-front.jpg', '')):
        for i, size in enumerate(s):
            first_row = not prows
            prows.append({
                'product_name': 'Demo Premium Tee', 'product_type': 'custom', 'slug': 'demo-premium-tee', 'category': cat,
                'short_description': 'Soft everyday tee' if first_row else '',
                'description': 'Our softest tee, perfect for your own design.' if first_row else '',
                'fabric_composition': '100% ringspun cotton' if first_row else '', 'softness': 'Soft' if first_row else '',
                'fabric_weight': '180 GSM' if first_row else '', 'fit': 'Regular' if first_row else '',
                'live': 'no', 'size_chart_image': 'size-chart.jpg' if first_row else '',
                'color': color, 'size': size, 'price': '12.99' if i < 2 else '14.99',
                'discount_price': '10.99' if i < 2 else '', 'stock': '100',
                'front_image': front if i == 0 else '', 'back_image': back if i == 0 else '',
            })
    for color, front in ((c1, 'blank-hoodie-1-front.jpg'), (c2, 'blank-hoodie-2-front.jpg')):
        for i, size in enumerate(s[:2]):
            prows.append({'product_name': 'Demo Blank Hoodie', 'product_type': 'shop', 'slug': 'demo-blank-hoodie',
                          'category': cat2, 'live': 'no', 'color': color, 'size': size, 'price': '24.99',
                          'stock': '50', 'front_image': front if i == 0 else ''})
    files['products.csv'] = _csv_bytes([c[0] for c in PRODUCT_COLUMNS], prows)

    # shop_designs.csv: one design on the shop base product above, 2 colours
    drows = [
        {'design_name': 'Demo Bride Crew Hoodie', 'slug': 'demo-bride-crew-hoodie', 'base_product': 'demo-blank-hoodie',
         'occasions': occ, 'price': '39.99', 'discount_price': '34.99', 'short_description': 'Matching hoodies for the bride crew',
         'description': 'Printed with care. Add a name on the front.', 'is_best_seller': 'no', 'live': 'no', 'order': '1',
         'is_personalizable': 'yes', 'allow_image_upload': 'no', 'allow_text': 'yes',
         'text_fields': 'Name on front:12:required | Date:10', 'gallery_images': 'bride-crew-lifestyle.jpg',
         'color': c1, 'hero_image': 'bride-crew-1.jpg', 'is_default': 'yes'},
        {'design_name': 'Demo Bride Crew Hoodie', 'color': c2, 'base_product': 'demo-blank-hoodie', 'hero_image': 'bride-crew-2.jpg'},
    ]
    files['shop_designs.csv'] = _csv_bytes([c[0] for c in DESIGN_COLUMNS], drows)

    images = {
        'premium-tee-1-front.jpg': (f'Premium Tee - {c1} - front', rgb1), 'premium-tee-1-back.jpg': (f'Premium Tee - {c1} - back', rgb1),
        'premium-tee-2-front.jpg': (f'Premium Tee - {c2} - front', rgb2), 'size-chart.jpg': ('Size chart', (255, 255, 255)),
        'blank-hoodie-1-front.jpg': (f'Blank Hoodie - {c1}', rgb1), 'blank-hoodie-2-front.jpg': (f'Blank Hoodie - {c2}', rgb2),
        'bride-crew-1.jpg': (f'Bride Crew Hoodie - {c1}', rgb1), 'bride-crew-2.jpg': (f'Bride Crew Hoodie - {c2}', rgb2),
        'bride-crew-lifestyle.jpg': ('Lifestyle photo', (233, 199, 192)),
    }
    for fname, (label, rgb) in images.items():
        files[f'images/{fname}'] = _demo_image(label, rgb)

    files['README.txt'] = _readme(cats, sizes, colors, occs, shop_bases).encode('utf-8')

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(f'studio-mohar-bulk-upload/{name}', data)
    return buf.getvalue()


def _csv_bytes(columns, rows):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=columns, extrasaction='ignore')
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, '') for k in columns})
    return ('﻿' + out.getvalue()).encode('utf-8')  # BOM so Excel opens accents correctly


def _readme(cats, sizes, colors, occs, shop_bases):
    def cols(columns):
        return '\n'.join(f'  {name:<22}{"(required) " if req else ""}{help_}' for name, req, help_ in columns)

    def listing(items):
        return ', '.join(items) if items else '(none yet)'

    return f"""STUDIO MOHAR - BULK PRODUCT UPLOAD
==================================

What's in this ZIP
------------------
  products.csv       - products (custom + shop) with every colour + size
  shop_designs.csv   - ready-made shop designs (optional)
  images/            - all photos (JPG, PNG, WEBP or GIF)

Replace the sample rows with your own products, then zip the folder and upload it
in the admin (Products > Bulk import). Open the CSV files in Excel or
Google Sheets and save them as "CSV UTF-8". Do not rename or remove the header row.
Empty cells are fine for columns that are not required.

How the rows work
-----------------
products.csv: ONE ROW PER COLOUR + SIZE. A tee in 2 colours x 3 sizes = 6 rows.
  Repeat product_name (and product_type, category) on every row of that product.
  Product details (description, fabric...) only need to be filled on the first row.
  Colour photos only need to be filled on one row of each colour.

shop_designs.csv: ONE ROW PER COLOUR of the design.
  base_product must be a product with product_type = shop. It can be a product
  that is already on the site, or one that is in products.csv of the same ZIP.
  The design colours must be colours of that base product.

Images: write the file name (e.g. tee-black-front.jpg) and put that file in the
images/ folder. You can also paste a full link (https://...) instead.
Lists (occasions, extra photos, gallery, text fields) are separated with |

yes / no columns accept: yes, no, true, false, 1, 0.

If a product (same name/slug and category) or design (same slug) already exists,
it is UPDATED: new colours/sizes are added, existing ones get the new price/stock.

products.csv columns
--------------------
{cols(PRODUCT_COLUMNS)}

shop_designs.csv columns
------------------------
{cols(DESIGN_COLUMNS)}

Values that exist on the site right now
---------------------------------------
Categories:  {listing([c.category_name for c in cats])}
Sizes:       {listing([s.Size_name for s in sizes])}
Colours:     {listing([c.color_name for c in colors if c.color_name])}
Occasions:   {listing([o.name for o in occs])}
Shop base products (for base_product): {listing([p.product_name for p in shop_bases])}
"""
