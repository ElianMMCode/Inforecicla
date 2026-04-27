# Casos de Prueba - CU-11: Consultar Asistente (ReciclaBot)

## Introducción

Este documento detalla los casos de prueba diseñados para cubrir exhaustivamente las funcionalidades derivadas del CU-11: "Consultar Asistente (ReciclaBot)", incluyendo validaciones adicionales como excepciones y manejo eficiente de conexiones persistentes.

---

## Casos de Prueba

| ID del Test                    | TC-CU11-01: Validar la carga del historial de conversación existente                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar la carga del historial de conversación existente                                                                   |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                                                |
| **Pasos de Ejecución**         | 1. Realizar GET al endpoint de historial del asistente.<br>2. Validar que los mensajes históricos se carguen correctamente. |
| **Datos de Prueba**            | N/A                                                                                                                                          |
| **Resultado Esperado**         | El historial completo del usuario autenticado asociado al ID del ECA es retornado.                                                                       |
| **Módulo de Django a Testear** | reciclabot/service.py:AsistenteECAService                                                                                                                                    |

| ID del Test                    | TC-CU11-02: Validar la entrada de texto del usuario                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar la entrada de texto del usuario                                                                                     |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                                         |
| **Pasos de Ejecución**         | 1. Enviar un texto como parámetro.<br>2. Validar que cumpla las reglas de negocio (longitud mínima, caracteres válidos).<br>                                                                 |
| **Datos de Prueba**            | Cadena válida de texto con una longitud mínima de 1.                                                                                                                                                  |
| **Resultado Esperado**         | Respuesta confirmando que la entrada es válida.                                                                                                                 |
| **Módulo de Django a Testear** | reciclabot/service.py:AsistenteECAService                                                                                                                                           |

| ID del Test                    | TC-CU11-03: Procesar mensaje en tiempo real utilizando WebSocket                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Procesar mensaje en tiempo real utilizando WebSocket                                                                                                              |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                          |
| **Pasos de Ejecución**         | 1. Conectar la interfaz WebSocket.<br>2. Enviar un mensaje válido.<br>3. Validar la respuesta en tiempo real del sistema.<br>                                                                 |
| **Datos de Prueba**            | Pregunta: "¿Qué materiales puedo reciclar aquí?"                                                                                                                                                                |
| **Resultado Esperado**         | Respuesta se entrega sobre un socket abierto y persistente. No hay timeout mientras el sistema IA genera la respuesta.                                                                                                                                           |
| **Módulo de Django a Testear** | chat/consumers.py                                                                                                                                          |

| ID del Test                    | TC-CU11-04: Validar persistencia de interacción en base de datos                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar persistencia de interacción en base de datos                                                                     |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar un envío.<br>2. Validar que las entradas (usuario, mensaje, respuesta) se persistieron correctamente en la base de datos. |
| **Datos de Prueba**            | Entrada válida en formato {usuario, mensaje}                                                                                                                                     |
| **Resultado Esperado**         | Datos del chat persistidos en la tabla de históricos del modelo correspondiente.                                                                                               |
| **Módulo de Django a Testear** | reciclabot/service.py:AsistenteECAService                                                                                                                  |

| ID del Test                    | TC-EXT12-01: Bloquear envío de consulta vacía                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Bloquear envío de consulta vacía                                                                     |
| **Precondiciones**             | Usuario autenticado correctamente                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar texto vacío.<br>2. Verificar que no se procese la consulta. |
| **Datos de Prueba**            | Cadena vacía: ""                                                                                                                                     |
| **Resultado Esperado**         | Se muestra mensaje de error "La consulta no puede estar vacía".                                                                                               |
| **Módulo de Django a Testear** | chat/consumers.py                                                                                                                  |

| ID del Test                    | TC-EXT13-01: Notificar al usuario cuando falla la comunicación con el servicio IA                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Notificar al usuario cuando falla la comunicación con el servicio IA                                                                     |
| **Precondiciones**             | Usuario autenticado correctamente<br>Servicio de IA desconectado                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar una consulta válida.<br>2. Forzar excepción de red.<br>3. Validar el mensaje de error recibido.<br>                                                                 |
| **Datos de Prueba**            | Entrada válida: "¿Cómo reciclar vidrio?"                                                                                                                                     |
| **Resultado Esperado**         | Mensaje de error: "El servicio no está disponible en este momento." se muestra al usuario.                                                                                               |
| **Módulo de Django a Testear** | chat/consumers.py                                                                                                                  |

---
## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados al asistente
ReciclaBot en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.