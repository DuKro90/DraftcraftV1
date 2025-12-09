"""Django admin for document models."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import logging

from .models import Document, ExtractionResult, AuditLog
from .admin_actions import BulkUploadAdminMixin
from .forms import (
    DocumentAdminForm,
    BetriebskennzahlTemplateAdminForm,
    HolzartKennzahlAdminForm,
    OberflächenbearbeitungKennzahlAdminForm,
    KomplexitaetKennzahlAdminForm,
    IndividuelleBetriebskennzahlAdminForm,
    MateriallistePositionAdminForm,
    SaisonaleMargeAdminForm,
    ExtractionFailurePatternAdminForm,
    PatternReviewSessionAdminForm,
    PatternFixProposalAdminForm,
    CalculationExplanationAdminForm,
    CalculationFactorAdminForm,
    UserProjectBenchmarkAdminForm,
)
from .betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
    MateriallistePosition,
    SaisonaleMarge,
    AdminActionAudit,
)
from .pattern_models import (
    ExtractionFailurePattern,
    PatternReviewSession,
    PatternFixProposal,
)
from .transparency_models import (
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark,
)

logger = logging.getLogger(__name__)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin for Document model."""

    form = DocumentAdminForm
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


# ============================================================================
# PHASE 3: BETRIEBSKENNZAHLEN (OPERATIONAL METRICS) ADMIN INTERFACE
# ============================================================================

# TIER 1: Global Standards
# ============================================================================


class HolzartKennzahlInline(admin.TabularInline):
    """Inline editor for wood type factors."""

    model = HolzartKennzahl
    extra = 1
    fields = ('holzart', 'kategorie', 'preis_faktor', 'verfuegbarkeit', 'is_enabled')
    list_display = ('holzart', 'kategorie', 'preis_faktor', 'is_enabled')


class OberflächenbearbeitungKennzahlInline(admin.TabularInline):
    """Inline editor for surface finishing factors."""

    model = OberflächenbearbeitungKennzahl
    extra = 1
    fields = ('bearbeitung', 'preis_faktor', 'zeit_faktor', 'is_enabled')


class KomplexitaetKennzahlInline(admin.TabularInline):
    """Inline editor for complexity/technique factors."""

    model = KomplexitaetKennzahl
    extra = 1
    fields = ('technik', 'preis_faktor', 'zeit_faktor', 'schwierigkeitsgrad', 'is_enabled')


@admin.register(BetriebskennzahlTemplate)
class BetriebskennzahlTemplateAdmin(admin.ModelAdmin):
    """Admin for global Betriebskennzahl templates."""

    form = BetriebskennzahlTemplateAdminForm
    list_display = ('name', 'version', 'status_badge', 'created_by', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at', 'created_by')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'created_by')
    date_hierarchy = 'updated_at'

    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'version', 'is_active')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [
        HolzartKennzahlInline,
        OberflächenbearbeitungKennzahlInline,
        KomplexitaetKennzahlInline,
    ]

    def status_badge(self, obj):
        """Display active/inactive status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 5px 10px; '
                'border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #95A5A6; color: white; padding: 5px 10px; '
            'border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HolzartKennzahl)
class HolzartKennzahlAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    """Admin for wood type factors with bulk upload support and cache invalidation."""

    # Bulk upload configuration
    bulk_upload_model_type = 'holzart'
    bulk_upload_template_required = True

    form = HolzartKennzahlAdminForm
    list_display = ('holzart', 'get_template_name', 'kategorie', 'preis_faktor', 'status_badge')
    list_filter = ('template', 'kategorie', 'is_enabled')
    search_fields = ('holzart', 'template__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Wood Type', {
            'fields': ('template', 'holzart', 'kategorie')
        }),
        ('Pricing', {
            'fields': ('preis_faktor',),
            'description': 'Price multiplier (1.0 = base, 1.3 = +30%)'
        }),
        ('Availability', {
            'fields': ('verfuegbarkeit',)
        }),
        ('Status', {
            'fields': ('is_enabled',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_template_name(self, obj):
        """Display template name."""
        return obj.template.name
    get_template_name.short_description = 'Template'

    def status_badge(self, obj):
        """Display enabled/disabled status."""
        if obj.is_enabled:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 2px;">Enabled</span>'
            )
        return format_html(
            '<span style="background-color: #E74C3C; color: white; padding: 3px 8px; '
            'border-radius: 2px;">Disabled</span>'
        )
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Save model and invalidate related cache."""
        super().save_model(request, obj, form, change)
        cache_key = f'holzarten_template_{obj.template_id}'
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key} (admin save)")

    def delete_model(self, request, obj):
        """Delete model and invalidate cache."""
        cache_key = f'holzarten_template_{obj.template_id}'
        super().delete_model(request, obj)
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key} (admin delete)")


