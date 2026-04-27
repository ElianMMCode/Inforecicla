# Casos de Prueba - CU-09: Monitorear Estado de Inventario

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-09: Monitorear Estado de Inventario.

---

## Casos de Prueba

| ID del Test                    | TC-CU09-01: Consultar Ocupación Global (%)                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el cálculo de ocupación global se realiza correctamente al sumar el total de stock versus la capacidad máxima de un Punto ECA.                                       |
| **Precondiciones**             | Existencia de inventarios asociados al Punto ECA.                                                                                                                                |
| **Pasos de Ejecución**         | 1. Enviar una solicitud GET a `/inventory/buscar-materiales-inventario/` con el `puntoId` correspondiente.<br>2. Verificar el campo `ocupacion_porcentaje` en la respuesta JSON. |
| **Datos de Prueba**            | `puntoId = UUID válido de un PuntoECA`.                                                                                                                                          |
| **Resultado Esperado**         | El campo `ocupacion_porcentaje` debe reflejar el porcentaje correcto considerando el stock y la capacidad.                                                                       |
| **Módulo de Django a Testear** | `inventory/views.py`, `inventory/service.py`.                                                                                                                                    |

| ID del Test                    | TC-CU09-02: Visualizar Desglose por Material                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Asegurar que el inventario desglosa correctamente la ocupación por material con su estado de alerta.                                                                                     |
| **Precondiciones**             | Cada material debe pertenecer a una categoría/tipo con los niveles `umbral_alerta` y `umbral_critico` configurados en el modelo.                                                         |
| **Pasos de Ejecución**         | 1. Realizar una llamada GET al endpoint `/inventory/buscar-materiales-inventario/`.<br>2. Inspeccionar los campos `nmbMaterial`, `stockActual`, `estado_alerta` en el JSON de respuesta. |
| **Datos de Prueba**            | `puntoId = UUID válido de un PuntoECA`.                                                                                                                                                  |
| **Resultado Esperado**         | Los materiales deben incluir correctamente sus datos de stock y alertas.                                                                                                                 |
| **Módulo de Django a Testear** | `inventory/models.py`, `inventory/service.py`.                                                                                                                                           |

| ID del Test                    | TC-EXT34-01: Disparar Alerta de Capacidad Crítica                                                                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el sistema emite una alerta crítica cuando el volumen supera el 85% de la capacidad.                                                                                                              |
| **Precondiciones**             | Un Punto ECA debe tener inventarios con `umbral_alerta` y `umbral_critico` configurados previamente.                                                                                                          |
| **Pasos de Ejecución**         | 1. Crear o actualizar un inventario mediante el servicio `/inventory/agregar/` con un `stock` que exceda el 85% de la capacidad máxima.<br>2. Observar el estado de alerta para el material en el inventario. |
| **Datos de Prueba**            | `stock_actual = 85`, `capacidad_maxima = 100`.                                                                                                                                                                |
| **Resultado Esperado**         | El estado de alerta debe ser "CRÍTICO" en `estado_alerta` del JSON.                                                                                                                                           |
| **Módulo de Django a Testear** | `inventory/models.py`, `inventory/service.py`, `inventory/views.py`.                                                                                                                                          |

| ID del Test                    | TC-EXT35-01: Sugerir Programación de Recolección                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Confirmar que al disparar una alerta crítica, el sistema sugiere programar la recolección.                                                                     |
| **Precondiciones**             | El material debe estar en estado crítico según el cálculo de ocupación.                                                                                        |
| **Pasos de Ejecución**         | 1. Consultar el endpoint `/inventory/buscar-materiales-inventario/` para materiales críticos.<br>2. Validar el atributo `sugerir_recoleccion` en la respuesta. |
| **Datos de Prueba**            | `estado_alerta = CRÍTICO`.                                                                                                                                     |
| **Resultado Esperado**         | La respuesta debe incluir un campo `sugerir_recoleccion = true`.                                                                                               |
| **Módulo de Django a Testear** | `inventory/views.py`, `inventory/service.py`.                                                                                                                  |

---

## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados al monitoreo de
inventarios en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.
