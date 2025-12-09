# Standardbauteile System - Phase 4B Implementation Summary

**Implementiert:** 2025-12-07
**Status:** ✅ COMPLETE - Ready for Migration & Integration Testing
**Version:** 1.0.0

---

## 📋 Übersicht

Das **Standardbauteile-System** ermöglicht die automatische Berechnung von Mengen und Kosten für standardisierte Bauteile (z.B. Topfbänder, ABS-Kanten, Griffe) basierend auf extrahierten Komponenten-Daten.

### Kern-Features

✅ **Multi-Gewerk-Katalog-System**
- Bauteile können mehreren Gewerken zugeordnet werden (Tischler, Zimmerer, Polsterer)
- Versionierte Kataloge mit Audit-Trail
- Firmenspezifische und globale Kataloge

✅ **Level 1 Regel-Engine (DSL)**
- Einfache arithmetische Operationen: MULTIPLY, ADD, SUBTRACT, FIXED
- Sichere JSON-basierte Regel-Definition
- Erweiterbar für zukünftige Level 2/3 (IF-THEN-ELSE, Matrix-Lookup)

✅ **Automatische Geometrie-Berechnungen**
- ABS-Kanten-Längen basierend auf Komponenten-Maßen
- User-editierbare Checkboxes für selektive Aktivierung
- Standard-Sichtbarkeitsregeln (z.B. Außenkanten = sichtbar, Innenkanten = optional)

✅ **Django Admin Integration**
- Bulk-Edit Capabilities (CSV/Excel-kompatibel)
- Versionskontrolle für Kataloge
- Visuelle Badges und Inline-Editing

✅ **Phase 3 CalculationEngine Integration**
- Bauteile-Kosten fließen in TIER 1 Materialkalkulation ein
- Export-Format kompatibel mit bestehender Calculation Pipeline

---

## 🏗️ Architektur

### Django Models (`backend/documents/models_bauteile.py`)

#### 1. **StandardBauteil**
```python
StandardBauteil(
    artikel_nr='HF-12345',
    name='Topfband 35mm Standard',
    kategorie='beschlag',
    gewerke=['tischler', 'allgemein'],
    einheit='stk',
    einzelpreis=2.50,
    lieferant='Häfele',
    ist_aktiv=True
)
```

**Felder:**
- `artikel_nr`: Eindeutige Artikel-Nummer (z.B. HF-12345)
- `name`: Bauteil-Bezeichnung
- `kategorie`: beschlag | verbinder | kante | befestigung | oberflaeche | sonstiges
- `gewerke`: ArrayField mit Mehrfachzuordnung
- `einzelpreis`: Preis pro Einheit (netto)
- `lieferant`: Hauptlieferant
- `ist_aktiv`: Aktiv in Kalkulationen?
- `verfuegbar_ab/bis`: Optional für Saison-Artikel

#### 2. **BauteilRegel**
```python
BauteilRegel(
    bauteil=topfband,
    name='Topfbänder pro Tür',
    regel_definition={
        'operation': 'MULTIPLY',
        'faktor': 3,
        'komponente': 'Tür',
        'attribut': 'anzahl'
    },
    prioritaet=100,
    ist_aktiv=True
)
```

**Level 1 DSL Operationen:**
- `MULTIPLY`: `faktor × komponente.attribut`
- `ADD`: Summe mehrerer Terme
- `SUBTRACT`: Differenz zweier Terme
- `FIXED`: Konstanter Wert

#### 3. **BauteilKatalog** (Versionskontrolle)
```python
BauteilKatalog(
    name='Beschlagskatalog Q1 2025',
    version='2025.1',
    firma=company_profile,  # Optional (None = global)
    gewerk='tischler',
    gueltig_ab=date(2025, 1, 1),
    gueltig_bis=date(2025, 3, 31),
    ist_standard=True,
    vorgaenger_version=previous_catalog  # Für Rollback
)
```

