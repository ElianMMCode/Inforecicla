import secrets
import string
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.publicaciones.models import Notificacion
from config import constants as cons

Usuario = get_user_model()

_URL_ELIMINAR = "publicacion:eliminar_notificacion"


def _generar_password():
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


_PWD_TEST = _generar_password()


class EliminarNotificacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ciudadano = Usuario.objects.create_user(
            email="ciudadano@test.com",
            numero_documento="111111",
            password=_PWD_TEST,
            nombres="Ciudadano",
            apellidos="Test",
            tipo_usuario=cons.TipoUsuario.CIUDADANO,
        )
        cls.gestor = Usuario.objects.create_user(
            email="gestor@test.com",
            numero_documento="222222",
            password=_PWD_TEST,
            nombres="Gestor",
            apellidos="Test",
            tipo_usuario=cons.TipoUsuario.GESTOR_ECA,
        )
        cls.otro_ciudadano = Usuario.objects.create_user(
            email="otro@test.com",
            numero_documento="333333",
            password=_PWD_TEST,
            nombres="Otro",
            apellidos="Test",
            tipo_usuario=cons.TipoUsuario.CIUDADANO,
        )

    def _crear_notificacion(self, usuario, **kwargs):
        return Notificacion.objects.create(usuario=usuario, **kwargs)

    def _url(self, notificacion):
        return reverse(_URL_ELIMINAR, kwargs={"notificacion_id": notificacion.pk})

    # ── POST elimina notificación propia ────────────────────────────────────

    def test_post_elimina_notificacion_propia(self):
        notif = self._crear_notificacion(self.ciudadano)
        self.client.force_login(self.ciudadano)

        response = self.client.post(self._url(notif))

        self.assertRedirects(response, reverse("perfil_ciudadano"))
        self.assertFalse(Notificacion.objects.filter(pk=notif.pk).exists())

    def test_post_elimina_notificacion_gestor(self):
        notif = self._crear_notificacion(self.gestor)
        self.client.force_login(self.gestor)

        response = self.client.post(self._url(notif))

        self.assertRedirects(response, "/punto-eca/", fetch_redirect_response=False)
        self.assertFalse(Notificacion.objects.filter(pk=notif.pk).exists())

    # ── GET devuelve 405 ─────────────────────────────────────────────────────

    def test_get_devuelve_405(self):
        notif = self._crear_notificacion(self.ciudadano)
        self.client.force_login(self.ciudadano)

        response = self.client.get(self._url(notif))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Notificacion.objects.filter(pk=notif.pk).exists())

    # ── No puede eliminar notificación ajena ─────────────────────────────────

    def test_no_elimina_notificacion_ajena(self):
        notif = self._crear_notificacion(self.ciudadano)
        self.client.force_login(self.otro_ciudadano)

        response = self.client.post(self._url(notif))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Notificacion.objects.filter(pk=notif.pk).exists())

    # ── Requiere autenticación ───────────────────────────────────────────────

    def test_requiere_autenticacion(self):
        notif = self._crear_notificacion(self.ciudadano)
        response = self.client.post(self._url(notif))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    # ── Sesión guarda evento_instancia_id al eliminar ────────────────────────

    def test_sesion_guarda_evento_id_al_eliminar(self):
        from apps.ecas.models import PuntoECA
        from apps.scheduling.models import Evento, EventoInstancia
        from apps.inventory.models import Material, CategoriaMaterial

        punto = PuntoECA.objects.create(
            gestor_eca=self.gestor,
            nombre="Punto Test",
        )
        categoria = CategoriaMaterial.objects.create(nombre="Cat Test")
        material = Material.objects.create(
            nombre="Material Test",
            categoria=categoria,
        )
        evento = Evento.objects.create(
            material=material,
            punto_eca=punto,
            usuario=self.gestor,
            titulo="Evento Test",
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now() + timedelta(hours=1),
        )
        instancia = EventoInstancia.objects.create(
            evento_base=evento,
            punto_eca=punto,
            usuario=self.gestor,
            fecha_inicio=timezone.now() + timedelta(hours=2),
            fecha_fin=timezone.now() + timedelta(hours=3),
        )

        notif = Notificacion.objects.create(
            usuario=self.gestor,
            evento_instancia=instancia,
        )
        self.client.force_login(self.gestor)

        self.client.post(self._url(notif))

        session = self.client.session
        eliminadas = session.get("_notif_evento_eliminadas", [])
        self.assertIn(str(instancia.pk), eliminadas)

    # ── _check_upcoming_event_notifications no recrea eventos eliminados ─────

    def test_evento_eliminado_no_se_recrea(self):
        from apps.ecas.models import PuntoECA
        from apps.scheduling.models import Evento, EventoInstancia
        from apps.inventory.models import Material, CategoriaMaterial
        from apps.ecas.views import _check_upcoming_event_notifications

        punto = PuntoECA.objects.create(
            gestor_eca=self.gestor,
            nombre="Punto Test 2",
        )
        categoria = CategoriaMaterial.objects.create(nombre="Cat Test 2")
        material = Material.objects.create(
            nombre="Material Test 2",
            categoria=categoria,
        )
        ahora = timezone.now()
        evento = Evento.objects.create(
            material=material,
            punto_eca=punto,
            usuario=self.gestor,
            titulo="Evento Proximo",
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(hours=1),
        )
        instancia = EventoInstancia.objects.create(
            evento_base=evento,
            punto_eca=punto,
            usuario=self.gestor,
            fecha_inicio=ahora + timedelta(hours=2),
            fecha_fin=ahora + timedelta(hours=3),
            es_completado=False,
        )

        # Primero verificar que se crea sin el filtro de eliminadas
        Notificacion.objects.filter(
            usuario=self.gestor, evento_instancia=instancia
        ).delete()
        _check_upcoming_event_notifications(punto, self.gestor)
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.gestor, evento_instancia=instancia
            ).exists(),
            "Debe crear la notificación cuando no está en la lista de eliminadas",
        )

        # Eliminarla y pasar la lista de eliminadas
        Notificacion.objects.filter(
            usuario=self.gestor, evento_instancia=instancia
        ).delete()
        eliminadas = [str(instancia.pk)]
        _check_upcoming_event_notifications(punto, self.gestor, eliminadas=eliminadas)
        self.assertFalse(
            Notificacion.objects.filter(
                usuario=self.gestor, evento_instancia=instancia
            ).exists(),
            "No debe recrear la notificación si el evento está en la lista de eliminadas",
        )
