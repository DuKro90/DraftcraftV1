"""
Configuration API Serializers - Phase 4D

Serializers for configuration endpoints (TIER 1 factors, TIER 2 company metrics).
"""
from rest_framework import serializers
from documents.betriebskennzahl_models import (
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
)


class HolzartConfigSerializer(serializers.ModelSerializer):
    """
    Holzart (wood type) configuration.

    GET /api/v1/config/holzarten/
    """

    class Meta:
        model = HolzartKennzahl
        fields = [
            'id',
            'holzart',
            'display_name',
            'preis_faktor',
            'kategorie',
            'beschreibung',
            'is_enabled',
        ]
        read_only_fields = ['id']


class OberflächenConfigSerializer(serializers.ModelSerializer):
    """
    Oberflächenbearbeitung (surface finish) configuration.

    GET /api/v1/config/oberflaechen/
    """

    class Meta:
        model = OberflächenbearbeitungKennzahl
        fields = [
            'id',
            'bearbeitung',
            'display_name',
            'preis_faktor',
            'zeit_faktor',
            'kategorie',
            'beschreibung',
            'is_enabled',
        ]
        read_only_fields = ['id']


class KomplexitaetConfigSerializer(serializers.ModelSerializer):
    """
    Komplexität (complexity/technique) configuration.

    GET /api/v1/config/komplexitaet/
    """

    schwierigkeitsgrad_display = serializers.CharField(
        source='get_schwierigkeitsgrad_display',
        read_only=True
    )

    class Meta:
        model = KomplexitaetKennzahl
        fields = [
            'id',
            'technik',
            'display_name',
            'preis_faktor',
            'zeit_faktor',
            'schwierigkeitsgrad',
            'schwierigkeitsgrad_display',
            'kategorie',
            'beschreibung',
            'is_enabled',
        ]
        read_only_fields = ['id', 'schwierigkeitsgrad_display']


class BetriebskennzahlConfigSerializer(serializers.ModelSerializer):
    """
    Individuelle Betriebskennzahl (company-specific metrics) configuration.

    GET /api/v1/config/betriebskennzahlen/
    PATCH /api/v1/config/betriebskennzahlen/
    """

    template_name = serializers.CharField(
        source='handwerk_template.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = IndividuelleBetriebskennzahl
        fields = [
            'id',
            'template_name',
            'stundensatz_arbeit',
            'gewinnmarge_prozent',
            'betriebskosten_umlage',
            'use_handwerk_standard',
            'use_custom_materials',
            'use_seasonal_adjustments',
            'use_customer_discounts',
            'use_bulk_discounts',
            'is_active',
            'updated_at',
        ]
        read_only_fields = ['id', 'template_name', 'updated_at']

    def validate_stundensatz_arbeit(self, value):
        """Validate hourly rate is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Stundensatz muss größer als 0 sein."
            )
        return value

    def validate_gewinnmarge_prozent(self, value):
        """Validate profit margin is reasonable."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Gewinnmarge muss zwischen 0 und 100 Prozent liegen."
            )
        return value


class BetriebskennzahlUpdateSerializer(serializers.Serializer):
    """
    Update serializer for Betriebskennzahl (partial updates allowed).

    PATCH /api/v1/config/betriebskennzahlen/
    {
        "stundensatz_arbeit": 75.00,
        "gewinnmarge_prozent": 25.0,
        "use_seasonal_adjustments": true
    }
    """

    stundensatz_arbeit = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        help_text="Hourly labor rate in EUR"
    )
    gewinnmarge_prozent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        help_text="Profit margin percentage (0-100)"
    )
    betriebskosten_umlage = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Overhead allocation per project in EUR"
    )
    use_handwerk_standard = serializers.BooleanField(
        required=False,
        help_text="Enable TIER 1 global standards (holzart, oberflaeche, komplexitaet)"
    )
    use_custom_materials = serializers.BooleanField(
        required=False,
        help_text="Use custom material price list"
    )
    use_seasonal_adjustments = serializers.BooleanField(
        required=False,
        help_text="Enable seasonal/campaign pricing adjustments"
    )
    use_customer_discounts = serializers.BooleanField(
        required=False,
        help_text="Enable customer tier discounts"
    )
    use_bulk_discounts = serializers.BooleanField(
        required=False,
        help_text="Enable bulk order discounts"
    )

    def validate_stundensatz_arbeit(self, value):
        """Validate hourly rate is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Stundensatz muss größer als 0 EUR sein."
            )
        return value

    def validate_gewinnmarge_prozent(self, value):
        """Validate profit margin is reasonable."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Gewinnmarge muss zwischen 0 und 100 Prozent liegen."
            )
        return value
