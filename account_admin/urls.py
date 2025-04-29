from django.urls import path, include 
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
#router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('accounts_admin/model/', include(router.urls)),
    path('create-user/', CreateUserView.as_view(), name='create-user'),
    path('change-role/<int:user_id>/', ChangeRoleView.as_view(), name='change-role'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]