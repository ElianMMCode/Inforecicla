import { createInventarioFormController } from './ecas-inventario-form-base.js';

const EcAsFormEditarInventario = (() => {
    const MODAL_ID = 'editarModal';
    const SUBMIT_ENDPOINT_PREFIX = '/punto-eca/materiales/inventario/actualizar/';

    const FIELD_MESSAGES = {
        editarStockActual: 'Ingresa el stock actual (mayor o igual a 0).',
        editarCapacidadMaxima: 'Ingresa la capacidad máxima (mayor o igual a 0).',
        editarUnidadMedida: 'Selecciona una unidad de medida.',
        editarPrecioCompra: 'Ingresa el precio de compra (mayor o igual a 0).',
        editarPrecioVenta: 'Ingresa el precio de venta (mayor o igual a 0).',
        editarUmbralAlerta: 'Ingresa el umbral de alerta (entre 0 y 100).',
        editarUmbralCritico: 'Ingresa el umbral crítico (entre 0 y 100).',
    };

    function buildPayload(form) {
        return {
            stockActual: Number.parseFloat(form.querySelector('#editarStockActual')?.value) || 0,
            capacidadMaxima: Number.parseFloat(form.querySelector('#editarCapacidadMaxima')?.value) || 0,
            unidadMedida: form.querySelector('#editarUnidadMedida')?.value || '',
            precioCompra: Number.parseFloat(form.querySelector('#editarPrecioCompra')?.value) || 0,
            precioVenta: Number.parseFloat(form.querySelector('#editarPrecioVenta')?.value) || 0,
            umbralAlerta: Number.parseInt(form.querySelector('#editarUmbralAlerta')?.value, 10) || 0,
            umbralCritico: Number.parseInt(form.querySelector('#editarUmbralCritico')?.value, 10) || 0,
        };
    }

    function getInventarioId(form) {
        const idInput = form.querySelector('#editarMaterialId');
        return idInput instanceof HTMLInputElement ? idInput.value : '';
    }

    function getSectionContext() {
        const section = document.querySelector('section[data-gestor]') || document.querySelector('section[data-punto-eca-id]');
        return {
            gestor: section?.dataset.gestor || '',
            usuarioId: section?.dataset.usuarioId || '',
        };
    }

    function hideEditModal() {
        const modalEl = document.getElementById(MODAL_ID);
        const modalInstance = modalEl ? globalThis.bootstrap?.Modal?.getInstance(modalEl) : null;
        if (modalInstance) {
            modalInstance.hide();
        }
    }

    async function submitEdicion(form, payload, { setSubmittingState, showSwal, getCsrfToken }) {
        const inventarioId = getInventarioId(form);
        const { gestor, usuarioId } = getSectionContext();

        if (!inventarioId) {
            await showSwal('error', 'Error', 'No se encontró el ID del inventario.');
            return;
        }

        if (!gestor || !usuarioId) {
            if (globalThis.console?.error) {
                globalThis.console.error('[EDITAR-INVENTARIO] Datos de usuario no encontrados.');
            }
            await showSwal('error', 'Error', 'No se encontraron los datos de usuario. Por favor recarga la página.');
            return;
        }

        setSubmittingState(form, true);
        const url = `${SUBMIT_ENDPOINT_PREFIX}${inventarioId}`;

        try {
            const response = await globalThis.fetch(url, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            const data = await response.json().catch(() => null);

            hideEditModal();

            if (response.ok && !data?.error) {
                await showSwal('success', '¡Operación Exitosa!', 'Los cambios se han guardado correctamente en la base de datos.');
                return;
            }

            const errorMessage = data?.mensaje || data?.message || data?.error || 'Hubo un error al guardar los cambios';
            await showSwal('error', 'Error al guardar', errorMessage);
        } catch (error) {
            hideEditModal();
            if (globalThis.console?.error) {
                globalThis.console.error('[EDITAR-INVENTARIO] Error en fetch:', error);
            }
            await showSwal('error', 'Error', 'No se pudo conectar con el servidor.');
        } finally {
            setSubmittingState(form, false);
        }
    }

    return createInventarioFormController({
        formId: 'formularioEditarInventario',
        submitButtonId: 'btnGuardarCambios',
        stockInputId: 'editarStockActual',
        capacityInputId: 'editarCapacidadMaxima',
        crossFieldMessage: 'El stock actual no puede superar la capacidad máxima.',
        fieldMessages: FIELD_MESSAGES,
        buildPayload,
        submit: submitEdicion,
    });
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', EcAsFormEditarInventario.init, { once: true });
} else {
    EcAsFormEditarInventario.init();
}
