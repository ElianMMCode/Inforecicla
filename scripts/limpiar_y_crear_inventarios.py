import os
import random
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


from django.db import transaction
from apps.inventory.models import Inventario, Material, CategoriaMaterial
from apps.ecas.models import PuntoECA
from apps.scheduling.models import Evento, EventoInstancia

JUNK_CATEGORY_IDS = [
    '08e6624f-1970-4b45-9617-19077a24c5d8',  # Libro
    '0bf0c497-64bd-4e9d-8e61-d97477bbaf01',  # Envases Plásticos
    '3949eba5-90cc-4117-bde0-873ec14e233d',  # Plastico
    '7deca245-4395-487a-a0c4-d35687cc055c',  # <script>alert(1)</script>
    'afd61604-1bb0-4382-96e8-71cb6acfd572',  # Papel y Cartón
    'd3ab111a-4860-4438-b72c-3f793b5ff6c4',  # Metales
    'ecf05784-8a70-424f-8fe0-b24881efb51e',  # Inactivo
    'baf5772b-6fe0-4420-a193-766b72e9fe2a',  # Pet 1
]

JUNK_MATERIAL_IDS = [
    '32198791-5c7b-40a4-8154-b920b9c753ba',  # Material Test Final
    'c6feb790-710a-4e3e-9f84-a08ddbd99589',  # Material Test Desc Vacia
    'be403804-e537-44d7-83b6-ab7644a5683d',  # Ropa vieja
    '5db89ae2-d47f-4551-a686-b4959ce846c4',  # Panini
    'f38d917a-81e4-4f8a-9bfc-c225f1fd539e',  # Panini 2022
    '5f16420a-796c-44f1-9af4-388cbed16566',  # Botella Cerveza
    '0199750c-af0e-70ef-b951-c581b4fe7d96',  # Cartón Mojado con Paja
    '68aaf633-d250-4346-a780-5bd3ead7f0b4',  # Latas de bebida de aluminio
    '74d253d5-f554-4134-b13c-71f1cfb59fdc',  # Plastico Test
    '90d4c292-a02c-447c-ab80-ed13b931ccde',  # Botellas PET transparentes
    'baa7d539-1662-454d-a25d-e48bb6e1b27e',  # Papel de oficina blanco
    'cfdb6734-8761-4579-a7e6-deaa93fdca08',  # Plastico
]

MATERIAL_NAMES = {
    'PET': ['Botella PET transparente', 'Botella PET verde'],
    'PEAD (HDPE)': ['Envase HDPE (detergente)', 'Garrafa HDPE'],
    'PEBD (LDPE)': ['Bolsa LDPE', 'Film stretch LDPE'],
    'PP': ['Tapa PP', 'Envase PP alimentos'],
    'PS': ['Icopor (PS expandido)'],
    'PVC': ['Tubos PVC'],
    'Cartón corrugado': ['Cartón'],
    'Cartón plegadizo': ['Cartulina plegadizo'],
    'Papel periódico': ['Papel periódico'],
    'Papel blanco (bond)': ['Papel bond blanco'],
    'Revistas/mixtos': ['Revistas y mixtos'],
    'Transparente': ['Frasco vidrio transparente', 'Botella retornable vidrio'],
    'Ámbar': ['Frasco vidrio ámbar'],
    'Verde': ['Frasco vidrio verde'],
    'Aluminio': ['Lata de aluminio'],
    'Acero/Hojalata': ['Lata de acero/hojalata'],
    'Chatarra férrica': ['Chatarra férrica'],
    'Envase multicapa': ['Envase Tetra Pak'],
    'Algodón': ['Ropa de algodón'],
    'Poliéster': ['Ropa de poliéster'],
    'Mezcla (mixtos)': ['Mezclas textiles'],
    'Pallets': ['Pallet de madera'],
    'MDF': ['MDF/Aglomerado'],
    'Pequeños aparatos': ['Celular en desuso'],
    'Grandes aparatos': ['Laptop dañada'],
    'Periféricos/Accesorios': ['Teclado/Mouse', 'Cargadores y cables'],
    'Pilas/Baterías': ['Pilas AA/AAA'],
    'Aceite de cocina usado': ['Aceite de cocina usado (UCE)'],
    'Llantas': ['Llantas usadas'],
    'Compostables': ['Orgánicos compostables'],
}


@transaction.atomic
def limpiar():
    print("=== LIMPIEZA ===")
    total_inv = Inventario.objects.count()
    Inventario.objects.all().delete()
    print(f"Inventarios eliminados: {total_inv}")

    referencing_events = Evento.objects.filter(material_id__in=JUNK_MATERIAL_IDS)
    if referencing_events.exists():
        event_ids = list(referencing_events.values_list('id', flat=True))
        referencing_instancias = EventoInstancia.objects.filter(evento_base_id__in=event_ids)
        if referencing_instancias.exists():
            print(f"Eliminando {referencing_instancias.count()} instancias de evento(s)...")
            referencing_instancias.delete()
        print(f"Eliminando {referencing_events.count()} evento(s) que referencian materiales basura...")
        referencing_events.delete()

    junk_mats = Material.objects.filter(id__in=JUNK_MATERIAL_IDS)
    print(f"Materiales basura a eliminar: {junk_mats.count()}")
    junk_mats.delete()

    for cat_id in JUNK_CATEGORY_IDS:
        cat = CategoriaMaterial.objects.filter(id=cat_id).first()
        if cat:
            print(f"Categoría eliminada: {cat.nombre}")
            cat.delete()

    pilas = CategoriaMaterial.objects.get(nombre='Pilas/Baterías')
    if pilas.estado == 'INACTIVO':
        pilas.estado = 'ACTIVO'
        pilas.save()
        print("Pilas/Baterías reactivada")

    print()


