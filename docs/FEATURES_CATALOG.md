# 📋 Features & Komponenten Katalog

**DraftcraftV1 - German Handwerk Document Analysis System**
**Version:** 2.3.0 | **Stand:** Dezember 2024

---

## 🎯 Übersicht

Das System bietet **5 Haupt-Features** für deutsche Handwerksbetriebe:

```
┌─────────────────────────────────────────────────────────────┐
│  DraftcraftV1 - Intelligente Dokument-Analyse & Kalkulation │
└─────────────────────────────────────────────────────────────┘
           │
           ├─► 1. Dokument-Extraktion (OCR + NER)
           ├─► 2. Intelligente Qualitätssicherung (Agentic RAG)
           ├─► 3. Automatische Preiskalkulation (8-Stufen)
           ├─► 4. Pattern-Analyse & Selbstlernend
           └─► 5. Transparenz & Nachvollziehbarkeit
```

---

## 1️⃣ Dokument-Extraktion

### Feature: OCR-Texterkennung aus Bau-Dokumenten

**Was macht es?**
Liest deutschen Text aus PDFs, Bildern und GAEB-XML Dateien mit spezieller Optimierung für Handwerks-Terminologie.

**Beteiligte Komponenten:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PDF/Image  │────►│  PaddleOCR   │────►│  Structured  │
│   Upload     │     │  (German)    │     │    Text      │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            └─► backend/extraction/services/ocr_service.py
```

**Technische Details:**
- **Service:** `GermanHandwerkOCRService` (`ocr_service.py`)
- **ML Model:** PaddleOCR 2.7 mit deutschen Modellen
- **Input:** PDF, JPG, PNG, TIFF (max 10MB)
- **Output:** Strukturierter Text mit Confidence Scores
- **Performance:** <2 Sekunden pro A4-Seite

**Besonderheiten:**
- ✅ Deutsche Umlaute (ä, ö, ü, ß)
- ✅ Zahlenformate: `1.234,56 €` (Punkt = Tausender, Komma = Dezimal)
- ✅ Datum: `DD.MM.YYYY`
- ✅ Handschrift-Erkennung (begrenzt)

---

### Feature: NER-Extraktion (Named Entity Recognition)

**Was macht es?**
Erkennt strukturierte Informationen wie Materialien, Maße, Preise aus dem OCR-Text.

**Beteiligte Komponenten:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  OCR Text    │────►│  spaCy NER   │────►│  Entities    │
│              │     │  (de_lg)     │     │  + Relations │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            └─► backend/extraction/services/ner_service.py
```

**Technische Details:**
- **Service:** `GermanHandwerkNERService` (`ner_service.py`)
- **ML Model:** spaCy 3.8 `de_core_news_lg` + Custom Labels
- **Extrahierte Entities:**
  - `MATERIAL`: Holzarten, Metalle, Stoffe
  - `DIMENSION`: Maße (m², lfm, Stk)
  - `MONEY`: Preise, Beträge
  - `DATE`: Termine, Fristen
  - `QUANTITY`: Mengenangaben
  - `SURFACE`: Oberflächenbehandlung
  - `COMPLEXITY`: Komplexitäts-Indikatoren

**Output-Beispiel:**
```json
{
  "entities": [
    {"text": "Eiche massiv", "label": "MATERIAL", "confidence": 0.94},
    {"text": "25 m²", "label": "DIMENSION", "confidence": 0.98},
    {"text": "geölt", "label": "SURFACE", "confidence": 0.89}
  ],
  "processing_time": 0.32
}
```

---

### Feature: GAEB XML Parser

**Was macht es?**
Liest standardisierte Leistungsverzeichnisse (LV) im GAEB-Format für Bauindustrie.

**Beteiligte Komponenten:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  GAEB XML    │────►│  XML Parser  │────►│  Structured  │
│  (VOB/A)     │     │  + Validator │     │  Positions   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            └─► backend/extraction/services/gaeb_service.py
```

**Technische Details:**
- **Service:** `GermanGAEBService` (`gaeb_service.py`)
- **Standards:** GAEB DA XML 3.3, VOB/A konform
- **Encoding:** UTF-8, Fallback Windows-1252
- **Performance:** <5 Sekunden für 100 Positionen

**Extrahierte Daten:**
- Ordnungszahl (LV-Position)
- Kurztext & Langtext
- Menge & Einheit
- Einheitspreis (EP)
- Gesamtpreis (GP)

---

## 2️⃣ Intelligente Qualitätssicherung (Agentic RAG)

### Feature: KI-gestützte Extraktion mit Gemini

**Was macht es?**
Bei niedriger OCR/NER-Confidence nutzt das System Google Gemini 1.5 Flash für verbesserte Extraktion.

**Beteiligte Komponenten:**
```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Low Confidence  │────►│  Gemini Agent    │────►│  Enhanced Data   │
│  Extraction      │     │  + Memory        │     │  + Explanation   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                  │
                                  ├─► backend/extraction/services/gemini_agent_service.py
                                  ├─► backend/extraction/services/memory_service.py
                                  └─► backend/extraction/services/confidence_router.py
