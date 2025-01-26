# Importaciones de Django (Incluido con Django, no requiere instalación adicional)
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required

# Importaciones para manejo de modelos personalizados (Incluido en tu proyecto)
from .models import *

# Manejo de archivos Excel con openpyxl
# Instalación en Windows: pip install openpyxl
# Instalación en Ubuntu 24: sudo apt install python3-openpyxl
from openpyxl.styles import *

# Creación y manipulación de PDFs
# Lectura de PDFs con pdfplumber
# Instalación en Windows: pip install pdfplumber
# Instalación en Ubuntu 24: sudo apt install python3-pdfplumber
import pdfplumber


# Manejo de configuraciones y rutas en Django (Incluido con Django)
import os
from django.conf import settings



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

meses_espanol = {
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


meses_espanol_a_numero = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12
}





meses = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]

# Lista de meses
meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


meses = {
    
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def cargar_asistencia_uno(request):
    pdf_file = None
    error_message = None

    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']

        # Obtener mes y año del formulario
        mes = request.POST.get('mes')
        año = request.POST.get('año')

        # Verificar el valor del mes (para depuración)
        print(f"Mes recibido: {mes}")  # Debugging: Muestra el valor de mes recibido en los logs

        # Validación de mes y año
        if not mes or not año:
            error_message = "Mes y año son requeridos."
            return render(request, 'cargar_asistencia.html', {'error_message': error_message})

        # Validar que el mes sea un número entre 1 y 12
        try:
            mes_num = int(mes)
            if mes_num < 1 or mes_num > 12:
                raise ValueError("Mes fuera de rango")
        except ValueError:
            error_message = "Mes no válido. Debe ser un número entre 1 y 12."
            return render(request, 'cargar_asistencia.html', {'error_message': error_message})

        try:
            # Leer el PDF para extraer el RUT y demás información
            with pdfplumber.open(pdf_file) as pdf:
                texto_completo = ""
                for pagina in pdf.pages:
                    texto_completo += pagina.extract_text()

            # Extraer el RUT del encabezado
            rut_linea = next((linea for linea in texto_completo.splitlines() if "RUT:" in linea), None)
            if rut_linea:
                rut = rut_linea.split(":")[1].strip().replace("-", "").replace(".", "")
            else:
                error_message = "RUT no encontrado en el PDF."
                return render(request, 'cargar_asistencia.html', {'error_message': error_message})

            # Asociar el PDF al perfil correspondiente
            try:
                perfil = PerfilUsuario.objects.get(rut=rut)

                # Obtener el nombre del mes (como string)
                mes_nombre = meses.get(mes_num, None)
                if not mes_nombre:
                    error_message = "Mes no válido."
                    return render(request, 'cargar_asistencia.html', {'error_message': error_message})

                # Crear el directorio basado en el RUT, año y nombre del mes
                directorio_pdf = os.path.join(settings.MEDIA_ROOT, 'asistencias_pdfs', rut, str(año), mes_nombre)
                os.makedirs(directorio_pdf, exist_ok=True)  # Crear directorio si no existe

                # Guardar el PDF en el servidor en el directorio específico del funcionario
                pdf_path = os.path.join(directorio_pdf, pdf_file.name)
                with open(pdf_path, 'wb') as f:
                    for chunk in pdf_file.chunks():
                        f.write(chunk)

                # Crear o actualizar la asistencia para el mes y año
                asistencia, created = AsistenciaMes.objects.get_or_create(
                    perfil=perfil,
                    mes=mes_num,  # Usamos el número del mes
                    año=año
                )

                # Actualizar el archivo PDF en el modelo AsistenciaMes
                asistencia.pdf_asistencia = f'asistencias_pdfs/{rut}/{año}/{mes_nombre}/{pdf_file.name}'
                asistencia.save()

                # También actualizar el PDF en el perfil (PerfilUsuario)
                perfil.pdf_asistencia = f'asistencias_pdfs/{rut}/{año}/{mes_nombre}/{pdf_file.name}'
                perfil.save()

                # Si todo va bien, devolver el archivo PDF para la descarga
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()

                pdf_response = HttpResponse(pdf_data, content_type='application/pdf')
                pdf_response['Content-Disposition'] = f'attachment; filename={pdf_file.name}'

                return pdf_response

            except PerfilUsuario.DoesNotExist:
                error_message = f"Perfil no encontrado para el RUT {rut}. El PDF no se asoció."
                return render(request, 'cargar_asistencia.html', {'error_message': error_message})

        except Exception as e:
            error_message = f"Error al procesar el PDF: {str(e)}"
            return render(request, 'cargar_asistencia.html', {'error_message': error_message})

    return render(request, 'cargar_asistencia.html', {'pdf_file': pdf_file, 'error_message': error_message})





def descargar_registro_asistencia(request):
    mensaje = None
    pdf_encontrado = False
    pdf_url = None

    if request.method == 'POST':
        # Obtener los datos del formulario
        usuario_id = request.POST.get('usuario')
        mes = int(request.POST.get('mes'))  # Asegurarnos de que el mes sea un número entero

        # Verificar que los campos estén presentes
        if not usuario_id or not mes:
            mensaje = "Todos los campos son requeridos."
            return render(request, 'seleccionar_usuario.html', {'mensaje': mensaje})

        # Obtener el perfil de usuario
        try:
            perfil = PerfilUsuario.objects.get(id=usuario_id)
        except PerfilUsuario.DoesNotExist:
            mensaje = "El usuario seleccionado no existe."
            return render(request, 'seleccionar_usuario.html', {'mensaje': mensaje})

        # Intentar buscar la asistencia para ese usuario y mes
        try:
            asistencia = AsistenciaMes.objects.get(perfil=perfil, mes=mes)
            pdf_url = asistencia.pdf_asistencia.url if asistencia.pdf_asistencia else None
            if pdf_url:
                pdf_encontrado = True
            else:
                mensaje = f"No se ha encontrado el archivo PDF para el mes {dict(AsistenciaMes.MES_CHOICES).get(mes)}."
        except AsistenciaMes.DoesNotExist:
            mensaje = f"No se ha encontrado el archivo PDF para el mes {dict(AsistenciaMes.MES_CHOICES).get(mes)}."

        # Si el PDF está encontrado, proceder con la descarga
        if pdf_encontrado:
            pdf_path = asistencia.pdf_asistencia.path  # Ruta completa al archivo en el sistema de archivos
            with open(pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                return response

        # Si no se encuentra el archivo, renderizamos el mensaje de error
        return render(request, 'seleccionar_usuario.html', {
            'mensaje': mensaje,
            'usuarios': PerfilUsuario.objects.all()
        })

    # Si no es POST, simplemente renderizamos el formulario
    return render(request, 'seleccionar_usuario.html', {
        'usuarios': PerfilUsuario.objects.all()
    })
    

@login_required  # Asegura que solo usuarios autenticados puedan acceder
def descargar_asistencia(request, rut, mes, año):
    try:
        # Verificar si el usuario actual tiene acceso al perfil de este RUT
        perfil = PerfilUsuario.objects.get(rut=rut)
        
        # Verifica que el usuario autenticado sea el mismo que el dueño del perfil
        if request.user != perfil.user:
            raise PermissionError("No tienes permiso para acceder a este archivo.")

        # Obtenemos el nombre del mes de la misma forma que antes
        meses = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
            7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        mes_nombre = meses.get(int(mes), None)
        if not mes_nombre:
            raise Http404("Mes no válido.")
        
        # Construir la ruta completa al archivo PDF
        directorio_pdf = os.path.join(settings.MEDIA_ROOT, 'asistencias_pdfs', perfil.nombre_completo.lower().replace(" ", "_"), str(año), mes_nombre)
        pdf_path = os.path.join(directorio_pdf, f"{rut}_{mes_nombre}_{año}.pdf")  # El nombre del archivo podría incluir el RUT, mes y año
        
        # Verificar si el archivo existe
        if not os.path.exists(pdf_path):
            raise Http404("Archivo no encontrado.")
        
        # Si el archivo existe, devolverlo como respuesta HTTP para descarga
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={os.path.basename(pdf_path)}'
        return response

    except PerfilUsuario.DoesNotExist:
        raise Http404("Perfil no encontrado.")
    except PermissionError as e:
        return HttpResponse(str(e), status=403)  # Respuesta con error 403 si no tiene permiso
    except Exception as e:
        return HttpResponse(f"Error al procesar la descarga: {str(e)}", status=500)
    
    
    
@login_required
def descargar_pdf_perfil(request):
    try:
        # Obtener el perfil del usuario autenticado
        perfil = request.user.perfilusuario

        # Verificar que el PDF esté configurado
        if not perfil.pdf_asistencia:
            raise Http404("No tienes un archivo asociado para descargar.")

        # Ruta completa al archivo
        ruta_pdf = perfil.pdf_asistencia.path

        # Verificar si el archivo existe en el servidor
        if not os.path.exists(ruta_pdf):
            raise Http404("El archivo no existe en el servidor.")

        # Enviar el archivo como respuesta de descarga
        with open(ruta_pdf, 'rb') as archivo:
            response = HttpResponse(archivo.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(ruta_pdf)}"'
            return response

    except PerfilUsuario.DoesNotExist:
        raise Http404("No se encontró el perfil asociado a este usuario.")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)




def panel_administrador(request):
    return render(request, 'Grupos/Administrador/panel_administrador.html')




import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from .forms import ExcelUploadForm
from .models import Asistencia

# Vista para cargar y guardar los datos del Excel
def cargar_excel(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        
        # Leer el archivo Excel usando pandas
        df = pd.read_excel(excel_file)

        # Crear una lista para almacenar las instancias de Asistencia antes de guardarlas
        asistencia_list = []

        # Recorrer las filas del DataFrame y guardar los datos en la base de datos
        for index, row in df.iterrows():
            try:
                # Convertir la fecha al formato adecuado YYYY-MM-DD si no está vacía
                if pd.notna(row['fecha']):
                    try:
                        fecha = datetime.strptime(row['fecha'], '%d-%m-%Y').date()
                    except ValueError:
                        fecha = None  # Si la fecha tiene un formato incorrecto, asignamos None
                else:
                    fecha = None  # Si la fecha está vacía, la dejamos vacía

                # Verificar si cada campo está vacío y dejarlo vacío si es necesario
                ac = row['ac'] if pd.notna(row['ac']) else None
                rut = row['rut'] if pd.notna(row['rut']) else None  # Asegurarse de que el RUT no esté vacío
                nombre = row['nombre'] if pd.notna(row['nombre']) else ''
                dpto = row['dpto'] if pd.notna(row['dpto']) else ''
                mes = row['mes'] if pd.notna(row['mes']) else ''
                ano = row['ano'] if pd.notna(row['ano']) else ''
                marcaciones = row['marcaciones'] if pd.notna(row['marcaciones']) else ''
                observaciones = row['observaciones'] if pd.notna(row['observaciones']) else ''

                # Validación: Si el RUT es obligatorio, comprobamos si está vacío
                if not rut:
                    print(f"Fila {index}: El RUT está vacío, asociando los datos al AC {ac}.")
                    # Si no hay RUT, pero sí hay AC, buscamos el registro con el AC
                    if ac:
                        # Aquí puedes decidir cómo asociar el AC a un registro existente o crear uno nuevo
                        # Si el 'ac' es único, puedes buscarlo y asociarlo con la fila
                        asistencia = Asistencia(
                            ac=ac,  # Asociar el valor de AC si el RUT no existe
                            rut=None,  # Si no hay RUT, dejamos este campo en blanco o como None
                            nombre=nombre,
                            dpto=dpto,
                            mes=mes,
                            ano=ano,
                            fecha=fecha,
                            marcaciones=marcaciones,
                            observaciones=observaciones,
                        )
                        asistencia_list.append(asistencia)
                    else:
                        print(f"Fila {index}: El RUT y el AC están vacíos, saltando esta fila.")
                        continue  # Si tampoco hay AC, omitimos la fila
                else:
                    # Si el RUT existe, asociamos los datos al RUT existente
                    asistencia = Asistencia(
                        ac=ac,  # Asociar AC si está presente
                        rut=rut,  # Asociamos el RUT
                        nombre=nombre,
                        dpto=dpto,
                        mes=mes,
                        ano=ano,
                        fecha=fecha,
                        marcaciones=marcaciones,
                        observaciones=observaciones,
                    )
                    asistencia_list.append(asistencia)  # Añadir la instancia a la lista

            except Exception as e:
                print(f"Error al procesar la fila {index}: {e}")

        # Guardar todas las instancias de una sola vez en la base de datos
        if asistencia_list:
            Asistencia.objects.bulk_create(asistencia_list)
            print(f"{len(asistencia_list)} registros guardados correctamente.")
        
        # Respuesta después de procesar el archivo
        return HttpResponse("Archivo cargado y datos guardados correctamente.")

    # Formulario para cargar el archivo Excel
    form = ExcelUploadForm()

    return render(request, 'cargar_excel.html', {'form': form})




from django.http import HttpResponse
from xhtml2pdf import pisa
from datetime import datetime
from .models import Asistencia

from datetime import datetime
from io import BytesIO
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.templatetags.static import static


import base64
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
from datetime import datetime
import os

def generar_pdf(request):
    # Obtener todos los registros de asistencia
    asistencia_records = Asistencia.objects.all()

    # Obtener la fecha y hora actual
    fecha_emision = datetime.now()
    fecha_actual = fecha_emision.strftime('%d-%m-%Y')
    hora_emision = fecha_emision.strftime('%H:%M:%S')

    # Traducir el mes al español
    meses_espanol = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
        'April': 'Abril', 'May': 'Mayo', 'June': 'Junio', 'July': 'Julio',
        'August': 'Agosto', 'September': 'Septiembre', 'October': 'Octubre',
        'November': 'Noviembre', 'December': 'Diciembre'
    }
    mes_actual = meses_espanol[fecha_emision.strftime('%B')]

    # Inicialización de la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="informe_asistencia.pdf"'

    # Convertir la imagen a Base64
    imagen_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Cesfaaaam.png')

    # Convertir imagen a base64
    with open(imagen_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Crear la imagen en formato base64 para el HTML
    imagen_base64 = f"data:image/png;base64,{encoded_image}"

    # Plantilla HTML base para el PDF
    html_content = f"""
    <html>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            h1 {{
                text-align: center;
                color: #0044cc;
                border-bottom: 2px solid #0044cc;
                margin-bottom: 20px;
            }}
            h2 {{
                text-align: center;
                font-size: 18px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                text-align: center;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            td {{
                font-size: 12px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .header .izquierda {{
                text-align: left;
                font-size: 10px;
            }}
            .header .derecha {{
                text-align: right;
                font-size: 10px;
            }}
            .mes {{
                text-align: center;
                font-size: 14px;
                font-weight: bold;
            }}
            .funcionario-info {{
                text-align: center;
                font-size: 12px;
                margin-top: 20px;
            }}
            .logo {{
                text-align: center;
                margin-top: 10px;
            }}
            .logo img {{
                width: 150px;
            }}
        </style>
        <body>
    """

    # Filtrar registros por funcionario y crear HTML para cada uno
    funcionarios = asistencia_records.values('nombre', 'rut').distinct()

    for funcionario in funcionarios:
        nombre_funcionario = funcionario['nombre']
        rut_funcionario = funcionario['rut']
        registros_funcionario = asistencia_records.filter(nombre=nombre_funcionario)

        # Insertar encabezado antes de cada funcionario
        html_content += f"""
            <div class="header">
                <div class="logo">
                    <img src="{imagen_base64}" alt="Logo" style="width: 50px; height: auto;">
                </div>
                <div class="izquierda">
                    <p><strong>MUNICIPALIDAD DE PAILLACO</strong></p>
                    <p><strong>DEPARTAMENTO DE SALUD</strong></p>
                </div>
                <div class="derecha">
                    <p><strong>Fecha de Emisión:</strong> {fecha_actual}</p>
                    <p><strong>Hora de Emisión:</strong> {hora_emision}</p>
                </div>
            </div>

            <h1>INFORME DE ASISTENCIA DE PERSONAL</h1>

            <div class="mes">
                <p><strong>Mes: {mes_actual}</strong></p>
            </div>
        """

        # Añadir los registros de asistencia para este funcionario
        html_content += f"""
            <div class="funcionario-info">
                <table style="font-size: 6px; width: 100%; table-layout: fixed;">
                    <tr>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px; background-color: yellow;">
                            <strong>FUNCIONARIO</strong>
                        </td>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px;">
                            {nombre_funcionario}
                        </td>
                    </tr>
                    <tr>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px; background-color: yellow;">
                            <strong>RUT</strong>
                        </td>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px;">
                            {rut_funcionario}
                        </td>
                    </tr>
                </table>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="font-size: 10px; text-align: center; background-color: yellow; padding-top: 3px;">FECHA</th>
                        <th style="font-size: 10px; text-align: center; background-color: yellow; padding-top: 3px;">MARCACIONES EN RELOJ</th>
                    </tr>
                </thead>
                <tbody>
        """

        for asistencia in registros_funcionario:
            html_content += f"""
            <tr>
                <td style="font-size: 10px; text-align: center; padding-top: 3px;">{asistencia.fecha.strftime('%d-%m-%Y')}</td>
                <td style="font-size: 10px; text-align: center; padding-top: 3px;">{asistencia.marcaciones}</td>
            </tr>
            """
        
        html_content += "</tbody></table><br />"

    html_content += """
        </body>
    </html>
    """

    # Convertir el HTML generado a PDF
    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=400)

    return response






def generar_pdfee(request):
    # Obtener todos los registros de asistencia
    asistencia_records = Asistencia.objects.all()

    # Obtener la fecha y hora actual
    fecha_emision = datetime.now()
    fecha_actual = fecha_emision.strftime('%d-%m-%Y')
    hora_emision = fecha_emision.strftime('%H:%M:%S')

    # Traducir el mes al español
    meses_espanol = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
        'April': 'Abril', 'May': 'Mayo', 'June': 'Junio', 'July': 'Julio',
        'August': 'Agosto', 'September': 'Septiembre', 'October': 'Octubre',
        'November': 'Noviembre', 'December': 'Diciembre'
    }
    mes_actual = meses_espanol[fecha_emision.strftime('%B')]

    # Inicialización de la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="informe_asistencia.pdf"'

    # Convertir la imagen a Base64
    imagen_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Cesfaaaam.png')

    # Convertir imagen a base64
    with open(imagen_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Crear la imagen en formato base64 para el HTML
    imagen_base64 = f"data:image/png;base64,{encoded_image}"

    # Plantilla HTML base para el PDF
    html_content = f"""
    <html>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            h1 {{
                text-align: center;
                color: #0044cc;
                border-bottom: 2px solid #0044cc;
                margin-bottom: 20px;
            }}
            h2 {{
                text-align: center;
                font-size: 18px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                text-align: center;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            td {{
                font-size: 12px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .header .izquierda {{
                text-align: left;
                font-size: 10px;
            }}
            .header .derecha {{
                text-align: right;
                font-size: 10px;
            }}
            .mes {{
                text-align: center;
                font-size: 14px;
                font-weight: bold;
            }}
            .funcionario-info {{
                text-align: center;
                font-size: 12px;
                margin-top: 20px;
            }}
            .logo {{
                text-align: center;
                margin-top: 10px;
            }}
            .logo img {{
                width: 150px;
            }}
        </style>
        <body>
    """

    # Filtrar registros por funcionario y crear HTML para cada uno
    funcionarios = asistencia_records.values('nombre', 'rut').distinct()

    for funcionario in funcionarios:
        nombre_funcionario = funcionario['nombre']
        rut_funcionario = funcionario['rut']
        registros_funcionario = asistencia_records.filter(nombre=nombre_funcionario)

        # Insertar encabezado antes de cada funcionario
        html_content += f"""
            <div class="header">
                <div class="logo">
                    <img src="{imagen_base64}" alt="Logo" style="width: 50px; height: auto;">
                </div>
                <div class="izquierda">
                    <p><strong>MUNICIPALIDAD DE PAILLACO</strong></p>
                    <p><strong>DEPARTAMENTO DE SALUD</strong></p>
                </div>
                <div class="derecha">
                    <p><strong>Fecha de Emisión:</strong> {fecha_actual}</p>
                    <p><strong>Hora de Emisión:</strong> {hora_emision}</p>
                </div>
            </div>

            <h1>INFORME DE ASISTENCIA DE PERSONAL</h1>

            <div class="mes">
                <p><strong>Mes: {mes_actual}</strong></p>
            </div>
        """

        # Añadir los registros de asistencia para este funcionario
        html_content += f"""
            <div class="funcionario-info">
                <table style="font-size: 6px; width: 100%; table-layout: fixed;">
                    <tr>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px; background-color: yellow;">
                            <strong>FUNCIONARIO</strong>
                        </td>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px;">
                            {nombre_funcionario}
                        </td>
                    </tr>
                    <tr>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px; background-color: yellow;">
                            <strong>RUT</strong>
                        </td>
                        <td style="width: 50%; text-align: center; vertical-align: bottom; padding: 8px 2px 2px 2px;">
                            {rut_funcionario}
                        </td>
                    </tr>
                </table>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="font-size: 10px; text-align: center; background-color: yellow; padding-top: 3px;">FECHA</th>
                        <th style="font-size: 10px; text-align: center; background-color: yellow; padding-top: 3px;">MARCACIONES EN RELOJ</th>
                    </tr>
                </thead>
                <tbody>
        """

        for asistencia in registros_funcionario:
            html_content += f"""
            <tr>
                <td style="font-size: 10px; text-align: center; padding-top: 3px;">{asistencia.fecha.strftime('%d-%m-%Y')}</td>
                <td style="font-size: 10px; text-align: center; padding-top: 3px;">{asistencia.marcaciones}</td>
            </tr>
            """
        
        html_content += "</tbody></table><br />"

    html_content += """
        </body>
    </html>
    """

    # Convertir el HTML generado a PDF
    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=400)

    return response











