from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, User
from .models import PerfilUsuario  # Importa el modelo PerfilUsuario si es necesario

@receiver(post_migrate)
def crear_grupo_administrador(sender, **kwargs):
    # Crear el grupo 'Administrador' si no existe
    grupo_administrador, created = Group.objects.get_or_create(name='Administrador')

    if created:
        print("Grupo 'Administrador' creado.")

    # Crear el usuario administrador si no existe
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin'  # Cambia la contraseña aquí
        )
        # Asignar el usuario al grupo de Administrador
        admin_user.groups.add(grupo_administrador)
        print("Usuario administrador creado y asignado al grupo 'Administrador'.")

        # Crear el PerfilUsuario para el administrador
        perfil_admin = PerfilUsuario(
            user=admin_user,
            rut='333',  # Cambia esto por un RUT válido
            telefono='123456789',  # Cambia esto por un número de teléfono válido
            profesion=None,  # O asigna una profesión si es necesario
            aprobado=True,  # Considerarlo aprobado por defecto
            numero_espera=None  # No aplicable para administradores
        )
        perfil_admin.save()
        print("Perfil de administrador creado.")
