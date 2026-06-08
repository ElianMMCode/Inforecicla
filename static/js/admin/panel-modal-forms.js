function _validarCampo(campo) {
    var valido = campo.checkValidity() && campo.value.trim() !== '';
    if (campo.hasAttribute('data-letters-required') && campo.value.trim() !== '') {
        var tieneLetra = /[A-Za-zÁÉÍÓÚáéíóúñÑüÜ]/.test(campo.value);
        if (!tieneLetra) valido = false;
    }
    return valido;
}

function _mensajeValidacionES(campo) {
    if (campo.validity.valid && !campo.validity.customError) return '';
    var etiqueta = MARCAR_ERRORES[campo.name] || campo.name.charAt(0).toUpperCase() + campo.name.slice(1);
    if (campo.validity.valueMissing) return etiqueta + ' es obligatorio.';
    if (campo.validity.patternMismatch) {
        if (campo.name === 'nombres' || campo.name === 'apellidos') return etiqueta + ': Solo se permiten letras, espacios, guiones o apóstrofes.';
        if (campo.name === 'celular') return etiqueta + ': Debe iniciar con 3 y tener exactamente 10 dígitos.';
        if (campo.name === 'fechaNacimiento' || campo.name === 'fecha_nacimiento') return etiqueta + ': Usa el formato DD-MM-AAAA o AAAA-MM-DD.';
        return etiqueta + ': El formato ingresado no es válido.';
    }
    if (campo.validity.tooShort) return etiqueta + ': Debe tener al menos ' + campo.minLength + ' caracteres.';
    if (campo.validity.tooLong) return etiqueta + ': Debe tener máximo ' + campo.maxLength + ' caracteres.';
    if (campo.validity.typeMismatch) return etiqueta + ': El formato no es correcto.';
    if (campo.validity.rangeUnderflow || campo.validity.rangeOverflow) return etiqueta + ': El valor está fuera del rango permitido.';
    if (campo.validity.customError) return etiqueta + ': ' + campo.validationMessage;
    if (campo.validity.badInput) return etiqueta + ': El valor ingresado no es válido.';
    return etiqueta + ': El valor ingresado no es válido.';
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

function initModalForm(formId, validarFn) {
    var form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        e.stopPropagation();

        if (typeof validarFn === 'function') {
            if (!validarFn(form)) {
                form.classList.add('was-validated');
                var errores = [];
                var invalidFields = [];
                var campos = form.querySelectorAll('[required], [pattern], [minlength]');
                for (var i = 0; i < campos.length; i++) {
                    if (!campos[i].checkValidity()) {
                        var msg = _mensajeValidacionES(campos[i]);
                        if (msg) {
                            errores.push(msg);
                            invalidFields.push({ field: campos[i], msg: msg });
                        }
                    }
                }
                var prom = mostrarErroresSwal(errores);
                if (prom && prom.then) {
                    (function (inv) {
                        prom.then(function () {
                            for (var j = 0; j < inv.length; j++) {
                                var item = inv[j];
                                item.field.classList.add('is-invalid');
                                var contenedor = item.field.closest('.col-12, .col-md-6, .col-md-12, .mb-3');
                                if (contenedor) {
                                    var fb = contenedor.querySelector('.invalid-feedback');
                                    if (fb) fb.textContent = item.msg;
                                }
                            }
                        });
                    })(invalidFields);
                }
                return;
            }
        }

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            var errores2 = [];
            var invalidFields2 = [];
            var campos2 = form.querySelectorAll('[required], [pattern], [minlength]');
            for (var i = 0; i < campos2.length; i++) {
                if (!campos2[i].checkValidity()) {
                    var msg2 = _mensajeValidacionES(campos2[i]);
                    if (msg2) {
                        errores2.push(msg2);
                        invalidFields2.push({ field: campos2[i], msg: msg2 });
                    }
                }
            }
            var prom2 = mostrarErroresSwal(errores2);
            if (prom2 && prom2.then) {
                (function (inv) {
                    prom2.then(function () {
                        for (var j = 0; j < inv.length; j++) {
                            var item = inv[j];
                            item.field.classList.add('is-invalid');
                            var contenedor = item.field.closest('.col-12, .col-md-6, .col-md-12, .mb-3');
                            if (contenedor) {
                                var fb = contenedor.querySelector('.invalid-feedback');
                                if (fb) fb.textContent = item.msg;
                            }
                        }
                    });
                })(invalidFields2);
            }
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
        }).then(function (result) {
            if (result.isConfirmed) {
                form.submit();
            }
        });
    });

    form.addEventListener('invalid', function (e) { e.preventDefault(); }, true);

    var campos = form.querySelectorAll('input, select, textarea');
    for (var i = 0; i < campos.length; i++) {
        (function (campo) {
            var eventName = campo.tagName === 'SELECT' ? 'change' : 'input';
            campo.addEventListener(eventName, function () {
                var valido = _validarCampo(campo);
                campo.classList.toggle('is-valid', valido);
                campo.classList.toggle('is-invalid', !valido && (campo.value.trim() !== '' || campo.required));
            });
            campo.addEventListener('blur', function () {
                var valido = _validarCampo(campo);
                campo.classList.toggle('is-valid', valido);
                campo.classList.toggle('is-invalid', !valido && (campo.value.trim() !== '' || campo.required));
            });
        })(campos[i]);
    }
}