#### 4. **BauteilKatalogPosition** (Through-Model)
```python
BauteilKatalogPosition(
    katalog=catalog,
    bauteil=topfband,
    katalog_einzelpreis=2.30,  # Überschreibt Standard-Preis
    position=10,
    ist_aktiv_in_katalog=True
)
```

#### 5. **GeometrieBerechnung** (ABS-Kanten)
```python
GeometrieBerechnung(
    extraction_result=extraction,
    bauteil=abs_kante,
    kanten_typ='tür_außen',
    formel='2 × (2.0m + 1.0m) × 2 Türen',
    berechnete_laenge=12.0,
    ist_aktiviert=True,  # ☑ Checkbox
    manuell_ueberschrieben=False,
    manuelle_laenge=None
)
```

**Kanten-Typen:**
- `korpus_außen` (immer sichtbar)
- `korpus_innen` (meist versteckt)
- `tür_außen` (immer sichtbar)
- `einlegeboden_vorder` (Front-Kante, sichtbar)
- `einlegeboden_seite` (Seiten, optional)
- `schublade_außen` (sichtbar)
- `rueckseite` (meist nicht bekanntet)

---

## 🔧 Services

### 1. **BauteilRegelEngine** (`bauteil_regel_engine.py`)

**Zweck:** Führt DSL-Regeln aus und berechnet Mengen.

**Beispiel:**
```python
from documents.services.bauteil_regel_engine import BauteilRegelEngine

components = {
    'Tür': {'anzahl': 2, 'höhe': 2.0, 'breite': 1.0},
    'Schublade': {'anzahl': 3}
}

regel = {
    'operation': 'ADD',
    'terme': [
        {'operation': 'MULTIPLY', 'faktor': 3, 'komponente': 'Tür', 'attribut': 'anzahl'},
        {'operation': 'MULTIPLY', 'faktor': 2, 'komponente': 'Schublade', 'attribut': 'anzahl'}
    ]
}

engine = BauteilRegelEngine(components)
menge = engine.execute_rule(regel)
# Result: (3 × 2) + (2 × 3) = 12
```

**Methoden:**
- `execute_rule(regel_definition)`: Führt Regel aus, gibt Decimal zurück
- `validate_rule(regel_definition)`: Validiert Regel ohne Ausführung
- `_extract_referenced_components()`: Extrahiert verwendete Komponenten

---

### 2. **GeometrieService** (`geometrie_service.py`)

**Zweck:** Berechnet geometriebasierte Mengen (ABS-Kanten-Längen).

**Beispiel:**
```python
from documents.services.geometrie_service import GeometrieService

service = GeometrieService(extraction_result_id='abc-123')

komponenten = [
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

# Erstelle editierbares Preview für Frontend
preview = service.create_editable_preview(berechnungen)

# Output:
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
        {
            'typ': 'einlegeboden_vorder',
            'beschreibung': 'Einlegeboden Vorderkante',
            'formel': '2.0m × 4 Einlegeböden',
            'länge': '8.0',
            'einheit': 'lfm',
            'ist_aktiviert': True,
            'ist_sichtbar': True
        },
        {
            'typ': 'einlegeboden_seite',
            'beschreibung': 'Einlegeboden Seitenkanten',
            'formel': '2 × 0.8m × 4 Einlegeböden',
            'länge': '6.4',
            'einheit': 'lfm',
            'ist_aktiviert': False,  # Optional
            'ist_sichtbar': False
        }
    ],
    'gesamt_aktiviert': '20.0',
    'gesamt_alle': '26.4'
}
```

**Methoden:**
- `calculate_abs_kanten(komponenten, apply_visibility_defaults)`: Haupt-Methode
- `calculate_total_kanten_länge(berechnungen, nur_aktivierte)`: Gesamt-Länge
- `create_editable_preview(berechnungen)`: Frontend-Export

---

### 3. **StandardbauteilIntegrationService** (`standardbauteil_integration.py`)

**Zweck:** Integration in Phase 3 CalculationEngine.

