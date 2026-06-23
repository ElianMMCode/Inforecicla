"""
Poblar Punto Usme El Dorado con flujo completo de Mayo 1 – Junio 22, 2026.
- 4 Centros de Acopio
- Precios en inventarios
- ~200 compras (3-7/día hábil)
- ~12 ventas (cada ~4-5 días)
- Umbrales ajustados para alertas
- Eventos
"""
import os
import sys
import random
import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.ecas.models import PuntoECA, CentroAcopio, Localidad
from apps.inventory.models import Inventario
from apps.operations.models import CompraInventario, VentaInventario
from apps.scheduling.models import Evento
from config.constants import TipoCentroAcopio, Visibilidad

random.seed(12345)  # NOSONAR
TODAY = datetime.date(2026, 6, 22)

Usuario = get_user_model()

PUNTO_ECA_EMAIL = os.environ.get('PUNTO_ECA_EMAIL', 'emelo.legacy@pm.me')

_CARTON = 'Cartón'
_PAPEL_BOND_BLANCO = 'Papel bond blanco'
_BOTELLA_PET_TRANSP = 'Botella PET transparente'
_ENVASE_TETRA_PAK = 'Envase Tetra Pak'
_PILAS_AA_AAA = 'Pilas AA/AAA'
_BOGOTA = 'Bogotá'

MATERIAL_CONFIG = [
    {'name': _CARTON, 'slug': 'carton', 'prob': 0.25, 'qty_range': (5, 80), 'precio_compra': 600, 'precio_venta': 1100},
    {'name': _PAPEL_BOND_BLANCO, 'slug': 'papel_bond', 'prob': 0.20, 'qty_range': (3, 50), 'precio_compra': 700, 'precio_venta': 1300},
    {'name': _BOTELLA_PET_TRANSP, 'slug': 'pet_transp', 'prob': 0.15, 'qty_range': (2, 25), 'precio_compra': 1200, 'precio_venta': 2100},
    {'name': _ENVASE_TETRA_PAK, 'slug': 'tetra', 'prob': 0.10, 'qty_range': (3, 20), 'precio_compra': 400, 'precio_venta': 800},
    {'name': 'Lata de aluminio', 'slug': 'aluminio', 'prob': 0.10, 'qty_range': (1, 12), 'precio_compra': 3500, 'precio_venta': 5800},
    {'name': 'Lata de acero/hojalata', 'slug': 'acero', 'prob': 0.05, 'qty_range': (2, 15), 'precio_compra': 800, 'precio_venta': 1500},
    {'name': 'Revistas y mixtos', 'slug': 'revistas', 'prob': 0.05, 'qty_range': (3, 25), 'precio_compra': 500, 'precio_venta': 900},
    {'name': 'Frasco vidrio transparente', 'slug': 'vidrio', 'prob': 0.04, 'qty_range': (2, 15), 'precio_compra': 200, 'precio_venta': 350},
    {'name': 'Botella PET verde', 'slug': 'pet_verde', 'prob': 0.03, 'qty_range': (1, 10), 'precio_compra': 1000, 'precio_venta': 1800},
    {'name': 'Ropa de algodón', 'slug': 'algodon', 'prob': 0.02, 'qty_range': (1, 6), 'precio_compra': 300, 'precio_venta': 600},
    {'name': _PILAS_AA_AAA, 'slug': 'pilas', 'prob': 0.005, 'qty_range': (0.5, 3), 'precio_compra': 100, 'precio_venta': 200},
    {'name': 'Ropa de poliéster', 'slug': 'poliester', 'prob': 0.005, 'qty_range': (1, 5), 'precio_compra': 250, 'precio_venta': 500},
]

OBSERVACIONES_COMPRA = [
    "Recolección diaria de recicladores de la zona",
    "Aporte de la comunidad del barrio El Dorado",
    "Entrega de material por parte de vecinos",
    "Recolección programa puerta a puerta",
    "Material clasificado por gestor ambiental",
    "Donación de material reciclable",
    "Compra a reciclador independiente",
    "Recolección de ruta ecológica",
    "Aporte del punto de recolección vecinal",
    "Material de la jornada de reciclaje",
]

OBSERVACIONES_COMPRA_BULK = [
    "CARGA MASIVA: Importación de registros del periodo anterior",
    "CARGA MASIVA: Migración de datos del sistema legacy",
    "CARGA MASIVA: Consolidado de corte mensual",
    "CARGA MASIVA: Carga inicial del mes desde báscula",
]

