from django.db import models

# Create your models here.
# Cliente (Información adicional del usuario)
class Client(models.Model):
    nombre = models.CharField(max_length=100, unique=True, default='Anonimo')
    direccion = models.TextField()
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    