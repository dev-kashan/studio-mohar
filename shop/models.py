
from django.db import models
from django.contrib.auth.models import User, update_last_login
from django.db.models.signals import pre_save
from django.utils.html import mark_safe
from PIL import Image
from datetime import date, datetime
from django.utils.text import slugify
from colorfield.fields import ColorField

from django.template.loader import render_to_string
from newecom.settings import DEFAULT_FROM_EMAIL , EMAIL_HOST_USER 

from django.core.mail import send_mail 
from django.utils.html import strip_tags
from ckeditor.fields import RichTextField
import os
# from django.core.files.base import ContentFile
# from .utils.order_package import generate_order_zip


COLOR_CHOICES = (
    ('success', 'green'),
    ('primary', 'blue'),
    ('danger', 'red'),
    ('warning', 'yellow'),
    ('secondary', 'black'),
)

SHIP_TYPE = (
    ('standard', 'Standard'),
    ('rush', 'Rush'),
    ('waitsave', 'Wait & Save'),
)


YES_OR_NO = (
    ('Yes' , 'Yes'),
    ('No' , 'No')
)


COUPON_FORMULA = (
    ('percentage' , 'percentage'),
    ('value' , 'value')
)
COUPON_STATUS = (
    ('inactive', 'inactive'),
    ('active', 'active'),
)


class Size_Chart(models.Model):
    Title = models.CharField(max_length=100 , default='')
    chart_image = models.ImageField(upload_to="shop/images" ,  blank=True, null=True )
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.Title
    
    class Meta:
        verbose_name_plural = '17. Size Chart'

    
class CouponCode(models.Model):
    coupon_title = models.CharField(max_length=255,default='')
    coupon_code = models.CharField(max_length=255,default='')
    coupon_limit = models.CharField(max_length=255,default='')
    coupon_formula = models.CharField(max_length=50,default='percentage',choices=COUPON_FORMULA)
    coupon_minus_value = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50,default='inactive',choices=COUPON_STATUS)
    def __str__(self):
        return self.coupon_title

    class Meta:
        verbose_name_plural = '10. Coupon Code'




class StickerType(models.Model):
    type_name = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.type_name
    class Meta:
        verbose_name_plural = '12 Sticker Type'



