from django.db import models
from django.core.validators import RegexValidator


class ContactoModel(models.Model):
    class ContactoModel(models.Model):
        celular = models.CharField(
            max_length=10,
            unique=True,
            blank=False,
            validators=[
                RegexValidator(
                    regex=r"^3\\d{9}$",
                    message="El celular debe inciar con 3",
                ),
            ],
        )

        class Meta:
            abstract = True

    class Meta:
        abstract = True


class CreacionModificacionModel(models.Model):
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
