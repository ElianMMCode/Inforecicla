from django.contrib import admin
from .models import Inventario, Material, CategoriaMaterial, TipoMaterial
# Register your models here.
admin.site.register(Inventario)
admin.site.register(Material)
admin.site.register(CategoriaMaterial)
admin.site.register(TipoMaterial)