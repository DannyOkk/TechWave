from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    ROLES = [
        ('admin', 'Admin'),
        ('operator', 'Operator'),
        ('client', 'Client'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='client')
    name = models.CharField(max_length=100, unique=True, default='Anonimo')
    address = models.TextField()
    phone = models.CharField(max_length=15)
    register_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users" 
