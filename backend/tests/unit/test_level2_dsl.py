"""
Unit Tests for Level 2 DSL Operations - Phase 4C

Tests for conditional logic, comparisons, and logical operations in the DSL.

Author: Claude Code
Created: December 2025
"""

import pytest
from decimal import Decimal
from documents.services.bauteil_regel_engine import (
    BauteilRegelEngine,
    InvalidRuleError,
    ComponentNotFoundError,
)


class TestLevel2IfThenElse:
    """Tests for IF_THEN_ELSE conditional logic."""

    def test_if_then_else_greater_than_true_branch(self):
        """Test IF_THEN_ELSE with GREATER_THAN condition evaluating to TRUE."""
        components = {"Tür": {"anzahl": 2, "höhe": 2.5}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "GREATER_THAN",
                "links": {"komponente": "Tür", "attribut": "höhe"},
                "rechts": 2.0,
            },
            "dann": {"operation": "FIXED", "wert": 4},
            "sonst": {"operation": "FIXED", "wert": 3},
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("4")  # Height 2.5 > 2.0, so THEN branch

    def test_if_then_else_greater_than_false_branch(self):
        """Test IF_THEN_ELSE with GREATER_THAN condition evaluating to FALSE."""
        components = {"Tür": {"anzahl": 2, "höhe": 1.8}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "GREATER_THAN",
                "links": {"komponente": "Tür", "attribut": "höhe"},
                "rechts": 2.0,
            },
            "dann": {"operation": "FIXED", "wert": 4},
            "sonst": {"operation": "FIXED", "wert": 3},
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("3")  # Height 1.8 < 2.0, so ELSE branch

    def test_if_then_else_equals_condition(self):
        """Test IF_THEN_ELSE with EQUALS condition."""
        components = {"Tür": {"anzahl": 5, "breite": 1.0}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "EQUALS",
                "links": {"komponente": "Tür", "attribut": "anzahl"},
                "rechts": 5,
            },
            "dann": {"operation": "MULTIPLY", "faktor": 10, "komponente": "Tür", "attribut": "anzahl"},
            "sonst": {"operation": "MULTIPLY", "faktor": 8, "komponente": "Tür", "attribut": "anzahl"},
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("50")  # 5 == 5, so 10 × 5 = 50

    def test_if_then_else_nested_conditions(self):
        """Test nested IF_THEN_ELSE logic."""
        components = {"Tür": {"höhe": 2.2, "breite": 1.2, "anzahl": 3}}
        engine = BauteilRegelEngine(components)

        # IF höhe > 2.0 THEN
        #   IF breite > 1.0 THEN 5 ELSE 4
        # ELSE 3
        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "GREATER_THAN",
                "links": {"komponente": "Tür", "attribut": "höhe"},
                "rechts": 2.0,
            },
            "dann": {
                "operation": "IF_THEN_ELSE",
                "bedingung": {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "breite"},
                    "rechts": 1.0,
                },
                "dann": {"operation": "FIXED", "wert": 5},
                "sonst": {"operation": "FIXED", "wert": 4},
            },
            "sonst": {"operation": "FIXED", "wert": 3},
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("5")  # höhe 2.2 > 2.0 AND breite 1.2 > 1.0