**Beispiel:**
```python
from documents.services.standardbauteil_integration import StandardbauteilIntegrationService

service = StandardbauteilIntegrationService(
    extraction_result_id='abc-123',
    company_profile_id='company-456'  # Optional
)

extracted_components = {
    'Tür': {'anzahl': 2, 'höhe': 2.0, 'breite': 1.0},
    'Einlegeboden': {'anzahl': 4, 'breite': 2.0, 'tiefe': 0.8}
}

# Berechne Bauteile-Kosten
summary = service.calculate_bauteil_kosten(extracted_components, gewerk='tischler')

# Export für CalculationEngine
export = service.export_bauteil_kosten_for_calculation_engine(summary)

# Output:
{
    'material_typ': 'Standardbauteile',
    'positionen': [
        {
            'artikel_nr': 'HF-12345',
            'name': 'Topfband 35mm',
            'menge': 6.0,  # 3 pro Tür × 2 Türen
            'einheit': 'Stück',
            'einzelpreis': 2.50,
            'gesamtpreis': 15.00,
            'kategorie': 'Beschläge',
            'berechnungsgrundlage': 'Regel: Topfbänder pro Tür'
        },
        {
            'artikel_nr': 'ABS-001',
            'name': 'ABS-Kante 0.4mm Eiche',
            'menge': 20.0,  # lfm
            'einheit': 'lfm',
            'einzelpreis': 1.20,
            'gesamtpreis': 24.00,
            'kategorie': 'Kantenbearbeitung',
            'berechnungsgrundlage': 'Geometrie-basiert (automatisch berechnet)'
        }
    ],
    'kategorie_summen': {
        'beschlaege': 15.00,
        'verbinder': 0.00,
        'kanten': 24.00,
        'befestigung': 0.00,
        'sonstiges': 0.00
    },
    'gesamt_netto': 39.00
}
```

**Katalog-Auswahl-Priorität:**
1. Explizit angegebener `katalog_id`
2. Firmenspezifischer Standard-Katalog (wenn `company_profile_id` angegeben)
3. Globaler Standard-Katalog für Gewerk

---

## 🎨 Django Admin Features

### StandardBauteil Admin

**Features:**
- ✅ Bulk-Aktionen: Aktivieren, Deaktivieren, CSV-Export
- ✅ Farbige Kategorie-Badges
- ✅ Gewerke-Anzeige (Mehrfachzuordnung)
- ✅ Verwendungs-Count (in wie vielen Katalogen?)
- ✅ Inline-Editing für Regeln

**Bulk-Export Format (CSV mit UTF-8 BOM, Excel-kompatibel):**
```csv
Artikel-Nr;Name;Beschreibung;Kategorie;Gewerke;Einheit;Einzelpreis (EUR);Lieferant;Aktiv
HF-12345;Topfband 35mm Standard;...;Beschläge;Tischler;Stück;2,50;Häfele;Ja
```

### BauteilKatalog Admin

**Features:**
- ✅ Versions-Historie mit Vorgänger-Links
- ✅ Rollback-Funktion (über `vorgaenger_version`)
- ✅ "Als Standard setzen" Aktion
- ✅ Katalog-Export als CSV
- ✅ Inline-Editing für Katalog-Positionen

**Version Control Beispiel:**
```
Katalog v2025.1 (aktuell)
  ← Vorgänger: v2024.4 (01.10.2024)
    ← Vorgänger: v2024.3 (01.07.2024)
```

### GeometrieBerechnung Admin

**Features:**
- ✅ Visuelle Checkbox-Status (☑/☐)
- ✅ Farbige Kanten-Typ Badges
- ✅ Manuell überschriebene Werte hervorgehoben (rot)
- ✅ JSON-Preview für Komponenten-Daten

---

## ✅ Tests

### Test Coverage

