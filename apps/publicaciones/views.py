from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

_COMENTARIO_MIN = 1
_COMENTARIO_MAX = 1000

# Create your views here.
def publicacion(request):
    return render(request, "publicacion/panel_publicaciones.html")
from .service import PublicacionService


def panel_publicaciones(request):
    return render(
        request,
        "publicacion/panel_publicaciones.html",
        PublicacionService.list_for_panel(request),
    )


def publicacion(request, publicacion_id):
    from .models import Reaccion, Guardados
    context = PublicacionService.get_detail_context(publicacion_id)
    if request.user.is_authenticated:
        context["mi_reaccion"] = Reaccion.objects.filter(
            publicacion_id=publicacion_id, usuario=request.user
        ).values_list("valor", flat=True).first()
        context["mi_guardado"] = Guardados.objects.filter(
            publicacion_id=publicacion_id, usuario=request.user
        ).exists()
    return render(request, "publicacion/publicacion.html", context)


@login_required
def toggle_guardado(request, publicacion_id):
    if request.method == "POST":
        from .models import Guardados, Publicacion
        pub = get_object_or_404(Publicacion, pk=publicacion_id)
        guardado = Guardados.objects.filter(usuario=request.user, publicacion=pub).first()
        if guardado:
            guardado.delete()
        else:
            Guardados.objects.create(usuario=request.user, publicacion=pub)
    return redirect("publicacion:detalle_publicacion", publicacion_id=publicacion_id)


@login_required
def agregar_comentario(request, publicacion_id):
    if request.method == "POST":
        from .models import Comentario, Publicacion
        pub = get_object_or_404(Publicacion, pk=publicacion_id)
        texto = request.POST.get("texto", "").strip()
        if not texto or len(texto) < _COMENTARIO_MIN:
            messages.error(request, "El comentario no puede estar vacío.")
        elif len(texto) > _COMENTARIO_MAX:
            messages.error(request, f"El comentario no puede superar los {_COMENTARIO_MAX} caracteres.")
        else:
            Comentario.objects.create(
                usuario=request.user,
                publicacion=pub,
                texto=texto,
            )
    return redirect("publicacion:detalle_publicacion", publicacion_id=publicacion_id)


@login_required
def editar_comentario(request, comentario_id):
    from .models import Comentario
    comentario = get_object_or_404(Comentario, pk=comentario_id)
    if comentario.usuario != request.user:
        return redirect("publicacion:detalle_publicacion", publicacion_id=comentario.publicacion_id)
    if request.method == "POST":
        texto = request.POST.get("texto", "").strip()
        if not texto or len(texto) < _COMENTARIO_MIN:
            messages.error(request, "El comentario no puede estar vacío.")
        elif len(texto) > _COMENTARIO_MAX:
            messages.error(request, f"El comentario no puede superar los {_COMENTARIO_MAX} caracteres.")
        else:
            comentario.texto = texto
            comentario.save()
    return redirect("publicacion:detalle_publicacion", publicacion_id=comentario.publicacion_id)


@login_required
def eliminar_comentario(request, comentario_id):
    from .models import Comentario
    comentario = get_object_or_404(Comentario, pk=comentario_id)
    if comentario.usuario != request.user:
        return redirect("publicacion:detalle_publicacion", publicacion_id=comentario.publicacion_id)
    if request.method == "POST":
        publicacion_id = comentario.publicacion_id
        comentario.delete()
        return redirect("publicacion:detalle_publicacion", publicacion_id=publicacion_id)
    return redirect("publicacion:detalle_publicacion", publicacion_id=comentario.publicacion_id)


@login_required
def votar_publicacion(request, publicacion_id):
    if request.method == "POST":
        from .models import Reaccion, Publicacion
        from config.constants import Votos
        valor = request.POST.get("valor")
        if valor in (Votos.LIKE, Votos.DISLIKE):
            pub = get_object_or_404(Publicacion, pk=publicacion_id)
            reaccion = Reaccion.objects.filter(publicacion=pub, usuario=request.user).first()
            if reaccion:
                if reaccion.valor == valor:
                    reaccion.delete()
                else:
                    reaccion.valor = valor
                    reaccion.save()
            else:
                Reaccion.objects.create(publicacion=pub, usuario=request.user, valor=valor)
    return redirect("publicacion:detalle_publicacion", publicacion_id=publicacion_id)