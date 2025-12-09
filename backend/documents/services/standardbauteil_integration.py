"""
Standardbauteil Integration Service - Phase 4B

Integrates component calculations into Phase 3 CalculationEngine.
Extends material cost calculation with standardized components.

Integration Point: Adds component costs to TIER 1 material calculations.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass
import logging

from ..models_bauteile import (
    StandardBauteil,
    BauteilRegel,
    BauteilKatalog,
    BauteilKatalogPosition,
    GeometrieBerechnung,
)
from .bauteil_regel_engine import BauteilRegelEngine, RegelEngineError
from .geometrie_service import GeometrieService, calculate_abs_kanten_auto

logger = logging.getLogger(__name__)


@dataclass
class BauteilKostenPosition:
    """Represents a single component cost position."""
    bauteil: StandardBauteil
    menge: Decimal
    einzelpreis: Decimal
    gesamtpreis: Decimal
    berechnungsgrundlage: str  # How quantity was calculated
    regel_name: Optional[str] = None


@dataclass
class BauteilKostenSummary:
    """Summary of all component costs."""
    positionen: List[BauteilKostenPosition]
    gesamt_beschlaege: Decimal
    gesamt_verbinder: Decimal
    gesamt_kanten: Decimal
    gesamt_befestigung: Decimal
    gesamt_sonstiges: Decimal
    gesamt_netto: Decimal


class StandardbauteilIntegrationService:
    """
    Service to calculate component costs and integrate into calculation pipeline.

    Usage:
        1. Initialize with extraction result and company profile
        2. Calculate component quantities based on rules
        3. Apply ABS edge calculations (geometry-based)
        4. Return cost summary for integration into Phase 3 CalculationEngine
    """

    def __init__(
        self,
        extraction_result_id: str,
        company_profile_id: Optional[str] = None,
        katalog_id: Optional[str] = None
    ):
        """
        Initialize integration service.

        Args:
            extraction_result_id: ID of extraction result with component data
            company_profile_id: Optional company profile for catalog selection
            katalog_id: Optional specific catalog ID (overrides auto-selection)
        """
        self.extraction_result_id = extraction_result_id
        self.company_profile_id = company_profile_id
        self.katalog_id = katalog_id
        self.katalog = None
        logger.debug(f"StandardbauteilIntegrationService initialized for extraction: {extraction_result_id}")

    def calculate_bauteil_kosten(
        self,
        extracted_components: Dict[str, Any],
        gewerk: str = 'tischler'
    ) -> BauteilKostenSummary:
        """
        Calculate complete component costs.

        Args:
            extracted_components: Component data from OCR/NER extraction:
                {
                    'Tür': {'anzahl': 2, 'höhe': 2.0, 'breite': 1.0},
                    'Einlegeboden': {'anzahl': 4, 'breite': 2.0, 'tiefe': 0.8},
                    ...
                }
            gewerk: Trade type (default: 'tischler')

        Returns:
            BauteilKostenSummary with all calculated positions

        Examples:
            >>> service = StandardbauteilIntegrationService(extraction_id='abc')
            >>> components = {'Tür': {'anzahl': 2}}
            >>> summary = service.calculate_bauteil_kosten(components)
            >>> print(summary.gesamt_netto)
        """
        # Step 1: Load appropriate catalog
        self.katalog = self._load_katalog(gewerk)

        if not self.katalog:
            logger.warning(f"No catalog found for gewerk '{gewerk}', skipping component calculation")
            return self._empty_summary()

        # Step 2: Get all active components with rules for this trade
        bauteile_mit_regeln = self._get_bauteile_mit_regeln(gewerk)

        # Step 3: Calculate quantities based on rules
        positionen = []
        regel_engine = BauteilRegelEngine(extracted_components)

        for bauteil, regeln in bauteile_mit_regeln:
            # Try to calculate quantity from rules
            menge = self._calculate_menge_aus_regeln(regel_engine, regeln)

            if menge is None or menge <= 0:
                logger.debug(f"Skipping {bauteil.name}: No valid quantity calculated")
                continue

            # Get price (catalog-specific or standard)
            einzelpreis = self._get_bauteil_preis(bauteil)
            gesamtpreis = menge * einzelpreis

            # Get rule name for documentation
            regel_name = regeln[0].name if regeln else None

            positionen.append(BauteilKostenPosition(
                bauteil=bauteil,
                menge=menge,
                einzelpreis=einzelpreis,
                gesamtpreis=gesamtpreis,
                berechnungsgrundlage=f"Regel: {regel_name}" if regel_name else "Manuell",
                regel_name=regel_name
            ))

        # Step 4: Add geometry-based calculations (ABS edges)
        geometrie_positionen = self._calculate_geometrie_kosten(extracted_components, gewerk)
        positionen.extend(geometrie_positionen)

        # Step 5: Create summary by category
        summary = self._create_summary(positionen)

        logger.info(
            f"Calculated {len(positionen)} component positions, "
            f"total: {summary.gesamt_netto}€"
        )

        return summary

    def _load_katalog(self, gewerk: str) -> Optional[BauteilKatalog]:
        """
        Load appropriate catalog for calculation.

        Priority:
        1. Explicit catalog_id (if provided)
        2. Company-specific standard catalog
        3. Global standard catalog for trade
        """
        from datetime import date
        from django.db.models import Q

        today = date.today()

        # Option 1: Explicit catalog
        if self.katalog_id:
            try:
                return BauteilKatalog.objects.get(id=self.katalog_id, ist_aktiv=True)
            except BauteilKatalog.DoesNotExist:
                logger.warning(f"Catalog {self.katalog_id} not found or inactive")

        # Option 2: Company-specific standard
        if self.company_profile_id:
            catalog = BauteilKatalog.objects.filter(
                firma_id=self.company_profile_id,
                gewerk=gewerk,
                ist_standard=True,
                ist_aktiv=True,
                gueltig_ab__lte=today,
            ).filter(
                Q(gueltig_bis__gte=today) | Q(gueltig_bis__isnull=True)
            ).first()

            if catalog:
                logger.debug(f"Using company-specific catalog: {catalog.name}")
                return catalog

        # Option 3: Global standard
        catalog = BauteilKatalog.objects.filter(
            firma__isnull=True,
            gewerk=gewerk,
            ist_standard=True,
            ist_aktiv=True,
            gueltig_ab__lte=today,
        ).filter(
            Q(gueltig_bis__gte=today) | Q(gueltig_bis__isnull=True)
        ).first()

        if catalog:
            logger.debug(f"Using global catalog: {catalog.name}")
            return catalog

        logger.warning(f"No valid catalog found for gewerk '{gewerk}'")
        return None

    def _get_bauteile_mit_regeln(self, gewerk: str) -> List[tuple]:
        """
        Get all active components with their calculation rules for a trade.

        Returns:
            List of (StandardBauteil, List[BauteilRegel]) tuples
        """
        if not self.katalog:
            return []

        # Get all components in catalog for this trade
        bauteile = StandardBauteil.objects.filter(
            kataloge=self.katalog,
            ist_aktiv=True,
            gewerke__contains=[gewerk]
        ).prefetch_related('regeln')

        result = []
        for bauteil in bauteile:
            # Get active rules for this component
            regeln = list(bauteil.regeln.filter(ist_aktiv=True).order_by('prioritaet'))

            # Skip if no rules (unless it's ABS-Kante which uses geometry)
            if not regeln and bauteil.kategorie != 'kante':
                continue

            result.append((bauteil, regeln))

        return result

    def _calculate_menge_aus_regeln(
        self,
        regel_engine: BauteilRegelEngine,
        regeln: List[BauteilRegel]
    ) -> Optional[Decimal]:
        """
        Calculate quantity from rules (uses first rule that succeeds).

        Args:
            regel_engine: Initialized rule engine
            regeln: List of rules (ordered by priority)

        Returns:
            Calculated quantity or None if no rule succeeded
        """
        for regel in regeln:
            try:
                menge = regel_engine.execute_rule(regel.regel_definition)
                logger.debug(f"Rule '{regel.name}' calculated quantity: {menge}")
                return menge
            except RegelEngineError as e:
                logger.debug(f"Rule '{regel.name}' failed: {e}, trying next rule")
                continue

        return None

    def _get_bauteil_preis(self, bauteil: StandardBauteil) -> Decimal:
        """
        Get component price (catalog-specific or standard).

        Args:
            bauteil: Component

        Returns:
            Price per unit
        """
        if not self.katalog:
            return bauteil.einzelpreis

        # Try to get catalog-specific price
        try:
            position = BauteilKatalogPosition.objects.get(
                katalog=self.katalog,
                bauteil=bauteil,
                ist_aktiv_in_katalog=True
            )
            return position.get_preis()
        except BauteilKatalogPosition.DoesNotExist:
            # Fallback to standard price
            return bauteil.einzelpreis

    def _calculate_geometrie_kosten(
        self,
        extracted_components: Dict[str, Any],
        gewerk: str
    ) -> List[BauteilKostenPosition]:
        """
        Calculate geometry-based costs (e.g., ABS edges).

        Args:
            extracted_components: Component data
            gewerk: Trade type

        Returns:
            List of geometry-based cost positions
        """
        positionen = []

        # Only for Tischler (ABS edges)
        if gewerk != 'tischler':
            return positionen

        # Find ABS-Kante component in catalog
        abs_kante_bauteile = StandardBauteil.objects.filter(
            kataloge=self.katalog,
            kategorie='kante',
            ist_aktiv=True
        )

        if not abs_kante_bauteile.exists():
            logger.debug("No ABS edge components in catalog, skipping")
            return positionen

        # Use first ABS-Kante component (could be extended to support multiple types)
        abs_kante = abs_kante_bauteile.first()

        # Convert components to list format for GeometrieService
        komponenten_list = []
        for typ, daten in extracted_components.items():
            komponenten_list.append({
                'typ': typ,
                'maße': daten.get('maße', {}),
                'anzahl': daten.get('anzahl', 1)
            })

        # Calculate ABS edge lengths
        try:
            geometrie_service = GeometrieService(self.extraction_result_id)
            berechnungen = geometrie_service.calculate_abs_kanten(
                komponenten_list,
                apply_visibility_defaults=True
            )

            # Calculate total activated edge length
            gesamt_laenge = geometrie_service.calculate_total_kanten_länge(
                berechnungen,
                nur_aktivierte=True
            )

            if gesamt_laenge > 0:
                einzelpreis = self._get_bauteil_preis(abs_kante)
                gesamtpreis = gesamt_laenge * einzelpreis

                positionen.append(BauteilKostenPosition(
                    bauteil=abs_kante,
                    menge=gesamt_laenge,
                    einzelpreis=einzelpreis,
                    gesamtpreis=gesamtpreis,
                    berechnungsgrundlage="Geometrie-basiert (automatisch berechnet)",
                    regel_name="ABS-Kanten Automatik"
                ))

                logger.debug(f"ABS edges: {gesamt_laenge} lfm × {einzelpreis}€ = {gesamtpreis}€")

        except Exception as e:
            logger.error(f"Error calculating geometry costs: {e}", exc_info=True)

        return positionen

    def _create_summary(self, positionen: List[BauteilKostenPosition]) -> BauteilKostenSummary:
        """
        Create summary by component category.

        Args:
            positionen: List of cost positions

        Returns:
            BauteilKostenSummary
        """
        gesamt_beschlaege = Decimal('0')
        gesamt_verbinder = Decimal('0')
        gesamt_kanten = Decimal('0')
        gesamt_befestigung = Decimal('0')
        gesamt_sonstiges = Decimal('0')

        for pos in positionen:
            kategorie = pos.bauteil.kategorie

            if kategorie == 'beschlag':
                gesamt_beschlaege += pos.gesamtpreis
            elif kategorie == 'verbinder':
                gesamt_verbinder += pos.gesamtpreis
            elif kategorie == 'kante':
                gesamt_kanten += pos.gesamtpreis
            elif kategorie == 'befestigung':
                gesamt_befestigung += pos.gesamtpreis
            else:
                gesamt_sonstiges += pos.gesamtpreis

        gesamt_netto = sum(pos.gesamtpreis for pos in positionen)

        return BauteilKostenSummary(
            positionen=positionen,
            gesamt_beschlaege=gesamt_beschlaege,
            gesamt_verbinder=gesamt_verbinder,
            gesamt_kanten=gesamt_kanten,
            gesamt_befestigung=gesamt_befestigung,
            gesamt_sonstiges=gesamt_sonstiges,
            gesamt_netto=gesamt_netto
        )

    def _empty_summary(self) -> BauteilKostenSummary:
        """Return empty summary."""
        return BauteilKostenSummary(
            positionen=[],
            gesamt_beschlaege=Decimal('0'),
            gesamt_verbinder=Decimal('0'),
            gesamt_kanten=Decimal('0'),
            gesamt_befestigung=Decimal('0'),
            gesamt_sonstiges=Decimal('0'),
            gesamt_netto=Decimal('0')
        )

    def export_bauteil_kosten_for_calculation_engine(
        self,
        summary: BauteilKostenSummary
    ) -> Dict[str, Any]:
        """
        Export component costs in format for Phase 3 CalculationEngine integration.

        Returns format compatible with TIER 1 material costs.

        Returns:
            {
                'material_typ': 'Standardbauteile',
                'positionen': [
                    {
                        'artikel_nr': 'HF-12345',
                        'name': 'Topfband 35mm',
                        'menge': 6,
                        'einheit': 'Stück',
                        'einzelpreis': 2.50,
                        'gesamtpreis': 15.00,
                        'kategorie': 'Beschläge',
                        'berechnungsgrundlage': 'Regel: Topfbänder pro Tür'
                    },
                    ...
                ],
                'kategorie_summen': {
                    'beschlaege': 50.00,
                    'verbinder': 20.00,
                    'kanten': 34.56,
                    'befestigung': 12.80,
                    'sonstiges': 0.00
                },
                'gesamt_netto': 117.36
            }
        """
        positionen_export = []

        for pos in summary.positionen:
            positionen_export.append({
                'artikel_nr': pos.bauteil.artikel_nr,
                'name': pos.bauteil.name,
                'menge': float(pos.menge),
                'einheit': pos.bauteil.get_einheit_display(),
                'einzelpreis': float(pos.einzelpreis),
                'gesamtpreis': float(pos.gesamtpreis),
                'kategorie': pos.bauteil.get_kategorie_display(),
                'berechnungsgrundlage': pos.berechnungsgrundlage
            })

        return {
            'material_typ': 'Standardbauteile',
            'positionen': positionen_export,
            'kategorie_summen': {
                'beschlaege': float(summary.gesamt_beschlaege),
                'verbinder': float(summary.gesamt_verbinder),
                'kanten': float(summary.gesamt_kanten),
                'befestigung': float(summary.gesamt_befestigung),
                'sonstiges': float(summary.gesamt_sonstiges)
            },
            'gesamt_netto': float(summary.gesamt_netto)
        }


def calculate_standardbauteile(
    extraction_result_id: str,
    extracted_components: Dict[str, Any],
    gewerk: str = 'tischler',
    company_profile_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to calculate component costs.

    Args:
        extraction_result_id: Extraction result ID
        extracted_components: Component data from OCR/NER
        gewerk: Trade type (default: 'tischler')
        company_profile_id: Optional company profile ID

    Returns:
        Dict in format for CalculationEngine integration

    Examples:
        >>> components = {
        ...     'Tür': {'anzahl': 2, 'maße': {'höhe': 2.0, 'breite': 1.0}},
        ...     'Einlegeboden': {'anzahl': 4, 'maße': {'breite': 2.0, 'tiefe': 0.8}}
        ... }
        >>> result = calculate_standardbauteile('extraction-123', components)
        >>> print(result['gesamt_netto'])
    """
    service = StandardbauteilIntegrationService(
        extraction_result_id=extraction_result_id,
        company_profile_id=company_profile_id
    )

    summary = service.calculate_bauteil_kosten(extracted_components, gewerk)
    return service.export_bauteil_kosten_for_calculation_engine(summary)
