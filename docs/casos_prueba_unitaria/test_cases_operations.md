# Casos de Prueba Unitarios: Módulo de Inventario y Operaciones (CU-07)

## CU-07A: Registrar Nueva Transacción / CU-07.3: Actualizar Historial de Operaciones

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-CU07A-01 | Validar que el Gestor ECA pueda registrar correctamente una nueva transacción (compra) y que el sistema actualice automáticamente el historial de operaciones y el stock. | El Gestor ECA está autenticado en el sistema. El Punto ECA cuenta con capacidad disponible en su inventario. | 1. Iniciar sesión y acceder al módulo de registro de transacciones.<br>2. Enviar una petición POST al endpoint de creación de transacción.<br>3. Ingresar la información del material, la cantidad y el tipo de operación. | `tipo: "compra"`<br>`material: "Plástico PET"`<br>`cantidad_kg: 10` | El sistema responde con el código HTTP 201 (Created). Se crea un registro en el historial de operaciones y el stock de "Plástico PET" del inventario se incrementa en 10kg. | `apps/operations/views.py` y `apps/operations/service.py` |

## CU-07B: Editar Transacción Existente / CU-07.2: Calcular Delta y Recalcular Stock

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-CU07B-01 | Validar la regla de negocio para el cálculo correcto del Delta al modificar la cantidad de una transacción ya existente, evitando sumar de manera duplicada el stock. | Existe previamente una transacción de compra exitosa registrada de 10kg de material. | 1. Acceder al registro histórico de la transacción.<br>2. Enviar una petición PUT/PATCH al endpoint de edición.<br>3. Actualizar el valor de la cantidad comprada de 10kg a 15kg. | `transaccion_id: 1`<br>`nueva_cantidad_kg: 15` | El sistema identifica internamente un Delta de +5kg. Se modifica la transacción y el stock se incrementa únicamente en 5kg adicionales. El sistema responde con el código HTTP 200 (OK). | `apps/operations/service.py` y `apps/inventory/models.py` |

## CU-07.1 / EXT-07: Validar Datos de Entrada / Mostrar Error - Datos Inválidos

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-EXT07-01 | Validar que el sistema rechace cualquier transacción que contenga datos numéricos inválidos (nulos o negativos) y lance la excepción correspondiente. | El Gestor ECA se encuentra en el formulario/endpoint de transacciones. | 1. Enviar una petición POST para crear una transacción.<br>2. Introducir valores negativos en la cantidad de material. | `tipo: "compra"`<br>`material: "Cartón"`<br>`cantidad_kg: -5` | El serializer/formulario rechaza la petición. Se retorna un error HTTP 400 (Bad Request) con un mensaje como "Los datos son inválidos: La cantidad debe ser superior a 0". No se altera el inventario. | `apps/operations/serializers.py` (o forms) y `apps/operations/views.py` |

## EXT-08: Bloquear Acción - Límite de Capacidad Superado

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-EXT08-01 | Garantizar que el sistema bloquee el registro de una transacción de compra si la cantidad ingresada ocasionaría que el Punto ECA supere su capacidad máxima volumétrica/peso. | El inventario actual del Punto ECA se encuentra al 98% de su capacidad total (ej. quedan únicamente 2kg de almacenamiento disponible). | 1. Intentar registrar una nueva compra mediante una petición POST.<br>2. Ingresar una cantidad superior al espacio disponible en el inventario. | `tipo: "compra"`<br>`material: "Vidrio"`<br>`cantidad_kg: 10` | El sistema bloquea la acción antes del guardado y retorna un error HTTP 400 o 409 (Conflict). Se devuelve el mensaje "Límite de capacidad superado". El stock actual no se modifica. | `apps/inventory/models.py` (métodos de validación de capacidad) y `apps/operations/service.py` |

## EXT-09: Bloquear Acción - Stock Insuficiente

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-EXT09-01 | Comprobar que no sea posible registrar una transacción de tipo "Venta" si la cantidad de material a extraer supera las existencias físicas en la base de datos. | El inventario registra que hay únicamente 15kg de "Plástico PET" en existencia. | 1. Enviar una petición POST para asentar una operación de salida/venta.<br>2. Seleccionar una cantidad que exceda el material disponible. | `tipo: "venta"`<br>`material: "Plástico PET"`<br>`cantidad_kg: 25` | El sistema bloquea la operación y retorna un error HTTP 400 (Bad Request). Se muestra un aviso al usuario indicando "Stock insuficiente para realizar esta operación". El inventario permanece en 15kg. | `apps/operations/service.py` y `apps/inventory/models.py` |