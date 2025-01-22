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
        password = request.POST.get('password', '').strip()

        try:
            # Buscar al usuario por el RUT
            perfil = PerfilUsuario.objects.get(rut=rut)
            user = perfil.user  # Obtener el usuario relacionado

            # Autenticar al usuario con la contraseña
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)

                # Verificar si el usuario pertenece al grupo "usuario registrado"
                if user.groups.filter(name='usuario registrado').exists():
                    # Redirigir a la interfaz específica
                    return render(request, 'Roles/UsuarioRegistrado/usuario_registrado.html')
                else:
                    # Si no pertenece al grupo, redirigir a una página general
                    return render(request, 'inicio.html', {'error': 'No tiene permisos para acceder a esta sección.'})
            else:
                return render(request, 'inicio.html', {'error': 'Credenciales incorrectas.'})

        except PerfilUsuario.DoesNotExist:
            return render(request, 'inicio.html', {'error': 'El RUT ingresado no está registrado.'})

    # Si la solicitud es GET, mostrar la página de inicio de sesión
    return render(request, 'inicio.html')

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

        # Asignar el rol de "usuario registrado"
        group, created = Group.objects.get_or_create(name='usuario registrado')
        user.groups.add(group)

        # Crear el perfil del usuario
        try:
            perfil = PerfilUsuario(user=user, rut=rut, telefono=telefono, profesion=profesion, aprobado=False)
            perfil.save()
        except Exception as e:
            user.delete()  # Eliminar usuario si el perfil no se pudo crear
            return render(request, 'registrarse.html', {'error': f'Error al crear el perfil: {e}'})

        # Autenticar y loguear al usuario
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

        return redirect('registro_exitoso')  # Redirigir a la página de éxito después del registro

    else:
        # Obtener las profesiones disponibles
        profesiones = Profesion_Oficio.objects.all()

        # Contar la cantidad de usuarios registrados
        usuarios_registrados = User.objects.count()

        # Pasar la cantidad de usuarios al contexto
        return render(request, 'registrarse.html', {
            'profesiones': profesiones,
            'usuarios_registrados': usuarios_registrados
        })
        
        
def registro_exitoso(request):
    return render(request, 'registro_exitoso.html')