// Script para modal de centros propios - Versión simplificada y directa
console.log('🚀 [MODAL-CENTROS] Script cargado');

let centroActualEnEdicion = null;

// Función auxiliar para obtener elemento de forma segura
function getElementSafe(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`⚠️ [MODAL-CENTROS] Elemento no encontrado: ${id}`);
    }
    return element;
}

// Función simple para abrir el modal
window.abrirDetallesCentro = function(event, centroId) {
    event.preventDefault();
    event.stopPropagation();

    console.log(`👀 [MODAL-CENTROS] Abriendo detalles del centro: ${centroId}`);

    // Verificar que el modal existe
    const modalElement = document.getElementById('modalDetallesCentroPropio');
    if (!modalElement) {
        console.error('❌ [MODAL-CENTROS] Modal no encontrado en el DOM');
        alert('Error: El modal de detalles no está disponible');
        return;
    }

    // Buscar la fila del centro
    let fila = null;
    fila = document.querySelector(`tr[data-centro-id="${centroId}"]`);
    if (!fila) {
        fila = document.querySelector(`tr.fila-centro-propio[data-centro-id="${centroId}"]`);
    }
    if (!fila) {
        fila = document.querySelector(`tr.fila-centro-global[data-centro-id="${centroId}"]`);
    }

    if (!fila) {
        console.error(`❌ [MODAL-CENTROS] Fila no encontrada para ID: ${centroId}`);
        alert('Error: No se encontraron los datos del centro');
        return;
    }

    // Obtener las celdas
    const celdas = fila.querySelectorAll('td');
    console.log(`📊 [MODAL-CENTROS] Número de celdas encontradas: ${celdas.length}`);

    if (celdas.length < 5) {
        console.error(`❌ [MODAL-CENTROS] No hay suficientes celdas (encontradas: ${celdas.length})`);
        return;
    }

    try {
        // Obtener todos los elementos del modal de forma segura
        const elementIds = [
            'inputCentroId',
            'inputNombreCentro',
            'inputTipoCentro',
            'inputLocalidadCentro',
            'inputTelefonoCentro',
            'inputEmailCentro',
            'inputContactoCentro',
            'inputNotasCentro',
            'editNombreCentro',
            'editTipoCentro',
            'editLocalidadCentro',
            'editTelefonoCentro',
            'editEmailCentro',
            'editContactoCentro',
            'editNotasCentro'
        ];

        const elementos = {};
        for (const id of elementIds) {
            elementos[id] = getElementSafe(id);
            if (!elementos[id]) {
                throw new Error(`Elemento ${id} no encontrado en el DOM`);
            }
        }

        console.log('✅ [MODAL-CENTROS] Todos los elementos del modal encontrados');

        // Guardar ID del centro en edición
        centroActualEnEdicion = centroId;

        // Limpiar campos de lectura
        elementos.inputCentroId.value = '';
        elementos.inputNombreCentro.textContent = '—';
        elementos.inputTipoCentro.textContent = '—';
        elementos.inputLocalidadCentro.textContent = '—';
        elementos.inputTelefonoCentro.textContent = '—';
        elementos.inputTelefonoCentro.href = '#';
        elementos.inputEmailCentro.textContent = '—';
        elementos.inputEmailCentro.href = 'mailto:#';
        elementos.inputContactoCentro.textContent = '—';
        elementos.inputNotasCentro.textContent = '—';

        // Limpiar campos de edición
        elementos.editNombreCentro.value = '';
        elementos.editTipoCentro.value = '';
        elementos.editLocalidadCentro.value = '';
        elementos.editTelefonoCentro.value = '';
        elementos.editEmailCentro.value = '';
        elementos.editContactoCentro.value = '';
        elementos.editNotasCentro.value = '';

        // Establecer ID
        elementos.inputCentroId.value = centroId;

        // Nombre (celda 0)
        const nombre = celdas[0]?.textContent?.trim() || '—';
        elementos.inputNombreCentro.textContent = nombre;
        elementos.editNombreCentro.value = nombre !== '—' ? nombre : '';
        console.log(`📝 Nombre: ${nombre}`);

        // Tipo (celda 1)
        const tipoBadge = celdas[1]?.querySelector('.badge');
        const tipo = tipoBadge?.textContent?.trim() || celdas[1]?.textContent?.trim() || '—';
        elementos.inputTipoCentro.textContent = tipo;
        elementos.editTipoCentro.value = tipo !== '—' ? tipo : '';
        console.log(`📝 Tipo: ${tipo}`);

        // Localidad
        const localidad = fila.getAttribute('data-localidad') || '—';
        elementos.inputLocalidadCentro.textContent = localidad;
        elementos.editLocalidadCentro.value = localidad !== '—' ? localidad : '';
        console.log(`📝 Localidad: ${localidad}`);

        // Teléfono (celda 3)
        const telefonoLink = celdas[3]?.querySelector('a');
        const telefono = telefonoLink?.textContent?.trim() || celdas[3]?.textContent?.trim() || '—';
        elementos.inputTelefonoCentro.textContent = telefono;
        elementos.editTelefonoCentro.value = telefono !== '—' ? telefono : '';
        if (telefono !== '—') {
            elementos.inputTelefonoCentro.href = `tel:${telefono}`;
        }
        console.log(`📝 Teléfono: ${telefono}`);

        // Notas (celda 4)
        const notas = celdas[4]?.textContent?.trim() || '—';
        elementos.inputNotasCentro.textContent = notas;
        elementos.editNotasCentro.value = notas !== '—' ? notas : '';
        console.log(`📝 Notas: ${notas}`);

        // Email
        const dataEmail = fila.getAttribute('data-email') || '—';
        if (dataEmail !== '—') {
            elementos.inputEmailCentro.textContent = dataEmail;
            elementos.inputEmailCentro.href = `mailto:${dataEmail}`;
        } else {
            elementos.inputEmailCentro.textContent = '—';
        }
        elementos.editEmailCentro.value = dataEmail !== '—' ? dataEmail : '';
        console.log(`📝 Email: ${dataEmail}`);

        // Contacto
        const dataContacto = fila.getAttribute('data-contacto') || '—';
        elementos.inputContactoCentro.textContent = dataContacto;
        elementos.editContactoCentro.value = dataContacto !== '—' ? dataContacto : '';
        console.log(`📝 Contacto: ${dataContacto}`);

        console.log(`✅ [MODAL-CENTROS] Datos cargados exitosamente`);

        // Modo lectura
        mostrarModoLectura();

        // Abrir el modal
        if (modalElement) {
            try {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log(`✅ [MODAL-CENTROS] Modal abierto`);
            } catch (error) {
                console.error('❌ [MODAL-CENTROS] Error al abrir el modal con Bootstrap:', error);
                alert('Error: No se pudo abrir el modal');
            }
        } else {
            console.error('❌ [MODAL-CENTROS] Elemento del modal no encontrado');
            alert('Error: No se pudo abrir el modal');
        }

    } catch (error) {
        console.error(`❌ [MODAL-CENTROS] Error al cargar datos:`, error);
        alert(`Error al cargar los datos del centro: ${error.message}`);
    }
};

