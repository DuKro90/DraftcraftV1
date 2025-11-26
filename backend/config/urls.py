"""
Main URL configuration for DraftCraft.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Authentication
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),

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
