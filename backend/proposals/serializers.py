"""Serializers for proposal models."""
from rest_framework import serializers
from .models import Proposal, ProposalLine, ProposalTemplate, ProposalCalculationLog


class ProposalLineSerializer(serializers.ModelSerializer):
    """Serializer for ProposalLine model."""

    class Meta:
        model = ProposalLine
        fields = (
            'id',
            'position',
            'description',
            'quantity',
            'unit',
            'unit_price',
            'discount_percent',
            'total',
        )
        read_only_fields = ('id', 'total')


class ProposalDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Proposal with line items."""

    lines = ProposalLineSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_name = serializers.CharField(source='document.original_filename', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    total_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
            'id',
            'proposal_number',
            'document_name',
            'template_name',
            'status',
            'status_display',
            'customer_name',
            'customer_address',
            'customer_email',
            'subtotal',
            'tax_amount',
            'total',
            'total_formatted',
            'lines',
            'valid_until',
            'notes',
            'terms',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'proposal_number',
            'document_name',
            'status_display',
            'subtotal',
            'tax_amount',
            'total',
            'created_at',
            'updated_at',
        )

    def get_total_formatted(self, obj):
        """Format total with currency."""
        if obj.template:
            return obj.template.format_price(obj.total)
        return f"{obj.total} EUR"


class ProposalListSerializer(serializers.ModelSerializer):
    """List serializer for Proposal (minimal fields)."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_name = serializers.CharField(source='document.original_filename', read_only=True)
    total_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
            'id',
            'proposal_number',
            'document_name',
            'status',
            'status_display',
            'customer_name',
            'total',
            'total_formatted',
            'valid_until',
            'created_at',
        )
        read_only_fields = fields

    def get_total_formatted(self, obj):
        """Format total with currency."""
        if obj.template:
            return obj.template.format_price(obj.total)
        return f"{obj.total} EUR"


class ProposalTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ProposalTemplate model."""

    class Meta:
        model = ProposalTemplate
        fields = (
            'id',
            'name',
            'description',
            'hourly_rate',
            'profit_margin_percent',
            'overhead_factor',
            'tax_rate_percent',
            'currency',
            'decimal_separator',
            'thousand_separator',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class ProposalCalculationLogSerializer(serializers.ModelSerializer):
    """Serializer for ProposalCalculationLog model."""

    proposal_number = serializers.CharField(source='proposal.proposal_number', read_only=True)

    class Meta:
        model = ProposalCalculationLog
        fields = (
            'id',
            'proposal_number',
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
        read_only_fields = fields


class ProposalCreateSerializer(serializers.Serializer):
    """Serializer for creating proposal from document."""

    document_id = serializers.CharField()
    template_id = serializers.IntegerField(required=False, allow_null=True)
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    valid_days = serializers.IntegerField(default=30, min_value=1)

    def validate_document_id(self, value):
        """Validate document exists."""
        from documents.models import Document
        try:
            Document.objects.get(id=value)
        except Document.DoesNotExist:
            raise serializers.ValidationError("Document not found")
        return value


class ProposalUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating proposal."""

    class Meta:
        model = Proposal
        fields = (
            'customer_name',
            'customer_address',
            'customer_email',
            'notes',
            'terms',
            'valid_until',
            'status',
        )


class ProposalSendSerializer(serializers.Serializer):
    """Serializer for sending proposal via email."""

    recipient_email = serializers.EmailField()
    message = serializers.CharField(required=False, allow_blank=True)


class ProposalExportSerializer(serializers.Serializer):
    """Serializer for exporting proposal."""

    format = serializers.ChoiceField(choices=['pdf', 'csv', 'json'])
    include_calculation_logs = serializers.BooleanField(default=False)
