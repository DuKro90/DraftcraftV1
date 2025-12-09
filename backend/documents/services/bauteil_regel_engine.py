"""
Bauteil Regel-Engine - Phase 4B + 4C (Level 1 + Level 2)

DSL (Domain Specific Language) for component quantity calculation.

Level 1 (Phase 4B):
- MULTIPLY: factor × component_count
- ADD: sum of multiple terms
- SUBTRACT: difference
- FIXED: constant value

Level 2 (Phase 4C):
- IF_THEN_ELSE: conditional logic
- GREATER_THAN: comparison >
- LESS_THAN: comparison <
- EQUALS: comparison ==
- GREATER_EQUAL: comparison >=
- LESS_EQUAL: comparison <=
- AND: logical AND
- OR: logical OR

Example Rules:
    Level 1:
    {"operation": "MULTIPLY", "faktor": 3, "komponente": "Tür", "attribut": "anzahl"}
    → 3 × Anzahl Türen

    Level 2:
    {
        "operation": "IF_THEN_ELSE",
        "bedingung": {
            "operation": "GREATER_THAN",
            "links": {"komponente": "Tür", "attribut": "höhe"},
            "rechts": 2.0
        },
        "dann": {"operation": "MULTIPLY", "faktor": 4, "komponente": "Tür", "attribut": "anzahl"},
        "sonst": {"operation": "MULTIPLY", "faktor": 3, "komponente": "Tür", "attribut": "anzahl"}
    }
    → IF Türhöhe > 2.0m THEN 4 Topfbänder ELSE 3 Topfbänder
"""

from typing import Dict, Any, List, Union
from decimal import Decimal
import logging
from .level2_dsl_operations import execute_if_then_else, execute_comparison, execute_logical

logger = logging.getLogger(__name__)


class RegelEngineError(Exception):
    """Base exception for rule engine errors."""
    pass


class InvalidRuleError(RegelEngineError):
    """Raised when rule definition is invalid."""
    pass


class ComponentNotFoundError(RegelEngineError):
    """Raised when referenced component doesn't exist in extraction data."""
    pass


