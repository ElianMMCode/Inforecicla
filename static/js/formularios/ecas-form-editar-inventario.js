const EcAsFormEditarInventario = (() => {
    const FORM_ID = 'formularioEditarInventario';
    const MODAL_ID = 'editarModal';
    const SUBMIT_ENDPOINT_PREFIX = '/punto-eca/materiales/inventario/actualizar/';
    const SWAL_CONFIRM_COLOR = '#198754';
    const CROSS_FIELD_MESSAGE = 'El stock actual no puede superar la capacidad máxima.';

    const FIELD_MESSAGES = {
        editarStockActual: 'Ingresa el stock actual (mayor o igual a 0).',
        editarCapacidadMaxima: 'Ingresa la capacidad máxima (mayor o igual a 0).',
        editarUnidadMedida: 'Selecciona una unidad de medida.',
        editarPrecioCompra: 'Ingresa el precio de compra (mayor o igual a 0).',
        editarPrecioVenta: 'Ingresa el precio de venta (mayor o igual a 0).',
        editarUmbralAlerta: 'Ingresa el umbral de alerta (entre 0 y 100).',
        editarUmbralCritico: 'Ingresa el umbral crítico (entre 0 y 100).',
    };

    const FIELD_IDS = Object.keys(FIELD_MESSAGES);

    function showSwal(icon, title, text) {
        if (globalThis.Swal?.fire) {
            return globalThis.Swal.fire({
                icon,
                title,
                text,
                confirmButtonColor: SWAL_CONFIRM_COLOR,
                confirmButtonText: 'Entendido',
            });
        }
        if (globalThis.console?.warn) {
            globalThis.console.warn('SweetAlert2 no disponible:', title, text);
        }
        return Promise.resolve({ isConfirmed: true });
    }

    function getCsrfToken() {
        const cookieToken = globalThis.getCSRFToken?.();
        return typeof cookieToken === 'string' ? cookieToken : '';
    }

    function hideEditModal() {
        const modalEl = document.getElementById(MODAL_ID);
        const modalInstance = modalEl ? globalThis.bootstrap?.Modal?.getInstance(modalEl) : null;
        if (modalInstance) {
            modalInstance.hide();
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

    function removeCrossFieldFeedback(input) {
        const wrapper = input.closest('.input-group') || input.parentElement;
        const existing = wrapper?.querySelector('.invalid-feedback.cross-field');
        if (existing) {
            existing.remove();
        }
    }

    function setCrossFieldError(input, message) {
        if (!(input instanceof HTMLInputElement)) {
            return;
        }
        if (message) {
            input.setCustomValidity(message);
            const wrapper = input.closest('.input-group') || input.parentElement;
            if (!wrapper) {
                return;
            }
            let feedback = wrapper.querySelector('.invalid-feedback.cross-field');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback cross-field';
                wrapper.appendChild(feedback);
            }
            feedback.textContent = message;
            return;
        }
        input.setCustomValidity('');
        removeCrossFieldFeedback(input);
    }

    function validateCrossField(form) {
        const stockInput = form.querySelector('#editarStockActual');
        const capacityInput = form.querySelector('#editarCapacidadMaxima');
        if (!(stockInput instanceof HTMLInputElement) || !(capacityInput instanceof HTMLInputElement)) {
            return true;
        }
        const stock = Number.parseFloat(stockInput.value);
        const capacity = Number.parseFloat(capacityInput.value);
        if (Number.isFinite(stock) && Number.isFinite(capacity) && stock > capacity) {
            setCrossFieldError(stockInput, CROSS_FIELD_MESSAGE);
            return false;
        }
        setCrossFieldError(stockInput, '');
        return true;
    }

    function attachCrossFieldLiveValidation(form) {
        const stockInput = form.querySelector('#editarStockActual');
        const capacityInput = form.querySelector('#editarCapacidadMaxima');
        [stockInput, capacityInput].forEach((input) => {
            if (input instanceof HTMLInputElement) {
                input.addEventListener('input', () => {
                    if (input.validity.customError) {
                        validateCrossField(form);
                    }
                });
            }
        });
    }

    function ensureFieldMessages(form) {
        FIELD_IDS.forEach((fieldId) => {
            const input = form.querySelector(`#${fieldId}`);
            if (!input) {
                return;
            }
            const inputGroup = input.closest('.input-group');
            const wrapper = inputGroup || input.parentElement;
            if (!wrapper) {
                return;
            }
            if (!wrapper.querySelector(`#${fieldId} ~ .invalid-feedback, .invalid-feedback[data-for="${fieldId}"]`)) {
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.dataset.for = fieldId;
                feedback.textContent = FIELD_MESSAGES[fieldId];
                if (inputGroup) {
                    inputGroup.appendChild(feedback);
                } else {
                    input.after(feedback);
                }
            }
        });
    }

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

    function setSubmittingState(form, isSubmitting) {
        const submitBtn = form.querySelector('#btnGuardarCambios');
        if (!(submitBtn instanceof HTMLButtonElement)) {
            return null;
        }
        if (isSubmitting) {
            if (!submitBtn.dataset.originalHtml) {
                submitBtn.dataset.originalHtml = submitBtn.innerHTML;
            }
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Guardando...';
        } else {
            submitBtn.disabled = false;
            if (submitBtn.dataset.originalHtml) {
                submitBtn.innerHTML = submitBtn.dataset.originalHtml;
                delete submitBtn.dataset.originalHtml;
            }
        }
        return submitBtn;
    }

    function notifyResult(esExito, titulo, mensaje) {
        return showSwal(esExito ? 'success' : 'error', titulo, mensaje);
    }

    async function submitEdicion(form) {
        const csrf = getCsrfToken();
        const inventarioId = getInventarioId(form);
        const { gestor, usuarioId } = getSectionContext();

        if (!inventarioId) {
            notifyResult(false, 'Error', 'No se encontró el ID del inventario.');
            return;
        }

        if (!gestor || !usuarioId) {
            if (globalThis.console?.error) {
                globalThis.console.error('[EDITAR-INVENTARIO] Datos de usuario no encontrados.');
            }
            notifyResult(false, 'Error', 'No se encontraron los datos de usuario. Por favor recarga la página.');
            return;
        }

        setSubmittingState(form, true);
        const payload = buildPayload(form);
        const url = `${SUBMIT_ENDPOINT_PREFIX}${inventarioId}`;

        try {
            const response = await globalThis.fetch(url, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            const data = await response.json().catch(() => null);

            hideEditModal();

            if (response.ok && !data?.error) {
                notifyResult(true, '¡Operación Exitosa!', 'Los cambios se han guardado correctamente en la base de datos.');
                return;
            }

            const errorMessage = data?.mensaje || data?.message || data?.error || 'Hubo un error al guardar los cambios';
            notifyResult(false, 'Error al guardar', errorMessage);
        } catch (error) {
            hideEditModal();
            if (globalThis.console?.error) {
                globalThis.console.error('[EDITAR-INVENTARIO] Error en fetch:', error);
            }
            notifyResult(false, 'Error', 'No se pudo conectar con el servidor.');
        } finally {
            setSubmittingState(form, false);
        }
    }

    async function handleSubmit(event) {
        const form = event.currentTarget;
        event.preventDefault();
        event.stopPropagation();

        validateCrossField(form);

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            await showSwal(
                'warning',
                'Campos obligatorios pendientes',
                'Por favor completa todos los campos requeridos del inventario.'
            );
            return;
        }

        form.classList.add('was-validated');
        await submitEdicion(form);
    }

    function attachResetCleanup(form) {
        form.addEventListener('reset', () => {
            form.classList.remove('was-validated');
            const stockInput = form.querySelector('#editarStockActual');
            if (stockInput instanceof HTMLInputElement) {
                setCrossFieldError(stockInput, '');
            }
        });
    }

    function init() {
        const form = document.getElementById(FORM_ID);
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        ensureFieldMessages(form);
        attachInvalidCapture(form);
        attachCrossFieldLiveValidation(form);
        attachResetCleanup(form);
        form.addEventListener('submit', (event) => {
            handleSubmit(event);
        });
    }

    return { init };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        EcAsFormEditarInventario.init();
    }, { once: true });
} else {
    EcAsFormEditarInventario.init();
}
