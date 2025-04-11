from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .serializer import *
from .models import *

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer