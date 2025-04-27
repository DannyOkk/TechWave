from django.urls import path, include 
from rest_framework import routers
from market import views

router = routers.DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
#router.register(r'supplier', views.SupplierViewSet, basename='supplier')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'orderdetail', views.OrderDetailViewSet, basename='orderdetail')
router.register(r'pay', views.PayViewSet, basename='pay')
router.register(r'shipment', views.ShipmentViewSet, basename='shipment')
router.register(r'cart', views.CartViewSet, basename='cart')

urlpatterns = [
    path('market/model/', include(router.urls))
]