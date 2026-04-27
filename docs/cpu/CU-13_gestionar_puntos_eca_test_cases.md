# Casos de Prueba - CU-13: Gestionar Puntos ECA

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-13: Gestionar Puntos ECA.

---

## Casos de Prueba

| ID del Test                    | TC-CU13-01: Registrar un nuevo Punto ECA                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Registrar un nuevo Punto ECA                                                                                                                                   |
| **Precondiciones**             | N/A                                                                                                                                |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `registrar_punto` con datos válidos. |
| **Datos de Prueba**            | Nombre="Punto ECA Test", Dirección="Calle 123", Teléfono="601234567", Localidad="Bogotá", Capacidad=100                                                                                                                                          |
| **Resultado Esperado**         | Punto ECA almacenado en la base de datos con los datos enviados.                                                                       |
| **Módulo de Django a Testear** | ecas/views.py:registrar_punto                                                                                                                                    |

| ID del Test                    | TC-CU13-02: Editar detalles y capacidad máxima de un Punto ECA                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Editar detalles y capacidad máxima de un Punto ECA                                                                                     |
| **Precondiciones**             | Punto ECA existente registrado.                                                                                                                         |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `editar_punto` con los detalles actualizados.<br>                                                                 |
| **Datos de Prueba**            | Nombre="Punto Modificado", Capacidad=150                                                                                                                                                  |
| **Resultado Esperado**         | Los cambios se reflejan correctamente en la base de datos.                                                                                                                 |
| **Módulo de Django a Testear** | ecas/views.py:editar_punto                                                                                                                                           |

| ID del Test                    | TC-CU13-03: Activar/Inactivar un Punto ECA                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Activar/Inactivar un Punto ECA                                                                                                              |
| **Precondiciones**             | Punto ECA existente registrado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `alternar_estado` para cambiar el estado operativo de un Punto ECA.<br>                                                                 |
| **Datos de Prueba**            | Estado=Inactivo                                                                                                                                                                |
| **Resultado Esperado**         | El estado operativo del Punto ECA cambia entre activo e inactivo.                                                                                                                                           |
| **Módulo de Django a Testear** | ecas/views.py:alternar_estado                                                                                                                                          |

| ID del Test                    | TC-CU13-04: Archivar/Eliminar un registro de Punto ECA                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Archivar/Eliminar un registro de Punto ECA                                                                                                                        |
| **Precondiciones**             | Punto ECA existente registrado.<br>Sin inventarios.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar DELETE al endpoint `eliminar_punto` para archivar el Punto ECA. |
| **Datos de Prueba**            | Punto ECA ID=123                                                                                                                                     |
| **Resultado Esperado**         | Punto marcado como "is_deleted=True" para garantizar trazabilidad.                                                                                               |
| **Módulo de Django a Testear** | ecas/views.py:eliminar_punto                                                                                                                  |

| ID del Test                    | TC-EXT23-01: Validar bloqueo de capacidad negativa o cero                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar bloqueo de capacidad negativa o cero                                                                     |
| **Precondiciones**             | N/A                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `editar_punto` con capacidad inválida.<br>                                                                 |
| **Datos de Prueba**            | Capacidad=-50                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando que la capacidad no puede ser negativa ni cero.                                                                                               |
| **Módulo de Django a Testear** | ecas/views.py:editar_punto                                                                                                                  |

| ID del Test                    | TC-EXT24-01: Mostrar error al intentar registrar coordenadas geográficas inválidas                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Mostrar error al intentar registrar coordenadas geográficas inválidas                                                                     |
| **Precondiciones**             | N/A                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `registrar_punto` con latitud/longitud inválidas.<br>                                                                 |
| **Datos de Prueba**            | Latitud="192.12345", Longitud="-181.67890"                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando valores fuera de rango para latitud/longitud.                                                                                               |
| **Módulo de Django a Testear** | ecas/views.py:registrar_punto                                                                                                                  |

| ID del Test                    | TC-EXT25-01: Denegar eliminación de un Punto ECA con inventario o historial asociado                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Denegar eliminación de un Punto ECA con inventario o historial asociado                                                                     |
| **Precondiciones**             | Punto ECA con inventario/historial.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar DELETE al endpoint `eliminar_punto` sobre un Punto que tiene inventario asociado.<br>                                                                 |
| **Datos de Prueba**            | Punto ECA ID=456                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando que no se puede eliminar porque tiene inventario asociado y debe marcarse.                                                                                               |
| **Módulo de Django a Testear** | ecas/views.py:eliminar_punto                                                                                                                  |

---
## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados a la gestión de
puntos ECA en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.