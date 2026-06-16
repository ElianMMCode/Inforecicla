import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Dashboard(models.Model):
    """Model representing an admin dashboard"""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    es_publico = models.BooleanField(default=False)
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboards')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tablero"
        verbose_name_plural = "Tableros"
        db_table = "adm_tablero"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre


class Widget(models.Model):
    """Model representing a widget within a dashboard"""
    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('metric', 'Metric'),
        ('text', 'Text'),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    titulo = models.CharField(max_length=200)
    tipo_widget = models.CharField(max_length=20, choices=WIDGET_TYPES)
    posicion_x = models.IntegerField(default=0)  # Grid position
    posicion_y = models.IntegerField(default=0)  # Grid position
    ancho = models.IntegerField(default=1)  # Grid columns
    alto = models.IntegerField(default=1)  # Grid rows
    configuracion = models.JSONField(default=dict, blank=True)  # Widget-specific configuration
    dashboard = models.ForeignKey('Dashboard', on_delete=models.CASCADE, related_name='widgets')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Widget"
        verbose_name_plural = "Widgets"
        db_table = "adm_widget"
        ordering = ['posicion_y', 'posicion_x']

    def __str__(self):
        return self.titulo


class Report(models.Model):
    """Model representing a generated report"""
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('users', 'Users Report'),
        ('operations', 'Operations Report'),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo_informe = models.CharField(max_length=20, choices=REPORT_TYPES)
    generado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    parametros = models.JSONField(default=dict, blank=True)  # Report generation parameters
    es_programado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Informe"
        verbose_name_plural = "Informes"
        db_table = "adm_informe"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo
