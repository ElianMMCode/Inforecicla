export function showAlert(icon, title, text, confirmButtonColor = '#198754') {
    if (globalThis.Swal?.fire) {
        return globalThis.Swal.fire({
            icon,
            title,
            text,
            confirmButtonText: 'Entendido',
            confirmButtonColor,
        });
    }

    // If SweetAlert2 is not available, avoid native alerts — log and return a resolved Promise
    console.warn('SweetAlert2 no disponible. Mensaje:', title, text);
    return Promise.resolve({ isConfirmed: true });
}

export function showValidationAlert(message) {
    return showAlert('warning', 'Campos obligatorios pendientes', message);
}

export function showResultAlert(icon, title, text) {
    return showAlert(icon, title, text);
}