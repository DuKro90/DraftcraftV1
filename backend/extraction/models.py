"""Extraction module models - OCR/NER processing."""
from django.db import models
from documents.models import Document


class ExtractionConfig(models.Model):
    """Configuration for extraction services."""

    LANGUAGE_CHOICES = [
        ('de', 'German'),
        ('en', 'English'),
    ]

    name = models.CharField(max_length=100, unique=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='de')

    # PaddleOCR settings
    ocr_enabled = models.BooleanField(default=True)
    ocr_confidence_threshold = models.FloatField(default=0.6)
    ocr_use_cuda = models.BooleanField(default=False)

    # spaCy NER settings
    ner_enabled = models.BooleanField(default=True)
    ner_model = models.CharField(max_length=100, default='de_core_news_lg')
    ner_confidence_threshold = models.FloatField(default=0.7)

    # Processing settings
    max_file_size_mb = models.IntegerField(default=50)
    timeout_seconds = models.IntegerField(default=300)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.language})"


class ExtractedEntity(models.Model):
    """Named entity extracted from document."""

    ENTITY_TYPES = [
        ('MATERIAL', 'Material'),
        ('QUANTITY', 'Quantity'),
        ('UNIT', 'Unit'),
        ('PRICE', 'Price'),
        ('PERSON', 'Person'),
        ('ORGANIZATION', 'Organization'),
        ('DATE', 'Date'),
        ('LOCATION', 'Location'),
        ('OTHER', 'Other'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='extracted_entities'
    )

    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES)
    text = models.CharField(max_length=500)
    start_offset = models.IntegerField()  # Character position in OCR text
    end_offset = models.IntegerField()

    confidence_score = models.FloatField()  # 0-1 confidence from NER
    metadata = models.JSONField(default=dict, blank=True)  # Normalized values, etc.

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_offset']
        indexes = [
            models.Index(fields=['document', 'entity_type']),
        ]

    def __str__(self):
        return f"{self.entity_type}: {self.text[:50]}"


class MaterialExtraction(models.Model):
    """Extracted material specifications from manufacturing document."""

    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='material_extraction'
    )

    # Extracted materials
    materials = models.JSONField(default=dict)  # {wood_type: quantity, ...}
    complexity_level = models.CharField(max_length=50, blank=True)
    surface_finish = models.CharField(max_length=50, blank=True)
    additional_features = models.JSONField(default=list, blank=True)

    # Extracted measurements
    dimensions = models.JSONField(default=dict)  # {width, height, depth, area, ...}
    unit = models.CharField(max_length=20, blank=True)

    # Processing metadata
    extraction_confidence = models.FloatField(default=0.0)
    requires_manual_review = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Materials for {self.document.original_filename}"
