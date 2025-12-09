"""
Level 2 DSL Operations - Phase 4C

Conditional logic and comparison operations for rule engine.
This module extends BauteilRegelEngine with Level 2 capabilities.
"""

from typing import Dict, Any, Union
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def execute_if_then_else(regel: Dict[str, Any], engine: 'BauteilRegelEngine') -> Decimal:
    """
    Execute IF-THEN-ELSE conditional logic.

    Format:
    {
        "operation": "IF_THEN_ELSE",
        "bedingung": {...},  # Comparison operation
        "dann": {...},       # Rule to execute if true
        "sonst": {...}       # Rule to execute if false
    }
    """
    bedingung = regel.get('bedingung')
    dann = regel.get('dann')
    sonst = regel.get('sonst')

    if not all([bedingung, dann, sonst]):
        from documents.services.bauteil_regel_engine import InvalidRuleError
        raise InvalidRuleError("IF_THEN_ELSE requires 'bedingung', 'dann', 'sonst'")

    # Evaluate condition - check if it's a logical or comparison operation
    condition_operation = bedingung.get('operation')
    if condition_operation in ['AND', 'OR']:
        condition_result = execute_logical(bedingung, engine)
    else:
        condition_result = execute_comparison(bedingung, engine)

    # Execute appropriate branch
    if condition_result:
        result = engine.execute_rule(dann)
        logger.debug(f"IF condition TRUE, executing THEN branch: {result}")
    else:
        result = engine.execute_rule(sonst)
        logger.debug(f"IF condition FALSE, executing ELSE branch: {result}")

    return result


def execute_comparison(regel: Dict[str, Any], engine: 'BauteilRegelEngine') -> bool:
    """
    Execute comparison operation.

    Supported: GREATER_THAN, LESS_THAN, EQUALS, GREATER_EQUAL, LESS_EQUAL
    """
    operation = regel.get('operation')
    links = regel.get('links')
    rechts = regel.get('rechts')

    if not all([operation, links is not None, rechts is not None]):
        from documents.services.bauteil_regel_engine import InvalidRuleError
        raise InvalidRuleError(f"Comparison requires 'links' and 'rechts'")

    # Resolve left side (can be component attribute or literal)
    left_value = resolve_value(links, engine)

    # Resolve right side (can be component attribute or literal)
    right_value = resolve_value(rechts, engine)

    # Perform comparison
    if operation == 'GREATER_THAN':
        result = left_value > right_value
    elif operation == 'LESS_THAN':
        result = left_value < right_value
    elif operation == 'EQUALS':
        result = left_value == right_value
    elif operation == 'GREATER_EQUAL':
        result = left_value >= right_value
    elif operation == 'LESS_EQUAL':
        result = left_value <= right_value
    else:
        from documents.services.bauteil_regel_engine import InvalidRuleError
        raise InvalidRuleError(f"Unknown comparison operation: {operation}")

    logger.debug(f"Comparison: {left_value} {operation} {right_value} = {result}")
    return result


def execute_logical(regel: Dict[str, Any], engine: 'BauteilRegelEngine') -> bool:
    """
    Execute logical operation (AND, OR).

    Format:
    {"operation": "AND", "bedingungen": [cond1, cond2, ...]}
    """
    operation = regel.get('operation')
    bedingungen = regel.get('bedingungen', [])

    if not bedingungen:
        from documents.services.bauteil_regel_engine import InvalidRuleError
        raise InvalidRuleError(f"{operation} requires 'bedingungen' list")

    results = [execute_comparison(cond, engine) for cond in bedingungen]

    if operation == 'AND':
        result = all(results)
    elif operation == 'OR':
        result = any(results)
    else:
        from documents.services.bauteil_regel_engine import InvalidRuleError
        raise InvalidRuleError(f"Unknown logical operation: {operation}")

    logger.debug(f"{operation} of {len(bedingungen)} conditions: {result}")
    return result


def resolve_value(value_spec: Union[Dict, int, float, str], engine: 'BauteilRegelEngine') -> Decimal:
    """
    Resolve a value specification to a Decimal.

    Can be:
    - Literal number: 5, 2.5
    - Component reference: {"komponente": "Tür", "attribut": "höhe"}
    - Source reference: {"quelle": "distanz_km"}  # From context
    """
    # Literal number
    if isinstance(value_spec, (int, float)):
        return Decimal(str(value_spec))

    # Dict reference
    if isinstance(value_spec, dict):
        # Component attribute reference
        if 'komponente' in value_spec and 'attribut' in value_spec:
            komponente_name = value_spec['komponente']
            attribut = value_spec['attribut']

            komponente_data = engine.components.get(komponente_name)
            if komponente_data is None:
                from documents.services.bauteil_regel_engine import ComponentNotFoundError
                raise ComponentNotFoundError(
                    f"Component '{komponente_name}' not found in extracted data"
                )

            attribut_wert = komponente_data.get(attribut)
            if attribut_wert is None:
                from documents.services.bauteil_regel_engine import ComponentNotFoundError
                raise ComponentNotFoundError(
                    f"Attribute '{attribut}' not found in component '{komponente_name}'"
                )

            return Decimal(str(attribut_wert))

        # Context source reference (for Pauschalen)
        if 'quelle' in value_spec:
            quelle_key = value_spec['quelle']
            # Check if engine has context
            context = getattr(engine, 'context', {})
            if quelle_key in context:
                return Decimal(str(context[quelle_key]))
            else:
                logger.warning(f"Context source '{quelle_key}' not found, using 0")
                return Decimal('0')

    # String literal
    if isinstance(value_spec, str):
        try:
            return Decimal(value_spec)
        except:
            logger.warning(f"Cannot convert string '{value_spec}' to Decimal, using 0")
            return Decimal('0')

    logger.warning(f"Unknown value spec type: {type(value_spec)}, using 0")
    return Decimal('0')