@admin.register(OberflächenbearbeitungKennzahl)
class OberflächenbearbeitungKennzahlAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    """Admin for surface finishing factors with bulk upload support and cache invalidation."""

    # Bulk upload configuration
    bulk_upload_model_type = 'oberflaechen'
    bulk_upload_template_required = True

    form = OberflächenbearbeitungKennzahlAdminForm
    list_display = ('bearbeitung', 'get_template_name', 'preis_faktor', 'zeit_faktor', 'status_badge')
    list_filter = ('template', 'is_enabled')
    search_fields = ('bearbeitung', 'template__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Surface Treatment', {
            'fields': ('template', 'bearbeitung')
        }),
        ('Factors', {
            'fields': ('preis_faktor', 'zeit_faktor'),
            'description': 'Price and time multipliers (1.0 = no change)'
        }),
        ('Status', {
            'fields': ('is_enabled',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_template_name(self, obj):
        """Display template name."""
        return obj.template.name
    get_template_name.short_description = 'Template'

    def status_badge(self, obj):
        """Display enabled/disabled status."""
        if obj.is_enabled:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 2px;">Enabled</span>'
            )
        return format_html(
            '<span style="background-color: #E74C3C; color: white; padding: 3px 8px; '
            'border-radius: 2px;">Disabled</span>'
        )
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Save model and invalidate related cache."""
        super().save_model(request, obj, form, change)
        cache_key = f'oberflaechen_template_{obj.template_id}'
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key} (admin save)")

    def delete_model(self, request, obj):
        """Delete model and invalidate cache."""
        cache_key = f'oberflaechen_template_{obj.template_id}'
        super().delete_model(request, obj)
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key} (admin delete)")


@admin.register(KomplexitaetKennzahl)
class KomplexitaetKennzahlAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    """Admin for complexity/technique factors with bulk upload support and cache invalidation."""

    # Bulk upload configuration
    bulk_upload_model_type = 'komplexitaet'
    bulk_upload_template_required = True

    form = KomplexitaetKennzahlAdminForm
    list_display = ('technik', 'get_template_name', 'schwierigkeitsgrad', 'preis_faktor', 'zeit_faktor', 'status_badge')
    list_filter = ('template', 'schwierigkeitsgrad', 'is_enabled')
    search_fields = ('technik', 'template__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Technique', {
            'fields': ('template', 'technik', 'schwierigkeitsgrad')
        }),
        ('Factors', {
            'fields': ('preis_faktor', 'zeit_faktor'),
            'description': 'Price and time multipliers'
        }),
        ('Status', {
            'fields': ('is_enabled',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_template_name(self, obj):
        """Display template name."""
        return obj.template.name
    get_template_name.short_description = 'Template'

    def status_badge(self, obj):
        """Display enabled/disabled status."""
        if obj.is_enabled:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 2px;">Enabled</span>'
            )
        return format_html(
            '<span style="background-color: #E74C3C; color: white; padding: 3px 8px; '
            'border-radius: 2px;">Disabled</span>'
        )
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Save model and invalidate related cache."""
        super().save_model(request, obj, form, change)
        cache_key = f'komplexitaet_template_{obj.template_id}'
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key} (admin save)")

    def delete_model(self, request, obj):
        """Delete model and invalidate cache."""
        cache_key = f'komplexitaet_template_{obj.template_id}'
        super().delete_model(request, obj)
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key} (admin delete)")


