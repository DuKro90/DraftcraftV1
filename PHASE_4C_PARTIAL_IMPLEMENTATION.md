# Phase 4C - Kritische Erweiterungen (PARTIAL IMPLEMENTATION)

**Status:** ⚠️ **50% COMPLETE** - Multi-Material & Pauschalen Models fertig, Level 2 DSL & Integration ausstehend
**Datum:** 2025-12-07

---

## ✅ Was WURDE implementiert

### 1. **Multi-Material-System** (100% Complete)

**Files erstellt:**
- `backend/documents/schemas/multi_material_schema.py` (450 Zeilen)
- `backend/extraction/services/multi_material_calculation_service.py` (400 Zeilen)

**Features:**
✅ `MultiMaterialExtraction` - Container für Multi-Material-Produkte
✅ `MaterialSpecification` - Material pro Komponente
✅ `ComponentSpecification` - Komponente mit Material + Maße
✅ `MultiMaterialCalculationService` - Berechnung mit TIER 1 Faktoren pro Komponente
✅ Validierung & Helper-Funktionen
✅ Legacy-Converter (single → multi-material)

**Beispiel:**
```python
extraction = create_multi_material_extraction(
    product_name='Esstisch',
    product_typ='Tisch',
    components=[
        {
            'component_typ': 'Tischplatte',
            'material_typ': 'Holz',
            'holzart': 'Nussbaum',  # Teuer: Faktor 1.5
            'oberfläche': 'geölt',
            'maße': {'länge': 2.0, 'breite': 1.0, 'höhe': 0.04}
        },
        {
            'component_typ': 'Gestell',
            'material_typ': 'Holz',
            'holzart': 'Eiche',  # Günstiger: Faktor 1.3
            'maße': {'länge': 2.0, 'breite': 1.0, 'höhe': 0.75}
        }
    ]
)

# Berechnung
service = MultiMaterialCalculationService(user)
result = service.calculate_multi_material_cost(extraction.to_dict())

# Ergebnis: Unterschiedliche Faktoren pro Komponente!
# Tischplatte: Base × 1.5 (Nussbaum) × 1.10 (geölt)
# Gestell: Base × 1.3 (Eiche)
```

---

### 2. **Betriebspauschalen-Models** (100% Complete)

**Files erstellt:**
- `backend/documents/models_pauschalen.py` (400 Zeilen)

**Models:**
✅ `BetriebspauschaleRegel` - Regel für fixe Kosten
✅ `PauschaleAnwendung` - Anwendungs-Log mit User-Editierbarkeit

**Pauschalen-Typen:**
- `anfahrt` - Anfahrtskosten
- `entsorgung` - Entsorgungskosten
- `montage` - Montage/Installation
- `kleinauftrag` - Kleinauftragszuschlag
- `verpackung` - Verpackung/Versand
- `planung` - Planungs-/Beratungskosten
- `miete` - Geräte-/Werkzeugmiete
- `genehmigung` - Genehmigungsgebühren

**Berechnungsarten:**
- `fest` - Fester Betrag (z.B. 50€ Anfahrt)
- `pro_einheit` - Pro Einheit (z.B. 80€/m³ Entsorgung)
- `prozent` - Prozentsatz (z.B. 5% Verpackung)
- `konditional` - IF-THEN-ELSE (z.B. Distanz-abhängig)

**Beispiel:**
```python
# Anfahrt: 50€ (< 50km), 100€ (> 50km)
pauschale = BetriebspauschaleRegel.objects.create(
    user=user,
    name='Anfahrt Standard',
    pauschale_typ='anfahrt',
    berechnungsart='konditional',
    konditional_regel={
        'operation': 'IF_THEN_ELSE',
        'bedingung': {
            'operation': 'GREATER_THAN',
            'links': {'quelle': 'distanz_km'},
            'rechts': 50
        },
        'dann': {'betrag': 100.00},
        'sonst': {'betrag': 50.00}
    }
)

# Entsorgung: 80€ pro m³
pauschale = BetriebspauschaleRegel.objects.create(
    user=user,
    name='Entsorgung Altmöbel',
    pauschale_typ='entsorgung',
    berechnungsart='pro_einheit',
    betrag=Decimal('80.00'),
    einheit='m3'
)
```

