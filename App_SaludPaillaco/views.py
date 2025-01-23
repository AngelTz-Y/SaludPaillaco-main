from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import PerfilUsuario, Profesion_Oficio
from django.contrib.auth.models import Group
import pandas as pd
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PerfilUsuario, Asistencia
from datetime import datetime
import locale
import pandas as pd
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from .models import Asistencia

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
                    return redirect('panel_administrador')

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


# Diccionario para convertir nombre de mes a número
meses = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
    "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10,
    "Noviembre": 11, "Diciembre": 12
}

meses_esp = {
    "January": "Enero",
    "February": "Febrero",
    "March": "Marzo",
    "April": "Abril",
    "May": "Mayo",
    "June": "Junio",
    "July": "Julio",
    "August": "Agosto",
    "September": "Septiembre",
    "October": "Octubre",
    "November": "Noviembre",
    "December": "Diciembre",
}

def cargar_asistencia_uno(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        
        # Leer el archivo Excel
        df = pd.read_excel(excel_file)
        
        # Crear lista de registros procesados para generar el nuevo Excel
        registros = []
        
        # Iterar sobre cada fila del archivo
        for index, row in df.iterrows():
            # Normalizar el RUT (eliminar guiones)
            rut = str(row['RUT']).replace("-", "").strip()
            
            try:
                # Buscar el perfil del usuario por RUT (sin guion)
                perfil = PerfilUsuario.objects.get(rut=rut)
                
                # Leer Mes (nombre del mes como texto), Día y Horas trabajadas
                mes_texto = row['Mes']
                dia = int(row['Dia'])  # Convertir 'Dia' a entero
                horas_trabajadas = row['Horas Trabajadas']
                
                # Convertir el nombre del mes a número usando el diccionario
                if mes_texto in meses:
                    mes = meses[mes_texto]
                else:
                    print(f"Mes desconocido: {mes_texto}")
                    continue  # Saltar la fila si el mes no es válido
                
                # Crear fecha (usando el año actual)
                fecha = datetime(datetime.now().year, mes, dia)
                
                # Guardar la asistencia en la base de datos
                Asistencia.objects.create(perfil=perfil, fecha=fecha, horas_trabajadas=horas_trabajadas)

                # Añadir el registro procesado a la lista
                registros.append({
                    "RUT": rut,
                    "Mes": mes_texto,
                    "Dia": dia,
                    "Horas Trabajadas": horas_trabajadas,
                    "Fecha": fecha
                })
            
            except PerfilUsuario.DoesNotExist:
                # Si el RUT no existe en la base de datos
                print(f"Funcionario con RUT {rut} no encontrado.")
                continue  # Continuar con la siguiente fila
        
        # Generar un DataFrame de pandas con los registros procesados
        if registros:
            df_resultado = pd.DataFrame(registros)
            
            # Crear un archivo Excel en memoria
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=asistencia_procesada.xlsx'
            
            # Escribir el DataFrame a la respuesta HTTP (en formato Excel)
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name='Asistencia')
            
            return response
        
        return HttpResponse("Archivo procesado exitosamente, pero no se generaron registros.")

    return render(request, 'cargar_asistencia.html')


def descargar_asistencia(request):
    # Obtener todos los registros de asistencia desde la base de datos
    asistencias = Asistencia.objects.all().select_related('perfil')

    # Crear una lista con los registros para el archivo Excel
    registros = []
    for asistencia in asistencias:
        # Convertir el mes en inglés a español
        mes_espanol = meses_esp.get(asistencia.fecha.strftime('%B'), asistencia.fecha.strftime('%B'))

        registros.append({
            "RUT": asistencia.perfil.rut,
            "Nombre": asistencia.perfil.user.get_full_name(),
            "Mes": mes_espanol,  # Nombre del mes en español
            "Dia": asistencia.fecha.day,
            "Horas Trabajadas": asistencia.horas_trabajadas,
            "Fecha": asistencia.fecha.strftime('%Y-%m-%d')  # Fecha en formato YYYY-MM-DD
        })

    # Si hay registros, crear el archivo Excel
    if registros:
        # Crear un DataFrame con los registros
        df = pd.DataFrame(registros)
        
        # Crear una respuesta HTTP con tipo de contenido para un archivo Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=asistencia_registros.xlsx'

        # Crear un libro de trabajo de Excel con openpyxl
        wb = Workbook()
        ws = wb.active
        ws.title = "Asistencia"

        # Escribir los encabezados
        encabezados = df.columns.tolist()
        for col_num, col_name in enumerate(encabezados, 1):
            cell = ws.cell(row=1, column=col_num, value=col_name)
            cell.font = Font(bold=True)  # Negritas para los encabezados
            cell.alignment = Alignment(horizontal="center", vertical="center")  # Centrar encabezados

        # Escribir los registros de la tabla
        for row_num, row in enumerate(df.values, 2):
            for col_num, value in enumerate(row, 1):
                cell = ws.cell(row=row_num, column=col_num, value=value)
                cell.alignment = Alignment(horizontal="center", vertical="center")  # Centrar celdas

                # Aplicar negritas al mes
                if col_num == 3:  # Columna 'Mes'
                    cell.font = Font(bold=True)  # Negritas en los meses

        # Ajustar el tamaño de las columnas para que el texto se vea bien
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter  # Obtener la letra de la columna
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width

        # Guardar el archivo Excel en la respuesta
        wb.save(response)
        
        return response
    else:
        return HttpResponse("No se encontraron registros de asistencia para descargar.")



@csrf_exempt  # Evita problemas con CSRF (solo en desarrollo)
def cargar_asistencia_varios(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            # Leer el archivo Excel
            file = request.FILES['file']
            df = pd.read_excel(file)

            # Procesar cada fila del DataFrame (cada fila es un registro de asistencia)
            for index, row in df.iterrows():
                rut = row['RUT']  # RUT del trabajador
                try:
                    perfil = PerfilUsuario.objects.get(rut=rut)
                    mes = row['Mes']  # Mes (puede ser número o nombre)
                    dia = row['Dia']  # Día
                    horas_trabajadas = row['Horas Trabajadas']  # Horas trabajadas

                    # Convertir la fecha
                    if isinstance(mes, int) and 1 <= mes <= 12:
                        fecha = datetime(datetime.now().year, mes, dia)  # Año actual
                    else:
                        try:
                            fecha = datetime.strptime(f"{dia}-{mes}-2025", "%d-%B-%Y")
                        except ValueError:
                            print(f"Fecha no válida en el archivo para el RUT {rut}.")
                            continue

                    # Registrar la asistencia
                    Asistencia.objects.create(perfil=perfil, fecha=fecha, horas_trabajadas=horas_trabajadas)

                except PerfilUsuario.DoesNotExist:
                    print(f"Funcionario con RUT {rut} no encontrado.")

            return JsonResponse({'status': 'success', 'message': 'Asistencias registradas correctamente.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return HttpResponse("Método no permitido", status=405)





def panel_administrador(request):
    return render(request, 'Grupos/Administrador/panel_administrador.html')
    