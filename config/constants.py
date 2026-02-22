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


# Todas las localidades de Bogota con un método de búsqueda
class LocalidadBogota(models.TextChoices):
    USAQUEN = "USAQUEN", _("Usaquén")
    CHAPINERO = "CHAPINERO", _("Chapinero")
    SANTA_FE = "SANTA_FE", _("Santa Fe")
    SAN_CRISTOBAL = "SAN_CRISTOBAL", _("San Cristóbal")
    USME = "USME", _("Usme")
    TUNJUELITO = "TUNJUELITO", _("Tunjuelito")
    BOSA = "BOSA", _("Bosa")
    KENNEDY = "KENNEDY", _("Kennedy")
    FONTIBON = "FONTIBON", _("Fontibón")
    ENGATIVA = "ENGATIVA", _("Engativá")
    SUBA = "SUBA", _("Suba")
    BARRIOS_UNIDOS = "BARRIOS_UNIDOS", _("Barrios Unidos")
    TEUSAQUILLO = "TEUSAQUILLO", _("Teusaquillo")
    MARTIRES = "MARTIRES", _("Los Mártires")
    ANTONIO_NARINO = "ANTONIO_NARINO", _("Antonio Nariño")
    PUENTE_ARANDA = "PUENTE_ARANDA", _("Puente Aranda")
    CANDELARIA = "CANDELARIA", _("La Candelaria")
    RAFAEL_URIBE = "RAFAEL_URIBE", _("Rafael Uribe Uribe")
    CIUDAD_BOLIVAR = "CIUDAD_BOLIVAR", _("Ciudad Bolívar")
    SUMAPAZ = "SUMAPAZ", _("Sumapaz")

    # Búsqueda por valor en localidades
    @classmethod
    def por_localidad(cls, nombre):
        nombre_clean = nombre.lower().strip()
        for localidad in cls:
            if localidad.label.lower() == nombre_clean:
                return localidad
        raise ValueError(f"Localidad no válida: {nombre}")


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
    KG = "KL", _("Kilogramo")
    UNIDAD = "UN", _("Unidad")
    TONELADA = "TON", _("Tonelada")
    METRO_CUBICO = "MC", _("Metro cúbico")


class Calificacion(models.TextChoices):
    LIKE = "LIKE", _("Like")
    DISLIKE = "DISLIKE", _("Dislike")


class Visibilidad(models.TextChoices):
    GLOBAL = "GLOBAL", _("Global")
    ECA = "ECA", _("ECA")
