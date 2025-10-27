# Proyecto Django

Este es un proyecto Django con las siguientes características:

## Requisitos


## Instalación

1. Crear un entorno virtual:
```bash
python -m venv .venv
```

2. Activar el entorno virtual:
```bash
.venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecutar las migraciones:
```bash
python manage.py migrate
```

5. Iniciar el servidor:
```bash
python manage.py runserver
```

## Email / Password reset configuration

This project can send real emails (for password recovery) through SMTP. Do NOT commit credentials. Set the following environment variables in your deployment or local environment before running the server:

- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_HOST_USER=your@gmail.com
- EMAIL_HOST_PASSWORD=your_app_password_here
- EMAIL_USE_TLS=True
- DEFAULT_FROM_EMAIL=Your Site <no-reply@yourdomain.com>

When testing locally you can use Django's console backend (recommended) so the app
does not attempt to connect to an SMTP server and emails are printed to the
console instead:

- EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

If you want to test sending real emails locally, you can run a local SMTP debug
server (only for development) and point EMAIL_HOST/EMAIL_PORT to it. For
example, in a separate terminal run:

```powershell
# Start a local SMTP debug server that prints received emails to stdout (Python 3)
python -m smtpd -n -c DebuggingServer localhost:1025;
# Then set EMAIL_HOST=localhost and EMAIL_PORT=1025
```

Helper scripts
--------------
Two small scripts were added under `scripts/` to help debug email configuration:

- `scripts/print_email_settings.py` — prints the Django email settings that the project sees (useful to confirm environment variables are loaded).
- `scripts/test_smtp.py` — sends a test email to a recipient using the configured backend.

Example (PowerShell):

```powershell
# set environment variables in this session
$env:EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
$env:EMAIL_HOST='smtp.gmail.com'
$env:EMAIL_PORT='587'
$env:EMAIL_HOST_USER='tu@gmail.com'
$env:EMAIL_HOST_PASSWORD='TU_APP_PASSWORD'
$env:EMAIL_USE_TLS='True'
$env:DEFAULT_FROM_EMAIL='Mi Sitio <no-reply@tudominio.com>'

# confirm settings
python scripts/print_email_settings.py

# send a test mail
python scripts/test_smtp.py tu@correo.com
```

The views use `django.core.signing` to generate a time-limited token (2 hours). The password reset flow expects the frontend to call `/ecommerce/api/request_password_reset/` with JSON `{ "email": "..." }` and will send an email with a link to `/ecommerce/confirmar_recuperacion/?token=...`.

## Estructura del Proyecto

- `manage.py`: Script principal de Django
- `requirements.txt`: Lista de dependencias
- `ecommerce_app/`: Aplicación principal del proyecto
