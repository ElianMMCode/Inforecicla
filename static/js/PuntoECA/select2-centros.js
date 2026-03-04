/**
 * Select2 Centros - Script para inicializar Select2 en filtros de centros
 * Este script se ejecuta múltiples veces para asegurar que Select2 se inicialize
 * aunque sea en un fragment de Thymeleaf
 */

console.log('select2-centros.js cargado');

// Función para inicializar Select2 en filtros de centros
function inicializarSelect2Centros() {
    console.log('[Select2] Buscando elementos con clase .js-select-centros...');

    const tieneSelect2 = window.jQuery && typeof window.jQuery.fn.select2 === 'function';

    if (!tieneSelect2) {
        console.warn('[Select2] jQuery o Select2 aún no disponibles');
        return;
    }

    const $ = window.jQuery;
    const selectores = document.querySelectorAll('.js-select-centros');

    if (selectores.length === 0) {
        console.warn('[Select2] No se encontraron elementos .js-select-centros');
        return;
    }

    console.log('[Select2] Se encontraron', selectores.length, 'elementos');

    selectores.forEach(function(selectEl) {
        // Verificar si ya fue inicializado
        if ($(selectEl).hasClass('select2-hidden-accessible')) {
            console.log('[Select2] ✅ Ya está inicializado:', selectEl.id);
            return;
        }

        console.log('[Select2] Inicializando:', selectEl.id);
        const $select = $(selectEl);

        try {
            $select.select2({
                theme: 'bootstrap-5',
                width: '100%',
                placeholder: selectEl.dataset.placeholder || 'Selecciona una opción',
                allowClear: true,
                language: 'es',
                minimumResultsForSearch: Infinity
            });

            console.log('[Select2] ✅ Inicializado correctamente:', selectEl.id);

            // Eventos de Select2
            $select.on('select2:select select2:unselect select2:clear', function() {
                console.log('[Select2] Evento disparado en:', selectEl.id);
                if (selectEl.id === 'filtrarTipoCentroGlobalSelect') {
                    if (typeof filtrarCentrosGlobales === 'function') {
                        filtrarCentrosGlobales();
                    }
                } else if (selectEl.id === 'filtrarTipoCentroPropiosSelect') {
                    if (typeof filtrarCentrosPropios === 'function') {
                        filtrarCentrosPropios();
                    }
                }
            });
        } catch(error) {
            console.error('[Select2] ❌ Error en:', selectEl.id, error);
        }
    });
}

// Estrategia múltiple de inicialización
// 1. Si DOM ya está cargado
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[Select2] DOMContentLoaded');
        inicializarSelect2Centros();
    });
} else {
    console.log('[Select2] DOM ya cargado');
    inicializarSelect2Centros();
}

// 2. También ejecutar después de delays (por si el fragment se carga después)
setTimeout(function() {
    console.log('[Select2] Ejecución en 500ms');
    inicializarSelect2Centros();
}, 500);

setTimeout(function() {
    console.log('[Select2] Ejecución en 1000ms');
    inicializarSelect2Centros();
}, 1000);

setTimeout(function() {
    console.log('[Select2] Ejecución en 2000ms');
    inicializarSelect2Centros();
}, 2000);

// 3. Usar MutationObserver para detectar cuando se insertan nuevos elementos
if (window.MutationObserver) {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                // Verificar si alguno de los nodos añadidos contiene .js-select-centros
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.querySelector && node.querySelector('.js-select-centros')) {
                            console.log('[Select2] Elemento .js-select-centros detectado en MutationObserver');
                            setTimeout(inicializarSelect2Centros, 100);
                        }
                    }
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false,
        characterData: false
    });

    console.log('[Select2] MutationObserver activado');
}

// Exportar función global para fácil acceso
window.inicializarSelect2Centros = inicializarSelect2Centros;