class BauteilRegelEngine:
    """
    Level 1 + Level 2 Rule Engine for component quantity calculation.

    Executes arithmetic operations and conditional logic based on extracted component data.
    """

    # Level 1 operations
    ARITHMETIC_OPERATIONS = ['MULTIPLY', 'ADD', 'SUBTRACT', 'FIXED']

    # Level 2 operations
    CONDITIONAL_OPERATIONS = ['IF_THEN_ELSE']
    COMPARISON_OPERATIONS = ['GREATER_THAN', 'LESS_THAN', 'EQUALS', 'GREATER_EQUAL', 'LESS_EQUAL']
    LOGICAL_OPERATIONS = ['AND', 'OR']

    SUPPORTED_OPERATIONS = ARITHMETIC_OPERATIONS + CONDITIONAL_OPERATIONS + COMPARISON_OPERATIONS + LOGICAL_OPERATIONS

    def __init__(self, extracted_components: Dict[str, Any]):
        """
        Initialize rule engine with extracted component data.

        Args:
            extracted_components: Dictionary of extracted components from OCR/NER.
                Format: {
                    'Tür': {'anzahl': 2, 'höhe': 2.0, 'breite': 1.0},
                    'Einlegeboden': {'anzahl': 4, 'breite': 2.0, 'tiefe': 0.8},
                    ...
                }
        """
        self.components = extracted_components
        logger.debug(f"RegelEngine initialized with components: {list(self.components.keys())}")

    def execute_rule(self, regel_definition: Dict[str, Any]) -> Decimal:
        """
        Execute a rule and return calculated quantity.

        Args:
            regel_definition: Rule definition dict (see class docstring for format)

        Returns:
            Calculated quantity as Decimal

        Raises:
            InvalidRuleError: If rule format is invalid
            ComponentNotFoundError: If referenced component doesn't exist

        Examples:
            >>> engine = BauteilRegelEngine({'Tür': {'anzahl': 2}})
            >>> result = engine.execute_rule({
            ...     'operation': 'MULTIPLY',
            ...     'faktor': 3,
            ...     'komponente': 'Tür',
            ...     'attribut': 'anzahl'
            ... })
            >>> print(result)
            6
        """
        operation = regel_definition.get('operation')

        if operation not in self.SUPPORTED_OPERATIONS:
            raise InvalidRuleError(
                f"Unsupported operation '{operation}'. "
                f"Supported: {', '.join(self.SUPPORTED_OPERATIONS)}"
            )

        logger.debug(f"Executing rule: {operation}")

        if operation == 'MULTIPLY':
            return self._execute_multiply(regel_definition)
        elif operation == 'ADD':
            return self._execute_add(regel_definition)
        elif operation == 'SUBTRACT':
            return self._execute_subtract(regel_definition)
        elif operation == 'FIXED':
            return self._execute_fixed(regel_definition)
        elif operation == 'IF_THEN_ELSE':
            return execute_if_then_else(regel_definition, self)
        elif operation in self.COMPARISON_OPERATIONS:
            result = execute_comparison(regel_definition, self)
            return Decimal('1' if result else '0')
        elif operation in self.LOGICAL_OPERATIONS:
            result = execute_logical(regel_definition, self)
            return Decimal('1' if result else '0')

    def _execute_multiply(self, regel: Dict[str, Any]) -> Decimal:
        """
        Execute MULTIPLY operation.

        Format: {"operation": "MULTIPLY", "faktor": N, "komponente": "X", "attribut": "Y"}
        Returns: faktor × komponente.attribut
        """
        faktor = regel.get('faktor')
        komponente_name = regel.get('komponente')
        attribut = regel.get('attribut')

        if faktor is None:
            raise InvalidRuleError("MULTIPLY requires 'faktor' field")
        if komponente_name is None:
            raise InvalidRuleError("MULTIPLY requires 'komponente' field")
        if attribut is None:
            raise InvalidRuleError("MULTIPLY requires 'attribut' field")

        # Get component data
        komponente_data = self.components.get(komponente_name)
        if komponente_data is None:
            raise ComponentNotFoundError(
                f"Component '{komponente_name}' not found in extracted data. "
                f"Available components: {list(self.components.keys())}"
            )

        # Get attribute value
        attribut_wert = komponente_data.get(attribut)
        if attribut_wert is None:
            raise ComponentNotFoundError(
                f"Attribute '{attribut}' not found in component '{komponente_name}'. "
                f"Available attributes: {list(komponente_data.keys())}"
            )

        result = Decimal(str(faktor)) * Decimal(str(attribut_wert))
        logger.debug(f"MULTIPLY: {faktor} × {attribut_wert} = {result}")
        return result

    def _execute_add(self, regel: Dict[str, Any]) -> Decimal:
        """
        Execute ADD operation.

        Format: {"operation": "ADD", "terme": [term1, term2, ...]}
        Returns: sum of all terms
        """
        terme = regel.get('terme', [])

        if not isinstance(terme, list):
            raise InvalidRuleError("ADD requires 'terme' to be a list")
        if len(terme) == 0:
            raise InvalidRuleError("ADD requires at least one term")

        result = Decimal('0')
        for i, term in enumerate(terme):
            term_result = self.execute_rule(term)
            result += term_result
            logger.debug(f"ADD term {i+1}: {term_result}, running sum: {result}")

        logger.debug(f"ADD total: {result}")
        return result

    def _execute_subtract(self, regel: Dict[str, Any]) -> Decimal:
        """
        Execute SUBTRACT operation.

        Format: {"operation": "SUBTRACT", "minuend": term1, "subtrahend": term2}
        Returns: minuend - subtrahend
        """
        minuend = regel.get('minuend')
        subtrahend = regel.get('subtrahend')

        if minuend is None:
            raise InvalidRuleError("SUBTRACT requires 'minuend' field")
        if subtrahend is None:
            raise InvalidRuleError("SUBTRACT requires 'subtrahend' field")

        minuend_result = self.execute_rule(minuend)
        subtrahend_result = self.execute_rule(subtrahend)

        result = minuend_result - subtrahend_result
        logger.debug(f"SUBTRACT: {minuend_result} - {subtrahend_result} = {result}")
        return result

    def _execute_fixed(self, regel: Dict[str, Any]) -> Decimal:
        """
        Execute FIXED operation.

        Format: {"operation": "FIXED", "wert": N}
        Returns: N
        """
        wert = regel.get('wert')

        if wert is None:
            raise InvalidRuleError("FIXED requires 'wert' field")

        result = Decimal(str(wert))
        logger.debug(f"FIXED: {result}")
        return result

    def validate_rule(self, regel_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate rule definition without executing.

        Args:
            regel_definition: Rule definition to validate

        Returns:
            Validation result dict with keys:
                - valid (bool): Whether rule is valid
                - errors (List[str]): List of validation errors (empty if valid)
                - referenced_components (List[str]): Components referenced in rule

        Examples:
            >>> engine = BauteilRegelEngine({})
            >>> result = engine.validate_rule({
            ...     'operation': 'MULTIPLY',
            ...     'faktor': 3,
            ...     'komponente': 'Tür',
            ...     'attribut': 'anzahl'
            ... })
            >>> print(result['valid'])
            True
        """
        errors = []
        referenced_components = []

        try:
            # Try to extract referenced components without executing
            self._extract_referenced_components(regel_definition, referenced_components)

            # Check if operation is supported
            operation = regel_definition.get('operation')
            if operation not in self.SUPPORTED_OPERATIONS:
                errors.append(
                    f"Unsupported operation '{operation}'. "
                    f"Supported: {', '.join(self.SUPPORTED_OPERATIONS)}"
                )

        except InvalidRuleError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'referenced_components': list(set(referenced_components))
        }

    def _extract_referenced_components(
        self,
        regel: Dict[str, Any],
        components_list: List[str]
    ) -> None:
        """
        Recursively extract all component references from a rule.

        Args:
            regel: Rule definition
            components_list: List to append component names to (modified in-place)
        """
        operation = regel.get('operation')

        if operation == 'MULTIPLY':
            komponente = regel.get('komponente')
            if komponente:
                components_list.append(komponente)

        elif operation in ['ADD']:
            for term in regel.get('terme', []):
                self._extract_referenced_components(term, components_list)

        elif operation == 'SUBTRACT':
            minuend = regel.get('minuend')
            subtrahend = regel.get('subtrahend')
            if minuend:
                self._extract_referenced_components(minuend, components_list)
            if subtrahend:
                self._extract_referenced_components(subtrahend, components_list)

        # FIXED doesn't reference components


def calculate_bauteil_menge(
    regel_definition: Dict[str, Any],
    extracted_components: Dict[str, Any]
) -> Decimal:
    """
    Convenience function to calculate component quantity.

    Args:
        regel_definition: Rule definition dict
        extracted_components: Extracted component data from OCR/NER

    Returns:
        Calculated quantity as Decimal

    Raises:
        RegelEngineError: If rule execution fails

    Examples:
        >>> components = {'Tür': {'anzahl': 2}, 'Schublade': {'anzahl': 3}}
        >>> regel = {
        ...     'operation': 'ADD',
        ...     'terme': [
        ...         {'operation': 'MULTIPLY', 'faktor': 3, 'komponente': 'Tür', 'attribut': 'anzahl'},
        ...         {'operation': 'MULTIPLY', 'faktor': 2, 'komponente': 'Schublade', 'attribut': 'anzahl'}
        ...     ]
        ... }
        >>> result = calculate_bauteil_menge(regel, components)
        >>> print(result)  # (3×2) + (2×3) = 12
        12
    """
    engine = BauteilRegelEngine(extracted_components)
    return engine.execute_rule(regel_definition)
