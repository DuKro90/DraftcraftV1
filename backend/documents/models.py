"""Document management models."""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid

# Import Betriebskennzahl models (TIER 1-3 calculation metrics) for Django app registry
# This ensures Django discovers models in betriebskennzahl_models.py
from .betriebskennzahl_models import (  # noqa: F401
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
    MateriallistePosition,
    SaisonaleMarge,
    AdminActionAudit,
)

# Import Transparency models (Phase 4A: Explainable calculations & user benchmarks)
# This ensures Django discovers models in transparency_models.py
from .transparency_models import (  # noqa: F401
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark,
)

# Import Wiki models (Admin documentation system)
# This ensures Django discovers models in models_wiki.py
from .models_wiki import (  # noqa: F401
    WikiCategory,
    WikiArticle,
    WikiSearchLog,
    WikiFeedback,
)

# Import Standardbauteile models (Phase 4B: Component catalog & calculation rules)
# This ensures Django discovers models in models_bauteile.py
from .models_bauteile import (  # noqa: F401
    StandardBauteil,
    BauteilRegel,
    BauteilKatalog,
    BauteilKatalogPosition,
    GeometrieBerechnung,
    CompanyProfile,
)

# Import Betriebspauschalen models (Phase 4C: Fixed business expense rules)
# This ensures Django discovers models in models_pauschalen.py
from .models_pauschalen import (  # noqa: F401
    BetriebspauschaleRegel,
    PauschaleAnwendung,
)


class Document(models.Model):
    """Uploaded document for processing."""

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')

    # File info
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'docx', 'txt'])]
    )
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.IntegerField()

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')

    # Metadata
    document_type = models.CharField(max_length=50, default='pdf')  # pdf, gaeb, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # DSGVO
    retention_until = models.DateTimeField(null=True, blank=True)
    is_encrypted = models.BooleanField(default=False)

    # Extra data
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


class ExtractionResult(models.Model):
    """OCR/NER extraction results."""

    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='extraction_result'
    )

    # Extracted text
    ocr_text = models.TextField(blank=True)

    # Structured data (Phase 2)
    extracted_data = models.JSONField(default=dict)  # materials, quantities, prices, etc.

    # Quality metrics
    confidence_scores = models.JSONField(default=dict)  # per entity type
    processing_time_ms = models.IntegerField(default=0)

    # Errors (if any)
    error_messages = models.JSONField(default=list, blank=True)

    # Agent enhancement (agentic RAG)
    agent_enhanced = models.BooleanField(default=False, help_text='Was result enhanced by Gemini agent')
    agent_confidence = models.FloatField(null=True, blank=True, help_text='Agent confidence score after enhancement')
    requires_review = models.BooleanField(default=False, help_text='Flagged for human review by agent')
    review_reasons = models.JSONField(default=list, blank=True, help_text='Reasons why review is needed')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Extraction Results'

    def __str__(self):
        return f"Extraction for {self.document.original_filename}"


class AuditLog(models.Model):
    """DSGVO audit logging."""

    ACTION_CHOICES = [
        ('uploaded', 'Document Uploaded'),
        ('viewed', 'Document Viewed'),
        ('processed', 'Document Processed'),
        ('exported', 'Data Exported'),
        ('deleted', 'Document Deleted'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Details
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['document', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action} - {self.timestamp}"


class Batch(models.Model):
    """Batch job for processing multiple documents."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('partial_failure', 'Partial Failure'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batches')

    # Batch metadata
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Processing progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_count = models.IntegerField(default=0)
    processed_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)

    # Extra metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage."""
        if self.file_count == 0:
            return 0.0
        return (self.processed_count + self.error_count) / self.file_count * 100


class BatchDocument(models.Model):
    """Individual document within a batch."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='batch_documents'
    )

    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Cloud Task tracking (for async processing)
    cloud_task_id = models.CharField(max_length=255, blank=True, null=True)

    # Error handling
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['batch', 'status']),
            models.Index(fields=['document']),
        ]
        unique_together = [('batch', 'document')]

    def __str__(self):
        return f"{self.batch.name} - {self.document.original_filename}"
