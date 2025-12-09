# -*- coding: utf-8 -*-
"""
ExplanationService: Generates transparent, user-friendly explanations for calculations.

Phase 4A: Transparenz & Benutzerfreundlichkeit
Implements CLAUDE.md requirements:
- Progressive disclosure (Level 1-4 detail)
- Visual confidence indicators (Ampelsystem)
- Comparative explanations (vs. user history)
- Handwerker-Sprache (no technical jargon)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models import Avg, Min, Max, Count

from documents.models import ExtractionResult
from documents.transparency_models import (
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark,
)
from extraction.services.calculation_engine import CalculationEngine

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Generates transparent explanations for pricing calculations.

    Transparency Principles:
    1. Show confidence level prominently (Ampel-System: green/yellow/red)
    2. Break down top 3-5 factors with impact %
    3. Compare to user's own history
    4. Use Handwerker language ("Zeitaufwand" not "labor_hours")
    5. Make every decision traceable

    Example Usage:
        >>> explainer = ExplanationService(user)
        >>> explanation = explainer.create_explanation(
        ...     extraction_result,
        ...     calculation_result
        ... )
        >>> print(f"Confidence: {explanation.confidence_level}")
        >>> print(f"Total: {explanation.total_price_eur}€")
        >>> for factor in explanation.factors.all()[:3]:
        ...     print(f"- {factor.factor_name}: {factor.impact_percent}%")
    """

    def __init__(self, user: User):
        """
        Initialize explanation service for a user.

        Args:
            user: Django User instance
        """
        self.user = user
        self.calculator = CalculationEngine(user)

    def create_explanation(
        self,
        extraction_result: ExtractionResult,
        calculation_result: Dict[str, Any]
    ) -> CalculationExplanation:
        """
        Create comprehensive explanation for a calculation.

        Args:
            extraction_result: ExtractionResult with extracted data
            calculation_result: Dict from CalculationEngine.calculate_project_price()
                Expected keys:
                - total_price_eur: Decimal
                - breakdown: Dict with cost components
                - metadata: Dict with additional info

        Returns:
            CalculationExplanation with all factors and comparisons

        Raises:
            ValueError: If calculation_result is missing required fields
        """
        # Validate input
        if 'total_price_eur' not in calculation_result:
            raise ValueError("calculation_result must contain 'total_price_eur'")

        # 1. Determine confidence level
        confidence_score = self._calculate_confidence(extraction_result, calculation_result)
        confidence_level = self._get_confidence_level(confidence_score)

        # 2. Get user benchmark for comparison
        project_type = self._determine_project_type(extraction_result.extracted_data)
        benchmark = self._get_or_create_benchmark(project_type)

        # 3. Calculate deviation from user's average
        total_price = calculation_result.get('total_price_eur', Decimal('0'))
        deviation = self._calculate_deviation(total_price, benchmark.average_price_eur) if benchmark else None

        # 4. Create explanation record
        explanation = CalculationExplanation.objects.create(
            extraction_result=extraction_result,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            total_price_eur=total_price,
            similar_projects_count=benchmark.total_projects if benchmark else 0,
            user_average_for_type=benchmark.average_price_eur if benchmark else None,
            deviation_from_average_percent=deviation,
        )

        # 5. Create factor breakdowns
        self._create_factors(explanation, calculation_result)

        logger.info(
            f"Created explanation for {extraction_result.id}: "
            f"€{total_price}, confidence={confidence_level}"
        )

        return explanation

    def _calculate_confidence(
        self,
        extraction_result: ExtractionResult,
        calculation_result: Dict[str, Any]
    ) -> Decimal:
        """
        Calculate overall confidence score (0.000-1.000).

        Factors considered:
        - Extraction confidence scores (from OCR/NER)
        - Number of similar projects in history
        - Data completeness (required fields present)

        Args:
            extraction_result: ExtractionResult with confidence_scores
            calculation_result: Calculation metadata

        Returns:
            Decimal confidence score (0.000-1.000)
        """
        # Base confidence from extraction
        extraction_scores = extraction_result.confidence_scores or {}
        avg_extraction = Decimal(str(
            sum(extraction_scores.values()) / len(extraction_scores)
            if extraction_scores else 0.5
        ))

        # Boost if we have similar projects
        similar_projects = calculation_result.get('metadata', {}).get('similar_projects_count', 0)
        history_boost = min(Decimal('0.2'), Decimal(str(similar_projects)) * Decimal('0.02'))

        # Penalize if key fields missing
        required_fields = ['holzart', 'oberflaeche', 'material_sku']
        extracted_data = extraction_result.extracted_data or {}
        completeness = sum(1 for f in required_fields if f in extracted_data) / len(required_fields)
        completeness_penalty = Decimal('0.1') * (Decimal('1') - Decimal(str(completeness)))

        final_confidence = min(
            Decimal('1.0'),
            avg_extraction + history_boost - completeness_penalty
        )

        return final_confidence.quantize(Decimal('0.001'))

    def _get_confidence_level(self, score: Decimal) -> str:
        """
        Map confidence score to level (high/medium/low).

        Thresholds:
        - >= 0.8: high (green light)
        - 0.6-0.8: medium (yellow light)
        - < 0.6: low (red light)

        Args:
            score: Confidence score 0.000-1.000

        Returns:
            String: 'high', 'medium', or 'low'
        """
        if score >= Decimal('0.8'):
            return 'high'
        elif score >= Decimal('0.6'):
            return 'medium'
        else:
            return 'low'

    def _determine_project_type(self, extracted_data: Dict[str, Any]) -> str:
        """
        Determine project type from extracted data for benchmark comparison.

        Examples:
        - "Badezimmer-Fliesen"
        - "Küche-Elektrik"
        - "Schrank-Eiche"

        Simple heuristic (can be enhanced with ML later):
        - room_type + work_type + material

        Args:
            extracted_data: Dict with extracted fields

        Returns:
            String project type identifier
        """
        room = extracted_data.get('raum_typ', 'Projekt')
        work_type = extracted_data.get('arbeitstyp', '')
        material = extracted_data.get('holzart', '')

        if work_type and material:
            return f"{room}-{work_type}-{material}"
        elif work_type:
            return f"{room}-{work_type}"
        else:
            return room

    def _get_or_create_benchmark(self, project_type: str) -> Optional[UserProjectBenchmark]:
        """
        Get benchmark for this project type or None if no history.

        Args:
            project_type: Project type identifier

        Returns:
            UserProjectBenchmark or None if no history exists
        """
        try:
            return UserProjectBenchmark.objects.get(
                user=self.user,
                project_type=project_type
            )
        except UserProjectBenchmark.DoesNotExist:
            # No history yet - will be created after first project completion
            return None

    def _calculate_deviation(self, current: Decimal, average: Decimal) -> Decimal:
        """
        Calculate percentage deviation from average.

        Args:
            current: Current price
            average: Average price

        Returns:
            Percentage deviation (positive = above average, negative = below)
        """
        if average == 0:
            return Decimal('0')

        deviation = ((current - average) / average) * Decimal('100')
        return deviation.quantize(Decimal('0.01'))

    def _create_factors(
        self,
        explanation: CalculationExplanation,
        calculation_result: Dict[str, Any]
    ) -> None:
        """
        Create CalculationFactor records for each pricing component.

        Top 3-5 factors by impact % for Progressive Disclosure.

        Args:
            explanation: Parent CalculationExplanation
            calculation_result: Dict with 'breakdown' key containing cost components
        """
        breakdown = calculation_result.get('breakdown', {})
        total = calculation_result.get('total_price_eur', Decimal('1'))

        if total == 0:
            total = Decimal('1')  # Avoid division by zero

        factors_data = []

        # Material costs
        material_cost = breakdown.get('material_cost', Decimal('0'))
        if material_cost > 0:
            factors_data.append({
                'factor_name': 'Materialkosten',
                'factor_category': 'material',
                'amount_eur': material_cost,
                'impact_percent': (material_cost / total * 100).quantize(Decimal('0.01')),
                'explanation_text': self._explain_material_cost(breakdown),
                'data_source': 'tier2_company',
                'is_adjustable': True,
            })

        # Labor costs
        labor_cost = breakdown.get('labor_cost', Decimal('0'))
        if labor_cost > 0:
            factors_data.append({
                'factor_name': 'Zeitaufwand',
                'factor_category': 'labor',
                'amount_eur': labor_cost,
                'impact_percent': (labor_cost / total * 100).quantize(Decimal('0.01')),
                'explanation_text': self._explain_labor_cost(breakdown),
                'data_source': 'user_history',
                'is_adjustable': True,
            })

        # Wood type factor
        wood_adjustment = breakdown.get('wood_type_adjustment', Decimal('0'))
        if wood_adjustment != 0:
            factors_data.append({
                'factor_name': 'Holzart-Aufpreis',
                'factor_category': 'material',
                'amount_eur': wood_adjustment,
                'impact_percent': (abs(wood_adjustment) / total * 100).quantize(Decimal('0.01')),
                'explanation_text': self._explain_wood_factor(breakdown),
                'data_source': 'tier1_global',
                'is_adjustable': False,
            })

        # Complexity factor
        complexity_adjustment = breakdown.get('complexity_adjustment', Decimal('0'))
        if complexity_adjustment > 0:
            factors_data.append({
                'factor_name': 'Komplexität',
                'factor_category': 'labor',
                'amount_eur': complexity_adjustment,
                'impact_percent': (complexity_adjustment / total * 100).quantize(Decimal('0.01')),
                'explanation_text': self._explain_complexity(breakdown),
                'data_source': 'tier1_global',
                'is_adjustable': True,
            })

        # Overhead & margin
        overhead = breakdown.get('overhead', Decimal('0'))
        margin = breakdown.get('profit_margin', Decimal('0'))
        overhead_total = overhead + margin
        if overhead_total > 0:
            factors_data.append({
                'factor_name': 'Gemeinkosten & Marge',
                'factor_category': 'overhead',
                'amount_eur': overhead_total,
                'impact_percent': (overhead_total / total * 100).quantize(Decimal('0.01')),
                'explanation_text': f"Ihre Gemeinkosten ({overhead}€) + Gewinnmarge ({margin}€)",
                'data_source': 'tier2_company',
                'is_adjustable': True,
            })

        # Sort by impact (highest first) and create records
        factors_data.sort(key=lambda x: x['impact_percent'], reverse=True)

        for idx, factor_data in enumerate(factors_data):
            CalculationFactor.objects.create(
                explanation=explanation,
                display_order=idx,
                **factor_data
            )

    def _explain_material_cost(self, breakdown: Dict) -> str:
        """Generate Handwerker-friendly explanation for material costs."""
        sku = breakdown.get('material_sku', 'Standard')
        qty = breakdown.get('quantity', 1)
        unit_price = breakdown.get('unit_price', Decimal('0'))

        return f"{sku}: {qty} Stück à {unit_price}€"

    def _explain_labor_cost(self, breakdown: Dict) -> str:
        """Generate explanation for labor costs."""
        hours = breakdown.get('labor_hours', 0)
        rate = breakdown.get('labor_rate_per_hour', Decimal('0'))

        return f"{hours} Stunden à {rate}€/h (Ihr Stundensatz)"

    def _explain_wood_factor(self, breakdown: Dict) -> str:
        """Explain wood type pricing factor."""
        wood_type = breakdown.get('wood_type', 'Standard')
        factor = breakdown.get('wood_factor', Decimal('1.0'))

        if factor > Decimal('1.0'):
            return f"{wood_type.title()}: Hochwertiges Hartholz (Faktor {factor})"
        elif factor < Decimal('1.0'):
            return f"{wood_type.title()}: Günstiges Weichholz (Faktor {factor})"
        else:
            return f"{wood_type.title()}: Standard-Preisklasse"

    def _explain_complexity(self, breakdown: Dict) -> str:
        """Explain complexity factor."""
        technique = breakdown.get('complexity_technique', 'Standard')
        factor = breakdown.get('complexity_factor', Decimal('1.0'))

        if factor > Decimal('1.5'):
            return f"{technique}: Sehr aufwändige Handarbeit (Faktor {factor})"
        elif factor > Decimal('1.2'):
            return f"{technique}: Erhöhter Aufwand (Faktor {factor})"
        else:
            return f"{technique}: Normaler Aufwand"

    def update_benchmark_after_completion(
        self,
        project_type: str,
        final_price: Decimal,
        final_margin_percent: Decimal
    ) -> UserProjectBenchmark:
        """
        Update benchmark statistics after project completion.

        Called from training interface when user confirms final costs.
        Uses incremental averaging to update statistics.

        Args:
            project_type: Project type identifier
            final_price: Final project price
            final_margin_percent: Final profit margin percentage

        Returns:
            Updated UserProjectBenchmark

        Example:
            >>> explainer.update_benchmark_after_completion(
            ...     'Badezimmer-Fliesen',
            ...     Decimal('2850.00'),
            ...     Decimal('21.5')
            ... )
        """
        benchmark, created = UserProjectBenchmark.objects.get_or_create(
            user=self.user,
            project_type=project_type,
            defaults={
                'total_projects': 0,
                'average_price_eur': Decimal('0'),
                'min_price_eur': final_price,
                'max_price_eur': final_price,
                'average_margin_percent': Decimal('0'),
            }
        )

        if created:
            # First project of this type
            benchmark.total_projects = 1
            benchmark.average_price_eur = final_price
            benchmark.average_margin_percent = final_margin_percent
        else:
            # Update running averages
            old_total = benchmark.total_projects
            new_total = old_total + 1

            # Weighted average for price
            benchmark.average_price_eur = (
                (benchmark.average_price_eur * old_total + final_price) / new_total
            ).quantize(Decimal('0.01'))

            # Weighted average for margin
            benchmark.average_margin_percent = (
                (benchmark.average_margin_percent * old_total + final_margin_percent) / new_total
            ).quantize(Decimal('0.01'))

            # Update min/max
            if final_price < benchmark.min_price_eur:
                benchmark.min_price_eur = final_price
            if final_price > benchmark.max_price_eur:
                benchmark.max_price_eur = final_price

            benchmark.total_projects = new_total

        benchmark.save()
        logger.info(
            f"Updated benchmark for {self.user.username}/{project_type}: "
            f"{benchmark.total_projects} projects, Ø {benchmark.average_price_eur}€"
        )

        return benchmark
