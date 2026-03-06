from django.shortcuts import redirect
from django.db import transaction
from apps.ecas.models import Localidad
from apps.ecas.models import PuntoECA
from apps.users.models import Usuario


class PuntoService:
    @staticmethod
    @transaction.atomic
    def editar_punto(request, id):
        """
        Vista para editar el punto ECA.
        """
        print("--- DEBUG: DATOS RECIBIDOS ---")
        print(request.POST)
        print(f"Localidad enviada: {request.POST.get('localidad')}")
        print("------------------------------")
        try:
            punto = PuntoECA.objects.get(gestor_eca_id=id)
        except PuntoECA.DoesNotExist:
            return redirect("base:inicio")

        punto.nombre = request.POST.get("nombrePunto", punto.nombre)
        punto.direccion = request.POST.get("direccionPunto", punto.direccion)
        punto.celular = request.POST.get("celularPunto", punto.celular)
        punto.email = request.POST.get("emailPunto", punto.email)
        punto.telefono_punto = request.POST.get("telefonoPunto", punto.telefono_punto)
        punto.sitio_web = request.POST.get("sitioWebPunto", punto.sitio_web)
        punto.latitud = request.POST.get("latitud", punto.latitud)
        punto.longitud = request.POST.get("longitud", punto.longitud)
        punto.descripcion = request.POST.get("descripcionPunto", punto.descripcion)
        punto.logo_url_punto = request.POST.get("logoUrlPunto", punto.logo_url_punto)

        localidad_id = request.POST.get("localidadPunto")
        if localidad_id != str(punto.localidad.localidad_id if punto.localidad else ""):
            try:
                punto.localidad = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                pass  # Mantener la localidad actual si no existe la nueva

        try:
            punto.save()
        except Exception:
            pass

        return punto
