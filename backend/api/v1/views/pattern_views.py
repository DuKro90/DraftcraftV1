"""
Pattern Analysis API Views - Phase 4D

API endpoints for extraction failure pattern management and approval workflow.
"""
import logging
from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from api.v1.serializers.pattern_serializers import (
    PatternFailureSerializer,
    PatternDetailSerializer,
    PatternFixApprovalSerializer,
    PatternBulkActionSerializer,
)
from api.v1.permissions import CanManagePatterns, IsAdminUser
from documents.pattern_models import (
    ExtractionFailurePattern,
    PatternReviewSession,
)

logger = logging.getLogger(__name__)


class PatternFailureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Extraction failure pattern management.

    GET /api/v1/patterns/failures/
    GET /api/v1/patterns/failures/{id}/

    Users can view their own patterns.
    Admins can view all patterns.
    """

    permission_classes = [IsAuthenticated, CanManagePatterns]

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'retrieve':
            return PatternDetailSerializer
        return PatternFailureSerializer

    def get_queryset(self):
        """Get patterns for current user or all if admin."""
        queryset = ExtractionFailurePattern.objects.select_related(
            'user', 'reviewed_by'
        ).prefetch_related('review_sessions')

        # Filter by user unless admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        # Apply filters
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        is_reviewed = self.request.query_params.get('is_reviewed')
        if is_reviewed is not None:
            queryset = queryset.filter(is_reviewed=is_reviewed.lower() == 'true')

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        field_name = self.request.query_params.get('field_name')
        if field_name:
            queryset = queryset.filter(field_name__icontains=field_name)

        return queryset.order_by('-severity', '-affected_document_count')

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='severity',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)',
                required=False,
            ),
            OpenApiParameter(
                name='is_reviewed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by review status',
                required=False,
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status',
                required=False,
            ),
            OpenApiParameter(
                name='field_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by field name (partial match)',
                required=False,
            ),
        ],
        summary="List extraction failure patterns",
        description="Get extraction failure patterns with optional filters",
        tags=['Pattern Analysis'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get pattern details",
        description="Get detailed pattern information including review sessions",
        tags=['Pattern Analysis'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PatternApprovalView(views.APIView):
    """
    Approve pattern fix for deployment.

    POST /api/v1/patterns/{pattern_id}/approve-fix/
    {
        "review_title": "Fix low-confidence amount extraction",
        "description": "Apply regex pattern for German currency formats",
        "estimated_impact": "high",
        "estimated_documents_improved": 45,
        "scheduled_deployment": "2025-12-15T10:00:00Z"
    }

    Admin-only endpoint.
    Creates a PatternReviewSession with status 'approved'.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        request=PatternFixApprovalSerializer,
        responses={201: OpenApiTypes.OBJECT},
        summary="Approve pattern fix",
        description="Approve a pattern fix for deployment (admin only)",
        tags=['Pattern Analysis'],
    )
    def post(self, request, pattern_id):
        """Approve pattern fix."""
        # Validate request
        serializer = PatternFixApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Get pattern
            pattern = ExtractionFailurePattern.objects.get(id=pattern_id)

            # Check permission (must be admin or own the pattern)
            if not request.user.is_staff and pattern.user != request.user:
                return Response(
                    {
                        'detail': 'Sie haben keine Berechtigung für diese Aktion.',
                        'error_code': 'permission_denied'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create review session
            review_session = PatternReviewSession.objects.create(
                pattern=pattern,
                admin_user=request.user,
                status='approved',
                title=serializer.validated_data['review_title'],
                description=serializer.validated_data['description'],
                estimated_impact=serializer.validated_data['estimated_impact'],
                estimated_documents_improved=serializer.validated_data['estimated_documents_improved'],
                scheduled_deployment=serializer.validated_data.get('scheduled_deployment'),
                reviewed_cases_count=pattern.total_occurrences,
                approved_cases=pattern.total_occurrences,
            )

            # Update pattern
            pattern.is_reviewed = True
            pattern.reviewed_at = timezone.now()
            pattern.reviewed_by = request.user

            if serializer.validated_data.get('admin_notes'):
                pattern.admin_notes = serializer.validated_data['admin_notes']

            pattern.save()

            # Log approval
            logger.info(
                f"Pattern {pattern_id} approved by user {request.user.id}: "
                f"Review session {review_session.id} created"
            )

            return Response(
                {
                    'success': True,
                    'message': 'Pattern-Fix erfolgreich genehmigt.',
                    'pattern_id': str(pattern.id),
                    'review_session_id': str(review_session.id),
                    'status': review_session.status,
                    'scheduled_deployment': review_session.scheduled_deployment,
                },
                status=status.HTTP_201_CREATED
            )

        except ExtractionFailurePattern.DoesNotExist:
            return Response(
                {
                    'detail': f'Pattern nicht gefunden: {pattern_id}',
                    'error_code': 'pattern_not_found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.exception(f"Error approving pattern {pattern_id}")
            return Response(
                {
                    'detail': f'Fehler bei der Genehmigung: {str(e)}',
                    'error_code': 'approval_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatternBulkActionView(views.APIView):
    """
    Perform bulk actions on patterns.

    POST /api/v1/patterns/bulk-action/
    {
        "pattern_ids": ["uuid1", "uuid2", "uuid3"],
        "action": "mark_reviewed",
        "admin_notes": "Reviewed and approved for deployment"
    }

    Admin-only endpoint.
    Supported actions:
    - mark_reviewed: Mark patterns as reviewed
    - mark_inactive: Deactivate patterns
    - mark_active: Activate patterns
    - set_severity: Update severity level
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        request=PatternBulkActionSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Perform bulk action on patterns",
        description="Perform bulk actions on multiple patterns (admin only)",
        tags=['Pattern Analysis'],
    )
    def post(self, request):
        """Perform bulk action."""
        serializer = PatternBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pattern_ids = serializer.validated_data['pattern_ids']
        action = serializer.validated_data['action']
        severity = serializer.validated_data.get('severity')
        admin_notes = serializer.validated_data.get('admin_notes', '')

        try:
            # Get patterns
            patterns = ExtractionFailurePattern.objects.filter(id__in=pattern_ids)
            found_count = patterns.count()

            if found_count == 0:
                return Response(
                    {
                        'detail': 'Keine Patterns gefunden mit den angegebenen IDs.',
                        'error_code': 'no_patterns_found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Perform action
            updated_count = 0

            if action == 'mark_reviewed':
                patterns.update(
                    is_reviewed=True,
                    reviewed_at=timezone.now(),
                    reviewed_by=request.user,
                    admin_notes=admin_notes
                )
                updated_count = found_count

            elif action == 'mark_inactive':
                patterns.update(
                    is_active=False,
                    admin_notes=admin_notes
                )
                updated_count = found_count

            elif action == 'mark_active':
                patterns.update(
                    is_active=True,
                    admin_notes=admin_notes
                )
                updated_count = found_count

            elif action == 'set_severity':
                patterns.update(
                    severity=severity,
                    admin_notes=admin_notes
                )
                updated_count = found_count

            # Log bulk action
            logger.info(
                f"Bulk action '{action}' performed by user {request.user.id}: "
                f"{updated_count} patterns updated"
            )

            return Response(
                {
                    'success': True,
                    'message': f'{updated_count} Patterns erfolgreich aktualisiert.',
                    'action': action,
                    'updated_count': updated_count,
                    'requested_count': len(pattern_ids),
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception(f"Error performing bulk action '{action}'")
            return Response(
                {
                    'detail': f'Fehler bei Bulk-Aktion: {str(e)}',
                    'error_code': 'bulk_action_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
