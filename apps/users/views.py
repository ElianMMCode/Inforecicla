from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from apps.ecas.models import Localidad, PuntoECA
from apps.users.models import Usuario
from apps.users.service import UserService
from config import constants as cons


def render_login(request):
	errores = []
	next_url = request.GET.get("next") or request.POST.get("next")
	if request.method == "POST":
		email = request.POST.get("email", "").strip().lower()
		password = request.POST.get("password", "")
		user = authenticate(request, username=email, password=password)
		if user is not None:
			login(request, user)
			if next_url:
				return redirect(next_url)
			if bool(user.is_staff or user.is_superuser or user.tipo_usuario == cons.TipoUsuario.ADMIN):
				return redirect("/panel_admin/")
			return redirect("/")
		errores.append("Credenciales invalidad. Verifica tu email y contraseña.")

	return render(request, "templates-old/views/Auth/login.html", {"errores": errores, "next": next_url})


def render_registro_ciudadano(request):
	localidades = Localidad.objects.all()

	if request.method == "POST":
		if request.POST.get("carga_masiva") == "1":
			resultado = UserService.carga_masiva(request)
			if resultado and resultado.get("creados", 0) > 0:
				messages.success(request, f"Carga masiva completada: {resultado.get('creados', 0)} registros creados.")
			if resultado and resultado.get("errores"):
				primer_error = resultado["errores"][0]
				messages.error(request, f"Carga masiva con errores. Primera fila con error: {primer_error.get('line')}. {primer_error.get('error')}")
			return redirect("registro:ciudadano")

		data = request.POST
		errores = []

		nombres = data.get("nombres", "").strip()
		apellidos = data.get("apellidos", "").strip()
		email = data.get("email", "").strip().lower()
		celular = data.get("celular", "").strip()
		tipo_documento = data.get("tipoDocumento") or cons.TipoDocumento.CC
		numero_documento = data.get("numeroDocumento", "").strip() or f"CIU_{email}"
		ciudad = data.get("ciudad", "Bogota").strip() or "Bogota"
		localidad_id = data.get("localidad")
		fecha_nacimiento = data.get("fechaNacimiento") or None
		password = data.get("password", "")
		password_confirm = data.get("passwordConfirm", "")
		terminos = data.get("terminos")

		if not nombres:
			errores.append("Debe ingresar nombres.")
		if not apellidos:
			errores.append("Debe ingresar apellidos.")
		if not email:
			errores.append("Debe ingresar un email valido.")
		if not celular or not celular.startswith("3") or len(celular) != 10:
			errores.append("El celular debe iniciar en 3 y tener 10 digitos.")
		if not password or not password_confirm:
			errores.append("Se requiere contraseña y confirmacion.")
		if password != password_confirm:
			errores.append("Las contraseñas no coinciden.")
		if len(password) < 8:
			errores.append("La contraseña debe tener al menos 8 caracteres.")
		if not terminos:
			errores.append("Debe aceptar los terminos y condiciones.")
		if Usuario.objects.filter(email=email).exists():
			errores.append("Ya existe un usuario con ese correo electronico.")
		if data.get("numeroDocumento") and Usuario.objects.filter(numero_documento=data.get("numeroDocumento")).exists():
			errores.append("Ya existe un usuario con ese numero de documento.")

		localidad_inst = None
		if localidad_id:
			localidad_inst = Localidad.objects.filter(localidad_id=localidad_id).first()
			if not localidad_inst:
				errores.append("La localidad seleccionada no existe.")

		if errores:
			return render(
				request,
				"templates-old/views/Auth/registro-ciudadano.html",
				{"errores": errores, "localidades": localidades, **data.dict()},
			)

		try:
			with transaction.atomic():
				usuario = Usuario(
					email=email,
					numero_documento=numero_documento,
					celular=celular,
					nombres=nombres,
					apellidos=apellidos,
					tipo_documento=tipo_documento,
					tipo_usuario=cons.TipoUsuario.CIUDADANO,
					ciudad=ciudad,
					localidad=localidad_inst,
					fecha_nacimiento=fecha_nacimiento,
				)
				usuario.set_password(password)
				usuario.save()

			messages.success(request, "Registro exitoso. Ahora puedes iniciar sesion.")
			return redirect("login")
		except (IntegrityError, ValidationError) as e:
			errores.append(f"Error al registrar el ciudadano: {e}")

		return render(
			request,
			"templates-old/views/Auth/registro-ciudadano.html",
			{"errores": errores, "localidades": localidades, **data.dict()},
		)

	return render(
		request,
		"templates-old/views/Auth/registro-ciudadano.html",
		{"localidades": localidades},
	)


