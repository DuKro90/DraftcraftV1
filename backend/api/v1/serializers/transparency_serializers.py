"""
Transparency & Explanation API Serializers - Phase 4D

Serializers for AI transparency endpoints (Phase 4A models).
"""
from rest_framework import serializers
from documents.transparency_models import (
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark,
)


class CalculationFactorSerializer(serializers.ModelSerializer):
    """
    Individual calculation factor used in explanation.
    """

    class Meta:
        model = CalculationFactor
        fields = [
            'id',
            'factor_name',
            'factor_category',
            'amount_eur',
            'impact_percent',
            'explanation_text',
            'data_source',
            'is_adjustable',
            'display_order',
        ]
        read_only_fields = ['id']


class CalculationExplanationSerializer(serializers.ModelSerializer):
    """
    Calculation explanation serializer.

    GET /api/v1/calculations/{id}/explanation/

    Returns AI-generated explanation for why a price was calculated.
    """

    faktoren = CalculationFactorSerializer(many=True, read_only=True, source='factors')
    tier_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = CalculationExplanation
        fields = [
            'id',
            'confidence_level',
            'confidence_score',
            'total_price_eur',
            'similar_projects_count',
            'user_average_for_type',
            'deviation_from_average_percent',
            'faktoren',
            'tier_breakdown',
            'created_at',
        ]
        read_only_fields = fields

    def get_tier_breakdown(self, obj):
        """
        Calculate TIER breakdown from factors by aggregating amounts per data_source.
        """
        from django.db.models import Sum

        # Aggregate factors by data_source
        tier1 = obj.factors.filter(data_source='tier1_global').aggregate(
            total=Sum('amount_eur')
        )['total'] or 0

        tier2 = obj.factors.filter(data_source='tier2_company').aggregate(
            total=Sum('amount_eur')
        )['total'] or 0

        tier3 = obj.factors.filter(data_source='tier3_dynamic').aggregate(
            total=Sum('amount_eur')
        )['total'] or 0

        user_history = obj.factors.filter(data_source='user_history').aggregate(
            total=Sum('amount_eur')
        )['total'] or 0

        return {
            'tier1_contribution': float(tier1),
            'tier2_contribution': float(tier2),
            'tier3_contribution': float(tier3),
            'user_history_contribution': float(user_history),
        }


class UserBenchmarkSerializer(serializers.ModelSerializer):
    """
    User project benchmark serializer.

    GET /api/v1/benchmarks/user/

    Returns user's historical project data for comparison.
    """

    # Map frontend field names to backend model fields
    projekttyp = serializers.CharField(source='project_type', read_only=True)
    durchschnittspreis_eur = serializers.DecimalField(
        source='average_price_eur',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    median_preis_eur = serializers.SerializerMethodField()
    anzahl_projekte = serializers.IntegerField(source='total_projects', read_only=True)
    letztes_projekt_datum = serializers.DateTimeField(source='last_calculated', read_only=True)
    durchschnitt_abweichung_prozent = serializers.DecimalField(
        source='average_margin_percent',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = UserProjectBenchmark
        fields = [
            'id',
            'projekttyp',
            'durchschnittspreis_eur',
            'median_preis_eur',
            'min_preis_eur',
            'max_preis_eur',
            'anzahl_projekte',
            'letztes_projekt_datum',
            'durchschnitt_abweichung_prozent',
            'created_at',
        ]
        read_only_fields = fields

    def get_median_preis_eur(self, obj):
        """
        Calculate median price from user's project history.
        """
        from documents.models import ExtractionResult
        from statistics import median

        # Get all calculated prices for this project type
        prices = ExtractionResult.objects.filter(
            document__user=obj.user,
            extracted_data__has_key='projekttyp',
            extracted_data__has_key='calculated_price'
        ).filter(
            extracted_data__projekttyp=obj.project_type
        ).values_list('extracted_data__calculated_price', flat=True)

        # Convert to list of Decimals, filtering out None values
        price_list = []
        for price in prices:
            if price is not None:
                try:
                    price_list.append(float(price))
                except (ValueError, TypeError):
                    continue

        # Calculate median or return average as fallback
        if len(price_list) >= 2:
            return median(price_list)
        else:
            return obj.average_price_eur


class CalculationFeedbackSerializer(serializers.Serializer):
    """
    Serializer for submitting feedback on calculation.

    POST /api/v1/feedback/calculation/
    {
        "extraction_result_id": "uuid",
        "calculation_id": "uuid",
        "feedback_type": "zu_hoch",
        "erwarteter_preis_eur": 3500.00,
        "kommentare": "Preis scheint 20% zu hoch für diese Komplexität"
    }
    """

    extraction_result_id = serializers.UUIDField(
        help_text="ID of the ExtractionResult this feedback is for"
    )
    calculation_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID of the CalculationExplanation (if exists)"
    )
    feedback_type = serializers.ChoiceField(
        choices=[
            ('zu_hoch', 'Preis zu hoch'),
            ('zu_niedrig', 'Preis zu niedrig'),
            ('genau_richtig', 'Preis genau richtig'),
            ('faktor_fehlt', 'Wichtiger Faktor fehlt'),
            ('faktor_falsch', 'Faktor falsch angewendet'),
            ('sonstiges', 'Sonstiges Feedback'),
        ],
        help_text="Type of feedback"
    )
    erwarteter_preis_eur = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Expected price in EUR (optional)"
    )
    kommentare = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional comments"
    )
    faktoren_bewertung = serializers.JSONField(
        required=False,
        help_text="Rating of individual factors (optional): {factor_id: rating_1_5}"
    )

    def validate_erwarteter_preis_eur(self, value):
        """Validate expected price is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Erwarteter Preis muss größer als 0 EUR sein."
            )
        return value


class CalculationComparisonSerializer(serializers.Serializer):
    """
    Serializer for comparing calculation with benchmark.

    GET /api/v1/calculations/{id}/compare-benchmark/

    Returns:
    {
        "current_price_eur": 4500.00,
        "benchmark_avg_eur": 3800.00,
        "difference_eur": 700.00,
        "difference_percent": 18.4,
        "is_above_average": true,
        "explanation": "Ihr Preis liegt 18% über dem Durchschnitt...",
        "factors_causing_difference": [...]
    }
    """

    current_price_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    benchmark_avg_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    difference_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    difference_percent = serializers.FloatField()
    is_above_average = serializers.BooleanField()
    explanation = serializers.CharField()
    factors_causing_difference = serializers.ListField(
        child=serializers.JSONField()
    )
    sample_size = serializers.IntegerField(
        help_text="Number of historical projects in benchmark"
    )


class ExplanationRegenerateSerializer(serializers.Serializer):
    """
    Serializer for regenerating calculation explanation.

    POST /api/v1/calculations/{id}/regenerate-explanation/
    {
        "include_benchmark": true,
        "detail_level": "detailed"
    }
    """

    include_benchmark = serializers.BooleanField(
        default=True,
        help_text="Include benchmark comparison in explanation"
    )
    detail_level = serializers.ChoiceField(
        choices=[
            ('summary', 'Zusammenfassung'),
            ('detailed', 'Detailliert'),
            ('technical', 'Technisch (mit Formeln)'),
        ],
        default='detailed',
        help_text="Level of detail for explanation"
    )
    language = serializers.ChoiceField(
        choices=[
            ('de', 'Deutsch'),
            ('en', 'English'),
        ],
        default='de',
        help_text="Language for explanation"
    )
