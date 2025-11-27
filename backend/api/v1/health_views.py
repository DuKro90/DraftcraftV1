"""
Enhanced Health Check Endpoints for Cloud Run

Provides multiple health check endpoints for different Cloud Run probe types:
- /health/ - Basic liveness probe (always returns 200 OK if service is running)
- /health/ready/ - Readiness probe (checks database, cache, critical services)
- /health/startup/ - Startup probe (validates all services are initialized)
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Basic liveness probe - returns 200 if service is running.

    Cloud Run uses this to determine if the container should be restarted.
    Should be fast (<10 seconds) and only check if the process is alive.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'draftcraft',
        'environment': getattr(settings, 'ENVIRONMENT', 'unknown')
    })


def health_ready(request):
    """
    Readiness probe - checks if service can handle traffic.

    Cloud Run uses this to determine if traffic should be routed to this instance.
    Checks critical dependencies: database, cache.
    """
    checks = {
        'database': False,
        'cache': False,
    }

    errors = []

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = True
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
        logger.error(f"Health check database error: {e}")

    # Check cache connectivity
    try:
        cache_key = '__health_check__'
        cache.set(cache_key, 'ok', 10)
        cache_value = cache.get(cache_key)
        if cache_value == 'ok':
            checks['cache'] = True
            cache.delete(cache_key)
        else:
            errors.append("Cache read/write verification failed")
    except Exception as e:
        errors.append(f"Cache error: {str(e)}")
        logger.error(f"Health check cache error: {e}")

    # Service is ready only if all critical checks pass
    all_healthy = checks['database'] and checks['cache']

    response_data = {
        'status': 'ready' if all_healthy else 'not_ready',
        'checks': checks,
    }

    if errors:
        response_data['errors'] = errors

    status_code = 200 if all_healthy else 503
    return JsonResponse(response_data, status=status_code)


def health_startup(request):
    """
    Startup probe - checks if service has completed initialization.

    Cloud Run uses this during container startup to determine when the service
    is ready to receive traffic for the first time. More thorough than readiness.
    """
    checks = {
        'database': False,
        'cache': False,
        'migrations': False,
        'settings': False,
    }

    errors = []

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = True
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
        logger.error(f"Startup check database error: {e}")

    # Check cache connectivity
    try:
        cache_key = '__startup_check__'
        cache.set(cache_key, 'ok', 10)
        cache_value = cache.get(cache_key)
        if cache_value == 'ok':
            checks['cache'] = True
            cache.delete(cache_key)
        else:
            errors.append("Cache verification failed")
    except Exception as e:
        errors.append(f"Cache error: {str(e)}")
        logger.error(f"Startup check cache error: {e}")

    # Check database migrations are applied
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        checks['migrations'] = len(plan) == 0  # True if no pending migrations
        if plan:
            errors.append(f"Pending migrations: {len(plan)}")
    except Exception as e:
        errors.append(f"Migration check error: {str(e)}")
        logger.error(f"Startup check migrations error: {e}")

    # Check critical settings
    try:
        required_settings = ['SECRET_KEY', 'DATABASES']
        for setting_name in required_settings:
            if not hasattr(settings, setting_name):
                errors.append(f"Missing setting: {setting_name}")
            elif setting_name == 'SECRET_KEY' and settings.SECRET_KEY == 'insecure-dev-key':
                errors.append("Using insecure SECRET_KEY in production")

        checks['settings'] = len([e for e in errors if 'setting' in e.lower()]) == 0
    except Exception as e:
        errors.append(f"Settings check error: {str(e)}")
        logger.error(f"Startup check settings error: {e}")

    # Service is started only if all checks pass
    all_healthy = all(checks.values())

    response_data = {
        'status': 'started' if all_healthy else 'starting',
        'checks': checks,
    }

    if errors:
        response_data['errors'] = errors
        response_data['advice'] = 'Check logs for detailed error messages'

    status_code = 200 if all_healthy else 503
    return JsonResponse(response_data, status=status_code)
