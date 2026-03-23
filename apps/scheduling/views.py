from apps.inventory.models import Inventario
from apps.ecas.models import CentroAcopio
from apps.operations.models import VentaInventario, CompraInventario
from config import constants as cons
from apps.ecas.constants import SECTION_TEMPLATES
import json


# Create your views here.
def _build_calendario_context(punto):
    """
    Construye el contexto específico para la sección calendario.
    """
    # Materiales disponibles en el punto
    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
    )

    # Centros de acopio (globales y asociados a este punto)
    centros_globales = list(
        CentroAcopio.objects.filter(visibilidad=cons.Visibilidad.GLOBAL)
    )
    centros_locales = list(
        CentroAcopio.objects.filter(puntos_eca=punto, visibilidad=cons.Visibilidad.ECA)
    )
    # Unificar por ID
    centros = {str(c.id): c for c in centros_globales + centros_locales}.values()

    # Ventas como eventos del calendario
    ventas = VentaInventario.objects.filter(inventario__punto_eca=punto).select_related(
        "inventario__material", "centro_acopio"
    )
    compras = CompraInventario.objects.filter(
        inventario__punto_eca=punto
    ).select_related("inventario__material")

    eventos = []
    for venta in ventas:
        # Preparamos el evento de venta para FullCalendar
        eventos.append(
            {
                "id": f"venta-{venta.id}",
                "type": "venta",
                "title": f"{venta.inventario.material.nombre} - {venta.cantidad} {venta.inventario.unidad_medida}",
                "start": venta.fecha_venta.isoformat(),
                "end": None,
                "backgroundColor": "#28a745",
                "materialId": str(venta.inventario.material.id),
                "centroAcopioId": str(venta.centro_acopio.id)
                if venta.centro_acopio
                else None,
                # Extended props para JS/modales
                "nombreMaterial": venta.inventario.material.nombre,
                "precioUnitario": float(venta.precio_venta)
                if venta.precio_venta is not None
                else None,
                "cantidad": float(venta.cantidad),
                "unidadMedida": venta.inventario.unidad_medida,
                "nombreCentroAcopio": venta.centro_acopio.nombre
                if venta.centro_acopio
                else "",
                "observaciones": venta.observaciones or "",
            }
        )

    for compra in compras:
        eventos.append(
            {
                "id": f"compra-{compra.id}",
                "type": "compra",
                "title": f"{compra.inventario.material.nombre} - {compra.cantidad} {compra.inventario.unidad_medida}",
                "start": compra.fecha_compra.isoformat(),
                "end": None,
                "backgroundColor": "#dc3545",  # Rojo para compras
                "materialId": str(compra.inventario.material.id),
                "centroAcopioId": None,  # No hay centro en compra
                "observaciones": compra.observaciones or "",
                "cantidad": float(compra.cantidad),
                "precioUnitario": float(compra.precio_compra or 0),
            }
        )

    # Serializo centros para el <select>
    centros_list = [
        {"id": str(centro.id), "nombre": centro.nombre} for centro in centros
    ]

    # Eventos propios del calendario
    from apps.scheduling.models import Evento

    eventos_calendario = Evento.objects.filter(punto_eca=punto)
    for evento in eventos_calendario:
        eventos.append(
            {
                "id": f"evento-{evento.id}",
                "type": "evento",
                "title": evento.titulo or "Evento",
                "start": evento.fecha_inicio.isoformat(),
                "end": evento.fecha_fin.isoformat() if evento.fecha_fin else None,
                "backgroundColor": evento.color or "#007bff",
                "materialId": str(evento.material.id) if evento.material else None,
                "centroAcopioId": str(evento.centro_acopio.id)
                if evento.centro_acopio
                else None,
                "descripcion": evento.descripcion or "",
                # Podés agregar más props extendidos acá si los necesita el frontend
            }
        )

    return {
        "seccion": "calendario",
        "section_template": SECTION_TEMPLATES["calendario"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "materiales_inventario": materiales_inventario,
        "centros": centros_list,
        "eventos": eventos,
        "EVENTOS": json.dumps(eventos),
    }