---

## ⏳ Was FEHLT noch (für komplette Phase 4C)

### 3. **Level 2 Regel-Engine** (0% Complete)

**Was benötigt wird:**
- Erweiterung von `BauteilRegelEngine` um IF-THEN-ELSE
- Neue Operationen: `GREATER_THAN`, `LESS_THAN`, `EQUALS`, `AND`, `OR`
- `PauschaleCalculationService` für konditionale Pauschalen

**Geschätzter Aufwand:** 3-4 Stunden

### 4. **Django Admin für Pauschalen** (0% Complete)

**Was benötigt wird:**
- `BetriebspauschaleRegelAdmin` mit JSON-Editor
- `PauschaleAnwendungAdmin` mit Override-Funktion
- Inline-Editing für Anwendungen

**Geschätzter Aufwand:** 2 Stunden

### 5. **Integration in CalculationEngine** (0% Complete)

**Was benötigt wird:**
- Multi-Material-Check in `calculate_project_price()`
- Pauschalen-Anwendung nach TIER 3
- Export-Format Update

**Geschätzter Aufwand:** 2 Stunden

### 6. **Unit Tests** (0% Complete)

**Was benötigt wird:**
- `test_multi_material_calculation.py` (15 Tests)
- `test_pauschale_calculation.py` (12 Tests)
- `test_level2_regel_engine.py` (18 Tests)

**Geschätzter Aufwand:** 3 Stunden

### 7. **Dokumentation** (0% Complete)

**Was benötigt wird:**
- Vollständige Phase 4C Summary
- CHANGELOG Update
- Code-Beispiele

**Geschätzter Aufwand:** 1 Stunde

---

## 📊 Fortschritt

**Implementiert:** 2 / 7 Komponenten (29%)

| Komponente | Status | Aufwand geschätzt |
|------------|--------|-------------------|
| Multi-Material Schema | ✅ Done | - |
| Multi-Material Calculation | ✅ Done | - |
| Pauschalen Models | ✅ Done | - |
| Level 2 Regel-Engine | ⏳ Pending | 3-4h |
| Pauschalen Admin | ⏳ Pending | 2h |
| Integration | ⏳ Pending | 2h |
| Tests | ⏳ Pending | 3h |
| Dokumentation | ⏳ Pending | 1h |

**Gesamt verbleibend:** ~11-12 Stunden

---

## 🚀 Nächste Schritte (Empfehlung)

**Option A: Phase 4C komplett fertigstellen** (~11h)
1. Level 2 DSL implementieren (3-4h)
2. Pauschalen-Service + Admin (4h)
3. Integration + Tests (5h)
4. Dokumentation (1h)

**Option B: Migration & Testing des Bestehenden**
1. Migration für Multi-Material + Pauschalen Models ausführen
2. Test-Daten laden
3. Multi-Material-Berechnung testen
4. Feedback sammeln, dann Rest implementieren

**Option C: Priorisierung neu bewerten**
- Ist Level 2 DSL jetzt wichtiger als Phase 4D (Missing-Data-Handling)?
- Welche Features sind für deinen aktuellen Workflow **kritisch**?

---

## 📁 Erstellte Dateien

```
backend/
├── documents/
│   ├── models_pauschalen.py                  # ✅ 400 Zeilen
│   ├── schemas/
│   │   └── multi_material_schema.py          # ✅ 450 Zeilen
│   └── models.py                             # ✅ Updated (Import)
└── extraction/
    └── services/
        └── multi_material_calculation_service.py  # ✅ 400 Zeilen

Dokumentation:
└── PHASE_4C_PARTIAL_IMPLEMENTATION.md        # ✅ Dieses Dokument
```

---

## ❓ Entscheidung erforderlich

**Frage an dich:** Wie soll ich weitermachen?

**A)** Phase 4C komplett fertigstellen (Level 2 DSL + Integration + Tests) → ~11h
**B)** Erst Migration + Testing, dann weiter
**C)** Andere Priorität (z.B. Phase 4D Missing-Data-Handling wichtiger?)

**Gib mir Feedback und ich fahre fort!** 🚀
