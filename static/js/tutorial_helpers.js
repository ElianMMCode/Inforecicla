var driverObj = (typeof globalThis !== 'undefined' && globalThis.driver) ? globalThis.driver.js.driver : null;
var STORAGE_KEYS = ['tutorial_ciu_datos', 'tutorial_ciu_comentarios', 'tutorial_ciu_chat', 'tutorial_ciu_guardados', 'tutorial_ciu_mapa', 'tutorial_ciu_pub'];

function getCSRFToken() {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var c = cookies[i].trim();
        if (c.indexOf('csrftoken=') === 0) return c.substring(10);
    }
    return '';
}

function notificarServidor() {
    fetch('/api/tutorial-visto/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() }
    }).catch(function(e) { console.error('Error al notificar tutorial:', e); });
}

function checkAllToursDone() {
    var allDone = STORAGE_KEYS.every(function(k) { return localStorage.getItem(k) === '1'; });
    if (allDone) notificarServidor();
}

function iniciarTutorial(steps) {
    if (!steps || !steps.length) { checkAllToursDone(); return; }
    var tour = driverObj({
        showProgress: true,
        nextBtnText: 'Siguiente',
        prevBtnText: 'Anterior',
        doneBtnText: 'Entendido',
        onDestroyed: function() { checkAllToursDone(); },
        steps: steps
    });
    tour.drive();
}

function pasosDesdeConfig(lista) {
    var result = [];
    lista.forEach(function(item) {
        var el = document.getElementById(item[0]);
        if (el) result.push({ element: '#' + item[0], popover: { title: item[1], description: item[2], side: item[3] || 'bottom' } });
    });
    return result;
}

function storageGet(key) {
    try { return localStorage.getItem(key); } catch(e) { return null; }
}

function storageSet(key, val) {
    try { localStorage.setItem(key, val); return true; } catch(e) { console.error('Error en localStorage:', e); return false; }
}

function storageRemove(key) {
    try { localStorage.removeItem(key); } catch(e) { console.error('Error al limpiar localStorage:', e); }
}