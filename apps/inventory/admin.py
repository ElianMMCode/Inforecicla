from django.contrib import admin
from .models import Inventario, Material, CategoriaMaterial
# Register your models here.
admin.site.register(Inventario)
admin.site.register(Material)
admin.site.register(CategoriaMaterial)