"""
Base Django settings for DraftCraft.
Shared configuration for development, staging, and production.

Security Note: Production settings in separate file.
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-development-only-change-in-production'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',  # Token authentication
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    'django_extensions',
]

LOCAL_APPS = [
    'core.apps.CoreConfig',
    'extraction.apps.ExtractionConfig',
    'documents.apps.DocumentsConfig',
    'proposals.apps.ProposalsConfig',
    'api.apps.ApiConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # Enable gzip compression for API responses
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',  # TEMPORARY: Disabled due to Python 3.14 gettext bug
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                # 'django.template.context_processors.i18n',  # TEMPORARY: Disabled due to Python 3.14 gettext bug
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database - Override in development.py and production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='draftcraft_dev'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'ATOMIC_REQUESTS': True,
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'de'  # Default language
TIME_ZONE = 'Europe/Berlin'
USE_I18N = False  # TEMPORARY: Disabled due to Python 3.14 gettext bug
USE_TZ = True

# Supported languages (disabled temporarily)
# LANGUAGES = [
#     ('de', 'Deutsch'),
#     ('en', 'English'),
# ]

# Locale paths for translation files (disabled temporarily)
# LOCALE_PATHS = [
#     os.path.join(BASE_DIR, 'locale'),
# ]

# German number formatting (when German is selected)
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'

# Format localization per language
FORMAT_MODULE_PATH = [
    'config.formats',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# REST Framework Configuration
# ============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'api.v1.throttling.AnonBurstRateThrottle',
        'api.v1.throttling.AnonSustainedRateThrottle',
        'api.v1.throttling.UserBurstRateThrottle',
        'api.v1.throttling.UserSustainedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon_burst': '10/min',         # Anonymous: 10 req/min burst
        'anon_sustained': '100/hour',   # Anonymous: 100 req/hour sustained
        'user_burst': '60/min',         # Authenticated: 60 req/min burst
        'user_sustained': '1000/hour',  # Authenticated: 1000 req/hour sustained
        'document_upload': '10/hour',   # Document uploads: 10/hour
        'auth': '5/min',                # Authentication: 5/min (brute-force protection)
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DATETIME_FORMAT': '%d.%m.%Y %H:%M:%S',
    'DATE_FORMAT': '%d.%m.%Y',
    'TIME_FORMAT': '%H:%M:%S',
}

# ============================================================================
# CORS Configuration
# ============================================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# Logging Configuration
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'extraction': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'documents': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'proposals': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    },
}

# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# ============================================================================
# Security Headers
# ============================================================================
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = False  # Enabled in production only
SESSION_COOKIE_SECURE = False  # Enabled in production only
CSRF_COOKIE_SECURE = False  # Enabled in production only

# ============================================================================
# Email Configuration
# ============================================================================
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default='587', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@draftcraft.de')

# ============================================================================
# Celery Configuration
# ============================================================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# ============================================================================
# Project-Specific Settings
# ============================================================================

# OCR Configuration (Phase 2)
OCR_MODEL = config('OCR_MODEL', default='de')  # German model
OCR_CONFIDENCE_THRESHOLD = config('OCR_CONFIDENCE_THRESHOLD', default='0.7', cast=float)

# NER Configuration (Phase 2)
NER_MODEL = 'de_core_news_lg'
NER_CONFIDENCE_THRESHOLD = config('NER_CONFIDENCE_THRESHOLD', default='0.6', cast=float)

# Processing Configuration
MAX_FILE_SIZE_MB = config('MAX_FILE_SIZE_MB', default='50', cast=int)
ALLOWED_DOCUMENT_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'docx', 'txt']

# Document Retention (DSGVO Art. 5 - Storage Limitation)
DOCUMENT_RETENTION_DAYS = config('DOCUMENT_RETENTION_DAYS', default='365', cast=int)

# Encryption
ENCRYPTION_ENABLED = config('ENCRYPTION_ENABLED', default=False, cast=bool)
ENCRYPTION_KEY = config('ENCRYPTION_KEY', default='')

# GCP Configuration (Phase 3)
GCP_PROJECT_ID = config('GCP_PROJECT_ID', default='')
GCP_CREDENTIALS = config('GCP_CREDENTIALS', default='')
GCS_BUCKET_NAME = config('GCS_BUCKET_NAME', default='draftcraft-documents')
CLOUD_TASKS_QUEUE = config('CLOUD_TASKS_QUEUE', default='document-processing')

# ============================================================================
# Agentic RAG Configuration (Phase 2 Enhancement)
# ============================================================================

# Gemini API Configuration
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GEMINI_MODEL = config('GEMINI_MODEL', default='gemini-1.5-flash')
USE_MOCK_GEMINI = config('USE_MOCK_GEMINI', default='False', cast=bool)

# Redis Cache Configuration (for short-term memory)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,  # Gracefully degrade if Redis unavailable
        },
        'TIMEOUT': 3600,  # 1 hour TTL for short-term memory
    }
}

# Agent Settings - Intelligent routing configuration
AGENT_SETTINGS = {
    'ALWAYS_ENABLED': True,  # Agent always integrated, routing decides usage
    'CONFIDENCE_THRESHOLDS': {
        'auto_accept': 0.92,      # Skip agent for high-confidence results
        'agent_verify': 0.80,     # Agent verifies borderline results
        'agent_extract': 0.70,    # Agent re-extracts low-confidence results
        'human_review': 0.0,      # Results below 70% marked for manual review
    },
    'FIELD_WEIGHTS': {
        'amount': 3.0,            # Critical financial field
        'date': 2.5,              # Important for context
        'gaeb_position': 2.5,     # Critical for construction docs
        'vendor_name': 2.0,
        'invoice_number': 2.0,
        'material': 1.5,          # Important for cost estimation
        'contact_person': 1.0,
        'notes': 0.5,
    },
    'COMPLEXITY_SCORING': {
        'low': {'agent_threshold': 0.75, 'max_tokens': 500},
        'medium': {'agent_threshold': 0.80, 'max_tokens': 1000},
        'high': {'agent_threshold': 0.70, 'max_tokens': 2000},
    },
    'CONTEXT_WINDOW': 5,  # Include 5 previous documents for context
    'MEMORY_RETENTION_HOURS': 24,  # Keep short-term patterns for 24 hours
}

# Gemini API Budget Configuration
GEMINI_BUDGET_CONFIG = {
    'DEFAULT_MONTHLY_USD': config('AGENT_MONTHLY_BUDGET_USD', default='50.00', cast=float),
    'ALERT_THRESHOLD_PERCENT': config('AGENT_ALERT_THRESHOLD_PERCENT', default='80', cast=int),
    'HARD_STOP_PERCENT': 100,  # Stop processing when 100% budget reached
    'ESTIMATE_TOKENS_PER_CALL': {
        'auto_accept': 0,        # No API call
        'agent_verify': 200,     # ~100 input, 100 output
        'agent_extract': 500,    # ~200 input, 300 output
        'human_review': 0,       # Flagged, no API call
    },
    'MODEL_PRICING': {
        'gemini-1.5-flash': {
            'input_per_1m_tokens': 0.075,
            'output_per_1m_tokens': 0.30,
        },
        'gemini-2-pro': {
            'input_per_1m_tokens': 0.15,
            'output_per_1m_tokens': 0.60,
        },
    },
    'RETRY_POLICY': {
        'max_retries': 3,
        'backoff_factor': 1.5,
        'timeout_seconds': 30,
    },
}

# Analytics
SENTRY_DSN = config('SENTRY_DSN', default='')

# ============================================================================
# DRF Spectacular - OpenAPI 3.0 Schema Generation (Phase 4D)
# ============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'DraftCraft API',
    'DESCRIPTION': 'German Handwerk Document Analysis System - REST API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'SERVE_AUTHENTICATION': ['rest_framework.authentication.TokenAuthentication'],
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    'PREPROCESSING_HOOKS': [],
    'POSTPROCESSING_HOOKS': [],
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Development server'},
        {'url': 'https://draftcraft.app', 'description': 'Production server'},
    ],
    'TAGS': [
        {'name': 'Pricing', 'description': 'Price calculation endpoints'},
        {'name': 'Configuration', 'description': 'Configuration management (TIER 1/2 factors)'},
        {'name': 'Pattern Analysis', 'description': 'Extraction failure pattern management'},
        {'name': 'Transparency', 'description': 'AI transparency and explanations'},
        {'name': 'Documents', 'description': 'Document upload and processing'},
        {'name': 'Proposals', 'description': 'Proposal generation'},
    ],
    'ENUM_NAME_OVERRIDES': {
        'CustomerType': 'api.v1.serializers.calculation_serializers.PriceCalculationRequestSerializer.customer_type',
    },
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'expandResponses': '200,201',
        'pathInMiddlePanel': True,
    },
}
