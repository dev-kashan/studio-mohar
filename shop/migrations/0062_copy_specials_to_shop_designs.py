"""
Copy the existing "special" products (Products without a mockup template)
into the new ShopDesign model. The original Product rows are kept and
become each design's base_product, so old orders, carts and stock keep
working exactly as before.
"""
from django.db import migrations
from django.utils.html import strip_tags
from django.utils.text import slugify


def unique_slug(ShopDesign, base):
    base = (base or 'design')[:200]
    slug, n = base, 2
    while ShopDesign.objects.filter(slug=slug).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


def copy_specials(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    ProductAttribute = apps.get_model('shop', 'ProductAttribute')
    ProductPreview = apps.get_model('shop', 'ProductPreview')
    ShopDesign = apps.get_model('shop', 'ShopDesign')
    ShopDesignColor = apps.get_model('shop', 'ShopDesignColor')
    ShopDesignImage = apps.get_model('shop', 'ShopDesignImage')

    for p in Product.objects.filter(customize_mockup_template__isnull=True):
        if ShopDesign.objects.filter(base_product=p).exists():
            continue  # already copied

        attrs = list(ProductAttribute.objects.filter(product=p).order_by('id'))
        prices = [a.discount_price if a.discount_price and a.discount_price > 0 else a.price for a in attrs]
        prices = [x for x in prices if x]

        design = ShopDesign.objects.create(
            name=p.product_name or f'Design {p.product_id}',
            slug=unique_slug(ShopDesign, p.Slug or slugify(p.product_name or '')),
            base_product=p,
            short_description=strip_tags(p.short_desc or '').strip()[:255],
            description=p.desc or '',
            price=min(prices) if prices else 0,
            is_best_seller=bool(p.is_best_seller),
            live=p.live,
            meta_title=p.Meta_title or '',
            meta_description=p.Meta_description or '',
        )

        seen = set()
        for i, a in enumerate(attrs):
            if not a.color_id or a.color_id in seen:
                continue
            seen.add(a.color_id)
            image = a.image if a.image and 'noperview' not in str(a.image) else None
            if not image:
                continue  # hero image is required; admin can add it later
            ShopDesignColor.objects.create(
                design=design, color_id=a.color_id, hero_image=image,
                is_default=(len(seen) == 1), order=i,
            )

        for prev in ProductPreview.objects.filter(product=p).order_by('order'):
            if prev.image:
                ShopDesignImage.objects.create(design=design, image=prev.image, order=prev.order)


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0061_shop_designs'),
    ]

    operations = [
        migrations.RunPython(copy_specials, migrations.RunPython.noop),
    ]
