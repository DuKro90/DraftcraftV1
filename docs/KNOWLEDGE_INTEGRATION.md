# 🧩 Wissensbausteine & TIER-System

**DraftcraftV1 - Knowledge Integration in Calculation Pipeline**
**Version:** 2.3.0 | **Stand:** Dezember 2024

---

## 🎯 Warum ein TIER-System?

### Problem ohne strukturiertes Wissen

```
❌ OHNE TIER-System:
═══════════════════════════════════════════════════════════════

Szenario: Holzpreis steigt um 5%

Probleme:
├─ Alle Preise in Code hardcoded
├─ Änderung erfordert Code-Deployment
├─ Kein Audit-Trail (Wer änderte wann?)
├─ Keine Versionierung (Kann nicht zurückrollen)
└─ Inkonsistenz (Verschiedene Orte im Code)

Result: 2-4 Wochen bis Preis-Update live
```

### Lösung mit TIER-System

```
✅ MIT TIER-System:
═══════════════════════════════════════════════════════════════

Szenario: Holzpreis steigt um 5%

Lösung:
├─ Admin-Interface: MaterialList bearbeiten
├─ Sofort aktiv (kein Deployment)
├─ Automatisches Audit-Log
├─ Versionierung mit Rollback-Option
└─ Zentrale Datenhaltung (Single Source of Truth)

Result: 2-5 Minuten bis Preis-Update live
```

---

## 📊 TIER-System Architektur

### Drei-Schichten-Modell

```
┌─────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE PYRAMID                        │
└─────────────────────────────────────────────────────────────┘

                         ▲
                         │ Increasing Change Frequency
                         │ Decreasing Data Volume
                         │
        ┌────────────────────────────────┐
        │      TIER 3: DYNAMIC           │  Daily/Weekly
        │  (Seasonal, Customer-specific) │  ~10-50 rules
        └────────────────────────────────┘
                     ▲
                     │
          ┌──────────────────────────┐
          │   TIER 2: COMPANY        │      Quarterly
          │  (Labor, Overhead, Margin)│      ~1-5 records
          └──────────────────────────┘
                     ▲
                     │
     ┌───────────────────────────────────┐
     │        TIER 1: GLOBAL             │  1-2× per year
     │   (Materials, Complexity, Surface) │  ~30-50 records
     └───────────────────────────────────┘
```

### Daten-Fluss in Preiskalkulation

```
Extraction Result (ML Output)
  │
  ├─► Entities: ["Eiche", "1,5 m²", "geölt", "gefräst"]
  │
  ↓
┌─────────────────────────────────────────────────────────────┐
│               CALCULATION ENGINE (8 Steps)                   │
└─────────────────────────────────────────────────────────────┘
  │
  ├─► STEP 1: Base Price
  │   └─► Input: Material name + Dimension from entities
  │
  ├─► STEP 2-4: Multiply by TIER 1 Factors
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Query Database:                                    │
  │   │  ├─ MaterialList.get(name="Eiche")     → 1.3       │
  │   │  ├─ ComplexityFactor.get(name="gefräst") → 1.15    │
  │   │  └─ SurfaceFinish.get(name="geölt")    → 1.1       │
  │   └─────────────────────────────────────────────────────┘
  │
  ├─► STEP 5-7: Apply TIER 2 Company Metrics
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Query Database:                                    │
  │   │  CompanyMetrics.get_active()                        │
  │   │  ├─ labor_rate = 65 €/h                            │
  │   │  ├─ overhead_rate = 0.25 (25%)                     │
  │   │  └─ margin_rate = 0.20 (20%)                       │
  │   └─────────────────────────────────────────────────────┘
  │
  └─► STEP 8: Apply TIER 3 Dynamic Rules
      ┌─────────────────────────────────────────────────────┐
      │  Query Database:                                    │
      │  PricingRule.filter(is_active=True, valid_until>now)│
      │  ├─ "Winter-Rabatt": -5%                           │
      │  └─ "Stammkunde": -10%                             │
      └─────────────────────────────────────────────────────┘
      ↓
  FINAL PRICE: 1.268,29 € (with all factors applied)
```

