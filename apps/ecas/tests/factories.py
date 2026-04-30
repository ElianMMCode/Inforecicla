from factory.django import DjangoModelFactory
from factory.declarations import Sequence, SubFactory
from factory.faker import Faker
from apps.ecas.models import CentroAcopio, Localidad, PuntoECA
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        # Exclude username field since Usuario model uses email as USERNAME_FIELD
        # and doesn't have a username field
        exclude = ("username",)

    email = Sequence(lambda n: f"user{n}@example.com")
    numero_documento = Sequence(lambda n: f"12345678{n}")
    nombres = Sequence(lambda n: f"Nombre{n}")
    apellidos = Sequence(lambda n: f"Apellido{n}")
    password = "testpass123"
    is_active = True


class LocalidadFactory(DjangoModelFactory):
    class Meta:
        model = Localidad

    localidad_id = Faker("uuid4")
    nombre = Sequence(lambda n: f"Localidad {n}")
    descripcion = Faker("text", max_nb_chars=100)


class PuntoECAFactory(DjangoModelFactory):
    class Meta:
        model = PuntoECA

    gestor_eca = SubFactory(UserFactory)
    nombre = Sequence(lambda n: f"Punto ECA {n}")
    descripcion = Faker("text", max_nb_chars=500)
    celular = Sequence(lambda n: f"3{n:09d}")
    telefono_punto = Sequence(lambda n: f"60123456{n:02d}")
    direccion = Faker("address")
    logo_url_punto = Faker("url")
    foto_url_punto = Faker("url")
    email = Sequence(lambda n: f"punto{n}@example.com")


class CentroAcopioFactory(DjangoModelFactory):
    class Meta:
        model = CentroAcopio

    nombre = Sequence(lambda n: f"Centro de Acopio {n}")
    celular = Sequence(lambda n: f"3{n:09d}")
    tipo_centro = "PLANTA"
    visibilidad = "GLOBAL"
    descripcion = Faker("text", max_nb_chars=500)
    nota = Faker("text", max_nb_chars=500)
    email = Faker("email")
