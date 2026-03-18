from django.shortcuts import render

# Create your views here.
def publicacion(request):
    return render(request, "publicacion/panel_publicaciones.html")