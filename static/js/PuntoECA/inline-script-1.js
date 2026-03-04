(function() {
            const globalSelect = document.getElementById('centro_global');
            const propioSelect = document.getElementById('centro_propio');
            const hiddenInput = document.getElementById('centro_hidden');

            function sync(from, other) {
                const val = from.value || '';
                hiddenInput.value = val; // ← aquí se copia el UUID al hidden
                other.disabled = !!val; // si elegí uno, deshabilito el otro
                if (!val) other.disabled = false;
            }

            globalSelect.addEventListener('change', () => sync(globalSelect, propioSelect));
            propioSelect.addEventListener('change', () => sync(propioSelect, globalSelect));

            // Re-sync al volver con "atrás" del navegador
            window.addEventListener('pageshow', () => {
                if (globalSelect.value) sync(globalSelect, propioSelect);
                else if (propioSelect.value) sync(propioSelect, globalSelect);
                else hiddenInput.value = '';
            });
        })();