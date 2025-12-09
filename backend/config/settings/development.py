"""
Development settings for DraftCraft.
Extends base.py with development-specific overrides.
"""

from .base import *  # noqa

# Development: Enable debug mode
DEBUG = True
ALLOWED_HOSTS = ['*']

# Development database: SQLite by default (PostgreSQL optional)
import os
from decouple import config

db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')

if db_engine == 'django.db.backends.sqlite3':
    # SQLite for local development (no external DB needed)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    # PostgreSQL for production-like testing
    db_host = config('DB_HOST', default='localhost')
    is_supabase = 'supabase.co' in db_host

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='draftcraft_dev'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': db_host,
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
        }
    }

    # Add SSL for Supabase connections
    if is_supabase:
        DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

# Development email: Log to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS: Allow all in development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
    'http://localhost:5173',          # Vite dev server
    'http://localhost:5174',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:5174',
    'https://draftcraft-v1.vercel.app',  # Vercel Production (for testing)
]

# Enable Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Celery: Use eager mode (execute immediately)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Logging: More verbose in development
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'

# File storage: Local filesystem
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# REST Framework: More verbose responses
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Disable HSTS in development
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_SSL_REDIRECT = False

# Allow insecure cookies in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

print('[OK] Using DEVELOPMENT settings')
