"""
Pattern Analysis API Serializers - Phase 4D

Serializers for extraction failure pattern endpoints.
"""
from rest_framework import serializers
from documents.pattern_models import (
    ExtractionFailurePattern,
    PatternReviewSession,
)


class PatternFailureSerializer(serializers.ModelSerializer):
    """
    Extraction failure pattern serializer.

    GET /api/v1/patterns/failures/
    """

    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    pattern_type_display = serializers.CharField(
        source='get_pattern_type_display',
        read_only=True
    )
    resolution_status = serializers.CharField(read_only=True)
    reviewed_by_username = serializers.CharField(
        source='reviewed_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = ExtractionFailurePattern
        fields = [
            'id',
            'field_name',
            'pattern_type',
            'pattern_type_display',
            'root_cause',
            'severity',
            'severity_display',
            'confidence_threshold',
            'affected_document_count',
            'total_occurrences',
            'example_documents',
            'suggested_fix',
            'admin_notes',
            'is_active',
            'is_reviewed',
            'resolution_status',
            'reviewed_at',
            'reviewed_by_username',
            'detected_at',
            'last_updated',
            'resolution_deadline',
        ]
        read_only_fields = [
            'id',
            'detected_at',
            'last_updated',
            'severity_display',
            'pattern_type_display',
            'resolution_status',
        ]


class PatternDetailSerializer(serializers.ModelSerializer):
    """
    Detailed pattern serializer with review sessions.

    GET /api/v1/patterns/{pattern_id}/
    """

    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    pattern_type_display = serializers.CharField(
        source='get_pattern_type_display',
        read_only=True
    )
    resolution_status = serializers.CharField(read_only=True)
    reviewed_by_username = serializers.CharField(
        source='reviewed_by.username',
        read_only=True,
        allow_null=True
    )

    # Include review sessions
    review_sessions = serializers.SerializerMethodField()

    class Meta:
        model = ExtractionFailurePattern
        fields = [
            'id',
            'field_name',
            'pattern_type',
            'pattern_type_display',
            'root_cause',
            'severity',
            'severity_display',
            'confidence_threshold',
            'affected_document_count',
            'total_occurrences',
            'example_documents',
            'suggested_fix',
            'admin_notes',
            'is_active',
            'is_reviewed',
            'resolution_status',
            'reviewed_at',
            'reviewed_by_username',
            'detected_at',
            'last_updated',
            'resolution_deadline',
            'review_sessions',
        ]
        read_only_fields = [
            'id',
            'detected_at',
            'last_updated',
            'severity_display',
            'pattern_type_display',
            'resolution_status',
            'review_sessions',
        ]

    def get_review_sessions(self, obj):
        """Get review sessions for this pattern."""
        sessions = obj.review_sessions.all()[:10]  # Limit to 10 most recent
        return PatternReviewSessionSerializer(sessions, many=True).data


class PatternReviewSessionSerializer(serializers.ModelSerializer):
    """
    Pattern review session serializer.
    """

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    estimated_impact_display = serializers.CharField(
        source='get_estimated_impact_display',
        read_only=True
    )
    admin_username = serializers.CharField(
        source='admin_user.username',
        read_only=True,
        allow_null=True
    )
    approval_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = PatternReviewSession
        fields = [
            'id',
            'status',
            'status_display',
            'title',
            'description',
            'reviewed_cases_count',
            'approved_cases',
            'approval_rate',
            'rejection_reason',
            'estimated_impact',
            'estimated_impact_display',
            'estimated_documents_improved',
            'admin_username',
            'created_at',
            'completed_at',
            'scheduled_deployment',
        ]
        read_only_fields = [
            'id',
            'status_display',
            'estimated_impact_display',
            'approval_rate',
            'admin_username',
            'created_at',
        ]


class PatternFixApprovalSerializer(serializers.Serializer):
    """
    Serializer for approving a pattern fix.

    POST /api/v1/patterns/{pattern_id}/approve-fix/
    {
        "review_title": "Fix low-confidence amount extraction",
        "description": "Apply regex pattern for German currency formats",
        "estimated_impact": "high",
        "estimated_documents_improved": 45,
        "scheduled_deployment": "2025-12-15T10:00:00Z"
    }
    """

    review_title = serializers.CharField(
        max_length=200,
        help_text="Title for the review session"
    )
    description = serializers.CharField(
        help_text="Description of what changes are being reviewed"
    )
    estimated_impact = serializers.ChoiceField(
        choices=[
            ('low', 'Low Impact'),
            ('medium', 'Medium Impact'),
            ('high', 'High Impact'),
        ],
        default='medium',
        help_text="Estimated impact of this fix"
    )
    estimated_documents_improved = serializers.IntegerField(
        min_value=0,
        help_text="Estimated number of documents that will be improved"
    )
    scheduled_deployment = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="When to deploy this fix (optional)"
    )
    admin_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes about the approval"
    )


class PatternBulkActionSerializer(serializers.Serializer):
    """
    Serializer for bulk pattern actions.

    POST /api/v1/patterns/bulk-action/
    {
        "pattern_ids": ["uuid1", "uuid2", "uuid3"],
        "action": "mark_reviewed",
        "admin_notes": "Reviewed and approved for deployment"
    }
    """

    pattern_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of pattern IDs to process"
    )
    action = serializers.ChoiceField(
        choices=[
            ('mark_reviewed', 'Mark as Reviewed'),
            ('mark_inactive', 'Mark as Inactive'),
            ('mark_active', 'Mark as Active'),
            ('set_severity', 'Update Severity'),
        ],
        help_text="Action to perform on selected patterns"
    )
    severity = serializers.ChoiceField(
        choices=[
            ('CRITICAL', 'Critical'),
            ('HIGH', 'High'),
            ('MEDIUM', 'Medium'),
            ('LOW', 'Low'),
        ],
        required=False,
        help_text="New severity (only for set_severity action)"
    )
    admin_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes about this bulk action"
    )

    def validate(self, data):
        """Validate that severity is provided for set_severity action."""
        if data['action'] == 'set_severity' and not data.get('severity'):
            raise serializers.ValidationError({
                'severity': 'Severity is required for set_severity action'
            })
        return data