var MARCAR_ERRORES = {
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
    password: 'Contraseña',
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
    var invalidos = form.querySelectorAll('.is-invalid');
    for (var i = 0; i < invalidos.length; i++) {
        invalidos[i].classList.remove('is-invalid');
    }
    var valids = form.querySelectorAll('.is-valid');
    for (var i = 0; i < valids.length; i++) {
        valids[i].classList.remove('is-valid');
    }
    form.classList.remove('was-validated');
}

function limpiarErroresModal(modalEl) {
    if (!modalEl) return;
    var forms = modalEl.querySelectorAll('form');
    for (var i = 0; i < forms.length; i++) {
        limpiarErroresForm(forms[i]);
    }
}

function marcarErroresForm(form, fieldErrors) {
    if (!form || !fieldErrors) return;
    for (var key in fieldErrors) {
        if (!fieldErrors.hasOwnProperty(key) || key === '_general') continue;
        var field = form.querySelector('[name="' + key + '"]');
        if (!field) continue;
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        var contenedor = field.closest('.col-12, .col-md-6, .col-md-12, .mb-3');
        if (contenedor) {
            var feedback = contenedor.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.textContent = fieldErrors[key].replace(/^[\.\s]+/, '').replace(/[\.\s]+$/, '');
            }
        }
    }
    form.classList.remove('was-validated');
}

