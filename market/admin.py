from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderDetail)
admin.site.register(Pay)
admin.site.register(Category)
admin.site.register(Shipment)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__nombre', 'product__name')
    