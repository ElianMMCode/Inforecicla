from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from apps.inventory.models import Inventario
from config import constants as cons
from . import models
from apps.operations.service import CompraInventarioService, VentaInventarioService
from decimal import Decimal as decimal
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse, response, HttpResponse
import json
from django.utils import timezone
import datetime
from apps.ecas.models import CentroAcopio

# ===== import-export
from .resources import CompraInventarioResource, VentaInventarioResource
from import_export.formats.base_formats import XLSX
from weasyprint import HTML
from django.template.loader import render_to_string


# Create your views here.
def _build_movimientos_context(punto):
    # ... (código existente de contexto) ...
    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
    )
    compras = (
        models.CompraInventario.objects.filter(inventario__punto_eca=punto)
        .select_related("inventario__material")
        .order_by("-fecha_compra")
    )

    compras_list = [
        {
            "compraId": str(compra.id),
            "inventarioId": str(compra.inventario.id),
            "materialId": str(compra.inventario.material.id),
            "nombreMaterial": compra.inventario.material.nombre,
            "nombreCategoria": getattr(
                compra.inventario.material.categoria, "nombre", ""
            ),
            "nombreTipo": getattr(compra.inventario.material.tipo, "nombre", ""),
            "cantidad": float(compra.cantidad),
            "fechaCompra": compra.fecha_compra.isoformat(),
            "precioCompra": float(compra.precio_compra or 0),
            "observaciones": compra.observaciones or "",
        }
        for compra in compras
    ]

    ventas = (
        models.VentaInventario.objects.filter(inventario__punto_eca=punto)
        .select_related("inventario__material", "centro_acopio")
        .order_by("-fecha_venta")
    )

    ventas_list = [
        {
            "ventaId": str(venta.id),
            "inventarioId": str(venta.inventario.id),
            "materialId": str(venta.inventario.material.id),
            "nombreMaterial": venta.inventario.material.nombre,
            "nombreCategoria": getattr(
                venta.inventario.material.categoria, "nombre", ""
            ),
            "nombreTipo": getattr(venta.inventario.material.tipo, "nombre", ""),
            "cantidad": float(venta.cantidad),
            "fechaVenta": venta.fecha_venta.isoformat(),
            "precioVenta": float(venta.precio_venta or 0),
            "observaciones": venta.observaciones or "",
            "nombreCentroAcopio": getattr(venta.centro_acopio, "nombre", "")
            if getattr(venta, "centro_acopio", None)
            else "",
            "centroAcopioId": str(venta.centro_acopio.id)
            if getattr(venta, "centro_acopio", None)
            else "",
        }
        for venta in ventas
    ]

    # Centros de acopio (globales y asociados a este punto)
    centros_globales = list(
        CentroAcopio.objects.filter(visibilidad=cons.Visibilidad.GLOBAL)
    )
    centros_locales = list(
        CentroAcopio.objects.filter(puntos_eca=punto, visibilidad=cons.Visibilidad.ECA)
    )
    # Unificar por ID y convertir a lista de dicts simples para JS/JSON
    centros_map = {}
    for c in centros_globales + centros_locales:
        centros_map[str(c.id)] = {"id": str(c.id), "nombre": c.nombre}
    centros_list = list(centros_map.values())

    return {
        "seccion": "movimientos",
        "section_template": SECTION_TEMPLATES["movimientos"],
        "gestor": punto.gestor_eca,
        "punto": punto,
        "unidades_medida": cons.UnidadMedida.choices,
        "materiales_inventario": materiales_inventario,
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
        "centros": centros_list,
        "entradas": json.dumps(compras_list),
        "salidas": json.dumps(ventas_list),
        "historial_compras": compras_list,
        "historial_ventas": ventas_list,
        "HISTORIAL_COMPRAS": json.dumps(compras_list),
        "HISTORIAL_VENTAS": json.dumps(ventas_list),
    }


