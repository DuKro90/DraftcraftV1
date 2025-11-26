"""Serializers for document models."""
from rest_framework import serializers
from .models import Document, ExtractionResult, AuditLog


class ExtractionResultSerializer(serializers.ModelSerializer):
    """Serializer for ExtractionResult model."""

    document_id = serializers.CharField(source='document.id', read_only=True)
    confidence = serializers.SerializerMethodField()

    class Meta:
        model = ExtractionResult
        fields = (
            'id',
            'document_id',
            'ocr_text',
            'extracted_data',
            'confidence',
            'confidence_scores',
            'processing_time_ms',
            'error_messages',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'document_id',
            'ocr_text',
            'extracted_data',
            'confidence_scores',
            'processing_time_ms',
            'created_at',
            'updated_at',
        )

    def get_confidence(self, obj):
        """Calculate average confidence."""
        if obj.confidence_scores:
            values = [v for v in obj.confidence_scores.values() if isinstance(v, (int, float))]
            if values:
                return sum(values) / len(values)
        return None


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Document with extraction results."""

    extraction_result = ExtractionResultSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id',
            'file',
            'original_filename',
            'file_size_bytes',
            'file_size_display',
            'status',
            'status_display',
            'document_type',
            'created_at',
            'updated_at',
            'retention_until',
            'is_encrypted',
            'metadata',
            'extraction_result',
        )
        read_only_fields = (
            'id',
            'status',
            'created_at',
            'updated_at',
            'extraction_result',
        )

    def get_file_size_display(self, obj):
        """Return file size in MB."""
        return f"{obj.file_size_bytes / (1024 * 1024):.2f} MB"


class DocumentListSerializer(serializers.ModelSerializer):
    """List serializer for Document (minimal fields)."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id',
            'original_filename',
            'file_size_display',
            'status',
            'status_display',
            'document_type',
            'created_at',
        )
        read_only_fields = fields

    def get_file_size_display(self, obj):
        """Return file size in MB."""
        return f"{obj.file_size_bytes / (1024 * 1024):.2f} MB"


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload."""

    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id',
            'file',
            'original_filename',
            'file_size_bytes',
            'file_size_display',
            'document_type',
            'status',
            'created_at',
        )
        read_only_fields = (
            'id',
            'file_size_bytes',
            'status',
            'created_at',
        )

    def create(self, validated_data):
        """Set file size and other defaults on creation."""
        validated_data['file_size_bytes'] = validated_data['file'].size
        validated_data['original_filename'] = validated_data['file'].name
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def get_file_size_display(self, obj):
        """Return file size in MB."""
        return f"{obj.file_size_bytes / (1024 * 1024):.2f} MB"


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""

    action_display = serializers.CharField(source='get_action_display', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    document_name = serializers.CharField(source='document.original_filename', read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = (
            'id',
            'document',
            'document_name',
            'user',
            'user_name',
            'action',
            'action_display',
            'timestamp',
            'details',
        )
        read_only_fields = fields
