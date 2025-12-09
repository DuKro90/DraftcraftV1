"""
Admin Dashboard API Views - Phase 4D Step 3

Provides aggregate statistics and metrics for the admin dashboard.
Admin-only endpoints for operational monitoring.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from documents.models import Document, ExtractionResult
from documents.pattern_models import ExtractionFailurePattern
from documents.betriebskennzahl_models import IndividuelleBetriebskennzahl

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Get dashboard statistics",
    description="Get aggregate statistics for admin dashboard (admin only)",
    tags=['Admin Dashboard'],
    responses={
        200: OpenApiResponse(
            description="Dashboard statistics",
            response={
                'type': 'object',
                'properties': {
                    'total_documents': {'type': 'integer', 'description': 'Total documents in system'},
                    'processed_today': {'type': 'integer', 'description': 'Documents processed today'},
                    'active_patterns': {'type': 'integer', 'description': 'Active failure patterns'},
                    'critical_patterns': {'type': 'integer', 'description': 'Critical severity patterns'},
                    'avg_confidence': {'type': 'number', 'description': 'Average extraction confidence'},
                    'total_users': {'type': 'integer', 'description': 'Total active users'},
                    'documents_last_7_days': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'date': {'type': 'string'},
                                'count': {'type': 'integer'}
                            }
                        }
                    },
                    'pattern_severity_breakdown': {
                        'type': 'object',
                        'properties': {
                            'CRITICAL': {'type': 'integer'},
                            'HIGH': {'type': 'integer'},
                            'MEDIUM': {'type': 'integer'},
                            'LOW': {'type': 'integer'}
                        }
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    """
    Get comprehensive dashboard statistics.

    Admin-only endpoint providing:
    - Document processing statistics
    - Pattern analysis metrics
    - User activity data
    - 7-day trend data
    """
    try:
        today = timezone.now().date()

        # Document statistics
        total_documents = Document.objects.count()
        processed_today = Document.objects.filter(
            status='completed',
            created_at__date=today
        ).count()

        # Pattern statistics
        active_patterns = ExtractionFailurePattern.objects.filter(
            is_active=True
        ).count()

        critical_patterns = ExtractionFailurePattern.objects.filter(
            is_active=True,
            severity='CRITICAL'
        ).count()

        # Pattern severity breakdown
        pattern_breakdown = ExtractionFailurePattern.objects.filter(
            is_active=True
        ).values('severity').annotate(count=Count('id'))

        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        for item in pattern_breakdown:
            severity_counts[item['severity']] = item['count']

        # Average confidence (from recent extractions)
        avg_confidence_data = ExtractionResult.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).aggregate(
            avg_conf=Avg('confidence_scores__overall')
        )
        avg_confidence = avg_confidence_data.get('avg_conf') or 0.0

        # User statistics
        total_users = IndividuelleBetriebskennzahl.objects.filter(
            is_active=True
        ).count()

        # Last 7 days document trend
        documents_last_7_days = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = Document.objects.filter(
                created_at__date=date
            ).count()
            documents_last_7_days.append({
                'date': date.strftime('%Y-%m-%d'),
                'day': date.strftime('%a'),  # Mon, Tue, etc.
                'count': count
            })

        response_data = {
            'total_documents': total_documents,
            'processed_today': processed_today,
            'active_patterns': active_patterns,
            'critical_patterns': critical_patterns,
            'avg_confidence': round(avg_confidence, 3) if avg_confidence else 0.0,
            'total_users': total_users,
            'documents_last_7_days': documents_last_7_days,
            'pattern_severity_breakdown': severity_counts,
            'timestamp': timezone.now().isoformat()
        }

        logger.info(f"Dashboard stats requested by admin user {request.user.id}")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Error generating dashboard stats: {e}")
        return Response(
            {
                'detail': 'Fehler beim Abrufen der Dashboard-Statistiken',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get recent activity",
    description="Get recent system activity for admin dashboard",
    tags=['Admin Dashboard'],
    responses={
        200: OpenApiResponse(
            description="Recent activity items",
            response={
                'type': 'object',
                'properties': {
                    'activities': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'type': {'type': 'string'},
                                'title': {'type': 'string'},
                                'description': {'type': 'string'},
                                'timestamp': {'type': 'string'},
                                'severity': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def recent_activity(request):
    """
    Get recent system activity.

    Returns mixed activity feed from:
    - Recent document uploads
    - New patterns detected
    - Critical errors
    """
    try:
        activities = []

        # Recent document uploads (last 24 hours)
        recent_docs = Document.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24),
            status='completed'
        ).order_by('-created_at')[:10]

        for doc in recent_docs:
            activities.append({
                'type': 'document_processed',
                'title': 'Dokument erfolgreich verarbeitet',
                'description': doc.original_filename,
                'timestamp': doc.created_at.isoformat(),
                'severity': 'success',
                'icon': 'check-circle'
            })

        # Recent patterns (last 24 hours)
        recent_patterns = ExtractionFailurePattern.objects.filter(
            detected_at__gte=timezone.now() - timedelta(hours=24),
            is_active=True
        ).order_by('-detected_at')[:5]

        for pattern in recent_patterns:
            activities.append({
                'type': 'pattern_detected',
                'title': 'Neues Muster erkannt',
                'description': f'{pattern.field_name}: {pattern.root_cause} ({pattern.total_occurrences} Vorkommen)',
                'timestamp': pattern.detected_at.isoformat(),
                'severity': pattern.severity.lower() if pattern.severity else 'medium',
                'icon': 'alert-triangle'
            })

        # Recent errors (documents with error status)
        error_docs = Document.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24),
            status='error'
        ).order_by('-created_at')[:5]

        for doc in error_docs:
            activities.append({
                'type': 'document_error',
                'title': 'Dokumentverarbeitung fehlgeschlagen',
                'description': doc.original_filename,
                'timestamp': doc.created_at.isoformat(),
                'severity': 'error',
                'icon': 'x-circle'
            })

        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)

        # Limit to 20 most recent
        activities = activities[:20]

        return Response({
            'activities': activities,
            'total_count': len(activities)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Error getting recent activity: {e}")
        return Response(
            {
                'detail': 'Fehler beim Abrufen der Aktivitäten',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get system health status",
    description="Get health status of various system components",
    tags=['Admin Dashboard'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Any authenticated user can check health
def system_health(request):
    """
    Get system health status.

    Checks:
    - Database connectivity
    - Redis cache
    - Recent error rates
    """
    try:
        health_status = {
            'overall': 'healthy',
            'components': {},
            'timestamp': timezone.now().isoformat()
        }

        # Database check
        try:
            Document.objects.count()
            health_status['components']['database'] = {
                'status': 'healthy',
                'message': 'Database connection OK'
            }
        except Exception as e:
            health_status['overall'] = 'degraded'
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }

        # Cache check
        try:
            from django.core.cache import cache
            cache.set('health_check_test', 'ok', timeout=10)
            if cache.get('health_check_test') == 'ok':
                health_status['components']['cache'] = {
                    'status': 'healthy',
                    'message': 'Redis cache OK'
                }
            else:
                health_status['overall'] = 'degraded'
                health_status['components']['cache'] = {
                    'status': 'degraded',
                    'message': 'Cache read/write issue'
                }
        except Exception as e:
            health_status['overall'] = 'degraded'
            health_status['components']['cache'] = {
                'status': 'unhealthy',
                'message': f'Cache error: {str(e)}'
            }

        # Error rate check (last hour)
        try:
            recent_errors = Document.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1),
                status='error'
            ).count()

            recent_total = Document.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).count()

            error_rate = (recent_errors / recent_total * 100) if recent_total > 0 else 0

            if error_rate > 20:
                health_status['overall'] = 'degraded'
                status_msg = 'High error rate detected'
            else:
                status_msg = 'Error rate normal'

            health_status['components']['processing'] = {
                'status': 'healthy' if error_rate <= 20 else 'degraded',
                'message': status_msg,
                'error_rate': f'{error_rate:.1f}%',
                'recent_errors': recent_errors,
                'recent_total': recent_total
            }
        except Exception as e:
            health_status['components']['processing'] = {
                'status': 'unknown',
                'message': f'Could not check error rate: {str(e)}'
            }

        return Response(health_status, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Error checking system health: {e}")
        return Response(
            {
                'overall': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
