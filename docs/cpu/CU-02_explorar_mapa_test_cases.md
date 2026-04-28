# Casos de Prueba - CU-02: Explorar Puntos ECA en Mapa

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-02: Explorar Puntos ECA en Mapa.

---

## Casos de Prueba

| ID del Test                    | TC-CU02.1-01: Solicitar Permiso de Geolocalización                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el sistema gestione correctamente la respuesta del navegador para obtener la ubicación del usuario.                                                                   |
| **Precondiciones**             | El navegador debe soportar la API de Geolocation.                                                                                                                                |
| **Pasos de Ejecución**         | 1. Acceder a la vista del mapa. 2. Aceptar la solicitud de permisos del navegador.<br>                                                                 |
| **Datos de Prueba**            | Respuesta positiva del objeto `navigator.geolocation`.                                                                                                                                          |
| **Resultado Esperado**         | El sistema captura latitud y longitud del ciudadano para centrar la búsqueda.                                                                       |
| **Módulo de Django a Testear** | `map/static/js/map_logic.js` (Frontend integration), `map/views.py`                                                                                                                                    |

| ID del Test                    | TC-CU02.2-01: Renderizar Mapa Base                                                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la correcta carga del mapa base mediante la API externa (Google Maps/Leaflet).                                                                                     |
| **Precondiciones**             | API Key válida configurada en el entorno.                                                                                                                         |
| **Pasos de Ejecución**         | 1. Cargar la página del mapa. 2. Verificar la inicialización del contenedor del mapa.<br>                                                                 |
| **Datos de Prueba**            | Parámetros de inicialización (Zoom: 12, Center: Coordenadas del usuario).                                                                                                                                                  |
| **Resultado Esperado**         | El contenedor del mapa se renderiza sin errores de consola y muestra la capa base.                                                                                                                 |
| **Módulo de Django a Testear** | `map/templates/map.html`                                                                                                                                           |

| ID del Test                    | TC-CU02.3-01: Consultar ECAs Activos en Base de Datos                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que la API del backend retorne solo los puntos ECA que están marcados como activos.                                                                                                              |
| **Precondiciones**             | Existen puntos ECA en la BD (algunos activos y otros inactivos).                                                                                                          |
| **Pasos de Ejecución**         | 1. Realizar petición GET al endpoint de puntos de reciclaje.<br>                                                                 |
| **Datos de Prueba**            | Query param `is_active=true`.                                                                                                                                                                |
| **Resultado Esperado**         | Código HTTP 200. El JSON contiene una lista de objetos con `id`, `nombre`, `latitud` y `longitud`. Los puntos inactivos no aparecen.                                                                                                                                           |
| **Módulo de Django a Testear** | `map/views.py`, `map/models.py`                                                                                                                                          |

| ID del Test                    | TC-EXT03-01: Aplicar Filtro por Material                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar que al seleccionar un material (ej. Plástico), se actualicen los marcadores del mapa.                                                                     |
| **Precondiciones**             | Existen ECAs registrados que reciben distintos materiales.                                                                                        |
| **Pasos de Ejecución**         | 1. Seleccionar "Plástico" en el filtro de materiales. 2. Verificar la respuesta del servidor.<br>                                                                 |
| **Datos de Prueba**            | Query param `material="plastico"`.                                                                                                                                     |
| **Resultado Esperado**         | El sistema retorna solo los ECAs que aceptan plástico. El mapa remueve los marcadores que no coinciden.                                                                                               |
| **Módulo de Django a Testear** | `map/views.py`                                                                                                                  |

| ID del Test                    | TC-EXT04-01: Manejar Geolocalización Denegada                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que el sistema asigne el centro predeterminado (Bogotá) si el usuario deniega el permiso.                                                                     |
| **Precondiciones**             | El usuario hace clic en "Bloquear" permisos de ubicación.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Denegar permiso de geolocalización. 2. Verificar el centro del mapa.<br>                                                                 |
| **Datos de Prueba**            | Error de geolocalización `PERMISSION_DENIED`.                                                                                                                                     |
| **Resultado Esperado**         | El mapa se inicializa en las coordenadas por defecto configuradas (Bogotá: 4.6097, -74.0817).                                                                                               |
| **Módulo de Django a Testear** | `map/static/js/map_logic.js`                                                                                                                  |

| ID del Test                    | TC-EXT05-01: Mostrar Error de Carga - API Caída                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que se informe al usuario si el proveedor de mapas no está disponible.                                                                     |
| **Precondiciones**             | Simular fallo de conexión con el servidor de mapas o API Key inválida.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Intentar cargar el mapa con red limitada o bloqueando el script de la API.<br>                                                                 |
| **Datos de Prueba**            | Fallo de carga del script externo.                                                                                                                                     |
| **Resultado Esperado**         | Se muestra un mensaje de alerta: "Servicio de mapas temporalmente fuera de servicio".                                                                                               |
| **Módulo de Django a Testear** | `map/templates/map.html`                                                                                                                  |

| ID del Test                    | TC-EXT06-01: Notificar 'Sin Resultados' - Filtro sin coincidencias                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la respuesta cuando no existen puntos ECA que coincidan con el filtro de material aplicado.                                                                     |
| **Precondiciones**             | Aplicar filtros restrictivos (ej. Material: "Pilas" en una zona sin puntos).                                                                                                                        |
| **Pasos de Ejecución**         | 1. Aplicar filtro sin coincidencias.<br>                                                                 |
| **Datos de Prueba**            | Combinación de material y coordenadas sin resultados.                                                                                                                                     |
| **Resultado Esperado**         | Código HTTP 200 con lista vacía `[]`. El frontend muestra el mensaje: "No se encontraron puntos de reciclaje cercanos".                                                                                               |
| **Módulo de Django a Testear** | `map/views.py`                                                                                                                  |

| ID del Test                    | TC-EXT06-02: Notificar 'Sin Resultados' - Carga inicial sin ECAs en el área                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar la respuesta cuando no existen puntos ECA activos en el área geográfica del usuario al cargar el mapa por primera vez (sin filtros aplicados).                                                                     |
| **Precondiciones**             | No existen puntos ECA activos registrados en la BD dentro del rango de coordenadas del usuario.                                                                                                                        |
| **Pasos de Ejecución**         | 1. Acceder a la vista del mapa con geolocalización activa. 2. Esperar la carga inicial de puntos (sin aplicar ningún filtro).<br>                                                                 |
| **Datos de Prueba**            | Coordenadas del usuario en zona sin ECAs registrados. BD sin puntos activos en ese rango.                                                                                                                                     |
| **Resultado Esperado**         | Código HTTP 200 con lista vacía `[]`. El frontend muestra el mensaje: "No se encontraron puntos de reciclaje cercanos".                                                                                               |
| **Módulo de Django a Testear** | `map/views.py`, `map/models.py`                                                                                                                  |

---
## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados a la exploración de
puntos ECA en mapa en InfoRecicla. Asegúrese de preparar los datos iniciales
correctamente antes de su ejecución.
