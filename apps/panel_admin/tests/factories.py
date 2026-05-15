import factory
from django.contrib.auth import get_user_model
from config import constants as cons
from ..models import Dashboard, Widget, Report

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    nombres = factory.Faker('first_name')
    apellidos = factory.Faker('last_name')
    numero_documento = factory.Sequence(lambda n: f'100000000{n}')  # Unique document number
    tipo_documento = cons.TipoDocumento.CC  # Default to CC
    fecha_nacimiento = factory.Faker('date_of_birth', minimum_age=18, maximum_age=65)
    tipo_usuario = cons.TipoUsuario.CIUDADANO  # Default to citizen
    is_active = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Create the user instance using the manager's create_user method
        # This ensures proper password handling
        return User.objects.create_user(
            email=kwargs.get('email'),
            numero_documento=kwargs.get('numero_documento'),
            password=kwargs.get('password', 'testpass123'),
            nombres=kwargs.get('nombres'),
            apellidos=kwargs.get('apellidos'),
            fecha_nacimiento=kwargs.get('fecha_nacimiento'),
            tipo_documento=kwargs.get('tipo_documento', cons.TipoDocumento.CC),
            tipo_usuario=kwargs.get('tipo_usuario', cons.TipoUsuario.CIUDADANO),
            is_active=kwargs.get('is_active', True)
        )

class DashboardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dashboard
    
    name = factory.Faker('catch_phrase')
    description = factory.Faker('text', max_nb_chars=200)
    is_public = factory.Faker('boolean')
    owner = factory.SubFactory(UserFactory)

class WidgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Widget
    
    title = factory.Faker('sentence', nb_words=4)
    widget_type = factory.Iterator(['chart', 'table', 'metric', 'text'])
    position_x = factory.Faker('random_int', min=0, max=11)
    position_y = factory.Faker('random_int', min=0, max=10)
    width = factory.Faker('random_int', min=1, max=4)
    height = factory.Faker('random_int', min=1, max=3)
    dashboard = factory.SubFactory(DashboardFactory)
    config = factory.LazyAttribute(lambda obj: {})

class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report
    
    title = factory.Faker('sentence', nb_words=5)
    description = factory.Faker('text', max_nb_chars=300)
    report_type = factory.Iterator(['sales', 'inventory', 'users', 'operations'])
    generated_by = factory.SubFactory(UserFactory)
    parameters = factory.LazyAttribute(lambda obj: {})
    is_scheduled = factory.Faker('boolean')