---

## 🏗️ TIER 1: Global Standards

### Konzept

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: INDUSTRIE-STANDARDS                                │
├─────────────────────────────────────────────────────────────┤
│  Was:  Branchenübliche Multiplikatoren                      │
│  Wer:  Definiert durch Handwerks-Verbände / Erfahrungswerte │
│  Änderung: Selten (1-2× pro Jahr)                           │
│  Beispiel: "Eiche ist 30% teurer als Referenz-Holz"         │
└─────────────────────────────────────────────────────────────┘
```

### Model 1: MaterialList

```python
# backend/documents/models.py

class MaterialList(models.Model):
    """
    Holzarten, Metalle, Stoffe mit Basis-Eigenschaften und Preis-Faktoren.
    """
    # Identifikation
    name = models.CharField(max_length=100, unique=True)
    # Beispiel: "Eiche massiv", "Buche gedämpft", "Kiefer"

    category = models.CharField(max_length=50)
    # Beispiel: "Hartholz", "Weichholz", "Furnierholz"

    # Preisfaktor (relativ zu Basis-Material)
    factor = models.DecimalField(max_digits=4, decimal_places=2)
    # Beispiel: 1.30 = 30% teurer als Basis
    # Basis ist typischerweise Kiefer (factor=1.0)

    base_price_per_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    # Beispiel: 150.00 € pro m² für Eiche massiv

    # Eigenschaften (für ML-Context & Transparenz)
    properties = models.JSONField(default=dict)
    # Beispiel:
    # {
    #   "härte": "hoch",
    #   "farbe": "hellbraun-rotbraun",
    #   "herkunft": "Europa",
    #   "nachhaltigkeit": "FSC-zertifiziert",
    #   "verwendung": ["Möbel", "Parkett", "Treppen"],
    #   "verarbeitung": "schwer (hohe Dichte)"
    # }

    # Verfügbarkeit
    is_active = models.BooleanField(default=True)
    # False = Nicht mehr lieferbar / nicht mehr anbieten

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Material"
        verbose_name_plural = "Materialliste (TIER 1)"

    def __str__(self):
        return f"{self.name} (Faktor: {self.factor})"
```

**Beispiel-Daten:**

```sql
INSERT INTO documents_materiallist (name, category, factor, base_price_per_sqm, properties) VALUES
('Eiche massiv', 'Hartholz', 1.30, 150.00, '{"härte":"hoch","farbe":"hellbraun"}'),
('Buche gedämpft', 'Hartholz', 1.20, 130.00, '{"härte":"hoch","farbe":"rötlich"}'),
('Kiefer', 'Weichholz', 0.90, 90.00, '{"härte":"mittel","farbe":"gelblich"}'),
('Fichte', 'Weichholz', 0.80, 80.00, '{"härte":"niedrig","farbe":"hell"}'),
('Nussbaum', 'Edelholz', 1.80, 220.00, '{"härte":"hoch","farbe":"dunkelbraun"}');
```

### Model 2: ComplexityFactor

```python
class ComplexityFactor(models.Model):
    """
    Verarbeitungs-Komplexität mit Preis-Aufschlägen.
    """
    name = models.CharField(max_length=100, unique=True)
    # Beispiel: "gefräst", "gedrechselt", "geschnitzt"

    description = models.TextField()
    # Beispiel: "CNC-Fräsung von Kanten, Profilen oder Mustern"

    factor = models.DecimalField(max_digits=4, decimal_places=2)
    # Beispiel: 1.15 = 15% Aufschlag

    required_skill_level = models.CharField(max_length=50)
    # Beispiel: "Geselle mit CNC-Kenntnissen"

    required_equipment = models.CharField(max_length=200)
    # Beispiel: "CNC-Fräse, CAD/CAM-Software"

    time_factor = models.DecimalField(max_digits=3, decimal_places=2)
    # Beispiel: 1.5 = 50% mehr Arbeitszeit als Standard

    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['factor']
        verbose_name = "Komplexitätsfaktor"
        verbose_name_plural = "Komplexitätsfaktoren (TIER 1)"

    def __str__(self):
        return f"{self.name} (+{(self.factor-1)*100:.0f}%)"
