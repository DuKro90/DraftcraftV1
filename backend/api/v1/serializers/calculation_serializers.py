"""
Calculation API Serializers - Phase 4D

Serializers for pricing and calculation endpoints.
Supports CalculationEngine (8-step workflow) and Pauschalen integration.
"""
from rest_framework import serializers
from decimal import Decimal
from typing import Dict, Any


class PriceCalculationRequestSerializer(serializers.Serializer):
    """
    Request serializer for price calculation.

    POST /api/v1/calculate/price/
    {
        "extracted_data": {
            "holzart": "eiche",
            "oberflaeche": "lackieren",
            "komplexitaet": "hand_geschnitzt",
            "material_sku": "EICHE-25MM",
            "material_quantity": 10,
            "labor_hours": 40,
            "distanz_km": 25
        },
        "customer_type": "bestehende_kunden",
        "breakdown": true
    }
    """

    extracted_data = serializers.JSONField(
        help_text="Extracted document data with holzart, oberflaeche, komplexitaet, etc."
    )
    quantity = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Override quantity from extracted_data"
    )
    customer_type = serializers.ChoiceField(
        choices=[
            ('neue_kunden', 'Neue Kunden'),
            ('bestehende_kunden', 'Bestehende Kunden'),
            ('vip_kunden', 'VIP Kunden'),
            ('gross_kunden', 'Großkunden'),
        ],
        default='neue_kunden',
        help_text="Customer tier for discount calculation"
    )
    breakdown = serializers.BooleanField(
        default=True,
        help_text="Include detailed calculation breakdown in response"
    )
    extraction_result_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional: Link to ExtractionResult for Pauschalen context"
    )

    def validate_extracted_data(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted_data has minimum required fields."""
        required_fields = []  # Made flexible - engine handles missing fields

        # Validate numeric fields if present
        numeric_fields = ['material_quantity', 'labor_hours', 'distanz_km', 'material_cost_eur']
        for field in numeric_fields:
            if field in value:
                try:
                    Decimal(str(value[field]))
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        {field: f"Muss eine gültige Zahl sein. Erhalten: {value[field]}"}
                    )

        return value


class PriceBreakdownStepSerializer(serializers.Serializer):
    """Single calculation step in breakdown."""

    step_name = serializers.CharField()
    applied = serializers.BooleanField()
    price_before_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    price_after_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    details = serializers.JSONField(required=False)


class PauschaleItemSerializer(serializers.Serializer):
    """Single Pauschale applied to calculation."""

    regel_id = serializers.UUIDField()
    name = serializers.CharField()
    pauschale_typ = serializers.CharField()
    betrag_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    berechnungsart = serializers.CharField()
    details = serializers.JSONField(required=False)


class PriceBreakdownSerializer(serializers.Serializer):
    """Detailed breakdown of calculation steps."""

    step_1_base_material = serializers.JSONField(required=False)
    step_2_wood_type = serializers.JSONField(required=False)
    step_3_surface_finish = serializers.JSONField(required=False)
    step_4_complexity = serializers.JSONField(required=False)
    step_5_labor = serializers.JSONField(required=False)
    step_6_overhead_and_margin = serializers.JSONField(required=False)
    step_7_seasonal_adjustments = serializers.JSONField(required=False)
    step_8_customer_discounts = serializers.JSONField(required=False)
    multi_material_breakdown = serializers.JSONField(required=False)
    pauschalen_applied = PauschaleItemSerializer(many=True, required=False)


class PriceCalculationResponseSerializer(serializers.Serializer):
    """
    Response serializer for price calculation.

    Returns complete pricing with breakdown and Pauschalen.
    """

    # Transparency Integration (Phase 4A)
    calculation_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of CalculationExplanation for transparency features"
    )
    extraction_result_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of ExtractionResult for benchmark comparison"
    )

    # Pricing
    total_price_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Final total price including all adjustments and Pauschalen"
    )
    base_price_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Material cost before factors"
    )
    material_price_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Material cost after factors"
    )
    labor_price_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Labor cost"
    )
    final_price_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Price after all calculations (same as total_price_eur)"
    )
    pauschalen = serializers.JSONField(
        help_text="Applied Pauschalen (Anfahrt, Montage, etc.)"
    )
    breakdown = PriceBreakdownSerializer(
        required=False,
        help_text="Detailed calculation steps (if breakdown=true)"
    )
    warnings = serializers.ListField(
        child=serializers.CharField(),
        help_text="Warnings during calculation (e.g., missing factors)"
    )
    tiers_applied = serializers.JSONField(
        help_text="Which TIER 1/2/3 levels were used"
    )
    currency = serializers.CharField(default='EUR')
    calculated_at = serializers.DateTimeField(
        help_text="Timestamp of calculation"
    )


class MultiMaterialCalculationSerializer(serializers.Serializer):
    """
    Request serializer for multi-material calculation.

    POST /api/v1/calculate/multi-material/
    {
        "materials": [
            {
                "holzart": "eiche",
                "oberflaeche": "lackieren",
                "laenge_mm": 2000,
                "breite_mm": 800,
                "hoehe_mm": 25,
                "menge": 4
            },
            {
                "holzart": "buche",
                "oberflaeche": "oelen",
                "laenge_mm": 1500,
                "breite_mm": 600,
                "hoehe_mm": 18,
                "menge": 8
            }
        ],
        "customer_type": "bestehende_kunden"
    }
    """

    materials = serializers.ListField(
        child=serializers.JSONField(),
        min_length=1,
        help_text="List of materials with holzart, dimensions, oberflaeche"
    )
    customer_type = serializers.ChoiceField(
        choices=[
            ('neue_kunden', 'Neue Kunden'),
            ('bestehende_kunden', 'Bestehende Kunden'),
            ('vip_kunden', 'VIP Kunden'),
            ('gross_kunden', 'Großkunden'),
        ],
        default='neue_kunden'
    )
    breakdown = serializers.BooleanField(default=True)

    def validate_materials(self, value):
        """Validate each material has required fields."""
        required_fields = ['holzart', 'laenge_mm', 'breite_mm', 'hoehe_mm']

        for idx, material in enumerate(value):
            missing = [f for f in required_fields if f not in material]
            if missing:
                raise serializers.ValidationError(
                    f"Material {idx + 1} fehlt Pflichtfelder: {', '.join(missing)}"
                )

            # Validate numeric dimensions
            for field in ['laenge_mm', 'breite_mm', 'hoehe_mm']:
                if not isinstance(material.get(field), (int, float)) or material[field] <= 0:
                    raise serializers.ValidationError(
                        f"Material {idx + 1}: {field} muss eine positive Zahl sein"
                    )

        return value


class ApplicablePauschaleSerializer(serializers.Serializer):
    """
    Serializer for querying applicable Pauschalen.

    GET /api/v1/pauschalen/applicable/?auftragswert=5000&distanz_km=30

    Response includes all Pauschalen that would apply given context.
    """

    regel_id = serializers.UUIDField()
    name = serializers.CharField()
    pauschale_typ = serializers.CharField()
    berechnungsart = serializers.CharField()
    betrag_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    beschreibung = serializers.CharField()
    applies = serializers.BooleanField(
        help_text="Whether this Pauschale applies to given context"
    )
    calculated_amount_eur = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        required=False,
        help_text="Calculated amount if applies=true"
    )
    reason = serializers.CharField(
        required=False,
        help_text="Explanation why it applies or doesn't apply"
    )


class ApplicablePauschaleRequestSerializer(serializers.Serializer):
    """Request params for applicable Pauschalen query."""

    auftragswert = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Project value in EUR"
    )
    distanz_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        help_text="Distance in km"
    )
    montage_stunden = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        help_text="Installation hours"
    )
    material_menge = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Material quantity (m³, etc.)"
    )
