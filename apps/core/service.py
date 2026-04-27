from django.shortcuts import redirect
from django.db import transaction
from apps.ecas.models import Localidad
from apps.users.models import Usuario


class UserService:
    @staticmethod
    @transaction.atomic
    def editar_perfil(request, id):
        """
        Edita el perfil del usuario identificado por 'id' según los datos provistos en un request POST.
        Pensada para editores de perfil de tipo gestor ECA.
        - Actualiza campos personales, de contacto, documento y localidad.
        - Si el usuario no existe, redirige al inicio.
        - Utiliza transacciones atómicas para evitar condiciones de carrera durante el guardado.
        - Devuelve un diccionario con el usuario actualizado y posibles errores de validación.
        Args:
            request: HttpRequest de Django con datos en request.POST
            id: ID del usuario a editar
        Returns:
            dict | HttpResponseRedirect: {'usuario': usuario, 'errores': errores} o redirección si no existe el usuario.
        """

        # 1. Buscar usuario y hacer lock de fila para evitar condiciones de carrera
        try:
            usuario = Usuario.objects.select_for_update().get(id=id)
        except Usuario.DoesNotExist:
            # Si el usuario no existe, volvemos al inicio
            return redirect("base:inicio")

        # 2. Actualizar datos básicos (nombre, apellido, email, teléfono, biografía)
        usuario.nombres = request.POST.get("nombre", usuario.nombres)
        usuario.apellidos = request.POST.get("apellido", usuario.apellidos)
        usuario.email = request.POST.get("email", usuario.email)
        usuario.celular = request.POST.get("telefono", usuario.celular)
        usuario.biografia = request.POST.get("biografia", usuario.biografia)

        # 3. Fecha de nacimiento: setea None si viene vacía
        fecha_nacimiento = request.POST.get("fechaNacimiento")
        usuario.fecha_nacimiento = fecha_nacimiento if fecha_nacimiento else None

        # 4. Localidad: actualiza sólo si la id cambió y la nueva localidad existe
        localidad_id = request.POST.get("localidad")
        id_actual = str(usuario.localidad.localidad_id) if usuario.localidad else ""
        if localidad_id != id_actual:
            try:
                usuario.localidad = Localidad.objects.get(localidad_id=localidad_id)
            except Localidad.DoesNotExist:
                # Si no se encuentra la nueva localidad, mantiene la actual
                pass

        # 5. Documento
        usuario.tipo_documento = request.POST.get("tipo_documento", usuario.tipo_documento)
        usuario.numero_documento = request.POST.get("numero_documento", usuario.numero_documento)

        # 6. Intentar guardar y capturar errores de validación
        from django.core.exceptions import ValidationError

        errores = None
        try:
            usuario.save()
        except ValidationError as ex:
            errores = (
                ex.message_dict if hasattr(ex, "message_dict") else {"__all__": [str(ex)]}
            )
        except Exception as ex:
            print(f"[ERROR] al guardar usuario: {ex}")
            errores = {"__all__": [str(ex)]}

        # Devuelve siempre el usuario (modificado o no) y cualquier error de validación
        return {"usuario": usuario, "errores": errores}
