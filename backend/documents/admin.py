"""Django admin for document models."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Document, ExtractionResult, AuditLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin for Document model."""

    list_display = ('original_filename', 'status_badge', 'user', 'created_at', 'file_size_display')
    list_filter = ('status', 'document_type', 'created_at', 'is_encrypted')
    search_fields = ('original_filename', 'user__username', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'file_size_bytes')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('File Info', {
            'fields': ('id', 'file', 'original_filename', 'file_size_bytes', 'document_type')
        }),
        ('User', {
            'fields': ('user',)
        }),
        ('Processing', {
            'fields': ('status',)
        }),
        ('DSGVO Compliance', {
            'fields': ('retention_until', 'is_encrypted')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'uploaded': '#FFA500',
            'processing': '#3498DB',
            'completed': '#27AE60',
            'error': '#E74C3C',
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        size_mb = obj.file_size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"
    file_size_display.short_description = 'File Size'

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly after creation."""
        if obj:
            return self.readonly_fields + ('file', 'original_filename', 'file_size_bytes', 'document_type')
        return self.readonly_fields


@admin.register(ExtractionResult)
class ExtractionResultAdmin(admin.ModelAdmin):
    """Admin for ExtractionResult model."""

    list_display = ('document_name', 'confidence_score_display', 'processing_time', 'created_at')
    list_filter = ('created_at', 'document__status')
    search_fields = ('document__original_filename', 'document__id')
    readonly_fields = ('document', 'created_at', 'updated_at', 'ocr_text_preview')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Document', {
            'fields': ('document',)
        }),
        ('Extracted Data', {
            'fields': ('ocr_text_preview', 'extracted_data')
        }),
        ('Quality Metrics', {
            'fields': ('confidence_scores',)
        }),
        ('Errors', {
            'fields': ('error_messages',),
            'classes': ('collapse',)
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

    def confidence_score_display(self, obj):
        """Display confidence as percentage."""
        if obj.confidence_scores:
            avg_conf = sum(obj.confidence_scores.values()) / len(obj.confidence_scores)
            return f"{avg_conf * 100:.1f}%"
        return "N/A"
    confidence_score_display.short_description = 'Avg Confidence'

    def processing_time(self, obj):
        """Display processing time in seconds."""
        return f"{obj.processing_time_ms / 1000:.2f}s"
    processing_time.short_description = 'Processing Time'

    def ocr_text_preview(self, obj):
        """Show first 500 chars of OCR text."""
        text = obj.ocr_text[:500] if obj.ocr_text else "(No OCR text)"
        return text
    ocr_text_preview.short_description = 'OCR Text Preview'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin for AuditLog model."""

    list_display = ('action_badge', 'user', 'document_name', 'timestamp')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('document__original_filename', 'document__id', 'user__username')
    readonly_fields = ('action', 'user', 'document', 'timestamp', 'details')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Prevent manual audit log creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent audit log deletion (DSGVO compliance)."""
        return request.user.is_superuser

    def action_badge(self, obj):
        """Display action as colored badge."""
        colors = {
            'uploaded': '#3498DB',
            'viewed': '#95A5A6',
            'processed': '#27AE60',
            'exported': '#F39C12',
            'deleted': '#E74C3C',
        }
        color = colors.get(obj.action, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'

    def document_name(self, obj):
        """Display document filename or dash if deleted."""
        if obj.document:
            return obj.document.original_filename
        return "—"
    document_name.short_description = 'Document'