# TIER 2: Company-Specific Metrics
# ============================================================================


@admin.register(IndividuelleBetriebskennzahl)
class IndividuelleBetriebskennzahlAdmin(admin.ModelAdmin):
    """Admin for company-specific operational metrics."""

    form = IndividuelleBetriebskennzahlAdminForm
    list_display = ('get_company_name', 'stundensatz_arbeit', 'gewinnmarge_prozent', 'status_badge', 'updated_at')
    list_filter = ('is_active', 'use_handwerk_standard', 'use_seasonal_adjustments', 'updated_at')
    search_fields = ('user__username', 'user__email', 'handwerk_template__name')
    readonly_fields = ('created_at', 'updated_at', 'user')

    fieldsets = (
        ('Company Info', {
            'fields': ('user',),
            'description': 'User/company linked to this configuration'
        }),
        ('Pricing Configuration', {
            'fields': ('stundensatz_arbeit', 'betriebskosten_umlage', 'gewinnmarge_prozent'),
            'description': 'Labor rate, overhead allocation, and profit margin'
        }),
        ('TIER 1: Global Standards', {
            'fields': ('handwerk_template', 'use_handwerk_standard'),
            'description': 'Enable/disable wood types, finishes, and complexity factors'
        }),
        ('TIER 2: Custom Materials', {
            'fields': ('use_custom_materials',),
            'description': 'Enable custom material list (overrides global materials)'
        }),
        ('TIER 3: Dynamic Adjustments', {
            'fields': ('use_seasonal_adjustments', 'use_customer_discounts', 'use_bulk_discounts'),
            'description': 'Enable seasonal campaigns, customer discounts, and bulk pricing'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_company_name(self, obj):
        """Display company/user name."""
        return obj.user.get_full_name() or obj.user.username
    get_company_name.short_description = 'Company'

    def status_badge(self, obj):
        """Display active/inactive status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 2px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #E74C3C; color: white; padding: 3px 8px; '
            'border-radius: 2px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        """Prevent duplicate creation - use signals to auto-create."""
        return False


@admin.register(MateriallistePosition)
class MateriallistePositionAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    """Admin for material catalog management with bulk upload support."""

    # Bulk upload configuration
    bulk_upload_model_type = 'material'
    bulk_upload_user_specific = True

    form = MateriallistePositionAdminForm
    list_display = ('material_name', 'sku', 'get_company', 'standardkosten_eur', 'lieferant', 'status_badge')
    list_filter = ('is_enabled', 'lieferant', 'verfuegbarkeit', 'created_at')
    search_fields = ('material_name', 'sku', 'lieferant', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Material Info', {
            'fields': ('user', 'material_name', 'sku')
        }),
        ('Supplier', {
            'fields': ('lieferant', 'standardkosten_eur', 'verpackungseinheit', 'verfuegbarkeit')
        }),
        ('Bulk Discounts', {
            'fields': ('rabatt_ab_100', 'rabatt_ab_500'),
            'description': 'Discount percentages at quantity thresholds'
        }),
        ('Status', {
            'fields': ('is_enabled',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_company(self, obj):
        """Display company/user name."""
        return obj.user.username
    get_company.short_description = 'Company'

    def status_badge(self, obj):
        """Display enabled/disabled status."""
        if obj.is_enabled:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 2px;">Available</span>'
            )
        return format_html(
            '<span style="background-color: #E74C3C; color: white; padding: 3px 8px; '
            'border-radius: 2px;">Disabled</span>'
        )
    status_badge.short_description = 'Status'

    def get_readonly_fields(self, request, obj=None):
        """Make SKU readonly after creation."""
        if obj:
            return self.readonly_fields + ('sku', 'user')
        return self.readonly_fields


# TIER 3: Dynamic Adjustments
# ============================================================================


@admin.register(SaisonaleMarge)
class SaisonaleMargeAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    """Admin for seasonal pricing adjustments and campaigns with bulk upload support."""

    # Bulk upload configuration
    bulk_upload_model_type = 'saisonal'
    bulk_upload_user_specific = True

    form = SaisonaleMargeAdminForm
    list_display = ('name', 'get_company', 'adjustment_display', 'date_range', 'status_badge')
    list_filter = ('is_active', 'adjustment_type', 'applicable_to', 'start_date', 'end_date')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'is_current_display')
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Campaign Info', {
            'fields': ('user', 'name', 'description')
        }),
        ('Adjustment', {
            'fields': ('adjustment_type', 'value'),
            'description': 'Percentage (%) or absolute amount (EUR)'
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date', 'is_current_display')
        }),
        ('Applicability', {
            'fields': ('applicable_to',),
            'description': 'Which customers/projects qualify'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_company(self, obj):
        """Display company/user name."""
        return obj.user.username
    get_company.short_description = 'Company'

    def adjustment_display(self, obj):
        """Display adjustment value with unit."""
        unit = '%' if obj.adjustment_type == 'prozent' else '€'
        return f"{obj.value}{unit}"
    adjustment_display.short_description = 'Adjustment'

    def date_range(self, obj):
        """Display date range."""
        return f"{obj.start_date} - {obj.end_date}"
    date_range.short_description = 'Date Range'

    def status_badge(self, obj):
        """Display active/inactive status."""
        if obj.is_active:
            color = '#27AE60' if obj.is_current() else '#F39C12'
            status = 'Active (Current)' if obj.is_current() else 'Active (Pending)'
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 2px;">{}</span>',
                color,
                status
            )
        return format_html(
            '<span style="background-color: #95A5A6; color: white; padding: 3px 8px; '
            'border-radius: 2px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'

    def is_current_display(self, obj):
        """Show if campaign is currently active."""
        if obj.is_current():
            return format_html(
                '<span style="color: #27AE60; font-weight: bold;">Yes, active now</span>'
            )
        return 'No'
    is_current_display.short_description = 'Currently Active?'


# DSGVO: Admin Audit Trail
# ============================================================================


@admin.register(AdminActionAudit)
class AdminActionAuditAdmin(admin.ModelAdmin):
    """Read-only admin for audit trail (DSGVO compliance)."""

    list_display = ('action_badge', 'admin_user', 'get_affected_user', 'timestamp', 'status_badge')
    list_filter = ('action_type', 'status', 'timestamp', 'admin_user')
    search_fields = ('admin_user__username', 'affected_user__username', 'reasoning')
    readonly_fields = (
        'id', 'admin_user', 'affected_user', 'action_type', 'old_value', 'new_value',
        'affected_documents', 'reasoning', 'status', 'status_changed_by', 'status_changed_at',
        'status_reason', 'timestamp', 'retention_until'
    )
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Admin Action', {
            'fields': ('admin_user', 'action_type', 'timestamp')
        }),
        ('Affected User/Entity', {
            'fields': ('affected_user', 'affected_documents')
        }),
        ('Change Details', {
            'fields': ('old_value', 'new_value', 'reasoning'),
            'description': 'What changed and why'
        }),
        ('Approval Status', {
            'fields': ('status', 'status_changed_by', 'status_changed_at', 'status_reason')
        }),
        ('DSGVO Compliance', {
            'fields': ('retention_until',),
            'description': 'Record will be deleted after this date per DSGVO Art. 17'
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual audit creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superuser can delete, and only if retention date passed."""
        return False

    def has_change_permission(self, request, obj=None):
        """Only change status for pending approvals."""
        return request.user.is_staff

    def get_affected_user(self, obj):
        """Display affected user or GLOBAL."""
        return obj.affected_user.username if obj.affected_user else "GLOBAL"
    get_affected_user.short_description = 'Affected User'

    def action_badge(self, obj):
        """Display action type as badge."""
        colors = {
            'template_create': '#3498DB',
            'template_update': '#3498DB',
            'template_delete': '#E74C3C',
            'holzart_enable': '#27AE60',
            'holzart_disable': '#E74C3C',
            'holzart_update': '#F39C12',
            'material_add': '#27AE60',
            'material_update': '#F39C12',
            'material_remove': '#E74C3C',
            'seasonal_create': '#27AE60',
            'seasonal_update': '#F39C12',
            'seasonal_delete': '#E74C3C',
            'pattern_fix_apply': '#9B59B6',
            'confidence_threshold_update': '#F39C12',
            'field_weight_update': '#F39C12',
        }
        color = colors.get(obj.action_type, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            obj.get_action_type_display()
        )
    action_badge.short_description = 'Action'

    def status_badge(self, obj):
        """Display approval status."""
        colors = {
            'pending': '#F39C12',
            'applied': '#27AE60',
            'reverted': '#3498DB',
            'rejected': '#E74C3C',
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ============================================================================
# PATTERN ANALYSIS ADMIN INTERFACE - Phase 3
# ============================================================================


@admin.register(ExtractionFailurePattern)
class ExtractionFailurePatternAdmin(admin.ModelAdmin):
    """Admin for ExtractionFailurePattern - detected extraction issues."""

    form = ExtractionFailurePatternAdminForm
    list_display = (
        'field_name',
        'severity_badge',
        'pattern_type',
        'affected_document_count',
        'total_occurrences',
        'is_reviewed_badge',
        'created_at_display'
    )
    list_filter = (
        'severity',
        'pattern_type',
        'is_reviewed',
        'is_active',
        'detected_at',
        'user'
    )
    search_fields = ('field_name', 'root_cause', 'user__username')
    readonly_fields = (
        'id',
        'detected_at',
        'last_updated',
        'affected_document_count',
        'total_occurrences'
    )
    date_hierarchy = 'detected_at'

    fieldsets = (
        ('Pattern Identification', {
            'fields': ('field_name', 'pattern_type', 'root_cause')
        }),
        ('Severity & Metrics', {
            'fields': (
                'severity',
                'confidence_threshold',
                'affected_document_count',
                'total_occurrences'
            )
        }),
        ('Pattern Data', {
            'fields': ('example_documents', 'suggested_fix')
        }),
        ('Review Status', {
            'fields': ('is_reviewed', 'reviewed_at', 'reviewed_by', 'is_active')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
        ('Metadata', {
            'fields': ('id', 'user', 'detected_at', 'last_updated', 'resolution_deadline'),
            'classes': ('collapse',)
        }),
    )

    def severity_badge(self, obj):
        """Display severity as colored badge."""
        colors = {
            'CRITICAL': '#E74C3C',
            'HIGH': '#E67E22',
            'MEDIUM': '#F39C12',
            'LOW': '#95A5A6',
        }
        color = colors.get(obj.severity, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Severity'

    def is_reviewed_badge(self, obj):
        """Display review status as badge."""
        color = '#27AE60' if obj.is_reviewed else '#95A5A6'
        status_text = 'Reviewed' if obj.is_reviewed else 'Pending'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            status_text
        )
    is_reviewed_badge.short_description = 'Review Status'

    def created_at_display(self, obj):
        """Display creation date."""
        return obj.detected_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = 'Detected'

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation."""
        if obj:
            return self.readonly_fields + ('field_name', 'pattern_type', 'root_cause')
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete patterns."""
        return request.user.is_superuser


@admin.register(PatternReviewSession)
class PatternReviewSessionAdmin(admin.ModelAdmin):
    """Admin for PatternReviewSession - tracking admin reviews."""

    form = PatternReviewSessionAdminForm
    list_display = (
        'title',
        'status_badge',
        'pattern_summary',
        'approval_rate_display',
        'estimated_impact_badge',
        'created_at_display'
    )
    list_filter = (
        'status',
        'estimated_impact',
        'created_at',
        'admin_user'
    )
    search_fields = ('title', 'description', 'admin_user__username')
    readonly_fields = (
        'id',
        'pattern',
        'admin_user',
        'created_at',
        'approval_rate_display_calc'
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Review Session Info', {
            'fields': ('title', 'status', 'pattern', 'admin_user')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Review Metrics', {
            'fields': (
                'reviewed_cases_count',
                'approved_cases',
                'approval_rate_display_calc'
            )
        }),
        ('Impact Assessment', {
            'fields': (
                'estimated_impact',
                'estimated_documents_improved'
            )
        }),
        ('Rejection Details', {
            'fields': ('rejection_reason',),
            'classes': ('collapse',)
        }),
        ('Timeline', {
            'fields': ('created_at', 'completed_at', 'scheduled_deployment')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'draft': '#95A5A6',
            'in_progress': '#3498DB',
            'approved': '#27AE60',
            'rejected': '#E74C3C',
            'applied': '#9B59B6',
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def pattern_summary(self, obj):
        """Display pattern field name and type."""
        return f"{obj.pattern.field_name} ({obj.pattern.get_pattern_type_display()})"
    pattern_summary.short_description = 'Pattern'

    def approval_rate_display(self, obj):
        """Display approval rate as percentage."""
        rate = obj.approval_rate * 100
        return f"{rate:.1f}%"
    approval_rate_display.short_description = 'Approval Rate'

    def approval_rate_display_calc(self, obj):
        """Calculated approval rate for readonly display."""
        rate = obj.approval_rate * 100
        return f"{rate:.1f}% ({obj.approved_cases}/{obj.reviewed_cases_count})"
    approval_rate_display_calc.short_description = 'Approval Rate'

    def estimated_impact_badge(self, obj):
        """Display impact assessment as badge."""
        colors = {
            'low': '#95A5A6',
            'medium': '#F39C12',
            'high': '#E74C3C',
        }
        color = colors.get(obj.estimated_impact, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            obj.get_estimated_impact_display()
        )
    estimated_impact_badge.short_description = 'Impact'

    def created_at_display(self, obj):
        """Display creation date."""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = 'Created'

    def get_readonly_fields(self, request, obj=None):
        """Restrict edits for completed reviews."""
        if obj and obj.status in ['applied', 'rejected']:
            # All fields readonly for completed reviews
            return [
                'id', 'pattern', 'admin_user', 'created_at',
                'title', 'status', 'description', 'reviewed_cases_count',
                'approved_cases', 'estimated_impact', 'estimated_documents_improved',
                'completed_at', 'scheduled_deployment', 'approval_rate_display_calc'
            ]
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete review sessions."""
        return request.user.is_superuser


@admin.register(PatternFixProposal)
class PatternFixProposalAdmin(admin.ModelAdmin):
    """Admin for PatternFixProposal - proposed fixes for patterns."""

    form = PatternFixProposalAdminForm
    list_display = (
        'title',
        'status_badge',
        'fix_type',
        'field_summary',
        'test_success_badge',
        'is_ready_to_deploy_badge',
        'created_at_display'
    )
    list_filter = (
        'status',
        'fix_type',
        'created_at',
        'deployed_by'
    )
    search_fields = ('title', 'description', 'affected_field')
    readonly_fields = (
        'id',
        'pattern',
        'review_session',
        'created_at',
        'is_ready_to_deploy_display'
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Fix Proposal Info', {
            'fields': ('title', 'status', 'fix_type')
        }),
        ('Pattern & Context', {
            'fields': ('pattern', 'review_session', 'affected_field', 'description')
        }),
        ('Changes', {
            'fields': ('change_details',)
        }),
        ('Testing & Validation', {
            'fields': (
                'test_sample_size',
                'test_success_rate',
                'validation_notes',
                'is_ready_to_deploy_display'
            )
        }),
        ('Deployment', {
            'fields': (
                'confidence_score',
                'deployed_at',
                'deployed_by'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'proposed': '#3498DB',
            'testing': '#F39C12',
            'validated': '#27AE60',
            'deployed': '#9B59B6',
            'rolled_back': '#E74C3C',
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def field_summary(self, obj):
        """Display affected field."""
        return obj.affected_field
    field_summary.short_description = 'Field'

    def test_success_badge(self, obj):
        """Display test success rate as badge."""
        if obj.test_success_rate is None:
            return format_html(
                '<span style="background-color: #95A5A6; color: white; padding: 3px 8px; '
                'border-radius: 2px;">Not Tested</span>'
            )
        rate = obj.test_success_rate * 100
        color = '#27AE60' if rate >= 85 else '#F39C12' if rate >= 70 else '#E74C3C'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{:.1f}%</span>',
            color,
            rate
        )
    test_success_badge.short_description = 'Test Rate'

    def is_ready_to_deploy_badge(self, obj):
        """Display deployment readiness."""
        ready = obj.is_ready_to_deploy
        color = '#27AE60' if ready else '#95A5A6'
        text = 'Ready' if ready else 'Not Ready'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 2px;">{}</span>',
            color,
            text
        )
    is_ready_to_deploy_badge.short_description = 'Ready to Deploy'

    def is_ready_to_deploy_display(self, obj):
        """Display deployment readiness with details."""
        ready = obj.is_ready_to_deploy
        details = []
        if obj.status != 'validated':
            details.append(f"Status: {obj.get_status_display()} (need: validated)")
        if obj.test_success_rate is None:
            details.append("Test success rate: Not tested (need: ≥85%)")
        elif obj.test_success_rate < Decimal('0.85'):
            details.append(f"Test rate: {obj.test_success_rate*100:.1f}% (need: ≥85%)")
        if obj.confidence_score < Decimal('0.80'):
            details.append(f"Confidence: {obj.confidence_score*100:.1f}% (need: ≥80%)")

        status = 'READY TO DEPLOY' if ready else 'NOT READY TO DEPLOY'
        if details:
            status += '<br/>' + '<br/>'.join(details)
        return format_html(status)
    is_ready_to_deploy_display.short_description = 'Deployment Status'

    def created_at_display(self, obj):
        """Display creation date."""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = 'Created'

    def get_readonly_fields(self, request, obj=None):
        """Restrict edits for deployed/rolled_back fixes."""
        if obj and obj.status in ['deployed', 'rolled_back']:
            return self.readonly_fields + [
                'title', 'fix_type', 'affected_field', 'description',
                'change_details', 'confidence_score', 'status'
            ]
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete proposals."""
        return request.user.is_superuser


# =============================================================================
# PHASE 4A: Transparency & Explainability Admin
# =============================================================================


class CalculationFactorInline(admin.TabularInline):
    """Inline display of calculation factors."""
    model = CalculationFactor
    extra = 0
    fields = ['display_order', 'factor_name', 'amount_eur', 'impact_percent', 'explanation_text', 'data_source', 'is_adjustable']
    readonly_fields = ['display_order', 'impact_percent']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Factors are auto-generated, no manual adding."""
        return False


@admin.register(CalculationExplanation)
class CalculationExplanationAdmin(admin.ModelAdmin):
    """Admin interface for transparent calculation explanations."""

    form = CalculationExplanationAdminForm
    list_display = [
        'document_name',
        'confidence_badge',
        'total_price_display',
        'deviation_badge',
        'similar_projects_count',
        'created_at_display'
    ]
    list_filter = ['confidence_level', 'created_at']
    search_fields = ['extraction_result__document__original_filename']
    readonly_fields = ['created_at', 'extraction_result']
    inlines = [CalculationFactorInline]
    date_hierarchy = 'created_at'

    fieldsets = [
        ('Dokument', {
            'fields': ['extraction_result']
        }),
        ('Kalkulation', {
            'fields': ['total_price_eur', 'confidence_level', 'confidence_score']
        }),
        ('Vergleich mit Nutzer-Historie', {
            'fields': [
                'similar_projects_count',
                'user_average_for_type',
                'deviation_from_average_percent'
            ],
            'description': 'Vergleich dieser Kalkulation mit bisherigen Projekten des Nutzers'
        }),
        ('Metadaten', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]

    def document_name(self, obj):
        """Display document filename."""
        return obj.extraction_result.document.original_filename
    document_name.short_description = 'Dokument'

    def confidence_badge(self, obj):
        """Visual confidence indicator (Ampelsystem)."""
        colors = {'high': '#28a745', 'medium': '#ffc107', 'low': '#dc3545'}
        color = colors.get(obj.confidence_level, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_confidence_level_display()
        )
    confidence_badge.short_description = 'Konfidenz'

    def total_price_display(self, obj):
        """Format total price."""
        return f"{obj.total_price_eur:,.2f} €".replace(',', '.')
    total_price_display.short_description = 'Gesamtpreis'

    def deviation_badge(self, obj):
        """Visual deviation indicator."""
        if not obj.deviation_from_average_percent:
            return format_html('<span style="color: #6c757d;">-</span>')

        dev = float(obj.deviation_from_average_percent)
        if abs(dev) > 15:
            color = '#dc3545'  # Red - significant deviation
        elif abs(dev) > 5:
            color = '#ffc107'  # Yellow - moderate deviation
        else:
            color = '#28a745'  # Green - within range

        symbol = '↑' if dev > 0 else '↓' if dev < 0 else '='

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {:+.1f}%</span>',
            color, symbol, dev
        )
    deviation_badge.short_description = 'Abweichung'

    def created_at_display(self, obj):
        """Format created timestamp."""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = 'Erstellt am'

    def has_add_permission(self, request):
        """Explanations are auto-generated, no manual adding."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete explanations (DSGVO retention)."""
        return request.user.is_superuser


@admin.register(UserProjectBenchmark)
class UserProjectBenchmarkAdmin(admin.ModelAdmin):
    """Admin interface for user project benchmarks."""

    form = UserProjectBenchmarkAdminForm
    list_display = [
        'user',
        'project_type',
        'total_projects',
        'average_price_display',
        'price_range_display',
        'average_margin_display',
        'last_calculated_display'
    ]
    list_filter = ['user', 'project_type']
    search_fields = ['user__username', 'project_type']
    readonly_fields = ['last_calculated', 'created_at']
    date_hierarchy = 'last_calculated'

    fieldsets = [
        ('Projekt', {
            'fields': ['user', 'project_type']
        }),
        ('Statistiken', {
            'fields': [
                'total_projects',
                'average_price_eur',
                'min_price_eur',
                'max_price_eur',
                'average_margin_percent'
            ],
            'description': 'Aggregierte Statistiken basierend auf abgeschlossenen Projekten'
        }),
        ('Metadaten', {
            'fields': ['last_calculated', 'created_at'],
            'classes': ['collapse']
        }),
    ]

    def average_price_display(self, obj):
        """Format average price."""
        return f"{obj.average_price_eur:,.2f} €".replace(',', '.')
    average_price_display.short_description = 'Ø Preis'

    def price_range_display(self, obj):
        """Display price range."""
        min_price = f"{obj.min_price_eur:,.2f}".replace(',', '.')
        max_price = f"{obj.max_price_eur:,.2f}".replace(',', '.')
        return f"{min_price} € - {max_price} €"
    price_range_display.short_description = 'Preisspanne'

    def average_margin_display(self, obj):
        """Format average margin."""
        return f"{obj.average_margin_percent:.1f}%"
    average_margin_display.short_description = 'Ø Marge'

    def last_calculated_display(self, obj):
        """Format last calculated timestamp."""
        return obj.last_calculated.strftime('%d.%m.%Y %H:%M')
    last_calculated_display.short_description = 'Zuletzt aktualisiert'

    def has_add_permission(self, request):
        """Benchmarks are auto-generated, no manual adding."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete benchmarks."""
        return request.user.is_superuser


# Import Pauschalen Admin (Phase 4C)
from .admin_pauschalen import BetriebspauschaleRegelAdmin, PauschaleAnwendungAdmin
