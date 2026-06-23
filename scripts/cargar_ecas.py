import uuid
from django.contrib.auth import get_user_model
from apps.ecas.models import PuntoECA, Localidad
from config import constants

User = get_user_model()

# Cargar localidades
localidades = {l.nombre: l for l in Localidad.objects.all()}

# Gestores disponibles (los que no están asignados a ningún ECA activo)
emails_ocupados = PuntoECA.objects.filter(
    gestor_eca__isnull=False
).values_list("gestor_eca__email", flat=True)

gestores_libres = list(User.objects.filter(
    tipo_usuario=constants.TipoUsuario.GESTOR_ECA,
    is_active=True
).exclude(email__in=emails_ocupados))

print(f"Gestores disponibles: {len(gestores_libres)}")
gestor_idx = 0

# ============================================================
# DATOS REALISTAS DE PUNTOS ECA EN BOGOTÁ
# ============================================================
# (nombre, localidad, dirección, email_suffix, celular, telefono, horario, gestor_opcional)
ecas_data = [
    # --- USAQUÉN ---
    ("ECA Usaquén - Cedritos", "Usaquén",
     "Cra 19 # 134-52",
     "usaquen1", "3001110001", "6012345671",
     "Lun-Sáb 7:00-17:00", True),
    ("ECA Usaquén - Santa Bárbara", "Usaquén",
     "Cra 9 # 120-30",
     "usaquen2", "3001110002", "6012345672",
     "Lun-Vie 8:00-18:00, Sáb 8:00-14:00", True),

    # --- CHAPINERO ---
    ("ECA Chapinero - Porciúncula", "Chapinero",
     "Cra 7 # 60-40",
     "chapinero1", "3001110003", "6012345673",
     "Lun-Vie 7:00-19:00, Sáb 7:00-15:00", True),
    ("ECA Chapinero - Chicó", "Chapinero",
     "Cra 13 # 93-10",
     "chapinero2", "3001110004", "6012345674",
     "Lun-Sáb 8:00-17:00", True),

    # --- SANTA FE ---
    ("ECA Santa Fe - Centro", "Santa Fe",
     "Cra 5 # 14-50",
     "santafe1", "3001110005", "6012345675",
     "Lun-Vie 8:00-17:00", False),

    # --- SAN CRISTÓBAL ---
    ("ECA San Cristóbal - 20 de Julio", "San Cristóbal",
     "Cra 3 # 20-15",
     "scristobal1", "3001110006", "6012345676",
     "Lun-Sáb 7:00-16:00", True),

    # --- USME ---
    ("ECA Usme - Centro", "Usme",
     "Cra 1 # 70-40 Sur",
     "usme1", "3001110007", "6012345677",
     "Lun-Vie 8:00-17:00, Sáb 8:00-13:00", False),

    # --- BOSA --- (ya tiene 1 ECA: Nelson Hernan)
    ("ECA Bosa - La Estación", "Bosa",
     "Cra 80j # 60-30 Sur",
     "bosa2", "3001110008", "6012345678",
     "Lun-Sáb 8:00-17:00", True),

    # --- KENNEDY ---
    ("ECA Kennedy - Central", "Kennedy",
     "Av 1 de Mayo # 40-65",
     "kennedy1", "3001110009", "6012345679",
     "Lun-Vie 7:00-18:00, Sáb 7:00-14:00", True),
    ("ECA Kennedy - Patio Bonito", "Kennedy",
     "Cra 86 # 39-10 Sur",
     "kennedy2", "3001110010", "6012345680",
     "Lun-Sáb 8:00-17:00", True),

    # --- FONTIBÓN ---
    ("ECA Fontibón - Aeropuerto", "Fontibón",
     "Cra 108 # 20-30",
     "fontibon1", "3001110011", "6012345681",
     "Lun-Vie 8:00-18:00, Sáb 8:00-12:00", False),

    # --- ENGATIVÁ ---
    ("ECA Engativá - Pueblo", "Engativá",
     "Cra 93 # 68-25",
     "engativa1", "3001110012", "6012345682",
     "Lun-Sáb 7:00-17:00", True),
    ("ECA Engativá - Jardín Botánico", "Engativá",
     "Cra 74 # 56-12",
     "engativa2", "3001110013", "6012345683",
     "Lun-Vie 8:00-18:00", False),

    # --- SUBA --- (ya tiene 1 ECA: Punto Prueba)
    ("ECA Suba - Rincón", "Suba",
     "Cra 91 # 130-45",
     "suba2", "3001110014", "6012345684",
     "Lun-Sáb 7:00-17:00", True),

    # --- BARRIOS UNIDOS ---
    ("ECA Barrios Unidos", "Barrios Unidos",
     "Cra 30 # 68-50",
     "barriosunidos1", "3001110015", "6012345685",
     "Lun-Vie 8:00-17:00", False),

    # --- TEUSAQUILLO ---
    ("ECA Teusaquillo - Galerías", "Teusaquillo",
     "Cra 27 # 56-20",
     "teusaquillo1", "3001110016", "6012345686",
     "Lun-Sáb 8:00-17:00", True),

    # --- PUENTE ARANDA ---
    ("ECA Puente Aranda", "Puente Aranda",
     "Cra 50 # 15-30",
     "puentearanda1", "3001110017", "6012345687",
     "Lun-Vie 7:00-18:00, Sáb 7:00-14:00", False),

    # --- CIUDAD BOLÍVAR --- (ya tiene 1 ECA)
    ("ECA Ciudad Bolívar - Potosí", "Ciudad Bolívar",
     "Cra 27 # 62-10 Sur",
     "cbolivar2", "3001110018", "6012345688",
     "Lun-Sáb 7:00-16:00", True),

    # --- RAFAEL URIBE URIBE ---
    ("ECA Rafael Uribe - Quiroga", "Rafael Uribe Uribe",
     "Cra 14 # 30-40 Sur",
     "rafaeluribe1", "3001110019", "6012345689",
     "Lun-Vie 8:00-17:00, Sáb 8:00-13:00", False),

    # --- LA CANDELARIA ---
    ("ECA La Candelaria", "La Candelaria",
     "Cra 2 # 12-18",
     "candelaria1", "3001110020", "6012345690",
     "Lun-Vie 9:00-17:00", False),
]

