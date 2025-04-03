from django.urls import path, include 
from rest_framework import routers
from Main import views

router = routers.DefaultRouter()
router.register(r'clientes', views.ClienteViewSet, basename='cliente')
router.register(r'categorias', views.CategoriaViewSet, basename='categoria')
router.register(r'proveedores', views.ProveedorViewSet, basename='proveedor')
router.register(r'productos', views.ProductoViewSet, basename='producto')
router.register(r'pedidos', views.PedidoViewSet, basename='pedido')
router.register(r'detallepedidos', views.DetallePedidoViewSet, basename='detallepedido')
router.register(r'pago', views.PagoViewSet, basename='pago')
router.register(r'envios', views.EnvioViewSet, basename='envio')

urlpatterns = [
    path('Main/model/', include(router.urls))
]