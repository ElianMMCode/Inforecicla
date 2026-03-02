/**
 * Guía de Uso - Select2 en el Modal de Calendario
 *
 * Este archivo documenta el flujo completo de uso de Select2 en el modal
 * de creación de eventos del calendario.
 */

// ============================================
// 1. FLUJO DE INICIALIZACIÓN
// ============================================
/*
 * Al cargar la página:
 *
 * 1. Se ejecuta DOMContentLoaded
 * 2. Se verifica que jQuery y Select2 estén disponibles
 * 3. Se obtienen los inputs ocultos con puntoEcaId y usuarioId
 * 4. Se inicializa FullCalendar
 * 5. Se registran los listeners de eventos
 */


// ============================================
// 2. FLUJO AL HACER CLIC EN UNA FECHA
// ============================================
/*
 * Cuando el usuario hace clic en una fecha del calendario:
 *
 * 1. Se dispara el evento select() de FullCalendar
 * 2. Se llama a abrirModal(fecha)
 * 3. abrirModal():
 *    - Asigna la fecha al input de fecha
 *    - Muestra el modal
 *    - Llama a cargarMateriales()
 *    - Llama a cargarCentrosAcopio()
 *    - Después de 100ms, llama a inicializarSelect2()
 */


// ============================================
// 3. CARGA DE MATERIALES
// ============================================
/*
 * Función: cargarMateriales()
 * URL: /punto-eca/catalogo/inventario/materiales/buscar?puntoId={puntoId}
 * Método: GET
 *
 * Respuesta esperada:
 * [
 *   {
 *     materialId: 'f981963d-97ed-11f0-a638-c4cbe12e39be',
 *     nmbMaterial: 'Botella PET transparente',
 *     dscMaterial: 'Botella PET clara, enjuagada y sin etiqueta',
 *     ...
 *   },
 *   ...
 * ]
 *
 * Después de cargar:
 * 1. Se llena el select con las opciones
 * 2. Se destruye cualquier instancia anterior de Select2
 * 3. Se inicializa Select2 en el select
 */


// ============================================
// 4. CARGA DE CENTROS DE ACOPIO
// ============================================
/*
 * Función: cargarCentrosAcopio()
 * URL: /punto-eca/{puntoId}/centros-acopio
 * Método: GET
 *
 * Respuesta esperada:
 * [
 *   {
 *     cntAcpId: 'b1c2d3e4-f5a6-47b9-c12d-cdef01234501',
 *     nombreCntAcp: 'Centro de Acopio Sur',
 *     tienePuntoEca: true  // true = del punto, false = global
 *   },
 *   ...
 * ]
 *
 * Después de cargar:
 * 1. Se llenan los selects con las opciones
 * 2. Se añade "(del punto)" o "(global)" según corresponda
 * 3. Se destruye cualquier instancia anterior de Select2
 * 4. Se inicializa Select2 en el select
 */


// ============================================
// 5. INICIALIZACIÓN DE SELECT2
// ============================================
/*
 * Función: inicializarSelect2()
 *
 * Se inicializa Select2 en tres selects:
 *
 * 1. selectMaterial
 * 2. selectCentroAcopio
 * 3. selectTipoRepeticion
 *
 * Configuración para todos:
 * {
 *   dropdownParent: $('#modalCrearEvento'),  // El dropdown aparece dentro del modal
 *   language: 'es',                           // Idioma español
 *   width: '100%',                            // Ancho completo
 *   minimumResultsForSearch: 1,               // Mostrar búsqueda siempre
 *   placeholder: 'Seleccionar...',            // Texto placeholder
 *   allowClear: true,                         // Permitir limpiar (false para repetición)
 *   theme: 'bootstrap-5',                     // Tema Bootstrap 5
 *   containerCssClass: 'select2-custom'       // Clase personalizada
 * }
 */


// ============================================
// 6. GUARDADO DE EVENTO
// ============================================
/*
 * Función: guardarEvento()
 *
 * Se dispara cuando el usuario hace clic en "Guardar Evento"
 *
 * Validaciones:
 * - selectMaterial.value no está vacío
 * - inputTitulo tiene contenido
 *
 * Datos que se envían:
 * {
 *   materialId: string,           // Material seleccionado
 *   puntoEcaId: string,          // ID del punto
 *   usuarioId: string,           // ID del usuario
 *   centroAcopioId: string|null, // Centro seleccionado (opcional)
 *   titulo: string,              // Título del evento
 *   descripcion: string,         // Descripción opcional
 *   fechaInicio: ISO string,     // Fecha y hora inicio
 *   fechaFin: ISO string,        // Fecha y hora fin
 *   tipoRepeticion: enum,        // SIN_REPETICION|SEMANAL|QUINCENAL|MENSUAL
 *   color: string                // Color del evento (#28a745)
 * }
 *
 * URL POST: /api/eventos/crear-venta
 *
 * Si es exitoso:
 * 1. Se recarga el calendario con refetchEvents()
 * 2. Se cierra el modal
 * 3. Se limpia el formulario
 */


// ============================================
// 7. ESTILOS PERSONALIZADOS
// ============================================
/*
 * Archivo: /css/PuntoECA/select2-custom.css
 *
 * Clases CSS principales:
 *
 * .select2-custom
 *   - Ancho 100%
 *
 * .select2-custom .select2-container--bootstrap-5 .select2-selection
 *   - Bordes 2px color #dee2e6
 *   - Altura mínima 38px
 *   - Transición suave
 *
 * .select2-container--bootstrap-5 .select2-results__option--highlighted
 *   - Color de fondo verde #28a745
 *   - Color de texto blanco
 */


// ============================================
// 8. TROUBLESHOOTING
// ============================================
/*
 * Problema: "jQuery is not defined"
 *   Solución: Asegúrese que jQuery se carga antes de Select2
 *   Orden correcto en HTML:
 *     1. jQuery
 *     2. Bootstrap JS
 *     3. Select2 JS
 *     4. fullcalendar.js
 *
 * Problema: "Select2 is not defined"
 *   Solución: Asegúrese que Select2 se carga después de jQuery
 *
 * Problema: El dropdown aparece fuera del modal
 *   Solución: Está configurado dropdownParent: $('#modalCrearEvento')
 *   Si no funciona, verificar que el ID del modal es 'modalCrearEvento'
 *
 * Problema: Los datos no se cargan en los selects
 *   Solución: Revisar la consola del navegador para ver los errores
 *   Verificar que los endpoints devuelven JSON válido
 *
 * Problema: Select2 no se ve con estilos
 *   Solución: Asegúrese que se ha incluido select2-custom.css
 *   Verificar que Bootstrap 5 está cargado
 */


// ============================================
// 9. EJEMPLOS DE DEBUGGING
// ============================================
/*
 * Abrir consola del navegador (F12) y ejecutar:
 *
 * // Ver si jQuery está disponible
 * console.log(typeof jQuery);
 *
 * // Ver si Select2 está disponible
 * console.log(typeof jQuery.fn.select2);
 *
 * // Ver datos de Select2 en un elemento
 * console.log($('#selectMaterial').select2('data'));
 *
 * // Obtener valor seleccionado
 * console.log($('#selectMaterial').val());
 *
 * // Establecer valor programáticamente
 * $('#selectMaterial').val('valor').trigger('change');
 *
 * // Destruir y reinicializar Select2
 * $('#selectMaterial').select2('destroy');
 * $('#selectMaterial').select2({...opciones...});
 */

