# -*- coding: utf-8 -*-
"""Pattern analysis models for storing extraction failure patterns."""

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


class ExtractionFailurePattern(models.Model):
    """Stores a detected extraction failure pattern."""

    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical - Immediate attention needed'),
        ('HIGH', 'High - Important to fix'),
        ('MEDIUM', 'Medium - Should be addressed'),
        ('LOW', 'Low - Nice to have'),
    ]

    PATTERN_TYPE_CHOICES = [
        ('low_confidence', 'Low Confidence Field'),
        ('missing_field', 'Missing Field'),
        ('formatting_error', 'Formatting Error'),
        ('data_mismatch', 'Data Mismatch'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='extraction_patterns')

    # Pattern identification
    field_name = models.CharField(max_length=100, help_text='Field being extracted (e.g., amount, vendor_name)')
    pattern_type = models.CharField(max_length=50, choices=PATTERN_TYPE_CHOICES)
    root_cause = models.CharField(max_length=200, help_text='Why the pattern occurs')

    # Pattern metrics
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    confidence_threshold = models.DecimalField(
        max_digits=5, decimal_places=3, default=Decimal('0.70'),
        help_text='Average confidence of this pattern'
    )
    affected_document_count = models.IntegerField(default=0, help_text='Number of documents affected')
    total_occurrences = models.IntegerField(default=0, help_text='Total times pattern occurred')

    # Pattern data
    example_documents = models.JSONField(default=list, blank=True, help_text='List of affected document IDs')
    suggested_fix = models.TextField(blank=True, help_text='Suggested fix or improvement')
    admin_notes = models.TextField(blank=True, help_text='Admin notes on this pattern')

    # Status
    is_active = models.BooleanField(default=True, help_text='Pattern is being tracked')
    is_reviewed = models.BooleanField(default=False, help_text='Pattern has been reviewed by admin')
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text='When pattern was reviewed')
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_patterns'
    )

    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    resolution_deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-severity', '-affected_document_count']
        indexes = [
            models.Index(fields=['user', 'is_reviewed', 'severity']),
            models.Index(fields=['user', 'field_name']),
            models.Index(fields=['severity', 'is_active']),
        ]
        verbose_name = 'Extraction Failure Pattern'
        verbose_name_plural = 'Extraction Failure Patterns'

    def __str__(self):
        return f"{self.field_name} - {self.severity} ({self.affected_document_count} docs)"

    @property
    def resolution_status(self) -> str:
        """Get resolution status."""
        if self.is_reviewed:
            return 'Reviewed'
        if self.resolution_deadline:
            from django.utils import timezone
            if timezone.now() > self.resolution_deadline:
                return 'Overdue'
            return 'In Progress'
        return 'Not Started'


class PatternReviewSession(models.Model):
    """Tracks admin review of patterns."""

    STATUS_CHOICES = [
        ('draft', 'Draft - Not started'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved - Ready to apply'),
        ('rejected', 'Rejected - Needs more work'),
        ('applied', 'Applied - Changes deployed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern = models.ForeignKey(
        ExtractionFailurePattern, on_delete=models.CASCADE,
        related_name='review_sessions'
    )
    admin_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='pattern_reviews'
    )

    # Review details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=200, help_text='Review session title')
    description = models.TextField(help_text='What changes are being reviewed')

    # Review data
    reviewed_cases_count = models.IntegerField(default=0, help_text='Number of cases reviewed')
    approved_cases = models.IntegerField(default=0, help_text='Cases approved for fix')
    rejection_reason = models.TextField(blank=True, help_text='Why pattern was rejected')

    # Impact assessment
    estimated_impact = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Impact'),
            ('medium', 'Medium Impact'),
            ('high', 'High Impact'),
        ],
        default='medium'
    )
    estimated_documents_improved = models.IntegerField(default=0)

    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    scheduled_deployment = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pattern', 'status']),
            models.Index(fields=['admin_user', '-created_at']),
        ]
        verbose_name = 'Pattern Review Session'
        verbose_name_plural = 'Pattern Review Sessions'

    def __str__(self):
        return f"{self.title} - {self.status}"

    @property
    def approval_rate(self) -> float:
        """Percentage of reviewed cases approved."""
        if self.reviewed_cases_count == 0:
            return 0.0
        return self.approved_cases / self.reviewed_cases_count


class PatternFixProposal(models.Model):
    """Proposed fix for an extraction pattern."""

    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('testing', 'Testing'),
        ('validated', 'Validated'),
        ('deployed', 'Deployed'),
        ('rolled_back', 'Rolled Back'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review_session = models.ForeignKey(
        PatternReviewSession, on_delete=models.CASCADE,
        related_name='fix_proposals'
    )
    pattern = models.ForeignKey(
        ExtractionFailurePattern, on_delete=models.CASCADE,
        related_name='fix_proposals'
    )

    # Fix details
    title = models.CharField(max_length=200, help_text='Fix title')
    description = models.TextField(help_text='What is being changed and why')
    fix_type = models.CharField(
        max_length=50,
        choices=[
            ('confidence_threshold', 'Adjust Confidence Threshold'),
            ('field_weight', 'Update Field Weight'),
            ('extraction_logic', 'Improve Extraction Logic'),
            ('validation_rule', 'Add Validation Rule'),
        ]
    )

    # Changes
    change_details = models.JSONField(default=dict, help_text='Detailed changes (old → new)')
    affected_field = models.CharField(max_length=100, help_text='Which field is affected')

    # Testing/Validation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    test_sample_size = models.IntegerField(default=0, help_text='Number of test cases')
    test_success_rate = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True,
        help_text='Success rate in testing (0-1)'
    )
    validation_notes = models.TextField(blank=True, help_text='Notes from validation')

    # Deployment
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=3, default=Decimal('0.80'),
        help_text='Admin confidence in this fix (0-1)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deployed_at = models.DateTimeField(null=True, blank=True)
    deployed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='deployed_fixes'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['pattern', 'status']),
            models.Index(fields=['review_session', 'status']),
        ]
        verbose_name = 'Pattern Fix Proposal'
        verbose_name_plural = 'Pattern Fix Proposals'

    def __str__(self):
        return f"{self.title} - {self.status}"

    @property
    def is_ready_to_deploy(self) -> bool:
        """Check if fix is ready for deployment."""
        return (
            self.status == 'validated' and
            self.test_success_rate and
            self.test_success_rate >= Decimal('0.85') and
            self.confidence_score >= Decimal('0.80')
        )
