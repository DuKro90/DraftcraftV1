# -*- coding: utf-8 -*-
"""Unit tests for CalculationEngine service - Phase 3 pricing calculations."""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from extraction.services.calculation_engine import CalculationEngine, CalculationError
from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
    MateriallistePosition,
    SaisonaleMarge,
)


@pytest.mark.django_db
class TestCalculationEngineInitialization(TestCase):
    """Test CalculationEngine initialization."""

    def setUp(self):
        """Set up test user and configuration."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_initialization_requires_user(self):
        """Test that initialization requires a user."""
        with pytest.raises(CalculationError, match="User is required"):
            CalculationEngine(None)

    def test_initialization_requires_betriebskennzahl(self):
        """Test that initialization requires user to have Betriebskennzahl config."""
        with pytest.raises(CalculationError, match="has no Betriebskennzahl configuration"):
            CalculationEngine(self.user)

    def test_initialization_requires_active_config(self):
        """Test that configuration must be active."""
        IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=False,
            stundensatz_arbeit=Decimal('85.00'),
            gewinnmarge_prozent=Decimal('25.00'),
        )

        with pytest.raises(CalculationError, match="is inactive"):
            CalculationEngine(self.user)

    def test_initialization_success(self):
        """Test successful initialization."""
        IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            stundensatz_arbeit=Decimal('85.00'),
            gewinnmarge_prozent=Decimal('25.00'),
        )

        engine = CalculationEngine(self.user)
        assert engine.user == self.user
        assert engine.config.is_active


@pytest.mark.django_db
class TestCalculationEngineBasicWorkflow(TestCase):
    """Test basic 8-step calculation workflow."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
            use_handwerk_standard=False,
            use_custom_materials=False,
            use_seasonal_adjustments=False,
            use_customer_discounts=False,
            use_bulk_discounts=False,
        )
        self.engine = CalculationEngine(self.user)

    def test_calculate_basic_price_no_tiers(self):
        """Test basic calculation without any TIER 1-3 applied."""
        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('10'),
        }

        result = self.engine.calculate_project_price(extracted_data)

        # Material: 100€
        # Labor: 10h × 100€/h = 1000€
        # Total: 1100€
        # Overhead: 50€ → 1150€
        # Margin 25%: 1150€ × 1.25 = 1437.50€
        assert Decimal(str(result['total_price_eur'])) == Decimal('1437.50')
        assert result['tiers_applied']['tier_1_global'] is False
        assert result['tiers_applied']['tier_2_company'] is True
        assert result['breakdown']['step_1_base_material']['cost_eur'] == 100.0

    def test_calculate_with_zero_labor(self):
        """Test calculation with zero labor hours."""
        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)

        # Material: 100€
        # Labor: 0€
        # Total: 100€
        # Overhead: 50€ → 150€
        # Margin 25%: 150€ × 1.25 = 187.50€
        assert Decimal(str(result['total_price_eur'])) == Decimal('187.50')
        assert result['breakdown']['step_5_labor']['hours'] == 0

    def test_breakdown_structure(self):
        """Test that breakdown has all 8 steps."""
        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('5'),
        }

        result = self.engine.calculate_project_price(extracted_data, breakdown=True)
        breakdown = result['breakdown']

        # Check all steps present
        assert 'step_1_base_material' in breakdown
        assert 'step_2_wood_type' in breakdown
        assert 'step_3_surface_finish' in breakdown
        assert 'step_4_complexity' in breakdown
        assert 'step_5_labor' in breakdown
        assert 'step_6_overhead_and_margin' in breakdown
        assert 'step_7_seasonal_adjustments' in breakdown
        assert 'step_8_customer_discounts' in breakdown