```

**Beispiel-Daten:**

```sql
INSERT INTO documents_complexityfactor (name, description, factor, time_factor) VALUES
('Standard', 'Gerade Kanten, maschineller Zuschnitt', 1.00, 1.0),
('gefräst', 'CNC-Fräsung von Profilen', 1.15, 1.3),
('gedrechselt', 'Drechselarbeiten (Beine, Säulen)', 1.25, 1.5),
('geschnitzt', 'Handwerk-Schnitzerei', 1.50, 2.0),
('hand_geschnitzt', 'Feine Handschnitzerei (Ornamente)', 2.00, 3.0),
('intarsien', 'Einlegearbeiten verschiedener Hölzer', 1.80, 2.5);
```

### Model 3: SurfaceFinish

```python
class SurfaceFinish(models.Model):
    """
    Oberflächenbehandlung mit Preis-Aufschlägen.
    """
    name = models.CharField(max_length=100, unique=True)
    # Beispiel: "geölt", "lackiert", "gewachst"

    process_description = models.TextField()
    # Beispiel: "3-schichtige Öl-Behandlung mit UV-beständigem Öl"

    factor = models.DecimalField(max_digits=4, decimal_places=2)
    # Beispiel: 1.10 = 10% Aufschlag

    durability_years = models.IntegerField()
    # Beispiel: 10 Jahre (Erwartete Haltbarkeit)

    maintenance_effort = models.CharField(max_length=50)
    # Beispiel: "Niedrig", "Mittel", "Hoch"

    eco_friendly = models.BooleanField(default=True)
    # Beispiel: True = Umweltfreundlich (wichtig für Kunden)

    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['factor']
        verbose_name = "Oberfläche"
        verbose_name_plural = "Oberflächenbehandlungen (TIER 1)"

    def __str__(self):
        return f"{self.name} (+{(self.factor-1)*100:.0f}%)"
```

**Beispiel-Daten:**

```sql
INSERT INTO documents_surfacefinish (name, process_description, factor, durability_years, maintenance_effort) VALUES
('naturbelassen', 'Keine Behandlung, nur geschliffen', 1.00, 5, 'Hoch'),
('geölt', '3× Öl-Behandlung, UV-beständig', 1.10, 10, 'Mittel'),
('gewachst', 'Bienenwachs-Politur', 1.08, 8, 'Mittel'),
('lackiert', '2K-Lack, matt oder glänzend', 1.15, 15, 'Niedrig'),
('lasiert', 'Farbige Lasur (Holz sichtbar)', 1.12, 12, 'Niedrig'),
('klavierlack', 'Hochglanz-Lackierung (12 Schichten)', 1.60, 20, 'Niedrig');
```

### TIER 1 Workflow im System

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1 DATA LIFECYCLE                                      │
└─────────────────────────────────────────────────────────────┘

1. INITIAL SETUP (bei System-Start)
   └─► Admin importiert Industrie-Standards
       ├─ CSV-Import oder Django Fixtures
       └─ ~30-50 Einträge pro Modell

2. USAGE IN CALCULATION
   └─► CalculationEngine queries aktive Faktoren
       ├─ Cache: In-Memory für Performance
       ├─ Invalidierung: Bei Update via Django Signals
       └─> <1ms Zugriff auf gecachte Daten

3. ANNUAL REVIEW (1-2× pro Jahr)
   └─► Geschäftsführung prüft Faktoren
       ├─ Trigger: Marktpreis-Änderungen
       ├─ Änderung: Django Admin Interface
       └─► Sofort aktiv für neue Kalkulationen

4. AUDIT & COMPLIANCE
   └─► Jede Änderung geloggt
       ├─ Wer: updated_by (User)
       ├─ Wann: updated_at (Timestamp)
       └─► Historisierung: Django-Reversion (optional)
```

