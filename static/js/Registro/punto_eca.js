// js/Registro/puntoECA.js
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ecaForm");
    const alertBox = document.getElementById("formAlert");

    // Campos de cuenta
    const pass = document.getElementById("password");
    const pass2 = document.getElementById("password_confirm");

    // Geolocalización
    const geoBtn = document.getElementById("geoBtn");
    const locationDisplay = document.getElementById("locationDisplay");
    const latInput = document.getElementById("lat");
    const lngInput = document.getElementById("lng");

    // Archivos / opcionales
    const logoInput = document.getElementById("logo");

    // Utilidad: mostrar alertas
    function showAlert(type, msg) {
        alertBox.className = `alert alert-${type}`;
        alertBox.textContent = msg;
    }

    // Validar archivo (opcional)
    function validateLogo() {
        if (!logoInput || !logoInput.files || logoInput.files.length === 0) return true;
        const file = logoInput.files[0];
        const validTypes = ["image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"];
        const maxSizeMB = 2;
        if (!validTypes.includes(file.type)) {
            showAlert("danger", "El logo debe ser una imagen (png, jpg, webp, gif, svg).");
            logoInput.value = "";
            return false;
        }
        if (file.size > maxSizeMB * 1024 * 1024) {
            showAlert("danger", `El logo no puede superar ${maxSizeMB} MB.`);
            logoInput.value = "";
            return false;
        }
        return true;
    }

    if (logoInput) {
        logoInput.addEventListener("change", validateLogo);
    }

    // Botón de geolocalización
    if (geoBtn) {
        geoBtn.addEventListener("click", () => {
            if (!("geolocation" in navigator)) {
                showAlert("warning", "Tu navegador no soporta geolocalización.");
                return;
            }
            locationDisplay.textContent = "Obteniendo ubicación…";
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const { latitude, longitude } = pos.coords;
                    latInput.value = latitude.toString();
                    lngInput.value = longitude.toString();
                    locationDisplay.textContent = `Ubicación capturada: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
                    showAlert("success", "Ubicación cargada correctamente.");
                },
                (err) => {
                    const map = {
                        1: "Permiso denegado para obtener la ubicación.",
                        2: "Posición no disponible.",
                        3: "Tiempo de espera agotado al obtener la ubicación."
                    };
                    showAlert("warning", map[err.code] || "No fue posible obtener la ubicación.");
                    locationDisplay.textContent = "No se pudo obtener la ubicación.";
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        });
    }

    // Envío del formulario
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        e.stopPropagation();

        // Reset de alertas
        alertBox.className = "alert d-none";
        alertBox.textContent = "";

        // Validar contraseñas
        if (pass.value !== pass2.value) {
            pass2.setCustomValidity("No coincide");
        } else {
            pass2.setCustomValidity("");
        }

        // Validar archivo (si se cargó)
        if (!validateLogo()) {
            form.classList.add("was-validated");
            return;
        }

        // Activar validación Bootstrap
        form.classList.add("was-validated");
        if (!form.checkValidity()) return;

        // Construcción de FormData para soportar archivos
        const fd = new FormData(form);

        // Normalizar checkboxes a 0/1 (por si tu backend lo prefiere así)
        fd.set("show_on_map", document.getElementById("show_on_map").checked ? "1" : "0");
        const notif = document.getElementById("receive_notifications");
        if (notif) fd.set("receive_notifications", notif.checked ? "1" : "0");

        // Puedes revisar lo que se va a enviar:
        // for (let [k, v] of fd.entries()) console.log(k, v);

        // ======= EJEMPLO de integración con API (descomenta y adapta) =======
        // try {
        //   // 1) Crear usuario base + rol eca_manager (según account_type)
        //   const r1 = await fetch("/api/auth/register", {
        //     method: "POST",
        //     body: fd // si tu endpoint de register NO espera archivos, envía JSON en su lugar
        //   });
        //   if (!r1.ok) throw new Error("No se pudo crear la cuenta del gestor.");
        //   const { user_id, token } = await r1.json();
        //
        //   // 2) Crear punto ECA (con token del paso 1)
        //   // Si tu API de puntos NO acepta multipart, crea un nuevo FormData o JSON solo con los campos del ECA.
        //   const fdEca = new FormData();
        //   fdEca.set("eca_name", fd.get("eca_name"));
        //   fdEca.set("nit", fd.get("nit") || "");
        //   fdEca.set("opening_hours", fd.get("opening_hours") || "");
        //   fdEca.set("contact_email", fd.get("contact_email"));
        //   fdEca.set("contact_phone", fd.get("contact_phone"));
        //   fdEca.set("address", fd.get("address"));
        //   fdEca.set("city", fd.get("city"));
        //   fdEca.set("locality", fd.get("locality"));
        //   fdEca.set("lat", fd.get("lat") || "");
        //   fdEca.set("lng", fd.get("lng") || "");
        //   fdEca.set("website", fd.get("website") || "");
        //   if (logoInput && logoInput.files[0]) fdEca.set("logo", logoInput.files[0]);
        //   fdEca.set("show_on_map", fd.get("show_on_map")); // "0" o "1"
        //   fdEca.set("receive_notifications", fd.get("receive_notifications")); // "0" o "1"
        //
        //   const r2 = await fetch("/api/eca/points", {
        //     method: "POST",
        //     headers: { Authorization: `Bearer ${token}` },
        //     body: fdEca
        //   });
        //   if (!r2.ok) throw new Error("No se pudo registrar el Punto ECA.");
        //
        //   showAlert("success", "Punto ECA registrado correctamente. Redirigiendo…");
        //   setTimeout(() => (window.location.href = "gestor.html"), 1500);
        //   return;
        // } catch (err) {
        //   showAlert("danger", err.message || "Ocurrió un error al registrar el punto.");
        //   return;
        // }
        // ======= FIN EJEMPLO =======

        // Simulación si aún no tienes backend:
        showAlert("success", "Formulario válido. (Simulación) Aquí se enviaría a tu API. Redirigiendo…");
        setTimeout(() => (window.location.href = "/punto_eca"), 1500);
    });
});
