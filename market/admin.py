from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderDetail)
admin.site.register(Pay)
admin.site.register(Category)
#admin.site.register(Supplier)
admin.site.register(Shipment)