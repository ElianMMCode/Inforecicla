"""
Crear conversaciones de chat entre ciudadanos y puntos ECA.
- Punto Usme El Dorado (emelo.legacy@pm.me): chat con TODOS los ciudadanos
- Los otros 25 ECAs: chat con al menos 1 ciudadano cada uno
- 3-10 mensajes por conversación
"""
import os
import sys
import random
import datetime
from decimal import Decimal

PUNTO_ECA_EMAIL = os.environ.get('PUNTO_ECA_EMAIL', 'emelo.legacy@pm.me')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.ecas.models import PuntoECA
from apps.chat.models import Chat, Mensaje
from config.constants import TipoUsuario

random.seed(42)

Usuario = get_user_model()

MENSAJES_CIUDADANO = [
    "Buenos días, ¿cuál es el horario de atención?",
    "Hola, ¿reciben botellas plásticas?",
    "Buenas tardes, quiero reciclar cartón, ¿a qué hora puedo llevar?",
    "¿Tienen algún programa de recolección a domicilio?",
    "Hola, ¿cuánto pagan por el kilo de aluminio?",
    "Buen día, necesito información sobre cómo clasificar los residuos",
    "¿Reciben aceite de cocina usado?",
    "Hola, tengo varios electrodomésticos viejos, ¿los reciben?",
    "Buenas, ¿dónde queda exactamente el punto?",
    "¿Aceptan vidrio y metales?",
    "Quiero llevar mis pilas usadas, ¿tienen disposición especial?",
    "Hola, soy reciclador independiente, ¿a qué precio compran el PET?",
    "Buenos días, ¿puedo llevar ropa usada para reciclar?",
    "¿Tienen contenedores separados para cada material?",
    "Hola, ¿el punto está abierto los fines de semana?",
    "Buenas tardes, ¿cuál es el proceso para entregar materiales?",
    "¿Tienen campañas de reciclaje educativo?",
    "Hola, necesito saber si reciben Tetra Pak (envases de leche)",
    "Buen día, ¿a qué número puedo llamar para más información?",
    "¿Tienen servicio de pesaje certificado?",
    "Quiero saber si compran chatarra y a qué precio",
    "Hola, ¿reciben residuos peligrosos como pinturas o solventes?",
]

RESPUESTAS_ECA = [
    "¡Buen día! Claro que sí, puede traer sus materiales en nuestro horario de atención.",
    "Hola, gracias por contactarnos. Sí, recibimos todo tipo de plásticos limpios y clasificados.",
    "¡Claro! Estaremos encantados de recibir su cartón. Abrimos de 7am a 5pm.",
    "Sí, tenemos ruta de recolección los martes y jueves. Déjenos su dirección para agendarla.",
    "El kilo de aluminio lo pagamos a ${precio}/kg dependiendo de la calidad.",
    "Con gusto. Le recomendamos separar en seco (cartón, plástico, vidrio) y orgánico.",
    "Sí, recibimos aceite de cocina usado en envases cerrados. Tiene un manejo especial.",
    "Recibimos electrodomésticos como parte de nuestra línea RAEE. Pregunte por los precios.",
    "Estamos en {direccion}. Puede ver el mapa en nuestra página web.",
    "Sí, vidrio y metales los recibimos sin problema. El vidrio debe venir limpio.",
    "Tenemos contenedor especial para pilas. Por favor tráigalas en una bolsa separada.",
    "El PET lo pagamos a ${precio}/kg. Tráigalo limpio y preferiblemente compactado.",
    "Recibimos ropa en buen estado para reutilización y también la que no sirve para reciclaje textil.",
    "Sí, tenemos contenedores etiquetados para cada tipo de material.",
    "Abrimos de lunes a viernes de 7am a 5pm y sábados de 8am a 1pm.",
    "El proceso es simple: llega, pesamos su material, clasificamos y le pagamos al instante.",
    "Tenemos talleres educativos los primeros sábados de cada mes.",
    "Recibimos Tetra Pak, debe venir enjuagado y clasificado por separado.",
    "Puede llamarnos al {telefono} para atención personalizada.",
    "Sí, nuestra báscula está certificada por la Superintendencia de Industria y Comercio.",
    "Compramos chatarra férrica a ${precio}/kg. Para cantidades grandes podemos recoger.",
    "Materiales peligrosos como pinturas requieren un proceso especial. Consulte con nuestro gestor ambiental.",
]

