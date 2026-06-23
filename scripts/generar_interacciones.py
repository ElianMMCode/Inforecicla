import random
from django.contrib.auth import get_user_model
from apps.publicaciones.models import Publicacion, Comentario, Guardados, Reaccion
from config import constants

User = get_user_model()

# === 9 PUBLICACIONES ACTIVAS ===
publicaciones = list(Publicacion.objects.filter(estado=constants.Estado.ACTIVO).order_by("fecha_creacion"))
pub_ids = [p.id for p in publicaciones]

# === 24 CIUDADANOS ACTIVOS ===
usuarios = list(User.objects.filter(
    tipo_usuario=constants.TipoUsuario.CIUDADANO,
    is_active=True
).order_by("email"))

print(f"Usuarios: {len(usuarios)} | Publicaciones: {len(publicaciones)}")
random.seed(42)

# ============================================================
# BANCO DE TEXTOS REALISTAS PARA COMENTARIOS
# ============================================================
comentarios_pool = [
    # Opiniones generales
    "Excelente artículo, muy informativo. Gracias por compartir este contenido tan valioso.",
    "Muy importante la información compartida aquí. Todos deberíamos aplicar estos consejos.",
    "Gracias por la información detallada, me fue de gran ayuda para empezar a reciclar en casa.",
    "Me gustó mucho esta publicación. Ojalá más personas conocieran estos datos.",
    "Qué buen contenido, lo compartiré con mi familia y vecinos.",
    "Interesante, no sabía muchos de estos datos. Aprendí algo nuevo hoy.",
    "Muy bueno, deberían hacer más publicaciones como esta.",
    "Me parece genial que haya este tipo de información disponible para todos.",
    "Gracias por tomarte el tiempo de explicar esto tan claro.",
    "Excelente iniciativa, así se crea conciencia ambiental.",

    # Preguntas e interés
    "¿Cada cuánto actualizan esta información? Me gustaría estar al tanto.",
    "¿En qué otros puntos ECA puedo llevar estos materiales además de los mencionados?",
    "¿Hay algún requisito especial para llevar residuos electrónicos?",
    "¿Puedo llevar varios tipos de materiales juntos o debo separarlos por tipo?",
    "Qué bien explicado. ¿Tienen algún taller presencial para aprender más?",
    "¿Los residuos orgánicos también se pueden llevar a los puntos ECA?",

    # Tetra Pak específicamente
    "No sabía que los envases Tetra Pak se podían reciclar completamente. Siempre los botaba a la basura general, ahora los llevaré al ECA.",
    "Qué buen dato el de aplastar los envases Tetra Pak. Así ocupo menos espacio para almacenarlos.",
    "Muy práctico el paso a paso para los Tetra Pak. Ya empecé a hacerlo en casa.",
    "Perfecto, justo buscaba cómo preparar mis envases de leche. Gracias.",

    # Reciclaje en general
    "Desde que empecé a reciclar he notado que genero mucha menos basura. Vale la pena el esfuerzo.",
    "Cada vez más personas en mi edificio están reciclando, esto es contagioso.",
    "Pequeñas acciones generan grandes cambios. Todos podemos aportar nuestro granito de arena.",
    "El reciclaje debería ser obligatorio en todos los hogares colombianos.",
    "Me duele ver cómo la gente bota todo junto sin separar. Hay que educar más.",
    "Llevo 3 meses reciclando y ya veo la diferencia en casa. Menos bolsas de basura.",

    # Sobre la nueva ley
    "Excelente noticia lo de la nueva ley. Ojalá se cumpla a cabalidad.",
    "¿Cuándo empieza a regir la prohibición de plásticos?",
    "Me alegra que el gobierno esté tomando medidas en serio con el tema de residuos.",
    "Falta más divulgación sobre esta ley, mucha gente no la conoce todavía.",

    # Sobre jornadas/eventos
    "Allá estaré, no me pierdo estas jornadas. Siempre llevo mis materiales.",
    "Ojalá hubiera más jornadas como esta en todas las localidades.",
    "Ya marqué la fecha en el calendario. ¿Puedo llevar residuos de un familiar también?",
    "Excelente iniciativa, estas jornadas ayudan mucho a la comunidad.",

    # Sobre la infografía
    "Impactante saber que el vidrio tarda 4000 años en degradarse. Hay que reciclar más.",
    "Compartí esta infografía en mi trabajo y todos quedaron sorprendidos con los datos.",
    "Los datos de degradación son muy útiles para crear conciencia en los niños.",
    "Esta infografía debería estar en todos los colegios.",
]

# ============================================================
# 1. GENERAR COMENTARIOS (1-3 por usuario)
# ============================================================
print("\n--- COMENTARIOS ---")
contador = 0
for user in usuarios:
    num_comentarios = random.choices([1, 2, 3], weights=[3, 4, 3])[0]
    pubs_elegidas = random.sample(pub_ids, min(num_comentarios, len(pub_ids)))
    for pub_id in pubs_elegidas:
        texto = random.choice(comentarios_pool)
        obj, created = Comentario.objects.get_or_create(
            usuario=user,
            publicacion_id=pub_id,
            texto=texto,
            defaults={"tipo": "Noticia"},
        )
        if created:
            contador += 1

print(f"  Comentarios creados: {contador}")

# ============================================================
# 2. GENERAR GUARDADOS (2-4 por usuario)
# ============================================================
print("\n--- GUARDADOS ---")
contador = 0
for user in usuarios:
    num_guardados = random.choices([2, 3, 4], weights=[3, 4, 3])[0]
    pubs_elegidas = random.sample(pub_ids, min(num_guardados, len(pub_ids)))
    for pub_id in pubs_elegidas:
        obj, created = Guardados.objects.get_or_create(
            usuario=user,
            publicacion_id=pub_id,
        )
        if created:
            contador += 1

print(f"  Guardados creados: {contador}")

# ============================================================
# 3. GENERAR REACCIONES (3-5 por usuario, Like/Dislike)
# ============================================================
print("\n--- REACCIONES ---")
contador = 0
for user in usuarios:
    num_reacciones = random.choices([3, 4, 5], weights=[3, 4, 3])[0]
    pubs_elegidas = random.sample(pub_ids, min(num_reacciones, len(pub_ids)))
    for pub_id in pubs_elegidas:
        if random.random() < 0.8:  # 80% likes, 20% dislikes
            valor = "Like"
        else:
            valor = "Dislike"
        obj, created = Reaccion.objects.get_or_create(
            usuario=user,
            publicacion_id=pub_id,
            defaults={"valor": valor},
        )
        if created:
            contador += 1

print(f"  Reacciones creadas: {contador}")

# ============================================================
# RESUMEN
# ============================================================
print(f"\n{'='*50}")
print(f"Comentarios totales: {Comentario.objects.count()}")
print(f"Guardados totales:   {Guardados.objects.count()}")
print(f"Reacciones totales:  {Reaccion.objects.count()}")
print(f"{'='*50}")

# Usuarios con y sin interacciones

for tipo, modelo in [("Comentarios", Comentario), ("Guardados", Guardados), ("Reacciones", Reaccion)]:
    con = modelo.objects.values("usuario").distinct().count()
    print(f"Usuarios con {tipo}: {con}/{len(usuarios)}")