// Función para mostrar modo lectura
function mostrarModoLectura() {
    console.log('📖 [MODAL-CENTROS] Cambiar a modo lectura');
    document.querySelectorAll('.modo-lectura').forEach(el => el.classList.remove('d-none'));
    document.querySelectorAll('.modo-edicion').forEach(el => el.classList.add('d-none'));
}

// Función para mostrar modo edición
function mostrarModoEdicion() {
    console.log('✏️ [MODAL-CENTROS] Cambiar a modo edición');
    document.querySelectorAll('.modo-lectura').forEach(el => el.classList.add('d-none'));
    document.querySelectorAll('.modo-edicion').forEach(el => el.classList.remove('d-none'));
}

// Configurar event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 [MODAL-CENTROS] Configurando event listeners');

    // Botón agregar nuevo centro
    const btnAgregar = document.getElementById('btnAgregarNuevoCentro');
    if (btnAgregar) {
        btnAgregar.addEventListener('click', window.abrirCrearNuevoCentro);
        console.log('✅ [MODAL-CENTROS] Listener agregado a btnAgregarNuevoCentro');
    } else {
        console.warn('⚠️ [MODAL-CENTROS] Botón btnAgregarNuevoCentro no encontrado');
    }

    // Botón editar
    const btnEditar = document.getElementById('btnEditarModal');
    if (btnEditar) {
        btnEditar.addEventListener('click', mostrarModoEdicion);
    }

    // Botón cancelar edición
    const btnCancelar = document.getElementById('btnCancelarEdicion');
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function() {
            // Restaurar valores originales del modal
            mostrarModoLectura();
            // Restaurar título si fue modificado
            const titleElement = document.getElementById('modalDetallesCentroPropioLabel');
            if (titleElement && !centroActualEnEdicion) {
                titleElement.innerHTML = '<i class="bi bi-building me-2"></i>Detalles del Centro';
            }
            // Restaurar botones
            const btnBorrar = document.getElementById('btnBorrarModal');
            if (btnBorrar) btnBorrar.classList.remove('d-none');
            const btnGuardar = document.getElementById('btnGuardarEdicion');
            if (btnGuardar) {
                btnGuardar.innerHTML = '<i class="bi bi-save me-2"></i>Guardar';
            }
        });
    }

    // Botón guardar edición
    const btnGuardar = document.getElementById('btnGuardarEdicion');
    if (btnGuardar) {
        btnGuardar.addEventListener('click', window.guardarEdicionCentro);
    }

    // Botón borrar
    const btnBorrar = document.getElementById('btnBorrarModal');
    if (btnBorrar) {
        btnBorrar.addEventListener('click', borrarCentro);
    }

    console.log('✅ [MODAL-CENTROS] Event listeners configurados');
});