OBSERVACIONES_VENTA = [
    "Venta programada a planta de procesamiento",
    "Salida de material para reciclaje industrial",
    "Traslado a centro de acopio autorizado",
    "Descargue para procesamiento en Planta Usme",
    "Envío a recicladora para fundición",
]

CENTROS_DATA = [
    {
        'nombre': 'Planta de Procesamiento Usme',
        'tipo': TipoCentroAcopio.PLANTA,
        'visibilidad': Visibilidad.GLOBAL,
        'descripcion': 'Planta principal de procesamiento de materiales reciclables en la localidad de Usme.',
        'nota': 'Horario continuo de 7am a 5pm. Capacidad: 50 toneladas/día.',
        'nombre_contacto': 'Carlos Méndez',
        'email': 'carlos.mendez@procesamientousme.com',
        'celular': '3101112233',
        'ciudad': _BOGOTA,
        'localidad_nombre': 'Usme',
        'latitud': 4.5234,
        'longitud': -74.1325,
        'sitio_web': 'https://procesamientousme.com',
        'horario_atencion': 'Lun-Sáb 7:00-17:00',
        'direccion': 'Cra 5 # 15-30, Usme',
    },
    {
        'nombre': 'Centro de Transferencia El Dorado',
        'tipo': TipoCentroAcopio.PROVEEDOR,
        'visibilidad': Visibilidad.ECA,
        'descripcion': 'Centro de transferencia para materiales clasificados del sector oriental.',
        'nota': 'Solo para gestores ECA autorizados. Capacidad: 20 toneladas/día.',
        'nombre_contacto': 'Ana Rodríguez',
        'email': 'ana.rodriguez@transferenciaeldorado.com',
        'celular': '3102223344',
        'ciudad': _BOGOTA,
        'localidad_nombre': 'San Cristóbal',
        'latitud': 4.5621,
        'longitud': -74.0987,
        'sitio_web': '',
        'horario_atencion': 'Lun-Vie 8:00-16:00',
        'direccion': 'Cra 10 # 8-22, San Cristóbal',
    },
    {
        'nombre': 'Recicladora Sur de Bogotá',
        'tipo': TipoCentroAcopio.PROVEEDOR,
        'visibilidad': Visibilidad.GLOBAL,
        'descripcion': 'Recicladora del sur que procesa metales, plásticos y papel.',
        'nota': 'Compra todo tipo de materiales. Pago a 15 días.',
        'nombre_contacto': 'Pedro Martínez',
        'email': 'pedro.martinez@recicladorasur.com',
        'celular': '3103334455',
        'ciudad': _BOGOTA,
        'localidad_nombre': 'Ciudad Bolívar',
        'latitud': 4.4889,
        'longitud': -74.1543,
        'sitio_web': 'https://recicladorasur.com',
        'horario_atencion': 'Lun-Sáb 6:00-18:00',
        'direccion': 'Av. Villavicencio # 45-12, Ciudad Bolívar',
    },
    {
        'nombre': 'Planta de Reciclaje Inforecicla',
        'tipo': TipoCentroAcopio.PLANTA,
        'visibilidad': Visibilidad.GLOBAL,
        'descripcion': 'Planta central de la red Inforecicla para procesamiento de materiales.',
        'nota': 'Centro principal de acopio. Recibe materiales de toda la red.',
        'nombre_contacto': 'María García',
        'email': 'maria.garcia@inforecicla.com',
        'celular': '3104445566',
        'ciudad': _BOGOTA,
        'localidad_nombre': 'Kennedy',
        'latitud': 4.6213,
        'longitud': -74.1654,
        'sitio_web': 'https://inforecicla.com/planta',
        'horario_atencion': 'Lun-Vie 6:00-20:00, Sáb 7:00-14:00',
        'direccion': 'Av. Américas # 68-40, Kennedy',
    },
]

