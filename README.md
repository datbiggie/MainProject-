# Proyecto Django

Este es un proyecto Django con las siguientes características:

## Requisitos

- Python 3.13 o superior
- MySQL

## Instalación

1. Crear un entorno virtual:
```bash
python -m venv .venv
```

2. Activar el entorno virtual:
- Windows:
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

## Estructura del Proyecto

- `manage.py`: Script principal de Django
- `requirements.txt`: Lista de dependencias
- `ecommerce_app/`: Aplicación principal del proyecto