// Función para abrir el modal en modo creación de nuevo centro
window.abrirCrearNuevoCentro = function() {
    console.log('➕ [MODAL-CENTROS] Abriendo modal para crear nuevo centro');

    const modalElement = document.getElementById('modalDetallesCentroPropio');
    if (!modalElement) {
        console.error('❌ [MODAL-CENTROS] Modal no encontrado en el DOM');
        alert('Error: El modal no está disponible');
        return;
    }

    try {
        // Obtener todos los elementos del modal
        const elementIds = [
            'inputCentroId',
            'inputNombreCentro',
            'inputTipoCentro',
            'inputLocalidadCentro',
            'inputTelefonoCentro',
            'inputEmailCentro',
            'inputContactoCentro',
            'inputNotasCentro',
            'editNombreCentro',
            'editTipoCentro',
            'editLocalidadCentro',
            'editTelefonoCentro',
            'editEmailCentro',
            'editContactoCentro',
            'editNotasCentro'
        ];

        const elementos = {};
        for (const id of elementIds) {
            elementos[id] = getElementSafe(id);
            if (!elementos[id]) {
                throw new Error(`Elemento ${id} no encontrado en el DOM`);
            }
        }

        // Limpiar todos los campos
        elementos.inputCentroId.value = '';
        elementos.inputNombreCentro.textContent = '—';
        elementos.inputTipoCentro.textContent = '—';
        elementos.inputLocalidadCentro.textContent = '—';
        elementos.inputTelefonoCentro.textContent = '—';
        elementos.inputTelefonoCentro.href = '#';
        elementos.inputEmailCentro.textContent = '—';
        elementos.inputEmailCentro.href = 'mailto:#';
        elementos.inputContactoCentro.textContent = '—';
        elementos.inputNotasCentro.textContent = '—';

        // Limpiar campos de edición
        elementos.editNombreCentro.value = '';
        elementos.editTipoCentro.value = '';
        elementos.editLocalidadCentro.value = '';
        elementos.editTelefonoCentro.value = '';
        elementos.editEmailCentro.value = '';
        elementos.editContactoCentro.value = '';
        elementos.editNotasCentro.value = '';

        // Indicar que es un nuevo centro (sin ID)
        centroActualEnEdicion = null;

        // Cambiar el título del modal
        const titleElement = document.getElementById('modalDetallesCentroPropioLabel');
        if (titleElement) {
            titleElement.innerHTML = '<i class="bi bi-plus-circle me-2"></i>Crear Nuevo Centro';
        }

        console.log('✅ [MODAL-CENTROS] Modal preparado para crear nuevo centro');

        // Mostrar modo edición directamente para nuevo centro
        document.querySelectorAll('.modo-lectura').forEach(el => el.classList.add('d-none'));
        document.querySelectorAll('.modo-edicion').forEach(el => el.classList.remove('d-none'));

        // Ocultar botones que no aplican para creación
        const btnBorrar = document.getElementById('btnBorrarModal');
        if (btnBorrar) btnBorrar.classList.add('d-none');

        // Cambiar el texto del botón guardar
        const btnGuardar = document.getElementById('btnGuardarEdicion');
        if (btnGuardar) {
            btnGuardar.innerHTML = '<i class="bi bi-plus-circle me-2"></i>Crear Centro';
        }

        // Abrir el modal
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log('✅ [MODAL-CENTROS] Modal de creación abierto');

    } catch (error) {
        console.error('❌ [MODAL-CENTROS] Error al preparar modal de creación:', error);
        alert(`Error: ${error.message}`);
    }
};

