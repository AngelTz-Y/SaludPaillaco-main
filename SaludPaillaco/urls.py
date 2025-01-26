from django.contrib import admin
from django.urls import path
from App_SaludPaillaco.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio, name='inicio'),
    path('registrarse/', registrarse, name='registrarse'),
    path('registro_exitoso/', registro_exitoso, name='registro_exitoso'),
    path('aceptacion_usuario/', aceptacion_usuario, name='aceptacion_usuario'),
    path('Panel_Administrador/', panel_administrador, name='panel_administrador'),
    path('cargar_asistencia/', cargar_asistencia_uno, name='cargar_asistencia'),
    path('descargar_asistencia/', descargar_registro_asistencia, name='descargar_asistencia'),
    path('descargar_asistencia/<str:rut>/<int:mes>/<int:año>/', descargar_asistencia, name='descargar_asistencia_usuario'),
    path('descargar-pdf/', descargar_pdf_perfil, name='descargar_pdf_perfil'),
    path('cargar_excel/', cargar_excel, name='cargar_excel'),
    path('generar_pdf/', generar_pdf, name='generar_pdf')

    
]

# Agregar rutas para servir archivos estáticos y multimedia en desarrollo
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