```

**Technische Details:**
- **Services:**
  - `GeminiAgentService` - LLM API Integration
  - `MemoryService` - Dual-Layer Memory (Redis + PostgreSQL)
  - `ConfidenceRouter` - Intelligent Routing Logic

**4-Tier Routing System:**

```
Confidence Score      Action              Cost          Processing Time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
≥ 0.92               AUTO_ACCEPT         $0            <1s
0.80 - 0.92          AGENT_VERIFY        ~$0.0001      2-3s
0.70 - 0.80          AGENT_EXTRACT       ~$0.00025     3-5s
< 0.70               HUMAN_REVIEW        $0            Manual
```

**Memory-System:**
- **Short-term (Redis):** Letzte 100 Dokumente, TTL 24h
- **Long-term (PostgreSQL):** Alle verifizierten Extractions, unbegrenzt
- **Nutzung:** Kontext für Gemini-Prompts, Pattern-Erkennung

---

### Feature: Cost Tracking & Budget Management

**Was macht es?**
Überwacht API-Kosten und stoppt automatisch bei Budget-Überschreitung.

**Beteiligte Komponenten:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  API Call    │────►│  Cost        │────►│  Alert /     │
│              │     │  Tracker     │     │  Throttle    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            └─► backend/extraction/services/gemini_agent_service.py
```

**Technische Details:**
- **Tracking:** Pro Request, Daily, Monthly
- **Default Budget:** $10/month
- **Alert bei:** 80% Budget-Verbrauch
- **Action bei:** 100% → Gemini deaktivieren, nur OCR/NER

---

## 3️⃣ Automatische Preiskalkulation

### Feature: 8-Stufen Calculation Engine

**Was macht es?**
Berechnet präzise Handwerker-Preise basierend auf Material, Komplexität, Betriebskennzahlen.

**Beteiligte Komponenten:**
```
┌──────────────────────────────────────────────────────────────┐
│                    8-Stufen Calculation Pipeline              │
└──────────────────────────────────────────────────────────────┘
          │
          ├─► Step 1: Base Price Calculation
          │           (Material × Dimension)
          │
          ├─► Step 2: Material Factor (TIER 1)
          │           (Holzart: Eiche=1.3, Kiefer=0.9)
          │
          ├─► Step 3: Complexity Factor (TIER 1)
          │           (Gefräst=1.15, Geschnitzt=1.5)
          │
          ├─► Step 4: Surface Factor (TIER 1)
          │           (Geölt=1.1, Lackiert=1.15)
          │
          ├─► Step 5: Labor Cost (TIER 2)
          │           (Stundensatz × Arbeitsstunden)
          │
          ├─► Step 6: Overhead (TIER 2)
          │           (Werkstatt, Verwaltung, Versicherung)
          │
          ├─► Step 7: Margin (TIER 2)
          │           (Gewinnmarge 15-30%)
          │
          └─► Step 8: Dynamic Adjustments (TIER 3)
                      (Saison, Kunde, Auslastung)
```

**Technische Details:**
- **Service:** `CalculationEngine` (`calculation_engine.py`)
- **Models:** `MaterialList`, `ComplexityFactor`, `SurfaceFinish`, `CompanyMetrics`
- **Input:** Extracted Entities + TIER 1/2/3 Data
- **Output:** Detaillierte Preisaufstellung + Begründung

**Beispiel-Kalkulation:**
```
Projekt: Eichen-Schreibtisch, 1,5 m², geölt, gefräste Kanten

Step 1: Base Price        = 150,00 € × 1.5 m²        = 225,00 €
Step 2: Holzart (Eiche)   = 225,00 € × 1.3           = 292,50 €
Step 3: Komplexität       = 292,50 € × 1.15          = 336,38 €
Step 4: Oberfläche (geölt)= 336,38 € × 1.1           = 370,02 €
Step 5: Arbeitszeit       = 8h × 65 €/h              = 520,00 €
Step 6: Gemeinkosten      = (370,02 + 520) × 0.25    = 222,51 €
Step 7: Marge             = (370,02 + 520 + 222,51) × 0.20 = 222,51 €
Step 8: Saisonrabatt      = 1.335,04 € × 0.95        = 1.268,29 €

ENDPREIS: 1.268,29 € (netto)
```

---

### Feature: TIER 1/2/3 Wissensbausteine

**Was macht es?**
Strukturiert Preis-relevantes Wissen in 3 Kategorien mit unterschiedlicher Änderungshäufigkeit.

