# Casos de Prueba - CU-03: Consultar Detalle de Punto ECA

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-03: Consultar Detalle de Punto ECA.

---

## Casos de Prueba

| ID del Test                    | TC-CU03.1-01: Renderizar Información Base                                                                 |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el servidor retorne los datos generales (Nombre, Dirección, Teléfono) de un ECA específico.   |
| **Precondiciones**             | El punto ECA con ID 10 debe estar registrado en la base de datos con datos completos.                     |
| **Pasos de Ejecución**         | 1. Realizar petición GET al endpoint `/api/ecas/10/`.                                                     |
| **Datos de Prueba**            | `eca_id=10`                                                                                               |
| **Resultado Esperado**         | Código HTTP 200 OK. El JSON incluye los campos `name`, `address` y `contact_info` correctamente mapeados. |
| **Módulo de Django a Testear** | `locations/serializers.py`, `api/views.py`                                                                |

| ID del Test                    | TC-CU03.2-01: Consultar Horarios y Estado Operativo (Cálculo is_open)                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar que el backend calcule correctamente si el ECA está abierto comparando la hora actual con su jornada en BD.                  |
| **Precondiciones**             | ECA registrado con jornada de 08:00 a 17:00.                                                                                           |
| **Pasos de Ejecución**         | 1. Simular (Mock) hora del servidor a las 10:00 AM. 2. Realizar petición GET de detalle. 3. Simular hora a las 11:00 PM y repetir.<br> |
| **Datos de Prueba**            | `mock_now="10:00"`, `mock_now="23:00"`                                                                                                 |
| **Resultado Esperado**         | Para las 10:00 AM, el campo `is_open` debe ser `true`. Para las 11:00 PM, `is_open` debe ser `false`.                                  |
| **Módulo de Django a Testear** | `locations/models.py` (Property/Method), `locations/serializers.py`                                                                    |

| ID del Test                    | TC-CU03.3-01: Listar Materiales Aceptados y Precios                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que se listen todos los materiales vinculados al ECA con sus tarifas vigentes.                               |
| **Precondiciones**             | El ECA tiene asociados "Plástico" ($500/kg) y "Cartón" ($300/kg).                                                    |
| **Pasos de Ejecución**         | 1. Consultar detalle del punto ECA. 2. Verificar la lista anidada de materiales.<br>                                 |
| **Datos de Prueba**            | Petición de detalle estándar.                                                                                        |
| **Resultado Esperado**         | El JSON contiene un array `accepted_materials` con la descripción y el precio actualizado de cada material asociado. |
| **Módulo de Django a Testear** | `locations/serializers.py`, `inventory/models.py`                                                                    |

| ID del Test                    | TC-EXT19-01: Mostrar Alerta Visual - ECA Fuera de Servicio                                                                   |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el sistema marque un ECA como fuera de servicio si su flag `is_active` es falso, independientemente del horario. |
| **Precondiciones**             | Punto ECA registrado con `is_active=False`.                                                                                  |
| **Pasos de Ejecución**         | 1. Intentar consultar detalle del ECA.<br>                                                                                   |
| **Datos de Prueba**            | ECA con estado inactivo en BD.                                                                                               |
| **Resultado Esperado**         | El campo `status_message` indica "Temporalmente fuera de servicio" y `is_open` es forzado a `false`.                         |
| **Módulo de Django a Testear** | `locations/models.py`, `api/views.py`                                                                                        |

| ID del Test                    | TC-EXT20-01: Trazar Ruta de Navegación                                                                                |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la correcta generación del link externo de navegación (Google Maps/Waze) basado en las coordenadas del ECA. |
| **Precondiciones**             | El ECA tiene coordenadas válidas (Lat: 4.60, Lon: -74.08).                                                            |
| **Pasos de Ejecución**         | 1. Consultar detalle del ECA. 2. Verificar el campo `navigation_url`.<br>                                             |
| **Datos de Prueba**            | Coordenadas del punto en BD.                                                                                          |
| **Resultado Esperado**         | El backend retorna una URL válida tipo `https://www.google.com/maps/dir/?api=1&destination=4.60,-74.08`.              |
| **Módulo de Django a Testear** | `locations/serializers.py` o `locations/utils.py`                                                                     |

---

## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados al detalle de puntos
ECA en InfoRecicla. Asegúrese de preparar los datos iniciales correctamente
antes de su ejecución.

