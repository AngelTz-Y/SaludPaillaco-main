from django.db import models
from django.contrib.auth.models import User, Group
from datetime import datetime

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
    pdf_asistencia = models.FileField(upload_to='asistencias_pdfs/', null=True, blank=True)  # Campo para el PDF

    def __str__(self):
        return self.user.username
    
    
class Asistenciaa(models.Model):
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE)
    fecha = models.DateField()
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Asistencia de {self.perfil.user.username} en {self.fecha} ({self.horas_trabajadas} horas)"
    
    
class AsistenciaMes(models.Model):
    # Relación con el perfil de usuario
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='asistencias')
    
    # Mes y año (en vez de usar un texto plano, podemos usar un valor numérico para mejorar la relación)
    MES_CHOICES = [
        (1, 'Enero'),
        (2, 'Febrero'),
        (3, 'Marzo'),
        (4, 'Abril'),
        (5, 'Mayo'),
        (6, 'Junio'),
        (7, 'Julio'),
        (8, 'Agosto'),
        (9, 'Septiembre'),
        (10, 'Octubre'),
        (11, 'Noviembre'),
        (12, 'Diciembre'),
    ]
    
    mes = models.IntegerField(choices=MES_CHOICES)
    año = models.IntegerField(default=datetime.now().year)

    # El PDF de asistencia
    pdf_asistencia = models.FileField(upload_to='asistencias_pdfs/', null=True, blank=True)

    def __str__(self):
        mes_nombre = dict(self.MES_CHOICES).get(self.mes)
        return f'{self.perfil.user.get_full_name()} - {mes_nombre} {self.año}'

    class Meta:
        unique_together = ('perfil', 'mes', 'año')  # Un usuario puede tener un solo PDF por mes/año
    
    
    
    

class Asistencia(models.Model):
    ac = models.CharField(max_length=100)  # Elimina el `unique=True` para permitir duplicados de `ac`
    rut = models.CharField(max_length=12)  # El rut es de tipo cadena para almacenarlo correctamente.
    nombre = models.CharField(max_length=200)
    dpto = models.CharField(max_length=100)
    mes = models.CharField(max_length=20)
    ano = models.IntegerField()
    fecha = models.DateField()
    marcaciones = models.TextField()
    observaciones = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.rut} - {self.ac}"
    
    




