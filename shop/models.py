
from django.db import models
from django.core.files.storage import default_storage
from django.contrib.auth.models import User, update_last_login
from django.db.models.signals import pre_save
from django.utils.html import mark_safe
from PIL import Image
from datetime import date, datetime
from django.utils.text import slugify
from colorfield.fields import ColorField

from django.template.loader import render_to_string
from newecom.settings import DEFAULT_FROM_EMAIL , EMAIL_HOST_USER 

from django.core.mail import send_mail 
from django.utils.html import strip_tags
from ckeditor.fields import RichTextField
import os
# from django.core.files.base import ContentFile
# from .utils.order_package import generate_order_zip


COLOR_CHOICES = (
    ('success', 'green'),
    ('primary', 'blue'),
    ('danger', 'red'),
    ('warning', 'yellow'),
    ('secondary', 'black'),
)

SHIP_TYPE = (
    ('standard', 'Standard'),
    ('rush', 'Rush'),
    ('waitsave', 'Wait & Save'),
)


YES_OR_NO = (
    ('Yes' , 'Yes'),
    ('No' , 'No')
)


COUPON_FORMULA = (
    ('percentage' , 'percentage'),
    ('value' , 'value')
)
COUPON_STATUS = (
    ('inactive', 'inactive'),
    ('active', 'active'),
)


class Size_Chart(models.Model):
    Title = models.CharField(max_length=100 , default='')
    chart_image = models.ImageField(upload_to="shop/images" ,  blank=True, null=True )
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.Title
    
    class Meta:
        verbose_name_plural = '17. Size Chart'

    
class CouponCode(models.Model):
    coupon_title = models.CharField(max_length=255,default='')
    coupon_code = models.CharField(max_length=255,default='')
    coupon_limit = models.CharField(max_length=255,default='')
    coupon_formula = models.CharField(max_length=50,default='percentage',choices=COUPON_FORMULA)
    coupon_minus_value = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50,default='inactive',choices=COUPON_STATUS)
    def __str__(self):
        return self.coupon_title

    class Meta:
        verbose_name_plural = '10. Coupon Code'




class StickerType(models.Model):
    type_name = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.type_name
    class Meta:
        verbose_name_plural = '12 Sticker Type'



def slug_is_taken_by_site(slug):
    """True if /<slug>/ is already one of the site's own pages (cart, blog, admin...),
    so a product category can't take that URL."""
    from django.urls import resolve, Resolver404
    if slug in ('admin', 'jet', 'media', 'static', 'shop', 'design'):
        return True
    try:
        match = resolve(f'/{slug}/')
    except Resolver404:
        return False
    return match.url_name != 'category_styles'


# ---- "Upload HTML" option for blog posts, services and get-apparel-for pages ----
HTML_FILE_HELP = ("Optional: upload an .html file. When set, its content is shown as the page's article "
                  "instead of the content typed above (site header and footer stay). Clear it to go back.")


def validate_html_file(f):
    from django.core.exceptions import ValidationError
    if os.path.splitext(f.name)[1].lower() not in ('.html', '.htm'):
        raise ValidationError('Please upload an .html or .htm file.')


def read_uploaded_html(field):
    """Content of an uploaded .html file, ready to drop inside the page.
    A full document keeps the <style>/<link> tags of its <head> plus everything inside <body>."""
    import re
    if not field:
        return ''
    try:
        field.open('rb')
        raw = field.read()
        field.close()
    except (OSError, ValueError):
        return ''
    text = raw.decode('utf-8', errors='replace')
    body = re.search(r'<body[^>]*>(.*)</body>', text, re.DOTALL | re.IGNORECASE)
    if not body:
        return text
    head = re.search(r'<head[^>]*>(.*)</head>', text, re.DOTALL | re.IGNORECASE)
    styles = re.findall(r'<style[^>]*>.*?</style>|<link[^>]+rel=["\']?stylesheet[^>]*>', head.group(1), re.DOTALL | re.IGNORECASE) if head else []
    return '\n'.join(styles + [body.group(1)])


COLOR_FAMILIES = (
    # value, label, swatch shown in the colour filter
    ('black', 'Black'), ('white', 'White'), ('grey', 'Grey'), ('red', 'Red'), ('pink', 'Pink'),
    ('orange', 'Orange'), ('yellow', 'Yellow'), ('green', 'Green'), ('blue', 'Blue'),
    ('purple', 'Purple'), ('brown', 'Brown'), ('natural', 'Natural / Beige'), ('multi', 'Multi / Other'),
)
COLOR_FAMILY_SWATCH = {
    'black': '#1D1D1B', 'white': '#FFFFFF', 'grey': '#A6A6A2', 'red': '#C8323A', 'pink': '#EDB5C4',
    'orange': '#E07B2E', 'yellow': '#F2C94C', 'green': '#2F6B45', 'blue': '#2B5BA8', 'purple': '#6B4C9A',
    'brown': '#7A5134', 'natural': '#E8DFCC', 'multi': 'conic-gradient(#C8323A, #F2C94C, #2F6B45, #2B5BA8, #C8323A)',
}


class Color(models.Model):
    color_code = ColorField(default='' , blank=True , null=True)
    color_name = models.CharField(max_length=255 , default='' , blank=True , null=True)
    # Shade group for filters: Cardinal Red, Dark Red, Blood Red... all belong to "Red"
    family = models.CharField(max_length=20, choices=COLOR_FAMILIES, default='', blank=True, help_text="Colour group used by the shop colour filter")
    Available = models.CharField(choices=YES_OR_NO , default="Yes" , max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def color_Show(self):
        if self.color_code:
            return mark_safe('<div style="width:30px;height:30px;background-color:%s;"></div>' % (self.color_code))
        else:
            return mark_safe('------')


    def __str__(self):
        if self.color_name:
            return self.color_name
        else:
            return '----'

    class Meta:
        verbose_name_plural = '08. Colors'



class Size(models.Model):
    Size_name = models.CharField(max_length=255 , default='')
    Available = models.CharField(choices=YES_OR_NO , default="Yes" , max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.Size_name:
            return self.Size_name
        else:
            return '----'
    class Meta:
        verbose_name_plural = '09. Size'



class UploadSticker(models.Model):
    Sticker_Name = models.CharField(max_length=255)
    Sticker_type = models.ForeignKey(StickerType , on_delete=models.SET_NULL , null=True , blank=True)
    Sticker_Image = models.ImageField(upload_to="shop/stickers", max_length=10000 , default='shop/stickers/default_sticker.png')
    Sticker_Vector_File = models.ImageField(upload_to="shop/stickers", max_length=10000 , default='shop/stickers/default_sticker_file.png' , blank=True , null=True)
    Sticker_Price = models.FloatField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = '13 Upload Sticker'


    def sticker_preview(self):
        if self.Sticker_Image:
            return mark_safe('<img src="%s" class="admin_Category_image_per"/>' % (self.Sticker_Image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_image_per"/>')
        
    
    def Download_file(self):
        if self.Sticker_Vector_File:
            return mark_safe(f'<a href="{self.Sticker_Vector_File.url}" download>Download FIle</a>')
        else:
            return mark_safe(f'<a href="#">Download FIle</a>')

    def __str__(self):
        return self.Sticker_Name


# Category
class Category(models.Model):
    category_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    
    category_name = models.CharField(max_length=50, default=""  , verbose_name="Category")
    category = models.CharField(max_length=60, default="" , verbose_name="Category") 
    subcategories = models.CharField(
        max_length=50, default="", blank=True, null=True)
    offer = models.CharField(max_length=50 , default="new", blank=True, null=True)
    cate_image = models.ImageField(
        upload_to="shop/images", default="shop/images/noperview.jpg", blank=True, null=True)
    landscape_image = models.ImageField(
        upload_to="shop/images", default="shop/images/noperview.jpg", blank=True, null=True)
    pub_date = models.DateField(auto_now_add=True ,  blank=True, null=True)
    active = models.BooleanField(default=False)

    # Custom URL + styles page (e.g. /tshirts/ lists every T-shirt style)
    slug = models.SlugField(max_length=120, unique=True, null=True, blank=True, help_text="URL of this product's page, e.g. tshirts → /tshirts/")
    page_title = models.CharField(max_length=200, default='', blank=True, help_text="Heading on the styles page (falls back to the name)")
    page_description = models.TextField(default='', blank=True, help_text="Text under the heading on the styles page")
    meta_title = models.CharField(max_length=255, default='', blank=True)
    meta_description = models.TextField(max_length=1000, default='', blank=True)
    # All products page
    is_pinned = models.BooleanField(default=False, help_text="Show in the first row of the All products page")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     imag = Image.open(self.cate_image.path)
    #     if imag.width > 300 or imag.height> 300:
    #         output_size = (500, 500)
    #         imag.thumbnail(output_size)
    #         imag.save(self.cate_image.path)
            


    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    def __str__(self):
        return self.category_name

    def get_absolute_url(self):
        return f'/{self.slug}/' if self.slug else f'/products/{self.category_id}/'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.slug and slug_is_taken_by_site(self.slug):
            raise ValidationError({'slug': f'"/{self.slug}/" is already a page on the site - please choose another URL.'})

    def live_styles(self):
        """Design Lab products (styles) of this category that are live."""
        return self.product_set.filter(live=True, product_type='custom')

    class Meta:
        verbose_name_plural = '01. Category'

    def Category_image(self):
        if self.cate_image:
            return mark_safe('<img src="%s" class="admin_Category_image_per"/>' % (self.cate_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_image_per"/>')
    
    def Category_Banner(self):
        if self.landscape_image:
            return mark_safe('<img src="%s" class="admin_Category_Banner_per"/>' % (self.landscape_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_Banner_per"/>')


# Store
# class Store(models.Model):
#     store_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
#     store_user = models.ForeignKey(User, on_delete=models.CASCADE , default="" , blank=True, null=True)
#     store_name = models.CharField( max_length=50, default="", blank=True, null=True)
#     store = models.CharField(max_length=60, default="")
#     address = models.TextField( max_length=20000, default="", blank=True, null=True)
#     logo = models.ImageField( upload_to="shop/images", default="", blank=True, null=True)
#     store_product_img = models.ImageField(upload_to="shop/images", default="shop/img/noimage.jpg", blank=True, null=True)
#     issue_date = models.DateField(blank=True, null=True)
#     live = models.BooleanField(default=False)
    

    
#     def __unicode__(self):
#         return self.store_name

#     @staticmethod
#     def get_all_categories():
#         return Store.objects.all()

#     def __str__(self):
#         return self.store_name
    
#     def image_tag(self):
#         return mark_safe('<img src="%s" width="50" height="50"/>' % (self.logo.url))
    




class MockUp(models.Model):
    MockUp_Name = models.CharField(max_length=255)
    MockUp_Fornt_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_front.png')
    MockUp_Back_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_back.png')
    MockUp_Left_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_back.png')
    MockUp_Right_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_back.png')
    Mockup_banner = models.ImageField(upload_to="shop/stickers" , default='shop/stickers/default_mockup_back.png')
    Price = models.FloatField(default=0)
    Active = models.CharField(max_length=244 , choices=YES_OR_NO , default="No")
    date = models.DateTimeField(auto_now_add=True)

    def mockup_fornt_image(self):
        if self.MockUp_Fornt_Image:
            return mark_safe('<img src="%s" class="admin_Category_image_per"/>' % (self.MockUp_Fornt_Image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_image_per"/>')
        
    def __str__(self):
        return self.MockUp_Name
    
    class Meta:
        verbose_name_plural = '07. MockUps'



# Product type: decides where a product shows on the site
PRODUCT_TYPES = (
    ('custom', 'Custom - customer designs it in the Design Lab'),
    ('shop', 'Shop - blank garment used as base for Shop Designs'),
)


# All Product
class Product(models.Model):
    product_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    product_type = models.CharField(
        max_length=10, choices=PRODUCT_TYPES, default='custom', db_index=True,
        help_text="Custom = shows in the Design Lab and style pages. Shop = only used as the base product of Shop Designs.")
    user = models.ForeignKey(User, on_delete=models.CASCADE , default="" ,  blank=True, null=True)
    # brand = models.CharField(max_length=200, default="", blank=True, null=True)
    product_name = models.CharField(max_length=200, default="" , blank=True, null=True)
    is_best_seller = models.BooleanField(default=False, blank=True, null=True)
    is_sustainable = models.BooleanField(default=False, blank=True, null=True, verbose_name='Is Trending')

    size_available = models.CharField(max_length=200, default="" , blank=True, null=True)
    # product_model = models.CharField(max_length=225 , default="" , blank=True, null=True)
    # product_code = models.CharField(max_length=225 , default="")
    categories = models.ForeignKey(Category, on_delete=models.SET_NULL , default="" , blank=True, null=True)
    # sub_categories = models.CharField(max_length=50, default="", blank=True, null=True)
    Availibility = models.IntegerField(default=0)
    min_qty = models.IntegerField(default=1 , blank=True, null=True)
    max_qty = models.IntegerField(default=5 , blank=True, null=True)

    customize_mockup_template  = models.ForeignKey(MockUp , on_delete=models.SET_NULL , null=True , blank=True)
    size_chart_img = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)

    Slug = models.SlugField(max_length=255 , default="", blank=True, null=True)
    Meta_title = models.CharField(max_length=255 , default="", blank=True, null=True)
    Meta_description = models.TextField(max_length=1000, default="", blank=True, null=True)

    # price = models.FloatField(default=0 , blank=True, null=True)
    # sprice = models.FloatField(default=0, blank=True, null=True , verbose_name="Discount Price")
    # offer_tag = models.CharField(max_length=200, default="", blank=True, null=True)
    desc = models.TextField(max_length=9999999999999999999 , default="", blank=True, null=True , verbose_name="Descriptions")
    short_desc = models.TextField(max_length=9999999999999999999 , default="", blank=True, null=True , verbose_name="Short Description")
    pub_date = models.DateTimeField(auto_now_add=True, max_length=12 , blank=True, null=True)
    # show_in_slider =  models.BooleanField(default=False)
    # product_weight = models.CharField(max_length=2000, default="")
    # flash_sale = models.BooleanField(default=False)
    live = models.BooleanField(default=False)

    printed_image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    blank_image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)

    fabric_composition = models.CharField(max_length=255, blank=True, null=True)
    compare_product_img = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    softness = models.CharField(max_length=50, blank=True, null=True)
    fabric_weight = models.CharField(max_length=50, blank=True, null=True)
    fit = models.CharField(max_length=50, blank=True, null=True)
    construction_quality = models.CharField(max_length=50, blank=True, null=True)
    price_range = models.CharField(max_length=50, blank=True, null=True)
    durability = models.CharField(max_length=50, blank=True, null=True)


    # Product (style) page
    promo_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount % for colours marked 'Promo' below (0 = no promo)")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first on the styles page")

    def save(self, *args, **kwargs):
        # Only fill the URL when empty, so a custom URL typed in the admin is kept
        if not self.Slug:
            self.Slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)

    def card_photo(self):
        """Picture for product cards: the first real colour photo, else the old blank mockup."""
        pc = self.color_photos.filter(front_image__isnull=False).exclude(front_image='').first()
        if pc:
            return pc.front_image.url
        return f'/media/{self.blank_image}' if self.blank_image else '/media/shop/images/noperview.jpg'

    def get_absolute_url(self):
        cat = self.categories
        if cat and cat.slug and self.Slug:
            return f'/{cat.slug}/{self.Slug}/'
        return f'/product_detail/{self.product_id}/'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.Slug and self.categories_id:
            clash = Product.objects.filter(categories_id=self.categories_id, Slug=self.Slug).exclude(pk=self.pk)
            if clash.exists():
                raise ValidationError({'Slug': f'Another product in this category already uses "{self.Slug}".'})
    

    def stock(self):
        if self.Available() > 0:
            return mark_safe(f'<p style="color: #1b8900;white-space: nowrap; background: #2cdd0036;padding: 4px 7px;border-radius: 10px;margin: 0px 0px;text-align: center;">{self.Available()} in Stock</p>')
        else:
            return mark_safe(f'<p style="color: #f30c0c; white-space: nowrap;background: #dd000036;padding: 4px 7px;border-radius: 10px;margin: 0px 0px;text-align: center;">{self.Available()} Out Of Stock</p>')
    
    def __unicode__(self):
        return self.product_name



    def Available(self):
        all_avaliblity = 0
        if self.product_id:
            find_prod_attri = ProductAttribute.objects.filter(product__product_id=self.product_id)
            for i in find_prod_attri:
                all_avaliblity += i.Availibility 
            return all_avaliblity
        else:
            all_avaliblity = 0
            return all_avaliblity


    @staticmethod
    def get_all_products():
        return Product.objects.all()

    @staticmethod
    def get_all_products_by_categoryid(category_id):
        if category_id:
            return Product.objects.filter(categories=category_id)
        else:
            return Product.get_all_products()

    @staticmethod
    def get_all_products_by_storeid(store_id):
        if store_id:
            return Product.objects.filter(store=store_id)
        else:
            return Product.get_all_products()

    def __str__(self):
        return self.product_name

    
    def preview(self):
        """Admin list thumbnail. Order: blank image -> first colour photo
        (Product Colours) -> first variation image -> "No image" box."""
        img = '<img src="{}" width="50" height="50" style="object-fit:cover"/>'
        if self.blank_image and default_storage.exists(self.blank_image.name):
            return mark_safe(img.format(self.blank_image.url))
        # Products added with real colour photos (Product Colours)
        color = self.color_photos.exclude(front_image='').exclude(front_image__isnull=True).first()
        if color:
            return mark_safe(img.format(color.front_image.url))
        attr = ProductAttribute.objects.filter(product__product_id=self.product_id).first()
        if attr and attr.image and default_storage.exists(attr.image.name):
            return mark_safe(img.format(attr.image.url))
        return mark_safe('<span style="display:inline-flex;align-items:center;justify-content:center;'
                         'width:50px;height:50px;border:1px dashed #bbb;font-size:10px;color:#888">No image</span>')

    class Meta:
        verbose_name_plural = '02. Products'

class ProductColor(models.Model):
    """Real product photos for one colour of a style (replaces the tinted mockup
    on the product page). Sizes, prices and stock stay in Product Variations."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='color_photos')
    color = models.ForeignKey(Color, on_delete=models.PROTECT, help_text="Must be a colour this product has in its variations")
    is_promo = models.BooleanField(default=False, help_text="Show under 'Promo colours' with the product's promo discount")
    front_image = models.ImageField(upload_to='shop/product_colors', max_length=1000, blank=True, null=True)
    back_image = models.ImageField(upload_to='shop/product_colors', max_length=1000, blank=True, null=True)
    left_image = models.ImageField(upload_to='shop/product_colors', max_length=1000, blank=True, null=True, verbose_name='Left sleeve image')
    right_image = models.ImageField(upload_to='shop/product_colors', max_length=1000, blank=True, null=True, verbose_name='Right sleeve image')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('product', 'color')
        verbose_name = 'Colour photos'
        verbose_name_plural = 'Colour photos'

    def __str__(self):
        return f'{self.product} - {self.color}'

    def views(self):
        """[(label, url), ...] for the gallery, in display order."""
        out = []
        for label, field in (('Front', self.front_image), ('Back', self.back_image),
                             ('Left sleeve', self.left_image), ('Right sleeve', self.right_image)):
            if field:
                out.append((label, field.url))
        return out


class ProductPhoto(models.Model):
    """Extra gallery photos (On model, Fabric...). Leave colour empty to show for every colour."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='photos')
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, help_text="Empty = show for all colours")
    image = models.ImageField(upload_to='shop/product_photos', max_length=1000)
    label = models.CharField(max_length=60, default='', blank=True, help_text="e.g. On model, Fabric")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.product} - {self.label or "photo"}'


class ProductPreview(models.Model):
    VIEW_CHOICES = [
        ('front', 'Front'),
        ('back', 'Back'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="previews")
    view_type = models.CharField(max_length=20, choices=VIEW_CHOICES)
    image = models.ImageField(upload_to='shop/product_previews/')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.product_name} - {self.view_type} ({self.order})"



#contact
class Contact(models.Model):
    msg_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    name = models.CharField(max_length=70, default="")
    email = models.CharField(max_length=70, default="")
    phone = models.CharField(max_length=70, default="")
    desc = models.TextField(max_length=1000, default="" , verbose_name='message')
    date = models.DateTimeField(auto_now_add=True, max_length=12)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '11. Contacts'


def code_gen(word , obj):
    last_id = obj.objects.all().last()
    if last_id:
        if int(last_id.order_id) > 0:
            incres_id = int(last_id.order_id) + 1
        else:
            incres_id = 1
            
        now = date.today()
        str_date = now.strftime("%m%d%Y")
        cn_formet = f'{word}-{str_date}{incres_id}'
        return cn_formet
    else:
        incres_id = 1
        now = date.today()
        str_date = now.strftime("%m%d%Y")
        cn_formet = f'{word}-{str_date}{incres_id}'
        return cn_formet




class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Province(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    delivery_charge = models.PositiveIntegerField(default=0)
    tax = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = '20. Province'

    def __str__(self):
        return self.name
 

# Order
class Order(models.Model):
    order_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    Order_number = models.CharField(max_length=70, default="" ,  blank=True, null=True)
    # user = models.ForeignKey(User, on_delete=models.CASCADE , default="" ,  blank=True, null=True)
    name = models.CharField(max_length=70, default="")
    # ip_address = models.CharField(max_length=500, default="" , blank=True, null=True)
    email = models.CharField(max_length=70, default="")
    address = models.TextField(max_length=300, default="")
    apartment_suite = models.CharField(max_length=250, default='', blank=True, null=True)
    company = models.CharField(max_length=250, default='', blank=True, null=True)
    Country = models.ForeignKey(Country, on_delete=models.CASCADE, default=None, blank=True, null=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, default=None, blank=True, null=True)
    zip_code = models.CharField(max_length=70, default="", blank=True, null=True)
    city = models.CharField(max_length=70, default="", blank=True, null=True)
    phone = models.CharField(max_length=11, default="")
    promo = models.CharField(max_length=100, default="" , blank=True, null=True)
    coupon = models.ForeignKey(CouponCode, on_delete=models.CASCADE , blank=True,null=True)
    discount_amount = models.CharField(max_length=255,default='', verbose_name="Discount")
    # Home_or_office = models.CharField(max_length=100, default="")
    # Payment_method = models.CharField(max_length=100, default="")
    SubTotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    Delivery = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Grand Total'
    )
    special_instructions = models.TextField(max_length=2000 ,  default="" , blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, max_length=12)
    Active = models.BooleanField(default=False)
    ship_type = models.CharField(max_length=70, default="", blank=True, null=True, choices=SHIP_TYPE)

    estimated_delivery_time = models.DateField(auto_now_add=False)

    order_detail_zip = models.FileField(
        upload_to='order_packages/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name
    
    def generate_zip(self):
        """
        Generate the ZIP for this order and return it as an HTTP response for download.
        No file is saved in the database.
        """
        from django.http import HttpResponse
        from .utils.order_package import generate_order_zip_file
        try:
            zip_buffer = generate_order_zip_file(self)
            zip_buffer.seek(0)  # make sure buffer is at the start

            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename=ORDER_{self.Order_number}.zip'
            return response

        except Exception as e:
            print(f"Error generating ZIP for Order {self.Order_number}: {e}")
            return HttpResponse("Failed to generate ZIP.", status=500)


    def save(self, *args, **kwargs):
        if not self.Order_number:
            self.Order_number = code_gen('SM', Order)

        super(Order, self).save(*args, **kwargs)

        # ✅ Generate/update ZIP only once per order
        # try:
        #     from .utils.order_package import generate_order_zip_file
        #     from django.core.files.base import ContentFile

        #     zip_buffer = generate_order_zip_file(self)

        #     # overwrite previous ZIP
        #     self.order_detail_zip.save(
        #         f'ORDER_{self.Order_number}.zip',
        #         ContentFile(zip_buffer.read()),
        #         save=False
        #     )

        #     super(Order, self).save(update_fields=['order_detail_zip'])

        # except Exception as e:
        #     print(f"Error generating ZIP for Order {self.Order_number}: {e}")





    
    def nofity(self):
        today = datetime.now()
        # print(today.date() , self.created.date())
        if today.date() == self.created.date() and self.Active == False:
            return mark_safe('<p style="margin: 0px;background: #ff000066;text-align: center;padding: 5px 9px;border-radius: 50px;color: #b70000; font-weight: bold;white-space: nowrap;">New Order</p>')
        elif  self.Active == True:
            return mark_safe('<p style="margin: 0px;background: #00ff1f66;text-align: center;padding: 5px 9px;border-radius: 50px;color: #005c21; font-weight: bold;white-space: nowrap;">Active Order</p>')

        else:
            return mark_safe('<p style="margin: 0px;background: #fff70066;text-align: center;padding: 5px 9px;border-radius: 50px;color: #a99507; font-weight: bold;white-space: nowrap;">UnActive Order</p>')


    def Total_items(self):
        order_items_list = OrderItem.objects.filter(order_by__order_id=self.order_id)
        count_total = order_items_list.count()
        item_concatinate = ''
        for i in order_items_list:
            if i.status == 'processing':
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: #192ee4; font-weight: bold;">P , </span>'
                
            elif i.status == 'shipped':
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: #d9be00; font-weight: bold;">S , </span>'
            
            elif i.status == 'delivered':
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: #005c21; font-weight: bold;">D , </span>'
            
            else:
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: red; font-weight: bold;">C , </span>'
                
        return mark_safe(f'<p style="text-align: center;padding: 5px 9px;white-space: nowrap; font-weight: bold;">{item_concatinate} Total item {count_total}</p>'  )
        
    class Meta:
        verbose_name_plural = '05. Orders'

STATUS = (
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered' , 'Delivered'),
    ('cancelation' , 'Cancelation')
)


ORDER_TYPE = (
    ('Customize', 'Customize'),
    ('Normal', 'Normal'),
    ('Shop Design', 'Shop Design'),
)



class OrderItem(models.Model):
    order_by = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_item = models.ForeignKey(Product, on_delete=models.SET_DEFAULT , default='' ,  blank=True, null=True)
    product_name = models.CharField(max_length=255, default="")
    # product_brand = models.CharField(max_length=255, default="", blank=True, null=True)
    # quantity = models.IntegerField(default="" )
    # size = models.CharField(max_length=255, default="", blank=True, null=True)
    color = models.CharField(max_length=255, default="", blank=True, null=True)
    unity_price = models.FloatField(default=0)
    # weight = models.CharField(default='0' , max_length=255 , blank=True, null=True)
    item_total = models.FloatField(default=0)
    image = models.TextField(default="")
    date = models.DateTimeField(auto_now_add=True, max_length=12)
    status = models.CharField(choices=STATUS , max_length=50 , default='processing')
    order_status = models.CharField(max_length=255, default="" ,  blank=True, null=True , verbose_name='On Flash Sale')

    Mockup = models.ForeignKey(MockUp , on_delete=models.SET_DEFAULT , default='' ,  blank=True, null=True)
    Order_Type = models.CharField(max_length=200 , choices=ORDER_TYPE , default='Normal')
    Front_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Front Image')
    Back_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Back Image')
    Left_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Left Image')
    Right_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Right Image')
    
    Front_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    Back_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    Left_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    Right_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)

    # Shop designs only (empty for Design Lab / old orders)
    shop_design = models.ForeignKey('ShopDesign', on_delete=models.SET_NULL, null=True, blank=True)
    personal_image = models.FileField(upload_to='order_personal_images/', max_length=1000, blank=True, null=True, verbose_name='Customer photo')
    # Design Lab: print / embroidery per artwork, texts and the customer's notes
    design_details = models.TextField(default='', blank=True, verbose_name='Design details')
    # Front_Text = models.CharField(max_length=255, default="", blank=True, null=True)
    # Back_Text = models.CharField(max_length=255, default="", blank=True, null=True)

    # availibile_minus = models.BooleanField(default=False , blank=True, null=True , editable=False)
    # cancel_availibile_minus_field = models.BooleanField(default=False , blank=True, null=True , editable=False)

    Active = models.BooleanField(default=False) 
    
    def  __str__(self):
        return self.product_name[0:20] + "..."
    
    def Order_by_Id(self):
        if self.order_by:
            return self.order_by.order_id
        else:
            return ''
    def image_thumbnail(self):
        if self.image:
            return mark_safe('<img class="order_item_img" src="%s" width="50" height="50"/>' % (self.image))
        else:
            return mark_safe('<img class"order_item_img" src="/media/shop/images/noperview.jpg" width="50" height="50"/>')
        

    def save(self, *args, **kwargs):
        super(OrderItem, self).save(*args, **kwargs)

        orderid = self.id
        if not orderid:
            return

        try:
            order_item = OrderItem.objects.get(id=orderid)
        except OrderItem.DoesNotExist:
            return

        # Skip if no product
        if not order_item.order_item:
            return

        try:
            # Find matching product attribute (based on color only)
            if order_item.color not in [None, '', 'undefined', 'None']:
                filter_ava = ProductAttribute.objects.filter(
                    product__product_id=order_item.order_item.product_id,
                    color__color_name=order_item.color
                ).first()
            else:
                filter_ava = ProductAttribute.objects.filter(
                    product__product_id=order_item.order_item.product_id
                ).first()

            if not filter_ava:
                return

            # Quantity adjustment (if quantity field added later)
            calcul = getattr(order_item, 'quantity', 1)

            # Decrease stock when new order
            if order_item.Active is False and order_item.status != "cancelation":
                stock_update = filter_ava.Availibility - calcul
                order_item.Active = True
                order_item.save(update_fields=['Active'])
                ProductAttribute.objects.filter(id=filter_ava.id).update(Availibility=stock_update)

            # Restore stock when canceled
            elif order_item.status == "cancelation" and not order_item.Active:
                stock_update = filter_ava.Availibility + calcul
                order_item.Active = True
                order_item.save(update_fields=['Active'])
                ProductAttribute.objects.filter(id=filter_ava.id).update(Availibility=stock_update)

                # Send cancellation email
                params = {
                    'order_id': self.order_by.Order_number,
                    'name': self.order_by.name,
                    'email': self.order_by.email,
                    'address': self.order_by.address,
                    'city': self.order_by.city,
                    'country': self.order_by.country,
                    'phone': self.order_by.phone,
                    'date': self.order_by.created,
                    'item': order_item
                }
                html_message = render_to_string('shop/order_cancel_mail.html', params)
                plain_message = strip_tags(html_message)
                send_mail(
                    'Order Cancelled',
                    plain_message,
                    DEFAULT_FROM_EMAIL,
                    [self.order_by.email, EMAIL_HOST_USER],
                    html_message=html_message
                )

        except Exception as e:
            print(f"Error updating stock for OrderItem {orderid}: {e}")

        # ✅ Generate/update order ZIP whenever an item is saved
        # try:
        #     from .utils.order_package import generate_order_zip_file
        #     from django.core.files.base import ContentFile

        #     order = self.order_by
        #     zip_buffer = generate_order_zip_file(order)
        #     order.order_detail_zip.save(
        #         f'ORDER_{order.Order_number}.zip',
        #         ContentFile(zip_buffer.read()),
        #         save=False
        #     )
        #     super(Order, order).save(update_fields=['order_detail_zip'])

        # except Exception as e:
        #     print(f"Error generating ZIP for Order {self.order_by.Order_number}: {e}")



 
                # except:
                #     pass




    class Meta:
        verbose_name_plural = '06. Order Item'


class OrderItemSize(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.FloatField(default=0)
    total_price = models.FloatField(default=0)
    # Shop designs: this piece's text as JSON [{"label": "Text 1", "value": "Sara"}, ...]
    personalization = models.TextField(default='', blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.size} - {self.quantity}"

    def personalization_display(self):
        return personalization_as_html(self.personalization)
    personalization_display.short_description = "Personalization"


# Order_Update
class OrderUpdate(models.Model):
    update_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    order_id = models.IntegerField(default="")
    update_messages = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return self.update_messages[0:7] + "..."


    class Meta:
        verbose_name_plural = '08. Order Update'

#Banner
class Banner(models.Model):
    banner_title = models.CharField(max_length=200 , default="" , blank=True, null=True)
    landing_page_link = models.CharField(max_length=200 , default="#" , blank=True, null=True)
    pc_banner_image = models.ImageField(upload_to="shop/banner", blank=True, null=True)
    mobile_banner_image = models.ImageField(upload_to="shop/banner", blank=True, null=True)
    background_color = models.CharField(max_length=200 , default="" , blank=True, null=True)

    def __str__(self):
        return self.banner_title

    def image_tag(self):
        if self.pc_banner_image:
            return mark_safe('<img src="%s" width="50" />' % (self.pc_banner_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" width="50" height="50"/>')

    class Meta:
        verbose_name_plural = '09. Banners'


class CompetitorProduct(models.Model):
    main_product = models.ForeignKey(Product, on_delete=models.CASCADE) # your rull shirt
    competitor_name = models.CharField(max_length=200)
    competitor_image = models.ImageField(upload_to='competitor', blank=True, null=True)

    # the comparison fields
    fabric_composition = models.CharField(max_length=255, blank=True, null=True)
    softness = models.CharField(max_length=50, blank=True, null=True)
    fabric_weight = models.CharField(max_length=50, blank=True, null=True)
    fit = models.CharField(max_length=50, blank=True, null=True)
    construction_quality = models.CharField(max_length=50, blank=True, null=True)
    price_range = models.CharField(max_length=50, blank=True, null=True)
    durability = models.CharField(max_length=50, blank=True, null=True)


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE , default="" , blank=True , null=True)
    color = models.ForeignKey(Color , on_delete=models.SET_NULL , null=True , blank=True)
    size = models.ForeignKey(Size , on_delete=models.SET_NULL , null=True , blank=True)
    # color = models.CharField(max_length=100 , default="" , blank=True , null=True) 
    # size = models.CharField(max_length=100 , default="" , blank=True , null=True)
    price= models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    Availibility = models.IntegerField(default=0, blank=True, null=True , verbose_name='Availibility')
    Max_Qty = models.IntegerField(default=0, blank=True, null=True , verbose_name='Max Qty')
    weight = models.FloatField(default=0, blank=True, null=True)
    image = models.ImageField(upload_to="shop/images", default='shop/images/noperview.jpg' ,  blank=True, null=True)
    ogg_image = models.ImageField(upload_to="shop/images/ogg_image", default="shop/images/noperview.jpg",  blank=True, null=True)
    video_URL = models.CharField(max_length=255, default='' , blank=True , null=True)
    selected = models.BooleanField(default=True)
    select_for_color = models.CharField(max_length=50, default='' , blank=True , null=True)

    # def save(self, *args, **kwargs):
    #     if self.selected == True:
    #         if self.color:
    #             self.select_for_color = self.color

    #     super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.product_name} - {self.product.product_id}'

    def image_tag(self):
        if self.image:
            return mark_safe('<img src="%s" width="50" height="50"/>' % (self.image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" width="50" height="50"/>')
    
    class Meta:
        verbose_name_plural = '03. Product Variation'
    
  
class Product_Banner(models.Model):
    banner_name = models.CharField(max_length=200 , default="" , blank=True , null=True)         
    banner_title = models.CharField(max_length=255 , default="" , blank=True , null=True)
    banner_image = models.ImageField(upload_to="shop/images" ,  blank=True, null=True )
    landing_page_link = models.CharField(max_length=255 , default="#" , blank=True , null=True)

    def __str__(self):
        if self.banner_name:
            return self.banner_name
        else:
             return self.id
   
    def image_tag(self):
        if self.banner_image:
            return mark_safe('<img src="%s" width="70" height="50" >' %(self.banner_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" width="70" height="50"/>')

    class Meta:
        verbose_name_plural = '04. Product Banner'     
        
      

class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE , default="")
    device_ip = models.CharField(max_length=255 , default="")
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.device_ip
    
    class Meta:
        verbose_name_plural = '05. Product Views'
    
    
    
class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE , related_name='rates') 
    device_ip = models.CharField(max_length=100 , default='')
    rating = models.FloatField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.device_ip

    class Meta:
        verbose_name_plural = '10. Ratings'

class KeyWord(models.Model):
    KeyWords = models.CharField(max_length=200 , default="")
    Date = models.DateField(auto_now_add=True)
    DeviceIp = models.CharField(max_length=200 , default="",blank=True, null=True)
    user =  models.ForeignKey(User, on_delete=models.SET_NULL ,default=None, blank=True, null=True )
    def __str__(self):
        return self.KeyWords
    class Meta:
        verbose_name_plural = '11. KeyWords'

import uuid
class SavedDesign(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField()
    design_name = models.CharField(max_length=250, default='', blank=True, null=True )
    front_json = models.TextField(blank=True, null=True)
    back_json = models.TextField(blank=True, null=True)
    left_sleeve = models.TextField(blank=True, null=True)
    right_sleeve = models.TextField(blank=True, null=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product , on_delete=models.CASCADE, null=True, blank=True)
    product_attr = models.ForeignKey(ProductAttribute , on_delete=models.CASCADE, null=True, blank=True)
    mockup = models.ForeignKey(MockUp , on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_link(self):
        return f"/design/{self.uid}/"

    def __str__(self):
        return f"/design/{self.uid}/"

    class Meta:
        verbose_name_plural = '21. Saved Design'
    



class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '11. Blog Category'


class BlogPost(models.Model):
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, related_name="posts")
    meta_title = models.CharField(max_length=255, default='' ,blank=True, null=True)
    meta_description = models.TextField(default='' ,blank=True, null=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField()
    content = RichTextField(default="")
    image = models.ImageField(upload_to="shop/blog_images/")
    html_file = models.FileField(upload_to='shop/page_html/', blank=True, null=True, validators=[validate_html_file],
                                 verbose_name='Upload HTML', help_text=HTML_FILE_HELP)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    def uploaded_html(self):
        return read_uploaded_html(self.html_file)

    class Meta:
        verbose_name_plural = '12. Blog Post'
    
    
class Service(models.Model):
    meta_title = models.CharField(max_length=255, default='' ,blank=True, null=True)
    meta_description = models.TextField(default='' ,blank=True, null=True)
    title_for_dropdown = models.CharField(max_length=255, default='')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True,
                            help_text="URL of this page: /services/<this>/ (e.g. screen-printing). Left empty = made from the title.")
    subtitle = RichTextField(default='')
    icon_class = models.CharField(max_length=250, default='')
    image = models.ImageField(upload_to="shop/blog_images")
    setup_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    Per_Color_Price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    Per_Location_Price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    Rush = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    html_file = models.FileField(upload_to='shop/page_html/', blank=True, null=True, validators=[validate_html_file],
                                 verbose_name='Upload HTML', help_text=HTML_FILE_HELP)
    date = models.DateField(auto_now_add=True)

    def get_absolute_url(self):
        return f'/services/{self.slug}/' if self.slug else f'/service_detail/{self.id}/'

    def uploaded_html(self):
        return read_uploaded_html(self.html_file)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate base slug from title
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = "service"  # fallback if title is empty or invalid

            slug = base_slug
            counter = 1

            # Ensure uniqueness
            while Service.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '13. Service'
    
class GetApparelFor(models.Model):
    meta_title = models.CharField(max_length=255, default='' ,blank=True, null=True)
    meta_description = models.TextField(default='' ,blank=True, null=True)
    title_for_dropdown = models.CharField(max_length=255, default='')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True,
                            help_text="URL of this page: /get-apparel-for/<this>/ (e.g. church-groups). Left empty = made from the title.")
    subtitle = models.TextField()
    description = RichTextField(blank=True, null=True)
    icon_class = models.CharField(max_length=250, default='')
    image = models.ImageField(upload_to="shop/blog_images")
    html_file = models.FileField(upload_to='shop/page_html/', blank=True, null=True, validators=[validate_html_file],
                                 verbose_name='Upload HTML', help_text=HTML_FILE_HELP)
    date = models.DateField(auto_now_add=True)

    def get_absolute_url(self):
        return f'/get-apparel-for/{self.slug}/' if self.slug else f'/get_apparel_for/{self.id}/'

    def uploaded_html(self):
        return read_uploaded_html(self.html_file)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = "item"
            slug = base_slug
            counter = 1
            while GetApparelFor.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '14. Get Apparel For'

class GetApparelForSection(models.Model):
    get_apparel_for = models.ForeignKey(GetApparelFor, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    description = RichTextField(blank=True, null=True)

    def __str__(self):
        return f'{self.get_apparel_for.title} - {self.id}'

    class Meta:
        verbose_name_plural = '15. Get Apparel For Section'


class ServiceSection(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    subtitle = RichTextField(default='')
    image = models.ImageField(upload_to="shop/blog_images")

    def __str__(self):
        return f'{self.service.title} - {self.id}'

    class Meta:
        verbose_name_plural = 'Service Sections'
    
class GuestCart(models.Model):
    session_id = models.CharField(max_length=100, db_index=True)
    save_design_uid = models.CharField(max_length=1000, default='', blank=True, null=True)
    product_attr = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)

    # Mockup preview images
    front_image = models.TextField(blank=True, null=True)
    back_image = models.TextField(blank=True, null=True)
    left_image = models.TextField(blank=True, null=True, default='')
    right_image = models.TextField(blank=True, null=True, default='')

    # Raw design-only images (for printing)
    front_design_image = models.TextField(blank=True, null=True)
    back_design_image = models.TextField(blank=True, null=True)
    left_design_image = models.TextField(blank=True, null=True)
    right_design_image = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    price_of_each = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Shop designs only (empty for Design Lab / old items)
    shop_design = models.ForeignKey('ShopDesign', on_delete=models.SET_NULL, null=True, blank=True)
    personal_image = models.FileField(upload_to='cart_personal_images/', max_length=1000, blank=True, null=True, help_text="Customer photo for a personalizable shop design (same for every piece)")

    # Design Lab: what is on each side (print / embroidery, texts, notes) as readable text
    design_details = models.TextField(default='', blank=True)

    def __str__(self):
        return f"GuestCart {self.session_id} - {self.product_attr}"

    

class GuestCartItem(models.Model):
    cart = models.ForeignKey(GuestCart, on_delete=models.CASCADE, related_name='cart_items')
    size = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.FloatField(default=0)
    total_price = models.FloatField(default=0)
    # Shop designs: this piece's text as JSON [{"label": "Text 1", "value": "Sara"}, ...]
    personalization = models.TextField(default='', blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.size} × {self.quantity}"

    def personalization_display(self):
        return personalization_as_html(self.personalization)
    personalization_display.short_description = "Personalization"
  
class CartUploadedFile(models.Model):
    cart = models.ForeignKey(
        GuestCart,
        on_delete=models.CASCADE,
        related_name="uploaded_files"
    )

    file = models.FileField(
        upload_to="cart_uploaded_files/"
    )

    filename = models.CharField(
        max_length=255
    )

    side = models.CharField(
        max_length=20,
        choices=[
            ("front", "Front"),
            ("back", "Back"),
            ("left_sleeve", "Left Sleeve"),
            ("right_sleeve", "Right Sleeve"),
        ]
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.side})"


class OrderItemUploadedFile(models.Model):
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="uploaded_files"
    )

    file = models.FileField(upload_to="order_uploaded_files/")
    filename = models.CharField(max_length=255)
    side = models.CharField(
        max_length=20,
        choices=[
            ("front", "Front"),
            ("back", "Back"),
            ("left_sleeve", "Left Sleeve"),
            ("right_sleeve", "Right Sleeve"),
        ]
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.side})"


class DesignPricing(models.Model):
    # Existing fields
    embroidery_note = RichTextField(default="")


    front_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    back_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    left_sleeve_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    right_sleeve_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    embroidery_extra = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)


    standard_shipping_time =models.CharField(max_length=250, default='10-15')
    rush_shipping_time =models.CharField(max_length=250, default='7-10')

    # --- New dynamic shipping fields ---
    free_shipping_subtotal_threshold = models.DecimalField(
        max_digits=8, decimal_places=2, default=250.00,
        help_text="If subtotal is above this value, shipping becomes free."
    )
    free_shipping_postal_letters = models.CharField(
        max_length=100, default="L,M",
        help_text="Comma-separated list of first letters for free shipping (e.g. L,M)"
    )
    extra_charge_second_digit = models.CharField(
        max_length=5, default="0",
        help_text="If postal code's second digit matches this, extra charge applies."
    )
    extra_charge_amount = models.DecimalField(
        max_digits=6, decimal_places=2, default=5.00,
        help_text="Extra shipping charge for specific second digit postal codes."
    )
    rush_shipping_fee = models.DecimalField(
        max_digits=6, decimal_places=2, default=20.00,
        help_text="Extra cost for rush shipping."
    )
    waitsave_discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=30.00,
        help_text="Percentage discount for Wait & Save shipping."
    )

    class Meta:
        verbose_name_plural = '18. Design Pricing'



    def __str__(self):
        return "Design & Shipping Pricing Settings"


class QuantityDiscount(models.Model):
    pricing = models.ForeignKey(DesignPricing, on_delete=models.CASCADE, related_name='discount_tiers')
    min_qty = models.PositiveIntegerField()
    max_qty = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for open-ended range (e.g. 1000+)")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage discount")

    class Meta:
        ordering = ['min_qty']

    def __str__(self):
        if self.max_qty:
            return f"{self.min_qty}-{self.max_qty} pcs: {self.discount_percent}% off"
        return f"{self.min_qty}+ pcs: {self.discount_percent}% off"




# contact suppart 



class ContactSupport(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    compony_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    order_id = models.CharField(max_length=255, default='', blank=True, null=True)
    message = models.TextField(default='', blank=True, null=True)
    file = models.FileField( upload_to='shop/files', max_length=1000, default='', null=True, blank=True)
    # quantity = models.PositiveIntegerField()
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '17. Contact Support'

class ContactSales(models.Model):
    product = models.CharField(max_length=250, default='', blank=True, null=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    compony_name = models.CharField(max_length=255)
    product = models.CharField(max_length=255, default='')
    email = models.CharField(max_length=255)
    message = models.TextField(default='', blank=True, null=True)
    file = models.FileField( upload_to='shop/files', max_length=1000, blank=True, null=True)
    quantity = models.CharField(max_length=250, default='', blank=True, null=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '16. Contact Sales'
    

class Layout(models.Model):
    logo = models.ImageField(upload_to='shop/images', max_length=1000)
    favicon = models.ImageField(upload_to='shop/images', max_length=1000, default='')
    header_button_text = models.CharField(max_length=255)
    header_banner_text = models.CharField(max_length=255, default='')
    hero_title = models.CharField(max_length=255)
    hero_image = models.FileField(
        upload_to='shop/media',
        max_length=1000
    )

    def is_video(self):
        return os.path.splitext(self.hero_image.name)[1].lower() in (
            '.mp4', '.webm', '.ogg'
        )
    
    def __str__(self):
        return self.header_button_text

    class Meta:
        verbose_name_plural = '19. Layout'


class TopBannerText(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='text')
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class HeroFeature(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='features')
    title = models.CharField(max_length=255)
    short_desc = models.CharField(max_length=255)
    icon = models.ImageField(upload_to='shop/images', max_length=1000)
    
    # def __str__(self):
    #     return self.short_desc

    def __str__(self):
        return self.title
    

    

class Client(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='clients')
    title = models.CharField(max_length=255, default='', blank=True, null=True)
    image = models.ImageField(upload_to='shop/images', max_length=1000)
    
    def __str__(self):
        if self.title:
            return self.title
        else:
            return self.layout.hero_title

    class Meta:
        verbose_name_plural = '15. Clients'
        
class Faq(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)
    
    def __str__(self):
        if self.question:
            return self.question
        else:
            return self.answer



class AboutUs(models.Model):
    title = models.CharField(max_length=255)
    short_desc = models.CharField(max_length=255)
    long_desc = models.CharField(max_length=255)
    meta_title = models.CharField(max_length=255, default='', blank=True, verbose_name='SEO title')
    meta_description = models.TextField(max_length=1000, default='', blank=True, verbose_name='SEO description')
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '22. About Us'
    
class AboutSections(models.Model):
    about = models.ForeignKey(AboutUs, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    description = RichTextField(default='')
    image = models.ImageField(upload_to='shop/images', max_length=1000, default='')
    # def __str__(self):
    #     return self.short_desc

    def __str__(self):
        return self.title


class TermsCondition(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField(default="")
    meta_title = models.CharField(max_length=255, default='', blank=True, verbose_name='SEO title')
    meta_description = models.TextField(max_length=1000, default='', blank=True, verbose_name='SEO description')
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '23. Terms & Conditions'

class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField(default="")
    meta_title = models.CharField(max_length=255, default='', blank=True, verbose_name='SEO title')
    meta_description = models.TextField(max_length=1000, default='', blank=True, verbose_name='SEO description')
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '24. Privacy Policy'

class ShippingPolicy(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField(default="")
    meta_title = models.CharField(max_length=255, default='', blank=True, verbose_name='SEO title')
    meta_description = models.TextField(max_length=1000, default='', blank=True, verbose_name='SEO description')
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '24. Shipping Policy'

class InstagramPost(models.Model):
    title = models.CharField(max_length=255)
    link = models.CharField(max_length=255, default='', blank=True, null=True)
    image = models.ImageField( upload_to='shop/images', max_length=1000)
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '25. Instagram Posts'


# =====================================================================
# SHOP DESIGNS (ready-made designs sold on the Shop page)
# ---------------------------------------------------------------------
# Separate from Product on purpose: a Product is a blank garment that
# customers design on in the Design Lab. A ShopDesign is a finished
# design printed on one of those blanks (base_product), sold at a fixed
# price, optionally personalizable (customer text and/or one photo).
# Personalization never changes the product images; it only travels
# with the cart/order so the team can see what to print.
# =====================================================================

class Occasion(models.Model):
    TEXT_TONE = (
        ('dark', 'Dark text (for light card colours)'),
        ('light', 'Light text (for dark card colours)'),
    )

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=150, unique=True, help_text="URL part, e.g. bridal-party-shirts → /shop/bridal-party-shirts/")
    subtitle = models.CharField(max_length=255, default='', blank=True, help_text="Short line on the card, e.g. 'Bride, bridesmaids, bachelorette'")
    image = models.ImageField(upload_to='shop/occasions', max_length=1000, blank=True, null=True, help_text="Card photo (optional - the card colour shows if empty)")
    card_color = ColorField(default='#EFE9E2', help_text="Card background colour")
    text_tone = models.CharField(max_length=10, choices=TEXT_TONE, default='dark')

    show_in_menu = models.BooleanField(default=True, help_text="Show under 'By occasion' in the Shop designs menu")
    show_on_shop_page = models.BooleanField(default=True, help_text="Show in 'Shop by occasion' on the shop page")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")
    live = models.BooleanField(default=True)

    # Occasion page content (all editable)
    page_title = models.CharField(max_length=255, default='', blank=True, help_text="Page heading, e.g. 'Bridal party shirts' (falls back to the name)")
    page_description = models.TextField(default='', blank=True, help_text="Intro text under the page heading")
    strip_title = models.CharField(max_length=200, default='', blank=True, help_text="Group quote strip title for this occasion, e.g. 'Dressing the whole wedding party?' (falls back to Shop settings)")
    seo_heading = models.CharField(max_length=255, default='', blank=True, help_text="Heading of the text block at the bottom of the page")
    seo_content = RichTextField(default='', blank=True, help_text="150-300 words about this occasion, shown at the bottom of the page")
    meta_title = models.CharField(max_length=255, default='', blank=True)
    meta_description = models.TextField(max_length=1000, default='', blank=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = '26. Shop - Occasions'

    # These slugs are taken by fixed /shop/... pages
    RESERVED_SLUGS = ('occasions', 'designs', 'design')

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.slug in self.RESERVED_SLUGS:
            raise ValidationError({'slug': f'"{self.slug}" is reserved, please choose another URL.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def card_preview(self):
        if self.image:
            return mark_safe('<img src="%s" class="admin_Category_image_per"/>' % (self.image.url))
        return mark_safe('<div style="width:50px;height:50px;border-radius:6px;background:%s;"></div>' % (self.card_color))
    card_preview.short_description = "Card"


class OccasionFaq(models.Model):
    occasion = models.ForeignKey(Occasion, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.question


class ShopDesign(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, help_text="URL part of the design page, e.g. bride-crew-tee")
    base_product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='shop_designs',
        help_text="The blank garment this design is printed on. Sizes, stock, fabric and size chart come from it.",
    )
    occasions = models.ManyToManyField(Occasion, blank=True, related_name='designs')

    short_description = models.CharField(max_length=255, default='', blank=True, help_text="One line under the title on the design page")
    description = RichTextField(default='', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Fixed price per piece")

    is_best_seller = models.BooleanField(default=False)
    live = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")

    # Personalization
    is_personalizable = models.BooleanField(default=False)
    allow_image_upload = models.BooleanField(default=False, help_text="Customer can upload one photo (used on every piece)")
    image_upload_label = models.CharField(max_length=255, default='Replace the photo', blank=True)
    image_upload_help = models.CharField(max_length=255, default='Optional, applies to every piece', blank=True)
    image_position_preview = models.ImageField(upload_to='shop/designs', max_length=1000, blank=True, null=True, help_text="Picture showing where the customer's photo goes")
    allow_text = models.BooleanField(default=False, help_text="Customer can add text - add the text fields below")
    personalization_gif = models.FileField(upload_to='shop/designs', max_length=1000, blank=True, null=True, help_text="GIF showing how personalization looks (instead of a live preview)")

    meta_title = models.CharField(max_length=255, default='', blank=True)
    meta_description = models.TextField(max_length=1000, default='', blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created']
        verbose_name_plural = '27. Shop - Designs'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def wants_image(self):
        return self.is_personalizable and self.allow_image_upload

    @property
    def wants_text(self):
        return self.is_personalizable and self.allow_text

    def personalization_badge(self):
        """Small label on product cards: 'Add a name' / 'Add a photo'."""
        if self.wants_text:
            return 'Add a name'
        if self.wants_image:
            return 'Add a photo'
        return ''

    def default_color(self):
        colors = list(self.colors.all())
        for c in colors:
            if c.is_default:
                return c
        return colors[0] if colors else None

    def preview(self):
        c = self.default_color()
        if c and c.hero_image:
            return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover"/>' % (c.hero_image.url))
        return mark_safe('<img src="/media/shop/images/noperview.jpg" width="50" height="50"/>')


class ShopDesignColor(models.Model):
    design = models.ForeignKey(ShopDesign, on_delete=models.CASCADE, related_name='colors')
    color = models.ForeignKey(Color, on_delete=models.PROTECT, help_text="Must be a colour the base product has")
    hero_image = models.ImageField(upload_to='shop/designs', max_length=1000)
    back_image = models.ImageField(upload_to='shop/designs', max_length=1000, blank=True, null=True, help_text="Optional - only if the design is printed on the back too")
    is_default = models.BooleanField(default=False, help_text="Shown first on cards and the design page")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_default', 'order', 'id']
        unique_together = ('design', 'color')

    def __str__(self):
        return f'{self.design.name} - {self.color}'


class ShopDesignImage(models.Model):
    """Extra gallery photos/GIFs (lifestyle shots etc.), not tied to a colour."""
    design = models.ForeignKey(ShopDesign, on_delete=models.CASCADE, related_name='gallery')
    image = models.FileField(upload_to='shop/designs', max_length=1000, help_text="JPG, PNG, WEBP or GIF")
    alt_text = models.CharField(max_length=255, default='', blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.design.name} - image {self.order}'


class ShopDesignTextField(models.Model):
    """One text box the customer fills per piece (Text 1, Text 2, ...)."""
    design = models.ForeignKey(ShopDesign, on_delete=models.CASCADE, related_name='text_fields')
    label = models.CharField(max_length=100, help_text="e.g. 'Text 1' or 'Name on front'")
    help_text = models.CharField(max_length=255, default='', blank=True, help_text="e.g. 'Name on the front, up to 12 letters'")
    placeholder = models.CharField(max_length=100, default='', blank=True, help_text="e.g. 'e.g. Sara'")
    max_length = models.PositiveIntegerField(default=12)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label


class ShopSettings(models.Model):
    """
    One record that holds every editable text of the new header menus and the
    Shop pages (menu promo, custom merch boxes, shop home, CTA cards, SEO).
    Use ShopSettings.load() - it never writes to the database.
    """
    # ---- Header: "Shop designs" menu promo banner ----
    menu_promo_eyebrow = models.CharField(max_length=100, default='The holiday drop', blank=True)
    menu_promo_title = models.CharField(max_length=200, default='Matching family tees, a name on every one', blank=True)
    menu_promo_button = models.CharField(max_length=60, default='Shop the drop', blank=True)
    menu_promo_url = models.CharField(max_length=500, default='/shop/', blank=True)
    menu_promo_image = models.ImageField(upload_to='shop/settings', max_length=1000, blank=True, null=True)
    menu_promo_color = ColorField(default='#A63A35')

    # ---- Header: "Custom merch" menu boxes ----
    design_box_title = models.CharField(max_length=100, default='Design it yourself')
    design_box_text = models.TextField(default='Open the Design Lab. Pick a product and colour, add your text, logo or art, choose print or embroidery, and see your price as you go.', blank=True)
    design_box_cta = models.CharField(max_length=60, default='Open the Design Lab')
    design_box_url = models.CharField(max_length=500, default='', blank=True, help_text="Leave empty to open the Design Lab with the first product")
    design_box_color = ColorField(default='#F1F2EC')

    idea_box_title = models.CharField(max_length=100, default='Send us your idea')
    idea_box_text = models.TextField(default='Share a sketch, screenshot or a design you love. We recreate it as your own and send you a free mockup.', blank=True)
    idea_box_cta = models.CharField(max_length=60, default='Send your idea')
    idea_box_url = models.CharField(max_length=500, default='/contact_sales/')
    idea_box_color = ColorField(default='#FFFFFF')

    # ---- Shop home (/shop/) ----
    shop_meta_title = models.CharField(max_length=255, default='Shop designs | Studio Mohar', blank=True)
    shop_meta_description = models.TextField(max_length=1000, default='', blank=True)
    hero_eyebrow = models.CharField(max_length=100, default='The holiday drop', blank=True)
    hero_title = models.CharField(max_length=200, default='Matching family tees, with your name on them')
    hero_button_text = models.CharField(max_length=60, default='Shop Christmas designs', blank=True)
    hero_button_url = models.CharField(max_length=500, default='/shop/designs/', blank=True)
    hero_image = models.ImageField(upload_to='shop/settings', max_length=1000, blank=True, null=True)
    hero_color = ColorField(default='#A63A35')

    occasions_heading = models.CharField(max_length=100, default='Shop by occasion')
    best_sellers_heading = models.CharField(max_length=100, default='Best sellers')
    new_heading = models.CharField(max_length=100, default='New this week')
    designs_per_row = models.PositiveIntegerField(default=4, help_text="How many designs show in Best sellers / New this week")

    group_card_eyebrow = models.CharField(max_length=100, default='For clubs, teams and events', blank=True)
    group_card_title = models.CharField(max_length=200, default='Ordering 20+ or have your own design?')
    group_card_text = models.TextField(default='Use any design here or bring your own. Free mockup, group pricing, and 15% off 50+ pieces with Wait & Save.', blank=True)
    group_card_button1 = models.CharField(max_length=60, default='Get a group quote', blank=True)
    group_card_button1_url = models.CharField(max_length=500, default='/contact_sales/', blank=True)
    group_card_button2 = models.CharField(max_length=60, default='Explore custom merch', blank=True)
    group_card_button2_url = models.CharField(max_length=500, default='/all_products/', blank=True)

    idea_card_eyebrow = models.CharField(max_length=100, default="Don't see the one?", blank=True)
    idea_card_title = models.CharField(max_length=200, default="Send us your idea, we'll make it yours")
    idea_card_text = models.TextField(default='Share a sketch, a screenshot or a design you love. We recreate it with your names and send you a free mockup.', blank=True)

    # ---- All occasions page (/shop/occasions/) ----
    occasions_page_title = models.CharField(max_length=200, default='Shop by occasion')
    occasions_page_intro = models.TextField(default='Designs for every celebration. Most can carry your names.', blank=True)
    occasions_meta_title = models.CharField(max_length=255, default='Shop by occasion | Studio Mohar', blank=True)
    occasions_meta_description = models.TextField(max_length=1000, default='', blank=True)

    # ---- All designs page (/shop/designs/) ----
    designs_page_title = models.CharField(max_length=200, default='All designs')
    designs_page_intro = models.TextField(default='Ready-made designs, printed in-house. Many can carry your names.', blank=True)
    designs_meta_title = models.CharField(max_length=255, default='All designs | Studio Mohar', blank=True)
    designs_meta_description = models.TextField(max_length=1000, default='', blank=True)

    # ---- Group quote strip (occasion + listing pages) ----
    strip_title = models.CharField(max_length=200, default='Ordering for the whole group?')
    strip_text = models.CharField(max_length=255, default='20+ shirts or your own design: get a group quote and a free mockup.', blank=True)
    strip_link_text = models.CharField(max_length=60, default='Get a group quote')
    strip_url = models.CharField(max_length=500, default='/contact_sales/')

    # ---- Design page ----
    personalize_heading = models.CharField(max_length=100, default='Personalize & choose sizes')
    sizes_heading = models.CharField(max_length=100, default='Choose sizes')
    details_heading = models.CharField(max_length=100, default='Fabric, fit & size chart')

    class Meta:
        verbose_name = 'Shop settings'
        verbose_name_plural = '28. Shop - Page & Menu Settings'

    def __str__(self):
        return 'Shop page & menu settings'

    @classmethod
    def load(cls):
        return cls.objects.first() or cls()


class ShopFeature(models.Model):
    """Trust strip items (Printed in Mississauga, Free GTA shipping, ...)."""
    ICONS = (
        ('fa-location-dot', 'Location pin'),
        ('fa-clock', 'Clock'),
        ('fa-truck', 'Truck'),
        ('fa-circle-check', 'Check'),
        ('fa-star', 'Star'),
        ('fa-heart', 'Heart'),
        ('fa-leaf', 'Leaf'),
        ('fa-gift', 'Gift'),
    )
    settings = models.ForeignKey(ShopSettings, on_delete=models.CASCADE, related_name='features')
    icon = models.CharField(max_length=40, choices=ICONS, default='fa-circle-check')
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=150, default='', blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class ProductPageSettings(models.Model):
    """Editable texts for the All products page, the styles pages and the product
    (style) page. Use ProductPageSettings.load() - it never writes to the database."""
    # All products page
    all_title = models.CharField(max_length=200, default='All products')
    all_intro = models.TextField(default='Premium blanks, printed or embroidered in-house in Mississauga.', blank=True)
    all_meta_title = models.CharField(max_length=255, default='Complete Custom Apparel Collection | Shirts, Hoodies, Bags & More | Studio Mohar', blank=True)
    all_url = models.SlugField(max_length=120, default='', blank=True, verbose_name='All products URL',
                               help_text='e.g. "products" makes the page /products/. Empty = /all_products/. The old /all_products/ link then redirects here.')
    all_meta_description = models.TextField(max_length=1000, default="Explore Studio Mohar's complete custom apparel collection. Premium t-shirts, hoodies, polos, hats, bags & more. Multiple decoration techniques & bulk discounts available.", blank=True)
    styles_label = models.CharField(max_length=40, default='styles', help_text="Shown under a category name: '4 styles'")

    # Product page
    includes_text = models.CharField(max_length=200, default='Includes a full-colour front print')
    delivery_min_days = models.PositiveIntegerField(default=5, help_text="Arrives = today + this many days ...")
    delivery_max_days = models.PositiveIntegerField(default=10, help_text="... to today + this many days")
    delivery_region = models.CharField(max_length=60, default='Ontario', blank=True)
    delivery_note = models.CharField(max_length=200, default='Need it sooner? Rush is available at checkout.', blank=True)
    request_colour_text = models.CharField(max_length=100, default="Don't see your colour?", blank=True)
    request_colour_link = models.CharField(max_length=60, default='Request a colour')
    request_colour_url = models.CharField(max_length=500, default='/contact_sales/')
    quote_link_text = models.CharField(max_length=100, default='Quote extra prints & embroidery')
    cta_text = models.CharField(max_length=60, default='Add your design')
    details_heading = models.CharField(max_length=100, default='Product details')
    size_chart_heading = models.CharField(max_length=100, default='Size chart')

    # "Upload inspo & we'll recreate it" card + popup (All products / styles pages)
    inspo_on = models.BooleanField(default=True, help_text="Show the Upload inspo card")
    inspo_card_text = models.CharField(max_length=120, default="Upload inspo & we'll recreate it.")
    inspo_title1 = models.CharField(max_length=120, default="Describe What You'd Like to See")
    inspo_help1 = models.CharField(max_length=255, default="Our Art team can do anything! We'll send you a free mockup and then revise it till you love it.", blank=True)
    inspo_placeholder = models.CharField(max_length=255, default="e.g. Turn our logo into a vintage badge, change the blue colour to dark yellow.", blank=True)
    inspo_error = models.CharField(max_length=200, default="Please share your ideas, & we'll bring your vision to life!")
    inspo_title2 = models.CharField(max_length=120, default="Where should we send the mockup?")
    inspo_help2 = models.CharField(max_length=255, default="We'll email it within one business day. This won't take more than two mins.", blank=True)
    inspo_button = models.CharField(max_length=60, default="Submit Request")
    inspo_note = models.CharField(max_length=120, default="Free mockup within one business day", blank=True)
    inspo_success = models.CharField(max_length=255, default="Thanks! Our art team is on it. Your free mockup will be in your inbox soon.")

    class Meta:
        verbose_name = 'Product page settings'
        verbose_name_plural = '29. Products - Page Settings'

    def __str__(self):
        return 'Product page settings'

    @classmethod
    def load(cls):
        return cls.objects.first() or cls()

    def all_products_url(self):
        return f'/{self.all_url}/' if self.all_url else '/all_products/'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.all_url and (slug_is_taken_by_site(self.all_url) or Category.objects.filter(slug=self.all_url).exists()):
            raise ValidationError({'all_url': f'"/{self.all_url}/" is already a page or a category URL - please choose another.'})


class InspoRequest(models.Model):
    """'Upload inspo & we'll recreate it' requests from the product pages."""
    STATUS = (('new', 'New'), ('mockup_sent', 'Mockup sent'), ('done', 'Done'))
    image = models.FileField(upload_to='inspo_requests/', max_length=1000, blank=True, null=True)
    description = models.TextField()
    email = models.EmailField()
    page = models.CharField(max_length=300, default='', blank=True, help_text="Page the request was sent from")
    status = models.CharField(max_length=20, choices=STATUS, default='new')
    staff_note = models.TextField(default='', blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Inspo request'
        verbose_name_plural = '30. Products - Inspo Requests'

    def __str__(self):
        return f'{self.email} ({self.created:%Y-%m-%d})'


class ProductTrustItem(models.Model):
    """Small icons under 'Add your design' (Canadian-owned, Premium blanks...)."""
    ICONS = (
        ('maple', 'Maple leaf'),
        ('award', 'Award ribbon'),
        ('fa-truck', 'Truck'),
        ('fa-circle-check', 'Check'),
        ('fa-location-dot', 'Location pin'),
        ('fa-clock', 'Clock'),
    )
    settings = models.ForeignKey(ProductPageSettings, on_delete=models.CASCADE, related_name='trust_items')
    icon = models.CharField(max_length=30, choices=ICONS, default='fa-circle-check')
    text = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


def personalization_as_html(raw):
    """Render the stored personalization JSON ([{label, value}, ...]) for admin/emails.
    Values are typed by customers, so they are always escaped."""
    import json
    from django.utils.html import format_html_join
    if not raw:
        return '-'
    try:
        rows = json.loads(raw)
    except (TypeError, ValueError):
        return '-'
    rows = [(r.get('label', ''), r.get('value', '')) for r in rows if isinstance(r, dict) and r.get('value')]
    return format_html_join(mark_safe('<br>'), '<b>{}:</b> {}', rows) if rows else '-'




