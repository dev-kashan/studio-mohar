from django import template

register = template.Library()

MAP = {
    "Small": "S",
    "Medium": "M",
    "Large": "L",
    "XS": "XS",
    "XL": "XL",
    "2XL": "2XL",
    "3XL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
}

@register.filter
def clean_sizes(size_string):
    if not size_string:
        return ""

    items = size_string.split(",")

    short = []
    for x in items:
        x = x.strip()
        short.append(MAP.get(x, x[:1].upper()))

    # remove duplicates while keeping order
    seen = []
    for s in short:
        if s not in seen:
            seen.append(s)

    return ", ".join(seen)
