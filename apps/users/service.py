from django.shortcuts import redirect
from django.db import transaction
from apps.ecas.models import Localidad, PuntoECA
from apps.users.models import Usuario
import csv
import io
from datetime import datetime
from config import constants as cons

class UserService:
    @staticmethod
    @transaction.atomic
    def editar_perfil(request, id):
        """
        Vista para editar el perfil del gestor ECA.
        """

        # Obtener usuario o redirigir si no existe
        try:
            # usuario = Usuario.objects.get(id=id)
            usuario = Usuario.objects.select_for_update().get(
                id=id
            )  # Bloqueo para evitar condiciones de carrera

        except Usuario.DoesNotExist:
            return redirect("base:inicio")

        # Actualizar campos básicos del usuario
        usuario.nombres = request.POST.get("nombre", usuario.nombres)
        usuario.apellidos = request.POST.get("apellido", usuario.apellidos)
        usuario.email = request.POST.get("email", usuario.email)
        usuario.celular = request.POST.get("telefono", usuario.celular)
        usuario.biografia = request.POST.get("biografia", usuario.biografia)
        usuario.fecha_nacimiento = request.POST.get("fechaNacimiento")

        # Manejo de la localidad como objeto
        localidad_id = request.POST.get("localidad")
        if localidad_id != str(
            usuario.localidad.localidad_id if usuario.localidad else ""
        ):
            try:
                usuario.localidad = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                pass  # Mantener la localidad actual si no existe la nueva

        usuario.tipo_documento = request.POST.get(
            "tipo_documento", usuario.tipo_documento
        )
        usuario.numero_documento = request.POST.get(
            "numero_documento", usuario.numero_documento
        )

        try:
            usuario.save()
        except Exception:
            pass  # Manejar errores silenciosamente por ahora

        return usuario

    @staticmethod
    @transaction.atomic
    def carga_masiva(request):
        """
        Procesa un archivo CSV subido en `request.FILES['archivo']` y crea usuarios.

        Requiere que el CSV tenga un header con nombres de columnas compatibles, por ejemplo:
        numero_documento,email,nombres,apellidos,password,tipo_usuario,fecha_nacimiento,celular,tipo_documento,localidad_id,biografia

        Si no hay header válido, intenta la forma posicional mínima:
        numero_documento;nombres;apellidos;email;password;tipo_usuario

        Retorna un diccionario {'creados': int, 'errores': list} con el resumen.
        """
        if request.method != 'POST' or 'archivo' not in request.FILES:
            return {'creados': 0, 'errores': [{'line': 0, 'error': 'No se recibió archivo CSV.'}]}

        archivo = request.FILES['archivo']
        # Validar extensión
        if not archivo.name.lower().endswith('.csv'):
            return {'creados': 0, 'errores': [{'line': 0, 'error': 'El archivo debe tener extensión .csv'}]}

        try:
            datos = archivo.read().decode('utf-8-sig')
        except Exception:
            datos = archivo.read().decode('latin-1')

        stream = io.StringIO(datos)

        # Detecta delimitador automáticamente entre ; y , para mayor compatibilidad.
        try:
            sample = datos[:2048]
            dialect = csv.Sniffer().sniff(sample, delimiters=';,')
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ';'

        reader = csv.reader(stream, delimiter=delimiter)

        try:
            header = next(reader)
        except StopIteration:
            return {'creados': 0, 'errores': [{'line': 0, 'error': 'El archivo CSV está vacío.'}]}

        # Normalizar encabezados
        header_norm = [h.strip().lower() for h in header]
        user_fieldnames = set([
            'numero_documento', 'numerodocumento',
            'email', 'correo',
            'nombres', 'nombre',
            'apellidos', 'apellido',
            'password', 'contrasena',
            'tipo_usuario', 'tipousuario', 'tipo',
            'fecha_nacimiento', 'fechanacimiento',
            'celular', 'telefono',
            'tipo_documento', 'tipodocumento',
            'localidad_id', 'localidad',
            'biografia', 'ciudad'
        ])
        punto_fieldnames = set([
            'nombrepunto', 'nombre_punto', 'nombres', 'nombre',
            'nit', 'numero_documento', 'numerodocumento',
            'correopunto', 'correo_punto', 'email', 'correo',
            'telefonopunto', 'telefono_punto', 'telefono',
            'celular',
            'direccionpunto', 'direccion',
            'localidadpunto', 'localidad',
            'latitud', 'longitud',
            'gestor_email', 'gestor',
            'tipodocumento', 'tipo_documento',
            'apellidos', 'apellido',
            'descripcion', 'ciudad'
        ])

        # Detectar si el CSV contiene usuarios o puntos ECA por encabezado o por tipo pasado en el formulario
        tipo_override = (request.POST.get('tipo') or request.POST.get('account_type') or '').strip()
        is_punto_by_type = tipo_override.lower() in ('gestoreca','gestor_eca','eca','puntoeca')

        has_user_fields = bool(user_fieldnames.intersection(set(header_norm)))
        has_punto_fields = bool(punto_fieldnames.intersection(set(header_norm)))

        use_header = has_user_fields or has_punto_fields

        creados = 0
        errores = []

        for i, row in enumerate(reader, start=2):
            try:
                if use_header:
                    row_map = {header_norm[idx]: row[idx].strip() if idx < len(row) else '' for idx in range(len(header_norm))}
                else:
                    # Positional fallback
                    # documento;nombres;apellidos;email;password;tipo_usuario
                    row_map = {}
                    row_map['numero_documento'] = row[0].strip() if len(row) > 0 else ''
                    row_map['nombres'] = row[1].strip() if len(row) > 1 else ''
                    row_map['apellidos'] = row[2].strip() if len(row) > 2 else ''
                    row_map['email'] = row[3].strip() if len(row) > 3 else ''
                    row_map['password'] = row[4].strip() if len(row) > 4 else ''
                    row_map['tipo_usuario'] = row[5].strip() if len(row) > 5 else ''

                # Determinar si esta fila corresponde a PuntoECA o Usuario
                row_keys = set(row_map.keys())
                is_punto = False
                if has_punto_fields or is_punto_by_type:
                    # heurística por campos
                    if any(k in row_keys for k in ('nombrepunto','nombre_punto','nombres','correopunto','telefonopunto','telefono_punto','direccionpunto','direccion')):
                        is_punto = True

                if is_punto:
                    # Mapear campos de PuntoECA (soporta nombres con/ sin guión/underscore)
                    nombre = row_map.get('nombrepunto') or row_map.get('nombre_punto') or row_map.get('nombres') or row_map.get('nombre')
                    correo_punto = row_map.get('correopunto') or row_map.get('correo_punto') or row_map.get('correo')
                    telefono_punto = row_map.get('telefonopunto') or row_map.get('telefono_punto') or row_map.get('telefono')
                    celular_contacto = row_map.get('celular') or row_map.get('telefono_contacto')
                    direccion = row_map.get('direccionpunto') or row_map.get('direccion')
                    sitio_web = row_map.get('sitio_web') or row_map.get('sitioweb')
                    localidad_val = row_map.get('localidadpunto') or row_map.get('localidad')
                    lat = row_map.get('latitud')
                    lon = row_map.get('longitud')
                    gestor_email = row_map.get('gestor_email') or row_map.get('gestor')
                    descripcion = row_map.get('descripcion') or ''
                    ciudad = row_map.get('ciudad') or 'Bogota'

                    if not nombre:
                        raise ValueError('Falta nombre del punto en la fila')

                    punto = PuntoECA.objects.create(
                        nombre=nombre,
                        direccion=direccion or '',
                        celular=celular_contacto or '',
                        email=correo_punto or '',
                        telefono_punto=telefono_punto or '',
                        sitio_web=sitio_web or '',
                        descripcion=descripcion,
                        ciudad=ciudad,
                    )
                    # asociar localidad
                    if localidad_val:
                        try:
                            punto.localidad = Localidad.objects.get(localidad_id=localidad_val)
                        except Exception:
                            try:
                                punto.localidad = Localidad.objects.get(nombre__iexact=localidad_val)
                            except Exception:
                                pass
                    # asociar gestor si se proporciona
                    if gestor_email:
                        try:
                            gestor = Usuario.objects.filter(email__iexact=gestor_email).first()
                            if gestor:
                                punto.gestor_eca = gestor
                        except Exception:
                            pass

                    def _parse_float_coordinate(value):
                        if value is None:
                            return None
                        s = str(value).strip()
                        if not s:
                            return None
                        s = s.replace(' ', '')
                        if '.' in s and ',' in s:
                            if s.rfind('.') < s.rfind(','):
                                s = s.replace('.', '')
                                s = s.replace(',', '.')
                            else:
                                s = s.replace(',', '')
                        else:
                            s = s.replace(',', '.')
                        import re
                        s = re.sub(r'[^0-9\.\-]', '', s)
                        if s in ('', '.', '-', '-.', '.-'):
                            return None
                        try:
                            return float(s)
                        except Exception:
                            return None

                    parsed_lat = _parse_float_coordinate(lat)
                    parsed_lon = _parse_float_coordinate(lon)
                    if parsed_lat is not None:
                        punto.latitud = parsed_lat
                    if parsed_lon is not None:
                        punto.longitud = parsed_lon

                    punto.save()
                    creados += 1
                else:
                    # Procesar como Usuario
                    numero_documento = row_map.get('numero_documento') or row_map.get('numerodocumento') or row_map.get('documento')
                    email = row_map.get('email') or row_map.get('correo')
                    nombres = row_map.get('nombres') or row_map.get('nombre')
                    apellidos = row_map.get('apellidos') or row_map.get('apellido')
                    password = row_map.get('password') or None
                    tipo_usuario = (row_map.get('tipo_usuario') or row_map.get('tipo') or '').upper()
                    fecha_nacimiento_raw = row_map.get('fecha_nacimiento') or row_map.get('fechanacimiento')
                    celular = row_map.get('celular') or row_map.get('telefono')
                    tipo_documento = row_map.get('tipo_documento') or row_map.get('tipodocumento')
                    localidad_id = row_map.get('localidad_id') or row_map.get('localidad')
                    biografia = row_map.get('biografia')
                    ciudad = row_map.get('ciudad') or 'Bogota'

                    if not numero_documento:
                        numero_documento = f"CIU_{email}" if email else ''

                    extra = {}
                    if nombres:
                        extra['nombres'] = nombres
                    if apellidos:
                        extra['apellidos'] = apellidos
                    if celular:
                        extra['celular'] = celular
                    if tipo_documento:
                        extra['tipo_documento'] = tipo_documento
                    if biografia:
                        extra['biografia'] = biografia
                    if ciudad:
                        extra['ciudad'] = ciudad

                    # fecha_nacimiento parse
                    if fecha_nacimiento_raw:
                        try:
                            extra['fecha_nacimiento'] = datetime.strptime(fecha_nacimiento_raw.strip(), '%Y-%m-%d').date()
                        except Exception:
                            try:
                                extra['fecha_nacimiento'] = datetime.strptime(fecha_nacimiento_raw.strip(), '%d/%m/%Y').date()
                            except Exception:
                                pass

                    # localizar localidad por id o nombre
                    if localidad_id:
                        try:
                            extra['localidad'] = Localidad.objects.get(localidad_id=localidad_id)
                        except Exception:
                            try:
                                extra['localidad'] = Localidad.objects.get(nombre__iexact=localidad_id)
                            except Exception:
                                pass

                    # Crear según tipo
                    if tipo_usuario in (cons.TipoUsuario.GESTOR_ECA, 'GECA'):
                        Usuario.objects.create_gestor_eca(email=email, numero_documento=numero_documento, password=password, **extra)
                    elif tipo_usuario in (cons.TipoUsuario.ADMIN, 'ADM', 'ADMIN'):
                        extra.setdefault('is_staff', True)
                        extra.setdefault('is_superuser', True)
                        extra.setdefault('tipo_usuario', cons.TipoUsuario.ADMIN)
                        Usuario.objects.create_user(email=email, numero_documento=numero_documento, password=password, **extra)
                    else:
                        extra.setdefault('tipo_usuario', cons.TipoUsuario.CIUDADANO)
                        Usuario.objects.create_user(email=email, numero_documento=numero_documento, password=password, **extra)

                    creados += 1
            except Exception as e:
                errores.append({'line': i, 'error': str(e), 'row': row})

        return {'creados': creados, 'errores': errores}
