from django.shortcuts import render
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from apps.ecas.models import PuntoECA
from apps.inventory.models import Inventario, Material, CategoriaMaterial, TipoMaterial
from apps.users.models import Usuario
from config import constants as cons
from apps.core.service import UserService
from apps.ecas.service import PuntoService
from apps.inventory.models import Material, CategoriaMaterial, TipoMaterial
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse
import json
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt


def _build_materiales_context(punto):
    """
    Construye el contexto por defecto para las demás secciones.
    """

    materiales_inventario = list(Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion"))

    total_stock = sum(float(inv.stock_actual) for inv in materiales_inventario)
    total_capacidad = sum(float(inv.capacidad_maxima) for inv in materiales_inventario)

    total_ok = sum(1 for inv in materiales_inventario if float(inv.ocupacion_actual) < float(inv.umbral_alerta))
    total_alerta = sum(1 for inv in materiales_inventario if float(inv.ocupacion_actual) >= float(inv.umbral_alerta) and float(inv.ocupacion_actual) < float(inv.umbral_critico))
    total_critico = sum(1 for inv in materiales_inventario if float(inv.ocupacion_actual) >= float(inv.umbral_critico))

    # Calcular porcentaje de ocupación global para el header
    if total_capacidad > 0:
        ocupacion_porcentaje = round((total_stock / total_capacidad) * 100)
    else:
        ocupacion_porcentaje = 0

    # KPIs adicionales para el header
    material_mayor_ocupacion = None
    material_mas_caro = None
    material_mas_barato = None
    costo_total_inventario = 0
    materiales_criticos = []
    if materiales_inventario:
        # Material mayor ocupación
        material_mayor_ocupacion = max(materiales_inventario, key=lambda i: float(i.ocupacion_actual))
        # Material más caro
        material_mas_caro = max(materiales_inventario, key=lambda i: float(i.precio_compra or 0))
        # Material más barato
        material_mas_barato = min(materiales_inventario, key=lambda i: float(i.precio_compra or 0))
        # Costo total inventario
        costo_total_inventario = sum(float(i.stock_actual) * float(i.precio_compra or 0) for i in materiales_inventario)
        # Materiales en estado crítico
        materiales_criticos = [i for i in materiales_inventario if float(i.ocupacion_actual) >= float(i.umbral_critico)]

    return {
        "seccion": "materiales",
        "section_template": SECTION_TEMPLATES["materiales"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "materiales_inventario": materiales_inventario,
        "total_stock": total_stock,
        "total_capacidad": total_capacidad,
        "total_ok": total_ok,
        "total_alerta": total_alerta,
        "total_critico": total_critico,
        "ocupacion_porcentaje": ocupacion_porcentaje,
        "categoria_inventario": (
            Inventario.objects.filter(punto_eca=punto)
            .select_related("material__categoria")
            .values_list("material__categoria__nombre", flat=True)
            .distinct()
        ),
        "tipo_inventario": (
            Inventario.objects.filter(punto_eca=punto)
            .select_related("material__tipo")
            .values_list("material__tipo__nombre", flat=True)
            .distinct()
        ),
        "material_mayor_ocupacion": material_mayor_ocupacion,
        "material_mas_caro": material_mas_caro,
        "material_mas_barato": material_mas_barato,
        "costo_total_inventario": costo_total_inventario,
        "materiales_criticos": materiales_criticos,
    }


def buscar_materiales_catalogo(request):
    # Nueva lógica: devolver materiales, categorías y tipos que están en el inventario del punto ECA
    punto_id = request.GET.get("puntoId", "").strip()
    query = request.GET.get("texto", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    tipo = request.GET.get("tipo", "").strip()

    inventario_qs = Inventario.objects.filter(punto_eca_id=punto_id).select_related(
        "material", "material__categoria", "material__tipo"
    )

    # Filtrar materiales por búsqueda de nombre/categoría/tipo
    if query:
        inventario_qs = inventario_qs.filter(
            Q(material__nombre__unaccent__icontains=query)
            | Q(material__categoria__nombre__unaccent__icontains=query)
            | Q(material__tipo__nombre__unaccent__icontains=query)
        )
    if categoria:
        inventario_qs = inventario_qs.filter(
            material__categoria__nombre__unaccent__iexact=categoria
        )
    if tipo:
        inventario_qs = inventario_qs.filter(
            material__tipo__nombre__unaccent__iexact=tipo
        )

    inventario_qs = inventario_qs.distinct()

    # Construir lista de materiales presentes en inventario
    resultados = []
    for item in inventario_qs:
        m = item.material
        resultados.append(
            {
                "materialId": str(m.id),  # UUID a String
                "nmbMaterial": m.nombre,
                "nmbCategoria": m.categoria.nombre if m.categoria else "General",
                "nmbTipo": m.tipo.nombre if m.tipo else "N/A",
                "dscMaterial": m.descripcion,
                "unidad": item.unidad_medida,
                "imagenUrl": m.imagen_url
                if m.imagen_url
                else "/static/img/materiales.png",
            }
        )

    return JsonResponse(resultados, safe=False)


def agregar_al_inventario(request):
    try:
        data = json.loads(request.body)

        material = Material.objects.get(id=data.get("materialId"))
        punto = PuntoECA.objects.get(id=data.get("puntoEcaId"))

        nuevo_material = Inventario.objects.create(
            punto_eca=punto,
            material=material,
            stock_actual=float(data.get("stockActual", 0)),
            capacidad_maxima=float(data.get("capacidadMaxima", 0)),
            unidad_medida=data.get("unidadMedida"),
            precio_compra=float(data.get("precioCompra", 0)),
            precio_venta=float(data.get("precioVenta", 0)),
            umbral_alerta=int(data.get("umbralAlerta", 20)),
            umbral_critico=int(data.get("umbralCritico", 10)),
        )
        return JsonResponse(
            {
                "mensaje": f"{material.nombre} agregado al inventario con éxito.",
                "error": False,
            }
        )
    except (Material.DoesNotExist, PuntoECA.DoesNotExist):
        return JsonResponse({"error": "Material o Punto ECA no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


def detalles_material_inventario(request, punto_id, inventario_id):
    punto = get_object_or_404(PuntoECA, id=punto_id)
    inventario_item = get_object_or_404(Inventario, punto_eca=punto, id=inventario_id)

    data = {
        "nmbMaterial": inventario_item.material.nombre,
        "nmbCategoria": inventario_item.material.categoria.nombre,
        "nmbTipo": inventario_item.material.tipo.nombre,
        "dscMaterial": inventario_item.material.descripcion,
        "stockActual": inventario_item.stock_actual,
        "capacidadMaxima": inventario_item.capacidad_maxima,
        "unidadMedida": inventario_item.unidad_medida,
        "precioCompra": inventario_item.precio_compra,
        "precioVenta": inventario_item.precio_venta,
        "porcentaje_ocupacion": float(inventario_item.ocupacion_actual),
        "imagenUrl": inventario_item.material.imagen_url,
        "umbralAlerta": inventario_item.umbral_alerta,
        "umbralCritico": inventario_item.umbral_critico,
    }

    return JsonResponse(data)


@require_http_methods(["PATCH"])
def actualizar_inventario(request, inventario_id):
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
            inventario_item = get_object_or_404(Inventario, id=inventario_id)

            inventario_item.stock_actual = float(
                data.get("stockActual", inventario_item.stock_actual)
            )
            inventario_item.capacidad_maxima = float(
                data.get("capacidadMaxima", inventario_item.capacidad_maxima)
            )
            inventario_item.unidad_medida = data.get(
                "unidadMedida", inventario_item.unidad_medida
            )
            inventario_item.precio_compra = float(
                data.get("precioCompra", inventario_item.precio_compra)
            )
            inventario_item.precio_venta = float(
                data.get("precioVenta", inventario_item.precio_venta)
            )
            inventario_item.umbral_alerta = int(
                data.get("umbralAlerta", inventario_item.umbral_alerta)
            )
            inventario_item.umbral_critico = int(
                data.get("umbralCritico", inventario_item.umbral_critico)
            )

            inventario_item.save()

            return JsonResponse(
                {"mensaje": "Inventario actualizado con éxito.", "error": False}
            )
        except Inventario.DoesNotExist:
            return JsonResponse({"error": "Inventario no encontrado"}, status=404)
        except Exception as e:
            return JsonResponse(
                {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
            )
    else:
        return JsonResponse({"error": "Método no permitido"}, status=405)


def buscar_materiales_inventario(request):
    punto_id = request.GET.get("puntoId", "").strip()
    query = request.GET.get("texto", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    unidad = request.GET.get("unidad", "").strip()  # nuevo filtro
    alerta = request.GET.get("alerta", "").strip()  # nuevo filtro
    ocupacion = request.GET.get("ocupacion", "").strip()  # nuevo filtro

    # Procesamos los filtros recibidos
    if not punto_id:
        return JsonResponse({"error": True, "mensaje": "Falta el puntoId"}, status=400)

    materiales_inventario = Inventario.objects.filter(
        punto_eca_id=punto_id
    ).select_related("material")

    if query:
        materiales_inventario = materiales_inventario.filter(
            Q(material__nombre__unaccent__icontains=query)
        )

    if categoria:
        materiales_inventario = materiales_inventario.filter(
            material__categoria__nombre__unaccent__icontains=categoria
        )
    if tipo:
        materiales_inventario = materiales_inventario.filter(
            material__tipo__nombre__iexact=tipo
        )
    if unidad:
        materiales_inventario = materiales_inventario.filter(
            unidad_medida=unidad
        )

    materiales_inventario = materiales_inventario.order_by("-fecha_modificacion")

    resultados = []
    for item in materiales_inventario:
        porcentaje_ocupacion = 0
        if item.capacidad_maxima and item.capacidad_maxima > 0:
            porcentaje_ocupacion = (item.stock_actual / item.capacidad_maxima) * 100
        else:
            porcentaje_ocupacion = 0
        porcentaje_ocupacion = round(porcentaje_ocupacion, 2)

        estado_alerta = "OK"
        # Mapping igual al template: Crítico si >= umbral_critico, Alerta si >= umbral_alerta, OK el resto
        if item.umbral_critico and porcentaje_ocupacion >= item.umbral_critico:
            estado_alerta = "Crítico"
        elif item.umbral_alerta and porcentaje_ocupacion >= item.umbral_alerta:
            estado_alerta = "Alerta"
        else:
            estado_alerta = "OK"

        resultados.append(
            {
                "inventarioId": str(item.id),
                "materialId": str(item.material.id),
                "nmbMaterial": item.material.nombre,
                "nmbCategoria": item.material.categoria.nombre
                if item.material.categoria
                else "General",
                "nmbTipo": item.material.tipo.nombre if item.material.tipo else "N/A",
                "dscMaterial": item.material.descripcion,
                "stockActual": item.stock_actual,
                "capacidadMaxima": item.capacidad_maxima,
                "unidadMedida": item.unidad_medida,
                "precioCompra": item.precio_compra,
                "precioVenta": item.precio_venta,
                "porcentaje_ocupacion": porcentaje_ocupacion,
                "umbral_alerta": item.umbral_alerta
                if hasattr(item, "umbral_alerta")
                else 0,
                "umbral_critico": item.umbral_critico
                if hasattr(item, "umbral_critico")
                else 0,
                "imagenUrl": item.material.imagen_url
                if item.material.imagen_url
                else "/static/img/materiales.png",
                "estado_alerta": estado_alerta,
            }
        )

    # Filtrado extra por ocupación y alerta
    if ocupacion:
        try:
            rango = ocupacion.split("-")
            minimo = float(rango[0]) if len(rango) > 0 else 0
            maximo = float(rango[1]) if len(rango) > 1 else 100
            resultados = [r for r in resultados if minimo <= r["porcentaje_ocupacion"] <= maximo]
            print(f"Después de filtrar ocupacion '{ocupacion}': {len(resultados)} items")
        except Exception as e:
            print(f"Error filtrando por ocupacion: {e}")
    if alerta:
        # Validar alerta (OK, Alerta, Crítico)
        resultados = [r for r in resultados if r["estado_alerta"] == alerta]
        print(f"Después de filtrar alerta '{alerta}': {len(resultados)} items")

    print(f"RESULTADOS: {len(resultados)}")
    return JsonResponse(resultados, safe=False)
