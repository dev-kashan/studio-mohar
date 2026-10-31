# from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index , name="shophome"),
    path('products/<int:id>/', views.products , name="products"),
    path('all_products/', views.all_products , name="all_products"),
    path('save-design/', views.save_design , name="save_design"),
    path('blog/', views.blog , name="blog"),
    path('blog_detail/<slug:slug>/', views.blog_detail , name="blog_detail"),
    path('retrieve-design/', views.retrieve_design_view, name='retrieve_design_request'),
    path("verify-code/", views.verify_design_code, name="verify_design_code"),
    path('design/<uid>/', views.load_design , name="load_design"),
    path('product_detail/<int:id>/', views.product_detail , name="product_detail"),
    path('service_detail/<int:id>/', views.service_detail , name="service_detail"),
    path('get_apparel_for/<int:id>/', views.get_apparel_for , name="get_apprel_for"),
    path('contact_sales/', views.contact_sales , name="contact_sales"),
    path('contact_support/', views.contact_support , name="contact_support"),
    path('our_story/', views.our_story , name="our_story"),
    path('specials/', views.specials , name="specials"),
    path('product/<int:myid>', views.product , name="product"),
    path('category/', views.category , name="category"),
    path('checkout/', views.checkout , name="checkout"),
    path('cart/', views.cart , name="cart"),
    # path('contact/', views.contact , name="contact"),
    path('order_tracker/', views.order_tracker , name="order_tracker"),
    # path('about/', views.about , name="about"),
    path('login/', views.loginsys , name="loginsys"),
    path('logout/', views.logoutsys , name="logoutsys"),
    path('singup/', views.singup , name="singup"),
    path('search/', views.search , name="search"),
    path('terms-conditions/', views.terms_conditions , name="terms-conditions"),
    path('privacy-policy/', views.privacy_policy , name="privacy_policy"),
    path('shipping-policy/', views.shipping_policy , name="shipping_policy"),
    path('search_sticker/', views.search_sticker , name="search_sticker"),
    path('search_sticker_by_category/', views.search_sticker_by_category , name="search_sticker"),
    path('check_coupon/', views.check_coupon , name="check_coupon"),
    # path('allstores/', views.allstores , name="allstores"),
    # path('store/', views.store , name="store"),
    # path('seller/', views.seller , name="seller"),
    # path('sellerinfo/', views.sellerinfo , name="sellerinfo"),
    # path('signup-for-seller/', views.singupseller , name="singupseller"),
    # path('login-for-seller/', views.loginseller , name="loginseller"),
    # path('deshboard/', views.deshboard , name="deshboard"),
    # path('product-add/', views.productadd , name="productadd"),
    path('filter-data/', views.filter_data , name="filter_data"),
    path('load-more/', views.load_more , name="load-more"),
    path('carthtmlssdsd/', views.shopping_list , name="shopping_list"),
    path('flash-product-data/', views.flash_product_filter , name="flashproduct_filter"),
    path('flash-sale/', views.flash_sale , name="flash_sale"),
    path('service/', views.service , name="service"),
    path('rating/', views.rating , name="rating"),
    path('search_suggestion/', views.search_suggestion , name="search_suggestion"),
    path('customize-editor/<int:id>/<str:slug>/<int:pid>/', views.customizeEditor , name="customizeEditor"),
    path('check_available/' , views.check_available , name="size"),
    path('loadmore-sticker/', views.loadmore_sticker , name="loadmore_sticker"),
    path('add-to-cart/', views.add_to_cart , name="add_to_cart"),
    path('add-to-cart-special/', views.add_to_cart_special , name="add_to_cart"),
    path('add-to-cart-shop-design/', views.add_to_cart_shop_design , name="add_to_cart_shop_design"),
    path('delete-cart-item/<int:cart_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('get-sizes/<int:product_id>/', views.get_sizes_for_color, name='get_sizes_for_color'),

    # path("products/filter/", views.filter_products, name="filter_products"),
    path('filter-products/', views.filter_products, name='filter_products'),

    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),






 
]
