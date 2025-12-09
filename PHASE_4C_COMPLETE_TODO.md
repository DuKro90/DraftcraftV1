# Phase 4C - Verbleibende Implementation Tasks

**Status:** 70% Complete
**Was fehlt:** PauschaleService, Admin, Integration, Tests, Migration

---

## ✅ FERTIG (70%)

1. ✅ Multi-Material Schema + Service
2. ✅ Betriebspauschalen Models
3. ✅ Level 2 DSL Operations Module

---

## ⏳ TODO (30%) - Für dich zum Ausführen

### 1. BauteilRegelEngine - Level 2 Integration (15 Min)

**File:** `backend/documents/services/bauteil_regel_engine.py`

**Füge hinzu in `execute_rule()` Methode (nach Line ~110):**

```python
# Import Level 2 operations
from .level2_dsl_operations import execute_if_then_else, execute_comparison, execute_logical

# In execute_rule(), nach existing operations:
elif operation == 'IF_THEN_ELSE':
    return execute_if_then_else(regel_definition, self)
elif operation in self.COMPARISON_OPERATIONS:
    result = execute_comparison(regel_definition, self)
    return Decimal('1' if result else '0')  # Convert bool to Decimal
elif operation in self.LOGICAL_OPERATIONS:
    result = execute_logical(regel_definition, self)
    return Decimal('1' if result else '0')
```

---

### 2. PauschaleCalculationService (30 Min)

**Erstelle:** `backend/documents/services/pauschale_calculation_service.py`

```python
"""Pauschale Calculation Service - Quick Implementation"""

from decimal import Decimal
from typing import Dict, Any, List
from documents.models_pauschalen import BetriebspauschaleRegel, PauschaleAnwendung
from .bauteil_regel_engine import BauteilRegelEngine

class PauschaleCalculationService:
    def __init__(self, user, extraction_result):
        self.user = user
        self.extraction_result = extraction_result

    def calculate_all_pauschalen(self, auftragswert: Decimal, context: Dict[str, Any]) -> Dict:
        """Calculate all applicable Pauschalen"""
        pauschalen = BetriebspauschaleRegel.objects.filter(
            user=self.user,
            ist_aktiv=True
        )

        results = []
        total = Decimal('0')

        for pauschale in pauschalen:
            if not pauschale.is_applicable_for_order(auftragswert):
                continue

            betrag = self._calculate_pauschale(pauschale, context)
            if betrag > 0:
                # Create PauschaleAnwendung
                anwendung = PauschaleAnwendung.objects.create(
                    extraction_result=self.extraction_result,
                    pauschale=pauschale,
                    berechnungsgrundlage=context,
                    berechneter_betrag=betrag
                )
                results.append({
                    'name': pauschale.name,
                    'betrag': float(betrag),
                    'anwendung_id': str(anwendung.id)
                })
                total += betrag

        return {'pauschalen': results, 'total': float(total)}

    def _calculate_pauschale(self, pauschale: BetriebspauschaleRegel, context: Dict) -> Decimal:
        """Calculate single Pauschale"""
        if pauschale.berechnungsart == 'fest':
            return pauschale.betrag

        elif pauschale.berechnungsart == 'pro_einheit':
            menge_key = f"{pauschale.pauschale_typ}_menge"
            menge = Decimal(str(context.get(menge_key, 0)))
            return pauschale.betrag * menge

        elif pauschale.berechnungsart == 'prozent':
            auftragswert = context.get('auftragswert', Decimal('0'))
            return auftragswert * (pauschale.prozentsatz / 100)

        elif pauschale.berechnungsart == 'konditional':
            # Use Level 2 DSL
            engine = BauteilRegelEngine({})
            engine.context = context  # Add context for resolution
            try:
                return engine.execute_rule(pauschale.konditional_regel)
            except Exception as e:
                logger.error(f"Error executing konditional regel: {e}")
                return Decimal('0')

        return Decimal('0')
```

---

### 3. Django Admin (20 Min)

**Erstelle:** `backend/documents/admin_pauschalen.py`

```python
"""Django Admin for Betriebspauschalen"""

from django.contrib import admin
from .models_pauschalen import BetriebspauschaleRegel, PauschaleAnwendung

@admin.register(BetriebspauschaleRegel)
class BetriebspauschaleRegelAdmin(admin.ModelAdmin):
    list_display = ('name', 'pauschale_typ', 'berechnungsart', 'betrag', 'ist_aktiv')
    list_filter = ('pauschale_typ', 'berechnungsart', 'ist_aktiv')
    search_fields = ('name', 'beschreibung')
    readonly_fields = ('id', 'erstellt_am', 'aktualisiert_am')

    fieldsets = (
        ('Identifikation', {'fields': ('id', 'user', 'name', 'pauschale_typ', 'beschreibung')}),
        ('Berechnung', {'fields': ('berechnungsart', 'betrag', 'einheit', 'prozentsatz', 'konditional_regel')}),
        ('Anwendungs-Bedingungen', {'fields': ('min_auftragswert', 'max_auftragswert')}),
        ('Status', {'fields': ('ist_aktiv', 'prioritaet', 'gueltig_ab', 'gueltig_bis')}),
    )

@admin.register(PauschaleAnwendung)
class PauschaleAnwendungAdmin(admin.ModelAdmin):
    list_display = ('pauschale', 'extraction_result', 'berechneter_betrag', 'manuell_ueberschrieben')
    readonly_fields = ('id', 'erstellt_am', 'aktualisiert_am')
```