EVENTOS_DATA = [
    {'dia': 1, 'titulo': 'Carga masiva de inventario inicial', 'mat_slug': 'carton', 'color': '#ffc107', 'desc': 'Registro masivo de materiales acumulados durante el cierre mensual.', 'tipo_rep': 'NINGUNA'},
    {'dia': 8, 'titulo': 'Venta programada - Planta Usme', 'mat_slug': 'carton', 'color': '#28a745', 'desc': 'Venta de cartón y papel acumulado a Planta de Procesamiento Usme.', 'tipo_rep': 'NINGUNA'},
    {'dia': 14, 'titulo': 'Recolección especial de RAEE y pilas', 'mat_slug': 'pilas', 'color': '#dc3545', 'desc': 'Jornada especial de recolección de residuos eléctricos y electrónicos.', 'tipo_rep': 'NINGUNA'},
    {'dia': 18, 'titulo': 'Venta programada - Recicladora Sur', 'mat_slug': 'aluminio', 'color': '#28a745', 'desc': 'Venta de metales acumulados a Recicladora Sur de Bogotá.', 'tipo_rep': 'NINGUNA'},
    {'dia': 22, 'titulo': 'Mantenimiento de equipos de clasificación', 'mat_slug': 'pet_transp', 'color': '#007bff', 'desc': 'Mantenimiento preventivo de la banda de clasificación y báscula.', 'tipo_rep': 'NINGUNA'},
    {'dia': 27, 'titulo': 'Venta programada - Inforecicla', 'mat_slug': 'tetra', 'color': '#28a745', 'desc': 'Venta de Tetra Pak y plásticos a Planta de Reciclaje Inforecicla.', 'tipo_rep': 'NINGUNA'},
    {'dia': 32, 'titulo': 'Carga masiva de mitad de mes', 'mat_slug': 'papel_bond', 'color': '#ffc107', 'desc': 'Registro masivo de compras acumuladas de la primera quincena.', 'tipo_rep': 'NINGUNA'},
    {'dia': 36, 'titulo': 'Venta programada - Transferencia El Dorado', 'mat_slug': 'papel_bond', 'color': '#28a745', 'desc': 'Venta de papel bond acumulado a Centro de Transferencia El Dorado.', 'tipo_rep': 'NINGUNA'},
    {'dia': 41, 'titulo': 'Jornada de reciclaje comunitario', 'mat_slug': 'pet_transp', 'color': '#17a2b8', 'desc': 'Jornada abierta a la comunidad para entrega de materiales reciclables.', 'tipo_rep': 'NINGUNA'},
    {'dia': 45, 'titulo': 'Venta programada - Recicladora Sur', 'mat_slug': 'aluminio', 'color': '#28a745', 'desc': 'Venta de metales acumulados a Recicladora Sur.', 'tipo_rep': 'NINGUNA'},
    {'dia': 49, 'titulo': 'Venta programada - Planta Usme', 'mat_slug': 'carton', 'color': '#28a745', 'desc': 'Venta de cartón y Tetra Pak a Planta de Procesamiento Usme.', 'tipo_rep': 'NINGUNA'},
    {'dia': 53, 'titulo': 'Cierre mensual y programación de ventas', 'mat_slug': 'carton', 'color': '#6f42c1', 'desc': 'Corte mensual de inventarios y programación de ventas del próximo mes.', 'tipo_rep': 'NINGUNA'},
]

VENTA_PRECIOS = {
    _CARTON: 1050,
    _PAPEL_BOND_BLANCO: 1250,
    _BOTELLA_PET_TRANSP: 2000,
    _ENVASE_TETRA_PAK: 750,
    'Lata de aluminio': 5500,
    'Lata de acero/hojalata': 1400,
    'Revistas y mixtos': 850,
    'Frasco vidrio transparente': 300,
    'Botella PET verde': 1700,
    'Ropa de algodón': 500,
    _PILAS_AA_AAA: 150,
    'Ropa de poliéster': 400,
}


def get_business_days(start, end):
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += datetime.timedelta(days=1)
    return days


def random_time(day, min_hour=7, max_hour=17):
    hour = random.randint(min_hour, max_hour)  # NOSONAR
    minute = random.randint(0, 59)  # NOSONAR
    return timezone.make_aware(datetime.datetime(day.year, day.month, day.day, hour, minute))


