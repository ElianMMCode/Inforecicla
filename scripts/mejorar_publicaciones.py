from datetime import datetime, timezone
from django.contrib.auth import get_user_model
from apps.publicaciones.models import Publicacion, CategoriaPublicacion
from config import constants

User = get_user_model()
admin = User.objects.filter(email="admin@inforecicla.com").first()
now = datetime.now(timezone.utc)

# ============================================================
# 1. MEJORAR contenido de publicaciones activas existentes
# ============================================================

# --- "La importancia de reciclar" ---
pub = Publicacion.objects.filter(titulo="La importancia de reciclar").first()
if pub:
    pub.contenido = """Reciclar no es solo una tendencia ambiental, es una responsabilidad con nuestro planeta y las futuras generaciones. En Colombia, cada persona genera aproximadamente 0,8 kg de residuos al día, de los cuales solo una fracción se recicla correctamente.

¿Por qué es tan importante reciclar?

1. REDUCE LA CONTAMINACIÓN: Al reciclar evitamos que toneladas de residuos terminen en rellenos sanitarios, ríos y océanos. Un solo envase de plástico tarda hasta 500 años en degradarse.

2. AHORRA RECURSOS NATURALES: Reciclar una tonelada de papel salva 17 árboles. El vidrio reciclado se funde a menor temperatura que las materias primas vírgenes, ahorrando hasta un 30% de energía.

3. DISMINUYE LA HUELLA DE CARBONO: La producción a partir de materiales reciclados consume menos energía que la fabricación desde cero, reduciendo las emisiones de CO₂.

4. GENERA EMPLEO: La industria del reciclaje crea puestos de trabajo en recolección, clasificación y transformación. En Bogotá, más de 20.000 recicladores de oficio realizan esta labor.

5. ECONOMÍA CIRCULAR: Separar correctamente nuestros residuos permite que los materiales vuelvan a la cadena productiva como materia prima, cerrando el ciclo.

Cada acción cuenta. Empieza hoy: separa tus residuos en casa, lleva los reciclables a tu Punto ECA más cercano y comparte esta información con tu comunidad."""
    pub.resumen = "Descubre por qué reciclar es fundamental para el medio ambiente, la economía y la sociedad. Datos clave sobre el impacto del reciclaje en Colombia."
    pub.es_destacado = True
    pub.save()
    print("✓ Mejorada: La importancia de reciclar")

# --- "Buenas Practicas de Reciclaje Bogotano" ---
pub = Publicacion.objects.filter(titulo="Buenas Practicas de Reciclaje Bogotano").first()
if pub:
    pub.contenido = """En la capital colombiana, la correcta separación de residuos es clave para un reciclaje efectivo. Aquí te compartimos las buenas prácticas que debes seguir:

SEPARACIÓN EN ORIGEN
- Residuos aprovechables: plástico, vidrio, papel, cartón, metal y tetra pak.
- Residuos orgánicos: restos de comida, cáscaras, residuos de jardín.
- Residuos no aprovechables: servilletas usadas, papel higiénico, icopor sucio.

PLÁSTICOS
- Botellas PET: enjuágalas, retira la tapa y aplástalas.
- Envases de shampoo y detergente (HDPE): enjuaga bien y aplasta.
- Bolsas plásticas: límpialas y sécalas antes de almacenar.

PAPEL Y CARTÓN
- Cajas de cartón: desármalas y aplánalas.
- Papel bond: sin grapas, clips ni cinta adhesiva.
- Periódicos y revistas: apílalos ordenadamente.
- OJO: el papel contaminado con grasa o alimentos NO es reciclable.

VIDRIO
- Botellas y frascos: enjuágalos y retira las tapas.
- Clasifica por color: transparente, ámbar y verde.
- Nunca mezcles vidrio con cerámica o espejos.

METALES
- Latas de aluminio: enjuágalas y aplástalas.
- Latas de conserva: lávalas bien antes de reciclar.

TETRA PAK
- Envases de leche, jugos y caldos: enjuaga, escurre, aplasta y tapa.

Lleva tus residuos aprovechables al Punto ECA más cercano y contribuye a hacer de Bogotá una ciudad más sostenible. ♻️"""
    pub.resumen = "Guía completa de separación de residuos en Bogotá: aprende cómo reciclar plástico, papel, vidrio, metal y tetra pak correctamente."
    pub.es_destacado = True
    guias = CategoriaPublicacion.objects.filter(nombre="Guías de Reciclaje").first()
    if guias:
        pub.categoria = guias
    pub.save()
    print("✓ Mejorada: Buenas Practicas de Reciclaje Bogotano")

