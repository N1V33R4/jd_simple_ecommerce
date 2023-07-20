from django.contrib import admin
from .models import Product, Order, OrderItem, ColorVariation, SizeVariation, Address, Payment

admin.site.register(Product, list_display=['title', 'image', 'active'])
admin.site.register(Order, list_display=['__str__' , 'get_subtotal'])
admin.site.register(OrderItem, list_display=['__str__' ,'order', 'product', 'quantity', 'get_total_item_price'])
admin.site.register(ColorVariation)
admin.site.register(SizeVariation)
admin.site.register(Address)
admin.site.register(Payment)