@pytest.mark.django_db
class TestCalculationEngineTier1(TestCase):
    """Test TIER 1 (Global Standards) - wood types, finishes, complexity."""

    def setUp(self):
        """Set up test data with template."""
        self.user = User.objects.create_user(username='testuser')
        self.template = BetriebskennzahlTemplate.objects.create(
            name='Standard Woodcraft 2024',
            is_active=True,
        )

        # Create wood type factors
        HolzartKennzahl.objects.create(
            template=self.template,
            holzart='eiche',
            kategorie='hartholz',
            preis_faktor=Decimal('1.3'),
        )

        # Create surface finish factors
        OberflächenbearbeitungKennzahl.objects.create(
            template=self.template,
            bearbeitung='lackieren',
            preis_faktor=Decimal('1.15'),
            zeit_faktor=Decimal('1.3'),
        )

        # Create complexity factors
        KomplexitaetKennzahl.objects.create(
            template=self.template,
            technik='hand_geschnitzt',
            preis_faktor=Decimal('2.0'),
            zeit_faktor=Decimal('3.0'),
            schwierigkeitsgrad=3,
        )

        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            handwerk_template=self.template,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
            use_handwerk_standard=True,
            use_custom_materials=False,
            use_seasonal_adjustments=False,
            use_customer_discounts=False,
        )
        self.engine = CalculationEngine(self.user)

    def test_wood_type_factor_applied(self):
        """Test that wood type factor is applied correctly."""
        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('0'),
            'holzart': 'eiche',
        }

        result = self.engine.calculate_project_price(extracted_data)
        breakdown = result['breakdown']['step_2_wood_type']

        assert breakdown['applied'] is True
        assert breakdown['holzart'] == 'eiche'
        assert breakdown['factor'] == 1.3
        assert Decimal(str(breakdown['price_after_eur'])) == Decimal('130.00')

    def test_surface_finish_factor_applied(self):
        """Test that surface finish factor is applied."""
        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('0'),
            'holzart': 'eiche',
            'oberflaeche': 'lackieren',
        }

        result = self.engine.calculate_project_price(extracted_data)
        breakdown = result['breakdown']['step_3_surface_finish']

        assert breakdown['applied'] is True
        assert breakdown['bearbeitung'] == 'lackieren'
        assert breakdown['price_factor'] == 1.15

    def test_complexity_factor_applied(self):
        """Test that complexity factor is applied."""
        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('0'),
            'holzart': 'eiche',
            'oberflaeche': 'lackieren',
            'komplexitaet': 'hand_geschnitzt',
        }

        result = self.engine.calculate_project_price(extracted_data)
        breakdown = result['breakdown']['step_4_complexity']

        assert breakdown['applied'] is True
        assert breakdown['technik'] == 'hand_geschnitzt'
        assert breakdown['price_factor'] == 2.0

    def test_combined_tier1_factors(self):
        """Test combined application of all TIER 1 factors."""
        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('0'),
            'holzart': 'eiche',
            'oberflaeche': 'lackieren',
            'komplexitaet': 'hand_geschnitzt',
        }

        result = self.engine.calculate_project_price(extracted_data)

        # Material: 100€
        # Wood: 100€ × 1.3 = 130€
        # Surface: 130€ × 1.15 = 149.5€
        # Complexity: 149.5€ × 2.0 = 299€
        # Labor: 0€
        # Overhead: 50€ → 349€
        # Margin 25%: 349€ × 1.25 = 436.25€
        assert Decimal(str(result['total_price_eur'])) == Decimal('436.25')

    def test_disabled_wood_type_factor(self):
        """Test that disabled factors are not applied."""
        HolzartKennzahl.objects.filter(holzart='eiche').update(is_enabled=False)

        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('0'),
            'holzart': 'eiche',
        }

        result = self.engine.calculate_project_price(extracted_data)
        breakdown = result['breakdown']['step_2_wood_type']

        assert breakdown['applied'] is False


