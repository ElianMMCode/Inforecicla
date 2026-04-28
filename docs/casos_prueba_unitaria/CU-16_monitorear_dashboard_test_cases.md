# Casos de Prueba Unitarios - CU-16: Monitorear Dashboard General (KPIs)

## CU-16.1: Calcular Métricas de Usuarios Activos

### TC-CU16-01
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() correctamente cuenta el total de usuarios en el sistema cuando existen usuarios registrados.

**Precondiciones:**
- Base de datos de prueba inicializada
- No existen usuarios en el sistema inicialmente

**Pasos de Ejecución:**
1. Crear 5 usuarios de diferentes tipos (ADM, CIU, GECA) en la base de datos de prueba
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar el valor del campo "total_usuarios" en el resultado

**Datos de Prueba (Inputs):**
- Usuario 1: tipo_usuario = "ADM", email = "admin@test.com"
- Usuario 2: tipo_usuario = "CIU", email = "ciudadano1@test.com"
- Usuario 3: tipo_usuario = "CIU", email = "ciudadano2@test.com"
- Usuario 4: tipo_usuario = "GECA", email = "gestor1@test.com"
- Usuario 5: tipo_usuario = "ADM", email = "admin2@test.com"

**Resultado Esperado:**
- El campo "total_usuarios" en el diccionario retornado debe ser igual a 5

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

### TC-CU16-02
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() correctamente retorna 0 cuando no existen usuarios en el sistema.

**Precondiciones:**
- Base de datos de prueba inicializada
- No existen usuarios en el sistema

**Pasos de Ejecución:**
1. Asegurar que no existen usuarios en la base de datos de prueba
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar el valor del campo "total_usuarios" en el resultado

**Datos de Prueba (Inputs):**
- Ninguno (base de datos vacía)

**Resultado Esperado:**
- El campo "total_usuarios" en el diccionario retornado debe ser igual a 0

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

### TC-CU16-03
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() maneja correctamente excepciones al acceder a la tabla de usuarios.

**Precondiciones:**
- Base de datos de prueba configurada
- Simular una falla de conexión o error al acceder a la tabla Usuario

**Pasos de Ejecución:**
1. Configurar un mock que haga que Usuario.objects.count() lance una excepción
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar que el método retorna un diccionario con el campo "total_usuarios" igual a 0 (manejo de excepción)

**Datos de Prueba (Inputs):**
- Mock que lanza Exception al llamar a Usuario.objects.count()

**Resultado Esperado:**
- El campo "total_usuarios" en el diccionario retornado debe ser igual a 0
- El método no debe propagar la excepción

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

## CU-16.2: Agregar Volumen Histórico por Material

### TC-CU16-04
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() correctamente cuenta el total de materiales en el sistema cuando existen materiales registrados.

**Precondiciones:**
- Base de datos de prueba inicializada
- No existen materiales en el sistema inicialmente

**Pasos de Ejecución:**
1. Crear 3 materiales diferentes en la base de datos de prueba
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar el valor del campo "total_materiales" en el resultado

**Datos de Prueba (Inputs):**
- Material 1: nombre = "Plástico PET", categoria = "Plásticos"
- Material 2: nombre = "Cartón", categoria = "Papeles y Cartón"
- Material 3: nombre = "Vidrio", categoria = "Vidrios"

**Resultado Esperado:**
- El campo "total_materiales" en el diccionario retornado debe ser igual a 3

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

### TC-CU16-05
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() correctamente cuenta el total de tipos de materiales en el sistema.

**Precondiciones:**
- Base de datos de prueba inicializada
- No existen tipos de materiales en el sistema inicialmente

**Pasos de Ejecución:**
1. Crear 2 tipos de materiales diferentes en la base de datos de prueba
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar el valor del campo "total_tipos_material" en el resultado

**Datos de Prueba (Inputs):**
- Tipo 1: nombre = "Reciclable", estado = "ACTIVO"
- Tipo 2: nombre = "No Reciclable", estado = "ACTIVO"

**Resultado Esperado:**
- El campo "total_tipos_material" en el diccionario retornado debe ser igual a 2

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

### TC-CU16-06
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() correctamente cuenta el total de categorías de materiales en el sistema.

**Precondiciones:**
- Base de datos de prueba inicializada
- No existen categorías de materiales en el sistema inicialmente