def _crear_centros(punto):
    localidad_cache = {l.nombre: l for l in Localidad.objects.all()}
    centros = []
    for cd in CENTROS_DATA:
        loc = localidad_cache.get(cd['localidad_nombre'])
        centro, created = CentroAcopio.objects.get_or_create(
            nombre=cd['nombre'],
            defaults={
                'tipo_centro': cd['tipo'],
                'visibilidad': cd['visibilidad'],
                'descripcion': cd['descripcion'],
                'nota': cd['nota'],
                'nombre_contacto': cd['nombre_contacto'],
                'email': cd['email'],
                'celular': cd['celular'],
                'ciudad': cd['ciudad'],
                'localidad': loc,
                'latitud': cd['latitud'],
                'longitud': cd['longitud'],
                'sitio_web': cd['sitio_web'],
                'horario_atencion': cd['horario_atencion'],
            }
        )
        centro.puntos_eca.add(punto)
        centros.append(centro)
        print(f"  Centro: {'Creado' if created else 'Ya existe'} - {cd['nombre']}")
    return centros


def _setear_precios(mat_map):
    for mc in MATERIAL_CONFIG:
        inv = mat_map.get(mc['name'])
        if inv:
            inv.precio_compra = Decimal(str(mc['precio_compra']))
            inv.precio_venta = Decimal(str(mc['precio_venta']))
            inv.save()
    print("  Precios actualizados en inventarios")


def _generar_compras(business_days, day_index, mat_map, running_stock):
    material_names = [m['name'] for m in MATERIAL_CONFIG]
    material_probs = [m['prob'] for m in MATERIAL_CONFIG]
    creadas = 0
    bulk = 0

    for day in business_days:
        idx = day_index[day]
        for _ in range(random.randint(3, 7)):  # NOSONAR
            chosen = random.choices(material_names, weights=material_probs, k=1)[0]  # NOSONAR
            mc = next(m for m in MATERIAL_CONFIG if m['name'] == chosen)
            inv = mat_map[chosen]
            qty = round(random.uniform(*mc['qty_range']), 2)  # NOSONAR
            is_bulk = (idx <= 3) or (32 <= idx <= 34)
            obs = random.choice(OBSERVACIONES_COMPRA_BULK if is_bulk else OBSERVACIONES_COMPRA)  # NOSONAR
            fecha = random_time(day)
            CompraInventario.objects.create(
                inventario=inv, fecha_compra=fecha,
                cantidad=Decimal(str(qty)),
                precio_compra=Decimal(str(mc['precio_compra'])),
                observaciones=obs, carga_masiva=is_bulk,
            )
            running_stock[chosen] += qty
            creadas += 1
            if is_bulk:
                bulk += 1

    print(f"  Compras creadas: {creadas} ({bulk} carga masiva)")
    return creadas, bulk


def _crear_venta_unitaria(day, idx, chosen, inv, centros, running_stock):
    avail = running_stock[chosen]
    if avail < 20:
        return 0

    sell_pct = random.uniform(0.1, 0.4)  # NOSONAR
    qty = round(avail * sell_pct, 2)
    if qty < 5:
        qty = round(min(avail * 0.3, random.uniform(5, 30)), 2)  # NOSONAR

    is_bulk = (idx <= 3) or (32 <= idx <= 34)
    fecha = random_time(day, 8, 15)
    VentaInventario.objects.create(
        inventario=inv, fecha_venta=fecha,
        cantidad=Decimal(str(qty)),
        precio_venta=Decimal(str(VENTA_PRECIOS.get(chosen, 500))),
        observaciones=random.choice(OBSERVACIONES_VENTA),  # NOSONAR
        centro_acopio=random.choice(centros), carga_masiva=is_bulk,  # NOSONAR
    )
    running_stock[chosen] -= qty
    return 1 if not is_bulk else 2


def _generar_ventas(business_days, day_index, mat_map, centros, running_stock):
    venta_days = [d for i, d in enumerate(business_days) if i % 5 == 4 or i == len(business_days) - 1]
    creadas = 0
    bulk = 0

    for day in venta_days:
        idx = day_index[day]
        candidates = [m['name'] for m in MATERIAL_CONFIG if running_stock[m['name']] > 50]
        if not candidates:
            continue

        for _ in range(min(random.randint(1, 3), len(candidates))):  # NOSONAR
            chosen = random.choice(candidates)  # NOSONAR
            inv = mat_map[chosen]
            result = _crear_venta_unitaria(day, idx, chosen, inv, centros, running_stock)
            if result == 0:
                continue
            creadas += 1
            if result == 2:
                bulk += 1

    print(f"  Ventas creadas: {creadas} ({bulk} carga masiva)")
    return creadas, bulk