class TestLevel2Comparisons:
    """Tests for comparison operations (GREATER_THAN, LESS_THAN, etc.)."""

    def test_greater_than_true(self):
        """Test GREATER_THAN comparison returning TRUE."""
        components = {"Material": {"menge": 100}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "GREATER_THAN",
            "links": {"komponente": "Material", "attribut": "menge"},
            "rechts": 50,
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # 100 > 50 = TRUE (1)

    def test_greater_than_false(self):
        """Test GREATER_THAN comparison returning FALSE."""
        components = {"Material": {"menge": 30}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "GREATER_THAN",
            "links": {"komponente": "Material", "attribut": "menge"},
            "rechts": 50,
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("0")  # 30 < 50 = FALSE (0)

    def test_less_than_true(self):
        """Test LESS_THAN comparison returning TRUE."""
        components = {"Material": {"menge": 20}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "LESS_THAN",
            "links": {"komponente": "Material", "attribut": "menge"},
            "rechts": 50,
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # 20 < 50 = TRUE (1)

    def test_equals_true(self):
        """Test EQUALS comparison returning TRUE."""
        components = {"Material": {"menge": 50}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "EQUALS",
            "links": {"komponente": "Material", "attribut": "menge"},
            "rechts": 50,
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # 50 == 50 = TRUE (1)

    def test_greater_equal_boundary(self):
        """Test GREATER_EQUAL at boundary value."""
        components = {"Material": {"menge": 50}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "GREATER_EQUAL",
            "links": {"komponente": "Material", "attribut": "menge"},
            "rechts": 50,
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # 50 >= 50 = TRUE (1)

    def test_less_equal_boundary(self):
        """Test LESS_EQUAL at boundary value."""
        components = {"Material": {"menge": 50}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "LESS_EQUAL",
            "links": {"komponente": "Material", "attribut": "menge"},
            "rechts": 50,
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # 50 <= 50 = TRUE (1)


class TestLevel2LogicalOperations:
    """Tests for logical operations (AND, OR)."""

    def test_and_both_true(self):
        """Test AND with both conditions TRUE."""
        components = {"Tür": {"höhe": 2.5, "breite": 1.2}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "AND",
            "bedingungen": [
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "höhe"},
                    "rechts": 2.0,
                },
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "breite"},
                    "rechts": 1.0,
                },
            ],
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # TRUE AND TRUE = TRUE (1)

    def test_and_one_false(self):
        """Test AND with one condition FALSE."""
        components = {"Tür": {"höhe": 2.5, "breite": 0.8}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "AND",
            "bedingungen": [
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "höhe"},
                    "rechts": 2.0,
                },
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "breite"},
                    "rechts": 1.0,
                },
            ],
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("0")  # TRUE AND FALSE = FALSE (0)

    def test_or_both_true(self):
        """Test OR with both conditions TRUE."""
        components = {"Tür": {"höhe": 2.5, "breite": 1.2}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "OR",
            "bedingungen": [
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "höhe"},
                    "rechts": 2.0,
                },
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "breite"},
                    "rechts": 1.0,
                },
            ],
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # TRUE OR TRUE = TRUE (1)

    def test_or_one_true(self):
        """Test OR with one condition TRUE."""
        components = {"Tür": {"höhe": 2.5, "breite": 0.8}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "OR",
            "bedingungen": [
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "höhe"},
                    "rechts": 2.0,
                },
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "breite"},
                    "rechts": 1.0,
                },
            ],
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("1")  # TRUE OR FALSE = TRUE (1)

    def test_or_both_false(self):
        """Test OR with both conditions FALSE."""
        components = {"Tür": {"höhe": 1.8, "breite": 0.8}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "OR",
            "bedingungen": [
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "höhe"},
                    "rechts": 2.0,
                },
                {
                    "operation": "GREATER_THAN",
                    "links": {"komponente": "Tür", "attribut": "breite"},
                    "rechts": 1.0,
                },
            ],
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("0")  # FALSE OR FALSE = FALSE (0)


class TestPauschaleContext:
    """Tests for Pauschale calculations using context instead of components."""

    def test_pauschale_context_simple(self):
        """Test simple context-based calculation for Pauschale."""
        engine = BauteilRegelEngine({})
        engine.context = {"distanz_km": 75}

        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "GREATER_THAN",
                "links": {"quelle": "distanz_km"},
                "rechts": 50,
            },
            "dann": {"operation": "FIXED", "wert": 100},
            "sonst": {"operation": "FIXED", "wert": 50},
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("100")  # 75km > 50km, so 100 EUR

    def test_pauschale_context_multiple_conditions(self):
        """Test Pauschale with multiple context conditions."""
        engine = BauteilRegelEngine({})
        engine.context = {"distanz_km": 75, "montage_stunden": 10}

        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "AND",
                "bedingungen": [
                    {
                        "operation": "GREATER_THAN",
                        "links": {"quelle": "distanz_km"},
                        "rechts": 50,
                    },
                    {
                        "operation": "GREATER_THAN",
                        "links": {"quelle": "montage_stunden"},
                        "rechts": 8,
                    },
                ],
            },
            "dann": {"operation": "FIXED", "wert": 150},
            "sonst": {"operation": "FIXED", "wert": 75},
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("150")  # Both conditions TRUE


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_topfband_calculation_scenario(self):
        """
        Real-world scenario: Topfband quantity based on door height.

        Rule: If door height > 2.0m, use 4 hinges per door, else 3.
        """
        components = {"Tür": {"höhe": 2.3, "anzahl": 5}}
        engine = BauteilRegelEngine(components)

        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "GREATER_THAN",
                "links": {"komponente": "Tür", "attribut": "höhe"},
                "rechts": 2.0,
            },
            "dann": {
                "operation": "MULTIPLY",
                "faktor": 4,
                "komponente": "Tür",
                "attribut": "anzahl",
            },
            "sonst": {
                "operation": "MULTIPLY",
                "faktor": 3,
                "komponente": "Tür",
                "attribut": "anzahl",
            },
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("20")  # 2.3m > 2.0m → 4 hinges × 5 doors = 20

    def test_anfahrtspauschale_scenario(self):
        """
        Real-world scenario: Anfahrtspauschale based on distance.

        Rule:
        - Distance > 100km: 150 EUR
        - Distance > 50km: 100 EUR
        - Else: 50 EUR
        """
        engine = BauteilRegelEngine({})
        engine.context = {"distanz_km": 85}

        regel = {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "GREATER_THAN",
                "links": {"quelle": "distanz_km"},
                "rechts": 100,
            },
            "dann": {"operation": "FIXED", "wert": 150},
            "sonst": {
                "operation": "IF_THEN_ELSE",
                "bedingung": {
                    "operation": "GREATER_THAN",
                    "links": {"quelle": "distanz_km"},
                    "rechts": 50,
                },
                "dann": {"operation": "FIXED", "wert": 100},
                "sonst": {"operation": "FIXED", "wert": 50},
            },
        }

        result = engine.execute_rule(regel)
        assert result == Decimal("100")  # 85km > 50km but < 100km → 100 EUR
