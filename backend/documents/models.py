"""Document management models."""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid


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
