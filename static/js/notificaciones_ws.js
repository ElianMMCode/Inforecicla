function initNotificacionesWS(dropdownId, iconMap, defaultIcon = 'bi-bell-fill') {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${location.host}/ws/notificaciones/`);

    ws.onmessage = function (e) {
        const data = JSON.parse(e.data);

        const badge = document.querySelector(`#${dropdownId} .badge.bg-danger`);
        if (badge) {
            const current = Number.parseInt(badge.textContent.trim(), 10) || 0;
            badge.textContent = current + 1;
        } else {
            const btn = document.getElementById(dropdownId);
            if (btn) {
                const newBadge = document.createElement('span');
                newBadge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger';
                newBadge.style.fontSize = '.65rem';
                newBadge.innerHTML = '1<span class="visually-hidden">notificaciones sin leer</span>';
                btn.appendChild(newBadge);
            }
        }

        const menu = document.querySelector(`[aria-labelledby="${dropdownId}"]`);
        if (!menu) return;

        const empty = menu.querySelector('.text-center.text-muted');
        if (empty) empty.remove();

        const icon = (iconMap && iconMap[data.tipo]) || defaultIcon;
        const item = document.createElement('div');
        item.className = 'dropdown-item d-flex gap-2 align-items-start py-2 px-3 border-bottom bg-warning-subtle';
        item.style.whiteSpace = 'normal';
        item.setAttribute('data-notif-id', data.id);
        item.innerHTML = `
            <a href="${data.url}" class="d-flex gap-2 align-items-start flex-grow-1 text-decoration-none text-reset">
                <span class="rounded-circle bg-success-subtle text-success d-flex align-items-center justify-content-center flex-shrink-0 mt-1" style="width:32px;height:32px;">
                    <i class="bi ${icon}"></i>
                </span>
                <span class="flex-grow-1">
                    <span class="d-block small fw-semibold text-dark">${data.titulo}</span>
                    <span class="d-block text-muted" style="font-size:.72rem;"><i class="bi bi-clock me-1"></i>${data.fecha}</span>
                </span>
                <span class="badge rounded-pill bg-success align-self-center" style="font-size:.55rem;">Nueva</span>
            </a>`;

        const header = menu.querySelector('.px-3.py-2.border-bottom.bg-light');
        if (header && header.nextSibling) {
            menu.insertBefore(item, header.nextSibling);
        } else {
            menu.prepend(item);
        }
    };
}
