from django.shortcuts import redirect
from django.db import transaction
from apps.ecas.models import Localidad
from apps.ecas.models import PuntoECA


class PuntoService:
    @staticmethod
    @transaction.atomic
    def editar_punto(request, id):
        """
        Vista para editar el punto ECA.
        """
        try:
            punto = PuntoECA.objects.get(gestor_eca_id=id)
        except PuntoECA.DoesNotExist:
            return redirect("base:inicio")

        print(f"--- DEBUG --- Claves recibidas: {list(request.POST.keys())}")
        print(
            f"--- DEBUG --- Valor específico: '{request.POST.get('descripcionPunto')}'"
        )

        punto.nombre = request.POST.get("nombrePunto", punto.nombre)
        punto.direccion = request.POST.get("direccionPunto", punto.direccion)
        punto.celular = request.POST.get("celularPunto", punto.celular)
        punto.email = request.POST.get("emailPunto", punto.email)
        punto.telefono_punto = request.POST.get("telefonoPunto", punto.telefono_punto)
        punto.sitio_web = request.POST.get("sitioWebPunto", punto.sitio_web)
        # Convert latitud/longitud: accept empty as None
        lat = request.POST.get("latitud", None)
        punto.latitud = float(lat) if lat not in (None, "") else None
        lon = request.POST.get("longitud", None)
        punto.longitud = float(lon) if lon not in (None, "") else None
        punto.descripcion = request.POST.get("descripcionPunto", punto.descripcion)
        punto.logo_url_punto = request.POST.get("logoUrlPunto", punto.logo_url_punto)
        punto.horario_atencion = request.POST.get(
            "horarioAtencionPunto", punto.horario_atencion
        )

        localidad_id = request.POST.get("localidadPunto")
        if localidad_id != str(punto.localidad.localidad_id if punto.localidad else ""):
            try:
                punto.localidad = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                pass  # Mantener la localidad actual si no existe la nueva

        try:
            punto.save()
        except Exception as e:
            # Print and raise to make the error visible during debug
            print(f"--- ERROR AL GUARDAR PUNTO ECA: {e}")
            raise

        return punto
