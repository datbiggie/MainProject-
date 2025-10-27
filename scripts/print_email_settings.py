#!/usr/bin/env python3
"""Print Django email-related settings (loads Django)."""
import os
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
try:
    import django
    django.setup()
    from django.conf import settings
except Exception as e:
    print('Error loading Django settings:', e)
    sys.exit(2)

def main():
    keys = [
        'EMAIL_BACKEND', 'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER',
        'EMAIL_USE_TLS', 'EMAIL_USE_SSL', 'DEFAULT_FROM_EMAIL'
    ]
    for k in keys:
        print(f"{k} = {getattr(settings, k, None)}")

if __name__ == '__main__':
    main()
