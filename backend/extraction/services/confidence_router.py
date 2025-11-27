"""Intelligent routing service based on extraction confidence and complexity."""
import logging
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

from django.conf import settings

logger = logging.getLogger(__name__)


class RouteType(Enum):
    """Route types for extracted document processing."""
    AUTO_ACCEPT = "auto_accept"
    AGENT_VERIFY = "agent_verify"
    AGENT_EXTRACT = "agent_extract"
    HUMAN_REVIEW = "human_review"


class ComplexityLevel(Enum):
    """Document complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceRouterError(Exception):
    """Exception for routing errors."""
    pass


class ConfidenceRouter:
    """
    Intelligent routing service that determines processing path based on:
    - Overall extraction confidence
    - Field-level confidence with weighted importance
    - Document complexity
    - Historical pattern success

    Routes to:
    - AUTO_ACCEPT: High-confidence results → straight through processing
    - AGENT_VERIFY: Borderline results → agent verification pass
    - AGENT_EXTRACT: Low-confidence results → agent re-extraction
    - HUMAN_REVIEW: Very low/complex results → flag for manual review
    """

    def __init__(self):
        """Initialize router with configuration from Django settings."""
        config = settings.AGENT_SETTINGS
        self.confidence_thresholds = config['CONFIDENCE_THRESHOLDS']
        self.field_weights = config['FIELD_WEIGHTS']
        self.complexity_config = config['COMPLEXITY_SCORING']

    def route(
        self,
        extraction_result: Dict[str, Any],
        confidence_scores: Dict[str, float],
        complexity: Optional[ComplexityLevel] = None
    ) -> Tuple[RouteType, float, List[str]]:
        """
        Determine routing path for extracted document.

        Args:
            extraction_result: Extracted fields dictionary
            confidence_scores: Per-field confidence scores (0.0-1.0)
            complexity: Optional document complexity level

        Returns:
            Tuple of:
            - route_type: RouteType enum
            - weighted_confidence: Overall confidence score
            - reasoning: List of decision factors

        Raises:
            ConfidenceRouterError: If input validation fails
        """
        # Validate inputs
        if not isinstance(confidence_scores, dict):
            raise ConfidenceRouterError("confidence_scores must be a dictionary")

        if not confidence_scores:
            logger.warning("No confidence scores provided, routing to HUMAN_REVIEW")
            return RouteType.HUMAN_REVIEW, 0.0, ["No confidence scores provided"]

        # Estimate complexity if not provided
        if complexity is None:
            complexity = self._estimate_complexity(extraction_result)

        # Calculate weighted confidence
        weighted_confidence = self._calculate_weighted_confidence(
            extraction_scores=confidence_scores,
            extraction_result=extraction_result
        )

        # Apply complexity-based threshold adjustment
        adjusted_threshold = self._get_complexity_threshold(complexity)

        # Determine route
        reasoning = []

        if weighted_confidence >= self.confidence_thresholds['auto_accept']:
            route = RouteType.AUTO_ACCEPT
            reasoning.append(
                f"High confidence ({weighted_confidence:.3f}) → Auto-accept (no agent needed)"
            )

        elif weighted_confidence >= self.confidence_thresholds['agent_verify']:
            route = RouteType.AGENT_VERIFY
            reasoning.append(
                f"Borderline confidence ({weighted_confidence:.3f}) → Agent verification"
            )
            reasoning.append(self._identify_weak_fields(confidence_scores))

        elif weighted_confidence >= self.confidence_thresholds['agent_extract']:
            route = RouteType.AGENT_EXTRACT
            reasoning.append(
                f"Low confidence ({weighted_confidence:.3f}) → Agent re-extraction"
            )
            reasoning.append(self._identify_weak_fields(confidence_scores))

        else:
            route = RouteType.HUMAN_REVIEW
            reasoning.append(
                f"Very low confidence ({weighted_confidence:.3f}) → Human review needed"
            )
            reasoning.append(self._identify_weak_fields(confidence_scores))

        # Check for critical missing fields
        missing_critical = self._check_critical_fields(extraction_result)
        if missing_critical:
            if route == RouteType.AUTO_ACCEPT:
                route = RouteType.AGENT_VERIFY
                reasoning.append(f"Critical fields missing: {missing_critical}")
            elif route == RouteType.AGENT_VERIFY:
                route = RouteType.AGENT_EXTRACT
                reasoning.append(f"Critical fields missing: {missing_critical}")

        # Apply complexity penalty
        complexity_penalty = self._get_complexity_penalty(complexity)
        if complexity_penalty > 0:
            adjusted_confidence = max(weighted_confidence - complexity_penalty, 0.0)
            reason = (
                f"Complexity adjustment ({complexity.value}): "
                f"{weighted_confidence:.3f} → {adjusted_confidence:.3f}"
            )
            reasoning.append(reason)

            # Re-route if complexity penalty changes the route
            if adjusted_confidence < self.confidence_thresholds['agent_verify']:
                if route == RouteType.AUTO_ACCEPT:
                    route = RouteType.AGENT_VERIFY

        logger.info(
            f"Routing decision: {route.value} "
            f"(confidence={weighted_confidence:.3f}, complexity={complexity.value})"
        )

        return route, weighted_confidence, reasoning

    def route_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Tuple[RouteType, float, List[str]]]:
        """
        Route multiple documents.

        Args:
            documents: List of extraction results with confidence_scores

        Returns:
            List of routing results
        """
        results = []

        for doc in documents:
            try:
                extraction_result = doc.get('extraction_result', {})
                confidence_scores = doc.get('confidence_scores', {})

                route, confidence, reasoning = self.route(
                    extraction_result,
                    confidence_scores
                )

                results.append((route, confidence, reasoning))

            except Exception as e:
                logger.error(f"Failed to route document: {e}")
                results.append(
                    (RouteType.HUMAN_REVIEW, 0.0, [f"Error during routing: {e}"])
                )

        return results

    # ===== Confidence Calculation =====

    def _calculate_weighted_confidence(
        self,
        extraction_scores: Dict[str, float],
        extraction_result: Dict[str, Any]
    ) -> float:
        """
        Calculate weighted confidence across all fields.

        Weights critical financial fields (amount, date) higher than
        secondary metadata fields.

        Args:
            extraction_scores: Per-field confidence scores
            extraction_result: Extracted data

        Returns:
            Weighted confidence between 0.0 and 1.0
        """
        if not extraction_scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for field_name, confidence in extraction_scores.items():
            # Get field weight (default 1.0 if not configured)
            weight = self.field_weights.get(field_name, 1.0)

            total_weight += weight
            weighted_sum += confidence * weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _identify_weak_fields(self, confidence_scores: Dict[str, float]) -> str:
        """Identify fields with lowest confidence."""
        if not confidence_scores:
            return "No confidence scores"

        weak_fields = [
            (field, score)
            for field, score in confidence_scores.items()
            if score < 0.80
        ]

        weak_fields.sort(key=lambda x: x[1])  # Sort by confidence

        if weak_fields:
            field_str = ", ".join(
                [f"{field}({score:.2f})" for field, score in weak_fields[:3]]
            )
            return f"Weak fields: {field_str}"

        return "All fields above 0.80 confidence"

    # ===== Complexity Assessment =====

    def _estimate_complexity(self, extraction_result: Dict[str, Any]) -> ComplexityLevel:
        """Estimate document complexity from extraction data."""
        complexity_score = 0

        # Check for indicators of complexity
        if 'gaeb_position' in extraction_result and extraction_result['gaeb_position']:
            complexity_score += 2  # GAEB documents are complex

        if 'material' in extraction_result and extraction_result['material']:
            complexity_score += 1

        # Multiple items/positions
        if 'items' in extraction_result and isinstance(extraction_result['items'], list):
            complexity_score += len(extraction_result['items']) // 5

        # Special construction terms
        special_terms = ['gedrechselt', 'gefräst', 'geschnitzt', 'handgeschnitzt']
        text_fields = [extraction_result.get(f, '') for f in ['notes', 'description']]
        text_combined = ' '.join(text_fields).lower()

        for term in special_terms:
            if term in text_combined:
                complexity_score += 3

        if complexity_score >= 5:
            return ComplexityLevel.HIGH
        elif complexity_score >= 2:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.LOW

    def _get_complexity_threshold(self, complexity: ComplexityLevel) -> float:
        """Get confidence threshold based on complexity."""
        config = self.complexity_config.get(complexity.value, {})
        return config.get('agent_threshold', 0.75)

    def _get_complexity_penalty(self, complexity: ComplexityLevel) -> float:
        """Get confidence penalty for document complexity."""
        penalties = {
            ComplexityLevel.LOW: 0.0,
            ComplexityLevel.MEDIUM: 0.05,
            ComplexityLevel.HIGH: 0.10,
        }
        return penalties.get(complexity, 0.0)

    # ===== Field Validation =====

    def _check_critical_fields(self, extraction_result: Dict[str, Any]) -> List[str]:
        """Check for missing critical fields."""
        critical_fields = ['amount', 'date', 'vendor_name']
        missing = []

        for field in critical_fields:
            value = extraction_result.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(field)

        return missing

    # ===== Route Info Methods =====

    @staticmethod
    def get_route_description(route: RouteType) -> str:
        """Get human-readable description of route."""
        descriptions = {
            RouteType.AUTO_ACCEPT: (
                "Extraction accepted as-is. High confidence, no agent processing needed."
            ),
            RouteType.AGENT_VERIFY: (
                "Agent verifies extraction against source text. "
                "Confidence borderline, verification may improve accuracy."
            ),
            RouteType.AGENT_EXTRACT: (
                "Agent re-extracts document fields. "
                "Confidence low, re-extraction recommended for accuracy."
            ),
            RouteType.HUMAN_REVIEW: (
                "Manual review required. "
                "Confidence very low or critical fields missing."
            ),
        }
        return descriptions.get(route, "Unknown route")

    @staticmethod
    def get_expected_agent_cost(route: RouteType) -> str:
        """Get expected API cost for route."""
        costs = {
            RouteType.AUTO_ACCEPT: "$0 (no API call)",
            RouteType.AGENT_VERIFY: "~$0.000100 (200 tokens)",
            RouteType.AGENT_EXTRACT: "~$0.000250 (500 tokens)",
            RouteType.HUMAN_REVIEW: "$0 (no API call, manual review)",
        }
        return costs.get(route, "Unknown")

    def get_route_stats(self) -> Dict[str, Any]:
        """Get routing configuration and thresholds."""
        return {
            'confidence_thresholds': {
                key: value
                for key, value in self.confidence_thresholds.items()
            },
            'field_weights': self.field_weights.copy(),
            'complexity_scoring': self.complexity_config.copy(),
        }
