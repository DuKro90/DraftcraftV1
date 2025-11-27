# -*- coding: utf-8 -*-
"""Pattern Analysis Service: Detect and group extraction failure patterns.

Analyzes extraction results to identify:
- Common failure modes (low confidence fields)
- Grouped similar failures (by document type, field, error reason)
- Root cause analysis (why extraction fails)
- Recommendations for improvement

Used by admin dashboard for safe knowledge building workflow.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg, Count, Q

from documents.models import Document, ExtractionResult

logger = logging.getLogger(__name__)


class PatternAnalysisError(Exception):
    """Exception for pattern analysis errors."""
    pass


class ExtractionPattern:
    """Represents a grouped set of similar extraction failures."""

    def __init__(
        self,
        pattern_type: str,
        root_cause: str,
        field_name: str,
        confidence_threshold: float,
        affected_documents: List[str],
        frequency: int,
        example_values: List[Dict[str, Any]],
    ):
        """Initialize extraction pattern."""
        self.pattern_type = pattern_type  # 'low_confidence' | 'missing_field' | 'formatting_error'
        self.root_cause = root_cause  # 'unclear_handwriting' | 'non_standard_format' | etc.
        self.field_name = field_name  # 'amount' | 'vendor_name' | etc.
        self.confidence_threshold = confidence_threshold
        self.affected_documents = affected_documents
        self.frequency = frequency
        self.example_values = example_values
        self.severity = self._calculate_severity()

    def _calculate_severity(self) -> str:
        """Calculate severity: CRITICAL | HIGH | MEDIUM | LOW."""
        if self.frequency >= 50 and self.confidence_threshold < 0.60:
            return 'CRITICAL'
        elif self.frequency >= 20 and self.confidence_threshold < 0.70:
            return 'HIGH'
        elif self.frequency >= 10 and self.confidence_threshold < 0.80:
            return 'MEDIUM'
        return 'LOW'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/admin display."""
        return {
            'pattern_type': self.pattern_type,
            'root_cause': self.root_cause,
            'field_name': self.field_name,
            'confidence_threshold': float(self.confidence_threshold),
            'affected_documents': len(self.affected_documents),
            'frequency': self.frequency,
            'severity': self.severity,
            'example_values': self.example_values,
            'affected_document_ids': self.affected_documents,
        }


