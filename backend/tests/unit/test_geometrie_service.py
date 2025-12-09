"""
Unit tests for GeometrieService - Phase 4B

Tests automatic geometry-based calculations for ABS edge lengths.
"""

import pytest
from decimal import Decimal
from documents.services.geometrie_service import (
    GeometrieService,
    KantenBerechnung,
    GeometrieServiceError,
    calculate_abs_kanten_auto
)


class TestGeometrieService:
    """Test suite for GeometrieService."""

    @pytest.fixture
    def service(self):
        """Initialize service."""
        return GeometrieService(extraction_result_id='test-123')

    # =========================================================================
    # TÜR (DOOR) CALCULATIONS
    # =========================================================================

    def test_calculate_tür_kanten_single(self, service):
        """Test edge calculation for single door."""
        maße = {'höhe': 2.0, 'breite': 1.0}
        berechnungen = service._calculate_tür_kanten(maße, anzahl=1, komponente={})

        assert len(berechnungen) == 1
        berechnung = berechnungen[0]

        # Perimeter: 2 × (2.0 + 1.0) = 6.0 lfm
        assert berechnung.berechnete_laenge == Decimal('6.0')
        assert berechnung.kanten_typ == 'tür_außen'
        assert berechnung.ist_sichtbar is True

    def test_calculate_tür_kanten_multiple(self, service):
        """Test edge calculation for multiple doors."""
        maße = {'höhe': 2.0, 'breite': 1.0}
        berechnungen = service._calculate_tür_kanten(maße, anzahl=2, komponente={})

        assert len(berechnungen) == 1
        # Perimeter: 2 × (2.0 + 1.0) × 2 = 12.0 lfm
        assert berechnungen[0].berechnete_laenge == Decimal('12.0')

    # =========================================================================
    # KORPUS (CABINET BODY) CALCULATIONS
    # =========================================================================

    def test_calculate_korpus_kanten(self, service):
        """Test edge calculation for cabinet body."""
        maße = {'höhe': 2.0, 'breite': 2.0, 'tiefe': 0.8}
        berechnungen = service._calculate_korpus_kanten(maße, anzahl=1, komponente={})

        assert len(berechnungen) == 2  # Außen + Innen

        # Find außen and innen
        außen = next(b for b in berechnungen if b.kanten_typ == 'korpus_außen')
        innen = next(b for b in berechnungen if b.kanten_typ == 'korpus_innen')

        # Außen: 2 × (höhe + breite) = 2 × (2.0 + 2.0) = 8.0
        assert außen.berechnete_laenge == Decimal('8.0')
        assert außen.ist_sichtbar is True

        # Innen: 2 × tiefe = 2 × 0.8 = 1.6
        assert innen.berechnete_laenge == Decimal('1.6')
        assert innen.ist_sichtbar is False

    # =========================================================================
    # EINLEGEBODEN (SHELF) CALCULATIONS
    # =========================================================================

    def test_calculate_einlegeboden_kanten_single(self, service):
        """Test edge calculation for single shelf."""
        maße = {'breite': 2.0, 'tiefe': 0.8}
        berechnungen = service._calculate_einlegeboden_kanten(maße, anzahl=1, komponente={})

        assert len(berechnungen) == 2  # Vorder + Seiten

        vorder = next(b for b in berechnungen if b.kanten_typ == 'einlegeboden_vorder')
        seiten = next(b for b in berechnungen if b.kanten_typ == 'einlegeboden_seite')

        # Vorder: breite = 2.0
        assert vorder.berechnete_laenge == Decimal('2.0')
        assert vorder.ist_sichtbar is True

        # Seiten: 2 × tiefe = 2 × 0.8 = 1.6
        assert seiten.berechnete_laenge == Decimal('1.6')
        assert seiten.ist_sichtbar is False

    def test_calculate_einlegeboden_kanten_multiple(self, service):
        """Test edge calculation for multiple shelves."""
        maße = {'breite': 2.0, 'tiefe': 0.8}
        berechnungen = service._calculate_einlegeboden_kanten(maße, anzahl=4, komponente={})

        vorder = next(b for b in berechnungen if b.kanten_typ == 'einlegeboden_vorder')
        seiten = next(b for b in berechnungen if b.kanten_typ == 'einlegeboden_seite')

        # Vorder: 2.0 × 4 = 8.0
        assert vorder.berechnete_laenge == Decimal('8.0')

        # Seiten: 2 × 0.8 × 4 = 6.4
        assert seiten.berechnete_laenge == Decimal('6.4')

    # =========================================================================
    # SCHUBLADE (DRAWER) CALCULATIONS
    # =========================================================================

    def test_calculate_schublade_kanten(self, service):
        """Test edge calculation for drawers."""
        maße = {'höhe': 0.2, 'breite': 0.8}
        berechnungen = service._calculate_schublade_kanten(maße, anzahl=3, komponente={})

        assert len(berechnungen) == 1

        # Perimeter: 2 × (0.2 + 0.8) × 3 = 6.0
        assert berechnungen[0].berechnete_laenge == Decimal('6.0')
        assert berechnungen[0].kanten_typ == 'schublade_außen'

    # =========================================================================
    # COMPLETE COMPONENT SET CALCULATIONS
    # =========================================================================

    def test_calculate_abs_kanten_complete_set(self, service):
        """Test complete calculation for cabinet with multiple components."""
        komponenten = [
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
            {
                'typ': 'Einlegeboden',
                'maße': {'breite': 2.0, 'tiefe': 0.8},
                'anzahl': 4
            }
        ]

        berechnungen = service.calculate_abs_kanten(komponenten, apply_visibility_defaults=True)

        # Should have multiple edge segments
        assert len(berechnungen) > 0

        # Check that visibility defaults were applied
        visible_count = sum(1 for b in berechnungen if b.ist_aktiviert)
        hidden_count = sum(1 for b in berechnungen if not b.ist_aktiviert)

        # Außenkanten should be activated, Innenkanten should not
        assert visible_count > 0
        assert hidden_count > 0

    def test_calculate_abs_kanten_without_visibility_defaults(self, service):
        """Test calculation without applying visibility defaults."""
        komponenten = [
            {
                'typ': 'Tür',
                'maße': {'höhe': 2.0, 'breite': 1.0},
                'anzahl': 2
            }
        ]

        berechnungen = service.calculate_abs_kanten(komponenten, apply_visibility_defaults=False)

        # All should be activated by default when no defaults applied
        assert all(b.ist_aktiviert for b in berechnungen)

    # =========================================================================
    # TOTAL LENGTH CALCULATIONS
    # =========================================================================

    def test_calculate_total_kanten_länge_all_activated(self, service):
        """Test total length calculation with all edges activated."""
        berechnungen = [
            KantenBerechnung('tür_außen', 'formula', Decimal('12.0'), {}, True, True),
            KantenBerechnung('korpus_außen', 'formula', Decimal('8.0'), {}, True, True),
            KantenBerechnung('einlegeboden_vorder', 'formula', Decimal('8.0'), {}, True, True)
        ]

        total = service.calculate_total_kanten_länge(berechnungen, nur_aktivierte=True)
        assert total == Decimal('28.0')

    def test_calculate_total_kanten_länge_mixed_activation(self, service):
        """Test total length with mixed activation states."""
        berechnungen = [
            KantenBerechnung('tür_außen', 'formula', Decimal('12.0'), {}, True, True),
            KantenBerechnung('korpus_innen', 'formula', Decimal('8.0'), {}, False, False),
            KantenBerechnung('einlegeboden_vorder', 'formula', Decimal('8.0'), {}, True, True)
        ]

        # Only activated
        total_activated = service.calculate_total_kanten_länge(berechnungen, nur_aktivierte=True)
        assert total_activated == Decimal('20.0')  # 12 + 8

        # All edges
        total_all = service.calculate_total_kanten_länge(berechnungen, nur_aktivierte=False)
        assert total_all == Decimal('28.0')  # 12 + 8 + 8

    # =========================================================================
    # EDITABLE PREVIEW TESTS
    # =========================================================================

    def test_create_editable_preview(self, service):
        """Test creation of editable preview for frontend."""
        berechnungen = [
            KantenBerechnung('tür_außen', '2 × (2.0m + 1.0m) × 2', Decimal('12.0'), {'typ': 'Tür'}, True, True),
            KantenBerechnung('korpus_innen', '2 × 0.8m', Decimal('1.6'), {'typ': 'Korpus'}, False, False)
        ]

        preview = service.create_editable_preview(berechnungen)

        assert 'kanten' in preview
        assert 'gesamt_aktiviert' in preview
        assert 'gesamt_alle' in preview

        assert len(preview['kanten']) == 2
        assert preview['gesamt_aktiviert'] == '12.0'
        assert preview['gesamt_alle'] == '13.6'

        # Check first kante structure
        kante1 = preview['kanten'][0]
        assert kante1['typ'] == 'tür_außen'
        assert kante1['länge'] == '12.0'
        assert kante1['einheit'] == 'lfm'
        assert kante1['ist_aktiviert'] is True
        assert 'beschreibung' in kante1
        assert 'formel' in kante1

    # =========================================================================
    # CONVENIENCE FUNCTION TESTS
    # =========================================================================

    def test_calculate_abs_kanten_auto_convenience(self):
        """Test convenience function."""
        komponenten = [
            {'typ': 'Tür', 'maße': {'höhe': 2.0, 'breite': 1.0}, 'anzahl': 2}
        ]

        result = calculate_abs_kanten_auto(komponenten, extraction_result_id='test-456')

        assert 'kanten' in result
        assert 'gesamt_aktiviert' in result
        assert len(result['kanten']) > 0

    # =========================================================================
    # EDGE CASES & ERROR HANDLING
    # =========================================================================

    def test_empty_komponenten_list(self, service):
        """Test with empty components list."""
        berechnungen = service.calculate_abs_kanten([], apply_visibility_defaults=True)
        assert len(berechnungen) == 0

    def test_component_without_maße(self, service):
        """Test component without dimensions."""
        komponenten = [
            {
                'typ': 'Tür',
                # Missing 'maße'
                'anzahl': 2
            }
        ]

        berechnungen = service.calculate_abs_kanten(komponenten)
        # Should skip component with warning
        assert len(berechnungen) == 0

    def test_unknown_component_type(self, service):
        """Test unknown component type uses generic calculation."""
        komponenten = [
            {
                'typ': 'UnknownType',
                'maße': {'höhe': 1.0, 'breite': 2.0},
                'anzahl': 1
            }
        ]

        berechnungen = service.calculate_abs_kanten(komponenten)

        # Should use generic calculation
        assert len(berechnungen) == 1
        assert berechnungen[0].kanten_typ == 'sonstiges'
        # Generic: 2 × (1.0 + 2.0) = 6.0
        assert berechnungen[0].berechnete_laenge == Decimal('6.0')

    def test_generic_calculation_insufficient_dimensions(self, service):
        """Test generic calculation with insufficient dimensions."""
        maße = {'höhe': 1.0}  # Only one dimension
        berechnungen = service._calculate_generic_kanten(maße, anzahl=1, komponente={})

        # Should return empty list with warning
        assert len(berechnungen) == 0

    # =========================================================================
    # REAL-WORLD SCENARIO TESTS
    # =========================================================================

    def test_realistic_cabinet_scenario(self, service):
        """
        Test realistic scenario: Schrank 2×2×0.8m with 2 doors, 4 shelves.

        Expected activated edges (visibility defaults):
        - Korpus Außenkanten: 8.0 lfm ✓
        - Tür Außenkanten: 12.0 lfm ✓
        - Einlegeboden Vorderkante: 8.0 lfm ✓
        - Einlegeboden Seitenkanten: 6.4 lfm ✗ (not visible)
        - Korpus Innenkanten: 1.6 lfm ✗ (not visible)

        Total activated: 28.0 lfm
        Total all: 36.0 lfm
        """
        komponenten = [
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
            {
                'typ': 'Einlegeboden',
                'maße': {'breite': 2.0, 'tiefe': 0.8},
                'anzahl': 4
            }
        ]

        berechnungen = service.calculate_abs_kanten(komponenten, apply_visibility_defaults=True)
        preview = service.create_editable_preview(berechnungen)

        # Check totals
        gesamt_aktiviert = Decimal(preview['gesamt_aktiviert'])
        gesamt_alle = Decimal(preview['gesamt_alle'])

        assert gesamt_aktiviert == Decimal('28.0')
        assert gesamt_alle == Decimal('36.0')

        # Check individual segments
        kanten_dict = {k['typ']: Decimal(k['länge']) for k in preview['kanten']}

        assert kanten_dict['korpus_außen'] == Decimal('8.0')
        assert kanten_dict['tür_außen'] == Decimal('12.0')
        assert kanten_dict['einlegeboden_vorder'] == Decimal('8.0')
        assert kanten_dict['einlegeboden_seite'] == Decimal('6.4')
        assert kanten_dict['korpus_innen'] == Decimal('1.6')