def render_registro_eca(request):
	localidades = Localidad.objects.all()

	if request.method == "POST":
		if request.POST.get("carga_masiva") == "1":
			resultado = UserService.carga_masiva(request)
			if resultado and resultado.get("creados", 0) > 0:
				messages.success(request, f"Carga masiva completada: {resultado.get('creados', 0)} registros creados.")
			if resultado and resultado.get("errores"):
				primer_error = resultado["errores"][0]
				messages.error(request, f"Carga masiva con errores. Primera fila con error: {primer_error.get('line')}. {primer_error.get('error')}")
			return redirect("registro:eca")

		data = request.POST
		errores = []

		nombres = data.get("nombres", "").strip()
		apellidos = data.get("apellidos", "").strip()
		email = data.get("email", "").strip().lower()
		tipo_documento = data.get("tipoDocumento") or cons.TipoDocumento.CC
		numero_documento = data.get("numeroDocumento", "").strip() or f"GECA_{email}"
		celular = data.get("celular", "").strip()
		telefono_punto = data.get("telefono_punto", "").strip()
		direccion = data.get("direccion", "").strip()
		ciudad = data.get("ciudad", "Bogota").strip() or "Bogota"
		localidad_id = data.get("localidad")
		latitud = data.get("latitud")
		longitud = data.get("longitud")
		descripcion = data.get("descripcion", "")
		sitio_web = data.get("sitio_web", "").strip()
		logo_url_punto = data.get("logo_url_punto", "").strip()
		foto_url_punto = data.get("foto_url_punto", "").strip()
		horario_atencion = data.get("horario_atencion", "").strip()
		password = data.get("password", "")
		password_confirm = data.get("passwordConfirm", "")
		terminos = data.get("terminos")

		if not nombres:
			errores.append("Debe ingresar el nombre de la institucion.")
		if not apellidos:
			errores.append("Debe ingresar el nombre del contacto.")
		if not email:
			errores.append("Debe ingresar un email valido.")
		if not celular or not celular.startswith("3") or len(celular) != 10:
			errores.append("El celular debe iniciar en 3 y tener 10 digitos.")
		if not direccion:
			errores.append("Debe ingresar la direccion.")
		if not telefono_punto or not telefono_punto.startswith("60") or len(telefono_punto) != 10:
			errores.append("El telefono del punto debe iniciar en 60 y tener 10 digitos.")
		if not latitud or not longitud:
			errores.append("Debe seleccionar ubicacion en el mapa.")
		if not password or not password_confirm:
			errores.append("Se requiere contraseña y confirmacion.")
		if password != password_confirm:
			errores.append("Las contraseñas no coinciden.")
		if len(password) < 8:
			errores.append("La contraseña debe tener al menos 8 caracteres.")
		if not terminos:
			errores.append("Debe aceptar los terminos y condiciones.")
		if Usuario.objects.filter(email=email).exists():
			errores.append("Ya existe un usuario con ese correo electronico.")
		if data.get("numeroDocumento") and Usuario.objects.filter(numero_documento=data.get("numeroDocumento")).exists():
			errores.append("Ya existe un usuario con ese numero de documento.")

		localidad_inst = None
		if localidad_id:
			localidad_inst = Localidad.objects.filter(localidad_id=localidad_id).first()
			if not localidad_inst:
				errores.append("La localidad seleccionada no existe.")

		if errores:
			return render(
				request,
				"templates-old/views/Auth/registro-eca.html",
				{"errores": errores, "localidades": localidades, **data.dict()},
			)

		try:
			with transaction.atomic():
				usuario = Usuario(
					email=email,
					numero_documento=numero_documento,
					celular=celular,
					nombres=nombres,
					apellidos=apellidos,
					tipo_documento=tipo_documento,
					tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
					ciudad=ciudad,
					localidad=localidad_inst,
				)
				usuario.set_password(password)
				usuario.save()

				PuntoECA.objects.create(
					gestor_eca=usuario,
					nombre=nombres,
					descripcion=descripcion,
					telefono_punto=telefono_punto,
					direccion=direccion,
					ciudad=ciudad,
					email=email,
					celular=celular,
					logo_url_punto=logo_url_punto,
					foto_url_punto=foto_url_punto,
					sitio_web=sitio_web,
					horario_atencion=horario_atencion,
					localidad=localidad_inst,
					latitud=float(latitud),
					longitud=float(longitud),
				)

			messages.success(request, "Punto ECA registrado. Ahora puedes iniciar sesion.")
			return redirect("login")
		except (IntegrityError, ValidationError, ValueError) as e:
			errores.append(f"Error al registrar el punto ECA: {e}")

		return render(
			request,
			"templates-old/views/Auth/registro-eca.html",
			{"errores": errores, "localidades": localidades, **data.dict()},
		)

	return render(
		request,
		"templates-old/views/Auth/registro-eca.html",
		{"localidades": localidades},
	)
