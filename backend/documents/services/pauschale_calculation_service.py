"""
Pauschale Calculation Service - Phase 4C

Handles calculation of Betriebspauschalen (operational surcharges) for project pricing.

Supported calculation types:
- fest: Fixed amount
- pro_einheit: Per-unit calculation
- prozent: Percentage of order value
- konditional: Conditional calculation using Level 2 DSL

Author: Claude Code
Created: December 2025
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
import logging

from documents.models_pauschalen import BetriebspauschaleRegel, PauschaleAnwendung
from .bauteil_regel_engine import BauteilRegelEngine

logger = logging.getLogger(__name__)


class PauschaleCalculationService:
    """
    Service for calculating operational surcharges (Betriebspauschalen).

    Handles various calculation types including fixed amounts, per-unit calculations,
    percentages, and conditional rules using the DSL engine.
    """

    def __init__(self, user, extraction_result):
        """
        Initialize the service.

        Args:
            user: User object for filtering rules
            extraction_result: ExtractionResult instance for linking applications
        """
        self.user = user
        self.extraction_result = extraction_result

    def calculate_all_pauschalen(
        self, auftragswert: Decimal, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate all applicable Pauschalen for an order.

        Args:
            auftragswert: Total order value (for range filtering)
            context: Calculation context (distance, quantities, etc.)

        Returns:
            Dict with 'pauschalen' list and 'total' sum

        Example:
            >>> service = PauschaleCalculationService(user, extraction_result)
            >>> result = service.calculate_all_pauschalen(
            ...     auftragswert=Decimal('5000'),
            ...     context={'distanz_km': 75, 'montage_stunden': 8}
            ... )
            >>> print(result['total'])
            275.50
        """
        pauschalen = BetriebspauschaleRegel.objects.filter(
            user=self.user, ist_aktiv=True
        )

        results = []
        total = Decimal('0')

        for pauschale in pauschalen:
            # Check if pauschale applies to this order value
            if not pauschale.is_applicable_for_order(auftragswert):
                logger.debug(
                    f"Pauschale '{pauschale.name}' not applicable "
                    f"for order value {auftragswert}"
                )
                continue

            try:
                betrag = self._calculate_pauschale(pauschale, context)
                if betrag > 0:
                    # Create PauschaleAnwendung record
                    anwendung = PauschaleAnwendung.objects.create(
                        extraction_result=self.extraction_result,
                        pauschale=pauschale,
                        berechnungsgrundlage=context,
                        berechneter_betrag=betrag,
                    )

                    results.append(
                        {
                            "name": pauschale.name,
                            "typ": pauschale.pauschale_typ,
                            "betrag": float(betrag),
                            "anwendung_id": str(anwendung.id),
                        }
                    )
                    total += betrag

                    logger.info(
                        f"Applied Pauschale '{pauschale.name}': {betrag} EUR"
                    )

            except Exception as e:
                logger.error(
                    f"Error calculating Pauschale '{pauschale.name}': {e}",
                    exc_info=True,
                )
                # Continue with other Pauschalen even if one fails
                continue

        return {"pauschalen": results, "total": float(total)}

    def _calculate_pauschale(
        self, pauschale: BetriebspauschaleRegel, context: Dict[str, Any]
    ) -> Decimal:
        """
        Calculate a single Pauschale based on its calculation type.

        Args:
            pauschale: BetriebspauschaleRegel instance
            context: Calculation context

        Returns:
            Calculated amount as Decimal

        Raises:
            ValueError: If calculation type is invalid or required data is missing
        """
        berechnungsart = pauschale.berechnungsart

        if berechnungsart == "fest":
            # Fixed amount
            return pauschale.betrag

        elif berechnungsart == "pro_einheit":
            # Per-unit calculation: betrag × quantity
            # Look for quantity in context based on pauschale type
            menge_key = f"{pauschale.pauschale_typ}_menge"
            menge = context.get(menge_key, 0)

            if menge == 0:
                logger.warning(
                    f"No quantity found for key '{menge_key}' in context. "
                    f"Using 0."
                )

            return pauschale.betrag * Decimal(str(menge))

        elif berechnungsart == "prozent":
            # Percentage of order value
            auftragswert = context.get("auftragswert", Decimal("0"))
            return auftragswert * (pauschale.prozentsatz / Decimal("100"))

        elif berechnungsart == "konditional":
            # Conditional rule using Level 2 DSL
            if not pauschale.konditional_regel:
                raise ValueError(
                    f"Pauschale '{pauschale.name}' has berechnungsart=konditional "
                    f"but no konditional_regel defined"
                )

            # Create engine with empty components (pauschalen don't use components)
            engine = BauteilRegelEngine({})
            # Add context for resolution of variables
            engine.context = context

            try:
                result = engine.execute_rule(pauschale.konditional_regel)
                return result

            except Exception as e:
                logger.error(
                    f"Error executing konditional regel for '{pauschale.name}': {e}",
                    exc_info=True,
                )
                return Decimal("0")

        else:
            raise ValueError(
                f"Unknown berechnungsart '{berechnungsart}' for "
                f"Pauschale '{pauschale.name}'"
            )

    def get_applied_pauschalen(
        self, extraction_result_id
    ) -> List[PauschaleAnwendung]:
        """
        Get all applied Pauschalen for an extraction result.

        Args:
            extraction_result_id: ExtractionResult UUID

        Returns:
            List of PauschaleAnwendung instances
        """
        return PauschaleAnwendung.objects.filter(
            extraction_result_id=extraction_result_id
        ).select_related("pauschale")

    def recalculate_pauschalen(
        self, extraction_result, auftragswert: Decimal, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recalculate all Pauschalen for an extraction result.

        Deletes existing applications and recalculates from scratch.

        Args:
            extraction_result: ExtractionResult instance
            auftragswert: Total order value
            context: Calculation context

        Returns:
            Dict with 'pauschalen' list and 'total' sum
        """
        # Delete existing applications
        PauschaleAnwendung.objects.filter(
            extraction_result=extraction_result
        ).delete()

        logger.info(
            f"Deleted old Pauschalen applications for extraction {extraction_result.id}"
        )

        # Recalculate
        return self.calculate_all_pauschalen(auftragswert, context)
