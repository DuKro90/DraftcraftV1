"""
Main URL configuration for DraftCraft.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

from rest_framework.authtoken.views import obtain_auth_token
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """Root health check for Docker healthcheck."""
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    # Docker Health Check (root level for container healthcheck)
    path('health/', health_check, name='health'),

    # Language switching
    path('i18n/', include('django.conf.urls.i18n')),

    # Admin
    path('admin/', admin.site.urls),

    # API Authentication (Extended with Token Refresh, Registration, etc.)
    path('api/auth/', include('api.v1.auth_urls', namespace='auth')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # App URLs
    path('api/v1/', include('api.v1.urls', namespace='api-v1')),
]

# Health Check endpoints are provided by api/v1/health/ocr/ endpoint
# See: api.v1.views.HealthCheckViewSet

# Debug toolbar in development
try:
    from django.conf import settings
    if settings.DEBUG:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
except ImportError:
    pass
