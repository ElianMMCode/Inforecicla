# Casos de Prueba Unitarios: Módulo de Inventario y Operaciones (CU-07)

---

## CU-07A: Registrar Nueva Transacción

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-CU07A-01 | Validar que el Gestor ECA pueda registrar correctamente una nueva transacción de compra y que el sistema actualice el stock del inventario. | El Gestor ECA está autenticado. El Punto ECA tiene inventario con capacidad disponible. | 1. Iniciar sesión y acceder al módulo de registro de transacciones.<br>2. Enviar una petición POST al endpoint de creación de compra.<br>3. Ingresar el inventario, cantidad, precio y fecha. | `inventarioId: <uuid>`<br>`cantidad: 10`<br>`precioCompra: 500`<br>`fechaCompra: "2026-04-26T10:00:00"` | El servicio retorna `{"error": False, "status": 201}`. Se crea un registro en `CompraInventario` y el `stock_actual` del inventario se incrementa en 10 unidades. | `apps/operations/service.py` (CompraInventarioService.registro_compra), `apps/operations/models.py` (CompraInventario) |

---

## CU-07B: Editar Transacción Existente

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-CU07B-01 | Validar la regla de negocio para el cálculo correcto del Delta al modificar la cantidad de una compra existente, evitando sumar de manera duplicada el stock. | Existe previamente una `CompraInventario` de 10 unidades. El stock actual del inventario ya refleja esas 10 unidades. | 1. Acceder al registro de la compra existente.<br>2. Llamar a `CompraInventarioService.editar_compra` con la nueva cantidad.<br>3. Verificar el stock resultante. | `compraId: <uuid>`<br>`cantidad: 15`<br>`precioCompra: 500`<br>`fechaCompra: "2026-04-26T10:00:00"` | El servicio calcula un delta interno de +5. El `stock_actual` del inventario se incrementa únicamente en 5 unidades adicionales. Retorna `{"error": False, "status": 200}`. | `apps/operations/service.py` (CompraInventarioService.editar_compra, actualizar_stock_por_compra), `apps/inventory/models.py` (Inventario.stock_actual) |

---

## CU-07.1: Validar Datos de Entrada

> Sub-caso de uso compartido por CU-07A y CU-07B. Se activa antes de cualquier escritura en BD.
> Los tests de fallo de esta validación se documentan bajo **EXT-07**.

---

## CU-07.2: Calcular Delta y Recalcular Stock

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-CU07A-02 | Validar que al registrar una compra nueva (sin `cantidad_original`), el delta aplicado al stock sea igual a la cantidad completa ingresada. | Inventario con `stock_actual=0` y `capacidad_maxima=100`. | 1. Llamar a `CompraInventarioService.actualizar_stock_por_compra` con `cantidad=10` y sin `cantidad_original`.<br>2. Verificar el stock resultante. | `inventario.stock_actual: 0`<br>`cantidad: 10`<br>`cantidad_original: None` | El método calcula `delta = 10` (cantidad completa). El `stock_actual` pasa de 0 a 10. Retorna `None` (sin error). | `apps/operations/service.py` (CompraInventarioService.actualizar_stock_por_compra) |

---

## CU-07.3: Actualizar Historial de Operaciones

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-CU07-03A | Validar que al registrar una compra exitosa se persiste un registro en el historial (`CompraInventario`). | Inventario válido con capacidad disponible. | 1. Llamar a `CompraInventarioService.registro_compra` con datos válidos.<br>2. Consultar `CompraInventario.objects.filter(inventario=inventario)`. | `inventarioId: <uuid>`<br>`cantidad: 10`<br>`precioCompra: 500`<br>`fechaCompra: "2026-04-26T10:00:00"` | Existe exactamente 1 registro nuevo en `CompraInventario` para ese inventario, con `cantidad=10` y la fecha correcta. | `apps/operations/models.py` (CompraInventario), `apps/operations/service.py` (CompraInventarioService.registro_compra) |
| TC-CU07-03B | Validar que al registrar una venta exitosa se persiste un registro en el historial (`VentaInventario`). | Inventario válido con `stock_actual >= 10`. | 1. Llamar a `VentaInventarioService.registrar_venta` con datos válidos.<br>2. Consultar `VentaInventario.objects.filter(inventario=inventario)`. | `inventarioId: <uuid>`<br>`cantidad: 10`<br>`precioVenta: 800`<br>`fechaVenta: "2026-04-26T10:00:00"` | Existe exactamente 1 registro nuevo en `VentaInventario` para ese inventario, con `cantidad=10` y la fecha correcta. | `apps/operations/models.py` (VentaInventario), `apps/operations/service.py` (VentaInventarioService.registrar_venta) |

---