**TIER-System Übersicht:**

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: GLOBAL STANDARDS (Änderung: 1-2× pro Jahr)         │
├─────────────────────────────────────────────────────────────┤
│  - Holzarten-Faktoren      (z.B. Eiche=1.3, Fichte=0.8)     │
│  - Komplexitäts-Faktoren   (z.B. Gefräst=1.15)              │
│  - Oberflächen-Faktoren    (z.B. Geölt=1.1)                 │
│  Models: MaterialList, ComplexityFactor, SurfaceFinish      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  TIER 2: COMPANY METRICS (Änderung: 4× pro Jahr)            │
├─────────────────────────────────────────────────────────────┤
│  - Stundensätze            (z.B. Geselle=55€, Meister=75€)  │
│  - Gemeinkostenzuschlag    (z.B. 25%)                        │
│  - Gewinnmarge             (z.B. 20%)                        │
│  Model: CompanyMetrics                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  TIER 3: DYNAMIC (Änderung: Täglich/Wöchentlich)            │
├─────────────────────────────────────────────────────────────┤
│  - Saisonrabatte           (z.B. Winter -5%)                 │
│  - Kundenrabatte           (z.B. Stammkunde -10%)            │
│  - Auslastungs-Faktoren    (z.B. Hochsaison +15%)           │
│  Model: PricingRule                                          │
└─────────────────────────────────────────────────────────────┘
```

**Technische Details:**
- **Models:** 8 Django Models in `backend/documents/models.py`
- **Admin Interface:** Vollständige CRUD-Funktionen
- **Validation:** Automatische Plausibilitäts-Checks

---

## 4️⃣ Pattern-Analyse & Selbstlernendes System

### Feature: Fehler-Pattern Erkennung

**Was macht es?**
Analysiert fehlgeschlagene Extractions und identifiziert systematische Probleme.

**Beteiligte Komponenten:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Failed      │────►│  Pattern     │────►│  Root Cause  │
│  Extractions │     │  Analyzer    │     │  + Fixes     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            └─► backend/extraction/services/pattern_analyzer.py
```

**Technische Details:**
- **Service:** `PatternAnalyzer` (`pattern_analyzer.py`)
- **Modell:** `ExtractionPattern` (Speichert erkannte Muster)
- **Analyse-Kriterien:**
  - Fehler-Häufigkeit (>5 Vorkommen)
  - Root Cause (OCR-Qualität, NER-Fehler, Missing Data)
  - Confidence-Verteilung

**Pattern-Kategorien:**
- `OCR_FAILURE`: Schlechte Bildqualität, falsche Sprache
- `NER_MISS`: Unbekannte Terminologie
- `CALCULATION_ERROR`: Fehlende TIER-Daten
- `TIMEOUT`: Performance-Probleme

---

### Feature: Automatisches Knowledge Building

**Was macht es?**
Generiert Lösungsvorschläge für erkannte Patterns und deployed sie nach Freigabe.

**Beteiligte Komponenten:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Pattern     │────►│  Knowledge   │────►│  Deployed    │
│  Detected    │     │  Builder     │     │  Fix         │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ├─► backend/extraction/services/knowledge_builder.py
                            └─► Models: KnowledgeFix, FixDeployment
```

**Technische Details:**
- **Service:** `SafeKnowledgeBuilder` (`knowledge_builder.py`)
- **Fix-Typen:**
  - `OCR_PREPROCESSING`: Bild-Optimierung
  - `NER_TRAINING_DATA`: Neue Trainings-Beispiele
  - `TIER_DATA_ADDITION`: Fehlende Material/Komplexitäts-Einträge
  - `CALCULATION_RULE`: Neue Berechnungs-Logik

**Sicherheits-Mechanismen:**
- ✅ Staging-Umgebung für Tests
- ✅ Rollback bei Fehler-Rate >10%
- ✅ Admin-Freigabe vor Production-Deploy
- ✅ A/B Testing für neue Fixes

---

## 5️⃣ Transparenz & Nachvollziehbarkeit

### Feature: Calculation Explanations

**Was macht es?**
Generiert verständliche Erklärungen für jede Preiskalkulation.

**Beteiligte Komponenten:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Calculation │────►│  Explanation │────►│  Human-      │
│  Result      │     │  Service     │     │  Readable    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            └─► backend/extraction/services/explanation_service.py
```

**Technische Details:**
- **Service:** `ExplanationService` (`explanation_service.py`)
- **Model:** `CalculationExplanation` (documents/transparency_models.py)
- **Output-Format:** Markdown mit Schritt-für-Schritt Aufschlüsselung

