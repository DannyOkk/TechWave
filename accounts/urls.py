from django.urls import path, include 
from rest_framework import routers
from Accounts import views

router = routers.DefaultRouter()
router.register(r'clients', views.ClientViewSet, basename='client')

urlpatterns = [
    path('Accounts/model/', include(router.urls))
]