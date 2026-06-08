function _validarCampo(campo) {
    let valido = campo.checkValidity() && campo.value.trim() !== '';
    if ('lettersRequired' in campo.dataset && campo.value.trim() !== '') {
        const tieneLetra = /[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]/.test(campo.value);
        if (!tieneLetra) valido = false;
    }
    return valido;
}

const _MENSAJES_ERROR = {
    patternMismatch: (campo, etiqueta) => {
        if (campo.name === 'nombres' || campo.name === 'apellidos') return etiqueta + ': Solo se permiten letras, espacios, guiones o apóstrofes.';
        if (campo.name === 'celular') return etiqueta + ': Debe iniciar con 3 y tener exactamente 10 dígitos.';
        if (campo.name === 'fechaNacimiento' || campo.name === 'fecha_nacimiento') return etiqueta + ': Usa el formato DD-MM-AAAA o AAAA-MM-DD.';
        return etiqueta + ': El formato ingresado no es válido.';
    },
    valueMissing: (campo, etiqueta) => etiqueta + ' es obligatorio.',
    tooShort: (campo, etiqueta) => etiqueta + ': Debe tener al menos ' + campo.minLength + ' caracteres.',
    tooLong: (campo, etiqueta) => etiqueta + ': Debe tener máximo ' + campo.maxLength + ' caracteres.',
    typeMismatch: (campo, etiqueta) => etiqueta + ': El formato no es correcto.',
    rangeUnderflow: (campo, etiqueta) => etiqueta + ': El valor está fuera del rango permitido.',
    rangeOverflow: (campo, etiqueta) => etiqueta + ': El valor está fuera del rango permitido.',
    customError: (campo, etiqueta) => etiqueta + ': ' + campo.validationMessage,
    badInput: (campo, etiqueta) => etiqueta + ': El valor ingresado no es válido.',
    default: (campo, etiqueta) => etiqueta + ': El valor ingresado no es válido.',
};

function _mensajeValidacionES(campo) {
    if (campo.validity.valid && !campo.validity.customError) return '';
    const etiqueta = MARCAR_ERRORES[campo.name] || campo.name.charAt(0).toUpperCase() + campo.name.slice(1);
    for (const tipo of ['valueMissing', 'patternMismatch', 'tooShort', 'tooLong', 'typeMismatch', 'rangeUnderflow', 'rangeOverflow', 'customError', 'badInput']) {
        if (campo.validity[tipo]) return _MENSAJES_ERROR[tipo](campo, etiqueta);
    }
    return _MENSAJES_ERROR.default(campo, etiqueta);
}

function escaparHtml(texto) {
    return String(texto).replace(/[&<>"']/g, function (c) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] || c;
    });
}

function mostrarErroresSwal(errores) {
    if (typeof Swal === 'undefined' || !errores || errores.length === 0) return;
    return Swal.fire({
        icon: 'error',
        title: 'Corrige los campos',
        html: '<div class="text-start">' +
            errores.map(function (e) { return escaparHtml(e); }).join(' ') +
            '</div>',
        confirmButtonColor: '#198754',
    });
}

function _recolectarErrores(form) {
    const errores = [];
    const invalidFields = [];
    const campos = form.querySelectorAll('[required], [pattern], [minlength]');
    for (const campo of campos) {
        if (!campo.checkValidity()) {
            const msg = _mensajeValidacionES(campo);
            if (msg) {
                errores.push(msg);
                invalidFields.push({ field: campo, msg });
            }
        }
    }
    return { errores, invalidFields };
}

function _marcarCamposInvalidos(invalidFields) {
    for (const item of invalidFields) {
        item.field.classList.add('is-invalid');
        const contenedor = item.field.closest('.col-12, .col-md-6, .col-md-12, .mb-3');
        if (contenedor) {
            const fb = contenedor.querySelector('.invalid-feedback');
            if (fb) fb.textContent = item.msg;
        }
    }
}

function _mostrarErroresYMarcar(form) {
    const result = _recolectarErrores(form);
    if (result.errores.length === 0) return false;
    const prom = mostrarErroresSwal(result.errores);
    if (prom?.then) {
        prom.then(() => { _marcarCamposInvalidos(result.invalidFields); });
    }
    return true;
}

