# Casos de Prueba - CU-01/06: Registrar Cuenta en Plataforma

## Introducción

Este documento detalla los casos de prueba diseñados para validar los flujos
establecidos para el caso de uso CU-01/06: Registrar Cuenta en Plataforma.

---

## Casos de Prueba

| ID del Test                    | TC-CU01.1-01: Validar Formato de Datos                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| **Descripción / Objetivo**     | Verificar que el serializador valide correctamente campos obligatorios y formatos (nombre, apellido, email). |
| **Precondiciones**             | El sistema debe estar operativo y aceptar peticiones POST.                                                   |
| **Pasos de Ejecución**         | 1. Enviar petición de registro con campos de nombre o apellido vacíos. 2. Enviar email con formato inválido. |
| **Datos de Prueba**            | `first_name=""`, `last_name="Pérez"`, `email="correo-invalido"`                                              |
| **Resultado Esperado**         | Código HTTP 400 Bad Request. El sistema devuelve errores específicos por cada campo mal formado.             |
| **Módulo de Django a Testear** | `users/serializers.py`                                                                                       |

| ID del Test                    | TC-CU01.2-01: Aceptar Términos y Condiciones                                               |
| ------------------------------ | ------------------------------------------------------------------------------------------ |
| **Descripción / Objetivo**     | Validar que el registro falle si el usuario no marca la casilla de aceptación de términos. |
| **Precondiciones**             | Datos de usuario válidos.                                                                  |
| **Pasos de Ejecución**         | 1. Enviar petición de registro con `acepta_terminos=False`.                                |
| **Datos de Prueba**            | `acepta_terminos=False`                                                                    |
| **Resultado Esperado**         | El registro es rechazado. Error: "Debe aceptar los términos y condiciones para continuar". |
| **Módulo de Django a Testear** | `users/serializers.py` o `users/views.py`                                                  |

| ID del Test                    | TC-CU01.3-01: Verificar Disponibilidad de Correo                                            |
| ------------------------------ | ------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Comprobar que el sistema impida el registro con un email que ya existe en PostgreSQL.       |
| **Precondiciones**             | Existe un usuario registrado con el email `test@inforecicla.com`.                           |
| **Pasos de Ejecución**         | 1. Intentar registrar un nuevo usuario con el mismo email.                                  |
| **Datos de Prueba**            | `email="test@inforecicla.com"`                                                              |
| **Resultado Esperado**         | Código HTTP 400. Error: "Este correo electrónico ya está registrado". (Vinculado a EXT-01). |
| **Módulo de Django a Testear** | `users/serializers.py`                                                                      |

| ID del Test                    | TC-CU01.4-01: Validar Fortaleza de Contraseña                                                                          |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Verificar que se apliquen los validadores de complejidad de Django.                                                    |
| **Precondiciones**             | Configuración de `AUTH_PASSWORD_VALIDATORS` activa.                                                                    |
| **Pasos de Ejecución**         | 1. Intentar registro con contraseña de 4 caracteres. 2. Intentar con contraseña puramente numérica.                    |
| **Datos de Prueba**            | `password="1234"` o `password="12345678"`                                                                              |
| **Resultado Esperado**         | El sistema rechaza la contraseña. Error: "La contraseña es demasiado corta" o "demasiado común". (Vinculado a EXT-02). |
| **Módulo de Django a Testear** | `users/serializers.py`                                                                                                 |

| ID del Test                    | TC-CU01.5-01: Enviar Enlace de Activación                                                                                               |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar la generación del token UID/Token y el disparo del correo de bienvenida.                                                        |
| **Precondiciones**             | Datos de registro válidos. Backend de correo configurado (o consola para pruebas).                                                      |
| **Pasos de Ejecución**         | 1. Completar el registro exitosamente. 2. Revisar la cola de correos salientes.                                                         |
| **Datos de Prueba**            | Datos de usuario nuevos y válidos.                                                                                                      |
| **Resultado Esperado**         | Código HTTP 201 Created. Se genera un registro de usuario inactivo (`is_active=False`) y se envía el email con el enlace de activación. |
| **Módulo de Django a Testear** | `users/views.py`, `users/utils.py`                                                                                                      |

| ID del Test                    | TC-EXT01-01: Notificar Error - Correo Duplicado                                         |
| ------------------------------ | --------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar que la respuesta de error para email duplicado sea clara para el usuario final. |
| **Precondiciones**             | El email ya existe.                                                                     |
| **Pasos de Ejecución**         | Ejecutar flujo de registro duplicado.                                                   |
| **Datos de Prueba**            | `email="repetido@inforecicla.com"`                                                      |
| **Resultado Esperado**         | JSON de respuesta indicando específicamente el conflicto en el campo 'email'.           |
| **Módulo de Django a Testear** | `users/serializers.py`                                                                  |

| ID del Test                    | TC-EXT02-01: Notificar Error - Contraseña Débil                                               |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| **Descripción / Objetivo**     | Validar la retroalimentación detallada cuando la contraseña no cumple criterios de seguridad. |
| **Precondiciones**             | Validadores de Django activos.                                                                |
| **Pasos de Ejecución**         | Ingresar contraseña que solo contiene letras minúsculas.                                      |
| **Datos de Prueba**            | `password="sololetras"`                                                                       |
| **Resultado Esperado**         | Respuesta con los criterios de seguridad no cumplidos (longitud, mezcla de caracteres, etc.). |
| **Módulo de Django a Testear** | `users/serializers.py`                                                                        |

---

## Notas finales

Estos casos de prueba están diseñados para garantizar el cumplimiento de las
reglas de negocio y la precisión de los cálculos asociados al registro de
cuentas en InfoRecicla. Asegúrese de preparar los datos iniciales correctamente
antes de su ejecución.

