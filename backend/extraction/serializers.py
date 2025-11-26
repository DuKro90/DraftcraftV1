"""Serializers for extraction models."""
from rest_framework import serializers
from .models import ExtractionConfig, ExtractedEntity, MaterialExtraction


class ExtractedEntitySerializer(serializers.ModelSerializer):
    """Serializer for ExtractedEntity model."""

    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)

    class Meta:
        model = ExtractedEntity
        fields = (
            'id',
            'entity_type',
            'entity_type_display',
            'text',
            'start_offset',
            'end_offset',
            'confidence_score',
            'metadata',
            'created_at',
        )
        read_only_fields = fields


class MaterialExtractionSerializer(serializers.ModelSerializer):
    """Serializer for MaterialExtraction model."""

    document_id = serializers.CharField(source='document.id', read_only=True)
    document_name = serializers.CharField(source='document.original_filename', read_only=True)

    class Meta:
        model = MaterialExtraction
        fields = (
            'id',
            'document_id',
            'document_name',
            'materials',
            'complexity_level',
            'surface_finish',
            'additional_features',
            'dimensions',
            'unit',
            'extraction_confidence',
            'requires_manual_review',
            'review_notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'document_id',
            'document_name',
            'created_at',
            'updated_at',
        )


class ExtractionConfigSerializer(serializers.ModelSerializer):
    """Serializer for ExtractionConfig model."""

    class Meta:
        model = ExtractionConfig
        fields = (
            'id',
            'name',
            'language',
            'ocr_enabled',
            'ocr_confidence_threshold',
            'ocr_use_cuda',
            'ner_enabled',
            'ner_model',
            'ner_confidence_threshold',
            'max_file_size_mb',
            'timeout_seconds',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class ExtractionSummarySerializer(serializers.Serializer):
    """Serializer for extraction summary results."""

    document_id = serializers.CharField()
    original_filename = serializers.CharField()
    status = serializers.CharField()
    ocr_confidence = serializers.FloatField()
    entity_count = serializers.IntegerField()
    entity_types = serializers.DictField()
    materials_found = serializers.DictField()
    processing_time_ms = serializers.IntegerField()
    requires_review = serializers.BooleanField()
    created_at = serializers.DateTimeField()
