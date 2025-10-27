#!/usr/bin/env python3
"""Send a test email using Django's configured email backend.

Usage: set environment variables (EMAIL_BACKEND, EMAIL_HOST, etc.) then run:
    python scripts/test_smtp.py recipient@example.com
"""
import os
import sys

if len(sys.argv) < 2:
    print('Usage: python scripts/test_smtp.py recipient@example.com')
    sys.exit(1)

recipient = sys.argv[1]

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')

try:
    import django
    django.setup()
    from django.core.mail import send_mail
except Exception as e:
    print('Error loading Django:', e)
    sys.exit(2)

subject = 'SMTP test'
message = 'This is a test message from scripts/test_smtp.py'
from_email = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@example.com')

try:
    result = send_mail(subject, message, from_email, [recipient], fail_silently=False)
    print('send_mail result:', result)
except Exception as e:
    print('Error sending mail:', e)
    sys.exit(3)