CHATS_POR_ECA = {}


def make_aware(dt):
    return timezone.make_aware(dt)


def create_chat_and_messages(punto, ciudadano, gestor_eca):
    chat, created = Chat.objects.get_or_create(punto=punto, ciudadano=ciudadano)
    if not created:
        return chat, False

    n_mensajes = random.randint(3, 10)
    fecha_base = datetime.datetime(2026, 5, random.randint(1, 31), random.randint(8, 17), random.randint(0, 59))

    for i in range(n_mensajes):
        if i % 2 == 0:
            remitente = ciudadano
            texto = random.choice(MENSAJES_CIUDADANO)
        else:
            remitente = gestor_eca
            precio = random.randint(200, 5000)
            direccion = punto.direccion or "nuestra sede"
            telefono = punto.celular or "nuestro teléfono"
            texto = random.choice(RESPUESTAS_ECA).replace('{precio}', str(precio)).replace('{direccion}', direccion).replace('{telefono}', telefono)

        fecha = fecha_base + datetime.timedelta(minutes=random.randint(1, 120) * i)
        if fecha.date() > datetime.date(2026, 6, 22):
            fecha = make_aware(datetime.datetime(2026, 6, 22, random.randint(8, 17), random.randint(0, 59)))

        es_leido = True
        if i == n_mensajes - 1 and random.random() < 0.3:
            es_leido = False

        Mensaje.objects.create(
            chat=chat,
            remitente=remitente,
            texto=texto,
            fecha_envio=make_aware(fecha) if fecha.tzinfo is None else fecha,
            es_leido=es_leido,
            es_editado=random.random() < 0.05,
        )

    return chat, True


def run():
    print("=== POBLAR CHATS ===")
    random.seed(42)

    ciudadanos = list(Usuario.objects.filter(tipo_usuario=TipoUsuario.CIUDADANO, estado='ACTIVO'))
    ecas = list(PuntoECA.objects.filter(estado='ACTIVO').order_by('nombre'))
    print(f"Ciudadanos: {len(ciudadanos)}")
    print(f"ECAs: {len(ecas)}")

    punto_base = PuntoECA.objects.get(gestor_eca__email=PUNTO_ECA_EMAIL)
    gestor_base = Usuario.objects.get(email=PUNTO_ECA_EMAIL)

    total_chats = 0
    total_msgs = 0

    # 1. Punto Usme → chat con TODOS los ciudadanos
    print(f"\n--- Punto Usme El Dorado: {len(ciudadanos)} chats ---")
    for ciudadano in ciudadanos:
        chat, created = create_chat_and_messages(punto_base, ciudadano, gestor_base)
        if created:
            msg_count = chat.mensajes.count()
            total_chats += 1
            total_msgs += msg_count
            print(f"  Chat con {ciudadano.email:35s} → {msg_count} mensajes")
        else:
            print(f"  Chat con {ciudadano.email:35s} → ya existía")

    # 2. Otros ECAs → chat con al menos 1 ciudadano
    otros_ecas = [e for e in ecas if e.id != punto_base.id]
    ciudadanos_disponibles = list(ciudadanos)

    print(f"\n--- Otros {len(otros_ecas)} ECAs ---")
    for idx, eca in enumerate(otros_ecas):
        gestor = eca.gestor_eca or gestor_base
        ciudadano = ciudadanos_disponibles[idx % len(ciudadanos_disponibles)]

        chat, created = create_chat_and_messages(eca, ciudadano, gestor)
        if created:
            msg_count = chat.mensajes.count()
            total_chats += 1
            total_msgs += msg_count
            print(f"  {eca.nombre:35s} ↔ {ciudadano.email:35s} → {msg_count} mensajes")
        else:
            print(f"  {eca.nombre:35s} ↔ {ciudadano.email:35s} → ya existía")

    print(f"\n=== RESUMEN ===")
    print(f"Chats creados: {total_chats}")
    print(f"Mensajes creados: {total_msgs}")
    print(f"Total chats en DB: {Chat.objects.count()}")
    print(f"Total mensajes en DB: {Mensaje.objects.count()}")


if __name__ == '__main__':
    run()
