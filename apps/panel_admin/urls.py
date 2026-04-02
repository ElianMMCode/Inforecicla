from django.urls import path
from . import views

app_name = 'panel_admin'

urlpatterns = [
    path('', views.admin, name="panel_admin"),

    # Usuarios
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('usuarios/exportar/pdf/', views.exportar_usuarios_pdf, name='exportar_usuarios_pdf'),
    path('usuarios/exportar/excel/', views.exportar_usuarios_excel, name='exportar_usuarios_excel'),
    path('usuarios/importar/csv/', views.importar_usuarios_csv, name='importar_usuarios_csv'),
    path('usuarios/<uuid:usuario_id>/editar/', views.editar_usuario_admin, name='editar_usuario_admin'),

    # Publicaciones
    path('publicaciones/', views.listar_publicaciones_admin, name='listar_publicaciones_admin'),
    path('publicaciones/crear/', views.crear_publicacion_admin, name='crear_publicacion_admin'),
    path('publicaciones/<uuid:publicacion_id>/editar/', views.editar_publicacion_admin, name='editar_publicacion_admin'),

    # Puntos ECA
    path('puntos-eca/', views.listar_puntos_eca_admin, name='listar_puntos_eca_admin'),
    path('puntos-eca/crear/', views.crear_punto_eca_admin, name='crear_punto_eca_admin'),
    path('puntos-eca/exportar/pdf/', views.exportar_puntos_eca_pdf, name='exportar_puntos_eca_pdf'),
    path('puntos-eca/exportar/excel/', views.exportar_puntos_eca_excel, name='exportar_puntos_eca_excel'),
    path('puntos-eca/<uuid:punto_id>/editar/', views.editar_punto_eca_admin, name='editar_punto_eca_admin'),

    # Materiales
    path('materiales/', views.listar_materiales_admin, name='listar_materiales_admin'),
    path('materiales/exportar/pdf/', views.exportar_materiales_pdf, name='exportar_materiales_pdf'),
    path('materiales/exportar/excel/', views.exportar_materiales_excel, name='exportar_materiales_excel'),
    path('materiales/<uuid:material_id>/editar/', views.editar_material_admin, name='editar_material_admin'),

    # Categorías de materiales
    path('categorias-materiales/', views.listar_categorias_material_admin, name='listar_categorias_material_admin'),
    path('categorias-materiales/exportar/pdf/', views.exportar_categorias_material_pdf, name='exportar_categorias_material_pdf'),
    path('categorias-materiales/exportar/excel/', views.exportar_categorias_material_excel, name='exportar_categorias_material_excel'),
    path('categorias-materiales/crear/', views.crear_categoria_material, name='crear_categoria_material'),
    path('categorias-materiales/<uuid:categoria_id>/editar/', views.editar_categoria_material_admin, name='editar_categoria_material_admin'),

    # Categorías de publicaciones
    path('categorias-publicaciones/', views.listar_categorias_publicacion_admin, name='listar_categorias_publicacion_admin'),
    path('categorias-publicaciones/exportar/pdf/', views.exportar_categorias_publicacion_pdf, name='exportar_categorias_publicacion_pdf'),
    path('categorias-publicaciones/exportar/excel/', views.exportar_categorias_publicacion_excel, name='exportar_categorias_publicacion_excel'),
    path('categorias-publicaciones/crear/', views.crear_categoria_publicacion, name='crear_categoria_publicacion'),
    path('categorias-publicaciones/<uuid:categoria_id>/editar/', views.editar_categoria_publicacion_admin, name='editar_categoria_publicacion_admin'),

    # Tipos de materiales
    path('tipos-materiales/', views.listar_tipos_material_admin, name='listar_tipos_material_admin'),
    path('tipos-materiales/exportar/pdf/', views.exportar_tipos_material_pdf, name='exportar_tipos_material_pdf'),
    path('tipos-materiales/exportar/excel/', views.exportar_tipos_material_excel, name='exportar_tipos_material_excel'),
    path('tipos-materiales/crear/', views.crear_tipo_material, name='crear_tipo_material'),
    path('tipos-materiales/<uuid:tipo_id>/editar/', views.editar_tipo_material_admin, name='editar_tipo_material_admin'),
]
