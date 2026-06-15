import os
import django

# 1. Establecer la variable de entorno obligatoria antes de cualquier proceso
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. Inicializar el núcleo y el registro de apps de Django
django.setup()

# 3. Guardar la aplicación HTTP síncrona/asíncrona base
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# 4. REALIZAR LAS IMPORTACIONES DE CANALES DESPUÉS DE ESTABLECER EL NÚCLEO
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import apps.chat.routing
import apps.core.routing

# 5. Unificar todos los patrones de enrutamiento WebSocket en una sola lista limpia
websocket_patterns = apps.chat.routing.websocket_urlpatterns + apps.core.routing.websocket_urlpatterns

# 6. Definir la aplicación ASGI principal
application = ProtocolTypeRouter({
    # Peticiones HTTP normales procesadas de forma segura por Django
    "http": django_asgi_app,

    # Conexiones WebSocket para el Chat del Ciudadano, Punto ECA y Alertas
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_patterns
        )
    ),
})
