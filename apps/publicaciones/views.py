from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

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
    from .models import Reaccion
    context = PublicacionService.get_detail_context(publicacion_id)
    if request.user.is_authenticated:
        context["mi_reaccion"] = Reaccion.objects.filter(
            publicacion_id=publicacion_id, usuario=request.user
        ).values_list("valor", flat=True).first()
    return render(request, "publicacion/publicacion.html", context)


@login_required
def agregar_comentario(request, publicacion_id):
    if request.method == "POST":
        from .models import Comentario, Publicacion
        pub = get_object_or_404(Publicacion, pk=publicacion_id)
        texto = request.POST.get("texto", "").strip()
        if texto:
            Comentario.objects.create(
                usuario=request.user,
                publicacion=pub,
                texto=texto,
            )
    return redirect("publicacion:detalle_publicacion", publicacion_id=publicacion_id)


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