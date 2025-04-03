from django.contrib import admin
from .models import Producto, Pedido, DetallePedido, Pago, Cliente, Categoria, Proveedor, Envio

# Register your models here.

admin.site.register(Producto)
admin.site.register(Pedido)
admin.site.register(DetallePedido)
admin.site.register(Pago)
admin.site.register(Cliente)
admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(Envio)