"""Django admin for extraction models."""
from django.contrib import admin
from django.utils.html import format_html
from .models import ExtractionConfig, ExtractedEntity, MaterialExtraction


@admin.register(ExtractionConfig)
class ExtractionConfigAdmin(admin.ModelAdmin):
    """Admin for ExtractionConfig model."""

    list_display = ('name', 'language_badge', 'ocr_enabled', 'ner_enabled', 'updated_at')
    list_filter = ('language', 'ocr_enabled', 'ner_enabled', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'language')
        }),
        ('OCR Settings', {
            'fields': ('ocr_enabled', 'ocr_confidence_threshold', 'ocr_use_cuda')
        }),
        ('NER Settings', {
            'fields': ('ner_enabled', 'ner_model', 'ner_confidence_threshold')
        }),
        ('Processing Limits', {
            'fields': ('max_file_size_mb', 'timeout_seconds')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def language_badge(self, obj):
        """Display language as colored badge."""
        colors = {'de': '#3498DB', 'en': '#27AE60'}
        color = colors.get(obj.language, '#95A5A6')
        lang_name = dict(obj.LANGUAGE_CHOICES).get(obj.language)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color,
            lang_name
        )
    language_badge.short_description = 'Language'


@admin.register(ExtractedEntity)
class ExtractedEntityAdmin(admin.ModelAdmin):
    """Admin for ExtractedEntity model."""

    list_display = ('text_display', 'entity_type_badge', 'confidence_percent', 'document_name', 'created_at')
    list_filter = ('entity_type', 'confidence_score', 'created_at', 'document__status')
    search_fields = ('text', 'document__original_filename', 'document__id')
    readonly_fields = ('document', 'entity_type', 'text', 'start_offset', 'end_offset', 'created_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Document', {
            'fields': ('document',)
        }),
        ('Entity', {
            'fields': ('entity_type', 'text')
        }),
        ('Position', {
            'fields': ('start_offset', 'end_offset'),
            'classes': ('collapse',)
        }),
        ('Quality', {
            'fields': ('confidence_score',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def text_display(self, obj):
        """Display entity text, truncated."""
        text = obj.text[:50]
        if len(obj.text) > 50:
            text += "..."
        return text
    text_display.short_description = 'Text'

    def entity_type_badge(self, obj):
        """Display entity type as colored badge."""
        colors = {
            'MATERIAL': '#3498DB',
            'QUANTITY': '#27AE60',
            'UNIT': '#F39C12',
            'PRICE': '#E67E22',
            'PERSON': '#9B59B6',
            'ORGANIZATION': '#1ABC9C',
            'DATE': '#E74C3C',
            'LOCATION': '#34495E',
            'OTHER': '#95A5A6',
        }
        color = colors.get(obj.entity_type, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.entity_type
        )
    entity_type_badge.short_description = 'Type'

    def confidence_percent(self, obj):
        """Display confidence as percentage."""
        return f"{obj.confidence_score * 100:.1f}%"
    confidence_percent.short_description = 'Confidence'

    def document_name(self, obj):
        """Display document filename."""
        return obj.document.original_filename
    document_name.short_description = 'Document'

    def has_add_permission(self, request):
        """Prevent manual entity creation (should come from extraction)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent entity deletion (DSGVO compliance)."""
        return request.user.is_superuser


@admin.register(MaterialExtraction)
class MaterialExtractionAdmin(admin.ModelAdmin):
    """Admin for MaterialExtraction model."""

    list_display = ('document_name', 'complexity_level', 'surface_finish', 'confidence_display', 'requires_review_badge', 'updated_at')
    list_filter = ('complexity_level', 'surface_finish', 'requires_manual_review', 'updated_at')
    search_fields = ('document__original_filename', 'document__id')
    readonly_fields = ('document', 'created_at', 'updated_at')
    date_hierarchy = 'updated_at'

    fieldsets = (
        ('Document', {
            'fields': ('document',)
        }),
        ('Materials', {
            'fields': ('materials', 'unit')
        }),
        ('Specifications', {
            'fields': ('complexity_level', 'surface_finish', 'additional_features')
        }),
        ('Dimensions', {
            'fields': ('dimensions',),
            'classes': ('collapse',)
        }),
        ('Quality Control', {
            'fields': ('extraction_confidence', 'requires_manual_review', 'review_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def document_name(self, obj):
        """Display document filename."""
        return obj.document.original_filename
    document_name.short_description = 'Document'

    def confidence_display(self, obj):
        """Display confidence as percentage."""
        return f"{obj.extraction_confidence * 100:.1f}%"
    confidence_display.short_description = 'Confidence'

    def requires_review_badge(self, obj):
        """Display review status as badge."""
        if obj.requires_manual_review:
            return format_html(
                '<span style="background-color: #F39C12; color: white; padding: 3px 8px; '
                'border-radius: 3px;">Review Required</span>'
            )
        return format_html(
            '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
            'border-radius: 3px;">Auto-Approved</span>'
        )
    requires_review_badge.short_description = 'Status'
