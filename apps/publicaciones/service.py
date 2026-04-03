from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.http import Http404

from config import constants

from .models import CategoriaPublicacion, Publicacion


class PublicacionService:
    @staticmethod
    def _base_queryset():
        return (
            Publicacion.objects.filter(estado=constants.Estado.ACTIVO)
            .select_related("usuario", "categoria")
            .prefetch_related("comentarios__usuario", "reacciones")
            .annotate(
                likes_count=Count(
                    "reacciones",
                    filter=Q(reacciones__valor=constants.Votos.LIKE),
                    distinct=True,
                ),
                dislikes_count=Count(
                    "reacciones",
                    filter=Q(reacciones__valor=constants.Votos.DISLIKE),
                    distinct=True,
                ),
                comentarios_total=Count("comentarios", distinct=True),
            )
        )

    @classmethod
    def list_for_panel(cls, request):
        queryset = cls._base_queryset()

        query = (request.GET.get("q") or "").strip()
        categoria_id = request.GET.get("categoria")
        orden = request.GET.get("orden") or "recientes"

        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query)
                | Q(contenido__icontains=query)
                | Q(usuario__nombres__icontains=query)
                | Q(usuario__apellidos__icontains=query)
            )

        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        if orden == "valorados":
            queryset = queryset.order_by("-likes_count", "-fecha_creacion")
        elif orden == "comentados":
            queryset = queryset.order_by("-comentarios_total", "-fecha_creacion")
        else:
            queryset = queryset.order_by("-fecha_creacion")

        paginator = Paginator(queryset, 6)
        publicaciones = paginator.get_page(request.GET.get("page"))

        publicacion_id = request.GET.get("publicacion")
        publicacion_destacada = None
        if publicacion_id:
            publicacion_destacada = queryset.filter(pk=publicacion_id).first()
        if publicacion_destacada is None:
            publicacion_destacada = queryset.first()

        return {
            "publicaciones": publicaciones,
            "categorias": CategoriaPublicacion.objects.order_by("tipo"),
            "publicacion_destacada": publicacion_destacada,
            "filtros": {
                "q": query,
                "categoria": categoria_id or "",
                "orden": orden,
            },
        }

    @classmethod
    def get_detail_context(cls, publicacion_id):
        # Verificar si existe pero no está activa → 404
        try:
            pub = Publicacion.objects.get(pk=publicacion_id)
        except Publicacion.DoesNotExist:
            raise Http404
        if pub.estado != constants.Estado.ACTIVO:
            raise Http404
        publicacion = get_object_or_404(cls._base_queryset(), pk=publicacion_id)
        publicaciones_relacionadas = (
            cls._base_queryset()
            .exclude(pk=publicacion.pk)
            .order_by("-fecha_creacion")[:3]
        )
        return {
            "publicacion": publicacion,
            "publicaciones_relacionadas": publicaciones_relacionadas,
        }
        