import os
from django.contrib import admin
from django.db.models import Q
from django.forms.models import BaseInlineFormSet

from django.shortcuts import HttpResponseRedirect , redirect
from django.contrib import messages
# Register your models here.
from .models import *
from django.utils.html import format_html
from newecom.settings import ADMIN_LINK , MEDIA_ROOT
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404


# admin.site.register(Country)

# ProductPreview and CompetitorProduct inlines removed from the Product admin
# (not used any more). Models and existing data are untouched.


class OrderItemUploadedFileInline(admin.TabularInline):
    model = OrderItemUploadedFile
    extra = 0
    readonly_fields = ('file_link', 'filename', 'side', 'uploaded_at')
    can_delete = False

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "-"
    file_link.short_description = "File"

# ---------------- OrderItem Sizes Inline ----------------
class OrderItemSizeInline(admin.TabularInline):
    model = OrderItemSize
    extra = 0
    fields = ('size', 'unit_price','quantity','total_price', 'personalization_display')
    readonly_fields = ('personalization_display',)  # shop designs: customer text per piece

# ---------------- OrderItem Inline in OrderAdmin ----------------
class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    show_change_link = False  # we will use a custom button instead
    readonly_fields = ('image_thumbnail', 'details_button')
    
    fields = (
        ('image_thumbnail', 'details_button', 'image'),

        ('Order_Type', 'unity_price', 'item_total'),

        ('Mockup', 'order_item'),
        ('shop_design', 'personal_image'),
        ('Front_Image', 'Back_Image', 'Left_Image', 'Right_Image'),
        ('Front_Desgin_Image', 'Back_Desgin_Image', 'Left_Desgin_Image', 'Right_Desgin_Image'),
        ('design_details',),  # Design Lab: print / embroidery per artwork, texts, notes

        ('color', 'order_status', 'status', 'Active'),
    )

    def details_button(self, obj):
        if not obj.pk:
            return "-"
        url = reverse('admin:shop_orderitem_change', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">More details</a>', url)
    details_button.short_description = "Details"

# ---------------- Order Admin ----------------
class OrderAdmin(admin.ModelAdmin):
    fields = (
        ('name',),
        ('phone', 'email'),
        ('city', 'company'),
        ('zip_code', 'Country', 'province'),
        ('promo', 'coupon'),
        ('address',),
        ('SubTotal', 'tax', 'Delivery', 'discount_amount', 'total'),
        ('ship_type',),
        ('created', 'estimated_delivery_time', 'Active'),
        ('order_detail_zip',),
        ('special_instructions',)
    )
    
    list_display = ('name', 'Order_number', 'created', 'phone', 'total', 'Active', 'nofity', 'zip_button')
    list_filter = ('order_id', 'name', 'phone', 'Active', 'created')
    list_editable = ('Active',)
    search_fields = ('name', 'created', 'phone', 'email', 'Order_number', 'address')
    readonly_fields = ('created',)
    inlines = [OrderItemInline]

    # ---------------- ZIP button ----------------
    def zip_button(self, obj):
        url = reverse('admin:download_order_zip', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">Download ZIP</a>', url)

    zip_button.short_description = 'Order ZIP'

    # ---------------- Custom admin URL ----------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'download_zip/<int:order_id>/',
                self.admin_site.admin_view(self.download_zip_view),
                name='download_order_zip'
            ),
        ]
        return custom_urls + urls

    # ---------------- Generate ZIP on the fly ----------------
    def download_zip_view(self, request, order_id):
        from .models import Order
        order = get_object_or_404(Order, pk=order_id)

        try:
            zip_buffer = order.generate_zip()  # generate_zip now returns HttpResponse
            return zip_buffer
        except Exception as e:
            print(f"Error generating ZIP for Order {order.Order_number}: {e}")
            from django.contrib import messages
            messages.error(request, f"Failed to generate ZIP for Order {order.Order_number}.")
            return redirect(request.META.get('HTTP_REFERER', '/admin/'))







    # def response_add(self, request ,obj, post_url_continue=None):
    #     _save = request.POST.get('_save','')
    #     _addanother = request.POST.get('_addanother','')
    #     _continue = request.POST.get('_continue','')
    #     orderid = obj.order_id
        
    #     if orderid:
    #         order_item =  OrderItem.objects.filter(order_by__order_id=orderid)
    #         if order_item:
    #             for i in order_item:
    #                 if i.Order_Type == "Normal":
    #                     try:
    #                         filter_ava = ProductAttribute.objects.get(product__product_id=i.order_item.product_id , size__Size_name=i.size)
    #                     except:
    #                         filter_ava = ProductAttribute.objects.get(product__product_id=i.order_item.product_id)
                        

    #                     if filter_ava:
    #                         calcul = i.quantity 
    #                         minus_avable = filter_ava.Availibility - calcul
    #                         if i.availibile_minus == False:
    #                             if i.quantity  <= filter_ava.Availibility:

    #                                 try:
    #                                     get_prod = Product.objects.get(product_id=i.order_item.product_id)
    #                                 except:
    #                                     message =  f"Sorry Somethink wrong ! Error"
    #                                     messages.error(request , mark_safe(message))
    #                                     return redirect(f'/{ADMIN_LINK}shop/product/')
                                
                                    

    #                                 if i.order_status:
    #                                     OrderItem.objects.filter(id=i.id , Active=True).update(availibile_minus=True)
    #                                     if i.size == 'undefined' or i.size == '' or i.size == 'None' or i.size == None:
    #                                         ProductAttribute.objects.filter(product__product_id=i.order_item.product_id).update(Availibility=minus_avable)
    #                                     else:
    #                                         ProductAttribute.objects.filter(product__product_id=i.order_item.product_id , size=i.size).update(Availibility=minus_avable)
                                        
    #                                     prod_variations = ProductAttribute.objects.filter(product=get_prod)
    #                                     total_avalible = 0
    #                                     for x in prod_variations:
    #                                         if x.Availibility > 0:
    #                                             total_avalible+=x.Availibility

    #                                     update_product = Product.objects.filter(product_id=i.order_item.product_id).update(Availibility=total_avalible)

    #                                 else:
    #                                     if i.Active == True and i.status == "delivered":
    #                                         OrderItem.objects.filter(id=i.id , Active=True).update(availibile_minus=True)
    #                                         if i.size == 'undefined' or i.size == '' or i.size == 'None' or i.size == None:
    #                                             ProductAttribute.objects.filter(product__product_id=i.order_item.product_id).update(Availibility=minus_avable)
    #                                         else:
    #                                             ProductAttribute.objects.filter(product__product_id=i.order_item.product_id , size=i.size).update(Availibility=minus_avable)
                                            
    #                                         prod_variations = ProductAttribute.objects.filter(product=get_prod)
    #                                         total_avalible = 0
    #                                         for x in prod_variations:
    #                                             if x.Availibility > 0:
    #                                                 total_avalible+=x.Availibility

    #                                         update_product = Product.objects.filter(product_id=i.order_item.product_id).update(Availibility=total_avalible)
                    

    #     if _save == "Save":
    #         message =  f"The Order <a href='/{ADMIN_LINK}shop/order/{orderid}/change/'>{obj.name}..</a> was added successfully"
    #         messages.success(request , mark_safe(message))
    #         return redirect(f'/{ADMIN_LINK}shop/order/')
    #     elif _addanother == "Save and add another":
    #         message =  f"The Order <a href='/{ADMIN_LINK}shop/order/{orderid}/change/'>{obj.name}..</a> was added successfully. You may add another product view below."
    #         messages.success(request , mark_safe(message))
    #         return redirect(f'/{ADMIN_LINK}shop/order/add/')
    #     elif _continue == "Save and continue editing":
    #         message =  f"The Order <a href='/{ADMIN_LINK}shop/order/{orderid}/change/'>{obj.name}..</a> was added successfully. You may edit it again below."
    #         messages.success(request , mark_safe(message))
    #         return redirect(f'/{ADMIN_LINK}shop/order/{orderid}/change/')


    # def response_change(self, request ,obj, post_url_continue=None):
    #     _save = request.POST.get('_save','')
    #     _addanother = request.POST.get('_addanother','')
    #     _continue = request.POST.get('_continue','')
    #     orderid = obj.order_id
        
    #     if orderid:
    #         order_item =  OrderItem.objects.filter(order_by__order_id=orderid)
    #         if order_item:
    #             for i in order_item:
    #                 if i.Order_Type == "Normal":
    #                     try:
    #                         filter_ava = ProductAttribute.objects.get(product__product_id=i.order_item.product_id , size=i.size)
    #                     except:
    #                         filter_ava = ProductAttribute.objects.get(product__product_id=i.order_item.product_id)

    #                     if filter_ava:
    #                         calcul = i.quantity 
    #                         minus_avable = filter_ava.Availibility - calcul
    #                         if i.availibile_minus == False:
    #                             if i.quantity  <= filter_ava.Availibility:

    #                                 try:
    #                                     get_prod = Product.objects.get(product_id=i.order_item.product_id)
    #                                 except:
    #                                     message =  f"Sorry Somethink wrong ! Error"
    #                                     messages.error(request , mark_safe(message))
    #                                     return redirect(f'/{ADMIN_LINK}shop/product/')
                                
                                    

    #                                 if i.order_status:
    #                                     OrderItem.objects.filter(id=i.id , Active=True).update(availibile_minus=True)
    #                                     if i.size == 'undefined' or i.size == '' or i.size == 'None' or i.size == None:
    #                                         ProductAttribute.objects.filter(product__product_id=i.order_item.product_id).update(Availibility=minus_avable)
    #                                     else:
    #                                         ProductAttribute.objects.filter(product__product_id=i.order_item.product_id , size=i.size).update(Availibility=minus_avable)
                                        
    #                                     prod_variations = ProductAttribute.objects.filter(product=get_prod)
    #                                     total_avalible = 0
    #                                     for x in prod_variations:
    #                                         if x.Availibility > 0:
    #                                             total_avalible+=x.Availibility

    #                                     update_product = Product.objects.filter(product_id=i.order_item.product_id).update(Availibility=total_avalible)

    #                                 else:
    #                                     if i.Active == True and i.status == "delivered":
    #                                         OrderItem.objects.filter(id=i.id , Active=True).update(availibile_minus=True)
    #                                         if i.size == 'undefined' or i.size == '' or i.size == 'None' or i.size == None:
    #                                             ProductAttribute.objects.filter(product__product_id=i.order_item.product_id).update(Availibility=minus_avable)
    #                                         else:
    #                                             ProductAttribute.objects.filter(product__product_id=i.order_item.product_id , size=i.size).update(Availibility=minus_avable)
                                            
    #                                         prod_variations = ProductAttribute.objects.filter(product=get_prod)
    #                                         total_avalible = 0
    #                                         for x in prod_variations:
    #                                             if x.Availibility > 0:
    #                                                 total_avalible+=x.Availibility

    #                                         update_product = Product.objects.filter(product_id=i.order_item.product_id).update(Availibility=total_avalible)
                                            
                                        
                        

    #     if _save == "Save":
    #         message =  f"The Order <a href='/{ADMIN_LINK}shop/order/{orderid}/change/'>{obj.name}..</a> was change successfully"
    #         messages.success(request , mark_safe(message))
    #         return redirect(f'/{ADMIN_LINK}shop/order/')
    #     elif _addanother == "Save and add another":
    #         message =  f"The Order <a href='/{ADMIN_LINK}shop/order/{orderid}/change/'>{obj.name}..</a> was change successfully. You may add another product view below."
    #         messages.success(request , mark_safe(message))
    #         return redirect(f'/{ADMIN_LINK}shop/order/add/')
    #     elif _continue == "Save and continue editing":
    #         message =  f"The Order <a href='/{ADMIN_LINK}shop/order/{orderid}/change/'>{obj.name}..</a> was change successfully. You may edit it again below."
    #         messages.success(request , mark_safe(message))
    #         return redirect(f'/{ADMIN_LINK}shop/order/{orderid}/change/')



 
    class Meta:
       model = Order
       
