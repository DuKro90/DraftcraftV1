"""
Authentication URL Configuration for DraftCraft API
"""

from django.urls import path
from . import auth_views

app_name = 'auth'

urlpatterns = [
    # Token Authentication
    path('token/', auth_views.obtain_auth_token, name='token-obtain'),
    path('refresh/', auth_views.refresh_token, name='token-refresh'),
    path('verify/', auth_views.verify_token, name='token-verify'),
    path('logout/', auth_views.logout, name='logout'),

    # User Registration
    path('register/', auth_views.register_user, name='register'),

    # Password Reset
    path('password-reset/', auth_views.request_password_reset, name='password-reset'),
    path('password-reset/confirm/', auth_views.reset_password, name='password-reset-confirm'),
]
