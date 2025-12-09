# -*- coding: utf-8 -*-
"""Transparency models for explainable calculations and user benchmarks.

Phase 4A: Transparenz & Benutzerfreundlichkeit
- CalculationExplanation: Transparent explanation of pricing calculations
- CalculationFactor: Individual factors contributing to price (material, labor, etc.)
- UserProjectBenchmark: User-specific benchmarks for project type comparisons

Implements CLAUDE.md requirements:
- Progressive disclosure (Level 1-4 detail depth)
- Visual confidence indicators (Ampelsystem: high/medium/low)
- Comparative explanations (vs. user's own project history)
- Handwerker-Sprache (craftsman-friendly language)
"""

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class CalculationExplanation(models.Model):
    """
    Transparent explanation of a pricing calculation.

    Shows WHY each calculation step was made, in craftsman-friendly language.
    Implements transparency requirements from German Handwerk analysis:
    - Every calculation step must be traceable
    - Manual correction possible at any time
    - Results must be plausibly explainable
    - No "black box" situations

    Related to: ExtractionResult (1:1)
    Contains: Multiple CalculationFactors (1:N)

    Example:
        >>> explanation = CalculationExplanation.objects.get(pk=uuid)
        >>> print(f"Confidence: {explanation.get_confidence_level_display()}")
        >>> print(f"Total: {explanation.total_price_eur}€")
        >>> for factor in explanation.factors.all()[:3]:
        ...     print(f"- {factor.factor_name}: {factor.impact_percent}%")
    """

    extraction_result = models.OneToOneField(
        'documents.ExtractionResult',  # String reference to avoid circular import
        on_delete=models.CASCADE,
        related_name='calculation_explanation',
        help_text='ExtractionResult this explanation belongs to'
    )

    # Overall confidence (Ampelsystem)
    CONFIDENCE_LEVELS = [
        ('high', 'Hohe Sicherheit'),      # >= 0.8 - Green light
        ('medium', 'Mittlere Sicherheit'), # 0.6-0.8 - Yellow light
        ('low', 'Niedrige Sicherheit'),    # < 0.6 - Red light
    ]
    confidence_level = models.CharField(
        max_length=10,
        choices=CONFIDENCE_LEVELS,
        help_text='Traffic light indicator for calculation reliability'
    )
    confidence_score = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        help_text='Confidence score 0.000-1.000 (higher = more reliable)'
    )

    # Final calculation result
    total_price_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Final calculated price in EUR'
    )

    # Comparison to user history ("Wie kalkuliere ICH normalerweise?")
    similar_projects_count = models.IntegerField(
        default=0,
        help_text='Number of similar projects in user history used for calculation'
    )
    user_average_for_type = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="User's average price for this project type (null if no history)"
    )
    deviation_from_average_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='How much this differs from user average (positive or negative %)'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['extraction_result']),
            models.Index(fields=['confidence_level', '-created_at']),
        ]
        verbose_name = 'Calculation Explanation'
        verbose_name_plural = 'Calculation Explanations'

    def __str__(self):
        doc_name = self.extraction_result.document.original_filename
        return f"Explanation: {doc_name} ({self.get_confidence_level_display()})"

    def is_high_confidence(self) -> bool:
        """Check if calculation has high confidence (>= 0.8)."""
        return self.confidence_score >= Decimal('0.8')

    def requires_manual_review(self) -> bool:
        """Check if calculation should be manually reviewed (< 0.6)."""
        return self.confidence_score < Decimal('0.6')

    def get_deviation_direction(self) -> str:
        """Get human-readable deviation direction."""
        if not self.deviation_from_average_percent:
            return 'keine Vergleichsdaten'

        dev = float(self.deviation_from_average_percent)
        if dev > 5:
            return f'↑ {dev:.1f}% über Durchschnitt'
        elif dev < -5:
            return f'↓ {abs(dev):.1f}% unter Durchschnitt'
        else:
            return 'im Durchschnittsbereich'


