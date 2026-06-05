import { createInventarioFormController } from './ecas-inventario-form-base.js';

const EcAsFormAgregarInventario = (() => {
    const MODAL_ID = 'agregarInventarioModal';
    const SUBMIT_ENDPOINT = '/punto-eca/materiales/inventario/agregar/';
    const SUCCESS_RELOAD_DELAY_MS = 1200;

    const FIELD_MESSAGES = {
        stockInicial: 'Ingresa el stock inicial (mayor o igual a 0).',
        capacidadMaxima: 'Ingresa la capacidad máxima (mayor o igual a 0).',
        unidadMedida: 'Selecciona una unidad de medida.',
        precioCompra: 'Ingresa el precio de compra (mayor o igual a 0).',
        precioVenta: 'Ingresa el precio de venta (mayor o igual a 0).',
        umbralAlerta: 'Ingresa el umbral de alerta (entre 0 y 100).',
        umbralCritico: 'Ingresa el umbral crítico (entre 0 y 100).',
    };

    function buildPayload(form) {
        const puntoInput = form.querySelector('#agregarPuntoId');
        const materialInput = form.querySelector('#agregarMaterialId');
        return {
            materialId: materialInput instanceof HTMLInputElement ? materialInput.value : '',
            puntoEcaId: puntoInput instanceof HTMLInputElement ? puntoInput.value : '',
            stockActual: Number.parseFloat(form.querySelector('#stockInicial')?.value) || 0,
            capacidadMaxima: Number.parseFloat(form.querySelector('#capacidadMaxima')?.value) || 0,
            unidadMedida: form.querySelector('#unidadMedida')?.value || '',
            precioCompra: Number.parseFloat(form.querySelector('#precioCompra')?.value) || 0,
            precioVenta: Number.parseFloat(form.querySelector('#precioVenta')?.value) || 0,
            umbralAlerta: Number.parseInt(form.querySelector('#umbralAlerta')?.value, 10) || 0,
            umbralCritico: Number.parseInt(form.querySelector('#umbralCritico')?.value, 10) || 0,
        };
    }

    async function submitInventario(form, payload, { setSubmittingState, showSwal, getCsrfToken }) {
        setSubmittingState(form, true);
        try {
            const response = await globalThis.fetch(SUBMIT_ENDPOINT, {
                method: 'POST',
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

            if (response.ok && !data?.error) {
                await showSwal('success', '¡Operación exitosa!', 'El material fue agregado al inventario.');
                form.reset();
                const modalEl = document.getElementById(MODAL_ID);
                const modalInstance = modalEl ? globalThis.bootstrap?.Modal?.getInstance(modalEl) : null;
                if (modalInstance) {
                    modalInstance.hide();
                }
                globalThis.setTimeout(() => globalThis.location.reload(), SUCCESS_RELOAD_DELAY_MS);
                return;
            }

            const errorMessage = data?.mensaje || data?.message || data?.error || 'No fue posible guardar el inventario.';
            await showSwal('error', 'Error al guardar', errorMessage);
        } catch (error) {
            if (globalThis.console?.error) {
                globalThis.console.error('[AGREGAR-INVENTARIO] Error en fetch:', error);
            }
            await showSwal('error', 'Error', 'No se pudo conectar con el servidor.');
        } finally {
            setSubmittingState(form, false);
        }
    }

    return createInventarioFormController({
        formId: 'formAgregarInventario',
        submitButtonId: 'btnGuardarInventario',
        stockInputId: 'stockInicial',
        capacityInputId: 'capacidadMaxima',
        crossFieldMessage: 'El stock inicial no puede superar la capacidad máxima.',
        fieldMessages: FIELD_MESSAGES,
        buildPayload,
        submit: submitInventario,
    });
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', EcAsFormAgregarInventario.init, { once: true });
} else {
    EcAsFormAgregarInventario.init();
}
