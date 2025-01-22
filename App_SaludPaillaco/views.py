from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import PerfilUsuario, Profesion_Oficio
from django.contrib.auth.models import Group

# Create your views here.
def inicio(request):
    if request.method == 'POST':
        # Procesar el formulario de inicio de sesión
        rut = request.POST.get('rut', '').strip()
        password = request.POST.get('password', '').lower().strip()

        try:
            # Buscar al usuario por el RUT
            perfil = PerfilUsuario.objects.get(rut=rut)
            user = perfil.user  # Obtener el usuario relacionado

            # Autenticar al usuario con la contraseña
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)

                # Verificar si el usuario es administrador (staff)
                if user.is_staff:
                    # Si es administrador, redirigir al panel de administración
                    return redirect('aceptacion_usuario')

                # Verificar si el usuario pertenece al grupo "usuario en espera"
                if user.groups.filter(name='usuario en espera').exists():
                    # Calcular la posición en la lista de espera
                    usuarios_en_espera = PerfilUsuario.objects.filter(aprobado=False).order_by('numero_espera')
                    posicion = list(usuarios_en_espera).index(perfil) + 1

                    # Renderizar la interfaz para usuarios en espera con su posición
                    return render(request, 'Grupos/Usuarios/usuario_no_registrado.html', {
                        'posicion': posicion,
                        'total_espera': usuarios_en_espera.count(),
                        'numero_espera': perfil.numero_espera
                    })
                
                # Verificar si el usuario pertenece al grupo "usuario registrado"
                if user.groups.filter(name='usuario registrado').exists():
                    return render(request, 'Grupos/Usuarios/usuario_registrado.html')
                
                # Si no pertenece a ningún grupo, redirigir con un mensaje de error
                return render(request, 'inicio.html', {'error': 'No tiene permisos para acceder a esta sección.'})
            else:
                return render(request, 'inicio.html', {'error': 'Credenciales incorrectas.'})

        except PerfilUsuario.DoesNotExist:
            return render(request, 'inicio.html', {'error': 'El RUT ingresado no está registrado.'})

    # Si la solicitud es GET, mostrar la página de inicio de sesión
    return render(request, 'inicio.html')

from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from .models import PerfilUsuario, Profesion_Oficio

def registrarse(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        firstname = request.POST.get('firstname', '').strip()
        lastname = request.POST.get('lastname', '').strip()
        username = f"{firstname} {lastname}"  # Nombre completo
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm-password', '').strip()
        rut = request.POST.get('rut', '').strip()
        telefono = request.POST.get('phone', '').strip()
        profesion_id = request.POST.get('profession', '').strip()

        # Verificar que las contraseñas coinciden
        if password != confirm_password:
            return render(request, 'registrarse.html', {'error': 'Las contraseñas no coinciden.'})

        # Verificar que la profesión seleccionada existe
        try:
            profesion = Profesion_Oficio.objects.get(id=profesion_id)
        except Profesion_Oficio.DoesNotExist:
            return render(request, 'registrarse.html', {'error': 'La profesión seleccionada no es válida.'})

        # Crear el usuario en Django
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=firstname,
                last_name=lastname
            )
        except Exception as e:
            return render(request, 'registrarse.html', {'error': f'Error al crear el usuario: {e}'})

        # Asignar el rol de "usuario en espera"
        group, created = Group.objects.get_or_create(name='usuario en espera')
        user.groups.add(group)

        # Generar número de espera
        numero_espera = PerfilUsuario.objects.filter(aprobado=False).count() + 1

        # Crear el perfil del usuario
        try:
            perfil = PerfilUsuario(
                user=user,
                rut=rut,
                telefono=telefono,
                profesion=profesion,
                aprobado=False,
                numero_espera=numero_espera
            )
            perfil.save()
        except Exception as e:
            user.delete()  # Eliminar usuario si el perfil no se pudo crear
            return render(request, 'registrarse.html', {'error': f'Error al crear el perfil: {e}'})

        # Mostrar el número de espera al usuario (opcional: redirigir con mensaje)
        return render(request, 'registro_exitoso.html', {'numero_espera': numero_espera})

    else:
        profesiones = Profesion_Oficio.objects.all()
        return render(request, 'registrarse.html', {'profesiones': profesiones})


        
        
def registro_exitoso(request):
    return render(request, 'registro_exitoso.html')



def aceptacion_usuario(request):
    if not request.user.is_staff:  # Verificar si el usuario tiene privilegios de administrador
        return redirect('inicio')  # Redirigir a la página de inicio si no es administrador

    # Obtener todos los usuarios en espera
    usuarios_en_espera = PerfilUsuario.objects.filter(aprobado=False)

    if request.method == 'POST':
        # Obtener el RUT del usuario que se va a aceptar
        rut_aceptado = request.POST.get('rut_aceptado', '').strip()

        try:
            # Buscar al usuario en espera por su RUT
            perfil_usuario = PerfilUsuario.objects.get(rut=rut_aceptado, aprobado=False)
            
            # Obtener el usuario asociado al perfil
            user = perfil_usuario.user

            # Verificar si el usuario está en el grupo 'usuario en espera'
            grupo_espera = Group.objects.get(name='usuario en espera')
            if grupo_espera in user.groups.all():
                # Remover al usuario del grupo 'usuario en espera'
                user.groups.remove(grupo_espera)

                # Añadir al usuario al grupo 'usuario registrado'
                grupo_registrado, created = Group.objects.get_or_create(name='usuario registrado')
                user.groups.add(grupo_registrado)

                # Marcar al perfil como aprobado
                perfil_usuario.aprobado = True
                perfil_usuario.save()

                # Redirigir o mostrar un mensaje de éxito
                return redirect('aceptacion_usuario')  # Redirigir a la misma página para que se vea la actualización
            else:
                return render(request, 'aceptacion_usuario.html', {'error': 'El usuario no está en espera.'})

        except PerfilUsuario.DoesNotExist:
            return render(request, 'aceptacion_usuario.html', {'error': 'Usuario no encontrado en espera.'})

    return render(request, 'aceptacion_usuario.html', {'usuarios_en_espera': usuarios_en_espera})