class CalculationFactor(models.Model):
    """
    Individual factor contributing to a calculation.

    Implements Progressive Disclosure:
    - Level 1: Show only top 3-5 factors (by impact_percent)
    - Level 2: Show all factors
    - Level 3: Show detailed breakdown with data sources

    Each factor explains:
    - What it is (factor_name in Handwerker language)
    - How much it costs (amount_eur)
    - Its impact on total price (impact_percent)
    - Why this value (explanation_text in plain German)
    - Where it comes from (data_source: TIER 1/2/3 or user history)

    Example:
        >>> factor = CalculationFactor.objects.get(pk=1)
        >>> print(f"{factor.factor_name}: {factor.amount_eur}€ ({factor.impact_percent}%)")
        >>> print(f"Erklärung: {factor.explanation_text}")
        "Materialkosten: 1282€ (45%)"
        "Erklärung: Eiche-Massivholz: 10 Bretter à 128.20€"
    """

    explanation = models.ForeignKey(
        CalculationExplanation,
        on_delete=models.CASCADE,
        related_name='factors',
        help_text='Parent calculation explanation'
    )

    # Factor identification
    factor_name = models.CharField(
        max_length=100,
        help_text="German craftsman-friendly name (e.g., 'Materialkosten', 'Zeitaufwand')"
    )
    factor_category = models.CharField(
        max_length=50,
        help_text="Category for grouping (e.g., 'material', 'labor', 'overhead')"
    )

    # Impact on total price
    amount_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount in EUR contributed by this factor'
    )
    impact_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Percentage of total price (0.00-100.00)'
    )

    # Human-readable explanation (Handwerker-Sprache)
    explanation_text = models.TextField(
        help_text='Plain German explanation for craftsmen (no technical jargon)'
    )

    # Data source transparency
    DATA_SOURCE_CHOICES = [
        ('tier1_global', 'TIER 1 - Globaler Standard'),
        ('tier2_company', 'TIER 2 - Firmenwerte'),
        ('tier3_dynamic', 'TIER 3 - Saisonale/Kunden-Anpassung'),
        ('user_history', 'Ihre bisherigen Projekte'),
    ]
    data_source = models.CharField(
        max_length=50,
        choices=DATA_SOURCE_CHOICES,
        help_text='Where this value comes from (transparency)'
    )

    # User interaction
    is_adjustable = models.BooleanField(
        default=True,
        help_text='Can user manually adjust this factor?'
    )

    # Display order (top factors first for Progressive Disclosure)
    display_order = models.IntegerField(
        default=0,
        help_text='Order for display (0 = first, higher = later)'
    )

    class Meta:
        ordering = ['display_order', '-impact_percent']
        indexes = [
            models.Index(fields=['explanation', 'display_order']),
            models.Index(fields=['factor_category']),
        ]
        verbose_name = 'Calculation Factor'
        verbose_name_plural = 'Calculation Factors'

    def __str__(self):
        return f"{self.factor_name} ({self.impact_percent}% - {self.amount_eur}€)"

    def is_major_factor(self) -> bool:
        """Check if this is a major factor (>= 10% impact)."""
        return self.impact_percent >= Decimal('10.0')

    def get_source_badge(self) -> str:
        """Get short badge text for data source."""
        badges = {
            'tier1_global': 'Standard',
            'tier2_company': 'Ihre Firma',
            'tier3_dynamic': 'Angepasst',
            'user_history': 'Ihre Erfahrung',
        }
        return badges.get(self.data_source, 'Unbekannt')


class UserProjectBenchmark(models.Model):
    """
    Aggregated statistics per user and project type for comparisons.

    Answers the question: "Wie kalkuliere ICH normalerweise?"

    Automatically updated when projects are completed via TrainingService.
    Used by ExplanationService to show comparative context:
    - "Diese Kalkulation liegt 12% über Ihrem Durchschnitt für Badezimmer"
    - "Ähnliche Projekte kosteten zwischen X und Y"

    Statistics tracked:
    - Number of completed projects
    - Average/min/max prices
    - Average profit margin

    Example:
        >>> benchmark = UserProjectBenchmark.objects.get(
        ...     user=user,
        ...     project_type='Badezimmer-Fliesen'
        ... )
        >>> print(f"{benchmark.total_projects} Projekte: Ø {benchmark.average_price_eur}€")
        "12 Projekte: Ø 2650.00€"
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_benchmarks',
        help_text='User who owns these benchmarks'
    )

    # Project categorization
    project_type = models.CharField(
        max_length=100,
        help_text="Project type identifier (e.g., 'Badezimmer-Fliesen', 'Küche-Elektrik')"
    )

    # Statistics (updated incrementally)
    total_projects = models.IntegerField(
        default=0,
        help_text='Number of completed projects of this type'
    )
    average_price_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Average final price across all projects'
    )
    min_price_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Lowest price for this project type'
    )
    max_price_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Highest price for this project type'
    )
    average_margin_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Average profit margin percentage'
    )

    # Metadata
    last_calculated = models.DateTimeField(
        auto_now=True,
        help_text='Last time these statistics were updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'project_type')]
        ordering = ['-last_calculated']
        indexes = [
            models.Index(fields=['user', 'project_type']),
            models.Index(fields=['user', '-last_calculated']),
        ]
        verbose_name = 'User Project Benchmark'
        verbose_name_plural = 'User Project Benchmarks'

    def __str__(self):
        return (
            f"{self.user.username} - {self.project_type} "
            f"({self.total_projects} Projekte, Ø {self.average_price_eur}€)"
        )

    def get_price_range_text(self) -> str:
        """Get human-readable price range."""
        return f"{self.min_price_eur}€ - {self.max_price_eur}€"

    def has_sufficient_data(self) -> bool:
        """Check if we have enough data for reliable comparisons (>= 3 projects)."""
        return self.total_projects >= 3

    def calculate_deviation(self, current_price: Decimal) -> Decimal:
        """
        Calculate percentage deviation from average.

        Args:
            current_price: Price to compare against average

        Returns:
            Percentage deviation (positive = above average, negative = below)

        Example:
            >>> benchmark.average_price_eur = Decimal('2000.00')
            >>> deviation = benchmark.calculate_deviation(Decimal('2200.00'))
            >>> print(f"{deviation}%")
            "10.00%"
        """
        if self.average_price_eur == 0:
            return Decimal('0.00')

        deviation = ((current_price - self.average_price_eur) / self.average_price_eur) * Decimal('100')
        return deviation.quantize(Decimal('0.01'))
