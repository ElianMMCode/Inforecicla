// Helpers compartidos entre crear_usuario.js y editar_usuario.js.
// Se cargan como script clasico (sin type=module) y exponen funciones globales
// para compatibilidad con el HTML que ya invoca `mostrarErroresSwal`,
// `confirmarEnvioSwal`, etc.

const USUARIO_LIMITE_NOMBRES_MIN = 3;
const USUARIO_LIMITE_NOMBRES_MAX = 30;
const USUARIO_LIMITE_APELLIDOS_MIN = 3;
const USUARIO_LIMITE_APELLIDOS_MAX = 40;
const USUARIO_LIMITE_PASSWORD_MIN = 8;
const USUARIO_DOMINIOS_EMAIL_PERMITIDOS = [".com", ".co", ".edu.co", ".com.co", "soy.sena.edu.co", "sena.edu.co"];
const USUARIO_TIPOS_DOCUMENTO_VALIDOS = new Set(["CC", "TI", "CE", "PA", "NIT"]);
const USUARIO_TIPOS_USUARIO_VALIDOS = new Set(["ADM", "CIU", "GECA"]);
const USUARIO_ESTADOS_VALIDOS = new Set(["activo", "inactivo"]);
const USUARIO_COLOR_CONFIRMAR = "#198754";
const USUARIO_COLOR_CANCELAR = "#6c757d";
const USUARIO_PATTERN_NOMBRES = /^[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-']+$/;
const USUARIO_PATTERN_CELULAR = /^3\d{9}$/;
const USUARIO_PATTERN_DOCUMENTO = /^\d{6,20}$/;
const USUARIO_PATTERN_MINUSCULA = /[a-z]/;
const USUARIO_PATTERN_MAYUSCULA = /[A-Z]/;
const USUARIO_PATTERN_NUMERO = /\d/;
const USUARIO_PATTERN_ESPECIAL = /[@$!%*?&_]/;

const USUARIO_REQUISITOS_PASSWORD = [
    { id: "reqMinusculas", patron: USUARIO_PATTERN_MINUSCULA, texto: "Mínimo una letra minúscula (a-z)" },
    { id: "reqMayusculas", patron: USUARIO_PATTERN_MAYUSCULA, texto: "Mínimo una letra mayúscula (A-Z)" },
    { id: "reqNumeros", patron: USUARIO_PATTERN_NUMERO, texto: "Mínimo un número (0-9)" },
    { id: "reqEspeciales", patron: USUARIO_PATTERN_ESPECIAL, texto: "Mínimo un carácter especial (@$!%*?&_)" },
    { id: "reqLongitud", patron: null, textoBase: "Mínimo 8 caracteres" },
];

const RE_FECHA_DD = /^(\d{2})-(\d{2})-(\d{4})$/;
const RE_FECHA_ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function formatDateDDMMYYYY(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${day}-${month}-${year}`;
}

function parsearFechaNacimiento(valor) {
    if (!valor || String(valor).trim() === '') return null;
    const limpio = String(valor).trim();
    const matchDD = RE_FECHA_DD.exec(limpio);
    if (matchDD) return new Date(+matchDD[3], +matchDD[2] - 1, +matchDD[1]);
    const matchISO = RE_FECHA_ISO.exec(limpio);
    if (matchISO) return new Date(+matchISO[1], +matchISO[2] - 1, +matchISO[3]);
    return null;
}

function fechaEsValida(dateObj) {
    return dateObj instanceof Date && !Number.isNaN(dateObj.getTime());
}

function normalizarCaracteresFecha(campo) {
    if (!campo?.value) return;
    const normalizado = campo.value.replace(/[/\\.\s]+/g, '-');
    if (normalizado !== campo.value) {
        campo.value = normalizado;
    }
}

function normalizarFechaNacimientoInput(campo) {
    if (!campo?.value) return;
    normalizarCaracteresFecha(campo);
    const fecha = parsearFechaNacimiento(campo.value);
    if (fecha && fechaEsValida(fecha)) {
        campo.value = formatDate(fecha);
    }
}

function validarNormalizarFechaNacimiento(campo, edadMinima) {
    if (!campo) return true;
    normalizarCaracteresFecha(campo);
    const valor = String(campo.value || '').trim();
    if (!valor) {
        campo.setCustomValidity('');
        actualizarEstadoCampo(campo);
        return true;
    }
    const soloDigitosGuiones = /^[\d-]+$/.test(valor);
    if (!soloDigitosGuiones) {
        campo.setCustomValidity('Solo se permiten números y guiones.');
        actualizarEstadoCampo(campo);
        return false;
    }
    const fecha = parsearFechaNacimiento(valor);
    if (!fecha || !fechaEsValida(fecha)) {
        campo.setCustomValidity('Formato de fecha inválido. Usa DD-MM-AAAA o AAAA-MM-DD.');
        actualizarEstadoCampo(campo);
        return false;
    }
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    if (fecha > hoy) {
        campo.setCustomValidity('La fecha de nacimiento no puede ser futura.');
        actualizarEstadoCampo(campo);
        return false;
    }
    const edadMin = edadMinima || 18;
    let edad = hoy.getFullYear() - fecha.getFullYear();
    const m = hoy.getMonth() - fecha.getMonth();
    if (m < 0 || (m === 0 && hoy.getDate() < fecha.getDate())) edad--;
    if (edad < edadMin) {
        campo.setCustomValidity('Debes ser mayor de ' + edadMin + ' años.');
        actualizarEstadoCampo(campo);
        return false;
    }
    if (edad > 100) {
        campo.setCustomValidity('Edad no válida.');
        actualizarEstadoCampo(campo);
        return false;
    }
    campo.value = formatDateDDMMYYYY(fecha);
    campo.setCustomValidity('');
    actualizarEstadoCampo(campo);
    return true;
}

function actualizarEstadoCampo(campo) {
    if (!campo) {
        return;
    }
    const valido = campo.checkValidity();
    const tieneValor = String(campo.value || "").trim() !== "";
    const formEnviado = campo.form?.classList.contains("was-validated") ?? false;
    campo.classList.toggle("is-valid", valido && tieneValor);
    campo.classList.toggle("is-invalid", !valido && (tieneValor || (campo.required && formEnviado)));
}

function escaparHtml(texto) {
    return String(texto).replace(/[&<>"']/g, (caracter) => {
        const mapa = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        };
        return mapa[caracter] || caracter;
    });
}

function mostrarErroresSwal(errores) {
    if (typeof Swal === "undefined" || !errores || errores.length === 0) {
        return;
    }
    return Swal.fire({
        icon: "error",
        title: "Corrige los campos",
        html: '<div class="text-start">' +
            errores.map(function (e) { return escaparHtml(e); }).join(' ') +
            '</div>',
        confirmButtonColor: USUARIO_COLOR_CONFIRMAR,
    });
}

function normalizarSoloDigitos(campo) {
    if (!campo) {
        return;
    }
    const valor = campo.value;
    const soloDigitos = valor.replace(/\D/g, "");
    if (valor !== soloDigitos) {
        campo.value = soloDigitos;
    }
}

function validarCelular(celularInput) {
    if (!celularInput) {
        return true;
    }
    normalizarSoloDigitos(celularInput);
    const esValido = USUARIO_PATTERN_CELULAR.test(celularInput.value);
    celularInput.setCustomValidity(esValido ? "" : "El celular debe iniciar con 3 y tener 10 dígitos.");
    actualizarEstadoCampo(celularInput);
    return esValido;
}

function validarNumeroDocumento(numeroDocumentoInput) {
    if (!numeroDocumentoInput) {
        return true;
    }
    normalizarSoloDigitos(numeroDocumentoInput);
    if (!numeroDocumentoInput.value) {
        numeroDocumentoInput.setCustomValidity("");
        actualizarEstadoCampo(numeroDocumentoInput);
        return true;
    }
    const esValido = USUARIO_PATTERN_DOCUMENTO.test(numeroDocumentoInput.value);
    numeroDocumentoInput.setCustomValidity(
        esValido ? "" : "El número de documento debe tener entre 6 y 20 dígitos, sin letras ni caracteres especiales.",
    );
    actualizarEstadoCampo(numeroDocumentoInput);
    return esValido;
}

function validarLocalidad(localidadInput, mensajeVacio) {
    if (!localidadInput) {
        return true;
    }
    const tieneLocalidad = String(localidadInput.value || "").trim() !== "";
    localidadInput.setCustomValidity(tieneLocalidad ? "" : (mensajeVacio || "Selecciona una localidad."));
    actualizarEstadoCampo(localidadInput);
    return tieneLocalidad;
}

function validarFechaNacimiento(fechaInput, fechaMaxima) {
    if (!fechaInput) {
        return true;
    }
    if (!fechaInput.value) {
        fechaInput.setCustomValidity("");
        actualizarEstadoCampo(fechaInput);
        return true;
    }
    const cumple = fechaInput.value <= fechaMaxima;
    if (!cumple) {
        fechaInput.setCustomValidity("La fecha debe corresponder a un menor de edad.");
        actualizarEstadoCampo(fechaInput);
        return false;
    }
    fechaInput.setCustomValidity("");
    actualizarEstadoCampo(fechaInput);
    return true;
}

function validarFechaNacimientoRango(fechaInput, fechaMinima, fechaMaxima, mensajeInvalido) {
    if (!fechaInput) {
        return true;
    }
    const valor = String(fechaInput.value || "").trim();
    if (!valor) {
        fechaInput.setCustomValidity("");
        actualizarEstadoCampo(fechaInput);
        return true;
    }
    const fecha = new Date(`${valor}T00:00:00`);
    if (Number.isNaN(fecha.getTime())) {
        fechaInput.setCustomValidity("Formato de fecha inválido.");
        actualizarEstadoCampo(fechaInput);
        return false;
    }
    const esValida = fecha <= fechaMaxima && fecha >= fechaMinima;
    fechaInput.setCustomValidity(esValida ? "" : (mensajeInvalido || "La fecha está fuera del rango permitido."));
    actualizarEstadoCampo(fechaInput);
    return esValida;
}

function validarOpcionSeleccion(campo, valoresValidos, mensajeInvalido, { caseSensitive = true } = {}) {
    if (!campo) {
        return true;
    }
    const valorCrudo = String(campo.value || "").trim();
    const valor = caseSensitive ? valorCrudo : valorCrudo.toLowerCase();
    const conjunto = caseSensitive ? valoresValidos : new Set([...valoresValidos].map((v) => v.toLowerCase()));
    const permiteVacio = campo.tagName === "SELECT" || !campo.required;
    const esValido = (!valor && permiteVacio) || conjunto.has(valor);
    campo.setCustomValidity(esValido ? "" : mensajeInvalido);
    actualizarEstadoCampo(campo);
    return esValido;
}

function validarTexto(campo, minimo, maximo, patron, mensajeMinimo, mensajeMaximo, mensajePatron) {
    if (!campo) {
        return true;
    }
    const valor = campo.value.trim();
    if (!valor) {
        campo.setCustomValidity(campo.required ? "Este campo es obligatorio." : "");
        actualizarEstadoCampo(campo);
        return !campo.required;
    }
    if (valor.length < minimo) {
        campo.setCustomValidity(mensajeMinimo);
        actualizarEstadoCampo(campo);
        return false;
    }
    if (valor.length > maximo) {
        campo.setCustomValidity(mensajeMaximo);
        actualizarEstadoCampo(campo);
        return false;
    }
    if (patron && !patron.test(valor)) {
        campo.setCustomValidity(mensajePatron);
        actualizarEstadoCampo(campo);
        return false;
    }
    campo.setCustomValidity("");
    actualizarEstadoCampo(campo);
    return true;
}

function _obtenerEtiquetaCampo(campo) {
    const mapa = {
        nombres: 'Nombres',
        apellidos: 'Apellidos',
        celular: 'Celular',
        email: 'Correo electrónico',
        password: 'Contraseña', // NOSONAR - field label, not credential
        passwordConfirm: 'Confirmar contraseña',
        tipo_documento: 'Tipo de documento',
        numero_documento: 'Número de documento',
        ciudad: 'Ciudad',
        localidad: 'Localidad',
        tipo_usuario: 'Tipo de usuario',
        estado_usuario: 'Estado del usuario',
        fechaNacimiento: 'Fecha de nacimiento',
        fecha_nacimiento: 'Fecha de nacimiento',
    };
    return mapa[campo.name] || campo.name.charAt(0).toUpperCase() + campo.name.slice(1);
}

function _mensajePatternMismatch(campo, etiqueta) {
    if (campo.name === 'nombres' || campo.name === 'apellidos') return etiqueta + ': Solo se permiten letras, espacios, guiones o apóstrofes.';
    if (campo.name === 'celular') return etiqueta + ': Debe iniciar con 3 y tener exactamente 10 dígitos.';
    if (campo.name === 'fechaNacimiento' || campo.name === 'fecha_nacimiento') return etiqueta + ': Usa el formato DD-MM-AAAA o AAAA-MM-DD.';
    return etiqueta + ': El formato ingresado no es válido.';
}

function _mensajeValidacionES(campo) {
    const etiqueta = _obtenerEtiquetaCampo(campo);
    if (campo.validity.valid && !campo.validity.customError) return '';
    if (campo.validity.valueMissing) return etiqueta + ' es obligatorio.';
    if (campo.validity.patternMismatch) return _mensajePatternMismatch(campo, etiqueta);
    if (campo.validity.tooShort) return etiqueta + ': Debe tener al menos ' + campo.minLength + ' caracteres.';
    if (campo.validity.tooLong) return etiqueta + ': Debe tener máximo ' + campo.maxLength + ' caracteres.';
    if (campo.validity.typeMismatch) return etiqueta + ': El formato no es correcto.';
    if (campo.validity.rangeUnderflow || campo.validity.rangeOverflow) return etiqueta + ': El valor está fuera del rango permitido.';
    if (campo.validity.customError) return etiqueta + ': ' + campo.validationMessage;
    if (campo.validity.badInput) return etiqueta + ': El valor ingresado no es válido.';
    return etiqueta + ': El valor ingresado no es válido.';
}

function obtenerErroresFormulario(campos) {
    return Array.from(new Set(campos.map(function (campo) {
        const msg = _mensajeValidacionES(campo);
        return msg || null;
    }).filter(Boolean)));
}

function registrarValidacionCampo(campo, handler) {
    if (!campo) {
        return;
    }
    const eventName = campo.tagName === "SELECT" ? "change" : "input";
    campo.addEventListener(eventName, handler);
    campo.addEventListener("blur", () => actualizarEstadoCampo(campo));
}

function confirmarEnvioSwal(mensaje) {
    const configuracion = {
        icon: "question",
        title: mensaje.title || "¿Confirmar?",
        text: mensaje.text || "",
        showCancelButton: true,
        confirmButtonText: mensaje.confirmText || "Sí",
        cancelButtonText: "Cancelar",
        confirmButtonColor: USUARIO_COLOR_CONFIRMAR,
        cancelButtonColor: USUARIO_COLOR_CANCELAR,
    };
    if (typeof Swal === "undefined") {
        return Promise.resolve({ isConfirmed: globalThis.confirm(mensaje.text || mensaje.title) });
    }
    return Swal.fire(configuracion);
}

function initPasswordVisibilityToggle(selector = ".toggle-password-button") {
    document.querySelectorAll(selector).forEach((button) => {
        if (button.dataset.togglePasswordBound === "1") {
            return;
        }
        button.dataset.togglePasswordBound = "1";
        button.addEventListener("click", (evento) => {
            evento.preventDefault();
            const targetSelector = button.dataset.target || button.querySelector(".toggle-password")?.dataset.target;
            if (!targetSelector) {
                return;
            }
            const input = document.querySelector(targetSelector);
            if (!input) {
                return;
            }
            const esPassword = input.type === "password";
            input.type = esPassword ? "text" : "password";
            const icono = button.querySelector(".toggle-password") || button;
            icono.classList.toggle("bi-eye", !esPassword);
            icono.classList.toggle("bi-eye-slash", esPassword);
        });
    });
}

function limitarUnSoloArroba(valor) {
    const texto = String(valor || "");
    const primerArroba = texto.indexOf("@");
    if (primerArroba === -1) {
        return texto;
    }
    return texto.slice(0, primerArroba + 1) + texto.slice(primerArroba + 1).replaceAll("@", "");
}

function emailEsValido(email) {
    if (!email) {
        return true;
    }
    if (email.includes(" ")) {
        return false;
    }
    const cantidadArrobas = (email.match(/@/g) || []).length;
    if (cantidadArrobas !== 1) {
        return false;
    }
    const dominio = email.split("@").pop() || "";
    return USUARIO_DOMINIOS_EMAIL_PERMITIDOS.some((sufijo) => dominio.endsWith(sufijo));
}

function validarEmail(emailInput) {
    if (!emailInput) {
        return true;
    }
    const normalizado = limitarUnSoloArroba(emailInput.value.trim().toLowerCase());
    if (emailInput.value !== normalizado) {
        emailInput.value = normalizado;
    }
    if (!normalizado) {
        emailInput.setCustomValidity("");
        actualizarEstadoCampo(emailInput);
        return true;
    }
    const valido = emailEsValido(normalizado);
    emailInput.setCustomValidity(
        valido
            ? ""
            : "El correo electrónico debe tener un solo @, sin espacios, sin puntos consecutivos, y terminar en .com, .co, .edu.co, com.co, soy.sena.edu.co o sena.edu.co.",
    );
    actualizarEstadoCampo(emailInput);
    return valido;
}

function actualizarRequisito(elemento, cumple, texto) {
    if (!elemento) {
        return;
    }
    elemento.classList.toggle("text-success", cumple);
    elemento.classList.toggle("text-danger", !cumple);
    elemento.classList.toggle("fw-semibold", cumple);
    elemento.innerHTML = cumple
        ? `✅ <span class="text-success">${escaparHtml(texto)}</span>`
        : `❌ <span class="text-danger">${escaparHtml(texto)}</span>`;
}

function contrasenaCumpleReglas(valor = "") {
    return USUARIO_PATTERN_MINUSCULA.test(valor)
        && USUARIO_PATTERN_MAYUSCULA.test(valor)
        && USUARIO_PATTERN_NUMERO.test(valor)
        && USUARIO_PATTERN_ESPECIAL.test(valor)
        && valor.length >= USUARIO_LIMITE_PASSWORD_MIN;
}

function actualizarRequisitosPasswordUI(valor = "") {
    USUARIO_REQUISITOS_PASSWORD.forEach((requisito) => {
        const elemento = document.getElementById(requisito.id);
        if (!elemento) {
            return;
        }
        if (requisito.id === "reqLongitud") {
            const cumple = valor.length >= USUARIO_LIMITE_PASSWORD_MIN;
            let textoFinal = requisito.textoBase;
            if (!cumple && valor.length > 0) {
                textoFinal += ` (${valor.length}/${USUARIO_LIMITE_PASSWORD_MIN})`;
            }
            actualizarRequisito(elemento, cumple, textoFinal);
            return;
        }
        const cumple = requisito.patron.test(valor);
        actualizarRequisito(elemento, cumple, requisito.texto);
    });
}

function bindPasswordRealtime(passwordInput, passwordConfirmInput, mensajeCoincidencia) {
    if (!passwordInput || !passwordConfirmInput) {
        return;
    }
    const actualizar = () => {
        const password = passwordInput.value;
        const passwordConfirm = passwordConfirmInput.value;
        const cumpleTodo = contrasenaCumpleReglas(password);
        actualizarRequisitosPasswordUI(password);
        if (passwordConfirm.length === 0) {
            passwordConfirmInput.setCustomValidity("");
            if (mensajeCoincidencia) {
                mensajeCoincidencia.textContent = "";
            }
            actualizarEstadoCampo(passwordInput);
            actualizarEstadoCampo(passwordConfirmInput);
            return;
        }
        passwordInput.setCustomValidity(cumpleTodo ? "" : "La contraseña no cumple los requisitos.");
        if (password !== passwordConfirm) {
            passwordConfirmInput.setCustomValidity("Las contraseñas no coinciden.");
            if (mensajeCoincidencia) {
                mensajeCoincidencia.innerHTML = '<span class="text-danger">✗ No coinciden</span>';
            }
            actualizarEstadoCampo(passwordInput);
            actualizarEstadoCampo(passwordConfirmInput);
            return;
        }
        passwordConfirmInput.setCustomValidity("");
        if (mensajeCoincidencia) {
            mensajeCoincidencia.innerHTML = '<span class="text-success">✓ Coinciden</span>';
        }
        actualizarEstadoCampo(passwordInput);
        actualizarEstadoCampo(passwordConfirmInput);
    };
    passwordInput.addEventListener("input", actualizar);
    passwordConfirmInput.addEventListener("input", actualizar);
    actualizar();
}

function bindSubmitUsuario({ formulario, camposValidacion, confirmar, antesDeEnviar }) {
    formulario.addEventListener("submit", (evento) => {
        evento.preventDefault();
        evento.stopPropagation();
        if (typeof antesDeEnviar === "function") {
            const resultado = antesDeEnviar(formulario);
            if (resultado === false) {
                return;
            }
        }
        if (!formulario.checkValidity()) {
            formulario.classList.add("was-validated");
            const promesa = mostrarErroresSwal(obtenerErroresFormulario(camposValidacion));
            if (promesa?.then) {
                promesa.then(function () {
                    camposValidacion.forEach(function (c) {
                        if (c && !c.checkValidity()) c.classList.add("is-invalid");
                    });
                });
            }
            return;
        }
        formulario.classList.add("was-validated");
        confirmarEnvioSwal(confirmar).then((resultado) => {
            if (resultado.isConfirmed) {
                formulario.submit();
            }
        });
    });
}
