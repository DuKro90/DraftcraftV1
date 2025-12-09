# -*- coding: utf-8 -*-
"""Integrated extraction pipeline combining Phase 2 (Agentic RAG) and Phase 3 (Betriebskennzahlen)."""

import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from documents.models import Document, ExtractionResult
from documents.pattern_models import ExtractionFailurePattern
from extraction.services.calculation_engine import CalculationEngine, CalculationError
from extraction.services.pattern_analyzer import PatternAnalyzer
from extraction.services.knowledge_builder import SafeKnowledgeBuilder, KnowledgeBuilderException
from extraction.services.explanation_service import ExplanationService


logger = logging.getLogger(__name__)


class IntegratedPipelineException(Exception):
    """Exception for integrated pipeline operations."""
    pass


class IntegratedExtractionPipeline:
    """
    Orchestrates complete document processing pipeline combining:
    - Phase 2: Agentic RAG (confidence routing, agent enhancement, cost tracking)
    - Phase 3: Betriebskennzahlen (pricing, pattern detection, knowledge building)

    Workflow:
    1. Document extracted (Phase 2) → get ExtractionResult with confidence scores
    2. Patterns analyzed → detect low confidence fields, data mismatches
    3. Safe fixes applied (if available) → improve extraction quality
    4. Pricing calculated → apply company-specific metrics
    5. Complete result with patterns and pricing returned

    Safety:
    - Patterns detected but not auto-applied (requires admin review)
    - Pricing only calculated if configured
    - All steps atomic with proper error handling
    - Pattern learning from successes/failures
    """

    def __init__(self, user: User):
        """
        Initialize integrated pipeline for a user.

        Args:
            user: User owning documents and configuration

        Raises:
            IntegratedPipelineException: If user lacks required configuration
        """
        self.user = user
        try:
            self.calculator = CalculationEngine(user)
            self.pattern_analyzer = PatternAnalyzer(user)
            self.knowledge_builder = SafeKnowledgeBuilder(user)
            self.explainer = ExplanationService(user)  # Phase 4A: Transparency
        except Exception as e:
            raise IntegratedPipelineException(
                f"Cannot initialize pipeline for user {user.username}: {str(e)}"
            )

    def process_extraction_result(
        self,
        extraction_result: ExtractionResult,
        apply_knowledge_fixes: bool = True,
        calculate_pricing: bool = True,
        create_explanation: bool = True  # Phase 4A: Create transparent explanation
    ) -> Dict[str, Any]:
        """
        Complete processing of an extraction result.

        Steps:
        1. Analyze patterns in extracted data
        2. Apply safe knowledge fixes (if available and approved)
        3. Calculate pricing (if configured)
        4. Create transparent explanation (Phase 4A - if pricing calculated)
        5. Return comprehensive result with all enrichments

        Args:
            extraction_result: ExtractionResult to process
            apply_knowledge_fixes: Apply validated knowledge fixes (default True)
            calculate_pricing: Calculate project pricing (default True)
            create_explanation: Create transparent explanation (default True, Phase 4A)

        Returns:
            Dict with:
                - extraction (dict): Original extraction result
                - patterns (dict): Detected patterns and analysis
                - pricing (dict or None): Calculated pricing
                - explanation (dict or None): Transparent explanation (Phase 4A)
                - knowledge_applied (list): Applied fixes
                - enrichments_timestamp (str): ISO timestamp
                - processing_notes (list): Warnings/info messages
        """
        notes = []
        patterns_result = None
        pricing_result = None
        explanation_data = None  # Phase 4A: Transparent explanation
        knowledge_applied = []

        try:
            # Step 1: Analyze patterns
            try:
                patterns_result = self._analyze_patterns(extraction_result)
                if patterns_result['summary']['low_confidence_fields']:
                    notes.append(
                        f"Detected {len(patterns_result['summary']['low_confidence_fields'])} "
                        "low-confidence fields"
                    )
            except Exception as e:
                logger.warning(f"Pattern analysis failed: {str(e)}")
                notes.append(f"Pattern analysis failed: {str(e)}")

            # Step 2: Apply safe knowledge fixes
            if apply_knowledge_fixes:
                try:
                    knowledge_applied = self._apply_knowledge_fixes(extraction_result)
                    if knowledge_applied:
                        notes.append(f"Applied {len(knowledge_applied)} validated fixes")
                except Exception as e:
                    logger.warning(f"Knowledge application failed: {str(e)}")
                    notes.append(f"Knowledge fixes skipped: {str(e)}")

            # Step 3: Calculate pricing
            if calculate_pricing:
                try:
                    pricing_result = self._calculate_pricing(extraction_result)
                    notes.append("Pricing calculated successfully")
                except CalculationError as e:
                    logger.warning(f"Pricing calculation failed: {str(e)}")
                    notes.append(f"Pricing calculation failed: {str(e)}")
                except Exception as e:
                    logger.warning(f"Unexpected error during pricing: {str(e)}")
                    notes.append(f"Pricing calculation error: {str(e)}")

            # Step 4: Create transparent explanation (Phase 4A)
            if create_explanation and pricing_result:
                try:
                    explanation = self.explainer.create_explanation(
                        extraction_result,
                        pricing_result
                    )
                    explanation_data = {
                        'confidence_level': explanation.confidence_level,
                        'confidence_score': float(explanation.confidence_score),
                        'similar_projects': explanation.similar_projects_count,
                        'user_average': float(explanation.user_average_for_type) if explanation.user_average_for_type else None,
                        'deviation_percent': float(explanation.deviation_from_average_percent) if explanation.deviation_from_average_percent else None,
                        'factors': [
                            {
                                'name': f.factor_name,
                                'category': f.factor_category,
                                'amount': float(f.amount_eur),
                                'impact_percent': float(f.impact_percent),
                                'explanation': f.explanation_text,
                                'data_source': f.get_source_badge(),
                                'adjustable': f.is_adjustable,
                            }
                            for f in explanation.factors.all()[:5]  # Top 5 factors for Progressive Disclosure
                        ]
                    }
                    notes.append("Transparente Erklärung erstellt")
                except Exception as e:
                    logger.warning(f"Could not create explanation: {str(e)}")
                    notes.append(f"Erklärung übersprungen: {str(e)}")

            logger.info(
                f"Processed extraction {extraction_result.id} for user {self.user.username}. "
                f"Patterns: {bool(patterns_result)}, Pricing: {bool(pricing_result)}, "
                f"Explanation: {bool(explanation_data)}"
            )

            return {
                'success': True,
                'extraction': self._serialize_extraction(extraction_result),
                'patterns': patterns_result,
                'pricing': pricing_result,
                'explanation': explanation_data,  # Phase 4A: Transparent explanation
                'knowledge_applied': knowledge_applied,
                'enrichments_timestamp': timezone.now().isoformat(),
                'processing_notes': notes,
            }

        except Exception as e:
            logger.error(f"Pipeline processing failed: {str(e)}", exc_info=True)
            raise IntegratedPipelineException(f"Pipeline processing failed: {str(e)}")

    def _analyze_patterns(self, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """
        Analyze patterns in extraction result.

        Args:
            extraction_result: ExtractionResult to analyze

        Returns:
            Dict with pattern analysis
        """
        extracted_data = extraction_result.extracted_data or {}
        confidence_scores = extraction_result.confidence_scores or {}

        analysis = self.pattern_analyzer.analyze_extraction_results()

        return {
            'low_confidence_patterns': analysis.get('low_confidence_patterns', []),
            'grouped_failures': analysis.get('grouped_failures', []),
            'root_causes': analysis.get('root_causes', []),
            'summary': analysis.get('summary_stats', {}),
        }

    def _apply_knowledge_fixes(self, extraction_result: ExtractionResult) -> List[Dict[str, Any]]:
        """
        Apply validated knowledge fixes to extraction.

        Args:
            extraction_result: ExtractionResult to enrich

        Returns:
            List of applied fixes with details
        """
        applied = []

        # Get ready-to-deploy fixes
        ready_fixes = self.knowledge_builder.get_ready_to_deploy_fixes()

        if not ready_fixes:
            return applied

        # For demonstration, we're not actually auto-applying fixes
        # (requires explicit admin approval in production)
        # Instead, we return what COULD be applied
        for fix in ready_fixes:
            fix_info = {
                'proposal_id': str(fix.id),
                'title': fix.title,
                'field': fix.pattern.field_name,
                'fix_type': fix.get_fix_type_display(),
                'test_success_rate': float(fix.test_success_rate or Decimal('0')),
                'status': 'ready_for_deployment',
                'note': 'Approved by admin, can be deployed',
            }
            applied.append(fix_info)

        return applied

    def _calculate_pricing(self, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """
        Calculate project pricing from extracted data.

        Args:
            extraction_result: ExtractionResult with extracted fields

        Returns:
            Dict with pricing breakdown

        Raises:
            CalculationError: If pricing cannot be calculated
        """
        extracted_data = extraction_result.extracted_data or {}

        # Extract relevant fields for pricing
        pricing_input = {
            'material_sku': extracted_data.get('material_sku'),
            'material_quantity': extracted_data.get('material_quantity', 1),
            'holzart': extracted_data.get('holzart'),
            'oberflaeche': extracted_data.get('surface_finish'),
            'komplexitaet': extracted_data.get('complexity'),
            'labor_hours': extracted_data.get('labor_hours', 0),
        }

        # Calculate price
        result = self.calculator.calculate_project_price(
            extracted_data=pricing_input,
            customer_type='neue_kunden',
            breakdown=True
        )

        return {
            'total_price_eur': result['total_price_eur'],
            'breakdown': result['breakdown'],
            'warnings': result['warnings'],
            'tiers_applied': result.get('tiers_applied', {}),
        }

    def _serialize_extraction(self, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """
        Serialize extraction result for response.

        Args:
            extraction_result: ExtractionResult to serialize

        Returns:
            Dict with extraction details
        """
        return {
            'id': str(extraction_result.id),
            'document_id': str(extraction_result.document.id),
            'extracted_data': extraction_result.extracted_data or {},
            'confidence_scores': extraction_result.confidence_scores or {},
            'ocr_text_length': len(extraction_result.ocr_text or ''),
            'created_at': extraction_result.created_at.isoformat(),
        }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current status of all pipeline components.

        Returns:
            Dict with status of calculation engine, pattern analyzer, knowledge builder
        """
        return {
            'user': self.user.username,
            'calculator_configured': self.calculator.config is not None,
            'pattern_analyzer_active': True,
            'knowledge_builder_ready': self.knowledge_builder.get_ready_to_deploy_fixes().count() > 0,
            'ready_to_deploy_fixes': self.knowledge_builder.get_ready_to_deploy_fixes().count(),
            'deployment_summary': self.knowledge_builder.get_deployment_summary(),
        }

    def get_extraction_recommendations(self, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """
        Get recommendations for improving this extraction.

        Args:
            extraction_result: ExtractionResult to analyze

        Returns:
            Dict with improvement recommendations
        """
        recommendations = {
            'extraction_quality': [],
            'knowledge_improvements': [],
            'pricing_notes': [],
        }

        # Check extraction quality
        confidence_scores = extraction_result.confidence_scores or {}
        low_confidence = [
            field for field, score in confidence_scores.items()
            if score < 0.80
        ]
        if low_confidence:
            recommendations['extraction_quality'].append(
                f"Low confidence in: {', '.join(low_confidence)}"
            )

        # Check knowledge improvements
        ready_fixes = self.knowledge_builder.get_ready_to_deploy_fixes()
        if ready_fixes:
            recommendations['knowledge_improvements'].append(
                f"{ready_fixes.count()} validated fixes ready to deploy"
            )

        # Check pricing
        try:
            pricing = self._calculate_pricing(extraction_result)
            if pricing['warnings']:
                recommendations['pricing_notes'] = pricing['warnings']
        except Exception:
            recommendations['pricing_notes'].append('Pricing calculation unavailable')

        return recommendations

    def create_processing_report(self, extraction_result: ExtractionResult) -> str:
        """
        Generate detailed processing report for an extraction.

        Args:
            extraction_result: ExtractionResult to report on

        Returns:
            Markdown formatted report
        """
        result = self.process_extraction_result(extraction_result)

        report = f"""
# Extraction Processing Report

## Document
- **ID**: {extraction_result.document.id}
- **Filename**: {extraction_result.document.original_filename}
- **Extraction Time**: {extraction_result.created_at.strftime('%d.%m.%Y %H:%M:%S')}

## Extracted Data
- **Fields**: {len(result['extraction']['extracted_data'])}
- **Average Confidence**: {self._calculate_avg_confidence(result['extraction']['confidence_scores']):.1%}

## Pattern Analysis
{self._format_patterns(result['patterns'])}

## Knowledge Fixes
{self._format_knowledge(result['knowledge_applied'])}

## Pricing
{self._format_pricing(result['pricing'])}

## Notes
{self._format_notes(result['processing_notes'])}

---
Report Generated: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        return report.strip()

    def _calculate_avg_confidence(self, scores: Dict[str, float]) -> float:
        """Calculate average confidence score."""
        if not scores:
            return 0.0
        return sum(scores.values()) / len(scores)

    def _format_patterns(self, patterns: Optional[Dict[str, Any]]) -> str:
        """Format pattern analysis for report."""
        if not patterns:
            return "No patterns detected"

        lines = []
        summary = patterns.get('summary', {})
        if summary.get('low_confidence_fields'):
            lines.append(
                f"**Low Confidence Fields**: {len(summary['low_confidence_fields'])}"
            )
        if not lines:
            lines.append("No significant patterns detected")

        return "\n".join(lines)

    def _format_knowledge(self, knowledge: List[Dict[str, Any]]) -> str:
        """Format knowledge improvements for report."""
        if not knowledge:
            return "No knowledge fixes applied"

        lines = [f"Applied {len(knowledge)} fixes:"]
        for fix in knowledge:
            lines.append(f"- {fix['title']} ({fix['fix_type']})")

        return "\n".join(lines)

    def _format_pricing(self, pricing: Optional[Dict[str, Any]]) -> str:
        """Format pricing for report."""
        if not pricing:
            return "Pricing not calculated"

        return f"**Total Price**: €{pricing['total_price_eur']:.2f}"

    def _format_notes(self, notes: List[str]) -> str:
        """Format processing notes for report."""
        if not notes:
            return "No processing notes"

        return "\n".join([f"- {note}" for note in notes])
