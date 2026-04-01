from django.urls import path
from . import views

app_name = "publicacion"

urlpatterns = [
    path("", views.panel_publicaciones, name="publicaciones"),
    path("panel/", views.panel_publicaciones, name="panel_publicaciones"),
    path("<uuid:publicacion_id>/", views.publicacion, name="detalle_publicacion"),
    path("<uuid:publicacion_id>/comentar/", views.agregar_comentario, name="agregar_comentario"),
    path("<uuid:publicacion_id>/votar/", views.votar_publicacion, name="votar_publicacion"),
    path("comentario/<uuid:comentario_id>/editar/", views.editar_comentario, name="editar_comentario"),
    path("comentario/<uuid:comentario_id>/eliminar/", views.eliminar_comentario, name="eliminar_comentario"),
]