**Unit Tests:**
- `test_bauteil_regel_engine.py` (21 Tests)
  - MULTIPLY, ADD, SUBTRACT, FIXED Operationen
  - Fehlerbehandlung (ComponentNotFound, InvalidRule)
  - Validation
  - Edge Cases (empty components, deeply nested)

- `test_geometrie_service.py` (18 Tests)
  - Tür, Korpus, Einlegeboden, Schublade Berechnungen
  - Visibility Defaults
  - Total Length Calculations
  - Editable Preview
  - Realistic Scenarios

**Test Ausführung:**
```bash
# Nur Standardbauteile-Tests
pytest backend/tests/unit/test_bauteil_regel_engine.py -v
pytest backend/tests/unit/test_geometrie_service.py -v

# Mit Coverage
pytest backend/tests/unit/test_bauteil_*.py backend/tests/unit/test_geometrie_*.py --cov=documents.services
```

**Erwartete Coverage:** >80% für alle Services

---

## 🚀 Nächste Schritte

### 1. Migration erstellen & ausführen

```bash
# Migration erstellen
python manage.py makemigrations documents

# Migration anwenden
python manage.py migrate

# Verifizierung
python manage.py check
```

### 2. Admin-Registrierung verifizieren

```python
# In backend/documents/admin.py sollte automatisch importiert werden:
from .admin_bauteile import (
    StandardBauteilAdmin,
    BauteilRegelAdmin,
    BauteilKatalogAdmin,
    GeometrieBerechnung Admin
)
```

Falls nicht, manuell importieren.

### 3. Test-Daten erstellen

```python
# Django Shell
python manage.py shell

from documents.models_bauteile import *
from decimal import Decimal

# Standard-Bauteil erstellen
topfband = StandardBauteil.objects.create(
    artikel_nr='HF-12345',
    name='Topfband 35mm Standard',
    kategorie='beschlag',
    gewerke=['tischler'],
    einheit='stk',
    einzelpreis=Decimal('2.50'),
    lieferant='Häfele',
    ist_aktiv=True
)

# Regel erstellen
BauteilRegel.objects.create(
    bauteil=topfband,
    name='Topfbänder pro Tür',
    regel_definition={
        'operation': 'MULTIPLY',
        'faktor': 3,
        'komponente': 'Tür',
        'attribut': 'anzahl'
    },
    ist_aktiv=True
)

# Katalog erstellen
from datetime import date

katalog = BauteilKatalog.objects.create(
    name='Test-Katalog Tischler',
    version='1.0',
    gewerk='tischler',
    gueltig_ab=date.today(),
    ist_aktiv=True,
    ist_standard=True
)

# Bauteil zu Katalog hinzufügen
katalog.bauteile.add(topfband)
```

### 4. Integration in CalculationEngine

**Wo einfügen:** `backend/extraction/services/calculation_engine.py`

```python
# In CalculationEngine.calculate_material_costs():

from documents.services.standardbauteil_integration import calculate_standardbauteile

def calculate_material_costs(self, extracted_data):
    """Calculate TIER 1 material costs."""

    # ... existing material calculations ...

    # NEU: Standardbauteile berechnen
    standardbauteile_kosten = calculate_standardbauteile(
        extraction_result_id=self.extraction_result_id,
        extracted_components=extracted_data.get('komponenten', {}),
        gewerk=self.gewerk,
        company_profile_id=self.company_profile_id
    )

    # Zu Gesamt-Materialkosten addieren
    total_material_cost += Decimal(standardbauteile_kosten['gesamt_netto'])

    # In Calculation Details speichern
    self.calculation_details['standardbauteile'] = standardbauteile_kosten

    return total_material_cost
```

### 5. Frontend-Integration (Optional für Phase 4B)

**Für Admin Dashboard:**
- Anzeige von `GeometrieBerechnung` Checkboxes
- Live-Preview von ABS-Kanten-Berechnungen
- Bearbeitung vor finaler Kalkulation

