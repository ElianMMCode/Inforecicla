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

    globalThis.alert(text);
    return Promise.resolve();
}

export function showValidationAlert(message) {
    return showAlert('warning', 'Campos obligatorios pendientes', message);
}

export function showResultAlert(icon, title, text) {
    return showAlert(icon, title, text);
}