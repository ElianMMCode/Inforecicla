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
| **Módulo de Django a Testear** | `social/views.py`                                                                                                                                    |

| ID del Test                    | TC-CU04.3-01: Agregar a Colección de Favoritos                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la persistencia de la relación Many-to-Many entre el usuario y una publicación guardada.                                                                                     |
| **Precondiciones**             | Usuario autenticado y publicación existente con ID 50.                                                                                                                         |
| **Pasos de Ejecución**         | 1. Enviar petición POST al endpoint de favoritos para la publicación 50.<br>                                                                 |
| **Datos de Prueba**            | `{"post_id": 50}`                                                                                                                                                  |
| **Resultado Esperado**         | Código HTTP 201 Created. El registro se refleja en la tabla intermedia de la base de datos vinculada al usuario.                                                                                                                 |
| **Módulo de Django a Testear** | `social/models.py`, `social/views.py`                                                                                                                                           |

| ID del Test                    | TC-CU05.1-01: Alternar Estado de 'Me Gusta' (Toggle)                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar la lógica de interruptor (si existe, elimina; si no, crea).                                                                                                              |
| **Precondiciones**             | Usuario autenticado.                                                                                                          |
| **Pasos de Ejecución**         | 1. Enviar POST (crea Like). 2. Enviar POST nuevamente al mismo post (elimina Like).<br>                                                                 |
| **Datos de Prueba**            | `{"post_id": 50}` (enviado dos veces).                                                                                                                                                                |
| **Resultado Esperado**         | 1er envío: 201 Created. 2do envío: 204 No Content (o confirmación de eliminación).                                                                                                                                           |
| **Módulo de Django a Testear** | `social/views.py`                                                                                                                                          |

| ID del Test                    | TC-CU05.2-01: Publicar Comentario y Prevención XSS                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la creación del comentario y asegurar que el texto sea saneado contra scripts maliciosos.                                                                                        |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar petición POST con un script de JS en el contenido. |
| **Datos de Prueba**            | `{"post_id": 50, "contenido": "Buen post <script>alert('xss')</script>"}`                                                                                                                                     |
| **Resultado Esperado**         | Código HTTP 201 Created. El contenido guardado en BD debe estar escapado o saneado (ej: `&lt;script&gt;`).                                                                                               |
| **Módulo de Django a Testear** | `social/serializers.py`, `core/utils.py` (saneamiento)                                                                                                                  |

| ID del Test                    | TC-EXT17-01: Mostrar Error - Límite Excedido                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el backend rechace comentarios que excedan los 500 caracteres.                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar petición POST con una cadena de 501 caracteres.<br>                                                                 |
| **Datos de Prueba**            | Payload JSON con campo `contenido` de longitud 501.                                                                                                                                     |
| **Resultado Esperado**         | Código HTTP 400 Bad Request. Error: "El comentario no puede exceder los 500 caracteres".                                                                                               |
| **Módulo de Django a Testear** | `social/serializers.py`                                                                                                                  |

| ID del Test                    | TC-EXT18-01: Bloquear Acción - Comentario Vacío                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar que no se permitan registros nulos o compuestos solo por espacios.                                                                     |
| **Precondiciones**             | Usuario autenticado.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Enviar POST con contenido "". 2. Enviar POST con contenido "   ".<br>                                                                 |
| **Datos de Prueba**            | `{"post_id": 50, "contenido": "   "}`                                                                                                                                     |
| **Resultado Esperado**         | Código HTTP 400 Bad Request. Error: "Este campo no puede estar en blanco".                                                                                               |
| **Módulo de Django a Testear** | `social/serializers.py`                                                                                                                  |

---
## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados al feed y
retroalimentación en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.