## EXT-07: Mostrar Error - Datos Inválidos

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-EXT07-01 | Validar que el sistema rechace una transacción con cantidad negativa o igual a cero y retorne el mensaje de error correspondiente. | El Gestor ECA se encuentra en el formulario/endpoint de transacciones. | 1. Llamar a `CompraInventarioService.registro_compra` con `cantidad=-5`.<br>2. Verificar la respuesta del servicio. | `inventarioId: <uuid>`<br>`cantidad: -5`<br>`precioCompra: 500`<br>`fechaCompra: "2026-04-26T10:00:00"` | El servicio retorna `{"error": True, "mensaje": "Valores inválidos.", "status": 400}`. No se crea ningún registro en `CompraInventario` ni se altera el stock. | `apps/operations/service.py` (CompraInventarioService.registro_compra - validación `cantidad <= 0`) |

---

## EXT-08: Bloquear Acción - Límite de Capacidad Superado

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-EXT08-01 | Garantizar que el sistema bloquee el registro de una nueva compra si la cantidad ingresada superaría la capacidad máxima del inventario. | Inventario con `stock_actual=98` y `capacidad_maxima=100` (solo 2 unidades disponibles). | 1. Llamar a `CompraInventarioService.registro_compra` con `cantidad=10`.<br>2. Verificar la respuesta del servicio. | `inventarioId: <uuid>`<br>`cantidad: 10`<br>`precioCompra: 500`<br>`fechaCompra: "2026-04-26T10:00:00"` | El servicio retorna `{"error": True, "mensaje": "No se puede realizar la compra porque el stock superaría la capacidad máxima del inventario.", "status": 400}`. El `stock_actual` permanece en 98. | `apps/operations/service.py` (CompraInventarioService.actualizar_stock_por_compra), `apps/inventory/models.py` (Inventario.capacidad_maxima) |
| TC-EXT08-02 | Garantizar que el sistema bloquee la edición de una compra si la nueva cantidad ocasionaría que el stock supere la capacidad máxima del inventario. | Inventario con `stock_actual=95` y `capacidad_maxima=100`. Compra existente de `cantidad_original=5`. | 1. Llamar a `CompraInventarioService.editar_compra` intentando cambiar la cantidad de 5 a 15 (delta=+10, nuevo stock=105).<br>2. Verificar la respuesta. | `compraId: <uuid>`<br>`cantidad: 15`<br>`precioCompra: 500`<br>`fechaCompra: "2026-04-26T10:00:00"` | El servicio retorna `{"error": True, "mensaje": "No se puede realizar la compra porque el stock superaría la capacidad máxima del inventario.", "status": 400}`. El `stock_actual` permanece en 95. | `apps/operations/service.py` (CompraInventarioService.actualizar_stock_por_compra), `apps/inventory/models.py` (Inventario.capacidad_maxima) |

---

## EXT-09: Bloquear Acción - Stock Insuficiente

| ID del Test | Descripción / Objetivo de la prueba | Precondiciones | Pasos de Ejecución | Datos de Prueba (Inputs) | Resultado Esperado | Módulo de Django a Testear |
|-------------|-------------------------------------|----------------|---------------------|--------------------------|--------------------|----------------------------|
| TC-EXT09-01 | Comprobar que no sea posible registrar una nueva venta si la cantidad supera el stock existente. | Inventario con `stock_actual=15`. | 1. Llamar a `VentaInventarioService.registrar_venta` con `cantidad=25`.<br>2. Verificar la respuesta del servicio. | `inventarioId: <uuid>`<br>`cantidad: 25`<br>`precioVenta: 800`<br>`fechaVenta: "2026-04-26T10:00:00"` | El servicio retorna `{"error": True, "mensaje": "No hay stock suficiente para realizar la venta. Stock actual: 15.0", "status": 400}`. El `stock_actual` permanece en 15. | `apps/operations/service.py` (VentaInventarioService.actualizar_stock_por_venta), `apps/inventory/models.py` (Inventario.stock_actual) |
| TC-EXT09-02 | Comprobar que no sea posible editar una venta si la nueva cantidad supera el stock disponible (stock actual + cantidad original de la venta). | Inventario con `stock_actual=10`. Venta existente con `cantidad_original=5` (stock disponible para reasignar = 10+5=15). | 1. Llamar a `VentaInventarioService.editar_venta` intentando cambiar la cantidad de 5 a 20 (supera los 15 disponibles).<br>2. Verificar la respuesta. | `ventaId: <uuid>`<br>`cantidad: 20`<br>`precioVenta: 800`<br>`fechaVenta: "2026-04-26T10:00:00"` | El servicio retorna `{"error": True, "mensaje": "No hay stock suficiente para realizar la venta. Stock disponible: 15.0", "status": 400}`. El `stock_actual` permanece en 10. | `apps/operations/service.py` (VentaInventarioService.actualizar_stock_por_venta), `apps/inventory/models.py` (Inventario.stock_actual) |
