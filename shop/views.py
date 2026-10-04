from django.contrib.messages.api import error
from django.http import request
from django.shortcuts import redirect, render, HttpResponse, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from math import ceil
from django.http import HttpResponse
import json
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Min,Max
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.db.models import Q , Sum
from django.db.models import Avg
import itertools
from django.core.mail import send_mail 
from django.utils.html import strip_tags
from newecom.settings import DEFAULT_FROM_EMAIL , EMAIL_HOST_USER , DELIVERY_ORAGIN , WITH_IN_CITY_DELIVERY_CHARGES , OUT_OF_CITY_DELIVERY_CHARGES ,MEDIA_ROOT
from django.core import serializers
from .cate_context import category_context
from django.db.models import Count, Q
from django.db import transaction
from decimal import Decimal, InvalidOperation

from PIL import Image
import io
import base64

from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt

from django.core.files.base import ContentFile
import stripe
from django.conf import settings

from django.core.exceptions import ObjectDoesNotExist
from datetime import date, timedelta
import random
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY
DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
EMAIL_HOST_USER = settings.EMAIL_HOST_USER

def base64_to_image_file(base64_str, filename):
    """Convert base64 data:image string to Django ContentFile"""
    if not base64_str or not base64_str.startswith('data:image'):
        return None
    format, imgstr = base64_str.split(';base64,')
    ext = format.split('/')[-1]  # e.g. 'png' or 'jpeg'
    return ContentFile(base64.b64decode(imgstr), name=f"{filename}.{ext}")


# Create your views here.

def basic(request):

    # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])
     
    data = {}
    data['allcategory']= allcategory 


    return render(request, 'shop/basic.html' , data)



def basetoimg(data , filename):
    filedate = datetime.now().time().microsecond
    logo_split_base64 = data.split(';base64,')
    logo_extention = logo_split_base64[0].split(':image/')[1]
    logo_binary_data = base64.b64decode(logo_split_base64[1])
    logo_PIL = Image.open(io.BytesIO(logo_binary_data))
    logo_PIL.save(f"{MEDIA_ROOT}/shop/images/{filename}{filedate}.{logo_extention}")
    logo_link = f"/shop/images/{filename}{filedate}.{logo_extention}"
    return logo_link


def search_suggestion(request):
    if 'term' in request.GET:
        search = request.GET.get('term')
        keywords =  KeyWord.objects.filter(KeyWords__icontains=search).order_by('?')[0:4]

        # qs = BrandCategory.objects.filter(Brand_Category_Title__icontains=request.GET.get('term') , status="Active" ).order_by('?')[0:4]
        # Brands = Brand.objects.filter(Brand_name__icontains=request.GET.get('term') , status="Active").order_by('?')[0:2]

        # qs_len = len(qs)
        # Brands_len = len(Brands)
        # keywords_len = len(keywords)
        # sum_b_qs_len = qs_len + Brands_len + keywords_len
        # sum_b_qs_len_minus =  16 - sum_b_qs_len

        product = Product.objects.filter(Q(brand__icontains=search) | Q(product_name__icontains=search) | Q(product_model__icontains=search) | Q(product_code__icontains=search) | Q(categories__category_name__icontains=search) | Q(categories__category__icontains=search) | Q(desc__icontains=search) | Q(product_id__icontains=search) , live=True).order_by('?')[0:8]
        
        
        # Brand_SubCategory = SubCategory.objects.filter(Subcategory_name__contains=request.GET.get('term') , status="Active")[0:12]
        # Brand_Category = Category.objects.filter(category_name__contains=request.GET.get('term') , status="Active")[0:12]
        
        titles = list()

        for kw in keywords:
            titles.append(['', f'<i class="fa fa-search"></i> {kw.KeyWords}', kw.KeyWords])

        for i in product:
            titles.append([str(i.productattribute_set.first().image)  , i.product_name[0:30], i.product_name] )

        # for bc in qs:
        #     titles.append([str(bc.Brand_Category_Image) , bc.Brand_Category_Title , bc.Brand_Category_Title])

            
        # for b in Brands:
        #     titles.append([str(b.Brand_logo)  , b.Brand_name,  b.Brand_name] )
        
           

        # titles = [product.title for product in qs]
        return JsonResponse({'results':titles})




ACCESS_CODES = {}

def retrieve_design_view(request):
    """
    Step 1 — User enters email or design ID.
    If it's an email, send a 6-digit access code.
    If it's a design ID, allow direct access (optional).
    """
    if request.method == "POST":
        query = request.POST.get("query", "").strip()

        # If it's an email
        if "@" in query:
            designs_exist = SavedDesign.objects.filter(email__iexact=query).exists()
            if not designs_exist:
                return render(request, "shop/retrieve_design.html", {
                    "error": "No designs found for this email."
                })

            # Generate and store code
            code = str(random.randint(100000, 999999))
            ACCESS_CODES[query] = {
                "code": code,
                "created_at": timezone.now()
            }

            # Send email with the code
            subject = "Your Design Access Code"
            context = {"code": code}
            html_content = render_to_string("shop/design_access_code.html", context)
            text_content = f"Your design access code is {code}. It will expire in 30 minutes."

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to=[query],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            return render(request, "shop/enter_code.html", {"email": query, "sent": True})

        # If user entered a numeric design ID (direct access)
        elif query.isdigit():
            designs = SavedDesign.objects.filter(Q(id=query)).order_by("-id")
            if not designs:
                return render(request, "shop/retrieve_design.html", {"error": "Design not found."})
            return render(request, "shop/retrieve_designs.html", {"designs": designs})

        else:
            return render(request, "shop/retrieve_design.html", {"error": "Enter a valid email or ID."})

    return render(request, "shop/retrieve_design.html")

