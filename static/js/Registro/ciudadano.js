// ciudadano.js
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("citizenForm");
    const pass = document.getElementById("password");
    const pass2 = document.getElementById("password_confirm");
    const alertBox = document.getElementById("formAlert");

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        event.stopPropagation();

        // Reset alertas
        alertBox.className = "alert d-none";
        alertBox.textContent = "";

        // Validar contraseñas coinciden
        if (pass.value !== pass2.value) {
            pass2.setCustomValidity("No coincide");
        } else {
            pass2.setCustomValidity("");
        }

        form.classList.add("was-validated");

        if (!form.checkValidity()) {
            return; // Hay campos inválidos
        }

        // Construcción de datos del formulario
        const data = {
            email: document.getElementById("email").value.trim(),
            password: pass.value,
            first_name: document.getElementById("first_name").value.trim(),
            last_name: document.getElementById("last_name").value.trim(),
            display_name: document.getElementById("display_name").value.trim(),
            phone: document.getElementById("phone").value.trim(),
            document_type: document.getElementById("document_type").value,
            document_number: document.getElementById("document_number").value.trim(),
            birthdate: document.getElementById("birthdate").value,
            address: document.getElementById("address").value.trim(),
            gender: (document.querySelector('input[name="gender"]:checked') || {}).value || null,
            receive_notifications: document.getElementById("receive_notifications").checked ? 1 : 0
        };

        // Simulación: mostrar datos en consola
        console.log("Datos de registro ciudadano:", data);

        // Mostrar alerta de éxito
        alertBox.className = "alert alert-success";
        alertBox.textContent = "Registro completado exitosamente. Redirigiendo...";

        // Reset del formulario visual
        form.reset();
        form.classList.remove("was-validated");

        // Redirección después de 2 segundos
        setTimeout(() => {
            window.location.href = "/ciudadano";
        }, 1000);
    });
});