# Coordenadas aproximadas por localidad (centroides de Bogotá)
coordenadas = {
    "Usaquén":           (4.712, -74.030),
    "Chapinero":         (4.645, -74.060),
    "Santa Fe":          (4.610, -74.070),
    "San Cristóbal":     (4.560, -74.090),
    "Usme":              (4.490, -74.130),
    "Tunjuelito":        (4.580, -74.140),
    "Bosa":              (4.610, -74.190),
    "Kennedy":           (4.630, -74.150),
    "Fontibón":          (4.675, -74.120),
    "Engativá":          (4.690, -74.100),
    "Suba":              (4.740, -74.080),
    "Barrios Unidos":    (4.665, -74.070),
    "Teusaquillo":       (4.635, -74.085),
    "Los Mártires":      (4.615, -74.090),
    "Antonio Nariño":    (4.590, -74.100),
    "Puente Aranda":     (4.620, -74.110),
    "La Candelaria":     (4.595, -74.075),
    "Rafael Uribe Uribe":(4.560, -74.105),
    "Ciudad Bolívar":    (4.540, -74.150),
    "Sumapaz":           (4.100, -74.200),
}

def variar_coord(base, rango=0.015):
    """Variar coordenada ligeramente para no dar el mismo punto"""
    import random
    random.seed(hash(base) % 2**32)
    return base + random.uniform(-rango, rango)

# ============================================================
# CREAR ECAs
# ============================================================
contador = 0
for item in ecas_data:
    nombre, loc_nombre, direccion, email_suf, cel, tel, horario, asignar_gestor = item

    loc = localidades.get(loc_nombre)
    if not loc:
        print(f"  ! Localidad no encontrada: {loc_nombre}")
        continue

    lat_base, lng_base = coordenadas.get(loc_nombre, (4.650, -74.100))

    email = f"eca.{email_suf}@inforecicla.com"

    # Gestor opcional
    gestor = None
    if asignar_gestor and gestor_idx < len(gestores_libres):
        gestor = gestores_libres[gestor_idx]
        gestor_idx += 1

    eca, created = PuntoECA.objects.get_or_create(
        email=email,
        defaults={
            "nombre": nombre,
            "descripcion": f"Punto ECA ubicado en {loc_nombre}, Bogotá. Atiende a la comunidad para la recepción de residuos aprovechables.",
            "celular": cel,
            "telefono_punto": tel,
            "ciudad": "Bogotá",
            "localidad": loc,
            "direccion": direccion,
            "latitud": variar_coord(lat_base),
            "longitud": variar_coord(lng_base),
            "horario_atencion": horario,
            "sitio_web": "https://inforecicla.com",
            "estado": constants.Estado.ACTIVO,
            "es_visible_en_mapa": True,
            "gestor_eca": gestor,
        },
    )
    if created:
        contador += 1
        gestor_str = f" → gestor: {gestor.email}" if gestor else ""
        print(f"✓ {nombre:40s} | {loc_nombre:20s} | ({lat_base:.4f}, {lng_base:.4f}){gestor_str}")

print(f"\n✅ Creados {contador} nuevos Puntos ECA")
print(f"Total ECAs: {PuntoECA.objects.count()}")
print(f"Activos: {PuntoECA.objects.filter(estado=constants.Estado.ACTIVO).count()}")
