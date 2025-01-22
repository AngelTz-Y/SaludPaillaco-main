from django.db import models
from django.contrib.auth.models import User, Group

class Profesion_Oficio(models.Model):
    profesion_oficio = models.CharField(max_length=100)

    def __str__(self):
        return self.profesion_oficio

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12)
    telefono = models.CharField(max_length=15)
    profesion = models.ForeignKey(Profesion_Oficio, on_delete=models.SET_NULL, null=True)
    aprobado = models.BooleanField(default=False)
    numero_espera = models.PositiveIntegerField(null=True, blank=True)  # Número secuencial

    def __str__(self):
        return self.user.username
    
    



