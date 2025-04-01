from django.contrib import admin
from .models import Producto, Pedido, DetallePedido, Pago

# Register your models here.

admin.site.register(Producto)
admin.site.register(Pedido)
admin.site.register(DetallePedido)
admin.site.register(Pago)