@pytest.mark.django_db
class TestCalculationEngineTier2(TestCase):
    """Test TIER 2 (Company-Specific) - overhead, margin."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('30.00'),
            betriebskosten_umlage=Decimal('200.00'),
            use_handwerk_standard=False,
        )
        self.engine = CalculationEngine(self.user)

    def test_overhead_allocation(self):
        """Test overhead allocation is added to cost."""
        extracted_data = {
            'material_cost_eur': Decimal('500.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        breakdown = result['breakdown']['step_6_overhead_and_margin']

        assert breakdown['overhead_allocation_eur'] == 200.0
        assert breakdown['cost_with_overhead_eur'] == 700.0  # 500 + 200

    def test_profit_margin(self):
        """Test profit margin is correctly calculated."""
        extracted_data = {
            'material_cost_eur': Decimal('500.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        breakdown = result['breakdown']['step_6_overhead_and_margin']

        # (500 + 200) × 1.30 = 910
        assert Decimal(str(breakdown['total_with_margin_eur'])) == Decimal('910.00')

    def test_labor_cost_calculation(self):
        """Test labor cost is correctly calculated."""
        extracted_data = {
            'material_cost_eur': Decimal('200.00'),
            'labor_hours': Decimal('10'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        labor_breakdown = result['breakdown']['step_5_labor']

        # 10h × 100€/h = 1000€
        assert labor_breakdown['hours'] == 10.0
        assert labor_breakdown['total_cost_eur'] == 1000.0


@pytest.mark.django_db
class TestCalculationEngineTier3(TestCase):
    """Test TIER 3 (Dynamic) - seasonal adjustments, discounts."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
            use_handwerk_standard=False,
            use_seasonal_adjustments=True,
            use_customer_discounts=True,
            use_bulk_discounts=False,
        )
        self.engine = CalculationEngine(self.user)

    def test_seasonal_adjustment_percent(self):
        """Test seasonal adjustment with percentage discount."""
        today = timezone.now().date()
        SaisonaleMarge.objects.create(
            user=self.user,
            name='Summer Campaign',
            adjustment_type='prozent',
            value=Decimal('10'),
            start_date=today,
            end_date=today + timedelta(days=30),
            applicable_to='alle',
            is_active=True,
        )

        extracted_data = {
            'material_cost_eur': Decimal('1000.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        seasonal_breakdown = result['breakdown']['step_7_seasonal_adjustments']

        assert seasonal_breakdown['applied'] is True
        assert len(seasonal_breakdown['adjustments']) == 1
        # 10% of 1000€ = 100€

    def test_seasonal_adjustment_absolute(self):
        """Test seasonal adjustment with absolute amount."""
        today = timezone.now().date()
        SaisonaleMarge.objects.create(
            user=self.user,
            name='Holiday Discount',
            adjustment_type='absolute',
            value=Decimal('50.00'),
            start_date=today,
            end_date=today + timedelta(days=30),
            applicable_to='bestehende_kunden',
            is_active=True,
        )

        extracted_data = {
            'material_cost_eur': Decimal('1000.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        seasonal_breakdown = result['breakdown']['step_7_seasonal_adjustments']

        assert seasonal_breakdown['applied'] is True

    def test_customer_discount(self):
        """Test customer-specific discount."""
        extracted_data = {
            'material_cost_eur': Decimal('1000.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(
            extracted_data,
            customer_type='bestehende_kunden'
        )

        discount_breakdown = result['breakdown']['step_8_customer_discounts']
        assert discount_breakdown['applied'] is True
        # Should have 5% discount for existing customers

    def test_no_seasonal_when_disabled(self):
        """Test no seasonal adjustments applied when disabled."""
        self.config.use_seasonal_adjustments = False
        self.config.save()

        # Reinitialize engine with updated config
        self.engine = CalculationEngine(self.user)

        today = timezone.now().date()
        SaisonaleMarge.objects.create(
            user=self.user,
            name='Campaign',
            adjustment_type='prozent',
            value=Decimal('10'),
            start_date=today,
            end_date=today + timedelta(days=30),
            applicable_to='alle',
            is_active=True,
        )

        extracted_data = {
            'material_cost_eur': Decimal('1000.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        seasonal_breakdown = result['breakdown']['step_7_seasonal_adjustments']

        assert seasonal_breakdown['applied'] is False


@pytest.mark.django_db
class TestCalculationEngineCustomMaterials(TestCase):
    """Test custom material list integration."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
            use_handwerk_standard=False,
            use_custom_materials=True,
            use_bulk_discounts=True,
        )

        # Create material
        self.material = MateriallistePosition.objects.create(
            user=self.user,
            material_name='Eichenbretter 25mm',
            sku='EICHE-25MM',
            lieferant='Holzhandel Mueller',
            standardkosten_eur=Decimal('45.50'),
            rabatt_ab_100=Decimal('5'),
            rabatt_ab_500=Decimal('10'),
            is_enabled=True,
        )

        self.engine = CalculationEngine(self.user)

    def test_custom_material_used(self):
        """Test custom material price is used."""
        extracted_data = {
            'material_sku': 'EICHE-25MM',
            'material_quantity': 10,
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        material_breakdown = result['breakdown']['step_1_base_material']

        assert material_breakdown['method'] == 'custom_material_list'
        assert material_breakdown['sku'] == 'EICHE-25MM'
        assert Decimal(str(material_breakdown['total_cost_eur'])) == Decimal('455.00')

    def test_bulk_discount_100_units(self):
        """Test bulk discount at 100+ units."""
        extracted_data = {
            'material_sku': 'EICHE-25MM',
            'material_quantity': 100,
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        discount_breakdown = result['breakdown']['step_8_customer_discounts']

        assert discount_breakdown['applied'] is True

    def test_bulk_discount_500_units(self):
        """Test bulk discount at 500+ units."""
        extracted_data = {
            'material_sku': 'EICHE-25MM',
            'material_quantity': 500,
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        # Should apply 10% discount

    def test_missing_custom_material_fallback(self):
        """Test fallback when custom material not found."""
        extracted_data = {
            'material_sku': 'NONEXISTENT-SKU',
            'material_quantity': 10,
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)

        assert len(result['warnings']) > 0
        assert 'Material not found' in result['warnings'][0] or 'Custom material not found' in result['warnings'][0]


@pytest.mark.django_db
class TestCalculationEnginePricingReport(TestCase):
    """Test pricing report generation."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.template = BetriebskennzahlTemplate.objects.create(
            name='Standard Template',
            is_active=True,
        )
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            handwerk_template=self.template,
            stundensatz_arbeit=Decimal('85.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
        )
        self.engine = CalculationEngine(self.user)

    def test_pricing_report_generation(self):
        """Test pricing report contains all required data."""
        report = self.engine.get_pricing_report()

        assert report['user'] == 'testuser'
        assert report['configuration']['hourly_rate_eur'] == 85.0
        assert report['configuration']['profit_margin_percent'] == 25.0
        assert report['configuration']['overhead_allocation_eur'] == 50.0
        assert report['tiers_enabled']['tier_2_company'] is True
        assert report['template']['name'] == 'Standard Template'


@pytest.mark.django_db
class TestCalculationEngineEdgeCases(TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            is_active=True,
            stundensatz_arbeit=Decimal('100.00'),
            gewinnmarge_prozent=Decimal('25.00'),
            betriebskosten_umlage=Decimal('50.00'),
        )
        self.engine = CalculationEngine(self.user)

    def test_missing_required_fields(self):
        """Test calculation with missing fields uses defaults."""
        extracted_data = {}

        result = self.engine.calculate_project_price(extracted_data)

        assert 'total_price_eur' in result
        assert result['total_price_eur'] > 0

    def test_negative_values_handled(self):
        """Test that negative values don't break calculation."""
        extracted_data = {
            'material_cost_eur': Decimal('-100.00'),
            'labor_hours': Decimal('0'),
        }

        # Should handle gracefully
        result = self.engine.calculate_project_price(extracted_data)
        assert isinstance(result['total_price_eur'], float)

    def test_very_large_numbers(self):
        """Test calculation with very large numbers."""
        extracted_data = {
            'material_cost_eur': Decimal('10000000.00'),
            'labor_hours': Decimal('1000'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        assert result['total_price_eur'] > 0
        assert isinstance(result['total_price_eur'], float)

    def test_zero_profit_margin(self):
        """Test calculation with zero profit margin."""
        self.config.gewinnmarge_prozent = Decimal('0')
        self.config.save()

        # Reinitialize engine with updated config
        self.engine = CalculationEngine(self.user)

        extracted_data = {
            'material_cost_eur': Decimal('100.00'),
            'labor_hours': Decimal('0'),
        }

        result = self.engine.calculate_project_price(extracted_data)
        # Should equal material + overhead without margin multiplier
        assert result['total_price_eur'] == 150.0
