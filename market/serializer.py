from rest_framework import serializers
from .models import *
from account_admin.serializer import UserSerializer

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

class OrderSerializer(serializers.ModelSerializer):
    # Para lectura: obtener detalles del usuario
    usuario_detalle = UserSerializer(source='usuario', read_only=True)
    
    # Cambio aquí: usar SlugRelatedField con username en lugar de PrimaryKeyRelatedField
    usuario = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',  # Usar username en lugar de id
        required=True,
        write_only=True
    )
    
    detalles = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'usuario', 'usuario_detalle', 'fecha', 'estado', 'total', 'detalles']

    def get_detalles(self, obj):
        try:
            # Intenta usar el related_name personalizado si existe
            detalles = obj.detalles.all()
        except AttributeError:
            # Si falla, usa el nombre por defecto de Django
            detalles = obj.orderdetail_set.all()
        
        return OrderDetailSerializer(detalles, many=True).data
    
    def to_representation(self, instance):
        # Cuando obtenemos datos, muestra el usuario completo pero no el ID
        representation = super().to_representation(instance)
        # Quitar usuario_id ya que tenemos la información completa en usuario_detalle
        if 'usuario' in representation:
            del representation['usuario']
        return representation

    def create(self, validated_data):
        # Extraer datos de detalles si existen
        detalles_data = self.initial_data.get('detalles', [])
        
        # Crear la orden correctamente con datos validados
        order = Order.objects.create(**validated_data)
        
        # Crear los detalles asociados
        for detalle_data in detalles_data:
            try:
                producto_id = detalle_data.get('producto')
                if not producto_id:
                    continue
                    
                producto = Product.objects.get(id=producto_id)
                cantidad = detalle_data.get('cantidad', 1)
                
                # Crear detalle sin pasar subtotal (se calcula automáticamente)
                OrderDetail.objects.create(
                    pedido=order,
                    producto=producto,
                    cantidad=cantidad
                )
            except Product.DoesNotExist:
                # Ignorar productos que no existen
                pass
        
        # Actualizar el total de la orden
        if hasattr(order, 'total_update'):
            order.total_update()
        
        return order
    
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

class PaySerializer(serializers.ModelSerializer):
    # Para mostrar detalles del pedido en respuestas GET
    pedido_detalle = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Pay
        fields = '__all__'
        
    def get_pedido_detalle(self, obj):
        """Muestra información resumida del pedido asociado al pago"""
        return {
            'id': obj.pedido.id,
            'total': float(obj.pedido.total),
            'estado': obj.pedido.estado,
            'fecha': obj.pedido.fecha
        }

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
            if pedido.estado not in ['pagado', 'procesando', 'enviado', 'entregado']:
                raise serializers.ValidationError(
                    f"No se puede crear un envío para un pedido en estado '{pedido.estado}'. "
                    f"El pedido debe estar pagado o en procesamiento."
                )
        
        # Validar la fecha estimada de entrega (si se proporciona)
        if 'fecha_entrega_estimada' in data and data['fecha_entrega_estimada']:
            from django.utils import timezone
            if data['fecha_entrega_estimada'] < timezone.now():
                raise serializers.ValidationError(
                    "La fecha estimada de entrega no puede ser en el pasado"
                )
        
        return data
    
    def create(self, validated_data):
        # Si el pedido está en estado pagado, cambiarlo a procesando al crear el envío
        pedido = validated_data['pedido']
        if pedido.estado == 'pagado':
            pedido.estado = 'procesando'
            pedido.save()
        
        return super().create(validated_data)

class CartItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    precio_unitario = serializers.DecimalField(source='producto.precio', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['id', 'producto_nombre', 'precio_unitario', 'subtotal']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['subtotal'] = float(instance.subtotal())
        return representation

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