# --- "¿Cómo entregar tus envases de leche y jugos (Tetra Pak)?" (la activa) ---
pub = Publicacion.objects.filter(
    titulo="¿Cómo entregar tus envases de leche y jugos (Tetra Pak)?",
    estado=constants.Estado.ACTIVO
).first()
if pub:
    pub.contenido = """Los envases de cartón para bebidas (Tetra Pak) son 100% reciclables, pero requieren una preparación previa para evitar malos olores y facilitar su almacenamiento en las Estaciones de Clasificación y Aprovechamiento (ECA).

PASO 1: LAVAR
Enjuaga el interior del envase con un poco de agua para eliminar cualquier residuo de líquido. No uses jabón, solo agua.

PASO 2: ESCURRIR
Déjalo secar por completo boca abajo para evitar la proliferación de hongos o bacterias. Puedes colocarlo en un escurridor de platos.

PASO 3: APLASTAR
Despliega las pestañas de las esquinas y aplástalo completamente para reducir su volumen hasta en un 70%. Si tiene tapa plástica, vuelve a enroscarla para que no se pierda durante el proceso de reciclaje.

PASO 4: ALMACENAR
Guarda los envases aplastados en una bolsa o caja hasta que tengas suficiente para llevar al Punto ECA.

BENEFICIOS DE RECICLAR TETRA PAK
- Se recupera el 100% del material: el papel (75%), el polietileno (20%) y el aluminio (5%).
- Con 65 envases se puede fabricar una silla de jardín.
- El papel recuperado se usa para hacer cajas de cartón reciclado.

¡Cada envase cuenta! Lleva tus tetra pak limpios y aplastados a tu ECA más cercano."""
    pub.resumen = "Aprende a preparar tus envases Tetra Pak en 4 pasos: lavar, escurrir, aplastar y almacenar. 100% reciclables, 3 materiales recuperables."
    # Mover a categoría más adecuada
    guias = CategoriaPublicacion.objects.filter(nombre="Guías de Reciclaje").first()
    if guias:
        pub.categoria = guias
    pub.save()
    print("✓ Mejorada: ¿Cómo entregar tus envases de leche y jugos (Tetra Pak)?")

# La publicación INACTIVA (duplicado) se conserva tal cual

# ============================================================
# 2. AGREGAR 6 nuevas publicaciones (total 10 = 4 existentes + 6 nuevas)
# ============================================================

def get_cat(nombre):
    return CategoriaPublicacion.objects.filter(nombre=nombre).first()

def crear(titulo, contenido, resumen, categoria, destacado=False, video_url=None):
    cat = get_cat(categoria)
    if not cat:
        print(f"  ! Categoría '{categoria}' no encontrada")
        return
    pub, created = Publicacion.objects.get_or_create(
        titulo=titulo,
        defaults={
            "contenido": contenido,
            "resumen": resumen,
            "categoria": cat,
            "es_destacado": destacado,
            "video_url": video_url,
            "usuario": admin,
            "estado": constants.Estado.ACTIVO,
        },
    )
    print(f"{'✓ Creada' if created else '  Ya existe'}: {titulo}")

