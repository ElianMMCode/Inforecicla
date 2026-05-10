"""
Constants para la app ECAS.

Este módulo centraliza los templates utilizados para renderizar secciones específicas en la interfaz de usuario del sistema ECAS. Permite mapear claves de sección a archivos de template HTML, facilitando el mantenimiento, la modularidad y el cambio de rutas desde un solo lugar.
"""

# Diccionario que asocia una clave de sección con su template correspondiente.
# Útil para cargar dinámicamente los templates según la lógica de la vista.
SECTION_TEMPLATES = {
    "resumen": "ecas/section-resumen.html",
    "calendario": "ecas/section-calendario.html",
    "centros": "ecas/section-centros.html",
    "configuracion": "ecas/section-configuracion.html",
    "detalles_materiales": "ecas/section-detalles-materiales.html",
    "materiales": "ecas/section-materiales.html",
    "movimientos": "ecas/section-movimientos.html",
    "perfil": "ecas/section-perfil.html",
    "mensajes": "ecas/section-mensajes.html",
}
# Si agregás una nueva sección, sumala acá para que quede centralizado su template.