---

## 🏢 TIER 2: Company Metrics

### Konzept

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: BETRIEBSKENNZAHLEN                                 │
├─────────────────────────────────────────────────────────────┤
│  Was:  Firmen-spezifische Kosten & Margen                   │
│  Wer:  Definiert durch Geschäftsführung                     │
│  Änderung: Quartalsweise (4× pro Jahr)                      │
│  Beispiel: "Unser Stundensatz: 65 €/h"                      │
└─────────────────────────────────────────────────────────────┘
```

### Model: CompanyMetrics

```python
class CompanyMetrics(models.Model):
    """
    Betriebswirtschaftliche Kennzahlen pro Firma.
    """
    # Firma (Multi-Tenant Support)
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    # Falls mehrere Betriebe dasselbe System nutzen

    # LABOR COSTS (Personalkosten)
    labor_rate_journeyman = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Stundensatz Geselle (€/h)"
    )
    # Beispiel: 65.00 €/h

    labor_rate_master = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Stundensatz Meister (€/h)"
    )
    # Beispiel: 85.00 €/h

    labor_rate_apprentice = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Stundensatz Azubi (€/h)"
    )
    # Beispiel: 35.00 €/h

    # OVERHEAD (Gemeinkosten)
    overhead_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        help_text="Gemeinkostenzuschlag (0.25 = 25%)"
    )
    # Beispiel: 0.2500 (25%)
    # Umfasst: Miete, Strom, Versicherung, Verwaltung, Werkzeug-Abnutzung

    # MARGIN (Gewinnmarge)
    margin_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        help_text="Gewinnmarge (0.20 = 20%)"
    )
    # Beispiel: 0.2000 (20%)

    # ARBEITSZEIT-SCHÄTZUNG (für Preiskalkulation)
    avg_hours_per_sqm = models.DecimalField(
        max_digits=4, decimal_places=2,
        help_text="Durchschnittliche Arbeitsstunden pro m²"
    )
    # Beispiel: 5.0h (für Standard-Möbel)

    # VALIDITY (Gültigkeitszeitraum)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    # Beispiel: 2024-01-01 bis 2024-03-31 (Q1)
    # valid_until=null → Aktuell gültig

    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-valid_from']
        verbose_name = "Betriebskennzahl"
        verbose_name_plural = "Betriebskennzahlen (TIER 2)"

    def __str__(self):
        return f"{self.company.name} - gültig ab {self.valid_from}"

    @classmethod
    def get_active(cls, company_id):
        """Returns currently active metrics for a company."""
        today = timezone.now().date()
        return cls.objects.filter(
            company_id=company_id,
            is_active=True,
            valid_from__lte=today,
            valid_until__isnull=True  # or valid_until >= today
        ).first()
```

**Beispiel-Daten:**

```sql
-- Schreinerei Müller GmbH
INSERT INTO documents_companymetrics (
    company_id, labor_rate_journeyman, labor_rate_master,
    overhead_rate, margin_rate, avg_hours_per_sqm,
    valid_from, is_active
) VALUES (
    1, 65.00, 85.00, 0.2500, 0.2000, 5.0, '2024-01-01', true
);

-- Quartals-Update Q2 (höhere Stundensätze)
INSERT INTO documents_companymetrics (
    company_id, labor_rate_journeyman, labor_rate_master,
    overhead_rate, margin_rate, avg_hours_per_sqm,
    valid_from, is_active
) VALUES (
    1, 68.00, 88.00, 0.2500, 0.2000, 5.0, '2024-04-01', true
);
-- Vorherige Zeile wird automatisch valid_until='2024-03-31' gesetzt
```

### TIER 2 im Calculation Engine

```python
# Beispiel-Code: calculation_engine.py

