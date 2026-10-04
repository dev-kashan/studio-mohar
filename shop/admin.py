from django.contrib import admin

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

class ProductPreviewInline(admin.TabularInline):
    model = ProductPreview
    extra = 1

class ProductCompareInline(admin.TabularInline):
    model = CompetitorProduct
    extra = 1


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
    fields = ('size', 'unit_price','quantity','total_price')

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
        ('Front_Image', 'Back_Image', 'Left_Image', 'Right_Image'),
        ('Front_Desgin_Image', 'Back_Desgin_Image', 'Left_Desgin_Image', 'Right_Desgin_Image'),

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
        ('color', 'order_status', 'status'),
        ('unity_price', 'item_total', 'date', 'Active'),
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

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fieldsets = [
        ("", {
            "classes": ("collapse"),
            "fields": (('product_name') ,
                       ('size_available'),
                        ('printed_image', 'blank_image', 'size_chart_img'),
                        ('categories' , 'customize_mockup_template'),
                        # ('min_qty' , 'max_qty' ,),
                        # ('price' , 'sprice'),
                        ('short_desc'),
                        ('desc'),
                        ('live', 'is_best_seller', 'is_sustainable'),
                        ('Meta_title', 'Meta_description'),
                ),
        }),
        
       
        ("Competition Details", {
            "classes": ("collapse"),
            "fields": (('fabric_composition', "softness") ,
                       ('fabric_weight', 'fit'),
                       ('construction_quality', 'price_range'),
                       ('durability'),
                       ('compare_product_img'),
                ),
        }),
        
       
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
    list_display =('preview' , 'product_name', 'categories', 'stock' , 'pub_date' , 'live')
    list_filter =('product_id' , 'categories__category_name' ,   'Availibility' , 'live' , 'pub_date',)
    list_editable = ('live', ) 
    search_fields = ('product_name' ,'categories__category_name'  , 'categories__category' , 'desc', 'pub_date')
    inlines = [ProductCompareInline, ProductAttributeAdminInline, ProductPreviewInline]
    # ordering = ['Availibility']
 
    class Meta:
       model = Product

    
        

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

    fields =(
        ('category_name', 'active'),
        ('cate_image'),
      

    )

    readonly_fields = ('Category_image' ,  'Category_Banner')

    list_display =('category_name' , 'category' , 'offer' , 'pub_date' , 'active' , 'Category_image')
    list_filter =('pub_date',)
    list_editable = ('active',)
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

admin.site.register(MockUp, MockUpAdmin)




class ColorAdmin(admin.ModelAdmin):
    fields = (
        ('color_code' , 'color_name' , 'Available')
    )
    list_display = ('color_code' , 'color_Show' ,  'color_name' , 'Available' , 'date')
    list_editable = ('Available' ,)
    search_fields = ('color_code' , 'color_name' , 'Available' , 'date')

admin.site.register(Color , ColorAdmin)



class SizeAdmin(admin.ModelAdmin):
    fields = (
        ('Size_name' , 'Available')
    )
    list_display = ('Size_name' , 'Available' , 'date')
    list_editable = ('Available' ,)
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
admin.site.register(TermsCondition)
admin.site.register(PrivacyPolicy)
admin.site.register(ShippingPolicy)

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
        ('subtitle',),
        ('description',),
        ('icon_class', 'image'),
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
    fields = ['size', 'quantity']
    readonly_fields = []  # you can add fields here to make them non-editable if needed

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
        ('subtitle',),
        ('icon_class', 'image'),
        ('setup_price', 'Per_Color_Price'),
        ('Per_Location_Price', 'Rush'),
    )


# @admin.register(ServiceSection)
# class ServiceSectionAdmin(admin.ModelAdmin):
#     list_display = ('service', 'title')
#     search_fields = ('title', 'subtitle')




admin.site.site_header="Ruii"
admin.site.site_title = "Ruii | Admin"
admin.site.index_title = "Welcome to Ruii"
admin.site.search_fields="search"

