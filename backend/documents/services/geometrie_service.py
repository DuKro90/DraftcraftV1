"""
Geometrie-Service - Phase 4B

Automatic geometry-based calculations for component quantities.
Primary use case: ABS edge length calculation for furniture components.

Features:
- Automatic edge length calculation based on component dimensions
- User-editable checkboxes for selective edge application
- Support for complex geometries (Korpus, Türen, Einlegeböden, Schubladen)
- Company-specific default preferences
"""

from typing import Dict, Any, List, Tuple
from decimal import Decimal
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class KantenBerechnung:
    """
    Represents a calculated edge with user-editable properties.
    """
    kanten_typ: str
    formel: str
    berechnete_laenge: Decimal
    komponenten_daten: Dict[str, Any]
    ist_aktiviert: bool = True  # Default: enabled
    ist_sichtbar: bool = True   # Is this edge typically visible?


class GeometrieServiceError(Exception):
    """Base exception for geometry service errors."""
    pass


class InvalidComponentError(GeometrieServiceError):
    """Raised when component data is invalid or incomplete."""
    pass


class GeometrieService:
    """
    Calculates geometry-based quantities for construction components.

    Primary focus: ABS edge length calculation for Tischler/Möbelbau.
    """

    # Standard edge visibility rules
    EDGE_VISIBILITY_DEFAULTS = {
        'korpus_außen': True,        # Always visible
        'korpus_innen': False,       # Usually hidden
        'tür_außen': True,           # Always visible
        'einlegeboden_vorder': True, # Front edge visible
        'einlegeboden_seite': False, # Side edges optional
        'schublade_außen': True,     # Visible
        'rueckseite': False,         # Back panel usually not edged
    }

    def __init__(self, extraction_result_id: str = None):
        """
        Initialize geometry service.

        Args:
            extraction_result_id: Optional ID of extraction result for linking
        """
        self.extraction_result_id = extraction_result_id
        logger.debug(f"GeometrieService initialized for extraction: {extraction_result_id}")

    def calculate_abs_kanten(
        self,
        komponenten: List[Dict[str, Any]],
        apply_visibility_defaults: bool = True
    ) -> List[KantenBerechnung]:
        """
        Calculate ABS edge lengths for all components.

        Args:
            komponenten: List of component dicts from extraction:
                [
                    {
                        'typ': 'Korpus',
                        'maße': {'höhe': 2.0, 'breite': 2.0, 'tiefe': 0.8},
                        'anzahl': 1
                    },
                    {
                        'typ': 'Tür',
                        'maße': {'höhe': 2.0, 'breite': 1.0},
                        'anzahl': 2
                    },
                    ...
                ]
            apply_visibility_defaults: Apply standard visibility rules?

        Returns:
            List of KantenBerechnung objects

        Examples:
            >>> service = GeometrieService()
            >>> komponenten = [
            ...     {'typ': 'Tür', 'maße': {'höhe': 2.0, 'breite': 1.0}, 'anzahl': 2}
            ... ]
            >>> berechnungen = service.calculate_abs_kanten(komponenten)
            >>> print(berechnungen[0].berechnete_laenge)
            12.0  # 2 × (2.0 + 1.0) × 2 Türen
        """
        alle_berechnungen = []

        for komponente in komponenten:
            typ = komponente.get('typ', '').lower()
            maße = komponente.get('maße', {})
            anzahl = komponente.get('anzahl', 1)

            if not maße:
                logger.warning(f"Component '{typ}' has no dimensions, skipping")
                continue

            # Dispatch to specific calculation method
            if typ == 'korpus':
                berechnungen = self._calculate_korpus_kanten(maße, anzahl, komponente)
            elif typ in ['tür', 'tuer']:
                berechnungen = self._calculate_tür_kanten(maße, anzahl, komponente)
            elif typ == 'einlegeboden':
                berechnungen = self._calculate_einlegeboden_kanten(maße, anzahl, komponente)
            elif typ == 'schublade':
                berechnungen = self._calculate_schublade_kanten(maße, anzahl, komponente)
            else:
                logger.warning(f"Unknown component type '{typ}', using generic calculation")
                berechnungen = self._calculate_generic_kanten(maße, anzahl, komponente)

            # Apply visibility defaults
            if apply_visibility_defaults:
                for berechnung in berechnungen:
                    default_visibility = self.EDGE_VISIBILITY_DEFAULTS.get(
                        berechnung.kanten_typ,
                        True  # Default to visible if not specified
                    )
                    berechnung.ist_aktiviert = default_visibility

            alle_berechnungen.extend(berechnungen)

        logger.info(f"Calculated {len(alle_berechnungen)} edge segments")
        return alle_berechnungen

    def _calculate_korpus_kanten(
        self,
        maße: Dict[str, float],
        anzahl: int,
        komponente: Dict[str, Any]
    ) -> List[KantenBerechnung]:
        """
        Calculate edge lengths for Korpus (cabinet body).

        Korpus has:
        - Außenkanten (outer edges) - visible sides
        - Innenkanten (inner edges) - usually hidden
        """
        höhe = Decimal(str(maße.get('höhe', 0)))
        breite = Decimal(str(maße.get('breite', 0)))
        tiefe = Decimal(str(maße.get('tiefe', 0)))
        anz = Decimal(str(anzahl))

        berechnungen = []

        # Außenkanten (2 sichtbare Seiten)
        # Formel: 2 × (höhe + breite) × anzahl
        außen_länge = 2 * (höhe + breite) * anz
        berechnungen.append(KantenBerechnung(
            kanten_typ='korpus_außen',
            formel=f'2 × ({höhe}m + {breite}m) × {anzahl} Korpus',
            berechnete_laenge=außen_länge,
            komponenten_daten=komponente,
            ist_sichtbar=True
        ))

        # Innenkanten (optional, meist nicht bekanntet)
        # Formel: 2 × tiefe × anzahl (für Fachböden-Auflage)
        innen_länge = 2 * tiefe * anz
        berechnungen.append(KantenBerechnung(
            kanten_typ='korpus_innen',
            formel=f'2 × {tiefe}m × {anzahl} Korpus (Fachboden-Auflagen)',
            berechnete_laenge=innen_länge,
            komponenten_daten=komponente,
            ist_sichtbar=False
        ))

        return berechnungen

    def _calculate_tür_kanten(
        self,
        maße: Dict[str, float],
        anzahl: int,
        komponente: Dict[str, Any]
    ) -> List[KantenBerechnung]:
        """
        Calculate edge lengths for Türen (doors).

        Doors typically need all 4 edges (perimeter).
        """
        höhe = Decimal(str(maße.get('höhe', 0)))
        breite = Decimal(str(maße.get('breite', 0)))
        anz = Decimal(str(anzahl))

        # Außenkanten (Umfang)
        # Formel: 2 × (höhe + breite) × anzahl
        außen_länge = 2 * (höhe + breite) * anz

        return [KantenBerechnung(
            kanten_typ='tür_außen',
            formel=f'2 × ({höhe}m + {breite}m) × {anzahl} Türen',
            berechnete_laenge=außen_länge,
            komponenten_daten=komponente,
            ist_sichtbar=True
        )]

    def _calculate_einlegeboden_kanten(
        self,
        maße: Dict[str, float],
        anzahl: int,
        komponente: Dict[str, Any]
    ) -> List[KantenBerechnung]:
        """
        Calculate edge lengths for Einlegeböden (shelves).

        Shelves typically have:
        - Front edge (always visible)
        - Side edges (optional, depends on design)
        """
        breite = Decimal(str(maße.get('breite', 0)))
        tiefe = Decimal(str(maße.get('tiefe', 0)))
        anz = Decimal(str(anzahl))

        berechnungen = []

        # Vorderkante (immer sichtbar)
        vorder_länge = breite * anz
        berechnungen.append(KantenBerechnung(
            kanten_typ='einlegeboden_vorder',
            formel=f'{breite}m × {anzahl} Einlegeböden',
            berechnete_laenge=vorder_länge,
            komponenten_daten=komponente,
            ist_sichtbar=True
        ))

        # Seitenkanten (optional)
        # Formel: 2 × tiefe × anzahl
        seiten_länge = 2 * tiefe * anz
        berechnungen.append(KantenBerechnung(
            kanten_typ='einlegeboden_seite',
            formel=f'2 × {tiefe}m × {anzahl} Einlegeböden',
            berechnete_laenge=seiten_länge,
            komponenten_daten=komponente,
            ist_sichtbar=False  # Optional
        ))

        return berechnungen

    def _calculate_schublade_kanten(
        self,
        maße: Dict[str, float],
        anzahl: int,
        komponente: Dict[str, Any]
    ) -> List[KantenBerechnung]:
        """
        Calculate edge lengths for Schubladen (drawers).

        Drawer fronts need perimeter edging.
        """
        höhe = Decimal(str(maße.get('höhe', 0)))
        breite = Decimal(str(maße.get('breite', 0)))
        anz = Decimal(str(anzahl))

        # Außenkanten (Umfang der Front)
        außen_länge = 2 * (höhe + breite) * anz

        return [KantenBerechnung(
            kanten_typ='schublade_außen',
            formel=f'2 × ({höhe}m + {breite}m) × {anzahl} Schubladen',
            berechnete_laenge=außen_länge,
            komponenten_daten=komponente,
            ist_sichtbar=True
        )]

    def _calculate_generic_kanten(
        self,
        maße: Dict[str, float],
        anzahl: int,
        komponente: Dict[str, Any]
    ) -> List[KantenBerechnung]:
        """
        Generic edge calculation for unknown component types.

        Calculates perimeter based on available dimensions.
        """
        # Try to extract any dimensions
        dims = []
        for key in ['höhe', 'breite', 'tiefe', 'länge']:
            if key in maße:
                dims.append(Decimal(str(maße[key])))

        if len(dims) < 2:
            logger.warning(f"Not enough dimensions for generic calculation: {maße}")
            return []

        # Calculate perimeter with first 2 dimensions
        umfang = 2 * sum(dims[:2]) * Decimal(str(anzahl))

        return [KantenBerechnung(
            kanten_typ='sonstiges',
            formel=f'2 × ({dims[0]}m + {dims[1]}m) × {anzahl}',
            berechnete_laenge=umfang,
            komponenten_daten=komponente,
            ist_sichtbar=True
        )]

    def calculate_total_kanten_länge(
        self,
        berechnungen: List[KantenBerechnung],
        nur_aktivierte: bool = True
    ) -> Decimal:
        """
        Calculate total edge length across all calculations.

        Args:
            berechnungen: List of KantenBerechnung objects
            nur_aktivierte: Only count enabled edges?

        Returns:
            Total length in lfm (Laufmeter)

        Examples:
            >>> service = GeometrieService()
            >>> berechnungen = [
            ...     KantenBerechnung('tür_außen', 'formula', Decimal('12.0'), {}, True, True),
            ...     KantenBerechnung('korpus_innen', 'formula', Decimal('8.0'), {}, False, False)
            ... ]
            >>> total = service.calculate_total_kanten_länge(berechnungen, nur_aktivierte=True)
            >>> print(total)
            12.0  # Only the enabled edge
        """
        if nur_aktivierte:
            filtered = [b for b in berechnungen if b.ist_aktiviert]
        else:
            filtered = berechnungen

        total = sum(b.berechnete_laenge for b in filtered)
        logger.debug(f"Total edge length: {total} lfm ({len(filtered)} segments)")
        return total

    def create_editable_preview(
        self,
        berechnungen: List[KantenBerechnung]
    ) -> Dict[str, Any]:
        """
        Create user-friendly preview for editing in admin/frontend.

        Returns dict suitable for JSON serialization with checkboxes.

        Returns:
            {
                'kanten': [
                    {
                        'typ': 'tür_außen',
                        'beschreibung': 'Tür Außenkanten',
                        'formel': '2 × (2.0m + 1.0m) × 2 Türen',
                        'länge': '12.0',
                        'einheit': 'lfm',
                        'ist_aktiviert': True,
                        'ist_sichtbar': True
                    },
                    ...
                ],
                'gesamt_aktiviert': '20.5',
                'gesamt_alle': '28.5'
            }
        """
        kanten_list = []
        for berechnung in berechnungen:
            kanten_list.append({
                'typ': berechnung.kanten_typ,
                'beschreibung': self._get_kanten_beschreibung(berechnung.kanten_typ),
                'formel': berechnung.formel,
                'länge': str(berechnung.berechnete_laenge),
                'einheit': 'lfm',
                'ist_aktiviert': berechnung.ist_aktiviert,
                'ist_sichtbar': berechnung.ist_sichtbar,
                'komponenten_daten': berechnung.komponenten_daten
            })

        gesamt_aktiviert = self.calculate_total_kanten_länge(berechnungen, nur_aktivierte=True)
        gesamt_alle = self.calculate_total_kanten_länge(berechnungen, nur_aktivierte=False)

        return {
            'kanten': kanten_list,
            'gesamt_aktiviert': str(gesamt_aktiviert),
            'gesamt_alle': str(gesamt_alle)
        }

    def _get_kanten_beschreibung(self, kanten_typ: str) -> str:
        """Get human-readable description for edge type."""
        beschreibungen = {
            'korpus_außen': 'Korpus Außenkanten',
            'korpus_innen': 'Korpus Innenkanten',
            'tür_außen': 'Tür Außenkanten',
            'einlegeboden_vorder': 'Einlegeboden Vorderkante',
            'einlegeboden_seite': 'Einlegeboden Seitenkanten',
            'schublade_außen': 'Schublade Außenkanten',
            'rueckseite': 'Rückseite',
            'sonstiges': 'Sonstiges'
        }
        return beschreibungen.get(kanten_typ, kanten_typ.replace('_', ' ').title())


def calculate_abs_kanten_auto(
    komponenten: List[Dict[str, Any]],
    extraction_result_id: str = None
) -> Dict[str, Any]:
    """
    Convenience function for automatic ABS edge calculation.

    Args:
        komponenten: List of component dicts from extraction
        extraction_result_id: Optional extraction result ID

    Returns:
        Editable preview dict (see create_editable_preview)

    Examples:
        >>> komponenten = [
        ...     {'typ': 'Tür', 'maße': {'höhe': 2.0, 'breite': 1.0}, 'anzahl': 2},
        ...     {'typ': 'Einlegeboden', 'maße': {'breite': 2.0, 'tiefe': 0.8}, 'anzahl': 4}
        ... ]
        >>> result = calculate_abs_kanten_auto(komponenten)
        >>> print(result['gesamt_aktiviert'])  # Total activated edges
    """
    service = GeometrieService(extraction_result_id)
    berechnungen = service.calculate_abs_kanten(komponenten, apply_visibility_defaults=True)
    return service.create_editable_preview(berechnungen)