**Beispiel-Erklärung:**
```markdown
## Preiskalkulation: Eichen-Schreibtisch

### Material-Basis
- Holzart: Eiche massiv (Premium-Hartholz, Faktor 1.3)
- Fläche: 1,5 m²
- Basis-Preis: 150,00 €/m²

### Verarbeitungs-Zuschläge
- Komplexität: Gefräste Kanten (+15%)
  → Erfordert CNC-Fräse und Fachkenntnisse
- Oberfläche: Geölt (+10%)
  → 3-schichtige Öl-Behandlung, UV-beständig

### Betriebs-Kosten
- Arbeitszeit: 8 Stunden Geselle (65 €/h)
- Gemeinkosten: 25% (Werkstatt, Strom, Werkzeug)
- Gewinnmarge: 20% (Betriebswirtschaftlich notwendig)

**Endergebnis: 1.268,29 € (netto)**
```

---

### Feature: User Project Benchmarks

**Was macht es?**
Vergleicht Projekt-Preise mit historischen Daten für Transparenz.

**Beteiligte Komponenten:**
- **Model:** `UserProjectBenchmark` (documents/transparency_models.py)
- **Daten:**
  - Durchschnittspreis pro m² (nach Material)
  - Preis-Perzentile (P25, P50, P75)
  - Ähnliche Projekte (5 nächste Nachbarn)

**Beispiel-Benchmark:**
```
Ihr Projekt: Eichen-Schreibtisch, 845 €/m²

Vergleich mit ähnlichen Projekten:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Günstigstes 25%:     720-780 €/m²
Durchschnitt:        810 €/m²
Teuerstes 25%:       840-920 €/m²

Ihr Preis liegt im oberen Durchschnitt ✓
Grund: Hohe Komplexität (gefräste Kanten)
```

---

## 📊 Komponenten-Matrix

### Backend Services Übersicht

| Service                  | File                         | Primäre Funktion                     | Dependencies          |
|--------------------------|------------------------------|--------------------------------------|-----------------------|
| OCRService               | ocr_service.py               | PDF → Text                           | PaddleOCR             |
| NERService               | ner_service.py               | Text → Entities                      | spaCy                 |
| GeminiAgentService       | gemini_agent_service.py      | LLM Enhancement                      | Google AI SDK         |
| MemoryService            | memory_service.py            | Context Management                   | Redis, PostgreSQL     |
| ConfidenceRouter         | confidence_router.py         | Intelligent Routing                  | -                     |
| CalculationEngine        | calculation_engine.py        | Price Calculation                    | TIER 1/2/3 Models     |
| PatternAnalyzer          | pattern_analyzer.py          | Failure Analysis                     | -                     |
| SafeKnowledgeBuilder     | knowledge_builder.py         | Fix Generation                       | PatternAnalyzer       |
| IntegratedPipeline       | integrated_pipeline.py       | Orchestration                        | All above             |
| ExplanationService       | explanation_service.py       | Transparency                         | CalculationEngine     |

### Django Models Übersicht

| Model                    | App          | Kategorie            | Beschreibung                           |
|--------------------------|--------------|----------------------|----------------------------------------|
| Document                 | documents    | Core                 | Hochgeladene Dokumente                 |
| MaterialList             | documents    | TIER 1               | Holzarten & Faktoren                   |
| ComplexityFactor         | documents    | TIER 1               | Verarbeitungs-Komplexität              |
| SurfaceFinish            | documents    | TIER 1               | Oberflächen-Behandlungen               |
| CompanyMetrics           | documents    | TIER 2               | Betriebskennzahlen                     |
| PricingRule              | documents    | TIER 3               | Dynamische Preis-Regeln                |
| CalculationExplanation   | documents    | Transparency         | Preis-Erklärungen                      |
| UserProjectBenchmark     | documents    | Transparency         | Preis-Vergleiche                       |
| ExtractionResult         | extraction   | ML Output            | OCR/NER Ergebnisse                     |
| ExtractionPattern        | extraction   | Self-Learning        | Fehler-Muster                          |
| KnowledgeFix             | extraction   | Self-Learning        | Lösungsvorschläge                      |
| FixDeployment            | extraction   | Self-Learning        | Deploy-Status                          |

---

## 🎯 Feature-Status

```
✅ = Production-ready
🟡 = In Development
⏳ = Planned

Feature                              Status  Test Coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OCR-Extraktion                       ✅      95%
NER-Extraktion                       ✅      92%
GAEB XML Parser                      ✅      88%
Agentic RAG (Gemini)                 ✅      87%
8-Stufen Calculation Engine          ✅      100%
Pattern-Analyse                      ✅      89%
Knowledge Building                   ✅      85%
Calculation Explanations             ✅      90%
User Benchmarks                      ✅      88%
REST API                             🟡      -
Admin Dashboard UI                   🟡      -
Mobile App                           ⏳      -
```

---

**Nächste Schritte:** Siehe `USER_FLOWS.md` für Nutzer-Perspektive und `ARCHITECTURE_LOGIC.md` für technische Details.
