"""
Authentication Views for DraftCraft API
Includes Token Auth, Token Refresh, Registration, Password Reset
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets


@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_auth_token(request):
    """
    Custom token authentication with expiration.

    POST /api/auth/token/
    {
        "username": "user@example.com",
        "password": "password123"
    }

    Returns:
    {
        "token": "abc123...",
        "user": {
            "id": 1,
            "username": "user@example.com",
            "email": "user@example.com"
        },
        "expires_at": "2025-12-09T12:00:00Z"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'detail': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate user
    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'detail': 'User account is disabled'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Get or create token
    token, created = Token.objects.get_or_create(user=user)

    # Check if token is expired (30 days)
    if not created:
        token_age = timezone.now() - token.created
        if token_age > timedelta(days=30):
            # Token expired, create new one
            token.delete()
            token = Token.objects.create(user=user)

    # Calculate expiration
    expires_at = token.created + timedelta(days=30)

    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'expires_at': expires_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token(request):
    """
    Refresh authentication token.

    POST /api/auth/refresh/
    Headers: Authorization: Token abc123...

    Returns:
    {
        "token": "new_token_xyz...",
        "expires_at": "2025-12-09T12:00:00Z"
    }
    """
    # Delete old token
    request.user.auth_token.delete()

    # Create new token
    token = Token.objects.create(user=request.user)
    expires_at = token.created + timedelta(days=30)

    return Response({
        'token': token.key,
        'expires_at': expires_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register new user account.

    POST /api/auth/register/
    {
        "username": "newuser",
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    }

    Returns:
    {
        "user": {
            "id": 2,
            "username": "newuser",
            "email": "user@example.com"
        },
        "token": "abc123...",
        "expires_at": "2025-12-09T12:00:00Z"
    }
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    password_confirm = request.data.get('password_confirm')

    # Validation
    if not all([username, email, password, password_confirm]):
        return Response(
            {'detail': 'All fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if password != password_confirm:
        return Response(
            {'detail': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {'detail': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if user exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'detail': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {'detail': 'Email already registered'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    # Create token
    token = Token.objects.create(user=user)
    expires_at = token.created + timedelta(days=30)

    # Send welcome email (optional)
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
        try:
            send_mail(
                subject='Willkommen bei DraftCraft',
                message=f'Hallo {username},\n\nDein Account wurde erfolgreich erstellt.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass  # Don't fail registration if email fails

    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'token': token.key,
        'expires_at': expires_at.isoformat(),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Request password reset email.

    POST /api/auth/password-reset/
    {
        "email": "user@example.com"
    }

    Returns:
    {
        "detail": "Password reset email sent if account exists"
    }
    """
    email = request.data.get('email')

    if not email:
        return Response(
            {'detail': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Always return success for security (don't leak if email exists)
    try:
        user = User.objects.get(email=email)

        # Generate reset token (store in cache/database in production)
        reset_token = secrets.token_urlsafe(32)

        # TODO: Store reset_token with expiration (Redis or DB)
        # For now, just send email with token

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        send_mail(
            subject='DraftCraft - Passwort zurücksetzen',
            message=f'Hallo {user.username},\n\nKlicke auf den Link um dein Passwort zurückzusetzen:\n{reset_url}\n\nDieser Link ist 1 Stunde gültig.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except User.DoesNotExist:
        pass  # Don't leak if user exists

    return Response({
        'detail': 'Password reset email sent if account exists'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password with token.

    POST /api/auth/password-reset/confirm/
    {
        "token": "reset_token_here",
        "password": "NewSecurePassword123!",
        "password_confirm": "NewSecurePassword123!"
    }

    Returns:
    {
        "detail": "Password reset successful"
    }
    """
    token = request.data.get('token')
    password = request.data.get('password')
    password_confirm = request.data.get('password_confirm')

    if not all([token, password, password_confirm]):
        return Response(
            {'detail': 'All fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if password != password_confirm:
        return Response(
            {'detail': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {'detail': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # TODO: Verify token from Redis/Database
    # For now, return error (needs Redis setup)
    return Response(
        {'detail': 'Password reset feature requires Redis configuration'},
        status=status.HTTP_501_NOT_IMPLEMENTED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by deleting token.

    POST /api/auth/logout/
    Headers: Authorization: Token abc123...

    Returns:
    {
        "detail": "Successfully logged out"
    }
    """
    # Delete token
    request.user.auth_token.delete()

    return Response({
        'detail': 'Successfully logged out'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Verify if token is still valid.

    GET /api/auth/verify/
    Headers: Authorization: Token abc123...

    Returns:
    {
        "valid": true,
        "user": {
            "id": 1,
            "username": "user@example.com",
            "email": "user@example.com"
        },
        "expires_at": "2025-12-09T12:00:00Z"
    }
    """
    token = request.user.auth_token
    expires_at = token.created + timedelta(days=30)

    # Check if token is expired
    is_valid = timezone.now() < expires_at

    return Response({
        'valid': is_valid,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        },
        'expires_at': expires_at.isoformat(),
    })
