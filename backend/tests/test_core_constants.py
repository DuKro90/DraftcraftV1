"""Tests for core constants (manufacturing specs)."""
import pytest
from decimal import Decimal
from core.constants import (
    GERMAN_WOOD_TYPES,
    COMPLEXITY_FACTORS,
    SURFACE_FACTORS,
    ADDITIONAL_FEATURES,
    UNIT_MAPPING,
    DEFAULT_HOURLY_RATE,
    DEFAULT_PROFIT_MARGIN,
)


class TestGermanWoodTypes:
    """Test wood type specifications."""

    def test_oak_exists(self):
        """Test that oak is defined."""
        assert 'eiche' in GERMAN_WOOD_TYPES
        assert GERMAN_WOOD_TYPES['eiche']['german_name'] == 'Eiche (Massivholz)'

    def test_wood_has_required_fields(self):
        """Test wood types have all required fields."""
        required_fields = [
            'german_name', 'category', 'base_time_hours_per_sqm',
            'base_material_cost_per_sqm', 'density', 'workability'
        ]
        for wood_code, wood_data in GERMAN_WOOD_TYPES.items():
            for field in required_fields:
                assert field in wood_data, f"{wood_code} missing {field}"

    def test_all_woods_have_positive_values(self):
        """Test that time and cost are positive."""
        for wood_code, wood_data in GERMAN_WOOD_TYPES.items():
            assert wood_data['base_time_hours_per_sqm'] > 0
            assert wood_data['base_material_cost_per_sqm'] > 0


class TestComplexityFactors:
    """Test complexity/craftsmanship factors."""

    def test_simple_factor_is_1_0(self):
        """Test that simple work has factor 1.0."""
        assert COMPLEXITY_FACTORS['simple']['time_factor'] == Decimal('1.0')

    def test_complexity_factors_ordered(self):
        """Test factors increase with complexity."""
        simple = COMPLEXITY_FACTORS['simple']['time_factor']
        milled = COMPLEXITY_FACTORS['milled']['time_factor']
        hand_carved = COMPLEXITY_FACTORS['hand_carved']['time_factor']

        assert simple < milled < hand_carved

    def test_all_factors_have_german_name(self):
        """Test that all factors have German description."""
        for factor_key, factor_data in COMPLEXITY_FACTORS.items():
            assert 'german_name' in factor_data
            assert len(factor_data['german_name']) > 0


class TestSurfaceFactors:
    """Test surface finish factors."""

    def test_natural_is_no_surcharge(self):
        """Test that natural finish has no material surcharge."""
        assert SURFACE_FACTORS['natural']['material_surcharge'] == Decimal('0.0')

    def test_surface_factors_have_time_and_cost(self):
        """Test surface factors have both time and material cost."""
        for surface_key, surface_data in SURFACE_FACTORS.items():
            assert 'time_factor' in surface_data
            assert 'material_surcharge' in surface_data
            assert surface_data['time_factor'] > 0


class TestAdditionalFeatures:
    """Test additional work items."""

    def test_assembly_exists(self):
        """Test assembly feature."""
        assert 'assembly' in ADDITIONAL_FEATURES
        assert ADDITIONAL_FEATURES['assembly']['time_cost_hours'] > 0

    def test_installation_takes_1_hour(self):
        """Test installation standard time."""
        assert ADDITIONAL_FEATURES['installation']['time_cost_hours'] == Decimal('1.0')


class TestUnitMapping:
    """Test supported measurement units."""

    def test_sqm_exists(self):
        """Test square meter unit."""
        assert 'sqm' in UNIT_MAPPING
        assert UNIT_MAPPING['sqm']['symbol'] == 'm²'

    def test_lfm_exists(self):
        """Test linear meter unit."""
        assert 'lfm' in UNIT_MAPPING
        assert UNIT_MAPPING['lfm']['german_name'] == 'Laufende Meter'

    def test_all_units_have_mapping(self):
        """Test all units have complete mapping."""
        required_fields = ['symbol', 'german_name', 'english_name', 'type']
        for unit_key, unit_data in UNIT_MAPPING.items():
            for field in required_fields:
                assert field in unit_data, f"{unit_key} missing {field}"


class TestDefaultValues:
    """Test default configuration values."""

    def test_hourly_rate_is_positive(self):
        """Test default hourly rate."""
        assert DEFAULT_HOURLY_RATE > 0
        assert DEFAULT_HOURLY_RATE == Decimal('75.00')

    def test_profit_margin_is_valid(self):
        """Test profit margin is between 0 and 1."""
        assert 0 < DEFAULT_PROFIT_MARGIN < 1


class TestConstantsIntegration:
    """Integration tests for constants."""

    def test_can_build_complete_product(self):
        """Test a complete product specification."""
        # Oak, 3m², milled, painted
        wood = GERMAN_WOOD_TYPES['eiche']
        complexity = COMPLEXITY_FACTORS['milled']
        surface = SURFACE_FACTORS['painted']

        base_time = Decimal('3') * wood['base_time_hours_per_sqm']
        adjusted_time = base_time * complexity['time_factor'] * surface['time_factor']

        assert adjusted_time > base_time  # Should have increased
        assert adjusted_time == Decimal('3') * Decimal('0.5') * Decimal('1.15') * Decimal('1.15')

    def test_pricing_scenario(self):
        """Test a pricing calculation scenario."""
        # Scenario: 3m² of oak, milled, painted
        quantity = Decimal('3')

        # Material costs
        base_material_cost = GERMAN_WOOD_TYPES['eiche']['base_material_cost_per_sqm']
        surface_surcharge = SURFACE_FACTORS['painted']['material_surcharge']
        total_material = (base_material_cost + surface_surcharge) * quantity

        # Labor costs
        base_time = GERMAN_WOOD_TYPES['eiche']['base_time_hours_per_sqm']
        complexity_factor = COMPLEXITY_FACTORS['milled']['time_factor']
        surface_factor = SURFACE_FACTORS['painted']['time_factor']
        total_hours = base_time * complexity_factor * surface_factor * quantity
        labor_cost = total_hours * DEFAULT_HOURLY_RATE

        # Total
        total_cost = total_material + labor_cost

        assert total_material > 0
        assert labor_cost > 0
        assert total_cost > total_material  # Material + labor
        assert total_cost == Decimal('3') * (Decimal('45.00') + Decimal('15.00')) + \
                            Decimal('0.5') * Decimal('1.15') * Decimal('1.15') * Decimal('3') * Decimal('75.00')
