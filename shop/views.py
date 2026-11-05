from django.contrib.messages.api import error
from django.http import request
from django.shortcuts import redirect, render, HttpResponse, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.views.decorators.http import require_POST
import os
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
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from PIL import Image
import io
import base64

from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

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
    # Categories now have custom URLs: /<slug>/
    category = Category.objects.filter(category_id=id).first()
    if category and category.slug:
        return redirect(category.get_absolute_url(), permanent=True)

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

# all_products() moved to the "PRODUCT PAGES" section at the end of this file
# (best seller / sustainable filters removed as per the brief).


def get_apparel_for(request, id):
    # Old number URL -> permanent redirect to the custom URL /get-apparel-for/<slug>/
    apparel = get_object_or_404(GetApparelFor, id=id)
    if apparel.slug:
        return redirect(apparel.get_absolute_url(), permanent=True)
    return get_apparel_for_page(request, apparel=apparel)


def get_apparel_for_page(request, slug=None, apparel=None):
    apparel = apparel or get_object_or_404(GetApparelFor, slug=slug)
    params = {
        'i':apparel,
        'page_html': apparel.uploaded_html(),   # "Upload HTML" from the admin replaces the article
    }
    return render(request, 'shop/get_apparel_for.html', params)

@ensure_csrf_cookie  # Add to Cart posts to /add-to-cart-special/ with fetch; new visitors have no csrftoken cookie otherwise
def product_detail(request, id):

    
    product = get_object_or_404(Product, product_id=id)

    # Old Shop (specials) products now live as ShopDesigns -> permanent redirect
    if not product.customize_mockup_template:
        shop_design = ShopDesign.objects.filter(base_product=product, live=True, colors__isnull=False).first()
        if shop_design:
            return redirect('shop_design_detail', slug=shop_design.slug, permanent=True)
    # Design Lab products now have custom URLs: /<category>/<style>/
    elif product.live and product.categories and product.categories.slug and product.Slug:
        return redirect(product.get_absolute_url(), permanent=True)

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
            .prefetch_related('productattribute_set__color')
        )
        # One dot per colour (attributes repeat a colour once per size); the template used the
        # colour NAME as a CSS colour, so "Cardinal Red" etc. showed no dot at all
        related_prod = list(related_prod)
        for rp in related_prod:
            seen, dots = set(), []
            for attr in rp.productattribute_set.all():
                code = attr.color.color_code if attr.color else ''
                if code and code not in seen:
                    seen.add(code)
                    dots.append(code)
            rp.rp_dots = dots[:5]
            rp.rp_more = max(0, len(dots) - 5)
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
    # Old number URL -> permanent redirect to the custom URL /services/<slug>/
    service = get_object_or_404(Service, id=id)
    if service.slug:
        return redirect(service.get_absolute_url(), permanent=True)
    return service_page(request, service=service)


