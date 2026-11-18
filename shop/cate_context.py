
from .models import *

def category_context(request):
    session_id = request.session.session_key
    if not session_id:
        request.session.save()
        session_id = request.session.session_key

    if request.user.is_authenticated:
        cart_count = GuestCart.objects.filter(session_id=session_id).count()
    else:
        cart_count = 0 
    Cate = Category.objects.filter(active=True)
    currency = 'C$'
    delivery = 10
    text_print = 300
    free_delivery_amount = 4500
    all_mockup_prod = Product.objects.filter(product_type='custom', live=True)
    all_services = Service.objects.all()
    all_apparel_for = GetApparelFor.objects.all()
    mockup_products = Product.objects.filter(product_type='custom', live=True)
    first_mockup_product = Product.objects.filter(
    product_type='custom',
    live=True
).first()

    layout = Layout.objects.first()  # get the first layout record
    
    pricing = DesignPricing.objects.first()


    context = {'Cate':Cate, 'first_mockup_product':first_mockup_product , 'currency':currency , 'delivery':delivery , 'text_print':text_print , 'mackup_btn':all_mockup_prod , 'free_delivery_amount':free_delivery_amount, 'all_services':all_services, 'mockup_products':mockup_products, 'all_apparel_for':all_apparel_for, 'layout': layout,
        'features': layout.features.all() if layout else [],
        'clients': layout.clients.all() if layout else [],
        'faqs': layout.faqs.all() if layout else [], 'cart_count':cart_count, 'design_pricing':pricing}


    # print('okkkk', pricing.front_price)

    if pricing:
        context['design_prices'] = {
            'front': float(pricing.front_price),
            'back': float(pricing.back_price),
            'left_sleeve': float(pricing.left_sleeve_price),
            'right_sleeve': float(pricing.right_sleeve_price),
            'embroidery_extra': float(pricing.embroidery_extra),
        }
    else:
        # fallback if pricing not set yet in admin
        context['design_prices'] = {
            'front': 10.0,
            'back': 10.0,
            'left_sleeve': 10.0,
            'right_sleeve': 10.0,
            'embroidery_extra': 5.0,
        }
    
    # New header menus: "Shop designs" occasions + editable menu texts
    context['shop_settings'] = ShopSettings.load()
    context['shop_menu_occasions'] = Occasion.objects.filter(live=True, show_in_menu=True)
    # All products page URL (custom URL from the admin, or /all_products/)
    context['all_products_url'] = ProductPageSettings.load().all_products_url()

    # Instant Quote: size boxes follow the admin Size order (short labels like the grid: Small -> S)
    from .templatetags.size_filters import clean_sizes
    quote_sizes = []
    for name in Size.objects.values_list('Size_name', flat=True):  # Size Meta ordering = admin order
        label = clean_sizes(name)
        if label and label not in quote_sizes:
            quote_sizes.append(label)
    context['quote_size_order'] = quote_sizes

    # mockup = MockUp.objects.filter(Active='Yes')
    # for m in mockup
    return context