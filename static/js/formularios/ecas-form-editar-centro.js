import { showAlert, showValidationAlert } from './formulario-alertas.js';
import { submitFormJson } from './formulario-submit-json.js';

const EcAsFormEditarCentro = (() => {
    const FORM_ID = 'formEditarCentro';
    const FEEDBACK_ID = 'editarCentroFeedback';

    function setFeedback(kind, message) {
        const modalBody = document.querySelector(`#${FORM_ID} .modal-body`);
        if (!modalBody) {
            return;
        }
        let feedback = document.getElementById(FEEDBACK_ID);
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.id = FEEDBACK_ID;
            modalBody.prepend(feedback);
        }
        feedback.className = `alert alert-${kind}`;
        feedback.textContent = message;
    }

    function clearFeedback() {
        const feedback = document.getElementById(FEEDBACK_ID);
        if (feedback) {
            feedback.remove();
        }
    }

    function refreshPropios(deps) {
        const root = globalThis;
        const centrosPropios = root.CENTROS_PROPIOS || [];
        deps.renderTablaCentros(centrosPropios, 'tablaCentrosPropiosBody');
        deps.updateBadge(centrosPropios.length, 'badgePropiosCount');
        const id = root.__ultimoCentroEditadoId;
        if (id != null) {
            deps.markEditedCentroRow(id);
        }
    }

    async function submitCentroEdit(form, deps) {
        const root = globalThis;
        const { response, payload } = await submitFormJson(form);

        if (response.ok && payload?.status === 'ok' && payload.centro) {
            const centrosPropios = root.CENTROS_PROPIOS || [];
            const idx = centrosPropios.findIndex((item) => String(item.id) === String(payload.centro.id));
            if (idx !== -1) {
                centrosPropios[idx] = payload.centro;
            }
            refreshPropios(deps);
            const message = payload.mensaje || 'Edición exitosa';
            setFeedback('success', message);
            await showAlert('success', 'Centro guardado', message);
            root.__ultimoCentroEditadoId = payload.centro.id;
            globalThis.setTimeout(() => {
                root.location.reload();
            }, 900);
            return;
        }

        const errorMessage = payload?.mensaje || payload?.error || 'Error al guardar los cambios';
        setFeedback('danger', errorMessage);
        await showAlert('error', 'No se pudo guardar', errorMessage);
    }

    async function handleSubmit(event, deps) {
        const form = event.currentTarget;
        event.preventDefault();
        event.stopPropagation();

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            await showValidationAlert('Revisa los campos del centro y corrige los datos marcados.');
            return;
        }

        form.classList.add('was-validated');
        clearFeedback();

        const submitBtn = form.querySelector('[type=submit]');
        if (submitBtn) {
            submitBtn.disabled = true;
        }

        try {
            await submitCentroEdit(form, deps);
        } catch (error) {
            if (globalThis.console?.error) {
                globalThis.console.error('[EDIT-CENTRO] Error inesperado en la comunicacion', error);
            }
            await showAlert('error', 'Error', 'Error inesperado en la comunicación con el servidor.');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        }
    }

    function attachInvalidCapture(form) {
        const elements = form.querySelectorAll('input, select, textarea');
        elements.forEach((element) => {
            element.addEventListener('invalid', (event) => {
                event.preventDefault();
            }, true);
        });
    }

    function init(deps = {}) {
        const form = document.getElementById(FORM_ID);
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        attachInvalidCapture(form);
        form.addEventListener('submit', (event) => {
            handleSubmit(event, deps);
        });
        form.addEventListener('reset', () => {
            form.classList.remove('was-validated');
            clearFeedback();
        });
    }

    return { init };
})();

export const { init } = EcAsFormEditarCentro;
