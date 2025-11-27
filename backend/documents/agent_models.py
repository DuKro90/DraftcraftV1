"""Agent memory, knowledge graph, and cost tracking models."""
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


class DocumentMemory(models.Model):
    """Short-term memory for document processing patterns (Redis-backed via Django Cache).

    Stores patterns learned during current session with 1-hour TTL.
    Used by ConfidenceRouter to improve extraction on similar documents.
    """

    PATTERN_TYPES = [
        ('layout', 'Document Layout Pattern'),
        ('vendor', 'Vendor Name Pattern'),
        ('amount', 'Amount/Price Pattern'),
        ('date', 'Date Format Pattern'),
        ('gaeb', 'GAEB Position Pattern'),
        ('material', 'Material Name Pattern'),
        ('contact', 'Contact Information Pattern'),
        ('custom', 'Custom Pattern'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_memories')

    # Pattern metadata
    pattern_type = models.CharField(max_length=20, choices=PATTERN_TYPES)
    pattern_data = models.JSONField()  # Flexible pattern storage (regex, keywords, format, etc.)

    # Learning metrics
    confidence = models.FloatField(default=0.7)  # How confident this pattern is
    usage_count = models.IntegerField(default=0)  # Times successfully applied
    success_count = models.IntegerField(default=0)  # Successful matches

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_used']
        indexes = [
            models.Index(fields=['user', 'pattern_type', '-last_used']),
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name_plural = 'Document Memories'

    def __str__(self):
        return f"{self.pattern_type} - {self.user.username}"

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this pattern."""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count


class KnowledgeGraph(models.Model):
    """Long-term persistent knowledge graph of entity relationships.

    Stores learned relationships between entities (vendors, materials, amounts, etc.)
    across documents. Used to improve extraction and provide context.
    """

    RELATIONSHIP_TYPES = [
        ('vendor_to_invoice', 'Vendor to Invoice Number'),
        ('vendor_to_contact', 'Vendor to Contact Info'),
        ('material_to_supplier', 'Material to Supplier'),
        ('amount_to_category', 'Amount to Cost Category'),
        ('date_to_vendor', 'Date Pattern to Vendor'),
        ('position_to_material', 'GAEB Position to Material'),
        ('custom', 'Custom Relationship'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge_graphs')

    # Entity relationship
    source_entity = models.CharField(max_length=255)  # e.g., "Schreinerei Müller"
    target_entity = models.CharField(max_length=255)  # e.g., "invoice_pattern_MM*"
    relationship_type = models.CharField(max_length=30, choices=RELATIONSHIP_TYPES)

    # Confidence and weight
    confidence = models.FloatField(default=0.5)  # 0.0 - 1.0
    weight = models.FloatField(default=1.0)  # Importance multiplier

    # Occurrence tracking
    occurrences = models.IntegerField(default=1)  # How many times seen
    co_occurrence_ratio = models.FloatField(default=1.0)  # How often they appear together

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', 'source_entity']),
            models.Index(fields=['user', 'target_entity']),
            models.Index(fields=['user', 'relationship_type', '-last_seen']),
            models.Index(fields=['user', '-occurrences']),
        ]
        unique_together = [('user', 'source_entity', 'target_entity', 'relationship_type')]
        verbose_name_plural = 'Knowledge Graphs'

    def __str__(self):
        return f"{self.source_entity} → {self.target_entity} ({self.relationship_type})"

    @property
    def reliability_score(self) -> float:
        """Calculate overall reliability (confidence * weight * co-occurrence)."""
        return self.confidence * self.weight * min(self.co_occurrence_ratio, 1.0)


class GeminiUsageLog(models.Model):
    """Log of all Gemini API calls for cost tracking and quota management."""

    ROUTE_TYPES = [
        ('auto_accept', 'Auto-Accept (Skipped Agent)'),
        ('agent_verify', 'Agent Verification'),
        ('agent_extract', 'Agent Re-Extraction'),
        ('human_review', 'Marked for Human Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gemini_usage_logs')

    # Document reference
    document_id = models.UUIDField(null=True, blank=True)  # FK to Document (soft reference)

    # Token and cost metrics
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)

    input_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=Decimal('0'))
    output_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=Decimal('0'))
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=Decimal('0'))

    # Routing context
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPES)
    confidence_before = models.FloatField(null=True, blank=True)
    confidence_after = models.FloatField(null=True, blank=True)

    # Performance
    processing_time_ms = models.IntegerField(default=0)
    cache_hit = models.BooleanField(default=False)

    # Model used
    gemini_model = models.CharField(max_length=50, default='gemini-1.5-flash')

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'route_type', '-created_at']),
            models.Index(fields=['created_at']),  # For billing aggregations
        ]
        verbose_name_plural = 'Gemini Usage Logs'

    def __str__(self):
        return f"{self.user.username} - {self.route_type} (${self.total_cost_usd})"


class UserAgentBudget(models.Model):
    """Per-user budget configuration and usage tracking for Gemini API."""

    BUDGET_STATUS = [
        ('active', 'Active'),
        ('warning', 'Warning - Near Limit'),
        ('paused', 'Paused - Budget Exceeded'),
        ('disabled', 'Disabled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_budget')

    # Budget limits
    monthly_budget_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text='Monthly budget in USD'
    )

    # Current usage
    current_month_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Cost used in current month'
    )

    # Model configuration
    gemini_model = models.CharField(
        max_length=50,
        default='gemini-1.5-flash',
        help_text='Gemini model to use (e.g., gemini-1.5-flash, gemini-2-pro)'
    )
    max_model_usage_percent = models.IntegerField(
        default=100,
        help_text='Maximum % of budget to use on expensive models (e.g., 20%)',
        validators=[lambda x: 0 <= x <= 100]
    )

    # Alert configuration
    alert_threshold_percent = models.IntegerField(
        default=80,
        help_text='Alert when usage reaches X% of budget',
        validators=[lambda x: 0 <= x <= 100]
    )
    alert_emails = models.JSONField(
        default=list,
        blank=True,
        help_text='Additional email addresses for budget alerts'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=BUDGET_STATUS,
        default='active',
        help_text='Current budget status'
    )

    # Tracking
    last_reset_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user', '-updated_at']),
        ]
        verbose_name_plural = 'User Agent Budgets'

    def __str__(self):
        return f"{self.user.username} - ${self.monthly_budget_usd}/month ({self.status})"

    @property
    def budget_used_percent(self) -> float:
        """Calculate percentage of budget used."""
        if self.monthly_budget_usd == 0:
            return 0.0
        return float(self.current_month_cost_usd / self.monthly_budget_usd * 100)

    @property
    def budget_remaining_usd(self) -> Decimal:
        """Calculate remaining budget."""
        return max(self.monthly_budget_usd - self.current_month_cost_usd, Decimal('0'))

    @property
    def can_afford_agent(self) -> bool:
        """Check if user can afford agent call based on current budget."""
        if self.status == 'paused':
            return False
        if self.status == 'disabled':
            return False
        # Assume average agent call is $0.01
        return self.budget_remaining_usd >= Decimal('0.01')