class CalculationEngine:
    def calculate_price(self, entities: List[Entity]) -> Decimal:
        # ... Steps 1-4 (TIER 1) ...

        # STEP 5: Labor Cost (TIER 2)
        metrics = CompanyMetrics.get_active(company_id=self.company_id)

        material_sqm = entities.get_dimension_value()  # 1.5 m²
        hours_needed = material_sqm * metrics.avg_hours_per_sqm  # 7.5h

        # Annahme: 80% Geselle, 20% Meister
        labor_cost = (
            hours_needed * 0.8 * metrics.labor_rate_journeyman +
            hours_needed * 0.2 * metrics.labor_rate_master
        )
        # = 7.5h × (0.8 × 65€ + 0.2 × 85€) = 7.5h × 69€ = 517.50€

        subtotal = material_cost + labor_cost  # From steps 1-4

        # STEP 6: Overhead (TIER 2)
        overhead = subtotal * metrics.overhead_rate
        # = (370.02 + 517.50) × 0.25 = 221.88€

        subtotal += overhead

        # STEP 7: Margin (TIER 2)
        margin = subtotal * metrics.margin_rate
        # = (887.52) × 0.20 = 177.50€

        final_price = subtotal + margin
        # = 1.065,02€

        return final_price
```

### Quartals-Review Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  QUARTERLY COMPANY METRICS UPDATE                           │
└─────────────────────────────────────────────────────────────┘

Zeitpunkt: Ende Q1/Q2/Q3/Q4 (z.B. März 25)

1. PREPARATION
   └─► Geschäftsführung analysiert:
       ├─ Kostenentwicklung (Personal, Miete, Material)
       ├─ Marktpreise (Wettbewerb)
       └─► Gewinnmarge-Ziel

2. UPDATE IN ADMIN
   └─► Django Admin → Company Metrics → Add New
       ├─ Alte Metriken: valid_until = 31.03.2024
       ├─ Neue Metriken: valid_from = 01.04.2024
       └─► System wählt automatisch richtige Metriken

3. IMPACT ANALYSIS (System-generiert)
   └─► Report zeigt:
       ├─ Durchschnittspreis alt vs. neu
       ├─ Betroffene offene Angebote
       └─► Empfehlung: Angebote aktualisieren?

4. NOTIFICATION
   └─► E-Mail an alle Kalkulations-Nutzer:
       "Neue Betriebskennzahlen ab 01.04. aktiv"
```

---

## 🎛️ TIER 3: Dynamic Rules

### Konzept

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: DYNAMISCHE REGELN                                  │
├─────────────────────────────────────────────────────────────┤
│  Was:  Kontext-abhängige Preis-Anpassungen                  │
│  Wer:  Geschäftsführung + Büro-Personal                     │
│  Änderung: Wöchentlich/Täglich                              │
│  Beispiel: "Winter-Rabatt -5% (Dez-Feb)"                    │
└─────────────────────────────────────────────────────────────┘
```

### Model: PricingRule

```python
class PricingRule(models.Model):
    """
    Dynamische Preis-Regeln mit Bedingungen.
    """
    RULE_TYPES = [
        ('DISCOUNT', 'Rabatt'),
        ('SURCHARGE', 'Aufschlag'),
        ('CUSTOM', 'Benutzerdefiniert'),
    ]

    name = models.CharField(max_length=100)
    # Beispiel: "Winter-Rabatt 2024"

    description = models.TextField()
    # Beispiel: "5% Rabatt für Aufträge in Winter-Monaten (Auslastung niedrig)"

    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)

    adjustment = models.DecimalField(
        max_digits=6, decimal_places=4,
        help_text="Adjustment factor: -0.05 = -5%, +0.10 = +10%"
    )
    # Beispiel: -0.0500 (5% Rabatt)

    # CONDITIONS (JSON for flexibility)
    conditions = models.JSONField(default=dict)
    # Beispiel:
    # {
    #   "date_range": {"start": "2024-12-01", "end": "2025-02-28"},
    #   "customer_ids": [123, 456],  # Nur für diese Kunden
    #   "project_type": "Möbel",     # Nur für Möbel-Projekte
    #   "min_value": 1000.00,        # Nur bei Aufträgen >1000€
    #   "material_category": "Hartholz"  # Nur Hartholz-Projekte
    # }

    priority = models.IntegerField(default=0)
    # Higher priority = applied first
    # Beispiel: Stammkunden-Rabatt (prio=10) vor Saison-Rabatt (prio=5)

    is_active = models.BooleanField(default=True)

    valid_from = models.DateField()
    valid_until = models.DateField()
    # Beispiel: 2024-12-01 bis 2025-02-28

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-priority', 'name']
        verbose_name = "Preis-Regel"
        verbose_name_plural = "Preis-Regeln (TIER 3)"

    def __str__(self):
        sign = '+' if self.adjustment > 0 else ''
        return f"{self.name} ({sign}{self.adjustment*100:.1f}%)"

    def is_applicable(self, context: dict) -> bool:
        """
        Checks if rule applies to given context.

        Args:
            context: {
                'date': datetime.date,
                'customer_id': int,
                'project_type': str,
                'total_value': Decimal,
                'material_category': str
            }
        """
        # Check active & validity
        if not self.is_active:
            return False
        if not (self.valid_from <= context['date'] <= self.valid_until):
            return False

        # Check conditions
        cond = self.conditions

        if 'customer_ids' in cond:
            if context.get('customer_id') not in cond['customer_ids']:
                return False

        if 'project_type' in cond:
            if context.get('project_type') != cond['project_type']:
                return False

        if 'min_value' in cond:
            if context.get('total_value', 0) < Decimal(cond['min_value']):
                return False

        if 'material_category' in cond:
            if context.get('material_category') != cond['material_category']:
                return False

        return True