def verify_design_code(request):
    """
    Step 2 — Verify code sent to email and show designs if valid.
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        code = request.POST.get("code", "").strip()

        stored = ACCESS_CODES.get(email)
        if not stored:
            return render(request, "shop/enter_code.html", {"email": email, "error": "No code found. Please request again."})

        # Check code and expiry
        if stored["code"] == code and timezone.now() - stored["created_at"] < timedelta(minutes=30):
            designs = SavedDesign.objects.filter(email__iexact=email).order_by("-id")
            return render(request, "shop/retrieve_designs.html", {"designs": designs})
        else:
            return render(request, "shop/enter_code.html", {"email": email, "error": "Invalid or expired code."})

    return redirect("retrieve_design_request")


def products(request, id):
    mockup_products = Product.objects.filter(customize_mockup_template__isnull=False, live=True, categories__category_id=id)
    total_count = mockup_products.count()

    # Example: if you’re showing 16 per page (can adjust later)
    showing_start = 1
    showing_end = min(16, total_count)

    context = {
        'mockup_products': mockup_products[:16],  # optional slice
        'total_count': total_count,
        'showing_start': showing_start,
        'showing_end': showing_end,
    }

    return render(request, 'shop/products.html', context)

def all_products(request):
    is_sustainable = request.GET.get('is_sustainable', '')
    is_best_seller = request.GET.get('is_best_seller', '')

    # Base query
    mockup_products = Product.objects.filter(customize_mockup_template__isnull=False, live=True)

    # Apply filters based on GET parameters
    if is_best_seller == 'Yes':
        mockup_products = mockup_products.filter(is_best_seller=True)
    if is_sustainable == 'Yes':
        mockup_products = mockup_products.filter(is_sustainable=True)

    total_count = mockup_products.count()

    # Pagination or visible range
    showing_start = 1
    showing_end = min(16, total_count)

    context = {
        'mockup_products': mockup_products[:16],
        'total_count': total_count,
        'showing_start': showing_start,
        'showing_end': showing_end,
    }

    return render(request, 'shop/all_products.html', context)


def get_apparel_for(request, id):
    apparel = GetApparelFor.objects.get(id=id)
    params = {
        'i':apparel
    }
    return render(request, 'shop/get_apparel_for.html', params)

def product_detail(request, id):

    
    product = get_object_or_404(Product, product_id=id)
    competitors = CompetitorProduct.objects.filter(main_product=product)

    # get distinct color options for this product
    filter_color = (
        ProductAttribute.objects
        .filter(product=product)
        .values('color__color_name', 'color__color_code', 'color__id')
        .annotate(
            Avalaible=Sum('Availibility'),
            image=Min('image'),
            attr_id=Min('id'),
            discount_price=Min('discount_price'),
            price=Min('price'),
        )
        .order_by('color__color_name')
    )
    related_prod = {}
    if not product.customize_mockup_template:
        related_prod = (
            Product.objects
            .filter(categories=product.categories, customize_mockup_template__isnull=True, live=True)
            .exclude(product_id=product.product_id)
        )
    # else:
    #     related_prod = (
    #         Product.objects
    #         .filter(categories=product.categories, customize_mockup_template__isnull=False, live=True)
    #         .exclude(product_id=product.product_id)
    #     )


    context = {
        'product': product,
        'related_prod': related_prod,
        'filter_color': filter_color,
        'competitors':competitors
    }

    

    


    return render(request, 'shop/product_detail.html', context)


def service_detail(request):
    return render(request, 'shop/service_detail.html')

def service_detail(request, id):
    service = get_object_or_404(Service, id=id)
    services = Service.objects.all().exclude(id=service.id)
    sections = service.servicesection_set.all()  # all related sections
    return render(request, 'shop/service_detail.html', {
        'service': service,
        'services': services,
        'sections': sections
    })

def contact_sales(request):
    products = Product.objects.all()
    if request.method == "POST":
        name = request.POST['name']
        product = request.POST['product']
        email = request.POST['email']
        phone = request.POST['phone']
        compony_name = request.POST['compony_name']
        message_text = request.POST['message']
        quantity = request.POST['quantity']
        image = request.FILES.get('image', None)

        # Save to DB
        ContactSales.objects.create(
            name=name,
            product=product,
            phone=phone,
            compony_name=compony_name,
            email=email,
            message=message_text,
            file=image,
            quantity=quantity,
        )

        # Email context
        context = {
            'name': name,
            'email': email,
            'phone': phone,
            'compony_name': compony_name,
            'product': product,
            'quantity': quantity,
            'message': message_text,
            'primary_color': '#7E9479',
        }

        # Render HTML email template
        html_content = render_to_string('shop/emails/contact_sales_email.html', context)
        subject_user = "Sales Contact Confirmation"
        subject_admin = f"New Sales Contact Submission from {name}"

        # Send email to user
        email_user = EmailMultiAlternatives(
            subject=subject_user,
            body="Thank you for contacting us regarding a product.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_user.attach_alternative(html_content, "text/html")
        email_user.send()

        # Send email to admin(s)
        admin_emails = settings.SALES_EMAILS
        email_admin = EmailMultiAlternatives(
            subject=subject_admin,
            body=f"New sales contact submission from {name}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails
        )
        email_admin.attach_alternative(html_content, "text/html")
        email_admin.send()

        messages.success(request, "Your Details have been Successfully Submitted. Thank You!")
        return redirect("/")

    return render(request, 'shop/contact_sales.html', {'products': products})


def our_story(request):
    story = AboutUs.objects.prefetch_related('sections').first()
    sections = story.sections.all() if story else []
    return render(request, 'shop/our_story.html', {
        'story': story,
        'sections': sections
    })

def specials(request):
    # Dynamic filter options with counts
    products = (
        Product.objects.filter(live=True, customize_mockup_template__isnull=True)
        .prefetch_related("productattribute_set", "productattribute_set__color", "productattribute_set__size")
        .select_related("categories")
        .order_by("-pub_date")
    )
    # Distinct categories with product count
    categories = (
        products.values('categories__category_id', 'categories__category_name')
        .annotate(count=Count('product_id'))
        .order_by('categories__category_name')
    )

    # Distinct colors with product count
    colors = (
        ProductAttribute.objects.filter(product__in=products)
        .values('color__id', 'color__color_name', 'color__color_code')
        .annotate(count=Count('id'))
        .order_by('color__color_name')
    )

    # Distinct sizes with product count
    sizes = (
        ProductAttribute.objects.filter(product__in=products)
        .values('size__id', 'size__Size_name')
        .annotate(count=Count('id'))
        .order_by('size__Size_name')
    )

    print('okkkk', len(products))

    context = {
        'products': products,
        'products_cout': len(products),
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'total_count': products.count(),
    }

    # Render your main templat
    return render(request, 'shop/specials.html', context)

def filter_products(request):
    colors = request.GET.getlist('colors[]')
    sizes = request.GET.getlist('sizes[]')
    categories = request.GET.getlist('categories[]')

    # Start with all live products
    products = Product.objects.filter(
        live=True,
        customize_mockup_template__isnull=True
    ).distinct().order_by('-pub_date')

    # Apply filters dynamically
    if categories:
        products = products.filter(categories__category_id__in=categories)

    if colors or sizes:
        attrs = ProductAttribute.objects.all()

        if colors:
            attrs = attrs.filter(color__id__in=colors)
        if sizes:
            attrs = attrs.filter(size__id__in=sizes)

        products = products.filter(product_id__in=attrs.values('product_id')).distinct()

    # Prepare JSON response
    product_list = []
    for product in products:
        attrs = ProductAttribute.objects.filter(product=product)

        # First attribute for image and price fallback
        first_attr = attrs.first()
        image_url = (
            first_attr.image.url
            if first_attr and first_attr.image
            else product.printed_image.url
        )

        # Collect UNIQUE color variants
        color_variants = []
        seen_colors = set()

        for pa in attrs:
            if pa.color and pa.color.id not in seen_colors:
                seen_colors.add(pa.color.id)
                color_variants.append({
                    'id': pa.color.id,
                    'name': pa.color.color_name,
                    'code': pa.color.color_code or '#000000',
                    'image': pa.image.url if pa.image else image_url,
                })

        product_list.append({
            'id': product.product_id,
            'name': product.product_name,
            'slug': product.Slug,
            'price': first_attr.price if first_attr else 0,
            'discount_price': first_attr.discount_price if first_attr else 0,
            'image': image_url,
            'category_name': product.categories.category_name if product.categories else '',
            'colors': color_variants,
        })

        

    return JsonResponse({'products': product_list, 'products_cout':len(product_list)})


    # return JsonResponse({'products': product_list, 'count': len(product_list)})

 

def contact_support(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        Order_ID = request.POST['Order_ID']
        compony_name = request.POST['compony_name']
        message_text = request.POST['message']
        # quantity = request.POST['quantity']
        image = request.FILES.get('image', None)

        # Save to DB
        ContactSupport.objects.create(
            name=name,
            phone=phone,
            order_id=Order_ID,
            compony_name=compony_name,
            email=email,
            message=message_text,
            file=image,
            # quantity=quantity,
        )

        # Prepare email context
        context = {
            'name': name,
            'email': email,
            'phone': phone,
            'compony_name': compony_name,
            'message': message_text,
            # 'quantity': quantity,
            'primary_color': '#7E9479',
        }

        # Render HTML email template
        html_content = render_to_string('shop/emails/contact_support_email.html', context)
        subject = "Contact Support Confirmation"

        # Send to user
        email_user = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for contacting us.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_user.attach_alternative(html_content, "text/html")
        email_user.send()

        # Send to admin
        admin_email = settings.SUPPORT_EMAILS  # or a separate admin email
        email_admin = EmailMultiAlternatives(
            subject=f"New Contact Support Submission from {name}",
            body=f"New contact support submission from {name}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_email
        )
        email_admin.attach_alternative(html_content, "text/html")
        email_admin.send()

        messages.success(request, "Your Details have been Successfully Submitted. Thank You!")
        return redirect("/")

    return render(request, 'shop/contact_support.html')


def index(request):


    i_posts = InstagramPost.objects.all() 


    mockup_products = Product.objects.filter(customize_mockup_template__isnull=False, live=True)
    # print(MyCategory,"cacaca")



    



    params = {'mockup_products':mockup_products, 'i_posts':i_posts}

    return render(request, 'shop/new_index.html', params)




# product details
def product(request, myid):
    try:

        product = Product.objects.get(product_id=myid , live=True)
    except:
        return redirect('/')
    
    filter_size = ProductAttribute.objects.filter(product=product).values('size__Size_name' , 'size__id').annotate(Avalaible=Sum('Availibility')).distinct().order_by('-Avalaible')
    filter_color = ProductAttribute.objects.filter(product=product).values('color__color_name' , 'color__color_code' , 'color__id').annotate(Avalaible=Sum('Availibility')).distinct().order_by('Avalaible')
   


    related_products=Product.objects.filter(categories=product.categories , live=True  ,flash_sale=False).annotate(avg_review=Avg('rates__rating')).exclude(product_id=myid).order_by('?')[:4]
    flash_sale = Product.objects.filter(live=True ,  show_in_slider=False ,flash_sale=True).annotate(avg_review=Avg('rates__rating')).order_by("?")[:2]
    show_in_modal = Product.objects.all().order_by('?')[:5]

    avg_rating = Rating.objects.filter(product=product).aggregate(avg_rating=Avg('rating'))
    total_rating = Rating.objects.filter(product=product).count()
    

     # # get user ip_address
    def get_ip(request):
        address = request.META.get('HTTP_X_FORWARDED_FOR')
        if address:
            ip = address.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    ip=get_ip(request)
    u=ProductView(device_ip=ip , product=product)
    result = ProductView.objects.filter(Q(device_ip__icontains=ip ,product=product))
    if len(result)== 1:
        pass
    elif len(result)>1:
        pass
    else:
        u.save()
        
    
     # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])


    context = {

        'total_rating':total_rating, 'avg_rating':avg_rating,'flash_sale':flash_sale , 'show_in_modal':show_in_modal, 'related_products': related_products ,'allcategory': allcategory, 'i' :product ,
        'filter_size':filter_size,
        'filter_color':filter_color
    }

    return render(request, 'shop/product.html', context)



# def checkout(request):
    
#     if request.method == 'POST':
#         # user = request.user
#         product_item = request.POST.get('itmejson', '')
#         convrtintodictpeoduct = json.loads(product_item)
#         total = request.POST.get('total', '')
#         name = request.POST.get('name', '') + " " + \
#             request.POST.get('lname', '')
#         email = request.POST.get('email', '')
#         address = request.POST.get('address', '') + \
#             " " + request.POST.get('address2', '')
#         city = request.POST.get('city', '')
#         country = request.POST.get('country', '')
#         zip_code = request.POST.get('zip_code', '')
#         phone = request.POST.get('phone', '')
#         promo = request.POST.get('promo', '')
#         Home_or_office = request.POST.get('home_office', '')
#         Payment_method = request.POST.get('payment_method', '')
#         tracker_json = request.POST.get('itmejson', '')

#         if request.user.is_authenticated:
#             order = Order( user=request.user, name=name, email=email, address=address, city=city, country=country,
#                         zip_code=zip_code, phone=phone, product_item=convrtintodictpeoduct, total=total , promo=promo , Home_or_office=Home_or_office ,
#                         Payment_method=Payment_method , tracker_json=tracker_json)
#         else:
#             order = Order(name=name, email=email, address=address, city=city, country=country,
#                         zip_code=zip_code, phone=phone, product_item=convrtintodictpeoduct, total=total , promo=promo , Home_or_office=Home_or_office ,
#                         Payment_method=Payment_method , tracker_json=tracker_json)
            
#         order.save()
#         update = OrderUpdate(order_id=order.order_id,
#                              update_desc="The order has been placed")
#         update.save()
#         id = order.order_id
#         msg = messages.success(request, f'Thank You "{name}" | Your Order Has Been Successfully Placed Your Tracking Code is "{id}"')

#         return render(request, 'shop/checkout.html', {'id': id, 'name': name.upper(), 'phone' : phone , 'address' : address, 'phone' : phone,  'msg': msg})

    
#     # category
#     allcategory = []
#     velu = Category.objects.values('category')
#     catefilter = {itme['category'] for itme in velu}
#     for cat in catefilter:
#         prod = Category.objects.filter(category=cat , active=True)
#         n = len(prod)
#         nSlides = n//4 + ceil((n/4)-(n//4))
#         allcategory.append([prod, range(1, nSlides), nSlides])


#     context = {

#          'allcategory':allcategory
#     }
#     return render(request, 'shop/checkout.html', context)


@transaction.atomic
def checkout(request):
    session_id = request.session.session_key
    if not session_id:
        request.session.save()
        session_id = request.session.session_key

    cart_items = GuestCart.objects.filter(session_id=session_id).select_related(
        'product_attr__product'
    ).order_by('-id')

    # Calculate total quantities
    for item in cart_items:
        total_qty = item.cart_items.aggregate(total=models.Sum('quantity'))['total'] or 0
        item.total_qty = total_qty

    if not cart_items.exists():
        return redirect('/cart/')

    if request.method == 'POST':
        data = request.POST
        name = f"{data.get('name', '')} {data.get('lname', '')}".strip()
        email = data.get('email', '')
        company = data.get('Company', '')
        address = f"{data.get('address', '')} {data.get('address2', '')}".strip()
        city = data.get('city', '')
        country = data.get('country', '')
        province_id = data.get('province', '')
        zip_code = data.get('zip_code', '')
        phone = data.get('phone', '')
        special_instructions = data.get('sp_intrac', '')
        coupon_code = data.get('coupon', '')
        shipping_type = data.get('shipping_type', 'standard')

        subtotal_inp = Decimal(data.get('subtotal_inp', '0'))
        grand_total_inp = Decimal(data.get('grand_total_inp', '0'))
        delivery_cost_inp = Decimal(data.get('delivery_cost_inp', '0'))
        discount_amo = Decimal(data.get('discount_amo') or '0')
        tax_amount_inp = Decimal(data.get('tax_amount_inp') or '0')

        # Create Stripe Checkout session
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'price_data': {
                            'currency': 'cad',
                            'product_data': {'name': f'Order from {name}'},
                            'unit_amount': int(grand_total_inp * 100),
                        },
                        'quantity': 1,
                    }
                ],
                payment_intent_data={
                    'capture_method': 'manual',  # 👈 HOLD payment
                    'metadata': {
                        'session_id': session_id,
                        'email': email,
                        'name': name,
                    }
                },
                success_url=request.build_absolute_uri('/stripe/success/'),
                cancel_url=request.build_absolute_uri('/stripe/cancel/'),
            )

            # Save data in session
            request.session['checkout_data'] = {
                'name': name,
                'email': email,
                'company': company,
                'address': address,
                'city': city,
                'country': country,
                'province': province_id,
                'zip_code': zip_code,
                'phone': phone,
                'special_instructions': special_instructions,
                'coupon': coupon_code,
                'shipping_type': shipping_type,

                # money → string
                'subtotal': str(subtotal_inp),
                'tax': str(tax_amount_inp),
                'grand_total': str(grand_total_inp),
                'delivery_cost': str(delivery_cost_inp),
                'discount_amount': str(discount_amo),
            }
            request.session.save()

            return redirect(checkout_session.url, code=303)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    # GET request
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat, active=True)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allcategory.append([prod, range(1, nSlides), nSlides])

    coutries = Country.objects.all()
    province = Province.objects.all()

    pricing = DesignPricing.objects.first()

    context = {
        'allcategory': allcategory,
        'cart_items': cart_items,
        'coutries': coutries,
        'pricing': pricing,
        'province': province,
        'stripe_public_key': settings.STRIPE_SECRET_KEY,
    }
    return render(request, 'shop/checkout.html', context)


def stripe_success(request):
    checkout_data = request.session.get('checkout_data')
    session_id = request.session.session_key

    if not checkout_data:
        return redirect('/cart/')

    try:
        get_cty = Country.objects.get(id=checkout_data['country'])
        get_Province = Province.objects.get(id=checkout_data['province'])
    except ObjectDoesNotExist:
        get_cty = None
        get_Province = None

    cart_items = GuestCart.objects.filter(session_id=session_id)
    if not cart_items.exists():
        return redirect('/cart/')

    # ---- Base delivery days ----
    base_delivery_days = 7  # default
    postal_code = checkout_data.get('zip_code', '').strip().upper()
    shipping_type = checkout_data.get('shipping_type', '').lower()

    # ---- Postal code adjustments ----
    if postal_code:
        if postal_code[0] in ['L', 'M']:
            base_delivery_days -= 1
        if len(postal_code) > 1 and postal_code[1].isdigit() and postal_code[1] == '0':
            base_delivery_days += 3

    # ---- Total quantity calculation ----
    total_qty = sum(
        sum(i.quantity for i in item.cart_items.all())
        for item in cart_items
    )

    if total_qty > 100:
        base_delivery_days += 2
        extra_100s = (total_qty - 100) // 100
        base_delivery_days += 0.5 * extra_100s
    elif total_qty > 50:
        base_delivery_days += 1

    # ---- Check stock availability ----
    for item in cart_items:
        if item.product_attr.Availibility <= 0:
            base_delivery_days += 2
            break

    # ---- Shipping type adjustments ----
    if shipping_type == 'rush':
        base_delivery_days = max(1, base_delivery_days - 3)
    elif shipping_type == 'waitsave':
        # Only valid if at least 50 pcs of one item
        # if any(sum(i.quantity for i in item.cart_items.all()) >= 50 for item in cart_items):
            base_delivery_days = 30

    estimated_delivery_date = date.today() + timedelta(days=base_delivery_days)

    # ---- Create order ----
    order = Order.objects.create(
        name=checkout_data['name'],
        email=checkout_data['email'],
        company=checkout_data['company'],
        address=checkout_data['address'],
        city=checkout_data['city'],
        zip_code=checkout_data['zip_code'],
        Country=get_cty,
        province=get_Province,
        phone=checkout_data['phone'],
        special_instructions=checkout_data['special_instructions'],
        discount_amount=checkout_data['discount_amount'],
        SubTotal=checkout_data['subtotal'],
        tax=checkout_data['tax'],
        Delivery=checkout_data['delivery_cost'],
        total=checkout_data['grand_total'],
        ship_type=checkout_data['shipping_type'],
        estimated_delivery_time=estimated_delivery_date,  # ✅ added field
    )

    # ---- Create order items ----
    for item in cart_items:
        product_attr = item.product_attr
        product = product_attr.product
        mockup = product.customize_mockup_template

        front_design_file = base64_to_image_file(item.front_image, f"front_{product.product_id}")
        back_design_file = base64_to_image_file(item.back_image, f"back_{product.product_id}")
        left_design_file = base64_to_image_file(item.left_image, f"back_{product.product_id}")
        right_design_file = base64_to_image_file(item.right_image, f"back_{product.product_id}")

        front_design_image = base64_to_image_file(item.front_design_image, f"front_design_{product.product_id}")
        back_design_image = base64_to_image_file(item.back_design_image, f"back_design_{product.product_id}")
        left_design_image = base64_to_image_file(item.left_design_image, f"back_design_{product.product_id}")
        right_design_image = base64_to_image_file(item.right_design_image, f"back_design_{product.product_id}")

        order_item = OrderItem.objects.create(
            order_by=order,
            order_item=product,
            product_name=product.product_name,
            color=str(product_attr.color) if product_attr.color else "",
            unity_price=float(item.price_of_each),
            item_total=float(item.total_price),
            image=item.front_image or '',
            Mockup=mockup,
            Order_Type='Customize' if mockup else 'Normal',
            Front_Image=front_design_file,
            Back_Image=back_design_file,
            Left_Image=left_design_file,
            Right_Image=right_design_file,

            Front_Desgin_Image=front_design_image,
            Back_Desgin_Image=back_design_image,
            Left_Desgin_Image=left_design_image,
            Right_Desgin_Image=right_design_image,
        )

        # ================= ORIGINAL UPLOADED FILES =================
        cart_uploaded_files = item.uploaded_files.all()

        for cart_file in cart_uploaded_files:
            OrderItemUploadedFile.objects.create(
                order_item=order_item,
                file=cart_file.file,        # same physical file
                filename=cart_file.filename,
                side=cart_file.side
            )

        for cart_size_item in item.cart_items.all():
            OrderItemSize.objects.create(
                order_item=order_item,
                size=cart_size_item.size,
                quantity=cart_size_item.quantity,
                unit_price=cart_size_item.unit_price,
            )

            product_attr_obj = ProductAttribute.objects.filter(
                product=product_attr.product,
                color=product_attr.color,
                size__Size_name=cart_size_item.size
            ).first()

            if product_attr_obj:
                product_attr_obj.Availibility = max(0, product_attr_obj.Availibility - cart_size_item.quantity)
                product_attr_obj.save()

    cart_items.delete()
    del request.session['checkout_data']

    ctx = category_context(request)
    symbol = ctx['currency']
    logo_layout = Layout.objects.first()

    order_items = []

    for item in order.orderitem_set.all():
        # Determine image URL
        if item.image:
            if item.image.startswith("data:"):
                # print('first if')
                image_src = request.build_absolute_uri(item.Front_Image.url)
            elif item.image.startswith("/media"):
                # print('elif')
                image_src = request.build_absolute_uri(item.image)
            else:
                # print('esle 1')
                image_src = request.build_absolute_uri(item.Front_Image.url)
        else:
            # print('esle 2')
            image_src = request.build_absolute_uri(item.Front_Image.url)

        # Sizes - assuming order_item has related sizes with quantity and unit_price
        sizes = item.sizes.all()  # Queryset

        # Calculate total for this item (sum of sizes total_price)
        item_total = sum([s.total_price for s in sizes]) if sizes else 0

        # print('images', image_src)
        # print('=======')

        order_items.append({
            "order_item": item,  # for product_name and any other field you might need
            "image": image_src,
            "Front_Image": item.Front_Image.url if item.Front_Image else '',
            "color": item.color if hasattr(item, 'color') else '',
            "sizes": sizes,
            "unity_price": item.unity_price if hasattr(item, 'unity_price') else 0,
            "item_total": item_total,
        })



    params_email = {
        'request': request,
        'order_id': order.Order_number,
        'order_items': order_items,
        'name': order.name,
        'email': order.email,
        'address': order.address,
        'city': order.city,
        'zip_code': order.zip_code,
        'province': order.province.name,
        'country': order.Country,
        'phone': order.phone,
        'SubTotal': order.SubTotal,
        'tax': order.tax,
        'Delivery': order.Delivery,
        'discount_amount': order.discount_amount,
        'total': order.total,
        'symbol': symbol,
        'date': order.created,
        'estimated_delivery_time': order.estimated_delivery_time,
        'logo': logo_layout.logo,
    }
    # for i in order.orderitem_set.all():
    #     print('image', i.image, i.Front_Image)

    html_message = render_to_string('shop/order_confirmation_mail.html', params_email)

    admin_emails = settings.ORDER_EMAILS + [order.email]

    plain_message = strip_tags(html_message)
    send_mail(
        'Order Confirmation',
        plain_message,
        DEFAULT_FROM_EMAIL,
        admin_emails,
        html_message=html_message
    )



    return render(request, 'shop/order_confirmation.html', {'order': order, 'order_items': order.orderitem_set.all()})



# --------------------------------------------------
# STRIPE WEBHOOK (called by Stripe after payment success)
# --------------------------------------------------


# def stripe_success(request):
#     return render(request, 'shop/order_confirmation.html')

def stripe_cancel(request):
    return render(request, 'shop/payment_failed.html')




def cart(request):
    session_id = request.session.session_key
    cart_items = GuestCart.objects.filter(session_id=session_id).order_by('-id')

    # cart = GuestCart.objects.last()
    # print(cart.cart_items.all())

    for item in cart_items:
        # Now we get total quantity by summing all related GuestCartItem quantities
        total_qty = item.cart_items.aggregate(total=models.Sum('quantity'))['total'] or 0
        item.total_qty = total_qty

    params = {
        "cart_items":cart_items
    }

    return render(request, 'shop/cart.html' , params)


def category(request):
   
    products = None
    categories = Category.get_all_categories()
    categoryID = request.GET.get('category')

    if categoryID:
        products = Product.get_all_products_by_categoryid(categoryID).filter(live=True).annotate(avg_review=Avg('rates__rating')).order_by('-product_id')
        # print(products , "my all products")
        # for i in products:

        
    else:
        products = Product.get_all_products().filter(live=True).annotate(avg_review=Avg('rates__rating')).order_by('-product_id')
    showprodname = Category.objects.get(category_id=categoryID)
    
    
    colors=ProductAttribute.objects.filter(product__categories__category_id=categoryID).distinct().values('color__color_name')
    sizes=ProductAttribute.objects.filter(product__categories__category_id=categoryID).distinct().values('size__Size_name')
    brands=Product.objects.filter(categories__category_id=categoryID).distinct().values('brand')
    product_name=Product.objects.filter(categories__category_id=categoryID).distinct().values('product_name')
    minMaxPrice=Product.objects.filter(categories__category_id=categoryID).values('productattribute__price').aggregate(Min('productattribute__price'),Max('productattribute__price'))
    # pageintion
    paginator = Paginator(products, per_page=40)
    page_number = request.GET.get('page' , 1)
    page_obj = paginator.get_page(page_number)

    # category
    # allcate = Store.objects.all()
    
    
    # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])



    data = {}
    data['product_name']=product_name
    data['minMaxPrice']=minMaxPrice
    data['brands']=brands
    data['colors']=colors
    data['sizes']=sizes
    data['data']= page_obj.object_list 
    # data['allcate']= allcate 
    data['categories'] = categories
    data['showprodname'] = showprodname
    data['allcategory']= allcategory 
    data['paginator'] = paginator
    data['page_obj'] = page_obj
    data['page_number'] = int(page_number)
     
    return render(request, 'shop/category.html', data)

# def allstores(request):
#     # category
#     allcate = Store.objects.filter(live=True)
    
    
#     # pageintion
#     paginator = Paginator(allcate, per_page=25)
#     page_number = request.GET.get('page' , 1)
#     page_obj = paginator.get_page(page_number)

#     # category
#     allcategory = []
#     velu = Category.objects.values('category')
#     catefilter = {itme['category'] for itme in velu}
#     for cat in catefilter:
#         prod = Category.objects.filter(category=cat , active=True)
#         n = len(prod)
#         nSlides = n//4 + ceil((n/4)-(n//4))
#         allcategory.append([prod, range(1, nSlides), nSlides])
    

#     data = {}
#     data['allcate']= page_obj.object_list  
#     data['allcategory']= allcategory 
#     data['paginator'] = paginator
#     data['page_obj'] = page_obj
#     data['page_number'] = int(page_number)
 

#     return render(request, 'shop/allstores.html', data)

# def store(request):
#     products = None
#     categories = Store.get_all_categories()
#     categoryID = request.GET.get('store')

#     if categoryID:
#         products = Product.get_all_products_by_storeid(categoryID).filter(live=True).order_by('-product_id')
#     else:
#         products = Product.get_all_products().filter(live=True).order_by('-product_id')
#     showprodname = Store.objects.get(store_id=categoryID)
    
    
#     # pageintion
#     paginator = Paginator(products, per_page= 24)
#     page_number = request.GET.get('page' , 1)
#     page_obj = paginator.get_page(page_number)

#     # category
#     allcategory = []
#     velu = Category.objects.values('category')
#     catefilter = {itme['category'] for itme in velu}
#     for cat in catefilter:
#         prod = Category.objects.filter(category=cat , active=True)
#         n = len(prod)
#         nSlides = n//4 + ceil((n/4)-(n//4))
#         allcategory.append([prod, range(1, nSlides), nSlides])


#     data = {}
#     data['products'] = page_obj.object_list 
#     data['categories'] = categories
#     data['categoryid'] = categoryID
#     data['showprodname'] = showprodname
#     data['allcategory']= allcategory 
#     data['paginator'] = paginator
#     data['page_obj'] = page_obj
#     data['page_number'] = int(page_number)

#     return render(request, 'shop/store.html', data)    


def order_tracker(request):
    # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])

    # if request.method=="POST":
    orderId = request.GET.get('orderId', None)
    phone = request.GET.get('phone', None)

    
    try:
        order = Order.objects.get(Order_number=orderId , phone=phone)
        order_msg = OrderUpdate.objects.filter(order_id=order.order_id)
    except:
        order = []
        order_msg = []
        if orderId and phone:
            messages.error(request , f'Sorry Order {orderId} is not exist please Try Again!')
            
    params = {'order':order , 'order_msg':order_msg , 'allcategory':allcategory , 'orderId':orderId , 'phone':phone}
    return render(request, 'shop/trekker.html', params)







def singup(request):
        # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])
        
    if request.method == 'POST':
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        # user exists
        if User.objects.filter(username=username).exists():
            messages.error(request, f'User "{username}" is already Exists')
            return redirect('singup')
        
        # hendle error
        if len(username) > 12:
            messages.error(
                request, 'Your User Name is too Long 12 characters ')
            return redirect('singup')

        if password != confirm_password:
            messages.error(request, 'Your Confirm Password is Not Match ')
            return redirect('singup')

        if not username.isalnum():
            messages.error(
                request, 'Please alphanumeric characters Like A-Z a-z 1-9 ')
            return redirect('singup')
        

        # user create
        myuser = User.objects.create_user(username, email, password)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()
        user = authenticate(username=username, password=password)
            
        if user is not None:
            login(request, user)
            messages.success(request, f'Thank You "{username}" | Your Account Has Been Successfully Create! ')
            return redirect('singup')
        
    else:
        prams = {'allcategory':allcategory}
        return render(request, 'shop/singup.html' , prams)


def loginsys(request):
    
    # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])
        
        
    if request.method == 'POST':
        loginusername = request.POST['loginusernameforbuy']
        loginpassword = request.POST['loginPasswordforbuy']

        user = authenticate(username=loginusername, password=loginpassword)
        if user is not None:
            login(request, user)
            messages.success(
                request, f'Thank You "{loginusername}" Your Login Has Been Successfully Done!')
            return redirect('loginsys')
        else:
            messages.error(
                request, 'You have entered an invalid username or password. please try again')
            return redirect('loginsys')

    params = {'allcategory':allcategory}
    return render(request , 'shop/login.html' , params)


def logoutsys(request):
    logout(request)
    logoutmsg = messages.success(request, 'Your Logout Has Been Success')
    return redirect('shophome' )
    


def search(request):
    query=request.GET['query']
 
    if len(query)>78:
        allprod=Product.objects.none()
    else:
        # allPostsbrand= Product.objects.filter(brand__contains=query , live=True).annotate(avg_review=Avg('rates__rating'))
        # allPostsproduct_name= Product.objects.filter(product_name__contains=query , live=True).annotate(avg_review=Avg('rates__rating'))
        # allPostssub_categories =Product.objects.filter(sub_categories__contains=query , live=True).annotate(avg_review=Avg('rates__rating'))
        # allPostsdesc =Product.objects.filter(desc__contains=query , live=True).annotate(avg_review=Avg('rates__rating'))
        # product_model = Product.objects.filter(product_model__contains=query , live=True).annotate(avg_review=Avg('rates__rating'))
        
        allprod = Product.objects.filter(Q(brand__icontains=query) | Q(product_name__icontains=query) | Q(product_model__icontains=query) | Q(product_code__icontains=query) | Q(categories__category_name__icontains=query) | Q(categories__category__icontains=query) | Q(desc__icontains=query) | Q(product_id__icontains=query) , live=True).annotate(avg_review=Avg('rates__rating'))
        
        # allprod =  allPostsbrand.union(allPostsproduct_name, allPostssub_categories , allPostsdesc , product_model, product_code)

    
    
    
    colors=ProductAttribute.objects.filter(Q(product__brand__icontains=query) | Q(product__product_name__icontains=query) | Q(product__product_model__icontains=query) | Q(product__product_code__icontains=query) | Q(product__categories__category_name__icontains=query) | Q(product__categories__category__icontains=query) | Q(product__desc__icontains=query) | Q(product__product_id__icontains=query)).distinct().values('color__color_name')

    sizes=ProductAttribute.objects.filter(Q(product__brand__icontains=query) | Q(product__product_name__icontains=query) | Q(product__product_model__icontains=query) | Q(product__product_code__icontains=query) | Q(product__categories__category_name__icontains=query) | Q(product__categories__category__icontains=query) | Q(product__desc__icontains=query) | Q(product__product_id__icontains=query)).distinct().values('size__Size_name')

    brands=Product.objects.filter(Q(brand__icontains=query) | Q(product_name__icontains=query) | Q(product_model__icontains=query) | Q(product_code__icontains=query) | Q(categories__category_name__icontains=query) | Q(categories__category__icontains=query) | Q(desc__icontains=query) | Q(product_id__icontains=query)).distinct().values('brand')

    product_name=Product.objects.filter(Q(brand__icontains=query) | Q(product_name__icontains=query) | Q(product_model__icontains=query) | Q(product_code__icontains=query) | Q(categories__category_name__icontains=query) | Q(categories__category__icontains=query) | Q(desc__icontains=query) | Q(product_id__icontains=query)).distinct().values('product_name')

    minMaxPrice=Product.objects.filter(Q(brand__icontains=query) | Q(product_name__icontains=query) | Q(product_model__icontains=query) | Q(product_code__icontains=query) | Q(categories__category_name__icontains=query) | Q(categories__category__icontains=query) | Q(desc__icontains=query) | Q(product_id__icontains=query)).values('productattribute__price').aggregate(Min('productattribute__price'),Max('productattribute__price'))
    

    # pageintion
    paginator = Paginator(allprod, per_page=40)
    page_number = request.GET.get('page' , 1)
    page_obj = paginator.get_page(page_number)


    # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])


    params={'data': page_obj.object_list, 'query': query , 'colors':colors , 'sizes' : sizes , 'product_name':product_name , 'brands':brands , 'minMaxPrice':minMaxPrice , 'allcategory':allcategory , 'paginator':paginator , 'page_obj':page_obj , 'page_number':int(page_number)}


    return render(request, 'shop/search.html', params)


def filter_data(request):
    colors=request.GET.getlist('color[]')
    product_name=request.GET.getlist('product_name[]')
    brands=request.GET.getlist('brand[]')
    sizes=request.GET.getlist('size[]')
    minPrice=request.GET['minPrice']
    maxPrice=request.GET['maxPrice']
    allProducts=Product.objects.filter(product_name__in=product_name).annotate(avg_review=Avg('rates__rating')).distinct()
    allProducts=allProducts.filter(productattribute__price__gte=minPrice).annotate(avg_review=Avg('rates__rating'))
    allProducts=allProducts.filter(productattribute__price__lte=maxPrice).annotate(avg_review=Avg('rates__rating'))
    if len(colors)>0:
        allProducts=Product.objects.filter(product_name__in=product_name , productattribute__color__color_name__in=colors).annotate(avg_review=Avg('rates__rating')).distinct()
    if len(brands)>0:
        allProducts=allProducts.filter(product_name__in=product_name  , brand__in=brands).annotate(avg_review=Avg('rates__rating')).distinct()
    if len(sizes)>0:
        allProducts=Product.objects.filter(product_name__in=product_name  , productattribute__size__Size_name__in=sizes).annotate(avg_review=Avg('rates__rating')).distinct()

    symbal = category_context(request)
    t=render_to_string('shop/filter-product.html',{'data':allProducts , "symbal":symbal['currency']})
    return JsonResponse({'data':t})


def load_more(request):
    filterlimit = int(request.GET['filterlimit'])
    currentproduct = int(request.GET['currentproduct'])
    loadproduct = Product.objects.filter( live=True , show_in_slider=False ,flash_sale=False).annotate(avg_review=Avg('rates__rating')).order_by('-product_id')[currentproduct:currentproduct+filterlimit]
    t=render_to_string('shop/filter-product.html',{'data':loadproduct})
    return JsonResponse({'data':t})



def shopping_list(request):
    return render (request , "shop/shopping_list.html")


    


def flash_sale(request):
    flash_product = Product.objects.filter(live=True , show_in_slider=False ,flash_sale=True).order_by('-product_id').annotate(avg_review=Avg('rates__rating'))
    # pageintion
    paginator = Paginator(flash_product, per_page= 40)
    page_number = request.GET.get('page' , 1)
    page_obj = paginator.get_page(page_number)

    # category
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])
        
    
       
    colors=ProductAttribute.objects.filter(product__live=True , product__show_in_slider=False , product__flash_sale=True).distinct().values('color__color_name')
    sizes=ProductAttribute.objects.filter(product__live=True , product__show_in_slider=False , product__flash_sale=True).distinct().values('size__Size_name')
    brands=Product.objects.filter(live=True , show_in_slider=False ,flash_sale=True).distinct().values('brand')
    product_name=Product.objects.filter(live=True , show_in_slider=False ,flash_sale=True).distinct().values('product_name')
    minMaxPrice=Product.objects.filter(live=True , show_in_slider=False ,flash_sale=True).values('productattribute__price').aggregate(Min('productattribute__price'),Max('productattribute__price'))

        
    data = {}
    data['product_name']=product_name
    data['minMaxPrice']=minMaxPrice
    data['brands']=brands
    data['colors']=colors
    data['sizes']=sizes
    data['data'] = page_obj.object_list 
    data['paginator'] = paginator
    data['allcategory'] = allcategory
    data['page_obj'] = page_obj
    data['page_number'] = int(page_number)
    return render(request, 'shop/flash_sale.html', data)

    
def flash_product_filter(request):
    colors=request.GET.getlist('color[]')
    product_name=request.GET.getlist('product_name[]')
    brands=request.GET.getlist('brand[]')
    sizes=request.GET.getlist('size[]')
    minPrice=request.GET['minPrice']
    maxPrice=request.GET['maxPrice']
    allProducts=Product.objects.filter(product_name__in=product_name ,live=True , show_in_slider=False ,flash_sale=True).annotate(avg_review=Avg('rates__rating')).distinct()
    allProducts=allProducts.filter(productattribute__price__gte=minPrice ,live=True , show_in_slider=False ,flash_sale=True).annotate(avg_review=Avg('rates__rating'))
    allProducts=allProducts.filter(productattribute__price__lte=maxPrice ,live=True , show_in_slider=False ,flash_sale=True).annotate(avg_review=Avg('rates__rating'))
    if len(colors)>0:
        allProducts=Product.objects.filter(product_name__in=product_name , productattribute__color__in=colors ,live=True , show_in_slider=False ,flash_sale=True).annotate(avg_review=Avg('rates__rating')).distinct()
    if len(brands)>0:
        allProducts=allProducts.filter(product_name__in=product_name  , brand__in=brands ,live=True , show_in_slider=False ,flash_sale=True).annotate(avg_review=Avg('rates__rating')).distinct()
    if len(sizes)>0:
        allProducts=Product.objects.filter(product_name__in=product_name  , productattribute__size__in=sizes ,live=True , show_in_slider=False ,flash_sale=True).annotate(avg_review=Avg('rates__rating')).distinct()
        
    t=render_to_string('shop/filter-product.html',{'data':allProducts})
    return JsonResponse({'data':t})

def service(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')+ " " + \
            request.POST.get('lname', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        messages.success(request, f'"{name}" Your Contact Has Been Successfully Send')
        return render(request, 'shop/service.html')
    
    return render (request , 'shop/service.html')


def rating(request):
    if request.method == "POST":
        star = request.POST['star']
        product_id = request.POST['product_id']
        product_name = request.POST['product_name']
        try:
            product = Product.objects.get(product_id=product_id  , live=True)
        except:
            return JsonResponse({"data":"error"})

        def get_ip(request):
            address = request.META.get('HTTP_X_FORWARDED_FOR')
            if address:
                ip = address.split(',')[-1].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip=get_ip(request)
        u=Rating(device_ip=ip , product=product , rating=star)
        result = Rating.objects.filter(Q(device_ip__icontains=ip ,product=product))
        if len(result)== 1:
            return JsonResponse({"data":"Already_Exist"})
        elif len(result)>1:
            return JsonResponse({"data":"Already_Exist"})
        else:
            u.save()

        return JsonResponse({"data":"success"})
    else:
        return JsonResponse({"data":"error"})



def customizeEditor(request , id , slug , pid):
    

    mockup_products = Product.objects.filter(customize_mockup_template__isnull=False, live=True).exclude(product_id=pid)

    attr_id = request.GET.get('attr_id')


    try:

        product = Product.objects.get(product_id=pid , live=True)
        product_attr = ProductAttribute.objects.get(id=attr_id)
        print('attr_id', attr_id, product_attr.discount_price)
        # for i in product.productattribute_set.all():
        previews = product.previews.all().order_by('order')
    except:
        product = []
        product_attr = []
        previews = []

    try:
        mockup = MockUp.objects.get(id=id)
    except:
        messages.error(request , 'Sorry mockup is Not Found')
        return redirect('/')
    
    filter_size = ProductAttribute.objects.filter(product=product).values('size__Size_name' , 'size__id').annotate(Avalaible=Sum('Availibility')).distinct().order_by('-Avalaible')
    filter_color = (
    ProductAttribute.objects
    .filter(product=product)
    .values('color__color_name', 'color__color_code', 'color__id')
    .annotate(
        Avalaible=Sum('Availibility'),
        image=Min('image'),
        price=Min('price'),
        dic_price=Min('discount_price'),
        attr_id=Min('id')  # ✅ get one attribute id per color
    )
    
)
 
    # print(filter_color)
    # print(filter_color)
    

    all_mockup = MockUp.objects.all()

    colors = Color.objects.filter(Available="Yes")
    sizes = Size.objects.filter(Available="Yes")

    sticker = UploadSticker.objects.all()
    all_type = StickerType.objects.all()        

    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {itme['category'] for itme in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat , active=True)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allcategory.append([prod, range(1, nSlides), nSlides])
    
    # all_sticker = UploadSticker
    

    params = {
        'mockup':mockup,
        'all_mockup':all_mockup,
        'color':colors,
        'size':sizes,
        'sticker':sticker,
        'code_id':id,
        'all_type':all_type,
        'i':product,
        'pid':pid,
        'allcategory':allcategory,
        'filter_size':filter_size,
        'mockup_products':mockup_products,
        'previews':previews,
        'filter_color':filter_color,
        'product_attr':product_attr,
        
    }

    pricing = DesignPricing.objects.first()

    if pricing:
        params['design_prices'] = {
            'front': float(pricing.front_price),
            'back': float(pricing.back_price),
            'left_sleeve': float(pricing.left_sleeve_price),
            'right_sleeve': float(pricing.right_sleeve_price),
            'embroidery_extra': float(pricing.embroidery_extra),
        }
    else:
        # fallback if pricing not set yet in admin
        params['design_prices'] = {
            'front': 10.0,
            'back': 10.0,
            'left_sleeve': 10.0,
            'right_sleeve': 10.0,
            'embroidery_extra': 5.0,
        }
        
    
    return render(request , 'shop/customizeEditor.html' , params)




def loadmore_sticker(request):
    get_current = request.GET['current']
    query = request.GET['query']
    category = request.GET['category']
    limit = 20

    if query and category and category != 'all':
        sticker = UploadSticker.objects.filter(Sticker_Name__icontains=query , Sticker_type__type_name__icontains=category)[int(get_current):int(get_current)+limit]
    elif query:
        sticker = UploadSticker.objects.filter(Sticker_Name__icontains=query)[int(get_current):int(get_current)+limit]
    elif category and category != 'all':
        sticker = UploadSticker.objects.filter(Sticker_type__type_name__icontains=category)[int(get_current):int(get_current)+limit]
    else:
        sticker = UploadSticker.objects.all()[int(get_current):int(get_current)+limit]
       
    t=render_to_string('shop/filter-sticker.html',{'data':sticker})
    return JsonResponse({'data':t})




def search_sticker(request):
    if request.method == 'POST':
        try:
            query = request.POST.get('query', '')
            category = request.POST.get('category', '')
    
        except:
            return JsonResponse({'error':'Error occurred while searching for sticker'})

        if query and category and category != 'all':
            find_sticker = UploadSticker.objects.filter(Sticker_Name__icontains=query , Sticker_type__type_name__icontains=category)

        elif query:
            find_sticker = UploadSticker.objects.filter(Sticker_Name__icontains=query)

        elif category and category != 'all':
            find_sticker = UploadSticker.objects.filter(Sticker_type__type_name__icontains=category)

        else:
            find_sticker = UploadSticker.objects.all()

        serialized_data = serializers.serialize('json', find_sticker)  # Serialize the queryset
        return JsonResponse({'data': serialized_data})
    
        
    else:
        return JsonResponse({'error': 'Invalid request method'})
    




def search_sticker_by_category(request):
    if request.method == 'POST':
        try:
            category = request.POST.get('category', '')
   
        except:
            return JsonResponse({'error':'Error occurred while searching for sticker'})

        if category and category != 'all':
            find_sticker = UploadSticker.objects.filter(Sticker_type__type_name__icontains=category)
            serialized_data = serializers.serialize('json', find_sticker)  # Serialize the queryset
            return JsonResponse({'data': serialized_data})
        else:
            find_sticker = UploadSticker.objects.all()
            serialized_data = serializers.serialize('json', find_sticker)  # Serialize the queryset
            return JsonResponse({'data': serialized_data})
            # else:
            #     find_sticker = UploadSticker.objects.filter(Sticker_Name__icontains=query)
            # print(find_sticker,"sticker")
     
    else:
        return JsonResponse({'error': 'Invalid request method'})
    






def check_coupon(request):
    if request.method == 'POST':
        try:
            limit = 0
            query = request.POST.get('coupon', '')
         
            find_coupon = CouponCode.objects.get(coupon_code=query ,status = 'active')
            limit = find_coupon.coupon_limit

        except CouponCode.DoesNotExist:
            return JsonResponse({'resp':'error', 'error': 'Coupon not found'})
        except Exception as e:
            return JsonResponse({'resp':'error' ,'error': f'Error: {str(e)}'})
        

        if find_coupon:
        
            if limit == 0:
                    # print("condition is ok")
                    return JsonResponse({'error': 'Coupon Expired'})
            data = {
                'formula':find_coupon.coupon_formula,
                'value':find_coupon.coupon_minus_value
            }
            return JsonResponse({'resp':'success' , 'data': data})
        else:
            return JsonResponse({'resp':'error' , 'error': 'No matching coupons found'})
    else:
        return JsonResponse({'resp':'error' , 'error': 'Invalid request method'})



# def CheckCoupon(request):

def check_available(request):
    prod_id = request.GET['prod_id']
    size = request.GET['size']
    # color = request.GET['color']

    try:
        product = Product.objects.get(product_id=prod_id)
        product_attr = ProductAttribute.objects.filter(product=product , size__Size_name=size).values('color__color_name' , 'color__color_code' , 'color__id' , 'Availibility' , 'price' , 'discount_price')
    except:
        return JsonResponse({'error': 'Coupon not found'})
    


    data = {}
    for c in list(product_attr):
        data[c['color__id']] = c


    return JsonResponse({'data':data , 'response':'Success'})





def terms_conditions(request):
    terms = TermsCondition.objects.first()
    return render(request , 'shop/terms-conditions.html', {'terms':terms})


def privacy_policy(request):
    terms = PrivacyPolicy.objects.first()
    return render(request , 'shop/privacy_policy.html', {'terms':terms})

def shipping_policy(request):
    terms = ShippingPolicy.objects.first()
    return render(request , 'shop/shipping_policy.html', {'terms':terms})




def save_design(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        name = data.get("name")
        print("RAW DATA:", data)
        print('name', name)
        tshirtColor = data.get("tshirtColor")
        attr_id = data.get("attr_id")
        front = data.get("front")
        left_sleeve = data.get("left_sleeve")
        right_sleeve = data.get("right_sleeve")
        back = data.get("back")
        product_id = data.get("product_id")
        mockup_id = data.get("mockup_id")
        try:
            get_attr = ProductAttribute.objects.get(id=attr_id)

        except:
            return redirect('/')

        get_product = Product.objects.get(product_id=product_id)
        get_mockup = MockUp.objects.get(id=mockup_id)
        # print("okkkkk", )

        design = SavedDesign.objects.create(
            email=email,
            design_name=name,
            front_json=front,
            back_json=back,
            left_sleeve=left_sleeve,
            right_sleeve=right_sleeve,
            color=get_attr.color,
            product=get_product,
            product_attr=get_attr,
            mockup=get_mockup,
        )

        # Link to design
        link = request.build_absolute_uri('/retrieve-design/')

        # Render HTML template
        subject = "Your Design is Saved | Studio Mohar"
        html_content = render_to_string("shop/emails/design_saved.html", {
            "product": get_product,
            "mockup": get_mockup,
            "link": link,
        })
        text_content = f"Your design is saved! Continue editing here: {link}"

        # Send both plain and HTML
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,  # hello@studiomohar.ca
            [email] + settings.DESIGN_SAVED_EMAILS,
            reply_to=[email],  # optional
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return JsonResponse({"success": True, 'uid':design.uid})
    return JsonResponse({"success": False}, status=400)


def load_design(request, uid):
    design = get_object_or_404(SavedDesign, uid=uid)

    # Get mockup/product again (assuming you stored pid & mockup id when saving)
    product = Product.objects.filter(product_id=design.product.product_id, live=True).first()
    mockup = MockUp.objects.filter(id=design.mockup.id).first()

    filter_size = ProductAttribute.objects.filter(product=product).values(
        'size__Size_name', 'size__id'
    ).annotate(Avalaible=Sum('Availibility')).distinct().order_by('-Avalaible')

    filter_color = ProductAttribute.objects.filter(product=product).values(
        'color__color_name', 'color__color_code', 'color__id', 'image'
    ).annotate(Avalaible=Sum('Availibility')).distinct().order_by('Avalaible')

    all_mockup = MockUp.objects.all()
    colors = Color.objects.filter(Available="Yes")
    sizes = Size.objects.filter(Available="Yes")
    sticker = UploadSticker.objects.all()
    all_type = StickerType.objects.all()

    # Same category logic
    allcategory = []
    velu = Category.objects.values('category')
    catefilter = {item['category'] for item in velu}
    for cat in catefilter:
        prod = Category.objects.filter(category=cat, active=True)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allcategory.append([prod, range(1, nSlides), nSlides])

    params = {
        'mockup': mockup,
        'all_mockup': all_mockup,
        'color': colors,
        'size': sizes,
        'sticker': sticker,
        'code_id': mockup.id if mockup else None,
        'all_type': all_type,
        'i': product,
        'pid': product.product_id if product else None,
        'allcategory': allcategory,
        'filter_size': filter_size,
        'filter_color': filter_color,
        # 👉 Add saved JSON here
        'saved_design': design,
    }

    return render(request, 'shop/customizeEditor.html', params)

def blog(request):
    categories = BlogCategory.objects.all()
    posts = BlogPost.objects.all().order_by('-date')
    return render(request, 'shop/blog.html', {'categories': categories, 'posts': posts})

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    related_post = BlogPost.objects.filter(category__id=post.category.id).exclude(id=post.id)[:3]
    return render(request, 'shop/blog_detail.html', {'post': post, 'related_post':related_post})



def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key

    # ✅ TEXT DATA (FormData)
    data = request.POST

    try:
        get_attr = ProductAttribute.objects.get(id=data.get("attr_id"))
    except ProductAttribute.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid attribute ID"}, status=400)

    # ✅ JSON FIELDS INSIDE FORMDATA
    images = json.loads(data.get("mockup_images", "{}"))
    design_only_images = json.loads(data.get("design_only_images", "{}"))
    canvas_json = json.loads(data.get("canvas_json", "{}"))

    quantities = json.loads(data.get("quantities", "{}")) if data.get("quantities") else {}

    try:
        each_price = Decimal(str(data.get("each_price", "0")).replace(",", "").strip())
        estimated_total = Decimal(str(data.get("estimatedTotal", "0")).replace(",", "").strip())
    except (InvalidOperation, TypeError):
        return JsonResponse({"success": False, "error": "Invalid price format"}, status=400)

    # ================= CART =================
    existing_cart = GuestCart.objects.filter(
        session_id=session_id,
        product_attr=get_attr
    ).first()

    if existing_cart:
        cart = existing_cart
        cart.save_design_uid = data.get("uid", "")
        cart.front_image = images.get("front")
        cart.back_image = images.get("back")
        cart.left_image = images.get("left_sleeve")
        cart.right_image = images.get("right_sleeve")
        cart.front_design_image = design_only_images.get("front")
        cart.back_design_image = design_only_images.get("back")
        cart.left_design_image = design_only_images.get("left_sleeve")
        cart.right_design_image = design_only_images.get("right_sleeve")
        cart.price_of_each = each_price
        cart.total_price = estimated_total
        cart.save()

        cart.cart_items.all().delete()
    else:
        cart = GuestCart.objects.create(
            session_id=session_id,
            product_attr=get_attr,
            save_design_uid=data.get("uid", ""),
            front_image=images.get("front"),
            back_image=images.get("back"),
            left_image=images.get("left_sleeve"),
            right_image=images.get("right_sleeve"),
            front_design_image=design_only_images.get("front"),
            back_design_image=design_only_images.get("back"),
            left_design_image=design_only_images.get("left_sleeve"),
            right_design_image=design_only_images.get("right_sleeve"),
            # price_of_each=each_price,
            total_price=estimated_total,
        )

    # ================= SIZES =================
    # total_cart_price = Decimal("0")
    for item in quantities:
        size = item["size"]
        qty = int(item["qty"])
        unit_price = Decimal(str(item["priceEach"]))
        item_total = unit_price * qty
        # total_cart_price += item_total

        GuestCartItem.objects.create(
            cart=cart,
            size=size,
            quantity=qty,
            unit_price=unit_price,
            total_price=item_total
        )

    # cart.total_price = total_cart_price
    # cart.save()


    # ================= FILES =================
    uploaded_files = request.FILES.getlist("uploaded_files")
    uploaded_files_meta = request.POST.getlist("uploaded_files_meta")

    for idx, file in enumerate(uploaded_files):
        meta = json.loads(uploaded_files_meta[idx])

        # Example save (adjust to your model)
        CartUploadedFile.objects.create(
            cart=cart,
            file=file,
            side=meta.get("side"),
            filename=meta.get("filename")
        )

    return JsonResponse({"success": True})


def add_to_cart_special(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key

    # Parse JSON body
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    attr_id = data.get("attr_id")
    if not attr_id:
        return JsonResponse({"success": False, "error": "Missing attribute ID"}, status=400)

    try:
        get_attr = ProductAttribute.objects.get(id=attr_id)
    except ProductAttribute.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid attribute ID"}, status=400)

    # Images and quantities
    images = data.get("images", {})  # already a dict
    quantities = data.get("quantities", {})

    try:
        each_price = Decimal(str(data.get("each_price", "0")).replace(",", "").strip())
        estimated_total = Decimal(str(data.get("estimatedTotal", "0")).replace(",", "").strip())
    except (InvalidOperation, TypeError):
        return JsonResponse({"success": False, "error": "Invalid price format"}, status=400)

    # Check for existing cart
    existing_cart = GuestCart.objects.filter(session_id=session_id, product_attr=get_attr).first()

    if existing_cart:
        cart = existing_cart
        cart.front_image = images.get("front")
        cart.price_of_each = each_price
        cart.total_price = estimated_total
        cart.save()
        cart.cart_items.all().delete()
    else:
        cart = GuestCart.objects.create(
            session_id=session_id,
            product_attr=get_attr,
            front_image=images.get("front"),
            # price_of_each=each_price,
            total_price=estimated_total,
        )

    # Create cart items
    for item in quantities:
        size = item["size"]
        qty = int(item["qty"])
        unit_price = Decimal(str(item["priceEach"]))
        item_total = unit_price * qty
        # total_cart_price += item_total

        GuestCartItem.objects.create(
            cart=cart,
            size=size,
            quantity=qty,
            unit_price=unit_price,
            total_price=item_total
        )

    return JsonResponse({"success": True})


@csrf_exempt
def delete_cart_item(request, cart_id):
    if request.method == "POST":
        try:
            cart_item = get_object_or_404(GuestCart, id=cart_id)
            cart_item.delete()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=405)

def get_sizes_for_color(request, product_id):
    color_id = request.GET.get('color_id')
    color_code = request.GET.get('color_code')  # optional fallback
    attr_id = request.GET.get('attr_id')  # optional fallback
    attributes = None

    get_attr = ProductAttribute.objects.get(id=attr_id)

    # ✅ Priority: color_id (preferred)
    if color_id:
        attributes = ProductAttribute.objects.filter(
            product_id=product_id,
            color_id=color_id
        ).select_related('size')

    # 🟡 Fallback: color_code (only if color_id missing)
    elif color_code:
        attributes = ProductAttribute.objects.filter(
            product_id=product_id,
            color__color_code__iexact=color_code.strip()
        ).select_related('size')

    # ❌ Neither provided
    else:
        return JsonResponse({'sizes': []})

    # ✅ Build response safely
    # print('attributes', attributes.image)
    size_data = [
        {
            'id': attr.id,
            'size': getattr(attr.size, 'Size_name', ''),  # safe fallback
            'availibility': attr.Availibility or 0,
            'image': attr.image.url if attr.image else '',
            'price': attr.discount_price,
            'discount_price': attr.discount_price,
            'max_qty': attr.Max_Qty or 0,
        }
        for attr in attributes
    ]

    return JsonResponse({'sizes': size_data, 'attr_id':get_attr.id})


# def filter_products(request):
#     # Accept both categories[]=1 style and categories=1,2 style
#     cat_ids = request.GET.getlist("categories[]") or request.GET.getlist("categories")
#     color_ids = request.GET.getlist("colors[]") or request.GET.getlist("colors")
#     size_ids = request.GET.getlist("sizes[]") or request.GET.getlist("sizes")

#     qs = Product.objects.filter(live=True)

#     if cat_ids:
#         qs = qs.filter(categories_id__in=cat_ids)

#     # If color/size filters are present, constrain via ProductAttribute
#     if color_ids or size_ids:
#         attrs = ProductAttribute.objects.filter(product__in=qs)
#         if color_ids:
#             attrs = attrs.filter(color_id__in=color_ids)
#         if size_ids:
#             attrs = attrs.filter(size_id__in=size_ids)
#         qs = qs.filter(productattribute__in=attrs).distinct()

#     qs = qs.prefetch_related("productattribute_set", "productattribute_set__color", "productattribute_set__size")

#     html = render_to_string("shop/partials/products_grid.html", {"products": qs}, request=request)
#     return JsonResponse({"html": html, "count": qs.count()})

