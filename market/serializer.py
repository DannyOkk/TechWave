from rest_framework import serializers
from .models import *
from account_admin.serializer import UserSerializer
from rest_framework.exceptions import ValidationError

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
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=True
    )
    
    class Meta:
        model = Product
        fields = ['id', 'nombre', 'descripcion', 'precio', 'stock', 'categoria']
    
    def to_representation(self, instance):
        # Esto es para mostrar detalles de la categoría en las respuestas GET
        representation = super().to_representation(instance)
        representation['categoria'] = {
            'id': instance.categoria.id,
            'nombre': instance.categoria.nombre
        }
        return representation
    
class OrderDetailSerializer(serializers.ModelSerializer):
    # Para mostrar detalles del producto en GET
    producto_detalle = ProductSerializer(source='producto', read_only=True)
    # Para aceptar IDs de producto en POST/PUT
    producto = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), 
        write_only=True
    )

    class Meta:
        model = OrderDetail
        fields = ['id', 'pedido', 'producto', 'producto_detalle', 'cantidad', 'subtotal']
        read_only_fields = ['subtotal']

class OrderSerializer(serializers.ModelSerializer):
    usuario_detalle = UserSerializer(source='usuario', read_only=True)
    
    usuario = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        required=True,
        write_only=True,
        help_text="Nombre de usuario del cliente que realiza el pedido. Debe existir en la base de datos."
    )
    
    # CAMBIO: Declaración directa del serializador de detalles.
    # Es más limpio y estándar que usar SerializerMethodField.
    detalles = OrderDetailSerializer(many=True, read_only=True)

    detalles_input = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="Lista de productos a incluir en el pedido"
    )

    class Meta:
        model = Order
        fields = ['id', 'usuario', 'usuario_detalle', 'fecha', 'estado', 'total', 'detalles', 'detalles_input', 'direccion_envio']
        read_only_fields = ['id', 'fecha', 'total']
        extra_kwargs = {
            'estado': {'default': 'pendiente', 'help_text': "Estado del pedido (default: pendiente)"}
        }
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Verificar si es una solicitud para edición
        request = self.context.get('request')
        if request and request.method in ['PUT']:
            # Formato simplificado para edición
            
            # Simplificar usuario_detalle a solo username
            if 'usuario_detalle' in representation:
                username = instance.usuario.username
                representation['usuario_detalle'] = {'username': username}
            
            # Eliminar campos que no se necesitan para edición
            if 'fecha' in representation:
                del representation['fecha']
            
            if 'total' in representation:
                del representation['total']
                
            # Simplificar detalles para edición
            if 'detalles' in representation:
                simplified_details = []
                for detalle in representation['detalles']:
                    simplified_details.append({
                        'id': detalle['id'],
                        'producto': detalle['producto_detalle']['id'],
                        'cantidad': detalle['cantidad']
                    })
                representation['detalles'] = simplified_details
        return representation

class PaySerializer(serializers.ModelSerializer):
    # Para mostrar detalles del pedido en respuestas GET
    pedido_detalle = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Pay
        fields = ['id', 'pedido', 'metodo', 'estado', 'pedido_detalle']
        read_only_fields = ['id', 'monto_pagado']
        extra_kwargs = {
            'metodo': {'required': True},
            'estado': {'default': 'pendiente'}
        }
        
    def get_pedido_detalle(self, obj):
        """Muestra información resumida del pedido asociado al pago"""
        return {
            'id': obj.pedido.id,
            'total': float(obj.pedido.total),
            'estado': obj.pedido.estado,
            'fecha': obj.pedido.fecha
        }
    
    def create(self, validated_data):
        # El monto_pagado se calcula automáticamente basado en el pedido
        pedido = validated_data.get('pedido')
        if pedido:
            validated_data['monto_pagado'] = pedido.total
        return super().create(validated_data)

class ShipmentSerializer(serializers.ModelSerializer):
    # Para mostrar detalles del pedido en respuestas GET
    pedido_detalle = serializers.SerializerMethodField(read_only=True)
    # Para aceptar IDs de pedido en POST/PUT
    pedido = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        required=True
    )
    fecha_envio_formateada = serializers.DateTimeField(source='fecha_envio', format='%d/%m/%Y %H:%M', read_only=True)
    fecha_entrega_estimada_formateada = serializers.DateTimeField(source='fecha_entrega_estimada', format='%d/%m/%Y', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'pedido', 'pedido_detalle', 'direccion_envio', 
            'empresa_envio', 'numero_guia', 'fecha_envio', 'fecha_envio_formateada',
            'fecha_entrega_estimada', 'fecha_entrega_estimada_formateada',
            'estado', 'estado_display'
        ]
        read_only_fields = ['fecha_envio']
    
    def get_pedido_detalle(self, obj):
        """Muestra información resumida del pedido asociado al envío"""
        pedido = obj.pedido
        return {
            'id': pedido.id,
            'cliente': pedido.usuario.username,
            'total': float(pedido.total),
            'estado': pedido.estado,
            'fecha': pedido.fecha,
            'productos': [
                {
                    'nombre': detalle.producto.nombre,
                    'cantidad': detalle.cantidad
                } for detalle in pedido.detalles.all()[:5]  # Limitar a 5 productos para evitar respuestas muy grandes
            ],
            'total_productos': pedido.detalles.count()
        }
    
    def validate(self, data):
        """Validaciones personalizadas para el envío"""
        # Verificar que el pedido esté en un estado válido para crear un envío
        if 'pedido' in data:
            pedido = data['pedido']
            if pedido.estado not in ['pendiente', 'preparando', 'en camino', 'entregado']:
                raise serializers.ValidationError(
                    f"No se puede crear un envío para un pedido en estado '{pedido.estado}'. "
                    f"El pedido debe estar en un estado válido para el envío."
                )
        
        return data
    
    def create(self, validated_data):
        pedido = validated_data['pedido']
        if pedido.estado == 'pendiente':
            pedido.estado = 'procesando'
            pedido.save()
        return super().create(validated_data)

class CartItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)
    categoria_nombre = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    precio_unitario = serializers.DecimalField(source='producto.precio', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'producto', 'producto_nombre', 'producto_descripcion', 'categoria_nombre', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['id', 'producto_nombre', 'producto_descripcion', 'categoria_nombre', 'precio_unitario', 'subtotal']
    
    def get_subtotal(self, obj):
        return float(obj.subtotal())

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    cantidad_items = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'usuario', 'items', 'total', 'cantidad_items', 'fecha_actualizacion']
        read_only_fields = ['id', 'usuario', 'fecha_actualizacion']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total'] = float(instance.total())
        representation['cantidad_items'] = instance.cantidad_items()
        return representation
