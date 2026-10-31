"""
Seed the Shop settings record, the trust strip and the occasions shown in the
client's Shop design, so the admin starts filled in. Everything stays editable.
Skips anything that already exists.
"""
from django.db import migrations

FEATURES = [
    ('fa-location-dot', 'Printed in Mississauga', 'In-house, by our team'),
    ('fa-clock', 'Ready in 5-10 days', 'Order early for the holidays'),
    ('fa-truck', 'Free GTA shipping', 'Free across Canada over $250'),
    ('fa-circle-check', 'No minimum', 'Order one, or fifty'),
]

OCCASIONS = [
    # name, slug, subtitle, card colour, text tone
    ('Christmas & New Year', 'christmas-new-year', 'Family and friends, matching', '#A63A35', 'light'),
    ('Bridal party', 'bridal-party-shirts', 'Bride, bridesmaids, bachelorette', '#F1E5E1', 'dark'),
    ('Birthdays', 'birthday-shirts', 'Milestones and birthday crews', '#EFEBE4', 'dark'),
    ('Teams & events', 'teams-events', 'Tournaments, trips, conferences', '#2F4A36', 'light'),
    ('Family & festive', 'family-festive', 'Eid, Diwali, reunions', '#1F1F1D', 'light'),
    ('Funny', 'funny-shirts', 'Wear it as is', '#E8EBE3', 'dark'),
]


def seed(apps, schema_editor):
    ShopSettings = apps.get_model('shop', 'ShopSettings')
    ShopFeature = apps.get_model('shop', 'ShopFeature')
    Occasion = apps.get_model('shop', 'Occasion')

    settings = ShopSettings.objects.first() or ShopSettings.objects.create()
    if not settings.features.exists():
        for i, (icon, title, subtitle) in enumerate(FEATURES):
            ShopFeature.objects.create(settings=settings, icon=icon, title=title, subtitle=subtitle, order=i)

    for i, (name, slug, subtitle, color, tone) in enumerate(OCCASIONS):
        if not Occasion.objects.filter(slug=slug).exists():
            Occasion.objects.create(
                name=name, slug=slug, subtitle=subtitle, card_color=color, text_tone=tone,
                order=i, page_title=f'{name} shirts' if not name.endswith('s') else name,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0063_shop_settings'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
