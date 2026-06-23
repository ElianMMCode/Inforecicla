from datetime import datetime, timezone
from apps.publicaciones.models import TipoPublicacion, CategoriaPublicacion
from config import constants

now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# ============================================================
# 1. Actualizar categoría "Educacion" existente
# ============================================================
try:
    cat = CategoriaPublicacion.objects.get(nombre="Educacion")
    cat.tipo = "Educativo"
    cat.descripcion = "Contenido educativo sobre reciclaje y gestión de residuos"
    cat.save()
    print(f"✓ Actualizada categoría '{cat.nombre}' → tipo 'Educativo'")
except CategoriaPublicacion.DoesNotExist:
    print("! Categoría 'Educacion' no encontrada, se omite actualización")

# ============================================================
# 2. Crear TipoPublicacion faltantes
# ============================================================
tipos_a_crear = [
    {"nombre": "Noticia",     "descripcion": "Información y novedades del sector del reciclaje"},
    {"nombre": "Evento",      "descripcion": "Actividades, jornadas y talleres programados"},
    {"nombre": "Educativo",   "descripcion": "Contenido formativo y didáctico sobre reciclaje"},
    {"nombre": "Punto ECA",   "descripcion": "Información y novedades de los Centros de Acopio"},
    {"nombre": "Campaña",     "descripcion": "Iniciativas y campañas de sensibilización ambiental"},
    {"nombre": "Guía / Tutorial", "descripcion": "Instrucciones detalladas y guías paso a paso"},
    {"nombre": "Consejo",     "descripcion": "Recomendaciones y datos útiles para el reciclaje"},
]

for t in tipos_a_crear:
    obj, created = TipoPublicacion.objects.get_or_create(
        nombre=t["nombre"],
        defaults={
            "descripcion": t["descripcion"],
            "estado": constants.Estado.ACTIVO,
        },
    )
    if created:
        print(f"✓ Creado TipoPublicacion: {t['nombre']}")
    else:
        print(f"  TipoPublicacion ya existe: {t['nombre']}")

# ============================================================
# 3. Crear CategoriaPublicacion faltantes
# ============================================================
categorias_a_crear = [
    # Noticia
    {"nombre": "Noticias del Sector",    "descripcion": "Noticias relevantes sobre reciclaje y medio ambiente",        "tipo": "Noticia"},
    {"nombre": "Actualidad Ambiental",   "descripcion": "Información sobre la situación ambiental actual",            "tipo": "Noticia"},
    {"nombre": "Comunicados Oficiales",  "descripcion": "Comunicados y anuncios oficiales de la plataforma",          "tipo": "Noticia"},
    # Evento
    {"nombre": "Jornadas de Reciclaje",  "descripcion": "Jornadas de recolección y separación de residuos",           "tipo": "Evento"},
    {"nombre": "Talleres y Capacitaciones", "descripcion": "Talleres formativos sobre reciclaje y sostenibilidad",    "tipo": "Evento"},
    {"nombre": "Ferias Ambientales",     "descripcion": "Ferias y exposiciones ambientales",                          "tipo": "Evento"},
    # Educativo (estas dos pensadas para contenido multimedia)
    {"nombre": "Video Tutoriales",       "descripcion": "Tutoriales en video sobre separación y reciclaje de residuos — preparada para contenido multimedia", "tipo": "Educativo"},
    {"nombre": "Infografías",            "descripcion": "Infografías educativas sobre reciclaje — preparada para contenido multimedia",                      "tipo": "Educativo"},
    {"nombre": "Guías de Reciclaje",     "descripcion": "Guías informativas sobre cómo reciclar correctamente",       "tipo": "Educativo"},
    # Punto ECA
    {"nombre": "Novedades del ECA",      "descripcion": "Noticias y novedades de los Centros de Acopio",              "tipo": "Punto Eca"},
    {"nombre": "Reportes y Estadísticas","descripcion": "Reportes y datos estadísticos de los ECA",                  "tipo": "Punto Eca"},
]

for c in categorias_a_crear:
    obj, created = CategoriaPublicacion.objects.get_or_create(
        nombre=c["nombre"],
        defaults={
            "descripcion": c["descripcion"],
            "tipo": c["tipo"],
            "estado": constants.Estado.ACTIVO,
        },
    )
    if created:
        print(f"✓ Creada CategoriaPublicacion: {c['nombre']} ({c['tipo']})")
    else:
        print(f"  CategoriaPublicacion ya existe: {c['nombre']}")

print("\n✅ Carga completada")
