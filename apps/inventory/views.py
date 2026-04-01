from django.views.decorators.http import require_POST, require_http_methods, require_GET
from apps.inventory.models import Inventario
from config import constants as cons
from apps.inventory.service import InventoryService
from apps.ecas.constants import SECTION_TEMPLATES
from django.http import JsonResponse
import json


def _build_materiales_context(punto):
    """
    Construye el contexto por defecto para las demás secciones.
    """

    materiales_inventario = list(
        Inventario.objects.filter(punto_eca=punto).order_by("-fecha_modificacion")
    )

    total_stock = sum(float(inv.stock_actual) for inv in materiales_inventario)
    total_capacidad = sum(float(inv.capacidad_maxima) for inv in materiales_inventario)

    total_ok = sum(
        1
        for inv in materiales_inventario
        if float(inv.ocupacion_actual) < float(inv.umbral_alerta)
    )
    total_alerta = sum(
        1
        for inv in materiales_inventario
        if float(inv.ocupacion_actual) >= float(inv.umbral_alerta)
        and float(inv.ocupacion_actual) < float(inv.umbral_critico)
    )
    total_critico = sum(
        1
        for inv in materiales_inventario
        if float(inv.ocupacion_actual) >= float(inv.umbral_critico)
    )

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
        material_mayor_ocupacion = max(
            materiales_inventario, key=lambda i: float(i.ocupacion_actual)
        )
        # Material más caro
        material_mas_caro = max(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        )
        # Material más barato
        material_mas_barato = min(
            materiales_inventario, key=lambda i: float(i.precio_compra or 0)
        )
        # Costo total inventario
        costo_total_inventario = sum(
            float(i.stock_actual) * float(i.precio_compra or 0)
            for i in materiales_inventario
        )
        # Materiales en estado crítico
        materiales_criticos = [
            i
            for i in materiales_inventario
            if float(i.ocupacion_actual) >= float(i.umbral_critico)
        ]

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


@require_GET
def buscar_materiales_catalogo_view(request):
    try:
        punto_id = request.GET.get("puntoId", "").strip()
        query = request.GET.get("texto", "").strip()
        categoria = request.GET.get("categoria", "").strip()
        tipo = request.GET.get("tipo", "").strip()

        resultados = InventoryService.buscar_materiales_fuera_inventario(
            punto_id=punto_id, query=query, categoria=categoria, tipo=tipo
        )
        return JsonResponse(resultados, safe=False)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@require_POST
def agregar_al_inventario_view(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de pebtición JSON inválido"}, status=400
            )
    try:
        response = InventoryService.crear_inventario(data)
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@require_GET
def detalle_iventario_view(request, punto_id, inventario_id):
    try:
        data = InventoryService.detalle_material_inventario(punto_id, inventario_id)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse(
            {"mensaje": f"Error técnico: {str(e)}", "error": True}, status=400
        )


@require_http_methods(["POST"])
def actualizar_inventario_view(request, inventario_id):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de petición JSON inválido"}, status=400
            )
    response_data = InventoryService.actualizar_inventario(inventario_id, data)
    return JsonResponse(response_data, safe=False)


@require_GET
def buscar_materiales_inventario_view(request):
    filtros = {c: v.strip() for c, v in request.GET.items()}
    data = {}
    if request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error", "Cuerpo de petición JSON inválido"}, status=400
            )
    parametros_busqueda = {**filtros, **data}
    resultados = InventoryService.buscar_materiales_dentro_inventario(
        parametros_busqueda
    )
    return JsonResponse(resultados, safe=False)


@require_http_methods(["DELETE"])
def eliminar_inventario_view(request, inventario_id):
    resp = InventoryService.eliminar_material_inventario(inventario_id)
    return JsonResponse(resp)


# ===== VISTAS ADMIN PANEL =====

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.ecas.models import PuntoECA
from apps.inventory.models import Material

