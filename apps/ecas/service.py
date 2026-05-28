from django.shortcuts import redirect
from django.db import transaction
from apps.ecas.models import Localidad
from apps.ecas.models import PuntoECA


class PuntoService:
    """
    Servicio de lógica de negocio para operaciones sobre puntos ECA.
    Abstrae acciones comunes sobre PuntoECA fuera de las vistas.
    """

    @staticmethod
    @transaction.atomic
    def editar_punto(request, id):
        """
        Edita el punto ECA asociado al id recibido (gestor_eca_id), usando los datos del request.POST.
        - Valida existencia del punto y redirige si no se encuentra.
        - Permite actualización parcial de cada campo: si el dato no viene, deja el valor anterior.
        - Convierte correctamente tipos (ej: lat/long a float o None).
        - Permite actualizar la localidad solo si cambió el id.
        - Guarda de forma atómica y levanta excepción para debug si algo falla.

        Args:
            request (HttpRequest): Request HTTP con datos POST del formulario.
            id (str|int): Identificador del gestor_eca asociado.

        Returns:
            PuntoECA instanciado (modificado), o redirect si el punto no existe.
        """
        try:
            punto = PuntoECA.objects.get(gestor_eca_id=id)
        except PuntoECA.DoesNotExist:
            return Helper.redireccionar_con_error(
                "base:inicio", "Punto ECA no encontrado."
            )

        # Actualización campo a campo (si el dato no viene, deja el valor actual)
        punto.nombre = request.POST.get("nombrePunto", punto.nombre)
        punto.direccion = request.POST.get("direccionPunto", punto.direccion)
        punto.celular = request.POST.get("celularPunto", punto.celular)
        punto.email = request.POST.get("emailPunto", punto.email)
        punto.telefono_punto = request.POST.get("telefonoPunto", punto.telefono_punto)
        punto.sitio_web = request.POST.get("sitioWebPunto", punto.sitio_web)

        # Latitud y longitud: convierte a float/None sólo si el dato viene y tiene valor
        lat = request.POST.get("latitud", None)
        punto.latitud = float(lat) if lat not in (None, "") else None
        lon = request.POST.get("longitud", None)
        punto.longitud = float(lon) if lon not in (None, "") else None
        punto.descripcion = request.POST.get("descripcionPunto", punto.descripcion)
        punto.logo_url_punto = request.POST.get("logoUrlPunto", punto.logo_url_punto)
        punto.horario_atencion = request.POST.get(
            "horarioAtencionPunto", punto.horario_atencion
        )

        # Si la localidad efectivamente cambió, la busca y actualiza. No la borra si no existe el id
        localidad_id = request.POST.get("localidadPunto")
        if localidad_id != str(punto.localidad.localidad_id if punto.localidad else ""):
            try:
                punto.localidad = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                pass  # Deja la localidad previa sin cambios si el id no existe

        try:
            punto.save()
        except Exception as e:
            # Loguea error y levanta para debug
            print(f"--- ERROR AL GUARDAR PUNTO ECA: {e}")
            raise

        return punto


class Helper:
    """
    Clase auxiliar para manejar redireccionamientos y organización de errores de forma centralizada.
    """

    @staticmethod
    def redireccionar_con_error(url_name, mensaje):
        from django.contrib import messages

        def wrapped_redirect(request):
            messages.error(request, mensaje)
            return redirect(url_name)

        return wrapped_redirect
