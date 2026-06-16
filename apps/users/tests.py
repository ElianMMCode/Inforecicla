import secrets
import string
import unittest
import uuid
from datetime import date
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sessions.models import Session
from django.test import TestCase

from apps.ecas.models import Localidad
from apps.users.utils import crear_token_validacion
from config import constants as cons

Usuario = get_user_model()

# ── Constantes de URL ─────────────────────────────────────────────────────────
_LOGIN = "/login/"
_LOGOUT = "/logout/"
_RECOVER = "/recuperar-contrasena/"
_PERFIL = "/perfil/"
_PERFIL_SKIP_MODAL = "/perfil/?skip_modal=1"
_PANEL_ADMIN = "/panel_admin/"
_PUNTO_ECA = "/punto-eca/"

# ── Mensaje de error canónico del módulo de autenticación ─────────────────────
_CRED_INVALIDAS = "Credenciales inválidas. Verifica tu email y contraseña."


# ── Generador de contraseñas aleatorias para tests ────────────────────────────

def _generar_password():
    """Genera una contraseña aleatoria que cumple los requisitos de complejidad."""
    simbolos = "@$!%*?&"
    alphabet = string.ascii_letters + string.digits + simbolos
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(16))
        if (
            any(c.isupper() for c in pwd)
            and any(c.islower() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in simbolos for c in pwd)
        ):
            return pwd


def _generar_password_corta():
    """Genera un input aleatorio de 3 caracteres para tests de validación de longitud.

    NO es una credencial real: es un fixture que el validador debe rechazar
    por no cumplir el mínimo de 8 caracteres.
    """
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(3))


_PASSWORD_VALIDA = _generar_password()
_PASSWORD_NUEVA = _generar_password()
_PWD_INCORRECTO = _generar_password()   # distinto a _PASSWORD_VALIDA, para tests de fallo
_PWD_CORTO = _generar_password_corta()  # demasiado corto para superar validación de longitud
_PWD_VACIO = ""                         # campo vacío para tests de campo obligatorio


# ── Helper de creación de usuarios ────────────────────────────────────────────

def _crear_usuario(
    email,
    password=None,
    numero_documento="123456",
    nombres="Test",
    apellidos="Usuario",
    tipo_usuario=cons.TipoUsuario.CIUDADANO,
    is_staff=False,
    is_superuser=False,
    is_active=True,
):
    """
    Crea un usuario de prueba con valores por defecto seguros.
    numero_documento debe ser único por cada llamada dentro del mismo test.
    """
    return Usuario.objects.create_user(
        email=email,
        numero_documento=numero_documento,
        password=password if password is not None else _PASSWORD_VALIDA,
        nombres=nombres,
        apellidos=apellidos,
        tipo_usuario=tipo_usuario,
        is_staff=is_staff,
        is_superuser=is_superuser,
        is_active=is_active,
    )


# ═════════════════════════════════════════════════════════════════════════════
# CU-00.1 — Validar Credenciales (Email / Password)
# Módulo: apps/users/views.py → render_login
# ═════════════════════════════════════════════════════════════════════════════

class ValidarCredencialesTests(TestCase):
    """CU-00.1: Prueba el comportamiento de render_login ante distintas
    combinaciones de credenciales."""

    def setUp(self):
        self.usuario = _crear_usuario(email="usuario@test.com")

    # ------------------------------------------------------------------
    def test_tc_cu001_01_login_exitoso_redirecciona(self):
        """TC-CU00.1-01: Credenciales correctas → redirección al perfil del rol."""
        response = self.client.post(
            _LOGIN,
            {"email": "usuario@test.com", "password": _PASSWORD_VALIDA},
        )
        self.assertRedirects(response, _PERFIL_SKIP_MODAL, fetch_redirect_response=False)

    def test_tc_cu001_02_fallo_email_inexistente(self):
        """TC-CU00.1-02: Email no registrado → mensaje de error genérico."""
        response = self.client.post(
            _LOGIN,
            {"email": "noexiste@test.com", "password": _PASSWORD_VALIDA},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(_CRED_INVALIDAS, response.context["errores"])

    def test_tc_cu001_03_fallo_password_incorrecto(self):
        """TC-CU00.1-03: Password incorrecto → mensaje de error genérico."""
        response = self.client.post(
            _LOGIN,
            {"email": "usuario@test.com", "password": _PWD_INCORRECTO},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(_CRED_INVALIDAS, response.context["errores"])

    def test_tc_cu001_04_email_en_mayusculas_es_normalizado(self):
        """TC-CU00.1-04: Email en mayúsculas es convertido a minúsculas antes
        de autenticar; la autenticación debe ser exitosa."""
        response = self.client.post(
            _LOGIN,
            {"email": "USUARIO@TEST.COM", "password": _PASSWORD_VALIDA},
        )
        self.assertRedirects(response, _PERFIL_SKIP_MODAL, fetch_redirect_response=False)

    def test_tc_cu001_05_login_incompleto_redirige_sin_parametro_forzado(self):
        """TC-CU00.1-05: Un ciudadano con perfil incompleto redirige a /perfil/
        sin `completar=1`, para no reabrir el modal al recargar."""
        usuario = _crear_usuario(
            email="incompleto@test.com",
            numero_documento="7654321",
        )
        usuario.numero_documento = None
        usuario.tipo_documento = ""
        usuario.fecha_nacimiento = None
        usuario.localidad = None
        usuario.save(update_fields=["numero_documento", "tipo_documento", "fecha_nacimiento", "localidad"])

        response = self.client.post(
            _LOGIN,
            {"email": "incompleto@test.com", "password": _PASSWORD_VALIDA},
        )

        self.assertRedirects(response, _PERFIL_SKIP_MODAL, fetch_redirect_response=False)

    def test_tc_cu001_05_email_con_espacios_extra_es_saneado(self):
        """TC-CU00.1-05: Espacios al inicio/final del email son eliminados antes
        de autenticar; la autenticación debe ser exitosa."""
        response = self.client.post(
            _LOGIN,
            {"email": "  usuario@test.com  ", "password": _PASSWORD_VALIDA},
        )
        self.assertRedirects(response, _PERFIL_SKIP_MODAL, fetch_redirect_response=False)

    def test_tc_cu001_06_login_muestra_modal_de_validacion_de_cuenta(self):
        """TC-CU00.1-06: El login expone el modal para ingresar el código de activación."""
        response = self.client.get(_LOGIN)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="activationModal"')
        self.assertContains(response, 'name="token"')

    def test_tc_cu001_06b_login_anonimo_autenticado_redirige_a_su_destino(self):
        """TC-CU00.1-06B: Un usuario autenticado no debe ver el login y debe ir a su dashboard."""
        usuario = _crear_usuario(
            email="redirigido@test.com",
            numero_documento="900009",
            tipo_usuario=cons.TipoUsuario.ADMIN,
            is_staff=True,
        )
        self.client.force_login(usuario)

        response = self.client.get(_LOGIN)

        self.assertRedirects(response, _PANEL_ADMIN, fetch_redirect_response=False)

    def test_tc_cu001_07_codigo_de_validacion_activa_la_cuenta(self):
        """TC-CU00.1-07: action=activar valida el token y activa el usuario."""
        usuario = _crear_usuario(
            email="activar@test.com",
            numero_documento="5555555",
            is_active=False,
        )
        token_obj = crear_token_validacion(
            email="activar@test.com",
            tipo="verificacion",
            usuario=usuario,
            desactivar_previos=False,
        )

        response = self.client.get(
            _LOGIN,
            {
                "action": "activar",
                "email": "activar@test.com",
                "token": token_obj.token,
            },
        )
        # After activation, the user should be logged in and redirected to their post-login page
        self.assertRedirects(response, _PERFIL_SKIP_MODAL, fetch_redirect_response=False)
        usuario.refresh_from_db()
        token_obj.refresh_from_db()
        self.assertTrue(usuario.is_active)
        self.assertFalse(token_obj.es_activo)
        self.assertIsNotNone(token_obj.fecha_validacion)
        # Ensure session contains authenticated user
        session = self.client.session
        from django.contrib.auth import SESSION_KEY
        self.assertIn(SESSION_KEY, session)

    @patch("apps.users.views.enviar_email_verificacion", return_value=True)
    def test_tc_cu001_08_login_inactivo_envia_un_solo_correo_de_activacion(self, mock_enviar_email):
        """TC-CU00.1-08: Un login con cuenta inactiva debe reenviar un único correo
        de activación y mostrar un solo mensaje informativo."""
        _crear_usuario(
            email="inactivo@test.com",
            numero_documento="5555556",
            is_active=False,
        )

        response = self.client.post(
            _LOGIN,
            {"email": "inactivo@test.com", "password": _PASSWORD_VALIDA},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_enviar_email.called)
        self.assertEqual(mock_enviar_email.call_count, 1)
        self.assertTrue(response.context["show_activation_resend"])

    @patch("apps.users.views.enviar_email_verificacion", return_value=True)
    def test_tc_cu001_09_reenviar_activacion_envia_un_solo_correo(self, mock_enviar_email):
        """TC-CU00.1-09: Reenviar activación desde el login debe enviar un único correo
        y no duplicar la notificación informativa."""
        _crear_usuario(
            email="reenviar@test.com",
            numero_documento="5555557",
            is_active=False,
        )

        response = self.client.post(
            _LOGIN,
            {"action": "reenviar", "email": "reenviar@test.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_enviar_email.call_count, 1)
        self.assertTrue(any("Reenviamos el enlace de activación a tu correo." in str(m) for m in response.context["messages"]))


# ═════════════════════════════════════════════════════════════════════════════
# CU-00.2 — Determinar Rol y Cargar Permisos
# Módulo: apps/users/views.py → render_login, apps/users/decorators.py
# ═════════════════════════════════════════════════════════════════════════════

class RolRedireccionTests(TestCase):
    """CU-00.2: Verifica que render_login redirige a la URL correcta según
    tipo_usuario/flags, y que ciudadano_required protege las vistas."""

    def test_tc_cu002_01_ciudadano_redirige_a_perfil(self):
        """TC-CU00.2-01: tipo_usuario=CIU es redirigido a /perfil/ tras login."""
        _crear_usuario(
            email="ciudadano@test.com",
            numero_documento="100001",
            tipo_usuario=cons.TipoUsuario.CIUDADANO,
        )
        response = self.client.post(
            _LOGIN,
            {"email": "ciudadano@test.com", "password": _PASSWORD_VALIDA},
        )
        self.assertRedirects(response, _PERFIL_SKIP_MODAL, fetch_redirect_response=False)

    def test_tc_cu002_02_gestor_eca_redirige_a_punto_eca(self):
        """TC-CU00.2-02: tipo_usuario=GECA es redirigido a /punto-eca/ tras login."""
        _crear_usuario(
            email="gestor@test.com",
            numero_documento="200002",
            tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
        )
        response = self.client.post(
            _LOGIN,
            {"email": "gestor@test.com", "password": _PASSWORD_VALIDA},
        )
        self.assertRedirects(response, _PUNTO_ECA, fetch_redirect_response=False)

    def test_tc_cu002_03_admin_tipo_adm_redirige_a_panel_admin(self):
        """TC-CU00.2-03a: tipo_usuario=ADM es redirigido a /panel_admin/ tras login."""
        _crear_usuario(
            email="admin@test.com",
            numero_documento="300003",
            tipo_usuario=cons.TipoUsuario.ADMIN,
        )
        response = self.client.post(
            _LOGIN,
            {"email": "admin@test.com", "password": _PASSWORD_VALIDA},
        )
        self.assertRedirects(response, _PANEL_ADMIN, fetch_redirect_response=False)

    def test_tc_cu002_03_is_staff_redirige_a_panel_admin(self):
        """TC-CU00.2-03b: is_staff=True es redirigido a /panel_admin/ tras login,
        independientemente del tipo_usuario."""
        _crear_usuario(
            email="staff@test.com",
            numero_documento="400004",
            tipo_usuario=cons.TipoUsuario.CIUDADANO,
            is_staff=True,
        )
        response = self.client.post(
            _LOGIN,
            {"email": "staff@test.com", "password": _PASSWORD_VALIDA},
        )
        self.assertRedirects(response, _PANEL_ADMIN, fetch_redirect_response=False)

    def test_tc_cu002_04_gestor_eca_bloqueado_en_perfil_ciudadano(self):
        """TC-CU00.2-04a: ciudadano_required redirige al Gestor ECA a /punto-eca/."""
        _crear_usuario(
            email="gestor2@test.com",
            numero_documento="500005",
            tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
        )
        self.client.login(username="gestor2@test.com", password=_PASSWORD_VALIDA)
        response = self.client.get(_PERFIL)
        self.assertRedirects(response, _PUNTO_ECA, fetch_redirect_response=False)

    def test_tc_cu002_04_admin_bloqueado_en_perfil_ciudadano(self):
        """TC-CU00.2-04b: ciudadano_required redirige al Admin a /panel_admin/."""
        _crear_usuario(
            email="admin2@test.com",
            numero_documento="600006",
            tipo_usuario=cons.TipoUsuario.ADMIN,
        )
        self.client.login(username="admin2@test.com", password=_PASSWORD_VALIDA)
        response = self.client.get(_PERFIL)
        self.assertRedirects(response, _PANEL_ADMIN, fetch_redirect_response=False)

    def test_tc_cu002_04_anonimo_redirigido_a_login_por_ciudadano_required(self):
        """TC-CU00.2-04c: ciudadano_required redirige a /login/?next= cuando el
        usuario no está autenticado."""
        response = self.client.get(_PERFIL)
        self.assertRedirects(
            response,
            f"/login/?next={_PERFIL}",
            fetch_redirect_response=False,
        )


# ═════════════════════════════════════════════════════════════════════════════
# CU-00.3 — Gestionar Sesión de Usuario
# Módulo: apps/users/views.py → render_login, config/urls.py → LogoutView
# ═════════════════════════════════════════════════════════════════════════════

class GestionSesionTests(TestCase):
    """CU-00.3: Prueba la creación, persistencia y destrucción de sesiones Django."""

    def setUp(self):
        self.usuario = _crear_usuario(
            email="sesion@test.com",
            numero_documento="700007",
        )

    def test_tc_cu003_01_login_exitoso_crea_sesion(self):
        """TC-CU00.3-01: Login exitoso establece SESSION_KEY en la sesión Django."""
        self.client.post(
            _LOGIN,
            {"email": "sesion@test.com", "password": _PASSWORD_VALIDA},
        )
        self.assertIn(SESSION_KEY, self.client.session)

    def test_tc_cu003_02_sesion_persiste_entre_peticiones(self):
        """TC-CU00.3-02: El SESSION_KEY permanece igual tras navegar a vistas protegidas."""
        self.client.login(username="sesion@test.com", password=_PASSWORD_VALIDA)
        session_key_inicial = self.client.session[SESSION_KEY]

        self.client.get(_PERFIL)

        self.assertIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.session[SESSION_KEY], session_key_inicial)

    def test_tc_cu003_03_logout_destruye_sesion_y_redirige_a_login(self):
        """TC-CU00.3-03: Logout elimina SESSION_KEY y redirige a /login/."""
        self.client.login(username="sesion@test.com", password=_PASSWORD_VALIDA)
        self.assertIn(SESSION_KEY, self.client.session)

        response = self.client.post(_LOGOUT)

        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertRedirects(response, _LOGIN, fetch_redirect_response=False)

    def test_tc_cu003_04_sesion_expirada_redirige_a_login(self):
        """TC-CU00.3-04: Sin sesión válida en el servidor, la vista protegida
        redirige a /login/?next=<url>. Se simula la expiración eliminando todos
        los registros de sesión de la base de datos."""
        self.client.login(username="sesion@test.com", password=_PASSWORD_VALIDA)
        self.assertIn(SESSION_KEY, self.client.session)

        Session.objects.all().delete()

        response = self.client.get(_PERFIL)
        self.assertRedirects(
            response,
            f"/login/?next={_PERFIL}",
            fetch_redirect_response=False,
        )


# ═════════════════════════════════════════════════════════════════════════════
# EXT-41 — Notificar Error: Credenciales Inválidas
# Módulo: apps/users/views.py → render_login
# ═════════════════════════════════════════════════════════════════════════════

class NotificacionErrorCredencialesTests(TestCase):
    """EXT-41: Verifica que los mensajes de error son seguros y no revelan
    información que permita enumerar usuarios del sistema."""

    def setUp(self):
        self.usuario = _crear_usuario(
            email="existente@test.com",
            numero_documento="800008",
        )

    def test_tc_ext41_01_error_por_email_no_registrado(self):
        """TC-EXT41-01: Email no registrado retorna el mensaje canónico de error."""
        response = self.client.post(
            _LOGIN,
            {"email": "noexiste@test.com", "password": _PWD_INCORRECTO},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(_CRED_INVALIDAS, response.context["errores"])

    def test_tc_ext41_02_error_por_password_incorrecto(self):
        """TC-EXT41-02: Password incorrecto retorna el mensaje canónico de error."""
        response = self.client.post(
            _LOGIN,
            {"email": "existente@test.com", "password": _PWD_INCORRECTO},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(_CRED_INVALIDAS, response.context["errores"])

    def test_tc_ext41_03_mensajes_identicos_previenen_enumeracion_de_usuarios(self):
        """TC-EXT41-03: El mensaje de error es idéntico para email inexistente
        y para password incorrecto, evitando la enumeración de usuarios."""
        resp_email_inexistente = self.client.post(
            _LOGIN,
            {"email": "fantasma@test.com", "password": _PWD_INCORRECTO},
        )
        resp_password_incorrecto = self.client.post(
            _LOGIN,
            {"email": "existente@test.com", "password": _PWD_INCORRECTO},
        )

        self.assertEqual(
            resp_email_inexistente.context["errores"],
            resp_password_incorrecto.context["errores"],
        )

    def test_tc_ext41_04_ambos_campos_vacios_no_autentican(self):
        """TC-EXT41-04a: Enviar email y password vacíos no autentica al usuario."""
        response = self.client.post(_LOGIN, {"email": "", "password": _PWD_VACIO})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertGreater(len(response.context["errores"]), 0)

    def test_tc_ext41_04_password_vacio_no_autentica(self):
        """TC-EXT41-04b: Email válido con password vacío no autentica al usuario.
        Django rechaza autenticaciones con contraseñas vacías por diseño."""
        response = self.client.post(
            _LOGIN,
            {"email": "existente@test.com", "password": _PWD_VACIO},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertGreater(len(response.context["errores"]), 0)


# ═════════════════════════════════════════════════════════════════════════════
# EXT-42 — Bloquear Cuenta: Exceso de Intentos Fallidos
# Estado: PENDIENTE DE IMPLEMENTACIÓN
# ═════════════════════════════════════════════════════════════════════════════

class BloqueoIntentosFallidosTests(TestCase):
    """EXT-42: Valida el mecanismo de bloqueo de cuenta por intentos fallidos.

    NOTA: Esta funcionalidad NO está implementada en el código actual.
    Según el documento de casos de prueba (test_cases_security_access.md),
    se requiere añadir:
      - Un campo failed_login_attempts / lockout_until en el modelo Usuario,
        o una tabla RegistroIntentos auxiliar.
      - Lógica de bloqueo en render_login (apps/users/views.py).
    Los tests se mantienen con @skip para ser habilitados cuando se implemente.
    """

    def setUp(self):
        self.usuario = _crear_usuario(
            email="bloqueo@test.com",
            numero_documento="900009",
        )

    @unittest.skip(
        "PENDIENTE — EXT-42: Mecanismo de bloqueo de cuenta no implementado. "
        "Se requiere lógica de contador en render_login y campo en el modelo."
    )
    def test_tc_ext42_01_bloqueo_tras_cinco_intentos_fallidos(self):
        """TC-EXT42-01: Cuenta bloqueada tras 5 intentos fallidos; el 6º intento
        con credenciales correctas debe ser rechazado."""
        for _ in range(5):
            self.client.post(
                _LOGIN,
                {"email": "bloqueo@test.com", "password": _PWD_INCORRECTO},
            )

        response = self.client.post(
            _LOGIN,
            {"email": "bloqueo@test.com", "password": _PASSWORD_VALIDA},
        )

        self.assertFalse(response.wsgi_request.user.is_authenticated)

    @unittest.skip(
        "PENDIENTE — EXT-42: Contador de intentos fallidos no implementado."
    )
    def test_tc_ext42_02_login_exitoso_resetea_contador(self):
        """TC-EXT42-02: Un login exitoso resetea el contador de intentos fallidos a 0."""
        for _ in range(2):
            self.client.post(
                _LOGIN,
                {"email": "bloqueo@test.com", "password": _PWD_INCORRECTO},
            )

        self.client.post(
            _LOGIN,
            {"email": "bloqueo@test.com", "password": _PASSWORD_VALIDA},
        )

        self.usuario.refresh_from_db()
        self.assertEqual(getattr(self.usuario, "failed_login_attempts", 0), 0)

    @unittest.skip(
        "PENDIENTE — EXT-42: Desbloqueo automático por tiempo no implementado. "
        "Se requiere campo lockout_until en el modelo o TTL en caché."
    )
    def test_tc_ext42_03_desbloqueo_automatico_tras_timeout(self):
        """TC-EXT42-03: La cuenta se desbloquea automáticamente tras el período
        de espera configurado y acepta credenciales correctas."""
        pass

    @unittest.skip(
        "PENDIENTE — EXT-42: Mensaje de cuenta bloqueada no implementado."
    )
    def test_tc_ext42_04_mensaje_informativo_durante_bloqueo(self):
        """TC-EXT42-04: Intentar login con cuenta bloqueada muestra un mensaje
        informativo (distinto del mensaje de credenciales inválidas)."""
        pass


# ═════════════════════════════════════════════════════════════════════════════
# EXT-43 — Recuperar Contraseña
# Módulo: apps/users/views.py → recuperar_contrasena
# ═════════════════════════════════════════════════════════════════════════════

class RecuperarContrasenaTests(TestCase):
    """EXT-43: Prueba el flujo completo de recuperación de contraseña en dos pasos:
    buscar el email (action=buscar) y restablecer la contraseña (action=reset)."""

    def setUp(self):
        self.usuario = _crear_usuario(
            email="usuario@test.com",
            numero_documento="111111",
        )

    def test_tc_ext43_01_buscar_email_existente_guarda_recovery_id_en_sesion(self):
        """TC-EXT43-01: action=buscar con email registrado almacena
        recovery_user_id en la sesión Django."""
        self.client.post(
            _RECOVER,
            {"action": "buscar", "email": "usuario@test.com"},
        )

        self.assertEqual(
            self.client.session["recovery_user_id"],
            str(self.usuario.pk),
        )

    def test_tc_ext43_02_buscar_email_inexistente_muestra_error(self):
        """TC-EXT43-02: action=buscar con email no registrado retorna mensaje de
        error y no establece recovery_user_id en sesión."""
        response = self.client.post(
            _RECOVER,
            {"action": "buscar", "email": "noexiste@test.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "No existe una cuenta registrada con ese correo.",
            response.context["errores"],
        )
        self.assertNotIn("recovery_user_id", self.client.session)


# ═════════════════════════════════════════════════════════════════════════════
# CU-00.4 — Registro Ciudadano
# Módulo: apps/users/views.py → render_registro_ciudadano
# ═════════════════════════════════════════════════════════════════════════════

class RegistroCiudadanoTests(TestCase):
    """CU-00.4: Verifica que el registro ciudadano funciona con el alta mínima
    y que el documento sintético no excede el límite del modelo."""

    @patch("apps.users.views.enviar_email_verificacion", return_value=True)
    def test_tc_cu004_01_registro_minimo_crea_usuario_sin_numero_documento_obligatorio(self, mock_enviar_email):
        response = self.client.post(
            "/registro/ciudadano/",
            {
                "nombres": "Ana",
                "apellidos": "Pérez",
                "email": "ana.registro.largo@test.com",
                "celular": "3001234567",
                "password": _PASSWORD_VALIDA,
                "passwordConfirm": _PASSWORD_VALIDA,
                "terminos": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        usuario = Usuario.objects.get(email="ana.registro.largo@test.com")
        self.assertIsNone(usuario.numero_documento)
        self.assertTrue(mock_enviar_email.called)

    def test_tc_cu004_01b_ciudadano_logueado_redirige_a_perfil(self):
        usuario = _crear_usuario(email="logueado.ciudadano@test.com")
        self.client.force_login(usuario)

        response = self.client.get("/registro/ciudadano/")

        self.assertRedirects(response, _PERFIL_SKIP_MODAL, fetch_redirect_response=False)

    def test_tc_cu004_02_manager_crea_usuario_sin_numero_documento_explicito(self):
        usuario = Usuario.objects.create_user(
            email="sin.documento@test.com",
            password=_PASSWORD_VALIDA,
            nombres="Luis",
            apellidos="Gómez",
        )

        self.assertIsNone(usuario.numero_documento)

    def test_tc_cu004_03_perfil_ciudadano_envia_pendientes_al_modal(self):
        usuario = Usuario.objects.create_user(
            email="pendientes@test.com",
            password=_PASSWORD_VALIDA,
            nombres="María",
            apellidos="López",
            numero_documento=None,
            tipo_documento="",
            fecha_nacimiento=None,
            localidad=None,
        )

        self.client.force_login(usuario)
        response = self.client.get(_PERFIL)

        self.assertEqual(response.status_code, 200)
        self.assertIn("perfil_pendientes", response.context)
        self.assertTrue(response.context["perfil_pendientes"]["numero_documento"])
        self.assertTrue(response.context["perfil_pendientes"]["tipo_documento"])
        self.assertTrue(response.context["perfil_pendientes"]["localidad"])
        self.assertTrue(response.context["perfil_pendientes"]["fecha_nacimiento"])

    def test_tc_cu004_04_actualizacion_parcial_no_borra_datos_existentes(self):
        localidad = Localidad.objects.create(localidad_id=uuid.uuid4(), nombre="Centro")
        usuario = Usuario.objects.create_user(
            email="parcial@test.com",
            password=_PASSWORD_VALIDA,
            nombres="Carlos",
            apellidos="Rojas",
            numero_documento=None,
            tipo_documento="",
            fecha_nacimiento=None,
            localidad=None,
        )

        self.client.force_login(usuario)

        response = self.client.post(
            "/perfil/actualizar/",
            {
                "localidad": str(localidad.localidad_id),
            },
            follow=True,
        )

        usuario.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(usuario.numero_documento)
        self.assertEqual(usuario.tipo_documento, "")
        self.assertIsNone(usuario.fecha_nacimiento)
        self.assertEqual(usuario.localidad_id, localidad.localidad_id)
        self.assertFalse(response.context["perfil_pendientes"]["localidad"])

        mensajes = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("Se guardaron algunos datos de tu perfil.", mensajes)

    def test_tc_cu004_05_actualizacion_total_muestra_perfil_completado(self):
        localidad = Localidad.objects.create(localidad_id=uuid.uuid4(), nombre="Norte")
        usuario = Usuario.objects.create_user(
            email="completo@test.com",
            password=_PASSWORD_VALIDA,
            nombres="Laura",
            apellidos="Torres",
            numero_documento=None,
            tipo_documento="",
            fecha_nacimiento=None,
            localidad=None,
        )

        self.client.force_login(usuario)

        response = self.client.post(
            "/perfil/actualizar/",
            {
                "tipoDocumento": "CC",
                "numeroDocumento": "987654321",
                "localidad": str(localidad.localidad_id),
                "fechaNacimiento": "1995-05-10",
            },
            follow=True,
        )

        usuario.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(usuario.numero_documento, "987654321")
        self.assertEqual(usuario.tipo_documento, "CC")
        self.assertEqual(usuario.localidad_id, localidad.localidad_id)
        self.assertEqual(usuario.fecha_nacimiento.isoformat(), "1995-05-10")
        self.assertFalse(response.context["perfil_pendientes"]["numero_documento"])
        self.assertFalse(response.context["perfil_pendientes"]["tipo_documento"])
        self.assertFalse(response.context["perfil_pendientes"]["localidad"])
        self.assertFalse(response.context["perfil_pendientes"]["fecha_nacimiento"])

        mensajes = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("¡Perfil completado correctamente!", mensajes)

    def test_tc_cu004_06_completar_perfil_vuelve_a_su_pagina_y_muestra_swal(self):
        localidad = Localidad.objects.create(localidad_id=uuid.uuid4(), nombre="Sur")
        usuario = Usuario.objects.create_user(
            email="retorno@test.com",
            password=_PASSWORD_VALIDA,
            nombres="Pedro",
            apellidos="Vega",
            numero_documento=None,
            tipo_documento="",
            fecha_nacimiento=None,
            localidad=None,
        )

        self.client.force_login(usuario)

        response = self.client.post(
            "/perfil/actualizar/",
            {
                "return_to": "/perfil/completar/",
                "numeroDocumento": "123456789",
                "tipoDocumento": "CC",
                "localidad": str(localidad.localidad_id),
                "fechaNacimiento": "1992-07-15",
            },
            follow=True,
        )

        self.assertEqual(response.redirect_chain[0][0], "/perfil/completar/")
        self.assertEqual(response.status_code, 200)
        mensajes = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("¡Perfil completado correctamente!", mensajes)



#########################################################################
