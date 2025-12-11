"""
Production settings for DraftCraft.
Extends base.py with production-specific hardening.
Sensitive values come from environment variables.
"""

from .base import *  # noqa
import os
import logging

# Validate environment variables before loading settings
from .validators import validate_production_environment
try:
    validate_production_environment()
except Exception as e:
    # Log and re-raise - fail fast if critical vars missing
    logging.error(f"Environment validation failed: {e}")
    raise

# Production: Disable debug
DEBUG = False

# Required in production
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError(
        'SECRET_KEY environment variable not set. '
        'Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    )

# Cloud SQL for PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': os.environ.get('DB_SSLMODE', 'allow'),  # Changed from 'disable' to 'allow' for local dev compatibility
        }
    }
}

# Email: Use SendGrid or similar
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
EMAIL_USE_TLS = True

# CORS: Restrict to frontend domain
# Vercel Frontend + Cloud Run Backend
CORS_ALLOWED_ORIGINS = [
    'https://draftcraft-v1.vercel.app',        # Vercel Production
]

# Use regex for Vercel preview deployments (wildcards not supported in CORS_ALLOWED_ORIGINS)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://draftcraft-v1-[a-zA-Z0-9-]+\.vercel\.app$',  # Vercel Preview Deploys
    r'^https://[a-zA-Z0-9-]+\.run\.app$',                    # Cloud Run
]

# Allow environment variable override for custom domains
if os.environ.get('CORS_ALLOWED_ORIGINS'):
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS').split(',')
if os.environ.get('CORS_ALLOWED_ORIGIN_REGEXES'):
    CORS_ALLOWED_ORIGIN_REGEXES = os.environ.get('CORS_ALLOWED_ORIGIN_REGEXES').split(',')

# CORS Additional Settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Celery: Use Redis in production
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TASK_ALWAYS_EAGER = False

# File storage: Cloud Storage (GCS)
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud_storage.GoogleCloudStorage'
GS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME')
GS_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# Security headers: STRICT (only in actual production)
if os.environ.get('SECURE_COOKIES', '').lower() == 'true':
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Static files: Serve from CDN
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Disable admin for security (use API instead)
# ADMIN_URL is randomly generated in production

# Logging: Cloud Run uses stdout/stderr (disable file logging)
# Remove file handler for Cloud Run (no persistent disk, permission issues)
if 'file' in LOGGING['handlers']:
    del LOGGING['handlers']['file']

# Update all loggers to use only console
for logger_name in LOGGING['loggers']:
    if 'file' in LOGGING['loggers'][logger_name].get('handlers', []):
        LOGGING['loggers'][logger_name]['handlers'] = ['console']

# Update root logger
if 'file' in LOGGING['root'].get('handlers', []):
    LOGGING['root']['handlers'] = ['console']

# Try Cloud Logging integration (optional)
try:
    import google.cloud.logging
    LOGGING['handlers']['cloud_logging'] = {
        'level': 'INFO',
        'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
    }
    # Use cloud logging if available
    LOGGING['root']['handlers'].append('cloud_logging')
except ImportError:
    # Fall back to console logging only
    pass

# Sentry: Error tracking
if os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        environment='production'
    )

# Encryption: Enable encryption for sensitive fields
ENCRYPTION_ENABLED = True
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

# Document retention: Strict DSGVO compliance
DOCUMENT_RETENTION_DAYS = 365

print('✅ Using PRODUCTION settings')