```

**Beispiel-Daten:**

```sql
-- Winter-Rabatt (Saison-abhängig)
INSERT INTO documents_pricingrule (
    name, description, rule_type, adjustment, conditions,
    priority, valid_from, valid_until, is_active
) VALUES (
    'Winter-Rabatt 2024/25',
    'Auslastung niedrig im Winter',
    'DISCOUNT',
    -0.0500,  -- 5% Rabatt
    '{"date_range": {"start": "2024-12-01", "end": "2025-02-28"}}',
    5,
    '2024-12-01',
    '2025-02-28',
    true
);

-- Stammkunden-Rabatt (Kunden-spezifisch)
INSERT INTO documents_pricingrule (
    name, description, rule_type, adjustment, conditions,
    priority, valid_from, valid_until, is_active
) VALUES (
    'Stammkunde: Möbelhaus XY',
    '10% Rabatt für langjährigen Stammkunden',
    'DISCOUNT',
    -0.1000,  -- 10% Rabatt
    '{"customer_ids": [123]}',  -- customer_id=123
    10,  -- Higher priority than seasonal
    '2024-01-01',
    '2025-12-31',
    true
);

-- Express-Aufschlag (Dringlichkeit)
INSERT INTO documents_pricingrule (
    name, description, rule_type, adjustment, conditions,
    priority, valid_from, valid_until, is_active
) VALUES (
    'Express-Zuschlag',
    'Lieferung in <7 Tagen',
    'SURCHARGE',
    0.2000,  -- 20% Aufschlag
    '{"express_delivery": true}',
    15,
    '2024-01-01',
    '2025-12-31',
    true
);

-- Großauftrags-Rabatt (Wert-basiert)
INSERT INTO documents_pricingrule (
    name, description, rule_type, adjustment, conditions,
    priority, valid_from, valid_until, is_active
) VALUES (
    'Großauftrag-Rabatt',
    'Ab 5.000€ Auftragswert',
    'DISCOUNT',
    -0.0300,  -- 3% Rabatt
    '{"min_value": 5000.00}',
    8,
    '2024-01-01',
    '2025-12-31',
    true
);
```

### TIER 3 im Calculation Engine

```python
# Beispiel-Code: calculation_engine.py (STEP 8)