def es_administrador(user):
    from config.constants import TipoUsuario
    if not user.is_authenticated:
        return False
    return bool(user.is_staff or user.is_superuser or user.tipo_usuario == TipoUsuario.ADMIN)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def dashboard_inventario(request):
    """Dashboard principal de inventarios con estadísticas generales"""
    inventarios = Inventario.objects.select_related('material', 'punto_eca', 'material__categoria', 'material__tipo').all()
    estadisticas_por_punto = {}
    for inv in inventarios:
        punto_nombre = inv.punto_eca.nombre
        if punto_nombre not in estadisticas_por_punto:
            estadisticas_por_punto[punto_nombre] = {
                'total_stock': 0,
                'capacidad': 0,
                'ocupacion': 0,
            }
        estadisticas_por_punto[punto_nombre]['total_stock'] += float(inv.stock_actual or 0)
        estadisticas_por_punto[punto_nombre]['capacidad'] += float(inv.capacidad_maxima or 0)

    for punto in estadisticas_por_punto:
        if estadisticas_por_punto[punto]['capacidad'] > 0:
            estadisticas_por_punto[punto]['ocupacion'] = (
                estadisticas_por_punto[punto]['total_stock'] /
                estadisticas_por_punto[punto]['capacidad'] * 100
            )
    
    contexto = {
        'inventarios': inventarios,
        'total_inventarios': inventarios.count(),
        'total_stock': sum(float(inv.stock_actual or 0) for inv in inventarios),
        'total_capacidad': sum(float(inv.capacidad_maxima or 0) for inv in inventarios),
        'inventarios_criticos': sum(1 for inv in inventarios if float(inv.ocupacion_actual or 0) >= float(inv.umbral_critico or 0)),
        'estadisticas_por_punto': estadisticas_por_punto,
    }
    return render(request, 'admin/inventario/dashboard.html', contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def crear_inventario_admin(request):
    """Crear nuevo inventario desde admin"""
    puntos = PuntoECA.objects.all()
    materiales = Material.objects.all()
    
    error = None
    if request.method == 'POST':
        try:
            punto_eca_id = request.POST.get('punto_eca_id')
            material_id = request.POST.get('material_id')
            stock_actual = float(request.POST.get('stock_actual', 0) or 0)
            capacidad_maxima = float(request.POST.get('capacidad_maxima', 0) or 0)
            umbral_alerta = int(float(request.POST.get('umbral_alerta', 60) or 60))
            umbral_critico = int(float(request.POST.get('umbral_critico', 80) or 80))

            if not punto_eca_id or not material_id:
                raise ValueError('Debes seleccionar punto ECA y material.')

            if capacidad_maxima <= 0:
                raise ValueError('La capacidad máxima debe ser mayor a 0.')

            if stock_actual < 0:
                raise ValueError('El stock actual no puede ser negativo.')

            if not (0 <= umbral_alerta <= 100 and 0 <= umbral_critico <= 100):
                raise ValueError('Los umbrales deben estar entre 0 y 100.')

            if umbral_alerta >= umbral_critico:
                raise ValueError('El umbral de alerta debe ser menor al umbral crítico.')

            if Inventario.objects.filter(punto_eca_id=punto_eca_id, material_id=material_id).exists():
                raise ValueError('Ya existe un inventario para ese material en el punto ECA seleccionado.')

            punto = get_object_or_404(PuntoECA, id=punto_eca_id)
            material = get_object_or_404(Material, id=material_id)

            Inventario.objects.create(
                punto_eca=punto,
                material=material,
                stock_actual=stock_actual,
                capacidad_maxima=capacidad_maxima,
                unidad_medida=cons.UnidadMedida.KG,
                umbral_alerta=umbral_alerta,
                umbral_critico=umbral_critico,
            )
            messages.success(request, 'Inventario creado correctamente.')
            return redirect('inventory:listar_inventarios')
        except Exception as e:
            error = str(e)
            messages.error(request, f'No se pudo crear el inventario: {error}')
    
    contexto = {
        'puntos': puntos,
        'materiales': materiales,
        'error': error,
    }
    return render(request, 'admin/inventario/crear.html', contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def editar_inventario_admin(request, inventario_id):
    """Editar inventario existente desde admin"""
    inventario = get_object_or_404(Inventario, id=inventario_id)
    puntos = PuntoECA.objects.all()
    materiales = Material.objects.all()
    
    error = None
    if request.method == 'POST':
        try:
            stock_actual = float(request.POST.get('stock_actual', inventario.stock_actual) or inventario.stock_actual)
            capacidad_maxima = float(request.POST.get('capacidad_maxima', inventario.capacidad_maxima) or inventario.capacidad_maxima)
            umbral_alerta = int(float(request.POST.get('umbral_alerta', inventario.umbral_alerta) or inventario.umbral_alerta))
            umbral_critico = int(float(request.POST.get('umbral_critico', inventario.umbral_critico) or inventario.umbral_critico))

            if capacidad_maxima <= 0:
                raise ValueError('La capacidad máxima debe ser mayor a 0.')

            if stock_actual < 0:
                raise ValueError('El stock actual no puede ser negativo.')

            if not (0 <= umbral_alerta <= 100 and 0 <= umbral_critico <= 100):
                raise ValueError('Los umbrales deben estar entre 0 y 100.')

            if umbral_alerta >= umbral_critico:
                raise ValueError('El umbral de alerta debe ser menor al umbral crítico.')

            inventario.stock_actual = stock_actual
            inventario.capacidad_maxima = capacidad_maxima
            inventario.umbral_alerta = umbral_alerta
            inventario.umbral_critico = umbral_critico
            inventario.save()

            messages.success(request, 'Inventario actualizado correctamente.')
            return redirect('inventory:listar_inventarios')
        except Exception as e:
            error = str(e)
            messages.error(request, f'No se pudo actualizar el inventario: {error}')
    
    contexto = {
        'inventario': inventario,
        'puntos': puntos,
        'materiales': materiales,
        'error': error,
    }
    return render(request, 'admin/inventario/editar.html', contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def detalle_inventario_admin(request, inventario_id):
    """Detalle de un inventario específico"""
    inventario = get_object_or_404(Inventario, id=inventario_id)
    return render(request, 'admin/inventario/detalle.html', {'inventario': inventario})


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def eliminar_inventario_admin(request, inventario_id):
    """Eliminar inventario"""
    inventario = get_object_or_404(Inventario, id=inventario_id)
    if request.method == 'POST':
        try:
            inventario.delete()
            messages.success(request, 'Inventario eliminado correctamente.')
            return redirect('inventory:listar_inventarios')
        except Exception as e:
            messages.error(request, f'No se pudo eliminar el inventario: {str(e)}')
    return render(request, 'admin/inventario/eliminar.html', {'inventario': inventario})


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def estadisticas_inventario(request):
    """Estadísticas de inventario con gráficos y análisis"""
    inventarios = Inventario.objects.select_related('material', 'punto_eca').all()
    
    # Estadísticas por punto ECA
    estadisticas_por_punto = {}
    for inv in inventarios:
        punto_nombre = inv.punto_eca.nombre
        if punto_nombre not in estadisticas_por_punto:
            estadisticas_por_punto[punto_nombre] = {
                'total_stock': 0,
                'capacidad': 0,
                'ocupacion': 0,
            }
        estadisticas_por_punto[punto_nombre]['total_stock'] += float(inv.stock_actual or 0)
        estadisticas_por_punto[punto_nombre]['capacidad'] += float(inv.capacidad_maxima or 0)
    
    # Calcular ocupación por punto
    for punto in estadisticas_por_punto:
        if estadisticas_por_punto[punto]['capacidad'] > 0:
            estadisticas_por_punto[punto]['ocupacion'] = (
                estadisticas_por_punto[punto]['total_stock'] / 
                estadisticas_por_punto[punto]['capacidad'] * 100
            )
    
    contexto = {
        'inventarios': inventarios,
        'estadisticas_por_punto': estadisticas_por_punto,
        'total_stock': sum(float(inv.stock_actual or 0) for inv in inventarios),
        'total_capacidad': sum(float(inv.capacidad_maxima or 0) for inv in inventarios),
    }
    return render(request, 'admin/inventario/estadisticas.html', contexto)


@login_required(login_url="/login/")
@user_passes_test(es_administrador, login_url="/inicio/")
def materiales_criticos(request):
    """Mostrar materiales en estado crítico"""
    inventarios_criticos = Inventario.objects.filter().select_related('material', 'punto_eca')
    
    # Filtrar solo los críticos
    criticos = [
        inv for inv in inventarios_criticos 
        if float(inv.ocupacion_actual or 0) >= float(inv.umbral_critico or 0)
    ]
    
    contexto = {
        'inventarios_criticos': criticos,
        'total_criticos': len(criticos),
    }
    return render(request, 'admin/inventario/criticos.html', contexto)
