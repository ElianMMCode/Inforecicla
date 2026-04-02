from django.db import models
from django.utils.translation import gettext_lazy as _


# Alerta para los inventario de los Puntos-Eca
class Alerta(models.TextChoices):
    OK = "OK", _("OK")
    ALERTA = "ALERTA", _("Alerta")
    CRITICO = "CRITICO", _("Crítico")


# Estados de las entidades
class Estado(models.TextChoices):
    ACTIVO = "ACTIVO", _("Activo")
    INACTIVO = "INACTIVO", _("Inactivo")
    SUSPENDIDO = "SUSPENDIDO", _("Suspendido")
    BLOQUEADO = "BLOQUEADO", _("BLOQUEADO")


# Tipos de Centros de Acopio
class TipoCentroAcopio(models.TextChoices):
    PLANTA = "PLANTA", _("Planta")
    PROVEEDOR = "PROVEEDOR", _("Proveedor")
    OTRO = "OTRO", _("Otro")

    # Búsqueda por valor en tipo de TipoCentroAcopio
    @classmethod
    def por_tipo(cls, tipo):
        tipo_clean = tipo.lower().strip()
        for tipo in cls:
            if tipo.label.lower() == tipo_clean:
                return tipo
        raise ValueError(f"Tipo no válido: {tipo}")


# Tipos de Documentos
class TipoDocumento(models.TextChoices):
    CC = "CC", _("Cédula de ciudadanía")
    TI = "TI", _("Tarjeta de identidad")
    RC = "RC", _("Registro civil")
    CE = "CE", _("Cédula de extranjería")
    PA = "PA", _("Pasaporte")
    NIT = "NIT", _("Número de Identificación Tributaria")
    PPT = "PPT", _("Permiso por Protección Temporal")
    SC = "SC", _("Salvoconducto")
    DIE = "DIE", _("Documento de Identidad Extranjero")

    @classmethod
    def por_codigo(cls, codigo):
        codigo_clean = codigo.upper().strip()
        for tipo in cls:
            if tipo.name == codigo_clean:
                return tipo
        raise ValueError(f"Tipo de documento no válido: {codigo}")


# Tipos de multimedia presentes en las publicaciones
class TipoMultimedia(models.TextChoices):
    IMG = "IMG", _("Imagen")
    VID = "VID", _("Video")
    DOC = "DOC", _("Documento")
    ENLC = "ENLC", _("Enlace")


class TipoRepeticion(models.TextChoices):
    SEMANAL = "SEMANAL", _("Semanal")
    QUINCENAL = "QUINCENAL", _("Quincenal")
    MENSUAL = "MENSUAL", _("Mensual")
    SIN_REPETICION = "SIN_REPETICION", _("Sin repetición")

    @property
    def dias_intervalo(self):
        intervalos = {
            self.SEMANAL: 7,
            self.QUINCENAL: 14,
            self.MENSUAL: 30,
            self.SIN_REPETICION: 0,
        }
        return intervalos[self]

    @property
    def descripcion(self):
        descripciones = {
            self.SEMANAL: _("Se repite cada 7 días"),
            self.QUINCENAL: _("Se repite cada 14 días"),
            self.MENSUAL: _("Se repite cada mes (30 días)"),
            self.SIN_REPETICION: _("Evento único, no se repite"),
        }
        return descripciones[self]

    @property
    def tiene_repeticion(self):
        return self != self.SIN_REPETICION


class TipoUsuario(models.TextChoices):
    ADMIN = "ADM", _("Admnisitrador")
    CIUDADANO = "CIU", _("Ciudadano")
    GESTOR_ECA = "GECA", _("Gestor ECA")


class UnidadMedida(models.TextChoices):
    KG = "KG", _("Kilogramo")
    UNIDAD = "UN", _("Unidad")
    TONELADA = "TON", _("Tonelada")
    METRO_CUBICO = "MC", _("Metro cúbico")


class Calificacion(models.TextChoices):
    LIKE = "LIKE", _("Like")
    DISLIKE = "DISLIKE", _("Dislike")


class Visibilidad(models.TextChoices):
    GLOBAL = "GLOBAL", _("Global")
    ECA = "ECA", _("ECA")
    
class TipoPublicacion(models.TextChoices):
    PUNTO_ECA = "Punto Eca", _("Punto Eca")
    NOTICIA = "Noticia", _("Noticia")
    EVENTO = "Evento", _("Evento"),
    EDUCACION = "Educativo", _("Educacion")
    
class Votos(models.TextChoices):
    LIKE = "Like", _("Like")
    DISLIKE = "Dislike", _("Dislike")
    
