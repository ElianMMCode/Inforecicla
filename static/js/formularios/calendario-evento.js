import { showResultAlert } from './formulario-alertas.js';

const CalendarioEventoForm = (() => {
    const FORM_ID = 'formCrearEvento';
    const API_URL = '/punto-eca/calendario/evento/nuevo/';

    const FIELD_IDS = {
        material: 'selectMaterial',
        centroAcopio: 'selectCentroAcopio',
        titulo: 'inputTitulo',
        descripcion: 'inputDescripcion',
        fechaInicio: 'inputFechaInicio',
        horaInicio: 'inputHoraInicio',
        horaFin: 'inputHoraFin',
        color: 'inputColor',
        tipoRepeticion: 'selectTipoRepeticion',
        fechaFinRepeticion: 'inputFechaFinRepeticion',
        observaciones: 'inputObservaciones',
        puntoEcaId: 'inputPuntoEcaId',
        usuarioId: 'inputUsuarioId',
    };

    function getForm() {
        const form = document.getElementById(FORM_ID);
        return form instanceof HTMLFormElement ? form : null;
    }

    function getControl(id) {
        const control = document.getElementById(id);
        return control instanceof HTMLInputElement || control instanceof HTMLSelectElement || control instanceof HTMLTextAreaElement
            ? control
            : null;
    }

    function getCookie(name) {
        if (!document.cookie) {
            return '';
        }

        for (const cookie of document.cookie.split(';')) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(`${name}=`)) {
                return decodeURIComponent(trimmed.slice(name.length + 1));
            }
        }

        return '';
    }

    function getValue(id) {
        return getControl(id)?.value || '';
    }

    async function showSwalNotification(icon, title, text) {
        if (globalThis.Swal?.fire) {
            return globalThis.Swal.fire({
                icon,
                title,
                text,
                confirmButtonColor: '#198754',
            });
        }

        if (globalThis.console?.warn) {
            globalThis.console.warn('SweetAlert2 no está disponible:', title, text);
        }

        return Promise.resolve();
    }

    function bindNativeValidationSuppression(form) {
        form.addEventListener('invalid', (event) => {
            event.preventDefault();
        }, true);
    }

    function syncTimeValidity() {
        const horaInicio = getControl(FIELD_IDS.horaInicio);
        const horaFin = getControl(FIELD_IDS.horaFin);

        if (!(horaInicio instanceof HTMLInputElement) || !(horaFin instanceof HTMLInputElement)) {
            return;
        }

        const inicio = horaInicio.value.trim();
        const fin = horaFin.value.trim();

        if (inicio && fin && fin <= inicio) {
            horaFin.setCustomValidity('La hora de fin debe ser posterior a la hora de inicio.');
            return;
        }

        horaFin.setCustomValidity('');
    }

    function bindFieldValidationSync(form) {
        const horaInicio = getControl(FIELD_IDS.horaInicio);
        const horaFin = getControl(FIELD_IDS.horaFin);

        const sync = () => {
            syncTimeValidity();

            if (form.classList.contains('was-validated')) {
                form.checkValidity();
            }
        };

        [horaInicio, horaFin].forEach((control) => {
            control?.addEventListener('input', sync);
            control?.addEventListener('change', sync);
        });

        syncTimeValidity();
    }

    function buildPayload() {
        return {
            materialId: getValue(FIELD_IDS.material),
            centroAcopioId: getValue(FIELD_IDS.centroAcopio),
            puntoEcaId: getValue(FIELD_IDS.puntoEcaId),
            usuarioId: getValue(FIELD_IDS.usuarioId),
            titulo: getValue(FIELD_IDS.titulo),
            descripcion: getValue(FIELD_IDS.descripcion),
            fechaInicio: getValue(FIELD_IDS.fechaInicio),
            horaInicio: getValue(FIELD_IDS.horaInicio),
            horaFin: getValue(FIELD_IDS.horaFin),
            color: getValue(FIELD_IDS.color),
            tipoRepeticion: getValue(FIELD_IDS.tipoRepeticion) || 'NINGUNA',
            fechaFinRepeticion: getValue(FIELD_IDS.fechaFinRepeticion),
            observaciones: getValue(FIELD_IDS.observaciones),
        };
    }

    async function submitEvent(form) {
        form.classList.add('was-validated');

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(buildPayload()),
            });

            const result = await response.json().catch(() => null);

            if (!response.ok || !result?.success) {
                await showResultAlert('error', 'Error', result?.error || 'No fue posible crear el evento.');
                return;
            }

            form.reset();
            form.classList.remove('was-validated');
            syncTimeValidity();
            await showResultAlert('success', 'Evento creado', result.message || 'Evento creado correctamente.');
            globalThis.location.reload();
        } catch (error) {
            if (globalThis.console?.error) {
                globalThis.console.error('Error al crear el evento:', error);
            }

            await showResultAlert('error', 'Error', 'No se pudo conectar con el servidor.');
        }
    }

    function init() {
        const form = getForm();
        if (!form) {
            return;
        }

        bindNativeValidationSuppression(form);
        bindFieldValidationSync(form);

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            syncTimeValidity();

            if (!form.checkValidity()) {
                event.stopPropagation();
                form.classList.add('was-validated');

                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid && typeof firstInvalid.focus === 'function') {
                    firstInvalid.focus();
                }

                await showSwalNotification(
                    'warning',
                    'Campos obligatorios pendientes',
                    'Completa los campos obligatorios antes de continuar.',
                );
                return;
            }

            submitEvent(form);
        });
    }

    return { init };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        CalendarioEventoForm.init();
    }, { once: true });
} else {
    CalendarioEventoForm.init();
}