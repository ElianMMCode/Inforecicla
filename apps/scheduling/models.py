from django.db import models
from config.base_models import CreacionModificacionModel
from django.utils import timezone


class Evento(CreacionModificacionModel):
    # Relaciones
    material = models.ForeignKey(
        "inventory.Material", on_delete=models.PROTECT, related_name="eventos"
    )
    centro_acopio = models.ForeignKey(
        "ecas.CentroAcopio",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos",
    )
    punto_eca = models.ForeignKey(
        "ecas.PuntoECA", on_delete=models.PROTECT, related_name="eventos"
    )
    usuario = models.ForeignKey(
        "users.Usuario", on_delete=models.PROTECT, related_name="eventos"
    )
    # Información de calendario
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    color = models.CharField(max_length=7, blank=True)
    # Configuración de repetición
    tipo_repeticion = models.CharField(
        max_length=15,
        choices=[
            ("NINGUNA", "Ninguna"),
            ("DIARIA", "Diaria"),
            ("SEMANAL", "Semanal"),
            ("MENSUAL", "Mensual"),
            # Agregar más si corresponde
        ],
        null=True,
        blank=True,
    )
    fecha_fin_repeticion = models.DateTimeField(null=True, blank=True)
    es_evento_generado = models.BooleanField(default=False)

    class Meta(CreacionModificacionModel.Meta):
        db_table = "evento"

    def generar_titulo(self):
        if self.material and hasattr(self.material, "descripcion"):
            self.titulo = f"{self.material.descripcion} - Venta"

    def generar_descripcion(self):
        desc = f"Material: {getattr(self.material, 'descripcion', '')}\n"
        if self.centro_acopio and hasattr(self.centro_acopio, "nombre"):
            desc += f"Centro de Acopio: {self.centro_acopio.nombre}\n"
        self.descripcion = desc

    def asignar_color_por_material(self):
        if self.material and hasattr(self.material, "tipo_material"):
            self.color = "#28a745"  # Verde Inforecicla por defecto


class EventoInstancia(CreacionModificacionModel):
    evento_base = models.ForeignKey(
        "scheduling.Evento", on_delete=models.PROTECT, related_name="instancias"
    )
    punto_eca = models.ForeignKey(
        "ecas.PuntoECA", on_delete=models.PROTECT, related_name="instancias_evento"
    )
    usuario = models.ForeignKey(
        "users.Usuario", on_delete=models.PROTECT, related_name="instancias_evento"
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    numero_repeticion = models.IntegerField(null=True, blank=True)
    es_completado = models.BooleanField(default=False)
    completado_en = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    def marcar_completada(self):
        self.es_completado = True
        self.completado_en = timezone.now()
        self.save(update_fields=["es_completado", "completado_en"])

    def desmarcar_completada(self):
        self.es_completado = False
        self.completado_en = None
        self.save(update_fields=["es_completado", "completado_en"])

    def dias_desde_creacion(self):
        if self.fecha_creacion:
            return (timezone.now() - self.fecha_creacion).days
        return None

    class Meta(CreacionModificacionModel.Meta):
        db_table = "evento_instancia"
