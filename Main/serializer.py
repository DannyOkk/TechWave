from rest_framework import serializers
from .models import *
from ..accounts.models import Client
from ..accounts.serializer import ClientSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
"""
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
"""
class ProductSerializer(serializers.ModelSerializer):
    categoria = CategorySerializer()
    #proveedor = SupplierSerializer()

    class Meta:
        model = Product
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    usuario = ClientSerializer()
    detalles = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_detalles(self, obj):
        detalles = obj.detalles.all()
        return OrderDetailSerializer(detalles, many=True).data

class OrderDetailSerializer(serializers.ModelSerializer):
    producto = ProductSerializer()

    class Meta:
        model = OrderDetail
        fields = '__all__'

class PaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pay
        fields = '__all__'

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = '__all__'