admin.site.register(Order,OrderAdmin)

class OrderItemAdmin(admin.ModelAdmin):
    fields = (
        ('image_thumbnail', 'order_by', 'order_item', 'product_name'),
        ('Order_Type', 'shop_design', 'personal_image'),
        ('color', 'order_status', 'status'),
        ('unity_price', 'item_total', 'date', 'Active'),
        ('design_details',),
    )
    list_filter = ('id', 'order_by', 'order_item', 'color', 'status', 'Active', 'date')
    readonly_fields = ('image_thumbnail', 'date',)
    list_display = ('image_thumbnail', 'order_by', 'Order_by_Id', 'product_name', 'unity_price', 'date', 'status','Active')
    list_editable = ('Active','status',)
    search_fields = ('order_by__name', 'product_name', 'product_brand', 'color', 'quantity', 'unity_price')
    inlines = [OrderItemUploadedFileInline, OrderItemSizeInline]

    
    
admin.site.register(OrderItem , OrderItemAdmin)


class ProductAttributeAdminInline(admin.TabularInline):
    model = ProductAttribute
    fields = (('image_tag' ,'image')  , ('color' , 'size'  , 'price' , 'discount_price' , 'Availibility', 'Max_Qty'))
    extra = 0
    readonly_fields = ('image_tag',)


class ProductColorFormSet(BaseInlineFormSet):
    """Colour photos must be for a colour the product has in its variations."""

    def clean(self):
        super().clean()
        if not self.instance.pk:
            return
        allowed = set(ProductAttribute.objects.filter(product=self.instance).values_list('color_id', flat=True))
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            color = form.cleaned_data.get('color')
            if color and allowed and color.id not in allowed:
                form.add_error('color', f'"{color}" is not in this product\'s variations - add it there first.')


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    formset = ProductColorFormSet
    extra = 0
    fields = ('color', 'is_promo', 'front_image', 'back_image', 'left_image', 'right_image', 'order')
    verbose_name_plural = "Colour photos (front / back / sleeves) - shown on the product page instead of the mockup"


class ProductPhotoInline(admin.TabularInline):
    model = ProductPhoto
    extra = 0
    fields = ('image', 'label', 'color', 'order')
    verbose_name_plural = "Extra photos (on model, fabric...)"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fieldsets = [
        ("", {
            "classes": ("collapse"),
            "fields": (('product_type'),
                       ('product_name') ,
                       ('Slug', 'display_order'),
                       ('size_available'),
                        ('printed_image', 'blank_image', 'size_chart_img'),
                        ('categories'),   # mockup template removed: colour photos are used instead
                        # ('min_qty' , 'max_qty' ,),
                        # ('price' , 'sprice'),
                        ('short_desc'),
                        ('desc'),
                        ('live', 'promo_percent'),
                        ('Meta_title', 'Meta_description'),
                ),
        }),
        # "Competition Details" fieldset removed (not used any more).
    ]
    # fields = (
    #     # ('product_code' , 'brand'),
    #     ('product_name', 'size_available'),
    #     ('printed_image', 'blank_image', 'size_chart_img'),
    #     ('categories' , 'customize_mockup_template'),
    #     # ('min_qty' , 'max_qty' ,),
    #     # ('price' , 'sprice'),
    #     ('short_desc'),
    #     ('desc'),
    #     ('live', 'is_best_seller', 'is_sustainable'),
    #     # ('Slug' , 'Meta_title' , 'Meta_description'),
    # )
    class Media:
        js = ('shop/js/Tinymceeditor.js',)
    list_display =('preview' , 'product_name', 'product_type', 'categories', 'stock' , 'pub_date' , 'live')
    list_filter =('product_type', 'product_id' , 'categories__category_name' ,   'Availibility' , 'live' , 'pub_date',)
    list_editable = ('live', ) 
    search_fields = ('product_name' ,'categories__category_name'  , 'categories__category' , 'desc', 'pub_date')
    inlines = [ProductAttributeAdminInline, ProductColorInline, ProductPhotoInline]
    # ordering = ['Availibility']
 
    class Meta:
       model = Product

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # No mockup any more: a Custom product needs colour photos to show in the Design Lab
        product = form.instance
        if product.product_type == 'custom' and product.live and not product.customize_mockup_template_id:
            if not product.color_photos.exclude(front_image='').exclude(front_image__isnull=True).exists():
                messages.warning(request, f'"{product}" has no colour photos yet, so it will not show in the Design Lab. '
                                          'Add them under "Colour photos" below.')

    def response_add(self, request ,obj, post_url_continue=None):
        _save = request.POST.get('_save','')
        _addanother = request.POST.get('_addanother','')
        _continue = request.POST.get('_continue','')

        product_id = obj.product_id
        try:
            get_prod = Product.objects.get(product_id=product_id)
        except:
            message =  f"Sorry Somethink wrong ! Error"
            messages.error(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/')

        prod_variations = ProductAttribute.objects.filter(product=get_prod)
        

        total_avalible = 0
        for i in prod_variations:
            if i.Availibility > 0:
                total_avalible+=i.Availibility

        # str_slug = obj.product_name
        # nospaces = str_slug.replace(" ", "-")
        
        update_product = Product.objects.filter(product_id=product_id).update(Availibility=total_avalible)
        
            
            
        if _save == "Save":
            message =  f"The Product <a href='/{ADMIN_LINK}shop/product/{product_id}/change/'>{obj.product_name[0:16]}..</a> was added successfully"
            messages.success(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/')
        elif _addanother == "Save and add another":
            message =  f"The Product <a href='/{ADMIN_LINK}shop/product/{product_id}/change/'>{obj.product_name[0:16]}..</a> was added successfully. You may add another product view below."
            messages.success(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/add/')
        elif _continue == "Save and continue editing":
            message =  f"The Product <a href='/{ADMIN_LINK}shop/product/{product_id}/change/'>{obj.product_name[0:16]}..</a> was added successfully. You may edit it again below."
            messages.success(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/{product_id}/change/')

    def response_change(self, request ,obj, post_url_continue=None):
        _save = request.POST.get('_save','')
        _addanother = request.POST.get('_addanother','')
        _continue = request.POST.get('_continue','')

        product_id = obj.product_id
        try:
            get_prod = Product.objects.get(product_id=product_id)
        except:
            message =  f"Sorry Somethink wrong ! Error"
            messages.error(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/')

        prod_variations = ProductAttribute.objects.filter(product=get_prod)
        


        total_avalible = 0
        for i in prod_variations:
            if i.Availibility > 0:
                total_avalible+=i.Availibility

        # str_slug = obj.product_name
        # nospaces = str_slug.replace(" ", "-")
        
        update_product = Product.objects.filter(product_id=product_id).update(Availibility=total_avalible)
        
        if _save == "Save":
            message =  f"The Product <a href='/{ADMIN_LINK}shop/product/{product_id}/change/'>{obj.product_name[0:16]}..</a> was Change successfully"
            messages.success(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/')
        elif _addanother == "Save and add another":
            message =  f"The Product <a href='/{ADMIN_LINK}shop/product/{product_id}/change/'>{obj.product_name[0:16]}..</a> was Change successfully. You may add another product view below."
            messages.success(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/add/')
        elif _continue == "Save and continue editing":
            message =  f"The Product <a href='/{ADMIN_LINK}shop/product/{product_id}/change/'>{obj.product_name[0:16]}..</a> was Change successfully. You may edit it again below."
            messages.success(request , mark_safe(message))
            return redirect(f'/{ADMIN_LINK}shop/product/{product_id}/change/')


# class StoreAdmin(admin.ModelAdmin):
#     list_display =( 'store_name','store_user','image_tag' , 'issue_date' , 'live')
#     list_filter =('issue_date',)
#     list_editable = ('store_user', 'live')
#     search_fields = ('store_name', 'store_user', 'address' , 'issue_date')

class CategoryAdmin(admin.ModelAdmin):

    fieldsets = [
        ("Category", {
            "fields": (('category_name', 'active'),
                       ('slug', 'display_order', 'is_pinned'),
                       ('Category_image', 'cate_image')),
            "description": "The image is the card on the All products page. URL: /<slug>/ shows every live style of this category.",
        }),
        ("Styles page", {
            "fields": ('page_title', 'page_description'),
        }),
        ("SEO", {
            "fields": ('meta_title', 'meta_description'),
        }),
    ]
    prepopulated_fields = {"slug": ("category_name",)}

    readonly_fields = ('Category_image' ,  'Category_Banner')

    list_display =('Category_image', 'category_name' , 'slug', 'is_pinned', 'display_order', 'pub_date' , 'active')
    list_display_links = ('Category_image', 'category_name')
    list_filter =('pub_date',)
    list_editable = ('active', 'is_pinned', 'display_order')
    search_fields = ('category_name' , 'category' ,  'pub_date')


class OrderUpdateAdmin(admin.ModelAdmin):
    list_display =('order_id' , 'update_messages' , 'timestamp' )
    list_filter =('order_id' , 'timestamp',)
    search_fields = ('order_id' , 'update_messages' , 'timestamp')


class BannerAdmin(admin.ModelAdmin):
    list_display =( 'banner_title', 'image_tag' )



class ProductAttributeAdmin(admin.ModelAdmin):
    list_display=('product', 'image_tag' ,  'color', 'size')
    list_filter =('price',)
    search_fields = ('product__product_name','price')


class Product_BannerAdmin(admin.ModelAdmin):
    fields = (
        ('image_tag' , 'banner_image' , 'banner_name', 'banner_title' , 'landing_page_link' ),
     
    )
    readonly_fields = ('image_tag' ,)
    list_display = ('banner_name', 'banner_title' , 'landing_page_link' , 'id' , 'image_tag')




class ProductViewAdmin(admin.ModelAdmin):
    list_display=('device_ip', 'product' ,  'date',)
    list_filter =('product' ,  'date',)
    search_fields = ('device_ip', 'product__product_name')
# admin.site.register(ProductView , ProductViewAdmin)



class RatingAdmin(admin.ModelAdmin):
    list_display = ('product' , 'rating' , 'device_ip' , 'date')
    search_fields = ('product__product_name',)
    list_filter = ('product' , 'rating' , 'device_ip' , 'date')

# admin.site.register(Rating , RatingAdmin)

class KeyWordAdmin(admin.ModelAdmin):
    list_display = ('KeyWords', 'user', 'Date','DeviceIp')
    search_fields = ('KeyWords', 'user' , 'DeviceIp')
    list_filter = ('KeyWords', 'user' , 'DeviceIp' , 'Date')
# admin.site.register(KeyWord , KeyWordAdmin)







class ContactAdmin(admin.ModelAdmin):
    add_form_template = 'app/htnn.'

    list_display = ('name','email', 'phone', 'desc' , 'date')
    search_fields = ('name','email', 'phone', 'desc' , 'date')
    list_filter = ('name','email', 'phone', 'date')

    
# admin.site.register(Contact , ContactAdmin)



class UploadStickerAdmin(admin.ModelAdmin):
    fields = (
        ('Sticker_Name' , 'Sticker_type' , 'Sticker_Price'),
        ('Sticker_Image' , 'Sticker_Vector_File')
    )
    list_display = ('Sticker_Name','Sticker_type', 'Download_file' , 'date' , 'sticker_preview')
    search_fields = ('Sticker_Name','Sticker_type__type_name')
    list_filter = ('Sticker_Name', 'Sticker_type', 'date')

# admin.site.register(UploadSticker, UploadStickerAdmin)



class MockUpAdmin(admin.ModelAdmin):
    fields = (
        ('MockUp_Name'),
        ('MockUp_Fornt_Image' , 'MockUp_Back_Image'),
        ('MockUp_Left_Image' , 'MockUp_Right_Image'),
    )
    list_display = ('MockUp_Name' , 'date' , 'mockup_fornt_image' , "Active")
    list_editable = ('Active',)
    search_fields = ('MockUp_Name',)
    list_filter = ('MockUp_Name','date')

# Hidden from the admin menu: products use colour photos now, not mockups.
# Old mockups stay in the database (saved designs / orders still point to them).
# Remove the "#" below to show "07. MockUps" again.
# admin.site.register(MockUp, MockUpAdmin)




class ColorAdmin(admin.ModelAdmin):
    fields = (
        ('color_code' , 'color_name' , 'Available'),
        'family',
    )
    list_display = ('color_code' , 'color_Show' ,  'color_name' , 'family', 'Available' , 'date')
    list_editable = ('Available' , 'family')
    list_filter = ('family',)
    search_fields = ('color_code' , 'color_name' , 'Available' , 'date')

admin.site.register(Color , ColorAdmin)



class SizeAdmin(admin.ModelAdmin):
    fields = (
        ('Size_name' , 'Available', 'order')
    )
    list_display = ('Size_name' , 'order' , 'Available' , 'date')
    list_editable = ('order' , 'Available')  # change the order right from the list
    search_fields  = ('Size_name' , 'Available' , 'date')

admin.site.register(Size , SizeAdmin)



class CouponCodeAdmin(admin.ModelAdmin):
    fields = (
        ('coupon_title' , 'coupon_code','coupon_minus_value'),
        ('coupon_limit' , 'coupon_formula' , 'status')
    )
    list_display = ('coupon_title' , 'coupon_code' , 'coupon_limit' , 'coupon_formula')
    list_editable = ('coupon_formula' ,)
    search_fields  = ('coupon_title' , 'coupon_code')


admin.site.register(CouponCode,CouponCodeAdmin)
    

class SizeChartAdmin(admin.ModelAdmin):
    fields = (
        ('Title' , 'chart_image'),
    )
    list_display = ('Title',)
    search_fields  = ('Title',)

# admin.site.register(Size_Chart ,SizeChartAdmin)


# admin.site.register(Product ,ProductAdmin)
# admin.site.register(StickerType)
# admin.site.register(Order,OrderAdmin)
# admin.site.register(OrderUpdate , OrderUpdateAdmin)
admin.site.register(Category , CategoryAdmin)
# admin.site.register(Store , StoreAdmin)
# admin.site.register(Banner , BannerAdmin)
admin.site.register(ProductAttribute,ProductAttributeAdmin)
# admin.site.register(Product_Banner , Product_BannerAdmin)
# admin.site.register(ProductPreview )

class QuantityDiscountInline(admin.TabularInline):
    model = QuantityDiscount
    extra = 1



@admin.register(DesignPricing)
class DesignPricingAdmin(admin.ModelAdmin):
    inlines = [QuantityDiscountInline]
    # class Media:
    #     js = ('tiy1.js',)


class AddingTinyAdmin(admin.ModelAdmin):
    class Media:
        js = ('tiny2.js',)


    
admin.site.register(Province )
# admin.site.register(Country )
admin.site.register(ContactSupport )
admin.site.register(InstagramPost )
admin.site.register(ContactSales )
# Policy pages: text + SEO title / description
@admin.register(TermsCondition, PrivacyPolicy, ShippingPolicy)
class PolicyPageAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ('title', 'description')}),
        ("SEO", {"fields": ('meta_title', 'meta_description')}),
    ]

class GetApparelForSectionInline(admin.StackedInline):  # you can also use admin.StackedInline
    model = GetApparelForSection
    extra = 1  # how many empty forms to display
    # class Media:
    #     js = ('tiny2.js',)
    fields = (
        ('title',),
        ('description',),
    )  # which fields show inline


# admin.site.register(GetApparelForSection)
@admin.register(GetApparelFor)
class GetApparelForAdmin(admin.ModelAdmin):
    # list_display = ('title')  # optional: customize list view
    # prepopulated_fields = {"slug": ("title",)}  # auto-fill slug from title
    search_fields = ('title', 'subtitle')     # optional: enable search
    list_filter = ('title',)                  # optional: filter by title

    fields = (
        ('meta_title'),
        ('meta_description'),
        ('title_for_dropdown'),
        ('title'),
        ('slug'),
        ('subtitle',),
        ('description',),
        ('icon_class', 'image'),
        ('html_file'),
    )

    inlines = [GetApparelForSectionInline]

    # class Media:
    #     js = ('tiny2.js',)


# @admin.register(GetApparelForSection)
# class GetApparelForAdmin(admin.ModelAdmin):
#     list_filter = ('get_apparel_for',)
#     class Media:
#         js = ('tiny2.js',)



class AboutSectionsInline(admin.TabularInline):
    model = AboutSections
    extra = 1  # show 1 empty form for adding new sections
    fields = ('title', 'description', 'image')
    show_change_link = True


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_desc', 'long_desc')
    search_fields = ('title', 'short_desc', 'long_desc')
    inlines = [AboutSectionsInline]
    fieldsets = [
        (None, {"fields": ('title', 'short_desc', 'long_desc')}),
        ("SEO", {"fields": ('meta_title', 'meta_description')}),
    ]


class HeroFeatureInline(admin.TabularInline):
    model = HeroFeature
    extra = 1  # number of empty rows to display
    fields = ('icon', 'title', 'short_desc')
    show_change_link = True

class TopBannerTextInline(admin.TabularInline):
    model = TopBannerText
    extra = 1  # number of empty rows to display


class ClientInline(admin.TabularInline):
    model = Client
    extra = 1
    fields = ('title', 'image')
    show_change_link = True


class FaqInline(admin.TabularInline):
    model = Faq
    extra = 1
    fields = ('question', 'answer')
    show_change_link = True


@admin.register(Layout)
class LayoutAdmin(admin.ModelAdmin):
    list_display = ('header_button_text', 'hero_title')
    inlines = [HeroFeatureInline, ClientInline, FaqInline, TopBannerTextInline]
    fieldsets = (
        ('Header & Hero Section', {
            'fields': ('logo', 'favicon', 'header_banner_text', 'header_button_text', 'hero_title', 'hero_image')
        }),
    )


# Optional: Register others separately if needed
# @admin.register(HeroFeature)
# class HeroFeatureAdmin(admin.ModelAdmin):
#     list_display = ('title', 'short_desc', 'layout')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('title', 'layout')

@admin.register(SavedDesign)
class SavedDesignAdmin(admin.ModelAdmin):
    list_display = ('email', 'get_link', 'created_at')
    list_filter = ('email',)


# @admin.register(Faq)
# class FaqAdmin(admin.ModelAdmin):
#     list_display = ('question', 'layout')



class GuestCartItemInline(admin.TabularInline):
    model = GuestCartItem
    extra = 0  # no empty rows by default
    fields = ['size', 'quantity', 'personalization_display']
    readonly_fields = ['personalization_display']  # shop designs: customer text per piece

# @admin.register(GuestCart)
class GuestCartAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'product_attr', 'total_price', 'created_at']
    inlines = [GuestCartItemInline]


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'excerpt')
    list_filter = ('category',)

    # class Media:
    #     js = ('tiny.js',)


class ServiceSectionInline(admin.TabularInline):  # you can also use admin.StackedInline
    model = ServiceSection
    extra = 1  # how many empty forms to display
    fields = ('title', 'subtitle', 'image')  # which fields show inline



@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'setup_price', 'Per_Color_Price', 'Per_Location_Price', 'Rush', 'date')
    # prepopulated_fields = {"slug": ("title",)}  # auto-generate slug
    inlines = [ServiceSectionInline]  # connect sections inline
    fields = (
        ('meta_title'),
        ('meta_description'),
        ('title_for_dropdown'),
        ('title'),
        ('slug'),
        ('subtitle',),
        ('icon_class', 'image'),
        ('setup_price', 'Per_Color_Price'),
        ('Per_Location_Price', 'Rush'),
        ('html_file'),
    )


# @admin.register(ServiceSection)
# class ServiceSectionAdmin(admin.ModelAdmin):
#     list_display = ('service', 'title')
#     search_fields = ('title', 'subtitle')


# =====================================================================
# SHOP DESIGNS (Shop page products) + OCCASIONS
# =====================================================================
from django import forms
from django.forms.models import BaseInlineFormSet


class OccasionFaqInline(admin.TabularInline):
    model = OccasionFaq
    extra = 1
    fields = ('question', 'answer', 'order')


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ('card_preview', 'name', 'slug', 'show_in_menu', 'show_on_shop_page', 'order', 'live')
    list_display_links = ('card_preview', 'name')
    list_editable = ('show_in_menu', 'show_on_shop_page', 'order', 'live')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name', 'subtitle')
    readonly_fields = ('card_preview',)
    inlines = [OccasionFaqInline]
    fieldsets = [
        ("Card", {
            "fields": (('name', 'slug'),
                       'subtitle',
                       ('card_preview', 'image'),
                       ('card_color', 'text_tone'),
                       ('show_in_menu', 'show_on_shop_page', 'order', 'live')),
        }),
        ("Occasion page", {
            "fields": ('page_title', 'page_description', 'strip_title', 'seo_heading', 'seo_content'),
        }),
        ("SEO", {
            "fields": ('meta_title', 'meta_description'),
        }),
    ]


class ShopDesignColorFormSet(BaseInlineFormSet):
    """Colours must exist on the base product, and only one can be the default."""

    def clean(self):
        super().clean()
        base = self.instance.base_product if self.instance.base_product_id else None
        allowed = set(ProductAttribute.objects.filter(product=base).values_list('color_id', flat=True)) if base else set()
        defaults = 0
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            color = form.cleaned_data.get('color')
            if base and color and color.id not in allowed:
                form.add_error('color', f'"{color}" is not a colour of {base}. Add it to the base product first.')
            if form.cleaned_data.get('is_default'):
                defaults += 1
        if defaults > 1:
            raise forms.ValidationError('Only one colour can be the default.')


class ShopDesignColorInline(admin.TabularInline):
    model = ShopDesignColor
    formset = ShopDesignColorFormSet
    extra = 1
    fields = ('color', 'hero_image', 'back_image', 'is_default', 'order')


class ShopDesignImageInline(admin.TabularInline):
    model = ShopDesignImage
    extra = 1
    fields = ('image', 'alt_text', 'order')
    verbose_name_plural = "Gallery (extra photos / GIFs)"


class ShopDesignTextFieldInline(admin.TabularInline):
    model = ShopDesignTextField
    extra = 0
    fields = ('label', 'help_text', 'placeholder', 'max_length', 'required', 'order')
    verbose_name_plural = "Personalization text fields (Text 1, Text 2, ...)"


class ShopDesignForm(forms.ModelForm):
    class Meta:
        model = ShopDesign
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Base product dropdown: only "Shop" type products (plus the one already
        # chosen, so an older design never loses its base product)
        if 'base_product' in self.fields:
            q = Q(product_type='shop')
            if self.instance.pk and self.instance.base_product_id:
                q |= Q(pk=self.instance.base_product_id)
            self.fields['base_product'].queryset = Product.objects.filter(q).order_by('product_name')
            self.fields['base_product'].help_text = (
                'Only products with Product type = "Shop" are listed. '
                'Sizes, stock, fabric and size chart come from it.')

    def clean(self):
        data = super().clean()
        if data.get('is_personalizable') and not (data.get('allow_image_upload') or data.get('allow_text')):
            raise forms.ValidationError('A personalizable design needs "Allow image upload", "Allow text", or both.')
        discount, price = data.get('discount_price'), data.get('price')
        if discount is not None and price is not None and not (0 < discount < price):
            self.add_error('discount_price', 'Discount price must be above 0 and lower than Price (or leave it empty).')
        return data


@admin.register(ShopDesign)
class ShopDesignAdmin(admin.ModelAdmin):
    form = ShopDesignForm
    list_display = ('preview', 'name', 'base_product', 'price', 'discount_price', 'is_personalizable', 'is_best_seller', 'order', 'live', 'created')
    list_display_links = ('preview', 'name')
    list_editable = ('is_best_seller', 'order', 'live')
    list_filter = ('live', 'is_best_seller', 'is_personalizable', 'occasions', 'base_product')
    search_fields = ('name', 'short_description')
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ('occasions',)
    inlines = [ShopDesignColorInline, ShopDesignImageInline, ShopDesignTextFieldInline]
    fieldsets = [
        ("Design", {
            "fields": (('name', 'slug'),
                       ('base_product', 'price', 'discount_price'),
                       'occasions',
                       'short_description',
                       'description',
                       ('is_best_seller', 'order', 'live')),
        }),
        ("Personalization", {
            "description": "Turn on 'Is personalizable', then choose image upload, text, or both. "
                           "For text, add the text fields at the bottom of this page. "
                           "Customer text/photos only go with the order - product images never change.",
            "fields": ('is_personalizable',
                       ('allow_image_upload', 'image_upload_label', 'image_upload_help'),
                       'image_position_preview',
                       'allow_text',
                       'personalization_gif'),
        }),
        ("SEO", {
            "fields": ('meta_title', 'meta_description'),
        }),
    ]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        design = form.instance
        if design.wants_image and not design.image_position_preview:
            messages.info(request, f'Tip: add a "position preview" image to "{design}" so customers see where their photo goes.')
        if design.wants_text and not design.text_fields.exists():
            messages.warning(request, f'"{design}" allows text but has no text fields yet - add them at the bottom of the page.')
        if design.live and not design.colors.exists():
            messages.warning(request, f'"{design}" is live but has no colours/hero images, so it will not show on the shop.')


class ShopFeatureInline(admin.TabularInline):
    model = ShopFeature
    extra = 1
    fields = ('icon', 'title', 'subtitle', 'order')
    verbose_name_plural = "Trust strip (shop page + design pages)"


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    inlines = [ShopFeatureInline]
    fieldsets = [
        ('Header - "Shop designs" menu banner', {
            "fields": (('menu_promo_eyebrow', 'menu_promo_button'), 'menu_promo_title',
                       ('menu_promo_url', 'menu_promo_color'), 'menu_promo_image'),
        }),
        ('Header - "Custom merch" menu boxes', {
            "fields": (('design_box_title', 'design_box_cta'), 'design_box_text', ('design_box_url', 'design_box_color'),
                       ('idea_box_title', 'idea_box_cta'), 'idea_box_text', ('idea_box_url', 'idea_box_color')),
        }),
        ('Shop page (/shop/)', {
            "fields": (('hero_eyebrow', 'hero_button_text'), 'hero_title', ('hero_button_url', 'hero_color'), 'hero_image',
                       ('occasions_heading', 'best_sellers_heading', 'new_heading', 'designs_per_row'),
                       ('group_card_eyebrow', 'group_card_title'), 'group_card_text',
                       ('group_card_button1', 'group_card_button1_url'), ('group_card_button2', 'group_card_button2_url'),
                       ('idea_card_eyebrow', 'idea_card_title'), 'idea_card_text',
                       'shop_meta_title', 'shop_meta_description'),
        }),
        ('All occasions page (/shop/occasions/)', {
            "fields": ('occasions_page_title', 'occasions_page_intro', 'occasions_meta_title', 'occasions_meta_description'),
        }),
        ('All designs page (/shop/designs/)', {
            "fields": ('designs_page_title', 'designs_page_intro', 'designs_meta_title', 'designs_meta_description'),
        }),
        ('Group quote strip (occasion pages)', {
            "fields": ('strip_title', 'strip_text', ('strip_link_text', 'strip_url')),
        }),
        ('Design page', {
            "fields": ('personalize_heading', 'sizes_heading', 'details_heading'),
        }),
    ]

    def has_add_permission(self, request):
        # Only one settings record
        return not ShopSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False




admin.site.site_header="Ruii"
admin.site.site_title = "Ruii | Admin"
admin.site.index_title = "Welcome to Ruii"
admin.site.search_fields="search"



# =====================================================================
# PRODUCT PAGES (All products / styles page / product page texts)
# =====================================================================
class ProductTrustItemInline(admin.TabularInline):
    model = ProductTrustItem
    extra = 1
    fields = ('icon', 'text', 'order')
    verbose_name_plural = "Icons under 'Add your design'"


@admin.register(ProductPageSettings)
class ProductPageSettingsAdmin(admin.ModelAdmin):
    inlines = [ProductTrustItemInline]
    fieldsets = [
        ('All products page', {
            "fields": ('all_title', 'all_url', 'all_intro', 'styles_label', 'all_meta_title', 'all_meta_description'),
        }),
        ('Upload inspo card + popup', {
            "fields": ('inspo_on', 'inspo_card_text', 'inspo_title1', 'inspo_help1', 'inspo_placeholder', 'inspo_error',
                       'inspo_title2', 'inspo_help2', ('inspo_button', 'inspo_note'), 'inspo_success'),
        }),
        ('Product page', {
            "fields": ('includes_text',
                       ('delivery_min_days', 'delivery_max_days', 'delivery_region'), 'delivery_note',
                       ('request_colour_text', 'request_colour_link', 'request_colour_url'),
                       ('quote_link_text', 'cta_text'),
                       ('details_heading', 'size_chart_heading')),
        }),
    ]

    def has_add_permission(self, request):
        return not ProductPageSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InspoRequest)
class InspoRequestAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'email', 'short_idea', 'status', 'page', 'created')
    list_display_links = ('thumb', 'email')
    list_editable = ('status',)
    list_filter = ('status', 'created')
    search_fields = ('email', 'description')
    readonly_fields = ('thumb_large', 'image_link', 'email', 'description', 'page', 'created')
    fields = ('thumb_large', 'image_link', 'email', 'description', 'page', 'created', 'status', 'staff_note')

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:6px">', obj.image.url)
        return '-'
    thumb.short_description = 'Image'

    def thumb_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:320px;max-height:320px;border-radius:8px">', obj.image.url)
        return 'No image'
    thumb_large.short_description = 'Image'

    def image_link(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener" download>Download</a>', obj.image.url) if obj.image else '-'
    image_link.short_description = 'File'

    def short_idea(self, obj):
        return (obj.description[:70] + '...') if len(obj.description) > 70 else obj.description
    short_idea.short_description = 'Idea'

    def has_add_permission(self, request):
        return False


# ---------------- Media Library (upload a file, copy its full URL) ----------------
_COPY_JS = ("var i=this.parentNode.querySelector('input');i.select();"
            "try{navigator.clipboard.writeText(i.value)}catch(e){}document.execCommand('copy');"
            "var b=this,t=b.textContent;b.textContent='Copied!';setTimeout(function(){b.textContent=t},1500);return false;")


def _copy_box(value, label='Copy URL', width='100%'):
    return format_html(
        '<span style="display:flex;gap:6px;align-items:center;max-width:560px">'
        '<input type="text" readonly value="{}" onclick="this.select()" '
        'style="width:{};font-family:monospace;font-size:12px;padding:5px 7px">'
        '<button type="button" onclick="{}" style="all:unset;cursor:pointer;flex-shrink:0;white-space:nowrap;'
        'background:#47bac1;color:#fff;font-size:12px;font-weight:600;padding:7px 12px;border-radius:4px">{}</button></span>',
        value, width, _COPY_JS, label)


@admin.register(MediaLibraryFile)
class MediaLibraryFileAdmin(admin.ModelAdmin):
    list_display = ('preview', 'name', 'copy_url', 'uploaded_at')
    list_display_links = ('preview', 'name')
    search_fields = ('title', 'file')
    list_per_page = 50
    fields = ('title', 'file', 'preview_large', 'copy_url', 'copy_html', 'uploaded_at')
    readonly_fields = ('preview_large', 'copy_url', 'copy_html', 'uploaded_at')

    # remember the request so we can build the full https://domain/media/... URL
    def get_queryset(self, request):
        self._request = request
        return super().get_queryset(request)

    def full_url(self, obj):
        if not obj or not obj.file:
            return ''
        req = getattr(self, '_request', None)
        return req.build_absolute_uri(obj.file.url) if req else obj.file.url

    def name(self, obj):
        return str(obj)
    name.short_description = 'Name'

    def preview(self, obj):
        if obj.kind == 'image':
            return format_html('<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:6px">', obj.file.url)
        if obj.kind == 'video':
            return format_html('<video src="{}" muted preload="metadata" style="width:60px;height:60px;object-fit:cover;border-radius:6px"></video>', obj.file.url)
        return format_html('<span style="font-size:11px">{}</span>', os.path.splitext(obj.file.name)[1].upper() or 'FILE')
    preview.short_description = 'Preview'

    def preview_large(self, obj):
        if not obj or not obj.file:
            return 'Save first - the preview and URL appear here.'
        if obj.kind == 'image':
            return format_html('<img src="{}" style="max-width:360px;max-height:360px;border-radius:8px">', obj.file.url)
        if obj.kind == 'video':
            return format_html('<video src="{}" controls style="max-width:420px;border-radius:8px"></video>', obj.file.url)
        return format_html('<a href="{}" target="_blank" rel="noopener">Open file</a>', obj.file.url)
    preview_large.short_description = 'Preview'

    def copy_url(self, obj):
        url = self.full_url(obj)
        return _copy_box(url) if url else '-'
    copy_url.short_description = 'URL (copy & use anywhere)'

    def copy_html(self, obj):
        url = self.full_url(obj)
        if not url:
            return '-'
        if obj.kind == 'image':
            tag = f'<img src="{url}" alt="{obj.title}" loading="lazy">'
        elif obj.kind == 'video':
            tag = f'<video src="{url}" autoplay muted loop playsinline></video>'
        else:
            tag = f'<a href="{url}" target="_blank">{obj}</a>'
        return _copy_box(tag, 'Copy HTML')
    copy_html.short_description = 'Ready-made HTML tag'