def _actualizar_stock(inventarios, running_stock):
    for inv in inventarios:
        inv.stock_actual = Decimal(str(round(running_stock[inv.material.nombre], 2)))
        inv.save()
    print("  Stocks actualizados")


def _ajustar_umbrales(mat_map):
    alert_config = [
        (_CARTON, 18, 28),
        (_PAPEL_BOND_BLANCO, 22, 32),
        (_ENVASE_TETRA_PAK, 20, 30),
        (_BOTELLA_PET_TRANSP, 12, 22),
        (_PILAS_AA_AAA, 8, 15),
    ]
    for name, al, cr in alert_config:
        inv = mat_map.get(name)
        if inv:
            inv.umbral_alerta = al
            inv.umbral_critico = cr
            inv.save()
    print("  Umbrales de alerta ajustados")


def _crear_eventos(business_days, punto, gestor, mat_map, centros):
    slug_to_name = {m['slug']: m['name'] for m in MATERIAL_CONFIG}
    creados = 0
    for ev_data in EVENTOS_DATA:
        idx = ev_data['dia']
        if idx > len(business_days):
            continue
        day = business_days[idx - 1]
        mat_name = slug_to_name[ev_data['mat_slug']]
        inv_ref = mat_map[mat_name]
        centro = random.choice(centros) if 'Venta' in ev_data['titulo'] else None  # NOSONAR
        inicio = random_time(day, 8, 10)
        fin = inicio + datetime.timedelta(hours=random.randint(1, 3))  # NOSONAR
        Evento.objects.create(
            material=inv_ref.material, centro_acopio=centro,
            punto_eca=punto, usuario=gestor,
            titulo=ev_data['titulo'], descripcion=ev_data['desc'],
            fecha_inicio=inicio, fecha_fin=fin,
            color=ev_data['color'], tipo_repeticion=ev_data['tipo_rep'],
            es_evento_generado=False,
        )
        creados += 1
    print(f"  Eventos creados: {creados}")
    return creados


def _verificar(punto, inventarios):
    print("\n=== VERIFICACIÓN ===")
    print(f"Compras: {CompraInventario.objects.filter(inventario__punto_eca=punto).count()}")
    print(f"Ventas: {VentaInventario.objects.filter(inventario__punto_eca=punto).count()}")
    print(f"Eventos: {Evento.objects.filter(punto_eca=punto).count()}")
    print(f"Centros de Acopio: {CentroAcopio.objects.count()}\n")
    for inv in inventarios:
        inv.refresh_from_db()
        occ = float(inv.ocupacion_actual or 0)
        print(f"{inv.material.nombre:35s} | stock={float(inv.stock_actual):>8.1f} | cap={float(inv.capacidad_maxima):>8.1f} | {occ:.1f}% | umbral_a={inv.umbral_alerta}% | umbral_c={inv.umbral_critico}% | {inv.alerta}")


@transaction.atomic
def run():
    print("=== POBLAR PUNTO USME EL DORADO ===")
    random.seed(12345)  # NOSONAR

    punto = PuntoECA.objects.get(gestor_eca__email=PUNTO_ECA_EMAIL)
    gestor = Usuario.objects.get(email=PUNTO_ECA_EMAIL)
    inventarios = list(Inventario.objects.filter(punto_eca=punto).select_related('material__categoria'))

    mat_map = {inv.material.nombre: inv for inv in inventarios}
    business_days = get_business_days(datetime.date(2026, 5, 1), TODAY)
    day_index = {d: i + 1 for i, d in enumerate(business_days)}
    running_stock = {inv.material.nombre: float(inv.stock_actual) for inv in inventarios}

    print(f"Punto ECA: {punto.nombre} ({punto.id})")
    print(f"Gestor: {gestor.email} ({gestor.id})")
    print(f"Inventarios: {len(inventarios)}, Días hábiles: {len(business_days)}")

    centros = _crear_centros(punto)
    _setear_precios(mat_map)
    _generar_compras(business_days, day_index, mat_map, running_stock)
    _generar_ventas(business_days, day_index, mat_map, centros, running_stock)
    _actualizar_stock(inventarios, running_stock)
    _ajustar_umbrales(mat_map)
    _crear_eventos(business_days, punto, gestor, mat_map, centros)
    _verificar(punto, inventarios)


if __name__ == '__main__':
    run()