function initModalFormAjax(formId, redirectUrl, validarFn) {
    var form = document.getElementById(formId);
    if (!form) return;

    var modalEl = form.closest('.modal');
    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', function () {
            limpiarErroresForm(form);
        });
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        e.stopPropagation();

        limpiarErroresForm(form);

        if (typeof validarFn === 'function') {
            var customResult = validarFn(form);
            if (customResult === false) return;
        }

        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            var errores = [];
            var invalidFields = [];
            var campos = form.querySelectorAll('[required], [pattern], [minlength]');
            for (var i = 0; i < campos.length; i++) {
                if (!campos[i].checkValidity()) {
                    var msg = _mensajeValidacionES(campos[i]);
                    if (msg) {
                        errores.push(msg);
                        invalidFields.push({ field: campos[i], msg: msg });
                    }
                }
            }
            var prom = mostrarErroresSwal(errores);
            if (prom && prom.then) {
                (function (inv) {
                    prom.then(function () {
                        for (var j = 0; j < inv.length; j++) {
                            var item = inv[j];
                            item.field.classList.add('is-invalid');
                            var contenedor = item.field.closest('.col-12, .col-md-6, .col-md-12, .mb-3');
                            if (contenedor) {
                                var fb = contenedor.querySelector('.invalid-feedback');
                                if (fb) fb.textContent = item.msg;
                            }
                        }
                    });
                })(invalidFields);
            }
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
        }).then(function (result) {
            if (!result.isConfirmed) return;

            var submitBtn = form.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Guardando...';
            }

            var formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Guardado',
                        text: data.message || 'Registro creado correctamente.',
                        confirmButtonColor: '#198754',
                    }).then(function () {
                        window.location.href = redirectUrl;
                    });
                } else {
                    var errorList = [];
                    var fieldErrors = {};
                    if (data.errors) {
                        if (Array.isArray(data.errors)) {
                            for (var ei = 0; ei < data.errors.length; ei++) {
                                errorList.push(String(data.errors[ei]));
                            }
                        } else if (typeof data.errors === 'object') {
                            for (var key in data.errors) {
                                if (!data.errors.hasOwnProperty(key) || key === '_general') continue;
                                var label = MARCAR_ERRORES[key] || key.charAt(0).toUpperCase() + key.slice(1);
                                var msg = String(data.errors[key]).replace(/^[\.\s]+/, '').replace(/[\.\s]+$/, '');
                                errorList.push(label + ': ' + msg);
                                fieldErrors[key] = msg;
                            }
                        }
                    }
                    if (data.message && errorList.length === 0) {
                        errorList.push(data.message);
                    }

                    var promesa = mostrarErroresSwal(errorList.length ? errorList : ['Error al guardar.']);
                    if (promesa && promesa.then) {
                        promesa.then(function () {
                            if (!form) return;
                            var hasFieldErrors = false;
                            for (var k in fieldErrors) { if (fieldErrors.hasOwnProperty(k)) { hasFieldErrors = true; break; } }
                            if (hasFieldErrors) {
                                marcarErroresForm(form, fieldErrors);
                            } else {
                                form.classList.add('was-validated');
                            }
                            if (modalEl) {
                                var modal = bootstrap.Modal.getInstance(modalEl);
                                if (modal) modal.show();
                            }
                        });
                    }
                }
            })
            .catch(function () {
                Swal.fire({
                    icon: 'error',
                    title: 'Error de conexión',
                    text: 'No se pudo conectar con el servidor. Intenta de nuevo.',
                    confirmButtonColor: '#198754',
                });
            })
            .finally(function () {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Guardar';
                }
            });
        });
    });

    var submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn && !submitBtn.getAttribute('data-original-text')) {
        submitBtn.setAttribute('data-original-text', submitBtn.innerHTML);
    }

    form.addEventListener('invalid', function (e) { e.preventDefault(); }, true);

    var campos = form.querySelectorAll('input, select, textarea');
    for (var i = 0; i < campos.length; i++) {
        (function (campo) {
            var eventName = campo.tagName === 'SELECT' ? 'change' : 'input';
            campo.addEventListener(eventName, function () {
                var valido = _validarCampo(campo);
                campo.classList.toggle('is-valid', valido);
                campo.classList.toggle('is-invalid', !valido && (campo.value.trim() !== '' || campo.required));
            });
            campo.addEventListener('blur', function () {
                var valido = _validarCampo(campo);
                campo.classList.toggle('is-valid', valido);
                campo.classList.toggle('is-invalid', !valido && (campo.value.trim() !== '' || campo.required));
            });
        })(campos[i]);
    }
}

function setupEditModal(btnSelector, modalId, fieldMapping) {
    var modal = document.getElementById(modalId);
    if (!modal) return;

    var buttons = document.querySelectorAll(btnSelector);
    for (var i = 0; i < buttons.length; i++) {
        (function (btn) {
            btn.addEventListener('click', function (e) {
                limpiarErroresModal(modal);
                for (var fieldName in fieldMapping) {
                    if (!fieldMapping.hasOwnProperty(fieldName)) continue;
                    var targetId = fieldMapping[fieldName];
                    var target = document.getElementById(targetId);
                    if (!target) continue;
                    var valor = btn.getAttribute('data-' + fieldName) || '';
                    target.value = valor;
                }

                var actionUrl = btn.getAttribute('data-action');
                if (actionUrl && modal.querySelector('form')) {
                    modal.querySelector('form').action = actionUrl;
                }
                var modalInstance = bootstrap.Modal.getOrCreateInstance(modal);
                if (modalInstance) modalInstance.show();
            });
        })(buttons[i]);
    }
}