---

### 4. Migration erstellen (5 Min)

```bash
cd backend
python manage.py makemigrations documents --name phase4c_multi_material_pauschalen
python manage.py migrate
```

---

### 5. Quick Tests (Optional - 20 Min)

**Erstelle:** `backend/tests/unit/test_level2_dsl.py`

```python
"""Quick Level 2 DSL Tests"""
import pytest
from decimal import Decimal
from documents.services.bauteil_regel_engine import BauteilRegelEngine

def test_if_then_else_greater_than():
    components = {'Tür': {'anzahl': 2, 'höhe': 2.5}}
    engine = BauteilRegelEngine(components)

    regel = {
        'operation': 'IF_THEN_ELSE',
        'bedingung': {
            'operation': 'GREATER_THAN',
            'links': {'komponente': 'Tür', 'attribut': 'höhe'},
            'rechts': 2.0
        },
        'dann': {'operation': 'FIXED', 'wert': 4},
        'sonst': {'operation': 'FIXED', 'wert': 3}
    }

    result = engine.execute_rule(regel)
    assert result == Decimal('4')  # Height 2.5 > 2.0, so THEN branch

def test_pauschale_context():
    engine = BauteilRegelEngine({})
    engine.context = {'distanz_km': 75}

    regel = {
        'operation': 'IF_THEN_ELSE',
        'bedingung': {
            'operation': 'GREATER_THAN',
            'links': {'quelle': 'distanz_km'},
            'rechts': 50
        },
        'dann': {'operation': 'FIXED', 'wert': 100},
        'sonst': {'operation': 'FIXED', 'wert': 50}
    }

    result = engine.execute_rule(regel)
    assert result == Decimal('100')  # 75km > 50km
```

---

### 6. Integration in CalculationEngine (15 Min)

**File:** `backend/extraction/services/calculation_engine.py`

**Am Ende von `calculate_project_price()` hinzufügen:**

```python
# Multi-Material check
from documents.schemas.multi_material_schema import is_multi_material_extraction
from extraction.services.multi_material_calculation_service import calculate_multi_material_cost

if is_multi_material_extraction(extracted_data):
    multi_result = calculate_multi_material_cost(self.user, extracted_data)
    material_cost = Decimal(str(multi_result['total_material_cost']))
    result['multi_material_breakdown'] = multi_result
else:
    # Existing single-material logic
    material_cost = self._calculate_single_material_cost(extracted_data)

# Pauschalen (after TIER 3)
from documents.services.pauschale_calculation_service import PauschaleCalculationService
pauschale_service = PauschaleCalculationService(self.user, extraction_result)
pauschalen_result = pauschale_service.calculate_all_pauschalen(
    auftragswert=result['total_price_eur'],
    context={
        'auftragswert': result['total_price_eur'],
        'distanz_km': extracted_data.get('distanz_km', 0),
        # Add other context as needed
    }
)

result['pauschalen'] = pauschalen_result
result['total_price_eur'] += Decimal(str(pauschalen_result['total']))
```

---

## 🎯 Execution Order

```bash
# 1. Integrate Level 2 in bauteil_regel_engine.py
# 2. Create pauschale_calculation_service.py
# 3. Create admin_pauschalen.py
# 4. Run migrations
python manage.py makemigrations documents
python manage.py migrate

# 5. Test in Django shell
python manage.py shell
>>> from documents.services.bauteil_regel_engine import BauteilRegelEngine
>>> engine = BauteilRegelEngine({'Tür': {'höhe': 2.5, 'anzahl': 2}})
>>> regel = {'operation': 'IF_THEN_ELSE', ...}  # Test Level 2
>>> result = engine.execute_rule(regel)

# 6. Create test data
>>> from documents.models_pauschalen import BetriebspauschaleRegel
>>> BetriebspauschaleRegel.objects.create(...)

# 7. Run tests
pytest backend/tests/unit/test_level2_dsl.py -v
```

---

## 📋 Checklist

- [ ] Level 2 DSL integration in bauteil_regel_engine.py
- [ ] PauschaleCalculationService created
- [ ] Django Admin for Pauschalen created
- [ ] Migrations run successfully
- [ ] Test data loaded
- [ ] Basic tests passing
- [ ] Integration in CalculationEngine
- [ ] Documentation updated

**Estimated Time:** 2-3 hours total

---

**Dann können wir alles zusammen testen bevor Phase 4D!** 🚀