**Pasos de Ejecución:**
1. Crear 4 categorías de materiales diferentes en la base de datos de prueba
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar el valor del campo "total_categorias_materiales" en el resultado

**Datos de Prueba (Inputs):**
- Categoría 1: nombre = "Plásticos", estado = "ACTIVO"
- Categoría 2: nombre = "Papeles y Cartón", estado = "ACTIVO"
- Categoría 3: nombre = "Vidrios", estado = "ACTIVO"
- Categoría 4: nombre = "Metales", estado = "ACTIVO"

**Resultado Esperado:**
- El campo "total_categorias_materiales" en el diccionario retornado debe ser igual a 4

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

## CU-16.3: Renderizar Componentes Gráficos

### TC-CU16-07
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() incluye todos los campos esperados en el resumen general.

**Precondiciones:**
- Base de datos de prueba inicializada
- Datos de prueba para todos los módulos

**Pasos de Ejecución:**
1. Poblar la base de datos con datos de prueba para usuarios, puntos ECA, materiales, etc.
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar que el diccionario retornado contiene todos los campos esperados

**Datos de Prueba (Inputs):**
- 2 usuarios
- 1 punto ECA
- 3 materiales
- 2 categorías de materiales
- 2 tipos de materiales
- 1 publicación
- 1 categoría de publicación

**Resultado Esperado:**
- El diccionario retornado debe contener los campos:
  - total_usuarios
  - total_puntos_eca
  - total_publicaciones
  - total_materiales
  - total_categorias_materiales
  - total_categorias_publicaciones
  - total_tipos_material
- Todos los campos deben tener valores numéricos >= 0

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

## EXT-14: Aplicar Filtro de Rango Temporal

### TC-CU16-08
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() actualmente no implementa filtrado por rango temporal (limitación conocida).

**Precondiciones:**
- Base de datos de prueba inicializada
- No hay parámetros de filtro implementados en el método actual

**Pasos de Ejecución:**
1. Llamar al método AdminDashboardService.obtener_resumen_general()
2. Verificar que el método no acepta parámetros de filtro de rango temporal
3. Verificar que el método retorna todos los registros sin filtrado por fecha

**Datos de Prueba (Inputs):**
- Ninguno (método no acepta parámetros)

**Resultado Esperado:**
- El método debe ser llamado sin parámetros
- El método debe retornar un diccionario con conteos totales (sin filtrado)
- Esta prueba documenta la limitación actual del método

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

## EXT-15: Cargar Datos desde Caché

### TC-CU16-09
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() actualmente no implementa caching (limitación conocida).

**Precondiciones:**
- Base de datos de prueba inicializada
- No hay implementación de caché en el método actual

**Pasos de Ejecución:**
1. Llamar al método AdminDashboardService.obtener_resumen_general() dos veces seguidas
2. Verificar que el método accede a la base de datos en cada llamada (no usa caché)
3. Verificar que no hay mecanismo de caché implementado

**Datos de Prueba (Inputs):**
- Ninguno (método no implementa caché)

**Resultado Esperado:**
- El método debe acceder a la base de datos en cada invocación
- No debe haber uso de mecanismos de caché como cache.get() o cache.set()
- Esta prueba documenta la limitación actual del método

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)

## EXT-16: Notificar Error - Tiempo de Consulta Excedido (Timeout)

### TC-CU16-10
**Descripción / Objetivo de la prueba:** Verificar que el servicio AdminDashboardService.obtener_resumen_general() maneja correctamente excepciones que podrían representar timeouts de consulta.

**Precondiciones:**
- Base de datos de prueba configurada
- Capacidad para simular excepciones de timeout en consultas a la base de datos

**Pasos de Ejecución:**
1. Configurar un mock que haga que una de las consultas de conteo lance una excepción simulando un timeout
2. Llamar al método AdminDashboardService.obtener_resumen_general()
3. Verificar que el método maneja la excepción y retorna un diccionario válido

**Datos de Prueba (Inputs):**
- Mock que lanza Exception en Usuario.objects.count() para simular timeout

**Resultado Esperado:**
- El método no debe propagar la excepción
- El diccionario retornado debe tener todos los campos esperados
- Los campos afectados por la excepción deben tener valor 0 (debido al manejo de excepción en el código actual)
- Otros campos deben tener sus valores correctos

**Módulo de Django a Testear:** apps/panel_admin/service.py (método obtener_resumen_general de AdminDashboardService)