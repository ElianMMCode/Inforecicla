function initNotificacionesWS(dropdownId, iconMap, defaultIcon) {
    var resolvedDefault = defaultIcon || 'bi-bell-fill';
    var protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    var ws = new WebSocket(protocol + '://' + location.host + '/ws/notificaciones/');

    ws.onmessage = function (e) {
        var data = JSON.parse(e.data);

        var badge = document.querySelector('#' + dropdownId + ' .badge.bg-danger');
        if (badge) {
            var current = Number.parseInt(badge.textContent.trim(), 10) || 0;
            badge.textContent = current + 1;
        } else {
            var btn = document.getElementById(dropdownId);
            if (btn) {
                var newBadge = document.createElement('span');
                newBadge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
                newBadge.style.fontSize = '.65rem';
                newBadge.innerHTML = '1<span class="visually-hidden">notificaciones sin leer</span>';
                btn.appendChild(newBadge);
            }
        }

        var menu = document.querySelector('[aria-labelledby="' + dropdownId + '"]');
        if (!menu) return;

        var empty = menu.querySelector('.text-center.text-muted');
        if (empty) empty.remove();

        var icon = (iconMap && iconMap[data.tipo]) || resolvedDefault;
        var item = document.createElement('div');
        item.className = 'dropdown-item d-flex gap-2 align-items-start py-2 px-3 border-bottom bg-warning-subtle';
        item.style.whiteSpace = 'normal';
        item.setAttribute('data-notif-id', data.id);
        item.innerHTML =
            '<a href="' + data.url + '" class="d-flex gap-2 align-items-start flex-grow-1 text-decoration-none text-reset">' +
            '<span class="rounded-circle bg-success-subtle text-success d-flex align-items-center justify-content-center flex-shrink-0 mt-1" style="width:32px;height:32px;">' +
            '<i class="bi ' + icon + '"></i></span>' +
            '<span class="flex-grow-1">' +
            '<span class="d-block small fw-semibold text-dark">' + data.titulo + '</span>' +
            '<span class="d-block text-muted" style="font-size:.72rem;"><i class="bi bi-clock me-1"></i>' + data.fecha + '</span>' +
            '</span>' +
            '<span class="badge rounded-pill bg-success align-self-center" style="font-size:.55rem;">Nueva</span>' +
            '</a>';

        var header = menu.querySelector('.px-3.py-2.border-bottom.bg-light');
        if (header && header.nextSibling) {
            menu.insertBefore(item, header.nextSibling);
        } else {
            menu.prepend(item);
        }
    };
}
