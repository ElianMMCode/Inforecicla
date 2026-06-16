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
            .prefetch_related("comentarios__usuario", "reacciones", "imagenes")
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
    def _filter_queryset(cls, queryset, request):
        query = (request.GET.get("q") or "").strip()
        categoria_id = request.GET.get("categoria")
        orden = request.GET.get("orden") or "recientes"
        solo_destacados = request.GET.get("destacados") == "1"

        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query)
                | Q(contenido__icontains=query)
                | Q(usuario__nombres__icontains=query)
                | Q(usuario__apellidos__icontains=query)
            )

        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        if solo_destacados:
            queryset = queryset.filter(es_destacado=True)

        if orden == "valorados":
            queryset = queryset.order_by("-likes_count", "-fecha_creacion")
        elif orden == "comentados":
            queryset = queryset.order_by("-comentarios_total", "-fecha_creacion")
        elif orden == "destacados":
            queryset = queryset.order_by("-es_destacado", "-fecha_creacion")
        else:
            queryset = queryset.order_by("-fecha_creacion")

        filtros = {
            "q": query,
            "categoria": categoria_id or "",
            "orden": orden,
            "destacados": "1" if solo_destacados else "",
        }
        return queryset, filtros

    @classmethod
    def list_for_panel(cls, request):
        queryset = cls._base_queryset()
        queryset, filtros = cls._filter_queryset(queryset, request)

        paginator = Paginator(queryset, 6)
        publicaciones = paginator.get_page(request.GET.get("page"))
        publicaciones_destacadas = cls._base_queryset().filter(es_destacado=True)[:5]

        return {
            "publicaciones": publicaciones,
            "total_pages": paginator.num_pages,
            "categorias": CategoriaPublicacion.objects.order_by("nombre", "tipo"),
            "publicaciones_destacadas": publicaciones_destacadas,
            "filtros": filtros,
        }

    @classmethod
    def ajax_cards(cls, request):
        from django.template.loader import render_to_string

        queryset = cls._base_queryset()
        queryset, _ = cls._filter_queryset(queryset, request)

        paginator = Paginator(queryset, 6)
        page = paginator.get_page(request.GET.get("page"))

        html = render_to_string(
            "publicacion/_publicacion_cards.html",
            {"publicaciones": page},
            request=request,
        )

        return {"html": html, "has_next": page.has_next(), "page": page.number}

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
        