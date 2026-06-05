import { showValidationAlert } from './formulario-alertas.js';

const EcAsFormFiltrosCentros = (() => {
    const FORM_CONFIGS = [
        {
            formId: 'filtrosFormCentrosGlobales',
            scope: 'Global',
            dataKey: 'CENTROS_GLOBALES',
            tableBodyId: 'tablaCentrosGlobalesBody',
            badgeId: 'badgeGlobalesCount',
        },
        {
            formId: 'filtrosFormCentrosPropios',
            scope: 'Propio',
            dataKey: 'CENTROS_PROPIOS',
            tableBodyId: 'tablaCentrosPropiosBody',
            badgeId: 'badgePropiosCount',
        },
    ];

    function readFiltros(scope) {
        const suffix = scope === 'Global' ? 'Global' : 'Propio';
        return {
            nombre: document.getElementById(`filtroNombre${suffix}`)?.value ?? '',
            tipo: document.getElementById(`filtroTipo${suffix}`)?.value ?? '',
            localidad: document.getElementById(`filtroLocalidad${suffix}`)?.value ?? '',
            contacto: document.getElementById(`filtroContacto${suffix}`)?.value ?? '',
            email: document.getElementById(`filtroEmail${suffix}`)?.value ?? '',
            telefono: document.getElementById(`filtroTelefono${suffix}`)?.value ?? '',
        };
    }

    function attachInvalidCapture(form) {
        const elements = form.querySelectorAll('input, select, textarea');
        elements.forEach((element) => {
            element.addEventListener('invalid', (event) => {
                event.preventDefault();
            }, true);
        });
    }

    function runFilter(config, deps) {
        const root = globalThis;
        const data = root[config.dataKey] || [];
        const filtros = readFiltros(config.scope);
        const filtrados = deps.filterCentros(data, filtros);
        deps.renderTablaCentros(filtrados, config.tableBodyId);
        deps.updateBadge(filtrados.length, config.badgeId);
    }

    function attachForm(config, deps) {
        const form = document.getElementById(config.formId);
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        attachInvalidCapture(form);

        const filterBtn = document.getElementById(`btnFiltrar${config.scope === 'Global' ? 'Globales' : 'Propios'}`);
        const clearBtn = document.getElementById(`btnLimpiar${config.scope === 'Global' ? 'Globales' : 'Propios'}`);

        if (filterBtn) {
            filterBtn.addEventListener('click', async (event) => {
                event.preventDefault();
                if (!form.checkValidity()) {
                    form.classList.add('was-validated');
                    await showValidationAlert('Revisa los filtros y corrige los datos marcados antes de buscar.');
                    return;
                }
                form.classList.remove('was-validated');
                runFilter(config, deps);
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', (event) => {
                event.preventDefault();
                deps.limpiarCampos(form);
                form.classList.remove('was-validated');
                runFilter(config, deps);
            });
        }

        form.addEventListener('reset', () => {
            form.classList.remove('was-validated');
        });
    }

    function init(deps = {}) {
        if (!deps.filterCentros || !deps.renderTablaCentros || !deps.updateBadge || !deps.limpiarCampos) {
            if (globalThis.console?.warn) {
                globalThis.console.warn('[ecas-form-filtros-centros] Dependencias incompletas, módulo inactivo.', deps);
            }
            return;
        }
        FORM_CONFIGS.forEach((config) => {
            attachForm(config, deps);
        });
    }

    return { init };
})();

export const { init } = EcAsFormFiltrosCentros;
