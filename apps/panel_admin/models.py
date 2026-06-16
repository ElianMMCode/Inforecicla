from django.db import models
from django.conf import settings
from django.utils import timezone


class Dashboard(models.Model):
    """Model representing an admin dashboard"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboards')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tablero"
        verbose_name_plural = "Tableros"
        db_table = "adm_tablero"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Widget(models.Model):
    """Model representing a widget within a dashboard"""
    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('metric', 'Metric'),
        ('text', 'Text'),
    ]

    title = models.CharField(max_length=200)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    position_x = models.IntegerField(default=0)  # Grid position
    position_y = models.IntegerField(default=0)  # Grid position
    width = models.IntegerField(default=1)  # Grid columns
    height = models.IntegerField(default=1)  # Grid rows
    config = models.JSONField(default=dict, blank=True)  # Widget-specific configuration
    dashboard = models.ForeignKey('Dashboard', on_delete=models.CASCADE, related_name='widgets')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Widget"
        verbose_name_plural = "Widgets"
        db_table = "adm_widget"
        ordering = ['position_y', 'position_x']

    def __str__(self):
        return self.title


class Report(models.Model):
    """Model representing a generated report"""
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('users', 'Users Report'),
        ('operations', 'Operations Report'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    parameters = models.JSONField(default=dict, blank=True)  # Report generation parameters
    is_scheduled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Informe"
        verbose_name_plural = "Informes"
        db_table = "adm_informe"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
