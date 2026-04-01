from django.urls import path

from . import views

app_name = "publicaciones"

urlpatterns = [
    path("", views.listar_publicaciones, name="list_publicaciones"),
    path("crear/", views.crear_publicacion, name="create_publicacion"),
    path("<uuid:publicacion_id>/editar/", views.editar_publicacion, name="edit_publicacion"),
    path("<uuid:publicacion_id>/eliminar/", views.eliminar_publicacion, name="delete_publicacion"),
]