# --- Noticia ---
crear(
    titulo="Nueva legislación ambiental en Colombia: lo que debes saber",
    contenido="""El Congreso de Colombia aprobó una nueva ley que fortalece la gestión integral de residuos sólidos. Esta normativa establece metas ambiciosas para la reducción de residuos enviados a rellenos sanitarios y promueve la economía circular.

Puntos clave de la nueva ley:

- Meta de reciclaje: las ciudades deberán reciclar al menos el 20% de sus residuos para 2030.
- Responsabilidad extendida del productor: los fabricantes de envases y empaques deberán financiar sistemas de recolección selectiva.
- Incentivos tributarios: reducción de impuestos para empresas que implementen programas de reciclaje internos.
- Prohibición progresiva de plásticos de un solo uso: para 2028 quedarán prohibidos en todo el territorio nacional.

Desde InfoRecicla estaremos publicando guías detalladas para que los ciudadanos y las empresas puedan cumplir con estas nuevas disposiciones. Mantente informado.""",
    resumen="El Congreso aprobó una nueva ley de residuos sólidos con metas de reciclaje, responsabilidad extendida y prohibición de plásticos de un solo uso.",
    categoria="Noticias del Sector",
    destacado=True,
)

# --- Evento ---
crear(
    titulo="Jornada de reciclaje: trae tus residuos aprovechables",
    contenido="""Te invitamos a participar en nuestra próxima jornada de reciclaje comunitaria. Es una oportunidad perfecta para disponer correctamente de todos aquellos residuos que tienes acumulados en casa.

Fecha: Sábado 15 de julio
Horario: 8:00 AM - 2:00 PM
Ubicación: Parque Central - Cra 7 # 45-20

QUÉ PUEDES TRAER:
- Plásticos: botellas PET, envases de productos de limpieza, bolsas limpias.
- Papel y cartón: periódicos, revistas, cajas, cuadernos usados.
- Vidrio: botellas y frascos de cualquier color.
- Metales: latas de aluminio, conservas, tapas metálicas.
- Tetra Pak: envases de leche, jugos y caldos (bien enjuagados).
- RAEE: celulares en desuso, cargadores, baterías, pequeños electrodomésticos.

No olvides llevar tus residuos limpios y secos para facilitar su procesamiento. ¡Te esperamos! ♻️""",
    resumen="Jornada de reciclaje comunitaria el 15 de julio en el Parque Central. Recibimos plásticos, papel, vidrio, metales, tetra pak y RAEE.",
    categoria="Jornadas de Reciclaje",
)

# --- Video Tutorial ---
crear(
    titulo="Cómo separar residuos en casa | Video Tutorial",
    contenido="""En este video tutorial aprenderás paso a paso cómo separar correctamente los residuos en tu hogar. Una correcta separación en origen es el primer paso para que los materiales puedan ser reciclados eficientemente.

TEMAS DEL TUTORIAL:
1. Identifica tus residuos: aprende a diferenciar entre aprovechables, orgánicos y no aprovechables.
2. Prepara los materiales: enjuague, secado y aplastado de envases.
3. Almacenamiento temporal: cómo organizar tus residuos en casa sin generar malos olores.
4. Entrega en el Punto ECA: qué llevar y cómo presentarlo.

Este contenido está diseñado para que toda la familia pueda participar en la tarea del reciclaje. Comparte el video con tus vecinos y amigos.

Recuerda: la educación ambiental comienza en casa. 💚""",
    resumen="Aprende paso a paso cómo separar residuos en casa: identificación, preparación, almacenamiento y entrega en tu Punto ECA.",
    categoria="Video Tutoriales",
    destacado=True,
    video_url="https://youtu.be/cvakvfXj0KE?si=MMRkBx3YBSI5A1V9",
)

# --- Infografía ---
crear(
    titulo="Infografía: tiempos de degradación de residuos",
    contenido="""¿Sabías cuánto tardan en degradarse los residuos que generamos? Conoce los tiempos aproximados de degradación de los materiales más comunes:

TIEMPOS DE DEGRADACIÓN:
- Residuos orgánicos: 3 a 4 semanas
- Papel: 2 a 5 meses
- Tela de algodón: 3 a 6 meses
- Madera: 2 a 3 años
- Lata de aluminio: 10 a 100 años
- Lata de acero: 100 años
- Bolsa plástica: 150 a 200 años
- Envase plástico: 100 a 500 años
- Pila o batería: 500 a 1000 años
- Botella de vidrio: 4000 años
- Icopor (poliestireno): más de 500 años

DATOS CLAVE:
- Reciclar una tonelada de vidrio ahorra 1,2 toneladas de materias primas.
- Reciclar una tonelada de aluminio ahorra 5 toneladas de bauxita.
- Por cada tonelada de papel reciclado se salvan 17 árboles.

Comparte esta infografía para crear conciencia sobre la importancia del reciclaje.""",
    resumen="Infografía con los tiempos de degradación de residuos comunes: desde 3 semanas (orgánicos) hasta 4000 años (vidrio). Datos clave sobre reciclaje.",
    categoria="Infografías",
    destacado=True,
)