class CalculationEngine:
    def calculate_price(self, entities: List[Entity]) -> Decimal:
        # ... Steps 1-7 (TIER 1 + TIER 2) ...
        base_price = Decimal('1065.02')  # Nach Schritt 7

        # STEP 8: Apply TIER 3 Dynamic Rules
        context = {
            'date': timezone.now().date(),
            'customer_id': self.customer_id,
            'project_type': entities.get_project_type(),
            'total_value': base_price,
            'material_category': entities.get_material_category()
        }

        # Fetch applicable rules (sorted by priority)
        rules = PricingRule.objects.filter(
            is_active=True,
            valid_from__lte=context['date'],
            valid_until__gte=context['date']
        ).order_by('-priority')

        # Apply rules in priority order
        applied_rules = []
        final_price = base_price

        for rule in rules:
            if rule.is_applicable(context):
                adjustment = final_price * rule.adjustment
                final_price += adjustment

                applied_rules.append({
                    'rule': rule.name,
                    'adjustment': adjustment,
                    'new_total': final_price
                })

        # Example Result:
        # base_price = 1.065,02€
        # Rule 1: "Stammkunde" (-10%) → -106,50€ = 958,52€
        # Rule 2: "Winter-Rabatt" (-5% on new total) → -47,93€ = 910,59€
        # final_price = 910,59€

        return final_price, applied_rules
```

### TIER 3 Management Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  DYNAMIC RULE LIFECYCLE                                     │
└─────────────────────────────────────────────────────────────┘

1. CREATE NEW RULE (Ad-hoc)
   Trigger: Geschäftsführung beschließt Promotion
   ├─► Django Admin → Pricing Rules → Add
   ├─► Felder ausfüllen (Name, Bedingungen, Gültigkeit)
   └─► Save → Sofort aktiv (wenn is_active=True)

2. MONITOR USAGE
   System tracked automatisch:
   ├─► Wie oft angewendet? (Counter pro Regel)
   ├─► Durchschnittlicher Rabatt/Aufschlag in €?
   └─► ROI: Hat Regel mehr Aufträge generiert?

3. EXPIRE AUTOMATICALLY
   Cron Job (täglich):
   ├─► Deaktiviert Regeln mit valid_until < heute
   └─► Optional: E-Mail "Regel XY ausgelaufen"

4. MANUAL DEACTIVATE
   Geschäftsführung:
   ├─► Regel vorzeitig beenden (is_active=False)
   └─► Grund: Budget erschöpft, Ziel erreicht
```

---

## 🔗 Integration aller TIERs

### Vollständiges Kalkulations-Beispiel

