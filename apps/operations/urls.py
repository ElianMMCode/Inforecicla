from django.urls import path
from . import views

app_name = "operations"

urlpatterns = [
    # ===== ADMIN PANEL - Gestión de Operaciones =====
    path('admin/', views.dashboard_operaciones, name='listar_operaciones'),
    path('admin/dashboard/', views.dashboard_operaciones, name='dashboard_operaciones'),
    
    # Compras
    path('admin/compras/', views.listar_compras_admin, name='listar_compras_admin'),
    path('admin/compras/crear/', views.crear_compra_admin, name='crear_compra_admin'),
    path('admin/compras/<uuid:compra_id>/editar/', views.editar_compra_admin, name='editar_compra_admin'),
    path('admin/compras/<uuid:compra_id>/eliminar/', views.eliminar_compra_admin, name='eliminar_compra_admin'),
    
    # Ventas
    path('admin/ventas/', views.listar_ventas_admin, name='listar_ventas_admin'),
    path('admin/ventas/crear/', views.crear_venta_admin, name='crear_venta_admin'),
    path('admin/ventas/<uuid:venta_id>/editar/', views.editar_venta_admin, name='editar_venta_admin'),
    path('admin/ventas/<uuid:venta_id>/eliminar/', views.eliminar_venta_admin, name='eliminar_venta_admin'),
    
    # Nueva operación (seleccionar tipo)
    path('admin/nueva/', views.nueva_operacion, name='nueva_operacion'),
    
    # Estadísticas y reportes
    path('admin/estadisticas/', views.estadisticas_operaciones, name='estadisticas_operaciones'),
    path('admin/criticos/', views.operaciones_criticas, name='operaciones_criticas'),
    
    # ===== API REST para Punto ECA (endpoints existentes) =====
    path(
        "registrar-compra/",
        views.registros_compras,
        name="registrar_entrada",
    ),
    path(
        "registrar-venta/",
        views.registros_ventas,
        name="registrar_venta",
    ),
    path(
        "editar-compra/<uuid:compra_id>/",
        views.editar_compra,
        name="editar_compra_api",
    ),
    path(
        "editar-venta/<uuid:venta_id>/",
        views.editar_venta,
        name="editar_venta_api",
    ),
    path(
        "borrar-compra/<uuid:compra_id>/",
        views.borrar_compra,
        name="borrar_compra",
    ),
    path(
        "borrar-venta/<uuid:venta_id>/",
        views.borrar_venta,
        name="borrar_venta",
    ),
    # === Exportar a Excel/PDF ===
    path(
        "exportar-compras-excel/",
        views.exportar_compras_excel,
        name="exportar_compras_excel",
    ),
    path(
        "exportar-compras-pdf/",
        views.exportar_compras_pdf,
        name="exportar_compras_pdf",
    ),
    path(
        "exportar-ventas-excel/",
        views.exportar_ventas_excel,
        name="exportar_ventas_excel",
    ),
    path(
        "exportar-ventas-pdf/",
        views.exportar_ventas_pdf,
        name="exportar_ventas_pdf",
    ),
    path(
        "exportar-historial-excel/",
        views.exportar_historial_excel,
        name="exportar_historial_excel",
    ),
    path(
        "exportar-historial-pdf/",
        views.exportar_historial_pdf,
        name="exportar_historial_pdf",
    ),
]
