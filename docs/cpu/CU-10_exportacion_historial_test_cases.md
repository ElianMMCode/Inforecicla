# Casos de Prueba - CU-10: Exportar Historial de Operaciones

## Introducción

Este documento detalla los casos de prueba diseñados para cubrir exhaustivamente
las funcionalidades derivadas del CU-10: "Exportar Historial de Operaciones",
incluyendo validaciones adicionales como excepciones y uso eficiente de
recursos.

---

## Casos de Prueba

| ID del Test                    | TC-CU10-01: Validar filtrado por rango de fechas                                                                                                                     |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar filtrado por rango de fechas                                                                                                                                 |
| **Precondiciones**             | Usuario autenticado como gestor ECA                                                                                                                                  |
| **Pasos de Ejecución**         | 1. Realizar GET al endpoint exportar_historial con parámetros start_date=2026-04-01 y end_date=2026-04-30.<br>2. Validar datos incluyen solo registros en ese rango. |
| **Datos de Prueba**            | start_date=2026-04-01<br>end_date=2026-04-30                                                                                                                         |
| **Resultado Esperado**         | Respuesta contiene solo operaciones desde el 1 de abril hasta el 30 de abril de 2026.                                                                                |
| **Módulo de Django a Testear** | operations/views.py:exportar_historial_excel                                                                                                                         |

| ID del Test                    | TC-CU10-02: Validar filtrado por material específico                                                                                                                  |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar filtrado por material específico                                                                                                                              |
| **Precondiciones**             | Usuario autenticado como gestor ECA                                                                                                                                   |
| **Pasos de Ejecución**         | 1. Realizar GET al endpoint exportar_historial con parámetro material_name="Plástico PET".<br>2. Validar respuesta contiene solo registros asociados al material.<br> |
| **Datos de Prueba**            | material_name="Plástico PET"                                                                                                                                          |
| **Resultado Esperado**         | Respuesta contiene solo registros donde el nombre del material es "Plástico PET".                                                                                     |
| **Módulo de Django a Testear** | operations/views.py:exportar_historial_excel                                                                                                                          |

| ID del Test                    | TC-CU10-03: Validar extracción y compilación de datos combinados                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Descripción / Objetivo**     | Validar extracción y compilación de datos combinados                                                                                 |
| **Precondiciones**             | Usuario autenticado correctamente<br>Historial con compras y ventas existentes                                                       |
| **Pasos de Ejecución**         | 1. Ejecución del endpoint exportar_historial.<br>2. Validar que compras y ventas estén unificados correctamente en la respuesta.<br> |
| **Datos de Prueba**            | N/A                                                                                                                                  |
| **Resultado Esperado**         | La respuesta contiene movimientos clasificados como compras o ventas, con detalles correctos, incluyendo totales calculados.         |
| **Módulo de Django a Testear** | operations/views.py:exportar_historial_excel<br>operations/resources.py:CompraInventarioResource                                     |

| ID del Test                    | TC-CU10-04: Validar generación de archivo Excel usando flujos                                                                                              |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar generación de archivo Excel usando flujos                                                                                                          |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                                          |
| **Pasos de Ejecución**         | 1. Realizar GET al endpoint exportar_historial.<br>2. Validar que el servidor utiliza streaming para el archivo generado.<br>3. Descargar Excel exportado. |
| **Datos de Prueba**            | N/A                                                                                                                                                        |
| **Resultado Esperado**         | Genera un archivo Excel descargable. Confirmar uso de streams en logs o métricas.                                                                          |
| **Módulo de Django a Testear** | operations/views.py:exportar_historial_excel                                                                                                               |

| ID del Test                    | TC-CU10-05: Validar manejo de excepción sin registros                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar manejo de excepción sin registros                                                                                                                                 |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                                                         |
| **Pasos de Ejecución**         | 1. Realizar GET al endpoint exportar_historial con filtros que resultan en 0 registros.<br>2. Validar respuesta con mensaje de "No hay registros en el rango solicitado". |
| **Datos de Prueba**            | Filtros que excluyen cualquier registro existente                                                                                                                         |
| **Resultado Esperado**         | Respuesta contiene mensaje "No hay registros en el rango solicitado" y código 404.                                                                                        |
| **Módulo de Django a Testear** | operations/views.py:exportar_historial_excel                                                                                                                              |

| ID del Test                    | TC-CU10-06: Validar manejo de archivos masivos en segundo plano                                                                                                                                                                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar manejo de archivos masivos en segundo plano                                                                                                                                                                                    |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                                                                                                                      |
| **Pasos de Ejecución**         | 1. Realizar GET al endpoint exportar_historial para un ECA con más de 10,000 registros.<br>2. Validar que la exportación se realice como job en segundo plano.<br>3. Confirmar recepción del correo con el enlace al archivo generado. |
| **Datos de Prueba**            | N/A                                                                                                                                                                                                                                    |
| **Resultado Esperado**         | Respuesta inicial indica exportación en segundo plano.<br>Correo incluye enlace al archivo generado.                                                                                                                                   |
| **Módulo de Django a Testear** | operations/views.py:exportar_historial_excel                                                                                                                                                                                           |

---

## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados a la exportación de
historial de operaciones en InfoRecicla. Asegúrese de preparar los datos
iniciales correctamente antes de su ejecución.
