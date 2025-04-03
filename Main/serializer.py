from rest_framework import serializers
from .models import *

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer()
    proveedor = ProveedorSerializer()

    class Meta:
        model = Producto
        fields = '__all__'

class PedidoSerializer(serializers.ModelSerializer):
    usuario = ClienteSerializer()
    detalles = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = '__all__'

    def get_detalles(self, obj):
        detalles = obj.detalles.all()
        return DetallePedidoSerializer(detalles, many=True).data

class DetallePedidoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer()

    class Meta:
        model = DetallePedido
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'

class EnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envio
        fields = '__all__'
