import factory
from django.contrib.auth import get_user_model
from apps.chat.models import Chat, Mensaje
from apps.ecas.models import PuntoECA
from config import constants as cons

class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    nombres = factory.Faker("first_name")
    apellidos = factory.Sequence(lambda n: f"Apellido{n}")
    tipo_documento = "CC"
    numero_documento = factory.Sequence(lambda n: f"123456{n}")
    fecha_nacimiento = "1990-01-01"
    tipo_usuario = cons.TipoUsuario.CIUDADANO
    is_active = True
    celular = factory.Sequence(lambda n: f"3{(n % 1000000000):09d}")  # Colombian mobile format
    password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create user with proper password handling"""
        password = kwargs.pop('password', None)
        # Create the user instance
        instance = model_class(*args, **kwargs)
        if password is not None:
            instance.set_password(password)
        else:
            instance.set_password('defaultpassword')
        instance.save()
        return instance

    @classmethod
    def gestor(cls):
        """Create a usuario gestor ECA"""
        return cls(tipo_usuario=cons.TipoUsuario.GESTOR_ECA)

class PuntoECAFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PuntoECA

    nombre = factory.Sequence(lambda n: f"Punto ECA-{n}")
    email = factory.Sequence(lambda n: f"puntoeca{n}@example.com")
    telefono_punto = factory.Sequence(lambda n: f"6012345{(n % 1000):03d}")  # Format: 60 + 7 digits
    celular = factory.Sequence(lambda n: f"3{(n % 1000000000):09d}")  # Format: 3 + 9 digits

class ChatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Chat

    punto = factory.SubFactory(PuntoECAFactory)
    ciudadano = factory.SubFactory(UsuarioFactory)
    fecha_creacion = factory.Faker("date_time_this_year")

    @classmethod
    def con_gestor(cls):
        """Create a chat with a gestor ECA instead of a ciudadano"""
        return cls(ciudadano=UsuarioFactory.gestor())

class MensajeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mensaje

    chat = factory.SubFactory(ChatFactory)
    remitente = factory.SubFactory(UsuarioFactory)
    texto = factory.Faker("sentence")
    fecha_envio = factory.Faker("date_time_this_year")
    es_leido = False
    es_editado = False

