from django.shortcuts import redirect
from django.db import transaction
from apps.ecas.models import Localidad
from apps.users.models import Usuario


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
        # Manejo robusto para fecha: si viene vacía (""), setea None
        fecha_nacimiento = request.POST.get("fechaNacimiento")
        if fecha_nacimiento:
            usuario.fecha_nacimiento = fecha_nacimiento
        else:
            usuario.fecha_nacimiento = None

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
        except Exception as ex:
            print(f"[ERROR] al guardar usuario: {ex}")

        return usuario