# (Código de views existentes continúa abajo...)


def registros_compras(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = CompraInventarioService.registro_compra(request, data)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


def registros_ventas(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = VentaInventarioService.registrar_venta(request, data)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


def editar_compra(request, compra_id):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = CompraInventarioService.editar_compra(request, data, compra_id)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


def editar_venta(request, venta_id):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = VentaInventarioService.editar_venta(request, data, venta_id)
        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


def borrar_compra(request, compra_id):
    resp = CompraInventarioService.borrar_compra(request, compra_id)
    return JsonResponse(resp, safe=False)


def borrar_venta(request, venta_id):
    resp = VentaInventarioService.borrar_venta(request, venta_id)
    return JsonResponse(resp, safe=False)


# ============== EXPORT EXCEL =============
def exportar_compras_excel(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    dataset = CompraInventarioResource().export(queryset)
    export_data = dataset.xlsx
    response = HttpResponse(
        export_data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="compras.xlsx"'
    return response


# ============== EXPORT PDF =============


def exportar_compras_pdf(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    compras = list(queryset)
    # Renderizar el HTML como string
    html_string = render_to_string("operations/compras_pdf.html", {"compras": compras})
    # Generar PDF desde el HTML
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[])
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="compras.pdf"'
    return response


def exportar_ventas_pdf(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    ventas = list(queryset)
    # Calcular total_venta por cada venta, si no viene en el modelo
    ventas_out = []
    total_ventas = 0
    for v in ventas:
        total = (v.cantidad or 0) * (v.precio_venta or 0)
        total_ventas += total
        # Enriquecer objeto para el template, sin tocar el modelo
        v.total_venta = total
        ventas_out.append(v)
    html_string = render_to_string("operations/ventas_pdf.html", {"ventas": ventas_out, "total_ventas": total_ventas})
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[])
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="ventas.pdf"'
    return response


def exportar_ventas_excel(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        queryset = queryset.filter(inventario__punto_eca__id=str(punto_eca_id))
    dataset = VentaInventarioResource().export(queryset)
    export_data = dataset.xlsx
    response = HttpResponse(
        export_data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="ventas.xlsx"'
    return response


# =========== HISTORIAL EXPORT EXCEL ===========
def exportar_historial_excel(request):
    """
    Exporta un Excel combinado de compras y ventas para el historial de movimientos
    """
    punto_eca_id = request.GET.get("punto_eca_id")
    compras = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    ventas = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        compras = compras.filter(inventario__punto_eca__id=str(punto_eca_id))
        ventas = ventas.filter(inventario__punto_eca__id=str(punto_eca_id))

    rows = []
    # Normalizar compras
    for c in compras:
        rows.append(
            {
                "tipo_movimiento": "Compra",
                "material": c.inventario.material.nombre,
                "fecha": c.fecha_compra,
                "cantidad": c.cantidad,
                "precio_unitario": c.precio_compra,
                "total": (c.cantidad or 0) * (c.precio_compra or 0),
                "centro_acopio": getattr(c.inventario.punto_eca, "nombre", ""),
                "observaciones": c.observaciones or "",
            }
        )
    # Normalizar ventas
    for v in ventas:
        rows.append(
            {
                "tipo_movimiento": "Venta",
                "material": v.inventario.material.nombre,
                "fecha": v.fecha_venta,
                "cantidad": v.cantidad,
                "precio_unitario": v.precio_venta,
                "total": (v.cantidad or 0) * (v.precio_venta or 0),
                "centro_acopio": getattr(v.centro_acopio, "nombre", "")
                or getattr(v.inventario.punto_eca, "nombre", ""),
                "observaciones": v.observaciones or "",
            }
        )

    # Ordenar por fecha descendente
    rows = sorted(rows, key=lambda r: r["fecha"], reverse=True)

    from import_export.formats.base_formats import XLSX
    from tablib import Dataset

    dataset = Dataset()
    dataset.headers = [
        "tipo_movimiento",
        "material",
        "fecha",
        "cantidad",
        "precio_unitario",
        "total",
        "centro_acopio",
        "observaciones",
    ]

    for row in rows:
        dataset.append(
            [
                row["tipo_movimiento"],
                row["material"],
                row["fecha"].strftime("%Y-%m-%d %H:%M"),
                float(row["cantidad"]) if row["cantidad"] is not None else "",
                float(row["precio_unitario"])
                if row["precio_unitario"] is not None
                else "",
                float(row["total"]) if row["total"] is not None else "",
                row["centro_acopio"],
                row["observaciones"],
            ]
        )

    export_data = dataset.xlsx
    response = HttpResponse(
        export_data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        'attachment; filename="historial_movimientos.xlsx"'
    )
    return response


def exportar_historial_pdf(request):
    punto_eca_id = request.GET.get("punto_eca_id")
    compras_queryset = models.CompraInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca"
    )
    ventas_queryset = models.VentaInventario.objects.all().select_related(
        "inventario__material", "inventario__punto_eca", "centro_acopio"
    )
    if punto_eca_id:
        compras_queryset = compras_queryset.filter(
            inventario__punto_eca__id=str(punto_eca_id)
        )
        ventas_queryset = ventas_queryset.filter(
            inventario__punto_eca__id=str(punto_eca_id)
        )

    compras = list(compras_queryset)
    ventas = list(ventas_queryset)
    historial = []
    for c in compras:
        historial.append(
            {
                "tipo": "Compra",
                "material": c.inventario.material.nombre
                if hasattr(c.inventario.material, "nombre")
                else "",
                "cantidad": c.cantidad,
                "precio_unitario": c.precio_compra,
                "total": (c.cantidad or 0) * (c.precio_compra or 0),
                "fecha": c.fecha_compra,
                "categoria": getattr(c.inventario.material, "categoria", ""),
                "observaciones": getattr(c, "observaciones", ""),
            }
        )
    for v in ventas:
        historial.append(
            {
                "tipo": "Venta",
                "material": v.inventario.material.nombre
                if hasattr(v.inventario.material, "nombre")
                else "",
                "cantidad": v.cantidad,
                "precio_unitario": v.precio_venta,
                "total": (v.cantidad or 0) * (v.precio_venta or 0),
                "fecha": v.fecha_venta,
                "categoria": getattr(v.inventario.material, "categoria", ""),
                "observaciones": getattr(v, "observaciones", ""),
                "centro_acopio": v.centro_acopio.nombre
                if hasattr(v, "centro_acopio") and v.centro_acopio
                else "",
            }
        )
    historial.sort(key=lambda m: m["fecha"] or "", reverse=True)
    html_string = render_to_string(
        "operations/historial_pdf.html", {"historial": historial}
    )
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[])
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="historial.pdf"'
    return response


# =========== ADMIN PANEL VIEWS ===========

def es_administrador(user):
    """Verifica si el usuario es administrador."""
    from config.constants import TipoUsuario
    if not user.is_authenticated:
        return False
    return bool(user.is_staff or user.is_superuser or user.tipo_usuario == TipoUsuario.ADMIN)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def dashboard_operaciones(request):
    """Dashboard de operaciones con estadísticas generales."""
    compras = models.CompraInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca'
    ).all()
    
    ventas = models.VentaInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca',
        'centro_acopio'
    ).all()
    
    # Calcular estadísticas
    total_compras = compras.count()
    total_ventas = ventas.count()
    
    total_cantidad_comprada = sum(c.cantidad or 0 for c in compras)
    total_cantidad_vendida = sum(v.cantidad or 0 for v in ventas)
    
    total_costo_compras = sum((c.cantidad or 0) * (c.precio_compra or 0) for c in compras)
    total_ingresos_ventas = sum((v.cantidad or 0) * (v.precio_venta or 0) for v in ventas)
    
    context = {
        'total_compras': total_compras,
        'total_ventas': total_ventas,
        'total_cantidad_comprada': total_cantidad_comprada,
        'total_cantidad_vendida': total_cantidad_vendida,
        'total_costo_compras': total_costo_compras,
        'total_ingresos_ventas': total_ingresos_ventas,
        'compras_recientes': compras[:5],
        'ventas_recientes': ventas[:5],
    }
    
    return render(request, 'admin/operaciones/dashboard.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def listar_compras_admin(request):
    """Lista todas las compras de inventario."""
    compras = models.CompraInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca'
    ).order_by('-fecha_compra')
    
    context = {
        'compras': compras,
        'total_compras': compras.count(),
    }
    
    return render(request, 'admin/operaciones/compras_listar.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_compra_admin(request):
    """Crea una nueva compra de inventario."""
    if request.method == 'GET':
        inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
        context = {
            'inventarios': inventarios,
        }
        return render(request, 'admin/operaciones/compra_crear.html', context)
    
    elif request.method == 'POST':
        inventario_id = request.POST.get('inventario_id')
        cantidad = request.POST.get('cantidad')
        precio_compra = request.POST.get('precio_compra')
        observaciones = request.POST.get('observaciones')
        
        try:
            data = {
                'inventarioId': inventario_id,
                'cantidad': float(cantidad),
                'precioCompra': float(precio_compra),
                'fechaCompra': timezone.now().isoformat(),
                'observaciones': observaciones or '',
            }
            respuesta = CompraInventarioService.registro_compra(request, data)
            if respuesta.get('error'):
                raise ValueError(respuesta.get('mensaje', 'No se pudo registrar la compra.'))
            messages.success(request, 'Compra registrada correctamente.')
            return redirect('operations:listar_compras_admin')
        except Exception as e:
            context = {
                'error': str(e),
                'inventarios': Inventario.objects.select_related('material', 'punto_eca').all(),
            }
            return render(request, 'admin/operaciones/compra_crear.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def editar_compra_admin(request, compra_id):
    """Edita una compra de inventario existente."""
    compra = get_object_or_404(models.CompraInventario, id=compra_id)
    
    if request.method == 'GET':
        inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
        context = {
            'compra': compra,
            'inventarios': inventarios,
        }
        return render(request, 'admin/operaciones/compra_editar.html', context)
    
    elif request.method == 'POST':
        cantidad = request.POST.get('cantidad')
        precio_compra = request.POST.get('precio_compra')
        observaciones = request.POST.get('observaciones')
        
        try:
            data = {
                'compraId': str(compra_id),
                'cantidad': float(cantidad),
                'precioCompra': float(precio_compra),
                'fechaCompra': compra.fecha_compra.isoformat(),
                'observaciones': observaciones or '',
            }
            respuesta = CompraInventarioService.editar_compra(request, data, compra_id)
            if respuesta.get('error'):
                raise ValueError(respuesta.get('mensaje', 'No se pudo actualizar la compra.'))
            messages.success(request, 'Compra actualizada correctamente.')
            return redirect('operations:listar_compras_admin')
        except Exception as e:
            inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
            context = {
                'compra': compra,
                'error': str(e),
                'inventarios': inventarios,
            }
            return render(request, 'admin/operaciones/compra_editar.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def eliminar_compra_admin(request, compra_id):
    """Elimina una compra de inventario."""
    compra = get_object_or_404(models.CompraInventario, id=compra_id)
    
    if request.method == 'GET':
        context = {
            'compra': compra,
        }
        return render(request, 'admin/operaciones/compra_eliminar.html', context)
    
    elif request.method == 'POST':
        try:
            respuesta = CompraInventarioService.borrar_compra(request, compra_id)
            if respuesta.get('error'):
                raise ValueError(respuesta.get('mensaje', 'No se pudo eliminar la compra.'))
            messages.success(request, 'Compra eliminada correctamente.')
            return redirect('operations:listar_compras_admin')
        except Exception as e:
            context = {
                'compra': compra,
                'error': str(e),
            }
            return render(request, 'admin/operaciones/compra_eliminar.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def listar_ventas_admin(request):
    """Lista todas las ventas de inventario."""
    ventas = models.VentaInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca',
        'centro_acopio'
    ).order_by('-fecha_venta')
    
    context = {
        'ventas': ventas,
        'total_ventas': ventas.count(),
    }
    
    return render(request, 'admin/operaciones/ventas_listar.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_venta_admin(request):
    """Crea una nueva venta de inventario."""
    if request.method == 'GET':
        inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
        centros_acopio = CentroAcopio.objects.all()
        context = {
            'inventarios': inventarios,
            'centros_acopio': centros_acopio,
        }
        return render(request, 'admin/operaciones/venta_crear.html', context)
    
    elif request.method == 'POST':
        inventario_id = request.POST.get('inventario_id')
        cantidad = request.POST.get('cantidad')
        precio_venta = request.POST.get('precio_venta')
        centro_acopio_id = request.POST.get('centro_acopio_id')
        observaciones = request.POST.get('observaciones')
        
        try:
            data = {
                'inventarioId': inventario_id,
                'cantidad': float(cantidad),
                'precioVenta': float(precio_venta),
                'fechaVenta': timezone.now().isoformat(),
                'centroAcopioId': centro_acopio_id or None,
                'observaciones': observaciones or '',
            }
            respuesta = VentaInventarioService.registrar_venta(request, data)
            if respuesta.get('error'):
                raise ValueError(respuesta.get('mensaje', 'No se pudo registrar la venta.'))
            messages.success(request, 'Venta registrada correctamente.')
            return redirect('operations:listar_ventas_admin')
        except Exception as e:
            inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
            centros_acopio = CentroAcopio.objects.all()
            context = {
                'error': str(e),
                'inventarios': inventarios,
                'centros_acopio': centros_acopio,
            }
            return render(request, 'admin/operaciones/venta_crear.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def editar_venta_admin(request, venta_id):
    """Edita una venta de inventario existente."""
    venta = get_object_or_404(models.VentaInventario, id=venta_id)
    
    if request.method == 'GET':
        inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
        centros_acopio = CentroAcopio.objects.all()
        context = {
            'venta': venta,
            'inventarios': inventarios,
            'centros_acopio': centros_acopio,
        }
        return render(request, 'admin/operaciones/venta_editar.html', context)
    
    elif request.method == 'POST':
        cantidad = request.POST.get('cantidad')
        precio_venta = request.POST.get('precio_venta')
        centro_acopio_id = request.POST.get('centro_acopio_id')
        observaciones = request.POST.get('observaciones')
        
        try:
            data = {
                'ventaId': str(venta_id),
                'cantidad': float(cantidad),
                'precioVenta': float(precio_venta),
                'fechaVenta': venta.fecha_venta.isoformat(),
                'centroAcopioId': centro_acopio_id or None,
                'observaciones': observaciones or '',
            }
            respuesta = VentaInventarioService.editar_venta(request, data, venta_id)
            if respuesta.get('error'):
                raise ValueError(respuesta.get('mensaje', 'No se pudo actualizar la venta.'))
            if centro_acopio_id:
                venta.centro_acopio_id = centro_acopio_id
                venta.save(update_fields=['centro_acopio'])
            else:
                venta.centro_acopio = None
                venta.save(update_fields=['centro_acopio'])
            messages.success(request, 'Venta actualizada correctamente.')
            return redirect('operations:listar_ventas_admin')
        except Exception as e:
            inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
            centros_acopio = CentroAcopio.objects.all()
            context = {
                'venta': venta,
                'error': str(e),
                'inventarios': inventarios,
                'centros_acopio': centros_acopio,
            }
            return render(request, 'admin/operaciones/venta_editar.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def eliminar_venta_admin(request, venta_id):
    """Elimina una venta de inventario."""
    venta = get_object_or_404(models.VentaInventario, id=venta_id)
    
    if request.method == 'GET':
        context = {
            'venta': venta,
        }
        return render(request, 'admin/operaciones/venta_eliminar.html', context)
    
    elif request.method == 'POST':
        try:
            respuesta = VentaInventarioService.borrar_venta(request, venta_id)
            if respuesta.get('error'):
                raise ValueError(respuesta.get('mensaje', 'No se pudo eliminar la venta.'))
            messages.success(request, 'Venta eliminada correctamente.')
            return redirect('operations:listar_ventas_admin')
        except Exception as e:
            context = {
                'venta': venta,
                'error': str(e),
            }
            return render(request, 'admin/operaciones/venta_eliminar.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def nueva_operacion(request):
    """Página para seleccionar tipo de operación (compra o venta)."""
    context = {}
    return render(request, 'admin/operaciones/nueva_operacion.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def estadisticas_operaciones(request):
    """Muestra estadísticas de compras y ventas."""
    compras = models.CompraInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca'
    ).all()
    
    ventas = models.VentaInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca',
        'centro_acopio'
    ).all()
    
    # Agrupar por mes para gráficos
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    
    estadisticas_por_mes = {}
    
    # Compras por mes
    compras_por_mes = compras.annotate(
        mes=TruncMonth('fecha_compra')
    ).values('mes').annotate(
        total_cantidad=Sum('cantidad'),
        total_costo=Sum(models.F('cantidad') * models.F('precio_compra'), output_field=models.DecimalField()),
        cantidad_transacciones=Count('id')
    ).order_by('mes')
    
    # Ventas por mes
    ventas_por_mes = ventas.annotate(
        mes=TruncMonth('fecha_venta')
    ).values('mes').annotate(
        total_cantidad=Sum('cantidad'),
        total_ingresos=Sum(models.F('cantidad') * models.F('precio_venta'), output_field=models.DecimalField()),
        cantidad_transacciones=Count('id')
    ).order_by('mes')
    
    context = {
        'compras_por_mes': compras_por_mes,
        'ventas_por_mes': ventas_por_mes,
        'total_compras': compras.count(),
        'total_ventas': ventas.count(),
        'total_costo_compras': sum((c.cantidad or 0) * (c.precio_compra or 0) for c in compras),
        'total_ingresos_ventas': sum((v.cantidad or 0) * (v.precio_venta or 0) for v in ventas),
    }
    
    return render(request, 'admin/operaciones/estadisticas.html', context)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def operaciones_criticas(request):
    """Muestra operaciones con alertas o problemas."""
    # Compras con stock resultante negativo
    compras_criticas = []
    compras = models.CompraInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca'
    ).all()
    
    for compra in compras:
        # Calcular stock resultante considerando otras operaciones
        stock_inicial = compra.inventario.stock_actual or 0
        if (stock_inicial - (compra.cantidad or 0)) < 0:
            compras_criticas.append(compra)
    
    # Ventas con stock insuficiente
    ventas_criticas = []
    ventas = models.VentaInventario.objects.select_related(
        'inventario__material',
        'inventario__punto_eca',
        'centro_acopio'
    ).all()
    
    for venta in ventas:
        stock_disponible = venta.inventario.stock_actual or 0
        if stock_disponible < (venta.cantidad or 0):
            ventas_criticas.append(venta)
    
    context = {
        'compras_criticas': compras_criticas,
        'ventas_criticas': ventas_criticas,
        'total_compras_criticas': len(compras_criticas),
        'total_ventas_criticas': len(ventas_criticas),
    }
    
    return render(request, 'admin/operaciones/criticos.html', context)