class Color(models.Model):
    color_code = ColorField(default='' , blank=True , null=True)
    color_name = models.CharField(max_length=255 , default='' , blank=True , null=True)
    Available = models.CharField(choices=YES_OR_NO , default="Yes" , max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def color_Show(self):
        if self.color_code:
            return mark_safe('<div style="width:30px;height:30px;background-color:%s;"></div>' % (self.color_code))
        else:
            return mark_safe('------')


    def __str__(self):
        if self.color_name:
            return self.color_name
        else:
            return '----'

    class Meta:
        verbose_name_plural = '08. Colors'



class Size(models.Model):
    Size_name = models.CharField(max_length=255 , default='')
    Available = models.CharField(choices=YES_OR_NO , default="Yes" , max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.Size_name:
            return self.Size_name
        else:
            return '----'
    class Meta:
        verbose_name_plural = '09. Size'



class UploadSticker(models.Model):
    Sticker_Name = models.CharField(max_length=255)
    Sticker_type = models.ForeignKey(StickerType , on_delete=models.SET_NULL , null=True , blank=True)
    Sticker_Image = models.ImageField(upload_to="shop/stickers", max_length=10000 , default='shop/stickers/default_sticker.png')
    Sticker_Vector_File = models.ImageField(upload_to="shop/stickers", max_length=10000 , default='shop/stickers/default_sticker_file.png' , blank=True , null=True)
    Sticker_Price = models.FloatField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = '13 Upload Sticker'


    def sticker_preview(self):
        if self.Sticker_Image:
            return mark_safe('<img src="%s" class="admin_Category_image_per"/>' % (self.Sticker_Image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_image_per"/>')
        
    
    def Download_file(self):
        if self.Sticker_Vector_File:
            return mark_safe(f'<a href="{self.Sticker_Vector_File.url}" download>Download FIle</a>')
        else:
            return mark_safe(f'<a href="#">Download FIle</a>')

    def __str__(self):
        return self.Sticker_Name


# Category
class Category(models.Model):
    category_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    
    category_name = models.CharField(max_length=50, default=""  , verbose_name="Category")
    category = models.CharField(max_length=60, default="" , verbose_name="Category") 
    subcategories = models.CharField(
        max_length=50, default="", blank=True, null=True)
    offer = models.CharField(max_length=50 , default="new", blank=True, null=True)
    cate_image = models.ImageField(
        upload_to="shop/images", default="shop/images/noperview.jpg", blank=True, null=True)
    landscape_image = models.ImageField(
        upload_to="shop/images", default="shop/images/noperview.jpg", blank=True, null=True)
    pub_date = models.DateField(auto_now_add=True ,  blank=True, null=True)
    active = models.BooleanField(default=False)
    
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     imag = Image.open(self.cate_image.path)
    #     if imag.width > 300 or imag.height> 300:
    #         output_size = (500, 500)
    #         imag.thumbnail(output_size)
    #         imag.save(self.cate_image.path)
            


    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name_plural = '01. Category'

    def Category_image(self):
        if self.cate_image:
            return mark_safe('<img src="%s" class="admin_Category_image_per"/>' % (self.cate_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_image_per"/>')
    
    def Category_Banner(self):
        if self.landscape_image:
            return mark_safe('<img src="%s" class="admin_Category_Banner_per"/>' % (self.landscape_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_Banner_per"/>')


# Store
# class Store(models.Model):
#     store_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
#     store_user = models.ForeignKey(User, on_delete=models.CASCADE , default="" , blank=True, null=True)
#     store_name = models.CharField( max_length=50, default="", blank=True, null=True)
#     store = models.CharField(max_length=60, default="")
#     address = models.TextField( max_length=20000, default="", blank=True, null=True)
#     logo = models.ImageField( upload_to="shop/images", default="", blank=True, null=True)
#     store_product_img = models.ImageField(upload_to="shop/images", default="shop/img/noimage.jpg", blank=True, null=True)
#     issue_date = models.DateField(blank=True, null=True)
#     live = models.BooleanField(default=False)
    

    
#     def __unicode__(self):
#         return self.store_name

#     @staticmethod
#     def get_all_categories():
#         return Store.objects.all()

#     def __str__(self):
#         return self.store_name
    
#     def image_tag(self):
#         return mark_safe('<img src="%s" width="50" height="50"/>' % (self.logo.url))
    




class MockUp(models.Model):
    MockUp_Name = models.CharField(max_length=255)
    MockUp_Fornt_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_front.png')
    MockUp_Back_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_back.png')
    MockUp_Left_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_back.png')
    MockUp_Right_Image = models.ImageField(upload_to="shop/stickers", max_length=1000 , default='shop/stickers/default_mockup_back.png')
    Mockup_banner = models.ImageField(upload_to="shop/stickers" , default='shop/stickers/default_mockup_back.png')
    Price = models.FloatField(default=0)
    Active = models.CharField(max_length=244 , choices=YES_OR_NO , default="No")
    date = models.DateTimeField(auto_now_add=True)

    def mockup_fornt_image(self):
        if self.MockUp_Fornt_Image:
            return mark_safe('<img src="%s" class="admin_Category_image_per"/>' % (self.MockUp_Fornt_Image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" class="admin_Category_image_per"/>')
        
    def __str__(self):
        return self.MockUp_Name
    
    class Meta:
        verbose_name_plural = '07. MockUps'



# All Product
class Product(models.Model):
    product_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE , default="" ,  blank=True, null=True)
    # brand = models.CharField(max_length=200, default="", blank=True, null=True)
    product_name = models.CharField(max_length=200, default="" , blank=True, null=True)
    is_best_seller = models.BooleanField(default=False, blank=True, null=True)
    is_sustainable = models.BooleanField(default=False, blank=True, null=True, verbose_name='Is Trending')

    size_available = models.CharField(max_length=200, default="" , blank=True, null=True)
    # product_model = models.CharField(max_length=225 , default="" , blank=True, null=True)
    # product_code = models.CharField(max_length=225 , default="")
    categories = models.ForeignKey(Category, on_delete=models.SET_NULL , default="" , blank=True, null=True)
    # sub_categories = models.CharField(max_length=50, default="", blank=True, null=True)
    Availibility = models.IntegerField(default=0)
    min_qty = models.IntegerField(default=1 , blank=True, null=True)
    max_qty = models.IntegerField(default=5 , blank=True, null=True)

    customize_mockup_template  = models.ForeignKey(MockUp , on_delete=models.SET_NULL , null=True , blank=True)
    size_chart_img = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)

    Slug = models.SlugField(max_length=255 , default="", blank=True, null=True)
    Meta_title = models.CharField(max_length=255 , default="", blank=True, null=True)
    Meta_description = models.TextField(max_length=1000, default="", blank=True, null=True)

    # price = models.FloatField(default=0 , blank=True, null=True)
    # sprice = models.FloatField(default=0, blank=True, null=True , verbose_name="Discount Price")
    # offer_tag = models.CharField(max_length=200, default="", blank=True, null=True)
    desc = models.TextField(max_length=9999999999999999999 , default="", blank=True, null=True , verbose_name="Descriptions")
    short_desc = models.TextField(max_length=9999999999999999999 , default="", blank=True, null=True , verbose_name="Short Description")
    pub_date = models.DateTimeField(auto_now_add=True, max_length=12 , blank=True, null=True)
    # show_in_slider =  models.BooleanField(default=False)
    # product_weight = models.CharField(max_length=2000, default="")
    # flash_sale = models.BooleanField(default=False)
    live = models.BooleanField(default=False)

    printed_image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    blank_image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)

    fabric_composition = models.CharField(max_length=255, blank=True, null=True)
    compare_product_img = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    softness = models.CharField(max_length=50, blank=True, null=True)
    fabric_weight = models.CharField(max_length=50, blank=True, null=True)
    fit = models.CharField(max_length=50, blank=True, null=True)
    construction_quality = models.CharField(max_length=50, blank=True, null=True)
    price_range = models.CharField(max_length=50, blank=True, null=True)
    durability = models.CharField(max_length=50, blank=True, null=True)


    def save(self, *args, **kwargs):
        self.Slug = slugify(self.product_name)
        super(Product, self).save(*args, **kwargs)
    

    def stock(self):
        if self.Available() > 0:
            return mark_safe(f'<p style="color: #1b8900;white-space: nowrap; background: #2cdd0036;padding: 4px 7px;border-radius: 10px;margin: 0px 0px;text-align: center;">{self.Available()} in Stock</p>')
        else:
            return mark_safe(f'<p style="color: #f30c0c; white-space: nowrap;background: #dd000036;padding: 4px 7px;border-radius: 10px;margin: 0px 0px;text-align: center;">{self.Available()} Out Of Stock</p>')
    
    def __unicode__(self):
        return self.product_name



    def Available(self):
        all_avaliblity = 0
        if self.product_id:
            find_prod_attri = ProductAttribute.objects.filter(product__product_id=self.product_id)
            for i in find_prod_attri:
                all_avaliblity += i.Availibility 
            return all_avaliblity
        else:
            all_avaliblity = 0
            return all_avaliblity


    @staticmethod
    def get_all_products():
        return Product.objects.all()

    @staticmethod
    def get_all_products_by_categoryid(category_id):
        if category_id:
            return Product.objects.filter(categories=category_id)
        else:
            return Product.get_all_products()

    @staticmethod
    def get_all_products_by_storeid(store_id):
        if store_id:
            return Product.objects.filter(store=store_id)
        else:
            return Product.get_all_products()

    def __str__(self):
        return self.product_name

    
    def preview(self):
        if self.blank_image:
            return mark_safe(f'<img src="/media/{self.blank_image}" width="50" height="50"/>')
        else:
            attr = ProductAttribute.objects.filter(product__product_id=self.product_id).first()
            if attr:
                return mark_safe(f'<img src="/media/{attr.image}" width="50" height="50"/>')
            else:
                return mark_safe(f'<img src="/media/shop/images/noperview.jpg" width="50" height="50"/>')

    class Meta:
        verbose_name_plural = '02. Products'

class ProductPreview(models.Model):
    VIEW_CHOICES = [
        ('front', 'Front'),
        ('back', 'Back'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="previews")
    view_type = models.CharField(max_length=20, choices=VIEW_CHOICES)
    image = models.ImageField(upload_to='shop/product_previews/')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.product_name} - {self.view_type} ({self.order})"



#contact
class Contact(models.Model):
    msg_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    name = models.CharField(max_length=70, default="")
    email = models.CharField(max_length=70, default="")
    phone = models.CharField(max_length=70, default="")
    desc = models.TextField(max_length=1000, default="" , verbose_name='message')
    date = models.DateTimeField(auto_now_add=True, max_length=12)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '11. Contacts'


def code_gen(word , obj):
    last_id = obj.objects.all().last()
    if last_id:
        if int(last_id.order_id) > 0:
            incres_id = int(last_id.order_id) + 1
        else:
            incres_id = 1
            
        now = date.today()
        str_date = now.strftime("%m%d%Y")
        cn_formet = f'{word}-{str_date}{incres_id}'
        return cn_formet
    else:
        incres_id = 1
        now = date.today()
        str_date = now.strftime("%m%d%Y")
        cn_formet = f'{word}-{str_date}{incres_id}'
        return cn_formet




class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Province(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    delivery_charge = models.PositiveIntegerField(default=0)
    tax = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = '20. Province'

    def __str__(self):
        return self.name
 

# Order
class Order(models.Model):
    order_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    Order_number = models.CharField(max_length=70, default="" ,  blank=True, null=True)
    # user = models.ForeignKey(User, on_delete=models.CASCADE , default="" ,  blank=True, null=True)
    name = models.CharField(max_length=70, default="")
    # ip_address = models.CharField(max_length=500, default="" , blank=True, null=True)
    email = models.CharField(max_length=70, default="")
    address = models.TextField(max_length=300, default="")
    apartment_suite = models.CharField(max_length=250, default='', blank=True, null=True)
    company = models.CharField(max_length=250, default='', blank=True, null=True)
    Country = models.ForeignKey(Country, on_delete=models.CASCADE, default=None, blank=True, null=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, default=None, blank=True, null=True)
    zip_code = models.CharField(max_length=70, default="", blank=True, null=True)
    city = models.CharField(max_length=70, default="", blank=True, null=True)
    phone = models.CharField(max_length=11, default="")
    promo = models.CharField(max_length=100, default="" , blank=True, null=True)
    coupon = models.ForeignKey(CouponCode, on_delete=models.CASCADE , blank=True,null=True)
    discount_amount = models.CharField(max_length=255,default='', verbose_name="Discount")
    # Home_or_office = models.CharField(max_length=100, default="")
    # Payment_method = models.CharField(max_length=100, default="")
    SubTotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    Delivery = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Grand Total'
    )
    special_instructions = models.TextField(max_length=2000 ,  default="" , blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, max_length=12)
    Active = models.BooleanField(default=False)
    ship_type = models.CharField(max_length=70, default="", blank=True, null=True, choices=SHIP_TYPE)

    estimated_delivery_time = models.DateField(auto_now_add=False)

    order_detail_zip = models.FileField(
        upload_to='order_packages/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name
    
    def generate_zip(self):
        """
        Generate the ZIP for this order and return it as an HTTP response for download.
        No file is saved in the database.
        """
        from django.http import HttpResponse
        from .utils.order_package import generate_order_zip_file
        try:
            zip_buffer = generate_order_zip_file(self)
            zip_buffer.seek(0)  # make sure buffer is at the start

            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename=ORDER_{self.Order_number}.zip'
            return response

        except Exception as e:
            print(f"Error generating ZIP for Order {self.Order_number}: {e}")
            return HttpResponse("Failed to generate ZIP.", status=500)


    def save(self, *args, **kwargs):
        if not self.Order_number:
            self.Order_number = code_gen('SM', Order)

        super(Order, self).save(*args, **kwargs)

        # ✅ Generate/update ZIP only once per order
        # try:
        #     from .utils.order_package import generate_order_zip_file
        #     from django.core.files.base import ContentFile

        #     zip_buffer = generate_order_zip_file(self)

        #     # overwrite previous ZIP
        #     self.order_detail_zip.save(
        #         f'ORDER_{self.Order_number}.zip',
        #         ContentFile(zip_buffer.read()),
        #         save=False
        #     )

        #     super(Order, self).save(update_fields=['order_detail_zip'])

        # except Exception as e:
        #     print(f"Error generating ZIP for Order {self.Order_number}: {e}")





    
    def nofity(self):
        today = datetime.now()
        # print(today.date() , self.created.date())
        if today.date() == self.created.date() and self.Active == False:
            return mark_safe('<p style="margin: 0px;background: #ff000066;text-align: center;padding: 5px 9px;border-radius: 50px;color: #b70000; font-weight: bold;white-space: nowrap;">New Order</p>')
        elif  self.Active == True:
            return mark_safe('<p style="margin: 0px;background: #00ff1f66;text-align: center;padding: 5px 9px;border-radius: 50px;color: #005c21; font-weight: bold;white-space: nowrap;">Active Order</p>')

        else:
            return mark_safe('<p style="margin: 0px;background: #fff70066;text-align: center;padding: 5px 9px;border-radius: 50px;color: #a99507; font-weight: bold;white-space: nowrap;">UnActive Order</p>')


    def Total_items(self):
        order_items_list = OrderItem.objects.filter(order_by__order_id=self.order_id)
        count_total = order_items_list.count()
        item_concatinate = ''
        for i in order_items_list:
            if i.status == 'processing':
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: #192ee4; font-weight: bold;">P , </span>'
                
            elif i.status == 'shipped':
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: #d9be00; font-weight: bold;">S , </span>'
            
            elif i.status == 'delivered':
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: #005c21; font-weight: bold;">D , </span>'
            
            else:
                item_concatinate += f'<span style="text-align: center;padding: 5px 2px;color: red; font-weight: bold;">C , </span>'
                
        return mark_safe(f'<p style="text-align: center;padding: 5px 9px;white-space: nowrap; font-weight: bold;">{item_concatinate} Total item {count_total}</p>'  )
        
    class Meta:
        verbose_name_plural = '05. Orders'

STATUS = (
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered' , 'Delivered'),
    ('cancelation' , 'Cancelation')
)


ORDER_TYPE = (
    ('Customize', 'Customize'),
    ('Normal', 'Normal'),
)



class OrderItem(models.Model):
    order_by = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_item = models.ForeignKey(Product, on_delete=models.SET_DEFAULT , default='' ,  blank=True, null=True)
    product_name = models.CharField(max_length=255, default="")
    # product_brand = models.CharField(max_length=255, default="", blank=True, null=True)
    # quantity = models.IntegerField(default="" )
    # size = models.CharField(max_length=255, default="", blank=True, null=True)
    color = models.CharField(max_length=255, default="", blank=True, null=True)
    unity_price = models.FloatField(default=0)
    # weight = models.CharField(default='0' , max_length=255 , blank=True, null=True)
    item_total = models.FloatField(default=0)
    image = models.TextField(default="")
    date = models.DateTimeField(auto_now_add=True, max_length=12)
    status = models.CharField(choices=STATUS , max_length=50 , default='processing')
    order_status = models.CharField(max_length=255, default="" ,  blank=True, null=True , verbose_name='On Flash Sale')

    Mockup = models.ForeignKey(MockUp , on_delete=models.SET_DEFAULT , default='' ,  blank=True, null=True)
    Order_Type = models.CharField(max_length=200 , choices=ORDER_TYPE , default='Normal')
    Front_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Front Image')
    Back_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Back Image')
    Left_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Left Image')
    Right_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True, verbose_name='Right Image')
    
    Front_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    Back_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    Left_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    Right_Desgin_Image = models.ImageField(upload_to='shop/images', max_length=1000, default='', blank=True, null=True)
    # Front_Text = models.CharField(max_length=255, default="", blank=True, null=True)
    # Back_Text = models.CharField(max_length=255, default="", blank=True, null=True)

    # availibile_minus = models.BooleanField(default=False , blank=True, null=True , editable=False)
    # cancel_availibile_minus_field = models.BooleanField(default=False , blank=True, null=True , editable=False)

    Active = models.BooleanField(default=False) 
    
    def  __str__(self):
        return self.product_name[0:20] + "..."
    
    def Order_by_Id(self):
        if self.order_by:
            return self.order_by.order_id
        else:
            return ''
    def image_thumbnail(self):
        if self.image:
            return mark_safe('<img class="order_item_img" src="%s" width="50" height="50"/>' % (self.image))
        else:
            return mark_safe('<img class"order_item_img" src="/media/shop/images/noperview.jpg" width="50" height="50"/>')
        

    def save(self, *args, **kwargs):
        super(OrderItem, self).save(*args, **kwargs)

        orderid = self.id
        if not orderid:
            return

        try:
            order_item = OrderItem.objects.get(id=orderid)
        except OrderItem.DoesNotExist:
            return

        # Skip if no product
        if not order_item.order_item:
            return

        try:
            # Find matching product attribute (based on color only)
            if order_item.color not in [None, '', 'undefined', 'None']:
                filter_ava = ProductAttribute.objects.filter(
                    product__product_id=order_item.order_item.product_id,
                    color__color_name=order_item.color
                ).first()
            else:
                filter_ava = ProductAttribute.objects.filter(
                    product__product_id=order_item.order_item.product_id
                ).first()

            if not filter_ava:
                return

            # Quantity adjustment (if quantity field added later)
            calcul = getattr(order_item, 'quantity', 1)

            # Decrease stock when new order
            if order_item.Active is False and order_item.status != "cancelation":
                stock_update = filter_ava.Availibility - calcul
                order_item.Active = True
                order_item.save(update_fields=['Active'])
                ProductAttribute.objects.filter(id=filter_ava.id).update(Availibility=stock_update)

            # Restore stock when canceled
            elif order_item.status == "cancelation" and not order_item.Active:
                stock_update = filter_ava.Availibility + calcul
                order_item.Active = True
                order_item.save(update_fields=['Active'])
                ProductAttribute.objects.filter(id=filter_ava.id).update(Availibility=stock_update)

                # Send cancellation email
                params = {
                    'order_id': self.order_by.Order_number,
                    'name': self.order_by.name,
                    'email': self.order_by.email,
                    'address': self.order_by.address,
                    'city': self.order_by.city,
                    'country': self.order_by.country,
                    'phone': self.order_by.phone,
                    'date': self.order_by.created,
                    'item': order_item
                }
                html_message = render_to_string('shop/order_cancel_mail.html', params)
                plain_message = strip_tags(html_message)
                send_mail(
                    'Order Cancelled',
                    plain_message,
                    DEFAULT_FROM_EMAIL,
                    [self.order_by.email, EMAIL_HOST_USER],
                    html_message=html_message
                )

        except Exception as e:
            print(f"Error updating stock for OrderItem {orderid}: {e}")

        # ✅ Generate/update order ZIP whenever an item is saved
        # try:
        #     from .utils.order_package import generate_order_zip_file
        #     from django.core.files.base import ContentFile

        #     order = self.order_by
        #     zip_buffer = generate_order_zip_file(order)
        #     order.order_detail_zip.save(
        #         f'ORDER_{order.Order_number}.zip',
        #         ContentFile(zip_buffer.read()),
        #         save=False
        #     )
        #     super(Order, order).save(update_fields=['order_detail_zip'])

        # except Exception as e:
        #     print(f"Error generating ZIP for Order {self.order_by.Order_number}: {e}")



 
                # except:
                #     pass




    class Meta:
        verbose_name_plural = '06. Order Item'


class OrderItemSize(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.FloatField(default=0)
    total_price = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.size} - {self.quantity}"


# Order_Update
class OrderUpdate(models.Model):
    update_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    order_id = models.IntegerField(default="")
    update_messages = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return self.update_messages[0:7] + "..."


    class Meta:
        verbose_name_plural = '08. Order Update'

#Banner
class Banner(models.Model):
    banner_title = models.CharField(max_length=200 , default="" , blank=True, null=True)
    landing_page_link = models.CharField(max_length=200 , default="#" , blank=True, null=True)
    pc_banner_image = models.ImageField(upload_to="shop/banner", blank=True, null=True)
    mobile_banner_image = models.ImageField(upload_to="shop/banner", blank=True, null=True)
    background_color = models.CharField(max_length=200 , default="" , blank=True, null=True)

    def __str__(self):
        return self.banner_title

    def image_tag(self):
        if self.pc_banner_image:
            return mark_safe('<img src="%s" width="50" />' % (self.pc_banner_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" width="50" height="50"/>')

    class Meta:
        verbose_name_plural = '09. Banners'


class CompetitorProduct(models.Model):
    main_product = models.ForeignKey(Product, on_delete=models.CASCADE) # your rull shirt
    competitor_name = models.CharField(max_length=200)
    competitor_image = models.ImageField(upload_to='competitor', blank=True, null=True)

    # the comparison fields
    fabric_composition = models.CharField(max_length=255, blank=True, null=True)
    softness = models.CharField(max_length=50, blank=True, null=True)
    fabric_weight = models.CharField(max_length=50, blank=True, null=True)
    fit = models.CharField(max_length=50, blank=True, null=True)
    construction_quality = models.CharField(max_length=50, blank=True, null=True)
    price_range = models.CharField(max_length=50, blank=True, null=True)
    durability = models.CharField(max_length=50, blank=True, null=True)


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE , default="" , blank=True , null=True)
    color = models.ForeignKey(Color , on_delete=models.SET_NULL , null=True , blank=True)
    size = models.ForeignKey(Size , on_delete=models.SET_NULL , null=True , blank=True)
    # color = models.CharField(max_length=100 , default="" , blank=True , null=True) 
    # size = models.CharField(max_length=100 , default="" , blank=True , null=True)
    price= models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, blank=True, null=True)
    Availibility = models.IntegerField(default=0, blank=True, null=True , verbose_name='Availibility')
    Max_Qty = models.IntegerField(default=0, blank=True, null=True , verbose_name='Max Qty')
    weight = models.FloatField(default=0, blank=True, null=True)
    image = models.ImageField(upload_to="shop/images", default='shop/images/noperview.jpg' ,  blank=True, null=True)
    ogg_image = models.ImageField(upload_to="shop/images/ogg_image", default="shop/images/noperview.jpg",  blank=True, null=True)
    video_URL = models.CharField(max_length=255, default='' , blank=True , null=True)
    selected = models.BooleanField(default=True)
    select_for_color = models.CharField(max_length=50, default='' , blank=True , null=True)

    # def save(self, *args, **kwargs):
    #     if self.selected == True:
    #         if self.color:
    #             self.select_for_color = self.color

    #     super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.product_name} - {self.product.product_id}'

    def image_tag(self):
        if self.image:
            return mark_safe('<img src="%s" width="50" height="50"/>' % (self.image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" width="50" height="50"/>')
    
    class Meta:
        verbose_name_plural = '03. Product Variation'
    
  
class Product_Banner(models.Model):
    banner_name = models.CharField(max_length=200 , default="" , blank=True , null=True)         
    banner_title = models.CharField(max_length=255 , default="" , blank=True , null=True)
    banner_image = models.ImageField(upload_to="shop/images" ,  blank=True, null=True )
    landing_page_link = models.CharField(max_length=255 , default="#" , blank=True , null=True)

    def __str__(self):
        if self.banner_name:
            return self.banner_name
        else:
             return self.id
   
    def image_tag(self):
        if self.banner_image:
            return mark_safe('<img src="%s" width="70" height="50" >' %(self.banner_image.url))
        else:
            return mark_safe('<img src="/media/shop/images/noperview.jpg" width="70" height="50"/>')

    class Meta:
        verbose_name_plural = '04. Product Banner'     
        
      

class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE , default="")
    device_ip = models.CharField(max_length=255 , default="")
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.device_ip
    
    class Meta:
        verbose_name_plural = '05. Product Views'
    
    
    
class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE , related_name='rates') 
    device_ip = models.CharField(max_length=100 , default='')
    rating = models.FloatField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.device_ip

    class Meta:
        verbose_name_plural = '10. Ratings'

class KeyWord(models.Model):
    KeyWords = models.CharField(max_length=200 , default="")
    Date = models.DateField(auto_now_add=True)
    DeviceIp = models.CharField(max_length=200 , default="",blank=True, null=True)
    user =  models.ForeignKey(User, on_delete=models.SET_NULL ,default=None, blank=True, null=True )
    def __str__(self):
        return self.KeyWords
    class Meta:
        verbose_name_plural = '11. KeyWords'

import uuid
class SavedDesign(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField()
    design_name = models.CharField(max_length=250, default='', blank=True, null=True )
    front_json = models.TextField(blank=True, null=True)
    back_json = models.TextField(blank=True, null=True)
    left_sleeve = models.TextField(blank=True, null=True)
    right_sleeve = models.TextField(blank=True, null=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product , on_delete=models.CASCADE, null=True, blank=True)
    product_attr = models.ForeignKey(ProductAttribute , on_delete=models.CASCADE, null=True, blank=True)
    mockup = models.ForeignKey(MockUp , on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_link(self):
        return f"/design/{self.uid}/"

    def __str__(self):
        return f"/design/{self.uid}/"

    class Meta:
        verbose_name_plural = '21. Saved Design'
    



class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '11. Blog Category'


class BlogPost(models.Model):
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, related_name="posts")
    meta_title = models.CharField(max_length=255, default='' ,blank=True, null=True)
    meta_description = models.TextField(default='' ,blank=True, null=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField()
    content = RichTextField(default="")
    image = models.ImageField(upload_to="shop/blog_images/")
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '12. Blog Post'
    
    
class Service(models.Model):
    meta_title = models.CharField(max_length=255, default='' ,blank=True, null=True)
    meta_description = models.TextField(default='' ,blank=True, null=True)
    title_for_dropdown = models.CharField(max_length=255, default='')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    subtitle = RichTextField(default='')
    icon_class = models.CharField(max_length=250, default='')
    image = models.ImageField(upload_to="shop/blog_images")
    setup_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    Per_Color_Price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    Per_Location_Price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    Rush = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate base slug from title
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = "service"  # fallback if title is empty or invalid

            slug = base_slug
            counter = 1

            # Ensure uniqueness
            while Service.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '13. Service'
    
class GetApparelFor(models.Model):
    meta_title = models.CharField(max_length=255, default='' ,blank=True, null=True)
    meta_description = models.TextField(default='' ,blank=True, null=True)
    title_for_dropdown = models.CharField(max_length=255, default='')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    subtitle = models.TextField()
    description = RichTextField(blank=True, null=True)
    icon_class = models.CharField(max_length=250, default='')
    image = models.ImageField(upload_to="shop/blog_images")
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = "item"
            slug = base_slug
            counter = 1
            while GetApparelFor.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '14. Get Apparel For'

class GetApparelForSection(models.Model):
    get_apparel_for = models.ForeignKey(GetApparelFor, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    description = RichTextField(blank=True, null=True)

    def __str__(self):
        return f'{self.get_apparel_for.title} - {self.id}'

    class Meta:
        verbose_name_plural = '15. Get Apparel For Section'


class ServiceSection(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    subtitle = RichTextField(default='')
    image = models.ImageField(upload_to="shop/blog_images")

    def __str__(self):
        return f'{self.service.title} - {self.id}'

    class Meta:
        verbose_name_plural = 'Service Sections'
    
class GuestCart(models.Model):
    session_id = models.CharField(max_length=100, db_index=True)
    save_design_uid = models.CharField(max_length=1000, default='', blank=True, null=True)
    product_attr = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)

    # Mockup preview images
    front_image = models.TextField(blank=True, null=True)
    back_image = models.TextField(blank=True, null=True)
    left_image = models.TextField(blank=True, null=True, default='')
    right_image = models.TextField(blank=True, null=True, default='')

    # Raw design-only images (for printing)
    front_design_image = models.TextField(blank=True, null=True)
    back_design_image = models.TextField(blank=True, null=True)
    left_design_image = models.TextField(blank=True, null=True)
    right_design_image = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    price_of_each = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"GuestCart {self.session_id} - {self.product_attr}"

    

class GuestCartItem(models.Model):
    cart = models.ForeignKey(GuestCart, on_delete=models.CASCADE, related_name='cart_items')
    size = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.FloatField(default=0)
    total_price = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.size} × {self.quantity}"
  
class CartUploadedFile(models.Model):
    cart = models.ForeignKey(
        GuestCart,
        on_delete=models.CASCADE,
        related_name="uploaded_files"
    )

    file = models.FileField(
        upload_to="cart_uploaded_files/"
    )

    filename = models.CharField(
        max_length=255
    )

    side = models.CharField(
        max_length=20,
        choices=[
            ("front", "Front"),
            ("back", "Back"),
            ("left_sleeve", "Left Sleeve"),
            ("right_sleeve", "Right Sleeve"),
        ]
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.side})"


class OrderItemUploadedFile(models.Model):
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="uploaded_files"
    )

    file = models.FileField(upload_to="order_uploaded_files/")
    filename = models.CharField(max_length=255)
    side = models.CharField(
        max_length=20,
        choices=[
            ("front", "Front"),
            ("back", "Back"),
            ("left_sleeve", "Left Sleeve"),
            ("right_sleeve", "Right Sleeve"),
        ]
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.side})"


class DesignPricing(models.Model):
    # Existing fields
    embroidery_note = RichTextField(default="")


    front_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    back_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    left_sleeve_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    right_sleeve_price = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    embroidery_extra = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)


    standard_shipping_time =models.CharField(max_length=250, default='10-15')
    rush_shipping_time =models.CharField(max_length=250, default='7-10')

    # --- New dynamic shipping fields ---
    free_shipping_subtotal_threshold = models.DecimalField(
        max_digits=8, decimal_places=2, default=250.00,
        help_text="If subtotal is above this value, shipping becomes free."
    )
    free_shipping_postal_letters = models.CharField(
        max_length=100, default="L,M",
        help_text="Comma-separated list of first letters for free shipping (e.g. L,M)"
    )
    extra_charge_second_digit = models.CharField(
        max_length=5, default="0",
        help_text="If postal code's second digit matches this, extra charge applies."
    )
    extra_charge_amount = models.DecimalField(
        max_digits=6, decimal_places=2, default=5.00,
        help_text="Extra shipping charge for specific second digit postal codes."
    )
    rush_shipping_fee = models.DecimalField(
        max_digits=6, decimal_places=2, default=20.00,
        help_text="Extra cost for rush shipping."
    )
    waitsave_discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=30.00,
        help_text="Percentage discount for Wait & Save shipping."
    )

    class Meta:
        verbose_name_plural = '18. Design Pricing'



    def __str__(self):
        return "Design & Shipping Pricing Settings"


class QuantityDiscount(models.Model):
    pricing = models.ForeignKey(DesignPricing, on_delete=models.CASCADE, related_name='discount_tiers')
    min_qty = models.PositiveIntegerField()
    max_qty = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for open-ended range (e.g. 1000+)")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage discount")

    class Meta:
        ordering = ['min_qty']

    def __str__(self):
        if self.max_qty:
            return f"{self.min_qty}-{self.max_qty} pcs: {self.discount_percent}% off"
        return f"{self.min_qty}+ pcs: {self.discount_percent}% off"




# contact suppart 



class ContactSupport(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    compony_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    order_id = models.CharField(max_length=255, default='', blank=True, null=True)
    message = models.TextField(default='', blank=True, null=True)
    file = models.FileField( upload_to='shop/files', max_length=1000, default='', null=True, blank=True)
    # quantity = models.PositiveIntegerField()
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '17. Contact Support'

class ContactSales(models.Model):
    product = models.CharField(max_length=250, default='', blank=True, null=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    compony_name = models.CharField(max_length=255)
    product = models.CharField(max_length=255, default='')
    email = models.CharField(max_length=255)
    message = models.TextField(default='', blank=True, null=True)
    file = models.FileField( upload_to='shop/files', max_length=1000, blank=True, null=True)
    quantity = models.CharField(max_length=250, default='', blank=True, null=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '16. Contact Sales'
    

class Layout(models.Model):
    logo = models.ImageField(upload_to='shop/images', max_length=1000)
    favicon = models.ImageField(upload_to='shop/images', max_length=1000, default='')
    header_button_text = models.CharField(max_length=255)
    header_banner_text = models.CharField(max_length=255, default='')
    hero_title = models.CharField(max_length=255)
    hero_image = models.FileField(
        upload_to='shop/media',
        max_length=1000
    )

    def is_video(self):
        return os.path.splitext(self.hero_image.name)[1].lower() in (
            '.mp4', '.webm', '.ogg'
        )
    
    def __str__(self):
        return self.header_button_text

    class Meta:
        verbose_name_plural = '19. Layout'


class TopBannerText(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='text')
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class HeroFeature(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='features')
    title = models.CharField(max_length=255)
    short_desc = models.CharField(max_length=255)
    icon = models.ImageField(upload_to='shop/images', max_length=1000)
    
    # def __str__(self):
    #     return self.short_desc

    def __str__(self):
        return self.title
    

    

class Client(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='clients')
    title = models.CharField(max_length=255, default='', blank=True, null=True)
    image = models.ImageField(upload_to='shop/images', max_length=1000)
    
    def __str__(self):
        if self.title:
            return self.title
        else:
            return self.layout.hero_title

    class Meta:
        verbose_name_plural = '15. Clients'
        
class Faq(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)
    
    def __str__(self):
        if self.question:
            return self.question
        else:
            return self.answer



class AboutUs(models.Model):
    title = models.CharField(max_length=255)
    short_desc = models.CharField(max_length=255)
    long_desc = models.CharField(max_length=255)
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '22. About Us'
    
class AboutSections(models.Model):
    about = models.ForeignKey(AboutUs, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    description = RichTextField(default='')
    image = models.ImageField(upload_to='shop/images', max_length=1000, default='')
    # def __str__(self):
    #     return self.short_desc

    def __str__(self):
        return self.title


class TermsCondition(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField(default="")
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '23. Terms & Conditions'

class PrivacyPolicy(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField(default="")
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '24. Privacy Policy'

class ShippingPolicy(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField(default="")
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '24. Shipping Policy'

class InstagramPost(models.Model):
    title = models.CharField(max_length=255)
    link = models.CharField(max_length=255, default='', blank=True, null=True)
    image = models.ImageField( upload_to='shop/images', max_length=1000)
        
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '25. Instagram Posts'
    



