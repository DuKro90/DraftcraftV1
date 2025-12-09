"""
Unit tests for BauteilRegelEngine - Phase 4B

Tests Level 1 DSL operations:
- MULTIPLY
- ADD
- SUBTRACT
- FIXED
"""

import pytest
from decimal import Decimal
from documents.services.bauteil_regel_engine import (
    BauteilRegelEngine,
    RegelEngineError,
    InvalidRuleError,
    ComponentNotFoundError,
    calculate_bauteil_menge
)


class TestBauteilRegelEngine:
    """Test suite for BauteilRegelEngine."""

    @pytest.fixture
    def sample_components(self):
        """Sample extracted components for testing."""
        return {
            'Tür': {
                'anzahl': 2,
                'höhe': 2.0,
                'breite': 1.0
            },
            'Schublade': {
                'anzahl': 3,
                'höhe': 0.2,
                'breite': 0.8
            },
            'Einlegeboden': {
                'anzahl': 4,
                'breite': 2.0,
                'tiefe': 0.8
            }
        }

    @pytest.fixture
    def engine(self, sample_components):
        """Initialize engine with sample components."""
        return BauteilRegelEngine(sample_components)

    # =========================================================================
    # MULTIPLY OPERATION TESTS
    # =========================================================================

    def test_multiply_basic(self, engine):
        """Test basic multiplication: 3 × Tür.anzahl."""
        regel = {
            'operation': 'MULTIPLY',
            'faktor': 3,
            'komponente': 'Tür',
            'attribut': 'anzahl'
        }

        result = engine.execute_rule(regel)
        assert result == Decimal('6')  # 3 × 2

    def test_multiply_with_decimal_factor(self, engine):
        """Test multiplication with decimal factor."""
        regel = {
            'operation': 'MULTIPLY',
            'faktor': 2.5,
            'komponente': 'Schublade',
            'attribut': 'anzahl'
        }

        result = engine.execute_rule(regel)
        assert result == Decimal('7.5')  # 2.5 × 3

    def test_multiply_component_not_found(self, engine):
        """Test multiplication with non-existent component."""
        regel = {
            'operation': 'MULTIPLY',
            'faktor': 3,
            'komponente': 'Fenster',  # Doesn't exist
            'attribut': 'anzahl'
        }

        with pytest.raises(ComponentNotFoundError) as exc_info:
            engine.execute_rule(regel)

        assert 'Fenster' in str(exc_info.value)

    def test_multiply_attribute_not_found(self, engine):
        """Test multiplication with non-existent attribute."""
        regel = {
            'operation': 'MULTIPLY',
            'faktor': 3,
            'komponente': 'Tür',
            'attribut': 'gewicht'  # Doesn't exist
        }

        with pytest.raises(ComponentNotFoundError) as exc_info:
            engine.execute_rule(regel)

        assert 'gewicht' in str(exc_info.value)

    def test_multiply_missing_faktor(self, engine):
        """Test multiplication with missing faktor field."""
        regel = {
            'operation': 'MULTIPLY',
            'komponente': 'Tür',
            'attribut': 'anzahl'
            # Missing 'faktor'
        }

        with pytest.raises(InvalidRuleError) as exc_info:
            engine.execute_rule(regel)

        assert 'faktor' in str(exc_info.value)

    # =========================================================================
    # ADD OPERATION TESTS
    # =========================================================================

    def test_add_two_terms(self, engine):
        """Test addition of two terms."""
        regel = {
            'operation': 'ADD',
            'terme': [
                {
                    'operation': 'MULTIPLY',
                    'faktor': 3,
                    'komponente': 'Tür',
                    'attribut': 'anzahl'
                },
                {
                    'operation': 'MULTIPLY',
                    'faktor': 2,
                    'komponente': 'Schublade',
                    'attribut': 'anzahl'
                }
            ]
        }

        result = engine.execute_rule(regel)
        # (3 × 2) + (2 × 3) = 6 + 6 = 12
        assert result == Decimal('12')

    def test_add_multiple_terms(self, engine):
        """Test addition of multiple terms."""
        regel = {
            'operation': 'ADD',
            'terme': [
                {'operation': 'MULTIPLY', 'faktor': 3, 'komponente': 'Tür', 'attribut': 'anzahl'},
                {'operation': 'MULTIPLY', 'faktor': 2, 'komponente': 'Schublade', 'attribut': 'anzahl'},
                {'operation': 'MULTIPLY', 'faktor': 1, 'komponente': 'Einlegeboden', 'attribut': 'anzahl'},
                {'operation': 'FIXED', 'wert': 10}
            ]
        }

        result = engine.execute_rule(regel)
        # (3×2) + (2×3) + (1×4) + 10 = 6 + 6 + 4 + 10 = 26
        assert result == Decimal('26')

    def test_add_empty_terms(self, engine):
        """Test ADD with empty terms list."""
        regel = {
            'operation': 'ADD',
            'terme': []
        }

        with pytest.raises(InvalidRuleError):
            engine.execute_rule(regel)

    def test_add_not_a_list(self, engine):
        """Test ADD with terme not being a list."""
        regel = {
            'operation': 'ADD',
            'terme': 'not-a-list'
        }

        with pytest.raises(InvalidRuleError):
            engine.execute_rule(regel)

    # =========================================================================
    # SUBTRACT OPERATION TESTS
    # =========================================================================

    def test_subtract_basic(self, engine):
        """Test basic subtraction."""
        regel = {
            'operation': 'SUBTRACT',
            'minuend': {
                'operation': 'MULTIPLY',
                'faktor': 10,
                'komponente': 'Tür',
                'attribut': 'anzahl'
            },
            'subtrahend': {
                'operation': 'MULTIPLY',
                'faktor': 2,
                'komponente': 'Schublade',
                'attribut': 'anzahl'
            }
        }

        result = engine.execute_rule(regel)
        # (10 × 2) - (2 × 3) = 20 - 6 = 14
        assert result == Decimal('14')

    def test_subtract_with_fixed(self, engine):
        """Test subtraction with fixed value."""
        regel = {
            'operation': 'SUBTRACT',
            'minuend': {
                'operation': 'FIXED',
                'wert': 100
            },
            'subtrahend': {
                'operation': 'MULTIPLY',
                'faktor': 5,
                'komponente': 'Tür',
                'attribut': 'anzahl'
            }
        }

        result = engine.execute_rule(regel)
        # 100 - (5 × 2) = 100 - 10 = 90
        assert result == Decimal('90')

    def test_subtract_negative_result(self, engine):
        """Test subtraction resulting in negative number."""
        regel = {
            'operation': 'SUBTRACT',
            'minuend': {
                'operation': 'FIXED',
                'wert': 5
            },
            'subtrahend': {
                'operation': 'FIXED',
                'wert': 10
            }
        }

        result = engine.execute_rule(regel)
        assert result == Decimal('-5')

    # =========================================================================
    # FIXED OPERATION TESTS
    # =========================================================================

    def test_fixed_integer(self, engine):
        """Test fixed value with integer."""
        regel = {
            'operation': 'FIXED',
            'wert': 10
        }

        result = engine.execute_rule(regel)
        assert result == Decimal('10')

    def test_fixed_decimal(self, engine):
        """Test fixed value with decimal."""
        regel = {
            'operation': 'FIXED',
            'wert': 12.5
        }

        result = engine.execute_rule(regel)
        assert result == Decimal('12.5')

    def test_fixed_missing_wert(self, engine):
        """Test FIXED with missing wert field."""
        regel = {
            'operation': 'FIXED'
        }

        with pytest.raises(InvalidRuleError):
            engine.execute_rule(regel)

    # =========================================================================
    # VALIDATION TESTS
    # =========================================================================

    def test_validate_rule_valid(self, engine):
        """Test validation of valid rule."""
        regel = {
            'operation': 'MULTIPLY',
            'faktor': 3,
            'komponente': 'Tür',
            'attribut': 'anzahl'
        }

        result = engine.validate_rule(regel)

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert 'Tür' in result['referenced_components']

    def test_validate_rule_invalid_operation(self, engine):
        """Test validation with unsupported operation."""
        regel = {
            'operation': 'DIVIDE',  # Not supported
            'faktor': 3
        }

        result = engine.validate_rule(regel)

        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert 'DIVIDE' in result['errors'][0]

    def test_validate_rule_complex(self, engine):
        """Test validation of complex nested rule."""
        regel = {
            'operation': 'ADD',
            'terme': [
                {'operation': 'MULTIPLY', 'faktor': 3, 'komponente': 'Tür', 'attribut': 'anzahl'},
                {'operation': 'MULTIPLY', 'faktor': 2, 'komponente': 'Schublade', 'attribut': 'anzahl'}
            ]
        }

        result = engine.validate_rule(regel)

        assert result['valid'] is True
        assert 'Tür' in result['referenced_components']
        assert 'Schublade' in result['referenced_components']

    # =========================================================================
    # CONVENIENCE FUNCTION TESTS
    # =========================================================================

    def test_calculate_bauteil_menge_convenience(self, sample_components):
        """Test convenience function."""
        regel = {
            'operation': 'MULTIPLY',
            'faktor': 3,
            'komponente': 'Tür',
            'attribut': 'anzahl'
        }

        result = calculate_bauteil_menge(regel, sample_components)
        assert result == Decimal('6')

    # =========================================================================
    # EDGE CASES & ERROR HANDLING
    # =========================================================================

    def test_unsupported_operation(self, engine):
        """Test with completely unsupported operation."""
        regel = {
            'operation': 'UNKNOWN_OP'
        }

        with pytest.raises(InvalidRuleError) as exc_info:
            engine.execute_rule(regel)

        assert 'UNKNOWN_OP' in str(exc_info.value)

    def test_empty_components(self):
        """Test engine with empty components dict."""
        engine = BauteilRegelEngine({})

        regel = {
            'operation': 'MULTIPLY',
            'faktor': 3,
            'komponente': 'Tür',
            'attribut': 'anzahl'
        }

        with pytest.raises(ComponentNotFoundError):
            engine.execute_rule(regel)

    def test_deeply_nested_add(self, engine):
        """Test deeply nested ADD operations."""
        regel = {
            'operation': 'ADD',
            'terme': [
                {
                    'operation': 'ADD',
                    'terme': [
                        {'operation': 'FIXED', 'wert': 5},
                        {'operation': 'FIXED', 'wert': 10}
                    ]
                },
                {'operation': 'FIXED', 'wert': 20}
            ]
        }

        result = engine.execute_rule(regel)
        # ((5 + 10) + 20) = 35
        assert result == Decimal('35')
