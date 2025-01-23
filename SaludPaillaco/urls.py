"""
URL configuration for SaludPaillaco project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from App_SaludPaillaco.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio, name='inicio'),
    path('registrarse/', registrarse, name='registrarse'),
    path('registro_exitoso/', registro_exitoso, name='registro_exitoso'),
    path('aceptacion_usuario/', aceptacion_usuario, name='aceptacion_usuario'),
    path('Panel_Administrador/', panel_administrador, name='panel_administrador'),
    path('cargar-asistencia-varios/', cargar_asistencia_varios, name='cargar_asistencia_varios'),
    path('cargar_asistencia/', cargar_asistencia_uno, name='cargar_asistencia'),
    path('descargar_asistencia/', descargar_asistencia, name='descargar_asistencia'),
    
    
    
]
