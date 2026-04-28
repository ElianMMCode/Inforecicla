from django.test import TestCase
import pytest
from django.db import connection


@pytest.mark.django_db
def test_verificar_entorno_bd():
    """
    Prueba de infraestructura para garantizar el aislamiento de la BD.
    """
    # Extraemos el nombre de la BD directamente de la conexión activa
    db_name = connection.settings_dict["NAME"]

    # Imprimimos el nombre en la terminal para inspección visual
    print(f"\n[AUDITORÍA DE ENTORNO] Pytest está operando en la BD: {db_name}")

    # Validamos por código que la BD contenga el prefijo 'test_'
    # o el nombre exacto que definiste en settings_test.py
    assert "test_inforecicla" in db_name, (
        f"¡ALERTA! Conectado a la BD incorrecta: {db_name}"
    )
