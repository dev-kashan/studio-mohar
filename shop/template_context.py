# from .models import Product,ProductAttribute
# from django.db.models import Min,Max
# def get_filters(request):
# 	cats=Product.objects.distinct().values('categories__category_name','categories__category_id')
# 	brands=Product.objects.distinct().values('brand','product_id')
# 	colors=ProductAttribute.objects.distinct().values('color')
# 	sizes=ProductAttribute.objects.distinct().values('size')
# 	minMaxPrice=ProductAttribute.objects.aggregate(Min('price'),Max('price'))
# 	data={
# 		'cats':cats,
# 		'brands':brands,
# 		'colors':colors,
# 		'sizes':sizes,
# 		'minMaxPrice':minMaxPrice,
# 	}
# 	return data