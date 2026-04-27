# Casos de Prueba - CU-12: Gestionar Calendario Operativo

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-12: Gestionar Calendario Operativo.

---

## Casos de Prueba

| ID del Test                    | TC-CU12-01: Renderizar vista del Calendario                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Renderizar vista del Calendario                                                                                                                                   |
| **Precondiciones**             | N/A                                                                                                                                |
| **Pasos de Ejecución**         | 1. Acceder al endpoint de vista del calendario. |
| **Datos de Prueba**            | N/A                                                                                                                                          |
| **Resultado Esperado**         | La vista retorna un JSON con eventos agregados al contexto del calendario.                                                                       |
| **Módulo de Django a Testear** | scheduling/views.py:_build_calendario_context                                                                                                                                    |

| ID del Test                    | TC-CU12-02: Validar renderizado de eventos de compra y venta.                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar renderizado de eventos de compra y venta.                                                                                     |
| **Precondiciones**             | Historial con eventos de compra y venta existentes                                                                                                                         |
| **Pasos de Ejecución**         | 1. Invocar el contexto del calendario para un punto dado.<br>2. Validar que los eventos de compra y venta se incluyen correctamente.<br>                                                                 |
| **Datos de Prueba**            | N/A                                                                                                                                                  |
| **Resultado Esperado**         | Respuesta incluye JSON con eventos de compra y venta mapeados a FullCalendar.                                                                                                                 |
| **Módulo de Django a Testear** | scheduling/views.py:_build_calendario_context                                                                                                                                           |

| ID del Test                    | TC-CU12-03: Programar un nuevo evento                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Programar un nuevo evento                                                                                                              |
| **Precondiciones**             | Usuario autenticado como Gestor ECA                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `crear_evento_venta` con datos válidos.<br>2. Validar que el evento se crea correctamente en la base de datos.<br>                                                                 |
| **Datos de Prueba**            | Titulo="Evento Test"<br>fechaInicio="2026-06-01T09:00:00"<br>horaFin="11:00"                                                                                                                                                                |
| **Resultado Esperado**         | El evento se almacena con los datos enviados.                                                                                                                                           |
| **Módulo de Django a Testear** | scheduling/views.py:crear_evento_venta                                                                                                                                          |

| ID del Test                    | TC-CU12-04: Modificar evento existente.                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Modificar evento existente.                                                                     |
| **Precondiciones**             | Evento existente programado                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `editar_evento_venta` actualizando los datos.<br>2. Validar las modificaciones en la respuesta. |
| **Datos de Prueba**            | Titulo="Evento Modificado"<br>fechaInicio="2026-06-15T18:00:00"                                                                                                                                     |
| **Resultado Esperado**         | Cambios reflejados correctamente en la base de datos.                                                                                               |
| **Módulo de Django a Testear** | scheduling/views.py:editar_evento_venta                                                                                                                  |

| ID del Test                    | TC-EXT36-01: Validar bloqueo de eventos en el pasado                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar bloqueo de eventos en el pasado                                                                     |
| **Precondiciones**             | N/A                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `crear_evento_venta` con fecha/hora pasada.<br>2. Validar la respuesta de error. |
| **Datos de Prueba**            | fechaInicio="2023-01-01T09:00:00"<br>horaFin="2023-01-01T11:00:00"                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error con mensaje 'No se pueden programar eventos en el pasado'.                                                                                               |
| **Módulo de Django a Testear** | scheduling/views.py:crear_evento_venta                                                                                                                  |

| ID del Test                    | TC-EXT37-01: Validar alerta por conflicto de horario                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar alerta por conflicto de horario                                                                     |
| **Precondiciones**             | Evento existente con intersección de rango temporal.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `crear_evento_venta` con rango de fecha que coincide con un evento existente.<br>2. Validar respuesta con mensaje de conflicto.<br>                                                                 |
| **Datos de Prueba**            | fechaInicio="2026-06-01T10:00:00"<br>horaFin="2026-06-01T12:00:00"                                                                                                                                     |
| **Resultado Esperado**         | Respuesta con mensaje de error indicando un conflicto de horario.                                                                                               |
| **Módulo de Django a Testear** | scheduling/views.py:crear_evento_venta                                                                                                                  |

| ID del Test                    | TC-EXT38-01: Validar sincronización de eventos públicos para el mapa del ciudadano                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar sincronización de eventos públicos para el mapa del ciudadano                                                                     |
| **Precondiciones**             | El evento está marcado como público.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar POST al endpoint `crear_evento_venta` con el campo "es_publico" en True.<br>2. Consultar la API pública del mapa.<br>                                                                 |
| **Datos de Prueba**            | es_publico=True<br>fechaInicio="2026-06-01T10:00:00"<br>fechaFin="2026-06-01T12:00:00"                                                                                                                                     |
| **Resultado Esperado**         | El evento es visible en la API pública y accesible desde el mapa ciudadano.                                                                                               |
| **Módulo de Django a Testear** | scheduling/views.py:crear_evento_venta                                                                                                                  |

---
## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados a la gestión del
calendario operativo en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.