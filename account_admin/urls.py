from django.urls import path, include 
from rest_framework import routers
from account_admin import views

router = routers.DefaultRouter()
router.register(r'clients', views.ClientViewSet, basename='client')

urlpatterns = [
    path('accounts/model/', include(router.urls))
]