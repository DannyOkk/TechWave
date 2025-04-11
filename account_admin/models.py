from django.db import models

class Client(models.Model):
    nombre = models.CharField(max_length=100, unique=True, default='Anonimo')
    direccion = models.TextField()
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre