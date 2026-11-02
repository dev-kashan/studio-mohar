"""
Fill the new product-page fields for existing data:
- a URL (slug) for every category, and a unique slug per product inside its category
- a colour family guessed from each colour's name (editable in the admin)
- the Product page settings record with the three trust items from the client's design
"""
from django.db import migrations
from django.utils.text import slugify

RESERVED = {'admin', 'jet', 'media', 'static', 'shop', 'design', 'cart', 'checkout', 'blog', 'login', 'logout',
            'search', 'products', 'all_products', 'specials', 'category', 'service', 'flash-sale'}

FAMILY_WORDS = [
    ('black', ['black', 'charcoal black', 'jet']),
    ('white', ['white', 'ivory', 'snow']),
    ('grey', ['grey', 'gray', 'heather', 'charcoal', 'ash', 'silver', 'slate']),
    ('red', ['red', 'maroon', 'burgundy', 'cardinal', 'wine', 'crimson', 'scarlet']),
    ('pink', ['pink', 'blush', 'rose', 'fuchsia', 'magenta']),
    ('orange', ['orange', 'coral', 'rust', 'peach']),
    ('yellow', ['yellow', 'gold', 'mustard', 'lemon']),
    ('green', ['green', 'olive', 'forest', 'kelly', 'mint', 'sage', 'teal', 'army']),
    ('blue', ['blue', 'navy', 'royal', 'denim', 'sky', 'aqua', 'cyan', 'turquoise']),
    ('purple', ['purple', 'violet', 'lavender', 'plum', 'lilac']),
    ('brown', ['brown', 'chocolate', 'toast', 'coffee', 'tan', 'mocha']),
    ('natural', ['natural', 'beige', 'cream', 'sand', 'khaki', 'oatmeal', 'bone']),
]


def guess_family(name):
    n = (name or '').lower()
    for family, words in FAMILY_WORDS:
        if any(w in n for w in words):
            return family
    return ''


def seed(apps, schema_editor):
    Category = apps.get_model('shop', 'Category')
    Product = apps.get_model('shop', 'Product')
    Color = apps.get_model('shop', 'Color')
    Settings = apps.get_model('shop', 'ProductPageSettings')
    Trust = apps.get_model('shop', 'ProductTrustItem')

    used = set(Category.objects.exclude(slug__isnull=True).exclude(slug='').values_list('slug', flat=True))
    for c in Category.objects.filter(slug__isnull=True) | Category.objects.filter(slug=''):
        base = slugify(c.category_name) or f'category-{c.category_id}'
        if base in RESERVED:
            base = f'{base}-apparel'
        slug, n = base, 2
        while slug in used:
            slug = f'{base}-{n}'
            n += 1
        used.add(slug)
        c.slug = slug
        c.save(update_fields=['slug'])

    for cat_id in Product.objects.values_list('categories_id', flat=True).distinct():
        seen = set()
        for p in Product.objects.filter(categories_id=cat_id).order_by('product_id'):
            base = p.Slug or slugify(p.product_name or '') or f'style-{p.product_id}'
            slug, n = base, 2
            while slug in seen:
                slug = f'{base}-{n}'
                n += 1
            seen.add(slug)
            if slug != p.Slug:
                Product.objects.filter(pk=p.pk).update(Slug=slug)

    for col in Color.objects.filter(family=''):
        fam = guess_family(col.color_name)
        if fam:
            Color.objects.filter(pk=col.pk).update(family=fam)

    s = Settings.objects.first() or Settings.objects.create()
    if not s.trust_items.exists():
        for i, (icon, text) in enumerate([('maple', 'Canadian-Owned and Operated'),
                                          ('award', 'Premium Blanks Only'),
                                          ('fa-truck', 'Free shipping over $250')]):
            Trust.objects.create(settings=s, icon=icon, text=text, order=i)


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0066_product_pages'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
