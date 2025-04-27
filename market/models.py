from django.db import models
from account_admin.models import User

# Create your models here.
class Category(models.Model):
    nombre = models.CharField(max_length=110, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Category"  
        verbose_name_plural = "Categories"  

class Product(models.Model):
    nombre = models.CharField(max_length=250)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    categoria = models.ForeignKey(Category, on_delete=models.CASCADE)
    #proveedor = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Product"  
        verbose_name_plural = "Products"  

class Order(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Relación con Client
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def total_update(self):
        self.total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.save()

    def save(self, *args, **kwargs):
        if self.pk:  # Solo si el pedido ya existe
            pedido_anterior = Order.objects.get(pk=self.pk)
            if pedido_anterior.estado != 'cancelado' and self.estado == 'cancelado':
                # Si el pedido se cancela, restituir stock de cada producto
                for detalle in self.detalles.all():
                    detalle.producto.stock += detalle.cantidad
                    detalle.producto.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.id} - {self.usuario.username}"
    
    class Meta:
        verbose_name = "Order"  
        verbose_name_plural = "Orders"  

class OrderDetail(models.Model):
    pedido = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:  # Solo descontar si es un nuevo detalle
            if self.producto.stock < self.cantidad:
                raise ValueError("No hay suficiente stock disponible")
            self.producto.stock -= self.cantidad
            self.producto.save()

        self.subtotal = self.producto.precio * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Pedido {self.pedido.id})"
    
    class Meta:
        verbose_name = "Order Detail"  
        verbose_name_plural = "Order Details"

class Pay(models.Model):
    pedido = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="pagos")  # <-- Relación 1:N
    metodo = models.CharField(max_length=20, choices=[
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('paypal', 'PayPal'),
        ('transferencia', 'Transferencia Bancaria'),
    ])
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
    ], default='pendiente')
    
    def __str__(self):
        return f"Pago de {self.monto_pagado} - {self.metodo} ({self.estado})"
    
    class Meta:
        verbose_name = "Pay"  
        verbose_name_plural = "Pays"

class Shipment(models.Model):
    pedido = models.OneToOneField(Order, on_delete=models.CASCADE)
    direccion_envio = models.TextField()
    empresa_envio = models.CharField(max_length=100)
    numero_guia = models.CharField(max_length=50, unique=True, null=True, blank=True)
    fecha_envio = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fecha_entrega_estimada = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=50, choices=[
        ('pendiente', 'Pendiente'),
        ('preparando', 'Preparando'),
        ('en camino', 'En camino'),
        ('entregado', 'Entregado'),
    ], default='pendiente')

    def __str__(self):
        return f"Envío de Pedido {self.pedido.id} - {self.empresa_envio} (Guía: {self.numero_guia if self.numero_guia else 'N/A'})"

    class Meta:
        verbose_name = "Shipment"  
        verbose_name_plural = "Shipments"
    
class Cart(models.Model):
    """Modelo para representar el carrito de compras de un usuario"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"
    
    def total(self):
        """Calcula el total del carrito"""
        return sum(item.subtotal() for item in self.items.all())
    
    def cantidad_items(self):
        """Obtiene la cantidad total de items en el carrito"""
        return sum(item.cantidad for item in self.items.all())
    
    def limpiar(self):
        """Elimina todos los items del carrito"""
        self.items.all().delete()
    
    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

class CartItem(models.Model):
    """Modelo para representar un item en el carrito"""
    carrito = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    def subtotal(self):
        """Calcula el subtotal del item"""
        return self.producto.precio * self.cantidad
    
    class Meta:
        verbose_name = "Item de Carrito"
        verbose_name_plural = "Items de Carrito"
        unique_together = ('carrito', 'producto')  # Un producto solo puede estar una vez en el carrito

""" Proveedor
class Supplier(models.Model):
    nombre = models.CharField(max_length=255)
    contacto = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"  
        verbose_name_plural = "Proveedores"
"""