**API Endpoint (zukünftig):**
```python
# GET /api/v1/extractions/{id}/standardbauteile/
# POST /api/v1/extractions/{id}/standardbauteile/calculate/
# PATCH /api/v1/extractions/{id}/geometrie/{geom_id}/  # Toggle checkbox
```

---

## 📚 Dateistruktur

```
backend/
├── documents/
│   ├── models_bauteile.py                    # ✅ Neue Models
│   ├── admin_bauteile.py                     # ✅ Admin-Klassen
│   ├── services/
│   │   ├── bauteil_regel_engine.py           # ✅ Regel-Engine
│   │   ├── geometrie_service.py              # ✅ Geometrie-Berechnungen
│   │   └── standardbauteil_integration.py    # ✅ Integration Service
│   └── migrations/
│       └── 000X_standardbauteile_models.py   # ⏳ Zu erstellen
└── tests/
    └── unit/
        ├── test_bauteil_regel_engine.py      # ✅ 21 Tests
        └── test_geometrie_service.py         # ✅ 18 Tests
```

---

## 🎯 Erfolgs-Kriterien

### ✅ Erfüllt:

1. **Django Models**
   - ✅ 5 Models implementiert (StandardBauteil, BauteilRegel, BauteilKatalog, BauteilKatalogPosition, GeometrieBerechnung)
   - ✅ Multi-Gewerk-Unterstützung via ArrayField
   - ✅ Versionskontrolle für Kataloge

2. **Services**
   - ✅ Level 1 Regel-Engine (MULTIPLY, ADD, SUBTRACT, FIXED)
   - ✅ Geometrie-Service mit ABS-Kanten-Automatik
   - ✅ Integration-Service für CalculationEngine

3. **Django Admin**
   - ✅ Bulk-Edit Capabilities
   - ✅ CSV-Export (Excel-kompatibel)
   - ✅ Versionskontrolle UI

4. **Tests**
   - ✅ 39 Unit Tests
   - ✅ >80% Coverage erwartet

5. **Dokumentation**
   - ✅ Implementierungs-Summary
   - ✅ Code-Beispiele
   - ✅ Integration-Guide

### ⏳ Ausstehend (nächste Schritte):

- Migration erstellen & ausführen
- Test-Daten in Datenbank laden
- Integration in CalculationEngine testen
- End-to-End Test mit realen Extraktion-Daten

---

## 📝 Changelog Entry

**Siehe:** `CHANGELOG.md`

```markdown
## [2025-12-07] - Phase 4B: Standardbauteile System

### Added
- **Django Models:** StandardBauteil, BauteilRegel, BauteilKatalog, BauteilKatalogPosition, GeometrieBerechnung
- **Services:**
  - `BauteilRegelEngine`: Level 1 DSL für Mengenberechnung (MULTIPLY, ADD, SUBTRACT, FIXED)
  - `GeometrieService`: Automatische ABS-Kanten-Längen-Berechnung mit user-editierbaren Checkboxes
  - `StandardbauteilIntegrationService`: Integration in Phase 3 CalculationEngine
- **Django Admin:**
  - Bulk-Edit für Bauteile (CSV-Export Excel-kompatibel)
  - Versionskontrolle für Kataloge mit Rollback-Funktion
  - Visuelle Badges und Inline-Editing
- **Tests:** 39 Unit Tests (Regel-Engine + Geometrie-Service)

### Changed
- `models.py`: Import von `models_bauteile.py` hinzugefügt

### Technical Details
- Multi-Gewerk-Support via PostgreSQL ArrayField
- Sichere JSON-basierte DSL (keine Code-Evaluation)
- Geometrie-Berechnungen: Tür, Korpus, Einlegeboden, Schublade
- Standard-Sichtbarkeitsregeln für ABS-Kanten
```

---

## 🤝 Mitwirkende

**Implementiert von:** Claude Code
**Review erforderlich:** Dustin (User)
**Getestet:** Unit Tests ✅ | Integration Tests ⏳

---

**Letztes Update:** 2025-12-07
**Nächste Review:** Nach Migration & Integration Testing