def service_page(request, slug=None, service=None):
    service = service or get_object_or_404(Service, slug=slug)
    services = Service.objects.all().exclude(id=service.id)
    sections = service.servicesection_set.all()  # all related sections
    return render(request, 'shop/service_detail.html', {
        'service': service,
        'services': services,
        'sections': sections,
        'page_html': service.uploaded_html(),   # "Upload HTML" from the admin replaces the sections
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


@ensure_csrf_cookie  # first page most visitors see: set the csrftoken cookie so later fetch() posts work
def index(request):


    i_posts = InstagramPost.objects.all() 


    # Homepage "Our Products" shows the first 3: lowest style order first, mixed across categories
    mockup_products = (Product.objects.filter(customize_mockup_template__isnull=False, live=True, categories__active=True)
                       .order_by('display_order', 'categories__display_order', 'product_id'))
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

        shop_design = item.shop_design  # set only for Shop page designs
        if mockup:
            order_type = 'Customize'
        elif shop_design:
            order_type = 'Shop Design'
        else:
            order_type = 'Normal'

        order_item = OrderItem.objects.create(
            order_by=order,
            order_item=product,
            product_name=shop_design.name if shop_design else product.product_name,
            color=str(product_attr.color) if product_attr.color else "",
            unity_price=float(item.price_of_each),
            item_total=float(item.total_price),
            image=item.front_image or '',
            Mockup=mockup,
            Order_Type=order_type,
            shop_design=shop_design,
            personal_image=item.personal_image or None,  # same physical file as the cart upload
            design_details=item.design_details,  # Design Lab: print / embroidery, texts, notes
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
                personalization=cart_size_item.personalization,
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



@ensure_csrf_cookie  # editor posts to /save-design/ and /add-to-cart/ via fetch; fresh/incognito visitors have no csrftoken cookie otherwise
def customizeEditor(request , id , slug , pid):
    # The new Design Lab (/design-lab/) replaces this editor. The site-wide "Start
    # designing" links all point at the first Design Lab product, so those open the
    # product picker; links for a specific product open that product in the editor.
    first = _design_lab_products().order_by('product_id').first()
    if first and pid == first.product_id and 'sizes' not in request.GET:
        return redirect('/design-lab/')
    lab_url = f'/design-lab/?product={pid}'
    if request.GET.get('color_id', '').isdigit():
        lab_url += f"&color={request.GET['color_id']}"
    if request.GET.get('sizes'):
        from urllib.parse import quote
        lab_url += '&sizes=' + quote(request.GET['sizes'])
    return redirect(lab_url)

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
        get_attr = ProductAttribute.objects.filter(id=attr_id).first()
        get_product = Product.objects.filter(product_id=product_id).first()
        get_mockup = MockUp.objects.filter(id=mockup_id).first()
        if not (get_attr and get_product and get_mockup):
            return JsonResponse({"success": False, "error": "Invalid product, attribute or mockup"}, status=400)
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
        # Design is already saved; an SMTP hiccup must not block add-to-cart
        try:
            msg.send()
        except Exception as e:
            print("save_design email failed:", e)

        return JsonResponse({"success": True, 'uid':design.uid})
    return JsonResponse({"success": False}, status=400)


@ensure_csrf_cookie
def load_design(request, uid):
    design = get_object_or_404(SavedDesign, uid=uid)
    # Designs saved in the new Design Lab open there; old ones keep the old editor
    if _dl_saved_sides(design) is not None:
        return redirect(f'/design-lab/?design={design.uid}')

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
    return render(request, 'shop/blog_detail.html', {'post': post, 'related_post':related_post,
                                                     'page_html': post.uploaded_html()})



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


# Shop designs: personalization upload limits
SHOP_DESIGN_MAX_IMAGE_MB = 15
SHOP_DESIGN_MAX_ROWS = 100
SHOP_DESIGN_MAX_QTY = 999
SHOP_DESIGN_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def add_to_cart_shop_design(request):
    """
    Add a Shop page design to the cart (multipart POST).
      design_id, color_id    - the design and the chosen colour
      rows                   - JSON: [{"size": "M", "qty": 2, "texts": {"<text_field_id>": "Sara"}}, ...]
      personal_image (file)  - optional customer photo, used on every piece
    The price always comes from the design (fixed), never from the browser.
    Each add creates its own cart line, because every line can carry different text.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    design_id = request.POST.get("design_id", "")
    color_id = request.POST.get("color_id", "")
    if not design_id.isdigit() or not color_id.isdigit():
        return JsonResponse({"success": False, "error": "Invalid data."}, status=400)

    design = ShopDesign.objects.filter(id=int(design_id), live=True).select_related("base_product").first()
    if not design:
        return JsonResponse({"success": False, "error": "This design is not available."}, status=400)

    design_color = design.colors.filter(color_id=int(color_id)).select_related("color").first()
    if not design_color:
        return JsonResponse({"success": False, "error": "Please choose a colour."}, status=400)

    # Sizes available for this colour on the base product
    color_attrs = ProductAttribute.objects.filter(product=design.base_product, color=design_color.color).select_related("size")
    sizes_available = {a.size.Size_name for a in color_attrs if a.size}
    product_attr = color_attrs.first()
    if not product_attr:
        return JsonResponse({"success": False, "error": "This colour is not available right now."}, status=400)

    try:
        rows = json.loads(request.POST.get("rows", "[]"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid data."}, status=400)
    if not isinstance(rows, list) or not rows or len(rows) > SHOP_DESIGN_MAX_ROWS:
        return JsonResponse({"success": False, "error": "Please add at least one size."}, status=400)

    text_fields = list(design.text_fields.all()) if design.wants_text else []

    clean_rows = []
    for n, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            return JsonResponse({"success": False, "error": "Invalid data."}, status=400)
        size = str(row.get("size", "")).strip()
        if size not in sizes_available:
            return JsonResponse({"success": False, "error": f"Row {n}: please choose a size."}, status=400)
        try:
            qty = int(row.get("qty", 0))
        except (TypeError, ValueError):
            qty = 0
        if qty < 1 or qty > SHOP_DESIGN_MAX_QTY:
            return JsonResponse({"success": False, "error": f"Row {n}: quantity must be between 1 and {SHOP_DESIGN_MAX_QTY}."}, status=400)

        texts = row.get("texts") or {}
        if not isinstance(texts, dict):
            texts = {}
        personalization = []
        for tf in text_fields:
            value = str(texts.get(str(tf.id), "")).strip()
            if tf.required and not value:
                return JsonResponse({"success": False, "error": f"Row {n}: {tf.label} is required."}, status=400)
            if len(value) > tf.max_length:
                return JsonResponse({"success": False, "error": f"Row {n}: {tf.label} can be up to {tf.max_length} letters."}, status=400)
            personalization.append({"label": tf.label, "value": value})
        clean_rows.append((size, qty, personalization))

    personal_image = request.FILES.get("personal_image") if design.wants_image else None
    if personal_image:
        if personal_image.size > SHOP_DESIGN_MAX_IMAGE_MB * 1024 * 1024:
            return JsonResponse({"success": False, "error": f"Image must be under {SHOP_DESIGN_MAX_IMAGE_MB} MB."}, status=400)
        # Only real raster photos. SVG/HTML could carry scripts that would run
        # when the team opens the file from the admin, so they are refused.
        try:
            with Image.open(personal_image) as img:
                img_format = (img.format or "").upper()
                img.verify()
        except Exception:
            img_format = ""
        if img_format not in SHOP_DESIGN_IMAGE_FORMATS:
            return JsonResponse({"success": False, "error": "Please upload a JPG, PNG, WEBP or GIF photo."}, status=400)
        personal_image.seek(0)

    if not request.session.session_key:
        request.session.create()

    unit_price = design.price
    total_qty = sum(q for _, q, _ in clean_rows)

    with transaction.atomic():
        cart = GuestCart.objects.create(
            session_id=request.session.session_key,
            product_attr=product_attr,
            shop_design=design,
            front_image=design_color.hero_image.url,
            back_image=design_color.back_image.url if design_color.back_image else "",
            price_of_each=unit_price,
            total_price=unit_price * total_qty,
            personal_image=personal_image,
        )
        for size, qty, personalization in clean_rows:
            GuestCartItem.objects.create(
                cart=cart,
                size=size,
                quantity=qty,
                unit_price=float(unit_price),
                personalization=json.dumps(personalization) if any(p["value"] for p in personalization) else "",
            )

    return JsonResponse({"success": True, "cart_id": cart.id})


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



# =====================================================================
# SHOP PAGES (2026 redesign): /shop/, /shop/occasions/, /shop/designs/,
# /shop/<occasion>/ and /shop/design/<slug>/
# Products here are ShopDesign records (see models.py), not Product.
# =====================================================================

SHOP_SORTS = (
    ('best', 'Best selling'),
    ('new', 'Newest'),
    ('price_asc', 'Price: low to high'),
    ('price_desc', 'Price: high to low'),
)


def _shop_designs():
    """Live designs that have at least one colour/hero image."""
    return (
        ShopDesign.objects.filter(live=True, colors__isnull=False)
        .distinct()
        .select_related('base_product')
        .prefetch_related('colors__color', 'gallery', 'text_fields', 'occasions')
    )


def _with_card_data(designs):
    """Attach the main/hover images and colour count used by the design cards."""
    designs = list(designs)
    for d in designs:
        colors = list(d.colors.all())
        main = colors[0] if colors else None
        d.card_main = main.hero_image.url if main else ''
        alt = ''
        if main and main.back_image:
            alt = main.back_image.url
        elif len(colors) > 1:
            alt = colors[1].hero_image.url
        else:
            gallery = list(d.gallery.all())
            if gallery:
                alt = gallery[0].image.url
        d.card_alt = alt
        d.color_count = len(colors)
    return designs


def _sort_designs(qs, sort):
    if sort == 'new':
        return qs.order_by('-created')
    if sort == 'price_asc':
        return qs.order_by('price', 'order')
    if sort == 'price_desc':
        return qs.order_by('-price', 'order')
    return qs.order_by('-is_best_seller', 'order', '-created')


def shop_home(request):
    shop = ShopSettings.load()
    per_row = shop.designs_per_row or 4
    designs = _shop_designs()
    context = {
        'shop': shop,
        'features': shop.features.all() if shop.pk else [],
        'occasions': Occasion.objects.filter(live=True, show_on_shop_page=True),
        'best_sellers': _with_card_data(designs.filter(is_best_seller=True).order_by('order', '-created')[:per_row]),
        'new_designs': _with_card_data(designs.order_by('-created')[:per_row]),
    }
    return render(request, 'shop/shop_home.html', context)


def shop_occasions(request):
    occasions = Occasion.objects.filter(live=True).annotate(
        design_count=Count('designs', filter=Q(designs__live=True), distinct=True)
    )
    return render(request, 'shop/shop_occasions.html', {'shop': ShopSettings.load(), 'occasions': occasions})


def _shop_listing(request, occasion=None):
    """Shared listing for an occasion page and the all-designs page (GET filters)."""
    base = _shop_designs()
    if occasion:
        base = base.filter(occasions=occasion)

    q = request.GET.get('q', '').strip()[:100]
    personalizable = request.GET.get('personalizable') == '1'
    best = request.GET.get('best') == '1'
    color = request.GET.get('color', '')
    size = request.GET.get('size', '').strip()[:50]
    sort = request.GET.get('sort', 'best')
    if sort not in dict(SHOP_SORTS):
        sort = 'best'

    # Filter options come from everything on this page (before filtering)
    color_options = (
        Color.objects.filter(shopdesigncolor__design__in=base).distinct().order_by('color_name')
    )
    size_options = list(
        ProductAttribute.objects.filter(product__shop_designs__in=base, size__isnull=False)
        .values_list('size__Size_name', flat=True).distinct().order_by('size__id')
    )
    size_options = list(dict.fromkeys(size_options))  # keep order, drop repeats

    designs = base
    if q:
        designs = designs.filter(Q(name__icontains=q) | Q(short_description__icontains=q) | Q(occasions__name__icontains=q))
    if personalizable:
        designs = designs.filter(is_personalizable=True)
    if best:
        designs = designs.filter(is_best_seller=True)
    if color.isdigit():
        designs = designs.filter(colors__color_id=int(color))
    if size:
        designs = designs.filter(base_product__productattribute__size__Size_name=size)
    designs = _with_card_data(_sort_designs(designs.distinct(), sort))

    return {
        'shop': ShopSettings.load(),
        'occasion': occasion,
        'designs': designs,
        'color_options': color_options,
        'size_options': size_options,
        'sorts': SHOP_SORTS,
        'f': {'q': q, 'personalizable': personalizable, 'best': best, 'color': color, 'size': size, 'sort': sort},
        'filtered': bool(q or personalizable or best or color or size),
    }


def shop_designs(request):
    return render(request, 'shop/shop_listing.html', _shop_listing(request))


def shop_occasion(request, slug):
    occasion = get_object_or_404(Occasion, slug=slug, live=True)
    context = _shop_listing(request, occasion)
    context['faqs'] = occasion.faqs.all()
    context['more_occasions'] = Occasion.objects.filter(live=True).exclude(id=occasion.id)[:4]
    return render(request, 'shop/shop_listing.html', context)


@ensure_csrf_cookie  # the page posts to /add-to-cart-shop-design/ with fetch
def shop_design_detail(request, slug):
    design = get_object_or_404(_shop_designs(), slug=slug)
    colors = list(design.colors.all())

    # Sizes per colour, from the base product's variations
    sizes_by_color = {}
    for a in ProductAttribute.objects.filter(product=design.base_product, size__isnull=False).select_related('size').order_by('size__id'):
        sizes = sizes_by_color.setdefault(a.color_id, [])
        if a.size.Size_name not in sizes:
            sizes.append(a.size.Size_name)

    gallery = list(design.gallery.all())
    text_fields = list(design.text_fields.all()) if design.wants_text else []

    # Breadcrumb: the occasion the visitor came from, else the first one
    occasions = list(design.occasions.filter(live=True))
    crumb = next((o for o in occasions if o.slug == request.GET.get('from')), occasions[0] if occasions else None)

    page_data = {
        'designId': design.id,
        'price': float(design.price),
        'wantsImage': design.wants_image,
        'colors': [{
            'id': c.color_id,
            'name': c.color.color_name,
            'code': c.color.color_code,
            'hero': c.hero_image.url,
            'back': c.back_image.url if c.back_image else '',
            'sizes': sizes_by_color.get(c.color_id, []),
        } for c in colors],
        'gallery': [g.image.url for g in gallery],
        'textFields': [{'id': t.id, 'label': t.label, 'placeholder': t.placeholder,
                        'max': t.max_length, 'required': t.required} for t in text_fields],
    }

    shop = ShopSettings.load()
    context = {
        'shop': shop,
        'design': design,
        'colors': colors,
        'gallery': gallery,
        'text_fields': text_fields,
        'crumb': crumb,
        'features': shop.features.all() if shop.pk else [],
        'page_data': page_data,
    }
    return render(request, 'shop/shop_design.html', context)


# =====================================================================
# PRODUCT PAGES (2026 redesign): /all_products/, /<category>/ (styles)
# and /<category>/<style>/ (product page). Products here are the blank
# garments of the Design Lab (Product with a mockup template).
# =====================================================================

SIZE_ORDER = ['XXS', '2XS', 'XS', 'S', 'SMALL', 'M', 'MEDIUM', 'L', 'LARGE', 'XL', 'XXL', '2XL', 'XXXL', '3XL',
              '4XL', '5XL', '6XL', 'OS', 'ONE SIZE']


SIZE_SHORT = {'SMALL': 'S', 'MEDIUM': 'M', 'LARGE': 'L', 'XXL': '2XL', 'XXXL': '3XL'}


def _size_key(name):
    n = (name or '').strip().upper()
    return (SIZE_ORDER.index(n) if n in SIZE_ORDER else len(SIZE_ORDER), n)


def _size_label(name):
    """Short label shown on the page, e.g. 'Small' -> 'S' (same as the Instant Quote)."""
    n = (name or '').strip()
    return SIZE_SHORT.get(n.upper(), n)


def _design_lab_products():
    return Product.objects.filter(live=True, customize_mockup_template__isnull=False)


def _product_colors(product):
    """Colours of a product, in admin order: [{id, name, hex, family, is_promo, photos, attr_id, sizes}]"""
    attrs = (ProductAttribute.objects.filter(product=product, color__isnull=False)
             .select_related('color', 'size').order_by('id'))
    photos = {pc.color_id: pc for pc in product.color_photos.all()}
    extras = list(product.photos.all())
    colors = {}
    for a in attrs:
        c = colors.get(a.color_id)
        if not c:
            pc = photos.get(a.color_id)
            c = colors[a.color_id] = {
                'id': a.color_id, 'name': a.color.color_name or '', 'hex': a.color.color_code or '#cccccc',
                'family': a.color.family, 'is_promo': bool(pc and pc.is_promo),
                'order': (pc.order if pc else 9999, a.color.color_name or ''),
                'photos': (pc.views() if pc else []) + [(p.label or 'Photo', p.image.url) for p in extras if p.color_id in (None, a.color_id)],
                'attr_id': a.id, 'sizes': {},
            }
        if a.size:
            price = a.discount_price if a.discount_price and a.discount_price > 0 else a.price
            c['sizes'].setdefault(a.size.Size_name, {'attr_id': a.id, 'price': float(price or 0), 'max': a.Max_Qty or 0})
    out = sorted(colors.values(), key=lambda c: c['order'])
    for c in out:
        c['sizes'] = [dict(name=k, label=_size_label(k), **v) for k, v in sorted(c['sizes'].items(), key=lambda kv: _size_key(kv[0]))]
        del c['order']
    return out


def _price_tiers():
    pricing = DesignPricing.objects.first()
    tiers = [{'min': t.min_qty, 'max': t.max_qty, 'pct': float(t.discount_percent)}
             for t in (pricing.discount_tiers.all() if pricing else [])]
    return float(pricing.front_price) if pricing else 10.0, tiers


def all_products(request):
    """All product categories (coastalreign-style cards). Pinned ones first."""
    settings_ = ProductPageSettings.load()
    # Custom URL set in the admin: the old /all_products/ address redirects to it
    if settings_.all_url and request.path == '/all_products/':
        return redirect(settings_.all_products_url(), permanent=True)
    categories = []
    for cat in Category.objects.filter(active=True).order_by('-is_pinned', 'display_order', 'category_name'):
        styles = cat.live_styles()
        n = styles.count()
        if not n:
            continue
        cat.style_count = n
        # Card image: the category image, or (if missing) the first style's photo
        cat.card_image = ''
        if cat.cate_image and 'noperview' not in cat.cate_image.name and cat.cate_image.storage.exists(cat.cate_image.name):
            cat.card_image = cat.cate_image.url
        else:
            pc = (ProductColor.objects.filter(product__in=styles, front_image__isnull=False).exclude(front_image='')
                  .order_by('product__display_order', 'order').first())
            if pc:
                cat.card_image = pc.front_image.url
        categories.append(cat)
    return render(request, 'shop/all_products.html', {'page': settings_, 'categories': categories})


def category_styles(request, cat_slug):
    """Every live style of one category, with a colour-family filter."""
    if cat_slug == ProductPageSettings.load().all_url:   # custom URL of the All products page
        return all_products(request)
    category = get_object_or_404(Category, slug=cat_slug, active=True)
    styles = list(category.live_styles().order_by('display_order', 'product_name'))
    family = request.GET.get('color', '')

    cards, families = [], {}
    for p in styles:
        colors = _product_colors(p)
        for c in colors:
            if c['family']:
                families[c['family']] = families.get(c['family'], 0) + 1
        if family and not any(c['family'] == family for c in colors):
            continue
        first = None
        if colors:
            first = next((c for c in colors if c['family'] == family), colors[0])
        cards.append({
            'product': p,
            'url': p.get_absolute_url() + (f'?color={first["id"]}' if family and first else ''),
            'photo': first['photos'][0][1] if first and first['photos'] else '',
            'hex': first['hex'] if first else '#ffffff',
            'fabric': p.fabric_composition or strip_tags(p.short_desc or '')[:90],
            'swatches': colors[:5],
            'more': max(0, len(colors) - 5),
        })

    family_options = [(k, label, COLOR_FAMILY_SWATCH.get(k, '#ccc')) for k, label in COLOR_FAMILIES if k in families]
    others = Category.objects.filter(active=True).exclude(pk=category.pk).order_by('-is_pinned', 'display_order')
    others = [c for c in others if c.slug and c.live_styles().exists()]
    return render(request, 'shop/category_styles.html', {
        'category': category, 'cards': cards, 'family_options': family_options, 'family': family,
        'others': others, 'page': ProductPageSettings.load(),
    })


def style_page(request, cat_slug, style_slug):
    """The product (style) page from the client's 'Signature Tee' design."""
    product = get_object_or_404(_design_lab_products().select_related('categories', 'customize_mockup_template'),
                                categories__slug=cat_slug, Slug=style_slug)
    colors = _product_colors(product)
    if not colors:
        raise Http404("This product has no colours yet")
    front_price, tiers = _price_tiers()
    page = ProductPageSettings.load()

    start = colors[0]
    want = request.GET.get('color', '')
    if want.isdigit():
        start = next((c for c in colors if c['id'] == int(want)), start)

    today = date.today()
    first_day = today + timedelta(days=page.delivery_min_days)
    last_day = today + timedelta(days=page.delivery_max_days)
    if first_day.month == last_day.month:
        arrives = f'{first_day:%b} {first_day.day}–{last_day.day}'
    else:
        arrives = f'{first_day:%b} {first_day.day} – {last_day:%b} {last_day.day}'

    mockup = product.customize_mockup_template
    promo_on = bool(product.promo_percent and product.promo_percent > 0)
    page_data = {
        'productId': product.product_id,
        'productName': product.product_name,
        'frontPrice': front_price,
        'promoPct': float(product.promo_percent or 0) if promo_on else 0,
        'tiers': tiers,
        'startColor': start['id'],
        'colors': colors,
        'blank': f'/media/{product.blank_image}' if product.blank_image else '',
        'editorBase': f'/design-lab/?product={product.product_id}' if mockup else '',
    }
    return render(request, 'shop/product_page.html', {
        'product': product,
        'category': product.categories,
        'colors': colors,
        'start': start,
        'promo_colors': [c for c in colors if c['is_promo']] if promo_on else [],
        'other_colors': [c for c in colors if not (c['is_promo'] and promo_on)],
        'page': page,
        'trust': page.trust_items.all() if page.pk else [],
        'arrives': arrives,
        'competitors': CompetitorProduct.objects.filter(main_product=product),
        'page_data': page_data,
    })


@require_POST
def inspo_request(request):
    """'Upload inspo & we'll recreate it': save the request, email the team and the customer."""
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError as _VE

    if request.POST.get('website'):            # honeypot field, hidden from people
        return JsonResponse({'success': True})
    description = request.POST.get('description', '').strip()[:5000]
    email = request.POST.get('email', '').strip()[:254]
    page = request.POST.get('page', '').strip()[:300]
    if not description:
        return JsonResponse({'success': False, 'field': 'description', 'error': ProductPageSettings.load().inspo_error}, status=400)
    try:
        validate_email(email)
    except _VE:
        return JsonResponse({'success': False, 'field': 'email', 'error': 'Please enter a valid email address.'}, status=400)

    image = request.FILES.get('image')
    if image:
        if image.size > SHOP_DESIGN_MAX_IMAGE_MB * 1024 * 1024:
            return JsonResponse({'success': False, 'field': 'image', 'error': f'Image must be under {SHOP_DESIGN_MAX_IMAGE_MB} MB.'}, status=400)
        try:
            with Image.open(image) as img:
                fmt = (img.format or '').upper()
                img.verify()
        except Exception:
            fmt = ''
        if fmt not in SHOP_DESIGN_IMAGE_FORMATS:
            return JsonResponse({'success': False, 'field': 'image', 'error': 'Please upload a JPG, PNG, WEBP or GIF image.'}, status=400)
        image.seek(0)

    req = InspoRequest.objects.create(image=image, description=description, email=email, page=page)

    # Emails: team gets the request (+ image), customer gets a confirmation. A mail
    # problem must not lose the request - it is already saved in the admin.
    try:
        admin_url = request.build_absolute_uri(f'/admin/shop/insporequest/{req.id}/change/')
        team = EmailMultiAlternatives(
            subject=f'New inspo request from {email}',
            body=f'Email: {email}\nPage: {page}\n\nIdea:\n{description}\n\nOpen in admin: {admin_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=list(getattr(settings, 'SALES_EMAILS', [])) or [settings.DEFAULT_FROM_EMAIL],
            reply_to=[email],
        )
        if req.image:
            req.image.open('rb')
            team.attach(os.path.basename(req.image.name), req.image.read(), getattr(image, 'content_type', None))
            req.image.close()
        team.send()
        EmailMultiAlternatives(
            subject='We got your idea - Studio Mohar',
            body=(f'Hi,\n\nThanks for sending us your idea. Our art team will make a free mockup and email it to you.\n\n'
                  f'Your idea:\n{description}\n\nStudio Mohar'),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        ).send()
    except Exception as exc:
        print(f'Inspo request {req.id}: email not sent: {exc}')

    return JsonResponse({'success': True, 'message': ProductPageSettings.load().inspo_success})


# =====================================================================
# DESIGN LAB (2026 redesign) - /design-lab/
# Values and flow from the client's "Design Lab Redesign" file:
# Choose your merch -> style -> colour -> editor (real colour photos per
# side) -> price -> "You're almost there!" (save + add to cart).
# The browser works out the price for display; the server always works it
# out again from the database, so a changed page can't lower the price.
# =====================================================================
DL_SIDES = ('front', 'back', 'left_sleeve', 'right_sleeve')
DL_SIDE_LABELS = {'front': 'Front', 'back': 'Back', 'left_sleeve': 'Left sleeve', 'right_sleeve': 'Right sleeve'}
DL_PHOTO_FIELDS = {'front': 'front_image', 'back': 'back_image', 'left_sleeve': 'left_image', 'right_sleeve': 'right_image'}
DL_MOCKUP_FIELDS = {'front': 'MockUp_Fornt_Image', 'back': 'MockUp_Back_Image',
                    'left_sleeve': 'MockUp_Left_Image', 'right_sleeve': 'MockUp_Right_Image'}
DL_MAX_QTY = 9999           # pieces per size
DL_MAX_ARTWORKS = 40        # images + texts over all sides
DL_MAX_FILES = 20
DL_MAX_IMAGE_MB = 15
DL_MAX_PREVIEW_MB = 12      # each generated preview picture (data URL)


def _dl_pricing():
    """Side print prices, embroidery price per artwork and quantity tiers from 'Design Pricing'."""
    pricing = DesignPricing.objects.first()
    if pricing:
        sides = {'front': float(pricing.front_price), 'back': float(pricing.back_price),
                 'left_sleeve': float(pricing.left_sleeve_price), 'right_sleeve': float(pricing.right_sleeve_price)}
        emb = float(pricing.embroidery_extra)
    else:
        sides, emb = {s: 10.0 for s in DL_SIDES}, 5.0
    _, tiers = _price_tiers()
    return {'sides': sides, 'emb': emb, 'tiers': tiers}


def _dl_quote(color, qty_by_size, sides_used, emb_count, promo_pct, pricing):
    """Price of an order, the same formula as design-lab.js:
       piece = (size price + print price of every side with artwork) x promo x quantity tier
               + embroidery price x number of embroidered artworks.
    The apparel price always includes one print, so a blank design is priced with the front print.
    Returns (rows [(size, qty, unit)], total, each) or None when nothing is ordered."""
    sizes = {s['name']: s for s in color['sizes']}
    rows = [(name, qty) for name, qty in qty_by_size.items() if qty > 0 and name in sizes]
    q = sum(qty for _, qty in rows)
    if not q:
        return None
    print_cost = sum(pricing['sides'][s] for s in sides_used) if sides_used else pricing['sides']['front']
    promo = promo_pct if color['is_promo'] else 0
    pct = 0
    for t in pricing['tiers']:
        if q >= t['min'] and (t['max'] is None or q <= t['max']):
            pct = t['pct']
            break
    out, total = [], Decimal('0')
    for name, qty in rows:
        unit = (sizes[name]['price'] + print_cost) * (1 - promo / 100) * (1 - pct / 100) + pricing['emb'] * emb_count
        unit = Decimal(str(unit)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)   # same as Math.round in JS
        out.append((name, qty, unit))
        total += unit * qty
    return out, total, (total / q).quantize(Decimal('0.01'))


def _dl_colors(product):
    """Colours of a style with the photo of every side ({'front': url, ...}).
    A colour without photos falls back to the old mockup pictures, tinted in the browser."""
    photos = {pc.color_id: pc for pc in product.color_photos.all()}
    mockup = product.customize_mockup_template
    out = []
    for c in _product_colors(product):
        if not c['sizes']:
            continue
        pc = photos.get(c['id'])
        sides, tinted = {}, False
        for side in DL_SIDES:
            field = getattr(pc, DL_PHOTO_FIELDS[side]) if pc else None
            if field:
                sides[side] = field.url
        if not sides and mockup:
            tinted = True
            for side in DL_SIDES:
                field = getattr(mockup, DL_MOCKUP_FIELDS[side])
                if field:
                    sides[side] = field.url
        if not sides:
            continue
        out.append({'id': c['id'], 'name': c['name'], 'hex': c['hex'], 'is_promo': c['is_promo'],
                    'attr_id': c['attr_id'], 'sides': sides, 'tinted': tinted, 'sizes': c['sizes']})
    return out


def _dl_style(product, pricing):
    colors = _dl_colors(product)
    if not colors:
        return None
    promo_on = bool(product.promo_percent and product.promo_percent > 0)
    lowest = min(s['price'] for c in colors for s in c['sizes']) + pricing['sides']['front']
    return {
        'id': product.product_id,
        'name': product.product_name,
        'facts': product.fabric_composition or strip_tags(product.short_desc or '')[:90],
        'from': round(lowest, 2),
        'promoPct': float(product.promo_percent) if promo_on else 0,
        'promoCount': sum(1 for c in colors if c['is_promo']) if promo_on else 0,
        'sizeChart': product.size_chart_img.url if product.size_chart_img else '',
        'photo': next(iter(colors[0]['sides'].values())),
        'colors': colors,
    }


def _dl_catalog(pricing):
    """Categories -> styles -> colours for the 'Choose your merch / style / colour' steps."""
    out = []
    for cat in Category.objects.filter(active=True).order_by('-is_pinned', 'display_order', 'category_name'):
        styles = []
        for p in (cat.live_styles().order_by('display_order', 'product_name')
                  .select_related('customize_mockup_template').prefetch_related('color_photos', 'photos')):
            style = _dl_style(p, pricing)
            if style:
                styles.append(style)
        if not styles:
            continue
        image = ''
        if cat.cate_image and 'noperview' not in cat.cate_image.name and cat.cate_image.storage.exists(cat.cate_image.name):
            image = cat.cate_image.url
        out.append({'id': cat.category_id, 'name': cat.category_name, 'image': image or styles[0]['photo'],
                    'styles': styles})
    return out


def _dl_parse_sizes(raw, color):
    """'S:2,M:3' (labels or names, from the product page link) -> {size name: qty}."""
    by_key = {}
    for s in color['sizes']:
        by_key[s['name'].upper()] = s['name']
        by_key[s['label'].upper()] = s['name']
    out = {}
    for pair in (raw or '').split(','):
        key, _, qty = pair.partition(':')
        name = by_key.get(key.strip().upper())
        if name and qty.strip().isdigit():
            out[name] = min(int(qty), DL_MAX_QTY)
    return out


def _dl_saved_sides(design):
    """The four side canvases of a Design Lab saved design, or None for an old-editor design."""
    sides = {}
    for side, field in (('front', 'front_json'), ('back', 'back_json'),
                        ('left_sleeve', 'left_sleeve'), ('right_sleeve', 'right_sleeve')):
        raw = getattr(design, field) or ''
        try:
            data = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return None
        if data is None:
            continue
        if not isinstance(data, dict) or data.get('dl') != 1:
            return None
        sides[side] = data.get('canvas')
    return sides


@ensure_csrf_cookie
def design_lab(request):
    """The Design Lab page. ?product=<id>&color=<id>&sizes=S:2,M:3 opens that product
    in the editor; ?design=<uid> reopens a saved design; no product shows the pickers."""
    pricing = _dl_pricing()
    catalog = _dl_catalog(pricing)
    page = ProductPageSettings.load()

    start = {'product': None, 'color': None, 'sizes': {}, 'design': None}
    want = request.GET.get('product', '')
    uid = request.GET.get('design', '')
    cart_sizes = {}
    if len(uid) == 36:
        saved = SavedDesign.objects.filter(uid=uid).first() if _is_uuid(uid) else None
        sides = _dl_saved_sides(saved) if saved else None
        if saved and sides is not None and saved.product_id:
            want = str(saved.product_id)
            start['color'] = saved.color_id
            start['design'] = {'uid': str(saved.uid), 'name': saved.design_name or '', 'email': saved.email, 'sides': sides}
            # Opened from the cart's edit button: bring back that line's sizes too
            if request.session.session_key:
                line = GuestCart.objects.filter(session_id=request.session.session_key, save_design_uid=str(saved.uid)).first()
                if line:
                    cart_sizes = {i.size: i.quantity for i in line.cart_items.all()}
    if want.isdigit():
        style = next((s for cat in catalog for s in cat['styles'] if s['id'] == int(want)), None)
        if style:
            start['product'] = style['id']
            color = style['colors'][0]
            want_color = request.GET.get('color', '') or str(start['color'] or '')
            if want_color.isdigit():
                color = next((c for c in style['colors'] if c['id'] == int(want_color)), color)
            start['color'] = color['id']
            start['sizes'] = _dl_parse_sizes(request.GET.get('sizes', ''), color) or {
                name: qty for name, qty in cart_sizes.items() if any(s['name'] == name for s in color['sizes'])}

    today = date.today()
    first_day = today + timedelta(days=page.delivery_min_days)
    last_day = today + timedelta(days=page.delivery_max_days)
    if first_day.month == last_day.month:
        arrives = f'{first_day:%b} {first_day.day}–{last_day.day}'
    else:
        arrives = f'{first_day:%b} {first_day.day} – {last_day:%b} {last_day.day}'

    lab_data = {
        'catalog': catalog,
        'pricing': pricing,
        'start': start,
        'arrives': arrives,
        'sideLabels': DL_SIDE_LABELS,
        'maxImageMb': DL_MAX_IMAGE_MB,
        'urls': {
            'save': '/design-lab/save/',
            'cart': '/cart/',
            'requestColour': page.request_colour_url or '/contact_sales/',
            'requestProduct': '/contact_sales/',
            'terms': '/terms-conditions/',
        },
    }
    return render(request, 'shop/design_lab.html', {'lab_data': lab_data})


def _is_uuid(value):
    import uuid as _uuid
    try:
        _uuid.UUID(value)
        return True
    except ValueError:
        return False


def _dl_artworks(sides, available):
    """Images/texts on the sides the product has: [(side, object dict)]."""
    out = []
    for side in DL_SIDES:
        canvas = sides.get(side) if side in available else None
        objects = canvas.get('objects') if isinstance(canvas, dict) else None
        if isinstance(objects, list):
            for obj in objects:
                if isinstance(obj, dict) and obj.get('type') in ('image', 'textbox', 'i-text', 'text'):
                    out.append((side, obj))
    return out


def _dl_details_text(artworks):
    """Readable summary for the cart line / order item, e.g.
    'Front: Image "logo.png" - Embroidery - Notes: 3 inches wide'."""
    lines = []
    for side, obj in artworks:
        method = 'Embroidery' if obj.get('dlMethod') == 'embroidery' else 'Print'
        if obj.get('type') == 'image':
            what = 'Image "%s"' % str(obj.get('dlName') or 'image')[:120]
        else:
            what = 'Text "%s" (%s, %s)' % (str(obj.get('text') or '')[:200], str(obj.get('fontFamily') or '')[:40],
                                           str(obj.get('fill') or '')[:20])
        line = f'{DL_SIDE_LABELS[side]}: {what} - {method}'
        notes = str(obj.get('dlNotes') or '').strip()
        if notes:
            line += f' - Notes: {notes[:1000]}'
        lines.append(line)
    return '\n'.join(lines)


def _dl_data_url(value):
    """Only accept generated PNG/JPEG previews, within the size limit."""
    value = value if isinstance(value, str) else ''
    if not value.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,')):
        return ''
    return value if len(value) <= DL_MAX_PREVIEW_MB * 1024 * 1024 * 4 // 3 else ''


def _dl_json(request, key, default):
    try:
        value = json.loads(request.POST.get(key, '') or 'null')
    except json.JSONDecodeError:
        return default
    return value if isinstance(value, type(default)) else default


@require_POST
def design_lab_save(request):
    """Save a Design Lab design (and, with action=cart, add it to the cart). Multipart POST:
      action          'save' (Save & Email My Design) or 'cart' (Save & Add to Cart)
      name, email     design name and the customer's email (email required)
      product_id, color_id
      sizes           JSON {size name: qty}                    - cart only
      sides           JSON {side: fabric canvas JSON}          - images/texts carry dlMethod/dlName/dlNotes
      previews        JSON {side: data URL of photo + design}  - cart only
      prints          JSON {side: data URL of the design only} - cart only
      design_uid      the saved design being edited (optional)
      uploaded_files  original image files, uploaded_files_meta JSON {"side", "filename"} each
    """
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError as _VE

    def fail(msg, field=''):
        return JsonResponse({'success': False, 'field': field, 'error': msg}, status=400)

    action = request.POST.get('action', 'save')
    email = request.POST.get('email', '').strip()[:254]
    name = request.POST.get('name', '').strip()[:250]
    try:
        validate_email(email)
    except _VE:
        return fail('Please enter a valid email address.', 'email')

    product_id, color_id = request.POST.get('product_id', ''), request.POST.get('color_id', '')
    if not product_id.isdigit() or not color_id.isdigit():
        return fail('Invalid data.')
    product = (_design_lab_products().select_related('customize_mockup_template')
               .prefetch_related('color_photos', 'photos').filter(product_id=int(product_id)).first())
    pricing = _dl_pricing()
    style = _dl_style(product, pricing) if product else None
    color = next((c for c in style['colors'] if c['id'] == int(color_id)), None) if style else None
    if not color:
        return fail('This product or colour is not available any more.')

    sides = _dl_json(request, 'sides', {})
    sides = {s: sides[s] for s in DL_SIDES if isinstance(sides.get(s), dict)}
    artworks = _dl_artworks(sides, color['sides'])
    if not artworks:
        return fail('Please upload an image or add text first.')
    if len(artworks) > DL_MAX_ARTWORKS:
        return fail(f'A design can have up to {DL_MAX_ARTWORKS} images and texts.')

    # Original files (for printing). Only real raster images: an SVG/HTML file could
    # carry a script that runs when the team opens it from the admin.
    files = request.FILES.getlist('uploaded_files')[:DL_MAX_FILES]
    metas = request.POST.getlist('uploaded_files_meta')
    clean_files = []
    for i, f in enumerate(files):
        try:
            meta = json.loads(metas[i]) if i < len(metas) else {}
        except json.JSONDecodeError:
            meta = {}
        side = meta.get('side') if isinstance(meta, dict) else None
        if side not in DL_SIDES:
            continue
        if f.size > DL_MAX_IMAGE_MB * 1024 * 1024:
            return fail(f'Images must be under {DL_MAX_IMAGE_MB} MB.')
        try:
            with Image.open(f) as img:
                fmt = (img.format or '').upper()
                img.verify()
        except Exception:
            fmt = ''
        if fmt not in SHOP_DESIGN_IMAGE_FORMATS:
            return fail('Please upload a JPG, PNG, WEBP or GIF image.')
        f.seek(0)
        clean_files.append((f, side, str(meta.get('filename') or f.name)[:255]))

    quote = None
    if action == 'cart':
        qty_by_size = {}
        for size_name, qty in _dl_json(request, 'sizes', {}).items():
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 0
            if qty < 0 or qty > DL_MAX_QTY:
                return fail(f'Quantity must be between 1 and {DL_MAX_QTY} per size.')
            if qty:
                qty_by_size[str(size_name)] = qty
        sides_used = sorted({side for side, _ in artworks})
        emb_count = sum(1 for _, obj in artworks if obj.get('dlMethod') == 'embroidery')
        quote = _dl_quote(color, qty_by_size, sides_used, emb_count, style['promoPct'], pricing)
        if not quote:
            return fail('Please enter how many pieces you need in each size.')

    def side_json(side):
        return json.dumps({'dl': 1, 'canvas': sides[side]}) if side in sides else None

    attr = ProductAttribute.objects.filter(id=color['attr_id']).select_related('color').first()
    with transaction.atomic():
        design = None
        uid = request.POST.get('design_uid', '')
        if _is_uuid(uid):
            design = SavedDesign.objects.filter(uid=uid, email__iexact=email).first()
        if design is None:
            design = SavedDesign(email=email)
        design.design_name = name
        design.front_json = side_json('front')
        design.back_json = side_json('back')
        design.left_sleeve = side_json('left_sleeve')
        design.right_sleeve = side_json('right_sleeve')
        design.color = attr.color if attr else None
        design.product = product
        design.product_attr = attr
        design.mockup = product.customize_mockup_template
        design.save()

        cart = None
        if quote:
            rows, total, each = quote
            if not request.session.session_key:
                request.session.create()
            previews = _dl_json(request, 'previews', {})
            prints = _dl_json(request, 'prints', {})
            # Editing a design that is already in this cart replaces that line
            cart = GuestCart.objects.filter(session_id=request.session.session_key, save_design_uid=str(design.uid)).first()
            if cart is None:
                cart = GuestCart(session_id=request.session.session_key, save_design_uid=str(design.uid))
            cart.product_attr = attr
            cart.front_image = _dl_data_url(previews.get('front'))
            cart.back_image = _dl_data_url(previews.get('back'))
            cart.left_image = _dl_data_url(previews.get('left_sleeve'))
            cart.right_image = _dl_data_url(previews.get('right_sleeve'))
            cart.front_design_image = _dl_data_url(prints.get('front'))
            cart.back_design_image = _dl_data_url(prints.get('back'))
            cart.left_design_image = _dl_data_url(prints.get('left_sleeve'))
            cart.right_design_image = _dl_data_url(prints.get('right_sleeve'))
            cart.price_of_each = each
            cart.total_price = total
            cart.design_details = _dl_details_text(artworks)
            cart.save()
            cart.cart_items.all().delete()
            cart.uploaded_files.all().delete()
            for size_name, qty, unit in rows:
                GuestCartItem.objects.create(cart=cart, size=size_name, quantity=qty, unit_price=float(unit))
            for f, side, filename in clean_files:
                CartUploadedFile.objects.create(cart=cart, file=f, side=side, filename=filename)

    # Email the link (same template as the old editor). A mail problem must not
    # lose the design or the cart line - both are already saved.
    try:
        link = request.build_absolute_uri('/retrieve-design/')
        msg = EmailMultiAlternatives(
            'Your Design is Saved | Studio Mohar',
            f'Your design is saved! Continue editing here: {link}',
            settings.DEFAULT_FROM_EMAIL,
            [email] + list(getattr(settings, 'DESIGN_SAVED_EMAILS', [])),
            reply_to=[email],
        )
        msg.attach_alternative(render_to_string('shop/emails/design_saved.html', {
            'product': product, 'mockup': product.customize_mockup_template, 'link': link,
        }), 'text/html')
        msg.send()
    except Exception as exc:
        print(f'Design Lab save {design.uid}: email not sent: {exc}')

    return JsonResponse({'success': True, 'uid': str(design.uid), 'cart_url': '/cart/' if cart else ''})
