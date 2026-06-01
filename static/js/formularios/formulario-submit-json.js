export async function submitFormJson(form) {
    const response = await globalThis.fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            Accept: 'application/json',
        },
    });

    const payload = await response.json().catch((error) => {
        if (globalThis.console?.debug) {
            globalThis.console.debug('No se pudo leer la respuesta JSON:', error);
        }
        return null;
    });

    return { response, payload };
}