function _vincularValidacionEnVivo(form) {
    form.addEventListener('invalid', (e) => { e.preventDefault(); }, true);
    const campos = form.querySelectorAll('input, select, textarea');
    for (const campo of campos) {
        const eventName = campo.tagName === 'SELECT' ? 'change' : 'input';
        campo.addEventListener(eventName, () => {
            const valido = _validarCampo(campo);
            campo.classList.toggle('is-valid', valido);
            campo.classList.toggle('is-invalid', !valido && (campo.value.trim() !== '' || campo.required));
        });
        campo.addEventListener('blur', () => {
            const valido = _validarCampo(campo);
            campo.classList.toggle('is-valid', valido);
            campo.classList.toggle('is-invalid', !valido && (campo.value.trim() !== '' || campo.required));
        });
    }
}

function initModalForm(formId, validarFn) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (typeof validarFn === 'function' && !validarFn(form)) {
            form.classList.add('was-validated');
            _mostrarErroresYMarcar(form);
            return;
        }

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            _mostrarErroresYMarcar(form);
            return;
        }

        form.classList.add('was-validated');

        Swal.fire({
            icon: 'question',
            title: '¿Guardar cambios?',
            text: 'Los datos están completos y listos para guardarse.',
            showCancelButton: true,
            confirmButtonText: 'Sí, guardar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#198754',
            cancelButtonColor: '#6c757d',
        }).then((result) => {
            if (result.isConfirmed) form.submit();
        });
    });

    _vincularValidacionEnVivo(form);
}

const MARCAR_ERRORES = {
    nombre: 'Nombre',
    descripcion: 'Descripción',
    estado: 'Estado',
    categoria_id: 'Categoría',
    tipo_id: 'Tipo',
    apellidos: 'Apellidos',
    email: 'Correo electrónico',
    celular: 'Celular',
    tipo_documento: 'Tipo de documento',
    numero_documento: 'Número de documento',
    localidad_id: 'Localidad',
    fecha_nacimiento: 'Fecha de nacimiento',
    tipo_usuario: 'Tipo de usuario',
    password: 'Contraseña', // NOSONAR - field label, not credential
    nombres: 'Nombres',
    direccion: 'Dirección',
    telefono_punto: 'Teléfono',
    sitio_web: 'Sitio web',
    horario_atencion: 'Horario de atención',
    logo_url_punto: 'Logo',
    latitud: 'Latitud',
    longitud: 'Longitud',
    tipo: 'Tipo',
    titulo: 'Título',
    contenido: 'Contenido',
    multimedia: 'Multimedia',
    nombre_punto: 'Nombre del punto',
    email_gestor: 'Email del gestor',
    passwordConfirm: 'Confirmar contraseña',
    is_active: 'Estado de la cuenta',
    estado_usuario: 'Estado del usuario',
    ciudad: 'Ciudad',
    foto_url_punto: 'Foto',
    tipoDocumento: 'Tipo de documento',
    numeroDocumento: 'Número de documento',
    localidad: 'Localidad',
};

function limpiarErroresForm(form) {
    if (!form) return;
    for (const el of form.querySelectorAll('.is-invalid, .is-valid')) {
        el.classList.remove('is-invalid', 'is-valid');
    }
    form.classList.remove('was-validated');
}

function limpiarErroresModal(modalEl) {
    if (!modalEl) return;
    for (const f of modalEl.querySelectorAll('form')) {
        limpiarErroresForm(f);
    }
}

function _trimPuntos(texto) {
    const s = String(texto);
    let inicio = 0;
    while (inicio < s.length && (s[inicio] === '.' || s[inicio] === ' ' || s[inicio] === '\t' || s[inicio] === '\n' || s[inicio] === '\r')) inicio++;
    let fin = s.length;
    while (fin > inicio && (s[fin-1] === '.' || s[fin-1] === ' ' || s[fin-1] === '\t' || s[fin-1] === '\n' || s[fin-1] === '\r')) fin--;
    return s.slice(inicio, fin);
}

function marcarErroresForm(form, fieldErrors) {
    if (!form || !fieldErrors) return;
    for (const key in fieldErrors) {
        if (!Object.prototype.hasOwnProperty.call(fieldErrors, key) || key === '_general') continue;
        const field = form.querySelector(`[name="${key}"]`);
        if (!field) continue;
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        const contenedor = field.closest('.col-12, .col-md-6, .col-md-12, .mb-3');
        if (contenedor) {
            const feedback = contenedor.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.textContent = _trimPuntos(fieldErrors[key]);
            }
        }
    }
    form.classList.remove('was-validated');
}

