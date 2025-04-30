from django.shortcuts import render
from rest_framework import viewsets, status
from .serializer import *
from .models import *
from TechWave.permissions import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las categorías de productos.
    - Administradores y operadores: acceso completo (CRUD)
    - Clientes: solo lectura (GET)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer 
    permission_classes = [CategoryPermission]
    
    def get_queryset(self):
        """Permite filtrar categorías por nombre"""
        queryset = Category.objects.all()
        nombre = self.request.query_params.get('nombre', None)
        if nombre is not None:
            queryset = queryset.filter(nombre__icontains=nombre)
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar productos.
    - Administradores y operadores: acceso completo (CRUD) 
    - Clientes: solo lectura (GET)
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [ProductPermission]
    
    def get_queryset(self):
        """Permite filtrar productos por nombre, categoría o precio"""
        queryset = Product.objects.all()
        nombre = self.request.query_params.get('nombre', None)
        categoria = self.request.query_params.get('categoria', None)
        precio_min = self.request.query_params.get('precio_min', None)
        precio_max = self.request.query_params.get('precio_max', None)
        
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if categoria:
            queryset = queryset.filter(categoria__id=categoria)
        if precio_min:
            queryset = queryset.filter(precio__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio__lte=precio_max)
            
        return queryset
        
    @action(detail=True, methods=['post'])
    def add_to_cart(self, request, pk=None):
        """Endpoint personalizado para agregar producto al carrito"""
        # 1. Obtener el producto
        producto = self.get_object()
        
        # 2. Obtener la cantidad solicitada (default: 1)
        cantidad = int(request.data.get('cantidad', 1))
        
        # 3. Validar que la cantidad sea positiva
        if cantidad <= 0:
            return Response(
                {'error': 'La cantidad debe ser mayor a cero'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. Validar que haya suficiente stock
        if cantidad > producto.stock:
            return Response(
                {'error': f'Stock insuficiente. Solo hay {producto.stock} unidades disponibles'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 5. Obtener o crear el carrito del usuario
        carrito, created = Cart.objects.get_or_create(usuario=request.user)
        
        # 6. Buscar si el producto ya está en el carrito
        try:
            item = CartItem.objects.get(carrito=carrito, producto=producto)
            # 6.1 Si existe, actualizar cantidad (verificando stock)
            nueva_cantidad = item.cantidad + cantidad
            if nueva_cantidad > producto.stock:
                return Response(
                    {'error': f'Stock insuficiente. Solo hay {producto.stock} unidades disponibles'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.cantidad = nueva_cantidad
            item.save()
            mensaje = 'Producto actualizado en el carrito'
        except CartItem.DoesNotExist:
            # 6.2 Si no existe, crear nuevo item
            CartItem.objects.create(
                carrito=carrito,
                producto=producto,
                cantidad=cantidad
            )
            mensaje = 'Producto agregado al carrito'
        
        # 7. Preparar respuesta con los datos del carrito actualizado
        datos_carrito = {
            'mensaje': mensaje,
            'total_items': carrito.cantidad_items(),
            'total': float(carrito.total()),
            'producto_agregado': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': float(producto.precio),
                'cantidad': cantidad,
            }
        }
        
        return Response(datos_carrito, status=status.HTTP_200_OK)

class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar órdenes/pedidos.
    - Administradores y operadores: acceso completo a todas las órdenes
    - Clientes: pueden crear órdenes y ver/editar solo las suyas
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [ClientOrderPermission]
    
    def get_queryset(self):
        """Filtra para que clientes vean solo sus órdenes"""
        user = self.request.user
        if user.role in ['admin', 'operator']:
            return Order.objects.all()
        return Order.objects.filter(usuario=user)
    
    def perform_create(self, serializer):
        """Valida que el usuario solo pueda crear pagos para sus órdenes"""
        pedido_id = self.request.data.get('pedido')
        user = self.request.user
        estado = self.request.data.get('estado', 'pendiente')  # Default estado is 'pendiente'
        
        try:
            pedido = Order.objects.get(id=pedido_id)
            
            # Verificar propiedad del pedido para usuarios normales
            if user.role not in ['admin', 'operator'] and pedido.usuario != user:
                raise serializers.ValidationError("No puedes crear pagos para pedidos que no te pertenecen")
            
            # Verificar estado del pedido
            if pedido.estado not in ['pendiente', 'procesando']:
                raise serializers.ValidationError(f"No se puede pagar un pedido en estado '{pedido.estado}'")
            
            # Usar automáticamente el total del pedido como monto pagado
            monto_pagado = pedido.total
                    
            # Guardar con el estado proporcionado (o pendiente por defecto) y monto correcto
            serializer.save(monto_pagado=monto_pagado, estado=estado)
            
        except Order.DoesNotExist:
            raise serializers.ValidationError("Pedido no encontrado")
        
    def perform_update(self, serializer):
        """Maneja la actualización de una orden y sus detalles"""
        instance = self.get_object()
        
        # Verificar si se pueden hacer cambios según el estado
        if instance.estado in ['entregado', 'cancelado']:
            raise serializers.ValidationError(
                f"No se puede modificar un pedido en estado '{instance.estado}'"
            )
        
        # Actualizar los campos básicos de la orden
        updated_instance = serializer.save()
        
        # Procesar detalles si se proporcionan
        detalles_data = self.request.data.get('detalles', [])
        if detalles_data:
            # Manejar cada detalle de la orden
            self._process_order_details(updated_instance, detalles_data)
            
        # Recalcular total
        if hasattr(updated_instance, 'total_update'):
            updated_instance.total_update()
    
    def _process_order_details(self, order, detalles_data):
        """Procesa los detalles de una orden durante la actualización"""
        for detalle_data in detalles_data:
            producto_id = detalle_data.get('producto')
            cantidad = detalle_data.get('cantidad', 1)
            detalle_id = detalle_data.get('id', None)
            
            if not producto_id:
                continue
                
            try:
                producto = Product.objects.get(id=producto_id)
                
                if detalle_id:
                    # Actualizar detalle existente
                    try:
                        detalle = OrderDetail.objects.get(id=detalle_id, pedido=order)
                        
                        # Si la cantidad cambia, ajustar el stock
                        if detalle.cantidad != cantidad:
                            # Devolver el stock anterior
                            producto.stock += detalle.cantidad
                            # Restar el nuevo stock
                            if producto.stock < cantidad:
                                raise serializers.ValidationError(
                                    f"Stock insuficiente para {producto.nombre}"
                                )
                            producto.stock -= cantidad
                            producto.save()
                        
                        detalle.cantidad = cantidad
                        detalle.save()
                    except OrderDetail.DoesNotExist:
                        raise serializers.ValidationError(
                            f"Detalle con id {detalle_id} no pertenece a esta orden"
                        )
                else:
                    # Crear nuevo detalle
                    if producto.stock < cantidad:
                        raise serializers.ValidationError(
                            f"Stock insuficiente para {producto.nombre}"
                        )
                        
                    OrderDetail.objects.create(
                        pedido=order,
                        producto=producto,
                        cantidad=cantidad
                    )
            except Product.DoesNotExist:
                # Ignorar productos que no existen
                pass
    
    @action(detail=True, methods=['post'], url_path='remove-detail/(?P<detail_id>[^/.]+)')
    def remove_detail(self, request, pk=None, detail_id=None):
        """Elimina un detalle específico de la orden"""
        order = self.get_object()
        
        # Verificar estado del pedido
        if order.estado in ['entregado', 'cancelado']:
            return Response(
                {'error': f'No se puede modificar un pedido en estado {order.estado}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            detail = OrderDetail.objects.get(id=detail_id, pedido=order)
            
            # Devolver el stock
            producto = detail.producto
            producto.stock += detail.cantidad
            producto.save()
            
            # Eliminar el detalle
            detail.delete()
            
            # Actualizar el total
            order.total_update()
            
            return Response(
                {'status': 'Detalle eliminado', 'total_actualizado': float(order.total)}, 
                status=status.HTTP_200_OK
            )
        except OrderDetail.DoesNotExist:
            return Response(
                {'error': 'El detalle no existe o no pertenece a esta orden'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Endpoint para cancelar una orden"""
        order = self.get_object()
        if order.estado == 'pendiente':
            order.estado = 'cancelado'
            order.save()  # Esto invocará el método save() personalizado que restaura el stock
            return Response({'status': 'pedido cancelado'}, status=status.HTTP_200_OK)
        return Response({'error': 'No se puede cancelar el pedido en su estado actual'}, 
                         status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_total(self, request, pk=None):
        """Endpoint para actualizar el total del pedido"""
        order = self.get_object()
        order.total_update()  # Usa el método personalizado del modelo
        return Response({'status': 'total actualizado', 'total': order.total}, 
                        status=status.HTTP_200_OK)
    
class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar el carrito de compras.
    - Cada usuario solo puede ver y modificar su propio carrito
    """
    serializer_class = CartSerializer  # Necesitarás crear este serializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get_queryset(self):
        """Retorna solo el carrito del usuario actual"""
        return Cart.objects.filter(usuario=self.request.user)
    
    def list(self, request):
        """Obtener detalles del carrito actual del usuario"""
        carrito, created = Cart.objects.get_or_create(usuario=request.user)
        serializer = self.get_serializer(carrito)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Vaciar el carrito"""
        carrito, created = Cart.objects.get_or_create(usuario=request.user)
        carrito.limpiar()
        return Response({'mensaje': 'Carrito vaciado correctamente'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Convertir carrito en pedido"""
        carrito, created = Cart.objects.get_or_create(usuario=request.user)
        
        # Verificar que el carrito no esté vacío
        if carrito.items.count() == 0:
            return Response(
                {'error': 'El carrito está vacío'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar stock disponible para todos los productos
        for item in carrito.items.all():
            if item.cantidad > item.producto.stock:
                return Response(
                    {'error': f'Stock insuficiente para {item.producto.nombre}. Solo hay {item.producto.stock} unidades disponibles'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Crear nuevo pedido
        pedido = Order.objects.create(
            usuario=request.user,
            estado='pendiente',
            total=carrito.total()
        )
        
        # Transferir items del carrito al pedido
        for item in carrito.items.all():
            OrderDetail.objects.create(
                pedido=pedido,
                producto=item.producto,
                cantidad=item.cantidad
            )
            
            # Actualizar stock del producto
            item.producto.stock -= item.cantidad
            item.producto.save()
        
        # Vaciar el carrito
        carrito.limpiar()
        
        return Response({
            'mensaje': 'Pedido creado correctamente',
            'pedido_id': pedido.id,
            'total': float(pedido.total)
        }, status=status.HTTP_201_CREATED)

class PayViewSet(viewsets.ModelViewSet):
    """
    ViewSet para pagos.
    - Admin y operadores: acceso completo a todos los pagos
    - Clientes: pueden crear pagos y ver los asociados a sus órdenes
    """
    queryset = Pay.objects.all()
    serializer_class = PaySerializer  
    permission_classes = [PaymentPermission]
    
    def get_queryset(self):
        """Filtra para que clientes vean solo pagos de sus órdenes"""
        user = self.request.user
        if user.role in ['admin', 'operator']:
            return Pay.objects.all()
        return Pay.objects.filter(pedido__usuario=user)
    
    def perform_create(self, serializer):
        """Valida que el usuario solo pueda crear pagos para sus órdenes"""
        pedido_id = self.request.data.get('pedido')
        user = self.request.user
        estado = self.request.data.get('estado', 'pendiente')  # Default estado is 'pendiente'
        
        try:
            pedido = Order.objects.get(id=pedido_id)
            
            # Verificar propiedad del pedido para usuarios normales
            if user.role not in ['admin', 'operator'] and pedido.usuario != user:
                raise serializers.ValidationError("No puedes crear pagos para pedidos que no te pertenecen")
            
            # Verificar estado del pedido
            if pedido.estado not in ['pendiente', 'procesando']:
                raise serializers.ValidationError(f"No se puede pagar un pedido en estado '{pedido.estado}'")
            
            # Usar automáticamente el total del pedido como monto pagado
            monto_pagado = pedido.total
                    
            # Guardar con el estado proporcionado (o pendiente por defecto) y monto correcto
            serializer.save(monto_pagado=monto_pagado, estado=estado)
            
        except Order.DoesNotExist:
            raise serializers.ValidationError("Pedido no encontrado")
            
    @action(detail=True, methods=['post'])
    def complete_payment(self, request, pk=None):
        """Endpoint para marcar un pago como completado"""
        payment = self.get_object()
        
        # Verificar que solo admin/operator puedan completar pagos manualmente
        if request.user.role not in ['admin', 'operator']:
            return Response({'error': 'Solo administradores y operadores pueden completar pagos manualmente'}, 
                        status=status.HTTP_403_FORBIDDEN)
        
        if payment.estado != 'pendiente':
            return Response({'error': f'No se puede completar un pago en estado {payment.estado}'}, 
                        status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar el pago
        payment.estado = 'completado'
        payment.save()
        
        # Actualizar el estado del pedido
        pedido = payment.pedido
        pedido.estado = 'pagado'
        pedido.save()
        
        return Response({
            'status': 'pago completado',
            'pedido_actualizado': True,
            'nuevo_estado_pedido': pedido.estado
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Endpoint para cancelar un pago pendiente"""
        pago = self.get_object()
        
        if pago.estado != 'pendiente':
            return Response(
                {"error": f"No se puede cancelar un pago en estado '{pago.estado}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pago.estado = 'cancelado'
        pago.save()
        
        return Response({"mensaje": "Pago cancelado correctamente"}, status=status.HTTP_200_OK)

class ShipmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para envíos.
    - Admin y operadores: acceso completo a todos los envíos
    - Clientes: solo pueden ver información de sus propios envíos
    """
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [ShipmentPermission]
    
    def get_queryset(self):
        """Filtra para que clientes vean solo envíos de sus órdenes"""
        user = self.request.user
        if user.role in ['admin', 'operator']:
            return Shipment.objects.all()
        return Shipment.objects.filter(pedido__usuario=user)
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Endpoint para consultar el estado del envío"""
        shipment = self.get_object()
        tracking_data = {
            'numero_guia': shipment.numero_guia,
            'estado': shipment.estado,
            'empresa_envio': shipment.empresa_envio,
            'fecha_entrega_estimada': shipment.fecha_entrega_estimada,
            'direccion_envio': shipment.direccion_envio
        }
        return Response(tracking_data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Endpoint para actualizar el estado del envío (solo admin/operator)"""
        if not request.user.role in ['admin', 'operator']:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
            
        shipment = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        # Valida que el estado sea válido
        estados_validos = ['pendiente', 'preparando', 'en camino', 'entregado']
        if nuevo_estado not in estados_validos:
            return Response({'error': 'Estado inválido'}, status=status.HTTP_400_BAD_REQUEST)
            
        shipment.estado = nuevo_estado
        
        # Si se marca como enviado, actualizar también el pedido
        if nuevo_estado == 'en camino' and shipment.pedido.estado != 'enviado':
            shipment.pedido.estado = 'enviado'
            shipment.pedido.save()
            
        # Si se marca como entregado, actualizar también el pedido
        if nuevo_estado == 'entregado' and shipment.pedido.estado != 'entregado':
            shipment.pedido.estado = 'entregado'
            shipment.pedido.save()
            
        shipment.save()
        return Response({'status': 'Estado de envío actualizado'}, status=status.HTTP_200_OK)

"""
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
"""