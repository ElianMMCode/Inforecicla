"""
Recrear conversaciones de chat con fechas correctas.
Punto Usme → todos los ciudadanos; otros ECAs → 1 ciudadano cada uno.
"""
import os
import sys
import random
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.ecas.models import PuntoECA
from apps.chat.models import Chat, Mensaje
from config.constants import TipoUsuario

random.seed(42)  # NOSONAR:S2245
Usuario = get_user_model()

PUNTO_ECA_EMAIL = os.environ.get('PUNTO_ECA_EMAIL', 'emelo.legacy@pm.me')

TEXTS_CIU = [
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

TEXTS_ECA = [
    "¡Buen día! Claro que sí, puede traer sus materiales en nuestro horario de atención.",
    "Hola, gracias por contactarnos. Sí, recibimos todo tipo de plásticos limpios y clasificados.",
    "¡Claro! Estaremos encantados de recibir su cartón. Abrimos de 7am a 5pm.",
    "Sí, tenemos ruta de recolección los martes y jueves. Déjenos su dirección para agendarla.",
    "El kilo de aluminio lo pagamos a ${precio}/kg dependiendo de la calidad.",
    "Con gusto. Le recomendamos separar en seco (cartón, plástico, vidrio) y orgánico.",
    "Sí, recibimos aceite de cocina usado en envases cerrados. Tiene un manejo especial.",
    "Recibimos electrodomésticos como parte de nuestra línea RAEE. Pregunte por los precios.",
    "Estamos en nuestra sede principal. Puede ver el mapa en nuestra página web.",
    "Sí, vidrio y metales los recibimos sin problema. El vidrio debe venir limpio.",
    "Tenemos contenedor especial para pilas. Por favor tráigalas en una bolsa separada.",
    "El PET lo pagamos a ${precio}/kg. Tráigalo limpio y preferiblemente compactado.",
    "Recibimos ropa en buen estado para reutilización y también la que no sirve para reciclaje textil.",
    "Sí, tenemos contenedores etiquetados para cada tipo de material.",
    "Abrimos de lunes a viernes de 7am a 5pm y sábados de 8am a 1pm.",
    "El proceso es simple: llega, pesamos su material, clasificamos y le pagamos al instante.",
    "Tenemos talleres educativos los primeros sábados de cada mes.",
    "Recibimos Tetra Pak, debe venir enjuagado y clasificado por separado.",
    "Puede llamarnos a nuestra línea de atención para información personalizada.",
    "Sí, nuestra báscula está certificada por la Superintendencia de Industria y Comercio.",
    "Compramos chatarra férrica a ${precio}/kg. Para cantidades grandes podemos recoger.",
    "Materiales peligrosos como pinturas requieren un proceso especial. Consulte con nuestro gestor ambiental.",
]

def biz_days_between(start, end):
    return [d for d in (start + datetime.timedelta(n) for n in range((end - start).days + 1)) if d.weekday() < 5]

def random_biz_day(biz_days):
    return random.choice(biz_days)  # NOSONAR:S2245

def random_time_on(day):
    h = random.randint(8, 17)  # NOSONAR:S2245
    m = random.randint(0, 59)  # NOSONAR:S2245
    return datetime.datetime(day.year, day.month, day.day, h, m)

def make_aware(dt):
    return timezone.make_aware(dt)

def create_mensajes(chat, ciudadano, gestor, biz_days):
    n = random.randint(3, 10)  # NOSONAR:S2245
    day = random_biz_day(biz_days)
    t0 = random_time_on(day)

    for i in range(n):
        offset = datetime.timedelta(minutes=random.randint(5, 180) * i)  # NOSONAR:S2245
        dt = t0 + offset
        if dt.date() > datetime.date(2026, 6, 22):
            dt = dt - datetime.timedelta(days=random.randint(1, 7))  # NOSONAR:S2245

        if i % 2 == 0:
            rem = ciudadano
            txt = random.choice(TEXTS_CIU)  # NOSONAR:S2245
        else:
            rem = gestor
            precio = random.randint(500, 6000)  # NOSONAR:S2245
            txt = random.choice(TEXTS_ECA).replace('{precio}', str(precio))  # NOSONAR:S2245

        msg = Mensaje.objects.create(chat=chat, remitente=rem, texto=txt)
        Mensaje.objects.filter(id=msg.id).update(fecha_envio=make_aware(dt))

        if i == n - 1 and random.random() < 0.3:  # NOSONAR:S2245
            Mensaje.objects.filter(id=msg.id).update(es_leido=False)

        if random.random() < 0.05:  # NOSONAR:S2245
            Mensaje.objects.filter(id=msg.id).update(es_editado=True)

    return n


def run():
    print("=== POBLAR CHATS V2 ===")
    random.seed(42)  # NOSONAR:S2245

    ciudadanos = list(Usuario.objects.filter(tipo_usuario=TipoUsuario.CIUDADANO, estado='ACTIVO'))
    ecas = list(PuntoECA.objects.filter(estado='ACTIVO').order_by('nombre'))
    biz_days = biz_days_between(datetime.date(2026, 5, 1), datetime.date(2026, 6, 22))

    punto_base = PuntoECA.objects.get(gestor_eca__email=PUNTO_ECA_EMAIL)
    gestor_base = Usuario.objects.get(email=PUNTO_ECA_EMAIL)

    total_chats = 0
    total_msgs = 0

    # 1. Punto Usme → ALL ciudadanos
    print(f"Punto Usme → {len(ciudadanos)} ciudadanos")
    for c in ciudadanos:
        chat, _ = Chat.objects.get_or_create(punto=punto_base, ciudadano=c)
        if chat.mensajes.exists():
            continue
        total_chats += 1
        n = create_mensajes(chat, c, gestor_base, biz_days)
        total_msgs += n
        print(f"  {c.email:35s} → {n} msgs")

    # 2. Other ECAs
    otros = [e for e in ecas if e.id != punto_base.id]
    print(f"\nOtros {len(otros)} ECAs")
    for idx, eca in enumerate(otros):
        gestor = eca.gestor_eca or gestor_base
        c = ciudadanos[idx % len(ciudadanos)]
        chat, _ = Chat.objects.get_or_create(punto=eca, ciudadano=c)
        if chat.mensajes.exists():
            print(f"  {eca.nombre:35s} ↔ {c.email:35s} → ya existía")
            continue
        total_chats += 1
        n = create_mensajes(chat, c, gestor, biz_days)
        total_msgs += n
        print(f"  {eca.nombre:35s} ↔ {c.email:35s} → {n} msgs")

    print("\n=== TOTAL ===")
    print(f"Chats nuevos: {total_chats}")
    print(f"Mensajes nuevos: {total_msgs}")
    print(f"Chats en DB: {Chat.objects.count()}")
    print(f"Mensajes en DB: {Mensaje.objects.count()}")

    print("\nDistribución por fecha:")
    for d in Mensaje.objects.dates('fecha_envio', 'day').order_by('fecha_envio'):
        cnt = Mensaje.objects.filter(fecha_envio__date=d).count()
        print(f"  {d}: {cnt}")


if __name__ == '__main__':
    run()