# --- Consejo ---
crear(
    titulo="5 consejos para reciclar en apartamento",
    contenido="""Vivir en apartamento no es excusa para no reciclar. Con estos 5 consejos prácticos podrás incorporar el reciclaje en tu rutina diaria sin ocupar mucho espacio.

1. ORGANIZA TUS CONTENEDORES
Usa contenedores apilables o bolsas reutilizables colgadas en la puerta de un armario. Destina un espacio mínimo para cada tipo: papel, plástico, vidrio y orgánicos.

2. APLASTA Y COMPRIME
Aplasta botellas PET, latas y envases de tetra pak para reducir su volumen hasta en un 70%. Esto te permitirá almacenar más material en menos espacio.

3. LAVA Y SECA
Enjuaga los envases antes de almacenarlos para evitar malos olores y la proliferación de insectos. Un envase limpio y seco no genera problemas.

4. ESTABLECE UNA RUTINA
Define un día a la semana para llevar tus reciclables al Punto ECA. Por ejemplo, los sábados en la mañana. Convertir esto en un hábito hará que no se acumulen.

5. INVOLUCRA A LA FAMILIA
Asigna responsabilidades a cada miembro del hogar. Los niños pueden encargarse de aplastar botellas y los adultos de llevar los materiales al ECA. ¡El reciclaje en equipo funciona mejor!

Pequeñas acciones, grandes cambios. Empieza hoy.""",
    resumen="5 consejos útiles para reciclar en apartamentos: organización, aplastado de envases, rutina semanal y cómo involucrar a toda la familia.",
    categoria="Informativo",
)

# --- Novedades ECA ---
crear(
    titulo="¿Qué es un Punto ECA y cómo funciona?",
    contenido="""Los Puntos ECA (Estaciones de Clasificación y Aprovechamiento) son centros autorizados donde los ciudadanos pueden llevar sus residuos aprovechables para que sean clasificados, procesados y reintegrados a la cadena productiva.

CÓMO FUNCIONA:
1. LLEGADA: Acércate al Punto ECA más cercano con tus residuos limpios y clasificados.
2. RECEPCIÓN: Un gestor ECA recibe tus materiales y verifica que estén en condiciones adecuadas.
3. REGISTRO: Tus residuos son pesados y registrados en el sistema. Puedes ver tu historial de aportes.
4. CLASIFICACIÓN: Los materiales se separan por tipo y calidad para su posterior procesamiento.
5. VALORIZACIÓN: Los residuos son preparados para su venta a industrias recicladoras.

MATERIALES ACEPTADOS:
- Plásticos: PET, HDPE, PP.
- Papel y cartón: periódicos, revistas, cajas, papel bond.
- Vidrio: transparente, ámbar y verde.
- Metales: aluminio y acero.
- Tetra Pak: envases limpios y aplastados.

MATERIALES NO ACEPTADOS:
- Residuos orgánicos.
- Residuos peligrosos o químicos.
- Medicamentos vencidos.
- Materiales contaminados con grasa.

Encuentra el Punto ECA más cercano usando el mapa interactivo de InfoRecicla y empieza a reciclar hoy.""",
    resumen="Conoce qué son los Puntos ECA, cómo funcionan paso a paso, qué materiales reciben y cuáles no. Encuentra el más cercano en el mapa.",
    categoria="Novedades del ECA",
)

print()
print("✅ Proceso completado")
print(f"Total publicaciones en BD: {Publicacion.objects.count()}")
print(f"  Activas: {Publicacion.objects.filter(estado=constants.Estado.ACTIVO).count()}")
print(f"  Inactivas: {Publicacion.objects.filter(estado=constants.Estado.INACTIVO).count()}")