function _procesarErrorRespuesta(data) {
    const errorList = [];
    const fieldErrors = {};
    if (data.errors) {
        if (Array.isArray(data.errors)) {
            for (const err of data.errors) {
                errorList.push(String(err));
            }
        } else if (typeof data.errors === 'object') {
            for (const key in data.errors) {
                if (!Object.prototype.hasOwnProperty.call(data.errors, key) || key === '_general') continue;
                const label = MARCAR_ERRORES[key] || key.charAt(0).toUpperCase() + key.slice(1);
                const msg = _trimPuntos(String(data.errors[key]));
                errorList.push(label + ': ' + msg);
                fieldErrors[key] = msg;
            }
        }
    }
    if (data.message && errorList.length === 0) {
        errorList.push(data.message);
    }
    return { errorList, fieldErrors };
}

function _mostrarErrorGuardar(form, modalEl, fieldErrors) {
    const hasFieldErrors = Object.keys(fieldErrors).some((k) => fieldErrors[k] !== undefined);
    if (hasFieldErrors) {
        marcarErroresForm(form, fieldErrors);
    } else {
        form.classList.add('was-validated');
    }
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal?.show();
    }
}

function _deshabilitarBoton(submitBtn) {
    if (!submitBtn) return null;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Guardando...';
    return submitBtn;
}

function _restaurarBoton(submitBtn) {
    if (!submitBtn) return;
    submitBtn.disabled = false;
    submitBtn.innerHTML = submitBtn.dataset.originalText || 'Guardar';
}

function _guardarOriginalText(form) {
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn && !submitBtn.dataset.originalText) {
        submitBtn.dataset.originalText = submitBtn.innerHTML;
    }
    return submitBtn;
}

function initModalFormAjax(formId, redirectUrl, validarFn) {
    const form = document.getElementById(formId);
    if (!form) return;

    const modalEl = form.closest('.modal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', () => limpiarErroresForm(form));
    }

    const submitBtn = _guardarOriginalText(form);

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        e.stopPropagation();

        limpiarErroresForm(form);

        if (typeof validarFn === 'function' && validarFn(form) === false) return;

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            _mostrarErroresYMarcar(form);
            return;
        }

        form.classList.add('was-validated');

        Swal.fire({
            icon: 'question',
            title: '¿Guardar cambios?',
            text: 'Los datos están completos y listos para guardarse.',
            showCancelButton: true,
            confirmButtonText: 'Sí, guardar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#198754',
            cancelButtonColor: '#6c757d',
        }).then((result) => {
            if (!result.isConfirmed) return;

            const btn = _deshabilitarBoton(submitBtn);
            const formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then((response) => response.json())
            .then((data) => {
                if (data.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Guardado',
                        text: data.message || 'Registro creado correctamente.',
                        confirmButtonColor: '#198754',
                    }).then(() => { globalThis.location.href = redirectUrl; });
                } else {
                    const { errorList, fieldErrors } = _procesarErrorRespuesta(data);
                    const promesa = mostrarErroresSwal(errorList.length ? errorList : ['Error al guardar.']);
                    if (promesa?.then) {
                        promesa.then(() => _mostrarErrorGuardar(form, modalEl, fieldErrors));
                    }
                }
            })
            .catch(() => {
                Swal.fire({
                    icon: 'error', title: 'Error de conexión',
                    text: 'No se pudo conectar con el servidor. Intenta de nuevo.',
                    confirmButtonColor: '#198754',
                });
            })
            .finally(() => _restaurarBoton(btn));
        });
    });

    _vincularValidacionEnVivo(form);
}

function setupEditModal(btnSelector, modalId, fieldMapping) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    for (const btn of document.querySelectorAll(btnSelector)) {
        btn.addEventListener('click', () => {
            limpiarErroresModal(modal);
            for (const fieldName in fieldMapping) {
                if (!Object.prototype.hasOwnProperty.call(fieldMapping, fieldName)) continue;
                const targetId = fieldMapping[fieldName];
                const target = document.getElementById(targetId);
                if (!target) continue;
                target.value = btn.dataset[fieldName] || '';
            }

            const actionUrl = btn.dataset.action;
            if (actionUrl && modal.querySelector('form')) {
                modal.querySelector('form').action = actionUrl;
            }
            bootstrap.Modal.getOrCreateInstance(modal)?.show();
        });
    }
}