def get_material_refs():
    refs = {}
    for cat_name, mat_names in MATERIAL_NAMES.items():
        cat = CategoriaMaterial.objects.get(nombre=cat_name)
        for mat_name in mat_names:
            mat = Material.objects.get(nombre=mat_name, categoria=cat)
            refs[mat_name] = mat
    return refs


def create_inventories():
    print("=== CREANDO INVENTARIOS ===")
    refs = get_material_refs()
    ecas = list(PuntoECA.objects.filter(estado='ACTIVO').order_by('nombre'))
    print(f"ECAs activos: {len(ecas)}")

    comunes = [
        'Botella PET transparente', 'Cartón', 'Papel bond blanco',
        'Frasco vidrio transparente', 'Lata de aluminio',
        'Lata de acero/hojalata', 'Envase Tetra Pak',
    ]
    frecuentes = [
        'Envase HDPE (detergente)', 'Tapa PP', 'Revistas y mixtos',
        'Ropa de algodón', 'Ropa de poliéster',
    ]
    especiales = [
        'Celular en desuso', 'Teclado/Mouse', 'Aceite de cocina usado (UCE)',
        'Llantas usadas', 'Orgánicos compostables', 'Pilas AA/AAA',
        'Pallet de madera', 'Botella PET verde',
    ]
    menos_frecuentes = [
        'Icopor (PS expandido)', 'Tubos PVC', 'Papel periódico',
        'Frasco vidrio ámbar', 'Frasco vidrio verde',
        'Chatarra férrica', 'Mezclas textiles', 'MDF/Aglomerado',
    ]

    total = 0
    for idx, eca in enumerate(ecas):
        asignados = set(comunes)

        asig_frec = 3 if idx % 3 == 0 else 2
        extras_frec = sorted(frecuentes, key=lambda x: hash(x + str(idx)))[:asig_frec]
        asignados.update(extras_frec)

        if idx % 2 == 0:
            asig_esp = 2 if idx % 4 == 0 else 1
            extras_esp = sorted(especiales, key=lambda x: hash(str(idx) + x))[:asig_esp]
            asignados.update(extras_esp)

        if idx % 3 == 2:
            asig_menos = 2
            extras_menos = sorted(menos_frecuentes, key=lambda x: hash(x + str(idx)))[:asig_menos]
            asignados.update(extras_menos)

        for mat_name in asignados:
            mat = refs[mat_name]
            stock = random_stock(mat_name)
            cap = random_capacity(mat_name, stock)
            umbral_alerta, umbral_critico = random_umbrales()
            inv = Inventario(
                capacidad_maxima=cap,
                unidad_medida='KG',
                stock_actual=stock,
                umbral_alerta=umbral_alerta,
                umbral_critico=umbral_critico,
                material=mat,
                punto_eca=eca,
            )
            inv.save()
            total += 1

    print(f"Total inventarios creados: {total}")
    print()


def random_stock(mat_name):
    if 'PET' in mat_name or 'Botella' in mat_name:
        return round(random.uniform(5, 500), 2)
    if 'Cartón' in mat_name or 'Papel' in mat_name or 'Revistas' in mat_name:
        return round(random.uniform(10, 2000), 2)
    if 'Vidrio' in mat_name or 'Frasco' in mat_name:
        return round(random.uniform(10, 300), 2)
    if 'Aluminio' in mat_name or 'Acero' in mat_name or 'Chatarra' in mat_name:
        return round(random.uniform(20, 1000), 2)
    if 'Tetra' in mat_name:
        return round(random.uniform(50, 1500), 2)
    if 'Textil' in mat_name or 'Ropa' in mat_name or 'Mezcla' in mat_name:
        return round(random.uniform(5, 200), 2)
    if 'Pallet' in mat_name or 'MDF' in mat_name:
        return round(random.uniform(1, 50), 2)
    if 'Celular' in mat_name or 'Teclado' in mat_name or 'Cargadores' in mat_name or 'Laptop' in mat_name:
        return round(random.uniform(1, 30), 2)
    if 'Pilas' in mat_name:
        return round(random.uniform(10, 200), 2)
    if 'Aceite' in mat_name:
        return round(random.uniform(10, 500), 2)
    if 'Llantas' in mat_name:
        return round(random.uniform(1, 30), 2)
    if 'Orgánicos' in mat_name or 'Compost' in mat_name:
        return round(random.uniform(5, 100), 2)
    return round(random.uniform(10, 200), 2)


def random_capacity(mat_name, stock):
    factor = 1.5 if stock < 100 else 2.0 if stock < 500 else 3.0
    return round(stock * factor + random.uniform(50, 500), 2)


def random_umbrales():
    alerta = random.randint(60, 80)
    critico = random.randint(alerta + 5, 95)
    return alerta, critico


if __name__ == '__main__':
    random.seed(42)
    limpiar()
    create_inventories()
    print("=== COMPLETADO ===")
