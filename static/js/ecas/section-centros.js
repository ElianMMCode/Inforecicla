(function () {
    const root = globalThis;

    function el(id) {
        return document.getElementById(id);
    }

    function mostrarMensajeCentro(tipo, mensaje) {
        const cont = el('mensajesCentroContainer');
        if (!cont) {
            console.error('[mostrarMensajeCentro] No se encontro el contenedor de mensajes');
            alert(mensaje);
            return;
        }
        cont.innerHTML = `<div class="alert alert-${tipo} alert-dismissible fade show" role="alert">${mensaje}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button></div>`;
        setTimeout(() => {
            if (cont.firstChild) {
                cont.firstChild.classList.remove('show');
                setTimeout(() => {
                    cont.innerHTML = '';
                }, 300);
            }
        }, 2500);
    }

    function ensureMensajesContainer() {
        if (el('mensajesCentroContainer')) {
            return;
        }
        const fallbackDiv = document.createElement('div');
        fallbackDiv.id = 'mensajesCentroContainer';
        const refTable = document.querySelector('table');
        if (refTable?.parentNode) {
            refTable.parentNode.insertBefore(fallbackDiv, refTable);
            return;
        }
        document.body.insertBefore(fallbackDiv, document.body.firstChild);
    }

    function readJsonArrayFromScript(scriptId, fallback = []) {
        const scriptElement = el(scriptId);
        if (!scriptElement) {
            return fallback;
        }
        try {
            const parsed = JSON.parse(scriptElement.textContent || '[]');
            return Array.isArray(parsed) ? parsed : fallback;
        } catch (error) {
            console.warn('[section-centros] No se pudo leer ' + scriptId, error);
            return fallback;
        }
    }

    function loadCentroState() {
        try {
            const cgRaw = el('centrosGlobalesData')?.textContent || '[]';
            const cpRaw = el('centrosPropiosData')?.textContent || '[]';
            root.CENTROS_GLOBALES = cgRaw.trim() ? JSON.parse(cgRaw) : [];
            root.CENTROS_PROPIOS = cpRaw.trim() ? JSON.parse(cpRaw) : [];
        } catch (error) {
            console.error('[CRITICAL] Error al parsear centros', error);
            root.CENTROS_GLOBALES = [];
            root.CENTROS_PROPIOS = [];
        }
    }

    function reinitializeSelect2(select, placeholder) {
        if (!root.jQuery?.fn?.select2) {
            return false;
        }
        const $select = root.jQuery(select);
        if ($select.hasClass('select2-hidden-accessible')) {
            $select.select2('destroy');
        }
        $select.select2({
            theme: 'bootstrap4',
            width: '100%',
            allowClear: true,
            placeholder: placeholder,
        });
        return true;
    }

    function populateCatalogSelect(selectId, data, valueKey, labelKey, placeholder) {
        const select = el(selectId);
        if (!select) {
            return;
        }
        const currentValue = select.value;
        select.innerHTML = '';
        const optionIni = document.createElement('option');
        optionIni.value = '';
        optionIni.textContent = '-- Seleccione --';
        select.appendChild(optionIni);

        let hasCurrentValue = false;
        (Array.isArray(data) ? data : []).forEach((opt) => {
            const value = String(typeof opt === 'object' ? opt[valueKey] : opt[0]);
            const label = typeof opt === 'object' ? opt[labelKey] : opt[1];
            if (value == currentValue) {
                hasCurrentValue = true;
            }
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            select.appendChild(option);
        });

        if (currentValue && !hasCurrentValue) {
            const optLegacy = document.createElement('option');
            optLegacy.value = currentValue;
            optLegacy.textContent = 'Valor antiguo: ' + currentValue;
            select.appendChild(optLegacy);
        }

        select.value = currentValue;
        reinitializeSelect2(select, placeholder || '-- Seleccione --');
    }

    function initSelect2Filters(data, scope) {
        const typePlaceholder = 'Selecciona tipo...';
        const localityPlaceholder = 'Selecciona localidad...';
        const typeSelect = el('filtroTipo' + scope);
        const localitySelect = el('filtroLocalidad' + scope);
        if (typeSelect) {
            const types = new Set();
            data.forEach((centro) => {
                if (centro.get_tipo_centro_display?.trim()) {
                    types.add(centro.get_tipo_centro_display.trim());
                } else if (centro.tipo?.trim()) {
                    types.add(centro.tipo.trim());
                }
            });
            const previousType = typeSelect.value;
            const firstOption = typeSelect.querySelector('option');
            typeSelect.innerHTML = '';
            const clonedTypeOption = firstOption?.cloneNode(true);
            if (clonedTypeOption) {
                typeSelect.appendChild(clonedTypeOption);
            }
            Array.from(types).sort((a, b) => a.localeCompare(b, 'es')).forEach((value) => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                typeSelect.appendChild(option);
            });
            if (Array.from(typeSelect.options).some((opt) => opt.value === previousType)) {
                typeSelect.value = previousType;
            }
            reinitializeSelect2(typeSelect, typePlaceholder);
        }
        if (localitySelect) {
            const localities = new Set();
            data.forEach((centro) => {
                const localidad = typeof centro.localidad === 'object' && centro.localidad !== null ? centro.localidad.nombre : centro.localidad;
                if (localidad && typeof localidad === 'string' && localidad.trim()) {
                    localities.add(localidad.trim());
                }
            });
            const previousLocality = localitySelect.value;
            const firstOption = localitySelect.querySelector('option');
            localitySelect.innerHTML = '';
            const clonedLocalityOption = firstOption?.cloneNode(true);
            if (clonedLocalityOption) {
                localitySelect.appendChild(clonedLocalityOption);
            }
            Array.from(localities).sort((a, b) => a.localeCompare(b, 'es')).forEach((value) => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                localitySelect.appendChild(option);
            });
            if (Array.from(localitySelect.options).some((opt) => opt.value === previousLocality)) {
                localitySelect.value = previousLocality;
            }
            reinitializeSelect2(localitySelect, localityPlaceholder);
        }
    }

    function normalizeString(text) {
        return (text || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    function getLocalidadNombre(centro, fallback = '-') {
        if (centro.localidad && typeof centro.localidad === 'object' && centro.localidad.nombre) {
            return centro.localidad.nombre;
        }
        return centro.localidad || fallback;
    }

    function getColspan(tbody) {
        return tbody?.parentElement?.querySelectorAll('th').length || 5;
    }

    function renderCentroRow(centro, tableBodyId) {
        const isGlobal = tableBodyId === 'tablaCentrosGlobalesBody';
        const badgeClass = isGlobal ? 'bg-info-subtle text-info' : 'bg-success-subtle text-success';
        const tipoLabel = centro.get_tipo_centro_display || centro.tipo || '-';
        const contacto = centro.nombre_contacto || '-';
        const celularCell = centro.celular ? `<a href="tel:${centro.celular}" class="text-decoration-none">${centro.celular}</a>` : '<span>-</span>';
        const emailCell = centro.email ? `<a href="mailto:${centro.email}" class="text-decoration-none text-truncate d-block">${centro.email}</a>` : '<span>-</span>';
        const localidad = getLocalidadNombre(centro, '-');

        if (isGlobal) {
            return `
                <tr class="fila-centro-global" data-id="${centro.id}">
                    <td class="small">${centro.nombre || '-'}</td>
                    <td><span class="badge ${badgeClass}">${tipoLabel}</span></td>
                    <td class="small">${contacto}</td>
                    <td class="small">${celularCell}</td>
                    <td class="small">${emailCell}</td>
                    <td class="d-flex gap-1">
                        <button type="button" class="btn btn-outline-primary btn-sm btn-ver-detalles-centro" title="Ver detalles" data-id="${centro.id}" data-type="global">
                            <i class="bi bi-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        }

        return `
            <tr class="fila-centro-propio" data-id="${centro.id}">
                <td class="small">${centro.nombre || '-'}</td>
                <td><span class="badge ${badgeClass}">${tipoLabel}</span></td>
                <td class="small">${localidad}</td>
                <td class="small">${celularCell}</td>
                <td class="small"><small class="text-muted">${centro.nota || '-'}</small></td>
                <td class="d-flex gap-1">
                    <button type="button" class="btn btn-outline-primary btn-sm btn-ver-detalles-centro" title="Ver detalles" data-id="${centro.id}" data-type="propio">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger btn-sm btn-eliminar-centro" title="Eliminar" data-id="${centro.id}" data-type="propio">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    function renderTablaCentros(centros, tableBodyId) {
        const tbody = el(tableBodyId);
        if (!tbody) {
            return;
        }
        if (!Array.isArray(centros)) {
            tbody.innerHTML = '<tr class="text-danger"><td colspan="' + getColspan(tbody) + '">[Error] Centros no es un array</td></tr>';
            return;
        }
        if (!centros.length) {
            tbody.innerHTML = '<tr class="text-muted text-center"><td colspan="' + getColspan(tbody) + '" class="py-3"><small>Sin registros</small></td></tr>';
            return;
        }
        tbody.innerHTML = centros.map((centro) => renderCentroRow(centro, tableBodyId)).join('');
    }

    function updateBadge(count, badgeId) {
        const badge = el(badgeId);
        if (badge) {
            badge.textContent = count + ' registros';
        }
    }

    function filterCentros(centros, filtros) {
        return centros.filter((centro) => {
            if (filtros.nombre && !normalizeString(centro.nombre).includes(normalizeString(filtros.nombre))) {
                return false;
            }
            if (filtros.tipo && centro.get_tipo_centro_display && centro.get_tipo_centro_display !== filtros.tipo && centro.tipo !== filtros.tipo) {
                return false;
            }
            if (filtros.localidad) {
                const localidad = getLocalidadNombre(centro, '');
                if (localidad && normalizeString(localidad) !== normalizeString(filtros.localidad)) {
                    return false;
                }
            }
            if (filtros.contacto && centro.nombre_contacto && !normalizeString(centro.nombre_contacto).includes(normalizeString(filtros.contacto))) {
                return false;
            }
            if (filtros.email && centro.email && !normalizeString(centro.email).includes(normalizeString(filtros.email))) {
                return false;
            }
            if (filtros.telefono && centro.celular && !normalizeString(centro.celular).includes(normalizeString(filtros.telefono))) {
                return false;
            }
            return true;
        });
    }

    function syncSelectValue(selectId, value) {
        const select = el(selectId);
        if (!select) {
            return;
        }
        const normalizedValue = value ?? '';
        select.value = normalizedValue;
        if (root.jQuery?.fn?.select2) {
            root.jQuery(select).val(normalizedValue).trigger('change');
        }
    }

    function setText(id, value) {
        const node = el(id);
        if (node) {
            node.textContent = value;
        }
    }

    function syncLocalidadSelectWithDelay(locId) {
        const select = el('editCentroLocalidad');
        if (!select) {
            return;
        }
        const value = String(locId || '');
        const alreadyHas = Array.from(select.options).some((opt) => String(opt.value) === value);
        select.value = value;
        syncSelectValue('editCentroLocalidad', value);
        if (alreadyHas || !locId) {
            return;
        }
        const option = document.createElement('option');
        option.value = value;
        option.textContent = 'Valor antiguo: ' + value;
        select.appendChild(option);
        select.value = value;
        syncSelectValue('editCentroLocalidad', value);
    }

    function populateCentroDetailsModal(centro, isPropio) {
        const modal = new bootstrap.Modal(el(isPropio ? 'modalDetallesCentroPropio' : 'modalDetallesCentro'));
        const prefix = isPropio ? 'detCentroPropio' : 'detCentro';
        setText(prefix + 'Nombre', centro.nombre || '-');
        setText(prefix + 'Tipo', centro.get_tipo_centro_display || centro.tipo || '-');
        setText(prefix + 'Localidad', getLocalidadNombre(centro, '-'));
        setText(prefix + 'Contacto', centro.nombre_contacto || '-');
        setText(prefix + 'Celular', centro.celular || '-');
        setText(prefix + 'Email', centro.email || '-');
        if (isPropio) {
            el('inputCentroId').value = centro.id ?? '';
            setText('detCentroPropioNotas', (centro.nota && String(centro.nota).trim()) ? centro.nota : '-');
        }
        modal.show();
    }

    function prepareCentroEditForm(centro, fallbackData) {
        const nombre = fallbackData?.nombre || '';
        const localidad = fallbackData?.localidad || '';
        const contacto = fallbackData?.contacto || '';
        const celular = fallbackData?.celular || '';
        const email = fallbackData?.email || '';
        const tiposCatalogo = readJsonArrayFromScript('tiposCentroCatalogo');

        el('editCentroInputId').value = centro.id || '';
        el('editCentroNombre').value = centro.nombre || nombre || '';

        let tipoValue = centro.tipo || '';
        if (!tipoValue && centro.get_tipo_centro_display) {
            const match = tiposCatalogo.find((item) => item.label === centro.get_tipo_centro_display);
            tipoValue = match ? match.value : '';
        }
        el('editCentroTipo').value = tipoValue;
        syncSelectValue('editCentroTipo', tipoValue);

        const localidadValue = centro.localidad?.localidad_id || centro.localidad || localidad || '';
        el('editCentroLocalidad').value = localidadValue;
        syncLocalidadSelectWithDelay(localidadValue);

        el('editCentroCelular').value = centro.celular || celular || '';
        el('editCentroEmail').value = centro.email || email || '';
        el('editCentroContacto').value = centro.nombre_contacto || contacto || '';
        el('editCentroNotas').value = centro.nota || '';

        if (centro.id) {
            el('formEditarCentro').action = `/punto-eca/centros/editar-centro/${centro.id}/guardar/`;
        }
    }

    function resetCentroEditFormToNew() {
        const form = el('formEditarCentro');
        if (form) {
            form.reset();
            form.action = '/punto-eca/centros/registrar-centro/guardar/';
            form.querySelector('#editCentroInputId').value = '';
            form.querySelector('#editarCentroFeedback')?.remove();
        }
        const modalTitle = el('modalEditarCentroPropioLabel');
        if (modalTitle) {
            modalTitle.innerHTML = '<i class="bi bi-plus-circle me-2"></i>Agregar Centro';
        }
    }

    function markEditedCentroRow(centroId) {
        const filas = document.querySelectorAll('#tablaCentrosPropiosBody tr');
        for (const fila of filas) {
            if (fila.dataset.id === String(centroId)) {
                fila.classList.add('table-success');
                setTimeout(() => fila.classList.remove('table-success'), 1200);
                break;
            }
        }
    }

    function handleCentroDetallesClick(btn) {
        const tipo = btn.dataset.type;
        const id = btn.dataset.id;
        const centro = tipo === 'global'
            ? (root.CENTROS_GLOBALES || []).find((item) => String(item.id) === String(id))
            : (root.CENTROS_PROPIOS || []).find((item) => String(item.id) === String(id));
        if (!centro) {
            alert('No se encontraron los datos del centro');
            return;
        }
        populateCentroDetailsModal(centro, tipo === 'propio');
    }

    function handleEditarCentroPropioClick() {
        const id = el('inputCentroId')?.value;
        if (!id) {
            console.error('[EDIT-CENTRO] No centro UUID selected');
            return;
        }
        const centro = (root.CENTROS_PROPIOS || []).find((item) => String(item.id) === String(id));
        if (!centro) {
            alert('No se encuentra el centro propio para edición.');
            return;
        }
        const localidadesCatalogo = readJsonArrayFromScript('localidadesCatalogo');
        const tiposCentroCatalogo = readJsonArrayFromScript('tiposCentroCatalogo');
        populateCatalogSelect('editCentroLocalidad', localidadesCatalogo, 'localidad_id', 'nombre', '-- Seleccione --');
        populateCatalogSelect('editCentroTipo', tiposCentroCatalogo, 'value', 'label', '-- Seleccione --');
        prepareCentroEditForm(centro, {
            nombre: el('detCentroNombre')?.textContent || '',
            localidad: el('detCentroLocalidad')?.textContent || '',
            contacto: el('detCentroContacto')?.textContent || '',
            celular: el('detCentroCelular')?.textContent || '',
            email: el('detCentroEmail')?.textContent || '',
        });
        const modalDetalles = bootstrap.Modal.getInstance(el('modalDetallesCentroPropio'));
        if (modalDetalles) {
            modalDetalles.hide();
        }
        const modalEditar = new bootstrap.Modal(el('modalEditarCentroPropio'));
        modalEditar.show();
    }

    function handleAgregarCentroClick() {
        resetCentroEditFormToNew();
        const localidadesCatalogo = readJsonArrayFromScript('localidadesCatalogo');
        const tiposCentroCatalogo = readJsonArrayFromScript('tiposCentroCatalogo');
        populateCatalogSelect('editCentroLocalidad', localidadesCatalogo, 'localidad_id', 'nombre', '-- Seleccione --');
        populateCatalogSelect('editCentroTipo', tiposCentroCatalogo, 'value', 'label', '-- Seleccione --');
        const modalEditar = new bootstrap.Modal(el('modalEditarCentroPropio'));
        modalEditar.show();
    }

    async function submitCentroEdit(formEditarCentro) {
        const response = await fetch(formEditarCentro.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: new FormData(formEditarCentro),
        });
        const data = await response.json();
        let msg = 'Error al guardar los cambios';
        if (typeof data.mensaje === 'string') {
            msg = data.mensaje;
        } else if (data.status === 'ok') {
            msg = 'Edicion exitosa';
        }
        let feedback = el('editarCentroFeedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.id = 'editarCentroFeedback';
            feedback.className = 'alert';
            document.querySelector('#formEditarCentro .modal-body')?.prepend(feedback);
        }
        if (data.status === 'ok' && data.centro) {
            feedback.textContent = msg;
            feedback.className = 'alert alert-success';
            const idx = (root.CENTROS_PROPIOS || []).findIndex((item) => String(item.id) === String(data.centro.id));
            if (idx !== -1) {
                root.CENTROS_PROPIOS[idx] = data.centro;
            }
            renderTablaCentros(root.CENTROS_PROPIOS, 'tablaCentrosPropiosBody');
            updateBadge(root.CENTROS_PROPIOS.length, 'badgePropiosCount');
            setTimeout(() => root.location.reload(), 1000);
            setTimeout(() => markEditedCentroRow(data.centro.id), 500);
            return;
        }
        feedback.textContent = msg;
        feedback.className = 'alert alert-danger';
    }

    async function deleteCentroByButton(btn) {
        const centroId = btn.dataset.id;
        if (!centroId) {
            alert('ID de centro no encontrado');
            return;
        }
        if (!confirm('¿Seguro que queres eliminar este centro? Esta accion no se puede deshacer.')) {
            return;
        }
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Eliminando...';
        try {
            const response = await fetch(`eliminar-centro/${centroId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                },
            });
            let data = {};
            let jsonOk = false;
            try {
                data = await response.json();
                jsonOk = true;
            } catch (error) {
                console.warn('[DELETE-CENTRO] Respuesta no JSON', error);
            }
            if ((response.ok && (data.status === 'ok' || data.error === false)) || (response.ok && !jsonOk)) {
                mostrarMensajeCentro('success', data.mensaje || 'Centro eliminado correctamente.');
                if (Array.isArray(root.CENTROS_PROPIOS)) {
                    root.CENTROS_PROPIOS = root.CENTROS_PROPIOS.filter((item) => String(item.id) !== String(centroId));
                }
                renderTablaCentros(root.CENTROS_PROPIOS, 'tablaCentrosPropiosBody');
                updateBadge(root.CENTROS_PROPIOS.length, 'badgePropiosCount');
                return;
            }
            if (jsonOk) {
                mostrarMensajeCentro('danger', data.mensaje || data.error || 'Error al eliminar el centro');
                return;
            }
            mostrarMensajeCentro('danger', 'Error inesperado eliminando centro');
        } catch (error) {
            console.error('[DELETE-CENTRO] Error de red o inesperado eliminando centro', error);
            mostrarMensajeCentro('danger', 'Error de red o inesperado eliminando centro');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-trash"></i>';
        }
    }

    function bindFilterForm(scope) {
        const form = el('filtrosFormCentros' + scope);
        const data = scope === 'Global' ? (root.CENTROS_GLOBALES || []) : (root.CENTROS_PROPIOS || []);
        if (!form) {
            return;
        }
        initSelect2Filters(data, scope);

        const filterButton = el(scope === 'Global' ? 'btnFiltrarGlobales' : 'btnFiltrarPropios');
        const clearButton = el(scope === 'Global' ? 'btnLimpiarGlobales' : 'btnLimpiarPropios');
        if (filterButton) {
            filterButton.addEventListener('click', () => {
                initSelect2Filters(data, scope);
                const filtros = {
                    nombre: el('filtroNombre' + scope).value,
                    tipo: el('filtroTipo' + scope).value,
                    localidad: el('filtroLocalidad' + scope).value,
                    contacto: el('filtroContacto' + scope).value,
                    email: el('filtroEmail' + scope).value,
                    telefono: el('filtroTelefono' + scope).value,
                };
                const filtrados = filterCentros(data, filtros);
                renderTablaCentros(filtrados, scope === 'Global' ? 'tablaCentrosGlobalesBody' : 'tablaCentrosPropiosBody');
                updateBadge(filtrados.length, scope === 'Global' ? 'badgeGlobalesCount' : 'badgePropiosCount');
            });
        }
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                limpiarCampos(form);
                initSelect2Filters(data, scope);
                const filtros = {
                    nombre: el('filtroNombre' + scope).value,
                    tipo: el('filtroTipo' + scope).value,
                    localidad: el('filtroLocalidad' + scope).value,
                    contacto: el('filtroContacto' + scope).value,
                    email: el('filtroEmail' + scope).value,
                    telefono: el('filtroTelefono' + scope).value,
                };
                const filtrados = filterCentros(data, filtros);
                renderTablaCentros(filtrados, scope === 'Global' ? 'tablaCentrosGlobalesBody' : 'tablaCentrosPropiosBody');
                updateBadge(filtrados.length, scope === 'Global' ? 'badgeGlobalesCount' : 'badgePropiosCount');
            });
        }
    }

    function bindDetailButtons() {
        document.addEventListener('click', (event) => {
            const btn = event.target.closest('.btn-ver-detalles-centro');
            if (!btn) {
                return;
            }
            handleCentroDetallesClick(btn);
        });
    }

    function bindDeleteButtons() {
        document.addEventListener('click', (event) => {
            const btn = event.target.closest('.btn-eliminar-centro');
            if (btn?.dataset.type !== 'propio') {
                return;
            }
            deleteCentroByButton(btn);
        });
    }

    function bindEditSubmit() {
        const formEditarCentro = el('formEditarCentro');
        if (!formEditarCentro) {
            return;
        }
        formEditarCentro.addEventListener('submit', (event) => {
            event.preventDefault();
            const submitBtn = formEditarCentro.querySelector('[type=submit]');
            if (submitBtn) {
                submitBtn.disabled = true;
            }
            submitCentroEdit(formEditarCentro)
                .catch((error) => {
                    console.error('[EDIT-CENTRO] Error inesperado en la comunicacion', error);
                    alert('Error inesperado en la comunicacion');
                })
                .finally(() => {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                    }
                });
        });
    }

    function initCentroSection() {
        ensureMensajesContainer();
        loadCentroState();

        if (el('mensajesCentroContainer')) {
            // Keep behavior consistent when the fragment is re-rendered.
        }

        initSelect2Filters(root.CENTROS_GLOBALES || [], 'Global');
        initSelect2Filters(root.CENTROS_PROPIOS || [], 'Propio');

        renderTablaCentros(root.CENTROS_GLOBALES || [], 'tablaCentrosGlobalesBody');
        renderTablaCentros(root.CENTROS_PROPIOS || [], 'tablaCentrosPropiosBody');
        updateBadge((root.CENTROS_GLOBALES || []).length, 'badgeGlobalesCount');
        updateBadge((root.CENTROS_PROPIOS || []).length, 'badgePropiosCount');

        bindFilterForm('Global');
        bindFilterForm('Propio');
        bindDetailButtons();
        bindDeleteButtons();
        bindEditSubmit();

        el('btnAbrirEditarCentro')?.addEventListener('click', handleEditarCentroPropioClick);
        el('btnEditarCentroPropio')?.addEventListener('click', handleEditarCentroPropioClick);
        el('btnAgregarNuevoCentro')?.addEventListener('click', handleAgregarCentroClick);
    }

    document.addEventListener('DOMContentLoaded', initCentroSection);
})();
