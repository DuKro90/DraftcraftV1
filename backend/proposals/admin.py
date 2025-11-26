"""Django admin for proposal models."""
from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import Proposal, ProposalLine, ProposalTemplate, ProposalCalculationLog


@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    """Admin for ProposalTemplate model."""

    list_display = ('name', 'hourly_rate_display', 'profit_margin_percent', 'tax_rate_percent', 'status_badge', 'updated_at')
    list_filter = ('is_active', 'currency', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Pricing Configuration', {
            'fields': ('hourly_rate', 'profit_margin_percent', 'overhead_factor', 'tax_rate_percent')
        }),
        ('Display Settings', {
            'fields': ('currency', 'decimal_separator', 'thousand_separator')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def hourly_rate_display(self, obj):
        """Display hourly rate with currency."""
        return f"{obj.hourly_rate}€/h"
    hourly_rate_display.short_description = 'Hourly Rate'

    def status_badge(self, obj):
        """Display active status as badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27AE60; color: white; padding: 3px 8px; '
                'border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #95A5A6; color: white; padding: 3px 8px; '
            'border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'


class ProposalLineInline(admin.TabularInline):
    """Inline editor for proposal lines."""

    model = ProposalLine
    fields = ('position', 'description', 'quantity', 'unit', 'unit_price', 'discount_percent', 'total')
    readonly_fields = ('total',)
    extra = 1

    def get_queryset(self, request):
        """Order by position."""
        return super().get_queryset(request).order_by('position')


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Admin for Proposal model."""

    list_display = ('proposal_number', 'document_name', 'status_badge', 'total_display', 'created_at', 'valid_until')
    list_filter = ('status', 'created_at', 'template__is_active')
    search_fields = ('proposal_number', 'document__original_filename', 'customer_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'subtotal', 'tax_amount', 'total')
    inlines = [ProposalLineInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Document & Template', {
            'fields': ('id', 'document', 'template')
        }),
        ('Proposal Info', {
            'fields': ('proposal_number', 'status')
        }),
        ('Customer', {
            'fields': ('customer_name', 'customer_address', 'customer_email')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'total')
        }),
        ('Validity & Terms', {
            'fields': ('valid_until', 'notes', 'terms'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def document_name(self, obj):
        """Display document filename."""
        return obj.document.original_filename if obj.document else "—"
    document_name.short_description = 'Document'

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'draft': '#95A5A6',
            'sent': '#3498DB',
            'accepted': '#27AE60',
            'rejected': '#E74C3C',
            'completed': '#F39C12',
        }
        color = colors.get(obj.status, '#95A5A6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def total_display(self, obj):
        """Display total with currency."""
        if obj.template:
            return obj.template.format_price(obj.total)
        return f"{obj.total} EUR"
    total_display.short_description = 'Total'

    def save_model(self, request, obj, form, change):
        """Recalculate totals before save."""
        obj.recalculate_totals()
        super().save_model(request, obj, form, change)


@admin.register(ProposalLine)
class ProposalLineAdmin(admin.ModelAdmin):
    """Admin for ProposalLine model."""

    list_display = ('proposal_number', 'position', 'description', 'quantity_display', 'unit_price_display', 'total_display')
    list_filter = ('unit', 'proposal__status', 'proposal__created_at')
    search_fields = ('proposal__proposal_number', 'description')
    readonly_fields = ('proposal', 'total')

    fieldsets = (
        ('Proposal', {
            'fields': ('proposal',)
        }),
        ('Item Info', {
            'fields': ('position', 'description')
        }),
        ('Quantity & Unit', {
            'fields': ('quantity', 'unit')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'discount_percent', 'total')
        }),
    )

    def proposal_number(self, obj):
        """Display proposal number."""
        return obj.proposal.proposal_number
    proposal_number.short_description = 'Proposal'

    def quantity_display(self, obj):
        """Display quantity with unit."""
        return f"{obj.quantity} {obj.unit}"
    quantity_display.short_description = 'Quantity'

    def unit_price_display(self, obj):
        """Display unit price with currency."""
        return f"{obj.unit_price}€"
    unit_price_display.short_description = 'Unit Price'

    def total_display(self, obj):
        """Display total with currency."""
        return f"{obj.total}€"
    total_display.short_description = 'Total'

    def save_model(self, request, obj, form, change):
        """Recalculate line total before save."""
        obj.total = obj.calculate_total()
        super().save_model(request, obj, form, change)

        # Recalculate proposal totals
        obj.proposal.recalculate_totals()
        obj.proposal.save()


@admin.register(ProposalCalculationLog)
class ProposalCalculationLogAdmin(admin.ModelAdmin):
    """Admin for ProposalCalculationLog model (read-only audit)."""

    list_display = ('material_type', 'quantity_unit', 'calculated_unit_price_display', 'complexity_factor', 'created_at')
    list_filter = ('material_type', 'quality_tier', 'created_at')
    search_fields = ('material_type', 'proposal__proposal_number')
    readonly_fields = (
        'proposal',
        'material_type',
        'quantity',
        'unit',
        'base_material_cost',
        'base_labor_hours',
        'labor_cost',
        'complexity_factor',
        'surface_factor',
        'quality_tier',
        'calculated_unit_price',
        'created_at',
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Proposal Reference', {
            'fields': ('proposal',)
        }),
        ('Input Data', {
            'fields': ('material_type', 'quantity', 'unit')
        }),
        ('Cost Breakdown', {
            'fields': ('base_material_cost', 'base_labor_hours', 'labor_cost')
        }),
        ('Factors Applied', {
            'fields': ('complexity_factor', 'surface_factor', 'quality_tier')
        }),
        ('Result', {
            'fields': ('calculated_unit_price', 'created_at')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion (audit trail)."""
        return False

    def quantity_unit(self, obj):
        """Display quantity with unit."""
        return f"{obj.quantity} {obj.unit}"
    quantity_unit.short_description = 'Quantity'

    def calculated_unit_price_display(self, obj):
        """Display calculated unit price."""
        return f"{obj.calculated_unit_price}€/{obj.unit}"
    calculated_unit_price_display.short_description = 'Calculated Unit Price'