class PatternAnalyzer:
    """
    Analyzes extraction results to identify failure patterns.

    Methods:
    - analyze_low_confidence_fields() - Find fields with low confidence
    - group_similar_failures() - Group failures by similarity
    - root_cause_analysis() - Identify why failures occur
    - get_patterns_summary() - Overview of all patterns
    - suggest_improvements() - Recommendations for admin action
    """

    def __init__(self, user: Optional[User] = None, days_back: int = 30):
        """Initialize pattern analyzer.

        Args:
            user: Optional - analyze for specific user only
            days_back: Number of days to analyze
        """
        self.user = user
        self.days_back = days_back
        self.cutoff_date = timezone.now() - timedelta(days=days_back)

        logger.info(
            f"PatternAnalyzer initialized: user={user}, days_back={days_back}"
        )

    def analyze_extraction_results(self) -> Dict[str, Any]:
        """
        Complete analysis: low confidence, grouping, root causes.

        Returns:
            Dict with:
            - low_confidence_patterns: List[ExtractionPattern]
            - grouped_failures: Dict of grouped patterns
            - root_causes: Dict of root cause analysis
            - recommendations: List of improvement suggestions
            - summary_stats: Overall statistics
        """
        try:
            logger.info("Starting extraction result analysis")

            # Get extraction results
            query = ExtractionResult.objects.filter(
                created_at__gte=self.cutoff_date
            ).select_related('document')

            if self.user:
                query = query.filter(document__user=self.user)

            results = list(query)
            logger.debug(f"Analyzing {len(results)} extraction results")

            if not results:
                return {
                    'low_confidence_patterns': [],
                    'grouped_failures': {},
                    'root_causes': {},
                    'recommendations': [],
                    'summary_stats': {
                        'total_documents': 0,
                        'total_errors': 0,
                        'patterns_found': 0,
                        'critical_patterns': 0,
                    },
                }

            # Analyze low confidence fields
            low_confidence = self._analyze_low_confidence_fields(results)

            # Group similar failures
            grouped = self._group_similar_failures(results, low_confidence)

            # Root cause analysis
            root_causes = self._analyze_root_causes(grouped)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                low_confidence, root_causes
            )

            # Summary stats
            stats = self._calculate_summary_stats(results, low_confidence)

            return {
                'low_confidence_patterns': low_confidence,
                'grouped_failures': grouped,
                'root_causes': root_causes,
                'recommendations': recommendations,
                'summary_stats': stats,
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise PatternAnalysisError(f"Analysis failed: {e}")

    def _analyze_low_confidence_fields(
        self,
        results: List[ExtractionResult],
    ) -> List[ExtractionPattern]:
        """Identify fields with consistently low confidence."""
        logger.debug("Analyzing low confidence fields")

        field_confidences = defaultdict(list)
        field_documents = defaultdict(list)

        # Collect confidence scores by field
        for result in results:
            if result.confidence_scores:
                for field, confidence in result.confidence_scores.items():
                    field_confidences[field].append(confidence)
                    if confidence < 0.80:  # Below threshold
                        field_documents[field].append(str(result.document.id))

        patterns = []

        # Analyze each field
        for field, confidences in field_confidences.items():
            if not confidences:
                continue

            avg_confidence = sum(confidences) / len(confidences)
            low_count = sum(1 for c in confidences if c < 0.80)

            if low_count >= 3:  # At least 3 low-confidence occurrences
                pattern = ExtractionPattern(
                    pattern_type='low_confidence',
                    root_cause='unclear_document_formatting',  # Initial guess
                    field_name=field,
                    confidence_threshold=avg_confidence,
                    affected_documents=field_documents[field],
                    frequency=len(confidences),
                    example_values=[
                        {
                            'field': field,
                            'confidence': confidences[i],
                            'document_id': field_documents[field][i],
                        }
                        for i in range(min(3, len(field_documents[field])))
                    ],
                )
                patterns.append(pattern)
                logger.debug(
                    f"Found low confidence pattern: {field} "
                    f"(avg: {avg_confidence:.2f}, count: {low_count})"
                )

        return patterns

    def _group_similar_failures(
        self,
        results: List[ExtractionResult],
        patterns: List[ExtractionPattern],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group results by similarity (same field, similar confidence)."""
        logger.debug(f"Grouping {len(patterns)} patterns into failure groups")

        grouped = defaultdict(list)

        for pattern in patterns:
            # Group by field + confidence range
            group_key = self._create_group_key(pattern.field_name, pattern.severity)

            grouped[group_key].append({
                'pattern': pattern.to_dict(),
                'affected_count': len(pattern.affected_documents),
                'severity': pattern.severity,
            })

        return dict(grouped)

    def _analyze_root_causes(
        self,
        grouped_failures: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze why failures occur."""
        logger.debug("Analyzing root causes")

        root_causes = {}

        # Common failure reasons (expandable)
        failure_reasons = {
            'low_confidence_amount': {
                'description': 'Amount/price field extraction fails',
                'likely_causes': [
                    'Currency symbol ambiguity (€ vs $)',
                    'Comma/period decimal separator confusion',
                    'Multiple prices on page (invoice total vs line item)',
                    'Handwritten amounts',
                ],
                'impact': 'HIGH',
                'fixable': True,
            },
            'low_confidence_date': {
                'description': 'Date field extraction fails',
                'likely_causes': [
                    'Non-standard date format',
                    'Unclear handwriting',
                    'Multiple dates (invoice date vs due date)',
                ],
                'impact': 'HIGH',
                'fixable': True,
            },
            'low_confidence_vendor_name': {
                'description': 'Vendor/company name extraction fails',
                'likely_causes': [
                    'Unclear handwriting',
                    'Multi-line company names',
                    'Special characters in name',
                ],
                'impact': 'MEDIUM',
                'fixable': True,
            },
            'missing_field': {
                'description': 'Expected field not found in document',
                'likely_causes': [
                    'Document format not recognized',
                    'Field on optional page',
                    'Scanned at low quality',
                ],
                'impact': 'MEDIUM',
                'fixable': True,
            },
        }

        # Map patterns to root causes
        for group_key, failures in grouped_failures.items():
            # Determine cause based on field name and severity
            if 'amount' in group_key.lower():
                cause_key = 'low_confidence_amount'
            elif 'date' in group_key.lower():
                cause_key = 'low_confidence_date'
            elif 'vendor' in group_key.lower():
                cause_key = 'low_confidence_vendor_name'
            else:
                cause_key = 'missing_field'

            root_causes[group_key] = {
                **failure_reasons.get(cause_key, failure_reasons['missing_field']),
                'affected_failures': len(failures),
            }

        return root_causes

    def _generate_recommendations(
        self,
        patterns: List[ExtractionPattern],
        root_causes: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for improvement."""
        logger.debug("Generating improvement recommendations")

        recommendations = []

        # Critical patterns need immediate attention
        critical = [p for p in patterns if p.severity == 'CRITICAL']
        if critical:
            recommendations.append({
                'priority': 'CRITICAL',
                'action': 'Review and fix critical extraction patterns',
                'details': f'{len(critical)} critical patterns found',
                'affected_fields': [p.field_name for p in critical],
                'suggested_action': (
                    'Use Pattern Review workflow to examine failing cases '
                    'and adjust extraction logic or confidence thresholds'
                ),
            })

        # High severity patterns
        high = [p for p in patterns if p.severity == 'HIGH']
        if high:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Improve extraction for high-impact fields',
                'details': f'{len(high)} high-severity patterns found',
                'affected_fields': [p.field_name for p in high],
                'suggested_action': (
                    'Consider adjusting confidence thresholds or '
                    'updating extraction models'
                ),
            })

        # Fixable root causes
        fixable_causes = [
            (k, v) for k, v in root_causes.items() if v.get('fixable')
        ]
        if fixable_causes:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Address fixable root causes',
                'details': f'{len(fixable_causes)} fixable root causes identified',
                'affected_areas': [k for k, v in fixable_causes],
                'suggested_action': (
                    'Use Safe Knowledge Building workflow to test '
                    'improvements on sample cases'
                ),
            })

        return recommendations

    def _calculate_summary_stats(
        self,
        results: List[ExtractionResult],
        patterns: List[ExtractionPattern],
    ) -> Dict[str, Any]:
        """Calculate overall statistics."""
        total_fields = sum(
            len(r.confidence_scores) for r in results if r.confidence_scores
        )
        low_conf_fields = sum(
            sum(1 for c in r.confidence_scores.values() if c < 0.80)
            for r in results if r.confidence_scores
        )

        avg_confidence = (
            sum(
                sum(r.confidence_scores.values())
                for r in results if r.confidence_scores
            ) / total_fields if total_fields > 0 else 0
        )

        return {
            'total_documents': len(results),
            'total_fields_extracted': total_fields,
            'low_confidence_fields': low_conf_fields,
            'average_confidence': float(avg_confidence),
            'patterns_found': len(patterns),
            'critical_patterns': len([p for p in patterns if p.severity == 'CRITICAL']),
            'high_patterns': len([p for p in patterns if p.severity == 'HIGH']),
            'analysis_period_days': self.days_back,
        }

    def get_patterns_for_review(
        self,
        severity: Optional[str] = None,
        field_name: Optional[str] = None,
    ) -> List[ExtractionPattern]:
        """Get patterns matching criteria for admin review."""
        analysis = self.analyze_extraction_results()
        patterns = analysis['low_confidence_patterns']

        # Filter by severity
        if severity:
            patterns = [p for p in patterns if p.severity == severity]

        # Filter by field
        if field_name:
            patterns = [p for p in patterns if p.field_name == field_name]

        return patterns

    def get_pattern_timeline(self) -> Dict[str, Any]:
        """Get pattern frequency over time."""
        results = ExtractionResult.objects.filter(
            created_at__gte=self.cutoff_date
        ).select_related('document')

        if self.user:
            results = results.filter(document__user=self.user)

        # Group by day
        timeline = defaultdict(lambda: {'count': 0, 'avg_confidence': 0, 'errors': 0})

        for result in results:
            day = result.created_at.date()
            timeline[day]['count'] += 1

            if result.confidence_scores:
                avg = sum(result.confidence_scores.values()) / len(
                    result.confidence_scores
                )
                timeline[day]['avg_confidence'] += avg

            if result.error_messages:
                timeline[day]['errors'] += len(result.error_messages)

        # Calculate averages
        for day, stats in timeline.items():
            if stats['count'] > 0:
                stats['avg_confidence'] = stats['avg_confidence'] / stats['count']

        return dict(sorted(timeline.items()))

    # =====================
    # HELPER METHODS
    # =====================

    @staticmethod
    def _create_group_key(field_name: str, severity: str) -> str:
        """Create a grouping key from field and severity."""
        return f"{field_name}_{severity.lower()}"

    @staticmethod
    def get_field_recommendations(field_name: str) -> Dict[str, Any]:
        """Get specific recommendations for a field."""
        field_tips = {
            'amount': {
                'description': 'Financial amount extraction',
                'common_issues': [
                    'Currency symbols (€, $, etc.)',
                    'Thousand separators (1.000,50 vs 1,000.50)',
                    'Multiple amounts on page',
                    'Handwritten values',
                ],
                'improvement_tips': [
                    'Ensure OCR handles decimal separators correctly',
                    'Validate extracted amounts against document',
                    'Use ConfidenceRouter to flag low-confidence amounts',
                    'Consider manual review for high-value amounts',
                ],
            },
            'date': {
                'description': 'Date extraction',
                'common_issues': [
                    'Non-standard formats (DD.MM.YYYY vs MM/DD/YYYY)',
                    'Unclear handwriting',
                    'Multiple dates (invoice, due, delivery)',
                ],
                'improvement_tips': [
                    'Normalize date formats',
                    'Clearly label dates in extraction',
                    'Use document context to identify invoice date',
                ],
            },
            'vendor_name': {
                'description': 'Vendor/company name extraction',
                'common_issues': [
                    'Handwritten company names',
                    'Multi-line names',
                    'Special characters',
                ],
                'improvement_tips': [
                    'Compare against known vendor list',
                    'Use fuzzy matching for typos',
                    'Validate against database',
                ],
            },
        }

        return field_tips.get(field_name, {
            'description': f'Extraction for {field_name}',
            'common_issues': ['See analysis dashboard for details'],
            'improvement_tips': ['Review low-confidence examples'],
        })

    def export_patterns_report(self) -> str:
        """Generate a markdown report of all patterns."""
        analysis = self.analyze_extraction_results()

        report = "# Extraction Pattern Analysis Report\n\n"
        report += f"**Period:** Last {self.days_back} days\n"
        report += f"**Generated:** {timezone.now().isoformat()}\n\n"

        # Summary
        stats = analysis['summary_stats']
        report += "## Summary Statistics\n\n"
        report += f"- Total Documents: {stats['total_documents']}\n"
        report += f"- Total Fields: {stats['total_fields_extracted']}\n"
        report += f"- Low Confidence Fields: {stats['low_confidence_fields']}\n"
        report += f"- Average Confidence: {stats['average_confidence']:.2%}\n"
        report += f"- Patterns Found: {stats['patterns_found']}\n"
        report += f"- Critical Patterns: {stats['critical_patterns']}\n"
        report += f"- High Patterns: {stats['high_patterns']}\n\n"

        # Low confidence patterns
        if analysis['low_confidence_patterns']:
            report += "## Low Confidence Patterns\n\n"
            for pattern in analysis['low_confidence_patterns']:
                report += f"### {pattern.field_name.upper()} (Severity: {pattern.severity})\n\n"
                report += f"- Average Confidence: {pattern.confidence_threshold:.2%}\n"
                report += f"- Affected Documents: {len(pattern.affected_documents)}\n"
                report += f"- Root Cause: {pattern.root_cause}\n\n"

        # Recommendations
        if analysis['recommendations']:
            report += "## Recommendations\n\n"
            for i, rec in enumerate(analysis['recommendations'], 1):
                report += f"{i}. **{rec['priority']}**: {rec['action']}\n"
                report += f"   - {rec.get('suggested_action', '')}\n\n"

        return report