// Función mejorada para guardar edición o crear nuevo centro
window.guardarEdicionCentro = function() {
    console.log(`💾 [MODAL-CENTROS] Guardando - Modo: ${centroActualEnEdicion ? 'Edición' : 'Creación'}`);

    const nombre = document.getElementById('editNombreCentro').value.trim();
    const tipo = document.getElementById('editTipoCentro').value; // Select no necesita trim
    const telefono = document.getElementById('editTelefonoCentro').value.trim();
    const email = document.getElementById('editEmailCentro').value.trim();
    const contacto = document.getElementById('editContactoCentro').value.trim();
    const notas = document.getElementById('editNotasCentro').value.trim();
    const localidadId = document.getElementById('editLocalidadCentro')?.value; // Para crear/editar

    if (!nombre || !tipo) {
        alert('⚠️ El nombre y tipo son obligatorios');
        return;
    }

    // Obtener datos del componente para puntoEcaId
    const sectionCentros = document.querySelector('section[th\\:fragment="centros"]') ||
                           document.querySelector('[data-punto-eca-id]');
    const puntoEcaId = sectionCentros?.getAttribute('data-punto-eca-id');

    if (!puntoEcaId) {
        console.error('❌ [MODAL-CENTROS] No se encontró el ID del Punto ECA');
        alert('Error: No se pudo obtener el ID del Punto ECA');
        return;
    }

    const datos = {
        nombreCntAcp: nombre,
        tipoCntAcp: tipo,
        celular: telefono,
        email: email,
        nombreContactoCntAcp: contacto,
        nota: notas,
        localidadId: localidadId // Para crear
    };

    if (centroActualEnEdicion) {
        // EDITAR centro existente
        console.log(`✏️ [MODAL-CENTROS] Editando centro: ${centroActualEnEdicion}`);
        console.log('📋 Valores:', datos);

        fetch(`/centro-acopio/${centroActualEnEdicion}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        })
        .then(response => {
            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
            return response.json().catch(() => ({ success: true }));
        })
        .then(data => {
            console.log('✅ [MODAL-CENTROS] Centro actualizado');
            alert('✅ Centro actualizado correctamente');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalDetallesCentroPropio'));
            if (modal) modal.hide();
            if (window.buscarCentros) window.buscarCentros(true);
        })
        .catch(error => {
            console.error('❌ Error al actualizar:', error);
            alert(`❌ Error: ${error.message}`);
        });
    } else {
        // CREAR nuevo centro
        console.log('➕ [MODAL-CENTROS] Creando nuevo centro');
        console.log('📋 Valores:', datos);

        // Obtener puntoEcaId desde el data attribute del componente section
        const section = document.querySelector('[data-punto-eca-id]');
        const puntoEcaId = section?.getAttribute('data-punto-eca-id');

        if (!puntoEcaId) {
            console.error('❌ [MODAL-CENTROS] No se encontró el ID del Punto ECA');
            alert('❌ Error: No se pudo obtener el ID del Punto ECA');
            return;
        }

        console.log('📍 Punto ECA ID: ' + puntoEcaId);

        fetch(`/punto-eca/${puntoEcaId}/centro-acopio`, {
            method: 'POST',
            headers: {

                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        })
        .then(response => {
            console.log(`📡 Response status: ${response.status}`);
            if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
            return response.json().catch(() => ({ success: true }));
        })
        .then(data => {
            console.log('✅ [MODAL-CENTROS] Centro creado exitosamente');
            console.log('📦 Respuesta del servidor:', data);

            // Verificar si hay errores de validación
            if (data.isValidationError && data.validationErrors) {
                console.warn('⚠️ Errores de validación:', data.validationErrors);

                // Construir mensaje de error
                let mensajeError = '❌ Errores de validación:\n\n';
                data.validationErrors.forEach(error => {
                    mensajeError += `• ${error.field}: ${error.message}\n`;
                });

                alert(mensajeError);
                return;
            }

            alert('✅ Centro creado correctamente');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalDetallesCentroPropio'));
            if (modal) modal.hide();
            if (window.buscarCentros) window.buscarCentros(true);
            // Recargar la página para reflejar cambios
            setTimeout(() => location.reload(), 500);
        })
        .catch(error => {
            console.error('❌ [MODAL-CENTROS] Error al crear:', error);
            alert(`❌ Error al crear el centro: ${error.message}`);
        });
    }
};

console.log('✅ [MODAL-CENTROS] Sistema inicializado y listo');

function borrarCentro() {
    if (!centroActualEnEdicion) {
        alert('⚠️ No hay centro seleccionado para borrar');
        return;
    }

    // Solicitar confirmación
    const nombreCentro = document.getElementById('inputNombreCentro').textContent;
    const confirmacion = confirm(`¿Estás seguro de que deseas borrar el centro "${nombreCentro}"?\n\nEsta acción no se puede deshacer.`);

    if (!confirmacion) {
        console.log('⚠️ [MODAL-CENTROS] Borrado cancelado por el usuario');
        return;
    }

    console.log(`🗑️ [MODAL-CENTROS] Borrando centro: ${centroActualEnEdicion}`);

    fetch(`/centro-acopio/${centroActualEnEdicion}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log(`📡 [MODAL-CENTROS] Response status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        return response.json().catch(() => ({ success: true }));
    })
    .then(data => {
        console.log('✅ [MODAL-CENTROS] Centro eliminado exitosamente');
        console.log('📦 Respuesta del servidor:', data);
        alert('✅ Centro eliminado correctamente');

        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalDetallesCentroPropio'));
        if (modal) modal.hide();

        // Recargar tabla
        if (window.buscarCentros) window.buscarCentros(true);
    })
    .catch(error => {
        console.error('❌ [MODAL-CENTROS] Error al borrar:', error);
        alert(`❌ Error al borrar: ${error.message}`);
    });
}
