"""
API v1 Permissions - Phase 4D

Custom permissions for DraftCraft API.
Ensures users can only access their own resources and admins have full control.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to view/edit it.

    Assumes the model instance has a `user` field.
    Compatible with RLS (Row-Level Security) policies.
    """

    message = 'Sie müssen der Eigentümer dieser Ressource sein.'

    def has_object_permission(self, request, view, obj):
        """Check if user owns this object."""
        # Allow if user is admin
        if request.user and request.user.is_staff:
            return True

        # Check if object has user field
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if object has user_id field
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id

        # For documents, check via document relation
        if hasattr(obj, 'document') and hasattr(obj.document, 'user'):
            return obj.document.user == request.user

        # Default deny
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read access to everyone but write only to owner.
    """

    message = 'Sie müssen der Eigentümer sein, um diese Ressource zu bearbeiten.'

    def has_object_permission(self, request, view, obj):
        """Allow read to all, write to owner only."""
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only to owner
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users.

    Used for:
    - Pattern approval endpoints
    - Configuration management
    - Bulk operations
    """

    message = 'Nur Administratoren haben Zugriff auf diese Ressource.'

    def has_permission(self, request, view):
        """Check if user is admin."""
        return request.user and request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read access to authenticated users,
    but write access only to admins.
    """

    message = 'Nur Administratoren können diese Ressource bearbeiten.'

    def has_permission(self, request, view):
        """Allow read to authenticated, write to admin."""
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_staff


class CanAccessDocument(permissions.BasePermission):
    """
    Permission to check if user can access a specific document.

    Used for document-related endpoints.
    Ensures DSGVO compliance - users can only see their own documents.
    """

    message = 'Sie haben keinen Zugriff auf dieses Dokument.'

    def has_permission(self, request, view):
        """Check authenticated for list views."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check ownership for detail views."""
        # Admin can access all
        if request.user.is_staff:
            return True

        # User must own the document
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # For related objects (ExtractionResult, etc.)
        if hasattr(obj, 'document'):
            return obj.document.user == request.user

        return False


class CanManagePatterns(permissions.BasePermission):
    """
    Permission for pattern management operations.

    - Users can view their own patterns
    - Only admins can approve fixes or perform bulk actions
    """

    message = 'Sie haben keine Berechtigung für diese Pattern-Aktion.'

    def has_permission(self, request, view):
        """Check base permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Read access for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write access only for admins
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        # Admins can do anything
        if request.user.is_staff:
            return True

        # Users can view their own patterns
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'user'):
                return obj.user == request.user

        # Write operations only for admins
        return False


class CanModifyConfiguration(permissions.BasePermission):
    """
    Permission for configuration modification.

    - All authenticated users can view config
    - Only admins can modify global config (TIER 1)
    - Users can modify their own Betriebskennzahl (TIER 2)
    """

    message = 'Sie haben keine Berechtigung, diese Konfiguration zu ändern.'

    def has_permission(self, request, view):
        """Check base permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Read access for all authenticated
        if request.method in permissions.SAFE_METHODS:
            return True

        # Determine what's being modified
        # This is handled in views - here we just check authentication
        return True  # View will enforce specific rules

    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        # Read access for authenticated
        if request.method in permissions.SAFE_METHODS:
            return True

        # For IndividuelleBetriebskennzahl, allow user to modify their own
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff

        # For global config (TIER 1), only admins
        return request.user.is_staff


class HasActiveBetriebskennzahl(permissions.BasePermission):
    """
    Permission to check if user has active Betriebskennzahl configuration.

    Required for calculation endpoints - user must be properly configured.
    """

    message = 'Sie müssen zuerst Ihre Betriebskennzahlen konfigurieren.'

    def has_permission(self, request, view):
        """Check if user has active config."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins bypass this check
        if request.user.is_staff:
            return True

        # Check if user has active Betriebskennzahl
        from documents.betriebskennzahl_models import IndividuelleBetriebskennzahl

        try:
            config = IndividuelleBetriebskennzahl.objects.get(user=request.user)
            return config.is_active
        except IndividuelleBetriebskennzahl.DoesNotExist:
            return False


class RateLimitExempt(permissions.BasePermission):
    """
    Permission for rate limit exemption.

    Admins and trusted users can be exempted from rate limits.
    """

    def has_permission(self, request, view):
        """Check if user is exempt from rate limits."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins are exempt
        if request.user.is_staff:
            return True

        # Check if user has rate_limit_exempt flag (custom user model)
        if hasattr(request.user, 'rate_limit_exempt'):
            return request.user.rate_limit_exempt

        return False
