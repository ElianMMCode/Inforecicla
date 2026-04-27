# Casos de Prueba - CU-14: Gestionar Publicaciones del Feed

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-14: Gestionar Publicaciones del Feed.

---

## Casos de Prueba

| ID del Test                    | TC-CU14-01: Redactar una nueva publicación                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Redactar una nueva publicación                                                                                                                                   |
| **Precondiciones**             | Usuario autenticado.                                                                                                                                |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con título y contenido válidos. |
| **Datos de Prueba**            | Título="Nueva Publicación", Contenido="Contenido de prueba"                                                                                                                                          |
| **Resultado Esperado**         | Publicación almacenada en la base de datos con los datos enviados.                                                                       |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                                    |

| ID del Test                    | TC-CU14-02: Intentar redactar una publicación sin título o contenido                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Intentar redactar una publicación sin título o contenido                                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                         |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con título vacío o contenido vacío.<br>                                                                 |
| **Datos de Prueba**            | Título="", Contenido=""                                                                                                                                                  |
| **Resultado Esperado**         | Respuesta de error indicando "El campo título y contenido no deben estar vacíos".                                                                                                                 |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                                           |

| ID del Test                    | TC-CU14-03: Adjuntar archivos multimedia con validación de MIME y tamaño                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Adjuntar archivos multimedia con validación de MIME y tamaño                                                                                                              |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con un archivo multimedia válido.<br>                                                                 |
| **Datos de Prueba**            | Archivo=`imagen.jpg`, tamaño: 4 MB                                                                                                                                                                |
| **Resultado Esperado**         | Publicación creada junto con el archivo adjunto válido.                                                                                                                                           |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                                          |

| ID del Test                    | TC-CU14-04: Intentar adjuntar un archivo con tipo MIME inválido                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Intentar adjuntar un archivo con tipo MIME inválido                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con un archivo multimedia inválido. |
| **Datos de Prueba**            | Archivo=`archivo.txt`, tamaño: 2 MB                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando "Formato de archivo no soportado".                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-CU14-05: Intentar adjuntar un archivo excediendo el máximo permitido (5MB)                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Intentar adjuntar un archivo excediendo el máximo permitido (5MB)                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con un archivo multimedia inválido.<br>                                                                 |
| **Datos de Prueba**            | Archivo=`imagen.jpg`, tamaño: 6 MB                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando "El archivo excede el límite permitido de 5MB".                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-CU14-06: Editar el contenido de una publicación existente                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Editar el contenido de una publicación existente                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar PUT al endpoint `editar_publicacion` con contenido modificado. |
| **Datos de Prueba**            | Contenido="Contenido modificado de la publicación"                                                                                                                                     |
| **Resultado Esperado**         | Cambios almacenados en la base de datos y reflejados al consultar la publicación.                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-CU14-07: Intentar editar una publicación con cambios inválidos (campos vacíos)                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Intentar editar una publicación con cambios inválidos (campos vacíos)                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar PUT al endpoint `editar_publicacion` con campos vacíos.<br>                                                                 |
| **Datos de Prueba**            | Título="", Contenido=""                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando "El campo título y contenido no deben estar vacíos".                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-CU14-08: Marcar una publicación como "oculta"                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Marcar una publicación como "oculta"                                                                     |
| **Precondiciones**             | Usuario autenticado y publicación existente.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar DELETE al endpoint `ocultar_publicacion`.<br>                                                                 |
| **Datos de Prueba**            | ID de publicación válido.                                                                                                                                     |
| **Resultado Esperado**         | Publicación marcada como `is_published=False`.                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-CU14-09: Intentar eliminar de forma permanente una publicación con comentarios                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Intentar eliminar de forma permanente una publicación con comentarios                                                                     |
| **Precondiciones**             | Usuario autenticado y publicación con comentarios existentes.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Realizar DELETE al endpoint `eliminar_publicacion`.<br>                                                                 |
| **Datos de Prueba**            | ID de publicación válido con comentarios asociados.                                                                                                                                     |
| **Resultado Esperado**         | Respuesta indicando que no es posible eliminar directamente, solo ocultar.                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-EXT26-01: Bloquear creación de publicación con contenido de texto vacío                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Bloquear creación de publicación con contenido de texto vacío                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con campo contenido vacío.<br>                                                                 |
| **Datos de Prueba**            | Contenido=""                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando "El campo contenido no puede estar vacío".                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-EXT27-01: Rechazar archivo con formato no soportado durante creación de publicación                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Rechazar archivo con formato no soportado durante creación de publicación                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con un archivo de formato no permitido.<br>                                                                 |
| **Datos de Prueba**            | Archivo=`documento.pdf`, tamaño=200KB                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando "Formato de archivo no soportado."                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

| ID del Test                    | TC-EXT27-02: Rechazar archivo excediendo el límite de tamaño durante la creación                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Rechazar archivo excediendo el límite de tamaño durante la creación                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST al endpoint `crear_publicacion` con un archivo multimedia con tamaño >5MB.<br>                                                                 |
| **Datos de Prueba**            | Archivo=`imagen.jpg`, tamaño=6MB                                                                                                                                     |
| **Resultado Esperado**         | Respuesta de error indicando "El archivo excede el tamaño máximo permitido".                                                                                               |
| **Módulo de Django a Testear** | publicaciones/views.py                                                                                                                  |

---
## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados a la gestión de
publicaciones del feed en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.