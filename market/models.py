from django.db import models
from account_admin.models import Clients

# Create your models here.
class Category(models.Model):
    nombre = models.CharField(max_length=110, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Category"  
        verbose_name_plural = "Categories"  
    
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
    
    usuario = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True, blank=True)  # Relación con Client
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


# Envío
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
