# Casos de Prueba Unitarios e Integrales: CU-18 Gestionar Chat Interno en Tiempo Real

## Módulo: Mensajería P2P (Django Channels)

### 1. Establecer Conexión de Sockets (Handshake)
* **ID del Test:** TC-CU18.1-01
* **Descripción / Objetivo:** Validar la elevación de protocolo de HTTP a WS y la autenticación del usuario en el socket.
* **Precondiciones:** Usuario autenticado en el sistema (con token o cookie de sesión válida). Servidor ASGI (Daphne) y Redis/Channel Layer en ejecución.
* **Pasos de Ejecución:** 1. El cliente inicia una petición de conexión WebSocket (`ws://.../ws/chat/<room_name>/`).
  2. El middleware de autenticación de Channels procesa las credenciales.
* **Datos de Prueba (Inputs JSON):** Headers de la petición de conexión inicial (Handshake).
* **Resultado Esperado:** Código HTTP 101 Switching Protocols. El socket se acepta (`self.accept()`) y el usuario se añade al grupo de Channels correspondiente.
* **Módulo de Django a Testear:** `chat/consumers.py`, `chat/routing.py`

### 2. Cargar Historial de Mensajes Persistidos
* **ID del Test:** TC-CU18.2-01
* **Descripción / Objetivo:** Verificar que al conectar se recuperen los mensajes previos de la base de datos para renderizar el historial.
* **Precondiciones:** Conexión WebSocket establecida exitosamente. Existen registros previos en la tabla de mensajes entre el Ciudadano y el Gestor ECA.
* **Pasos de Ejecución:** 1. Conectar al WebSocket del chat específico.
  2. Verificar el primer payload que emite el backend inmediatamente después de aceptar la conexión.
* **Datos de Prueba (Inputs JSON):** Evento de conexión al room de chat.
* **Resultado Esperado:** El backend envía un payload JSON tipo `{"type": "history", "messages": [...]}` con los últimos N mensajes ordenados cronológicamente.
* **Módulo de Django a Testear:** `chat/consumers.py`, `chat/models.py`

### 3. Transmitir / Recibir Mensajes (WebSockets)
* **ID del Test:** TC-CU18.3-01
* **Descripción / Objetivo:** Validar el envío y recepción de payloads JSON en tiempo real entre el UserC (Ciudadano) y UserG (Gestor).
* **Precondiciones:** Ambos usuarios conectados al mismo grupo (Room) en el Channel Layer.
* **Pasos de Ejecución:** 1. UserC envía un payload JSON a través del socket con su mensaje.
  2. El backend procesa el mensaje, lo guarda en BD y lo emite al Channel Layer.
  3. UserG recibe el payload.
* **Datos de Prueba (Inputs JSON):** `{"action": "chat_message", "message": "Hola, ¿tienen espacio para cartón?"}`
* **Resultado Esperado:** UserG recibe en tiempo real el payload: `{"type": "chat_message", "message": "Hola, ¿tienen espacio para cartón?", "sender": "UserC"}`. El mensaje se persiste en la base de datos.
* **Módulo de Django a Testear:** `chat/consumers.py`, `chat/models.py`

### 4. Emitir Notificación de Nuevo Mensaje
* **ID del Test:** TC-CU18.4-01
* **Descripción / Objetivo:** Validar la lógica de estado: si el destinatario no está en la vista activa, la notificación se renderiza como indicador global.
* **Precondiciones:** UserG está conectado a la plataforma (WebSocket de notificaciones globales activo), pero no tiene abierta la sala de chat de UserC.
* **Pasos de Ejecución:** 1. UserC envía un mensaje a UserG.
  2. El backend identifica que UserG no está suscrito al grupo del chat específico.
  3. El backend envía el evento al grupo global de notificaciones de UserG.
* **Datos de Prueba (Inputs JSON):** Mensaje enviado desde UserC.
* **Resultado Esperado:** UserG recibe un payload de notificación en su socket global `{"type": "notification", "content": "Nuevo mensaje de UserC"}` para actualizar la campanita/indicador.
* **Módulo de Django a Testear:** `chat/consumers.py`, `chat/signals.py`

### 5. Bloquear Envío - Mensaje Vacío / Archivo no Soportado
* **ID del Test:** TC-EXT39-01
* **Descripción / Objetivo:** Validar las reglas de integridad de datos en el stream para evitar envíos en blanco o maliciosos.
* **Precondiciones:** Conexión de socket activa.
* **Pasos de Ejecución:** 1. Enviar un payload con el campo de texto vacío.
  2. Enviar un payload intentando subir un archivo ejecutable (si aplica).
* **Datos de Prueba (Inputs JSON):** `{"action": "chat_message", "message": "   "}` o `{"action": "send_file", "file_type": "application/x-msdownload"}`
* **Resultado Esperado:** El backend no persiste nada en BD. Devuelve un payload de error al remitente `{"type": "error", "message": "El mensaje no puede estar vacío"}`.
* **Módulo de Django a Testear:** `chat/consumers.py`

### 6. Notificar Error - Pérdida de Conexión
* **ID del Test:** TC-EXT40-01
* **Descripción / Objetivo:** Validar que el sistema maneje el cierre abrupto del socket (falla de red) y el frontend pueda intentar la reconexión.
* **Precondiciones:** Conexión de socket activa.
* **Pasos de Ejecución:** 1. Simular la caída del servidor de Redis o forzar el cierre del socket (`socket.close()`).
* **Datos de Prueba (Inputs JSON):** Código de cierre del socket (Ej. `1006 Abnormal Closure`).
* **Resultado Esperado:** Se ejecuta el método `disconnect()` en el consumer, limpiando la sesión del usuario en el Channel Layer. El cliente frontend debe emitir una alerta visual "Conexión perdida, reconectando...".
* **Módulo de Django a Testear:** `chat/consumers.py`