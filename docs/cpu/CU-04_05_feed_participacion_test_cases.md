# Casos de Prueba - CU-04/05: Explorar Feed y Retroalimentar

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-04/05: Explorar Feed y Retroalimentar.

---

## Casos de Prueba

| ID del Test                    | TC-CU04.1-01: Consultar Lista Paginada                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que la API retorne publicaciones en bloques con metadatos de paginación (count, next, previous).                                                                   |
| **Precondiciones**             | Existen al menos 15 publicaciones registradas; el tamaño de página está configurado en 10.                                                                                                                                |
| **Pasos de Ejecución**         | 1. Enviar petición GET a `/api/feed/`. |
| **Datos de Prueba**            | Query params por defecto.                                                                                                                                          |
| **Resultado Esperado**         | Código HTTP 200 OK. El JSON contiene 10 registros y el campo `next` apunta a la página 2.                                                                       |
| **Módulo de Django a Testear** | `publicaciones/views.py` (panel_publicaciones), `publicaciones/service.py` (PublicacionService.list_for_panel)                                                                                                                                    |

| ID del Test                    | TC-CU04.2-01: Visualizar Detalle y Multimedia                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que la vista de detalle retorne correctamente los datos completos de una publicación, incluyendo imágenes asociadas y video con su miniatura.                                                                   |
| **Precondiciones**             | Publicación con ID 50 registrada en BD con al menos una imagen (`ImagenPublicacion`) y un video con `video_thumbnail`.                                                                                                                                |
| **Pasos de Ejecución**         | 1. Enviar petición GET a `/publicacion/50/`. 2. Verificar los campos multimedia en el contexto renderizado. |
| **Datos de Prueba**            | `publicacion_id=50`, publicación con `video`, `video_thumbnail` e `imagenes` asociadas.                                                                                                                                          |
| **Resultado Esperado**         | Código HTTP 200 OK. El contexto incluye `titulo`, `contenido`, lista de `imagenes` (campo `imagen` y `descripcion`) y campos `video` y `video_thumbnail` de la publicación.                                                                       |
| **Módulo de Django a Testear** | `publicaciones/views.py` (publicacion - get_detail_context), `publicaciones/models.py` (Publicacion, ImagenPublicacion)                                                                                                                                    |

| ID del Test                    | TC-CU04.3-01: Agregar a Colección de Guardados                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la persistencia de la relación entre el usuario y una publicación guardada al ejecutar el toggle por primera vez.                                                                                     |
| **Precondiciones**             | Usuario autenticado y publicación existente con ID 50. El usuario NO ha guardado previamente esa publicación.                                                                                                                         |
| **Pasos de Ejecución**         | 1. Enviar petición POST al endpoint `toggle_guardado` para la publicación 50.<br>                                                                 |
| **Datos de Prueba**            | `publicacion_id=50`, sin registro previo en `Guardados` para ese usuario.                                                                                                                                                  |
| **Resultado Esperado**         | Se crea un registro en la tabla `tb_guardados`. El campo `mi_guardado` en el contexto de detalle es `True`.                                                                                                                 |
| **Módulo de Django a Testear** | `publicaciones/views.py` (toggle_guardado), `publicaciones/models.py` (Guardados)                                                                                                                                           |

| ID del Test                    | TC-CU04.3-02: Remover de Colección de Guardados (Toggle inverso)                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar que al ejecutar el toggle por segunda vez sobre una publicación ya guardada, el registro se elimina correctamente.                                                                                     |
| **Precondiciones**             | Usuario autenticado y publicación con ID 50. El usuario YA tiene esa publicación guardada en `tb_guardados`.                                                                                                                         |
| **Pasos de Ejecución**         | 1. Enviar petición POST al endpoint `toggle_guardado` para la publicación 50 (segunda ejecución).<br>                                                                 |
| **Datos de Prueba**            | `publicacion_id=50`, con registro previo existente en `Guardados` para ese usuario.                                                                                                                                                  |
| **Resultado Esperado**         | El registro en `tb_guardados` es eliminado. El campo `mi_guardado` en el contexto de detalle pasa a ser `False`.                                                                                                                 |
| **Módulo de Django a Testear** | `publicaciones/views.py` (toggle_guardado), `publicaciones/models.py` (Guardados)                                                                                                                                           |

| ID del Test                    | TC-CU05.1-01: Alternar Estado de 'Me Gusta' (Toggle)                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar la lógica de interruptor (si existe, elimina; si no, crea).                                                                                                              |
| **Precondiciones**             | Usuario autenticado.                                                                                                          |
| **Pasos de Ejecución**         | 1. Enviar POST a `votar_publicacion` con `valor=LIKE` (crea Reaccion). 2. Enviar POST nuevamente con el mismo valor (elimina Reaccion).<br>                                                                 |
| **Datos de Prueba**            | `publicacion_id=50`, `valor=LIKE` (enviado dos veces).                                                                                                                                                                |
| **Resultado Esperado**         | 1er envío: registro creado en tabla `reacciones`. 2do envío: registro eliminado (toggle inverso).                                                                                                                                           |
| **Módulo de Django a Testear** | `publicaciones/views.py` (votar_publicacion), `publicaciones/models.py` (Reaccion)                                                                                                                                          |

| ID del Test                    | TC-CU05.2-01: Publicar Comentario y Prevención XSS                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la creación del comentario y asegurar que el texto sea saneado contra scripts maliciosos.                                                                                        |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar petición POST a `agregar_comentario` con un script de JS en el contenido. |
| **Datos de Prueba**            | `{"publicacion_id": 50, "texto": "Buen post <script>alert('xss')</script>"}`                                                                                                                                     |
| **Resultado Esperado**         | Comentario creado correctamente. El contenido guardado en BD debe estar escapado o saneado (ej: `&lt;script&gt;`).                                                                                               |
| **Módulo de Django a Testear** | `publicaciones/views.py` (agregar_comentario), `publicaciones/models.py` (Comentario)                                                                                                                  |

| ID del Test                    | TC-EXT17-01: Mostrar Error - Límite Excedido                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el backend rechace comentarios que excedan los 1000 caracteres.                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar petición POST a `agregar_comentario` con una cadena de 1001 caracteres.<br>                                                                 |
| **Datos de Prueba**            | Campo `texto` con longitud 1001 caracteres (`_COMENTARIO_MAX = 1000` en `publicaciones/views.py`).                                                                                                                                     |
| **Resultado Esperado**         | Se agrega mensaje de error de Django: "El comentario no puede superar los 1000 caracteres". No se crea registro en BD.                                                                                               |
| **Módulo de Django a Testear** | `publicaciones/views.py` (agregar_comentario - validación `_COMENTARIO_MAX`)                                                                                                                  |

| ID del Test                    | TC-EXT18-01: Bloquear Acción - Comentario Vacío                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar que no se permitan registros nulos o compuestos solo por espacios.                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST con `texto=""`. 2. Enviar POST con `texto="   "` (solo espacios).<br>                                                                 |
| **Datos de Prueba**            | `{"publicacion_id": 50, "texto": "   "}`                                                                                                                                     |
| **Resultado Esperado**         | Se agrega mensaje de error de Django: "El comentario no puede estar vacío". No se crea registro en BD (el campo `.strip()` elimina espacios antes de validar).                                                                                               |
| **Módulo de Django a Testear** | `publicaciones/views.py` (agregar_comentario - validación `_COMENTARIO_MIN` y `.strip()`)                                                                                                                  |

---

## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados al feed y
retroalimentación en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.
