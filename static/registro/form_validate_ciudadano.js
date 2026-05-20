(function() {
    'use strict';
    window.addEventListener('load', function() {
        const forms = document.querySelectorAll('form');
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', function(event) {
                const password = document.getElementById('password').value;
                const passwordConfirm = document.getElementById('passwordConfirm').value;

                if (password !== passwordConfirm) {
                    event.preventDefault();
                    event.stopPropagation();
                    alert('Las contraseñas no coinciden');
                    return;
                }

                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }

                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();