```
PROJECT: Eichen-Schreibtisch für Stammkunde im Winter
════════════════════════════════════════════════════════════

Extrahierte Entities (ML):
  - Material: "Eiche massiv"
  - Dimension: "1,5 m²"
  - Complexity: "gefräst"
  - Surface: "geölt"

Context:
  - Kunde: Möbelhaus XY (ID=123, Stammkunde)
  - Datum: 15. Dezember 2024
  - Auftragswert: Noch unbekannt (wird berechnet)

═══════════════════════════════════════════════════════════════

STEP 1: Base Price
  MaterialList.get(name="Eiche massiv").base_price_per_sqm = 150€
  150€ × 1.5 m² = 225,00€

STEP 2: Material Factor (TIER 1)
  MaterialList.get(name="Eiche massiv").factor = 1.3
  225,00€ × 1.3 = 292,50€

STEP 3: Complexity Factor (TIER 1)
  ComplexityFactor.get(name="gefräst").factor = 1.15
  292,50€ × 1.15 = 336,38€

STEP 4: Surface Factor (TIER 1)
  SurfaceFinish.get(name="geölt").factor = 1.10
  336,38€ × 1.10 = 370,02€

STEP 5: Labor Cost (TIER 2)
  CompanyMetrics.get_active()
    .avg_hours_per_sqm = 5.0h/m²
    .labor_rate_journeyman = 65€/h
  1.5 m² × 5.0h/m² = 7.5h
  7.5h × 65€/h = 487,50€
  Subtotal: 370,02€ + 487,50€ = 857,52€

STEP 6: Overhead (TIER 2)
  CompanyMetrics.get_active().overhead_rate = 0.25 (25%)
  857,52€ × 0.25 = 214,38€
  Subtotal: 857,52€ + 214,38€ = 1.071,90€

STEP 7: Margin (TIER 2)
  CompanyMetrics.get_active().margin_rate = 0.20 (20%)
  1.071,90€ × 0.20 = 214,38€
  Subtotal: 1.071,90€ + 214,38€ = 1.286,28€

STEP 8: Dynamic Rules (TIER 3)
  Context: {customer_id: 123, date: 2024-12-15, total: 1.286,28€}

  Rule 1 (Priority 10): "Stammkunde Möbelhaus XY"
    Conditions: customer_id=123 ✓
    Adjustment: -10%
    1.286,28€ × -0.10 = -128,63€
    New Total: 1.157,65€

  Rule 2 (Priority 5): "Winter-Rabatt 2024/25"
    Conditions: date in Dec-Feb ✓
    Adjustment: -5%
    1.157,65€ × -0.05 = -57,88€
    New Total: 1.099,77€

═══════════════════════════════════════════════════════════════
FINAL PRICE (netto): 1.099,77€
USt (19%): 208,96€
BRUTTO: 1.308,73€

Applied Factors:
  ✓ TIER 1: Eiche (+30%), Gefräst (+15%), Geölt (+10%)
  ✓ TIER 2: Labor 7.5h, Overhead +25%, Margin +20%
  ✓ TIER 3: Stammkunde -10%, Winter -5%

Time to Calculate: 0.05 seconds (all data cached)
```

---

## 📊 Wissensbausteine: Performance & Caching

### Caching-Strategie

```
┌─────────────────────────────────────────────────────────────┐
│  KNOWLEDGE DATA CACHING                                     │
└─────────────────────────────────────────────────────────────┘

TIER 1 (Changes 1-2×/year):
  Cache: Application Memory (Django cache framework)
  Duration: 24 hours or until update signal
  Key: "tier1_materials", "tier1_complexity", "tier1_surface"
  Invalidation: Django signal on model save/delete

TIER 2 (Changes 4×/year):
  Cache: Application Memory
  Duration: 6 hours
  Key: "tier2_company_{company_id}_active"
  Invalidation: On CompanyMetrics update

TIER 3 (Changes daily/weekly):
  Cache: Redis (shared across instances)
  Duration: 1 hour
  Key: "tier3_active_rules"
  Invalidation: On PricingRule update
  Background refresh: Every 15 minutes

Performance Impact:
  Without cache: 5-10 DB queries per calculation
  With cache: 0-1 DB queries (only if cache miss)
  Speed-up: 10-20× faster (0.5s → 0.05s)
```

### Monitoring & Analytics

```
Tracked Metrics (Real-time Dashboard):
═══════════════════════════════════════════════════════════════

TIER 1 Usage:
  - Most used materials (Top 10)
  - Average material factor: 1.15
  - Complexity distribution: 60% Standard, 30% Gefräst, 10% Other

TIER 2 Impact:
  - Average labor hours per project: 6.2h
  - Average margin: 19.5% (Target: 20%)
  - Overhead coverage: 98% (near target)

TIER 3 Effectiveness:
  - Active rules: 8
  - Most applied: "Winter-Rabatt" (45% of projects in Dec-Feb)
  - Average discount: -8.2%
  - Revenue impact: -€12,500 (December), +25 projects (vs last year)

Knowledge Completeness:
  - TIER 1 coverage: 95% (entities found in database)
  - Missing entities: 5% (routed to Human Review)
  - Action: Add missing materials/surfaces to TIER 1
```

---

**Abschluss:** Das TIER-System ermöglicht **flexible, wartbare und transparente** Preiskalkulation ohne Code-Änderungen. Alle Wissensbausteine sind zentral verwaltbar, versioniert und audit-konform.

**Nächste Datei:** `README.md` - Übersichts-Index für alle Dokumentations-Dateien.
