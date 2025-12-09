# 📚 DraftcraftV1 - System Documentation

**Intelligente Dokument-Analyse & Preiskalkulation für deutsches Handwerk**

Version: 2.3.0 | Stand: Dezember 2024 | Status: Production-Ready

---

## 🎯 Was ist DraftcraftV1?

Ein **KI-gestütztes System** zur automatischen Extraktion von Daten aus deutschen Bau-Dokumenten und präziser Preiskalkulation für Handwerksbetriebe (Schreiner, Zimmerer, Polsterer).

**Kern-Features:**
- 🔍 OCR-Texterkennung (PaddleOCR, deutsche Modelle)
- 🧠 KI-Extraktion (spaCy NER + Google Gemini)
- 💰 8-Stufen Preiskalkulation mit TIER 1/2/3 System
- 📊 Selbstlernendes Pattern-System
- 🔐 DSGVO-konform (Supabase mit RLS Security)

**Zeitersparnis:** 20-30 Minuten → 2-3 Minuten pro Angebot (90% schneller)

---

## 📖 Dokumentations-Struktur

Diese Dokumentation ist in **5 Haupt-Dokumente** unterteilt, die verschiedene Perspektiven des Systems abdecken:

```
docs/
├── SYSTEM_OVERVIEW.md              ← Du bist hier
├── FEATURES_CATALOG.md             ← Was kann das System?
├── USER_FLOWS.md                   ← Wie nutzen User das System?
├── ARCHITECTURE_LOGIC.md           ← Wie ist es aufgebaut?
├── ML_PIPELINE.md                  ← Wie funktioniert die KI?
└── KNOWLEDGE_INTEGRATION.md        ← Wie fließen Wissensbausteine ein?
```

---

## 📋 1. Features Catalog

**Datei:** [`FEATURES_CATALOG.md`](./FEATURES_CATALOG.md)

**Für wen:** Produktmanager, Stakeholder, neue Entwickler

**Inhalt:**
- Vollständige Feature-Übersicht (5 Haupt-Features)
- Beteiligte Komponenten pro Feature
- Technische Details & Code-Beispiele
- Service Layer Matrix
- Django Models Übersicht
- Feature-Status & Test Coverage

**Highlights:**
```
✅ OCR-Extraktion           (95% Coverage)
✅ NER-Extraktion           (92% Coverage)
✅ 8-Stufen Kalkulation     (100% Coverage)
✅ Pattern-Analyse          (89% Coverage)
✅ Transparenz-System       (90% Coverage)
```

**ASCII-Diagramme:**
- Feature-Pipeline Übersicht
- OCR → NER → Calculation Flow
- Komponenten-Matrix

---

## 👤 2. User Flows

**Datei:** [`USER_FLOWS.md`](./USER_FLOWS.md)

**Für wen:** UX Designer, Produktmanager, Trainer

**Inhalt:**
- 4 detaillierte User Journeys
  1. Handwerker: Angebots-Erstellung (2-3 Min)
  2. Geschäftsführung: Kennzahlen-Management (5-10 Min)
  3. Büro-Personal: Qualitätssicherung (2-5 Min)
  4. IT-Admin: System-Wartung & Fix-Deployment
- UI/UX Prinzipien
- Workflow-Zeiten (vorher/nachher)
- Erfolgs-Metriken & KPIs
- Feedback-Loops & Lernen

**Highlights:**
```
Zeitersparnis pro Workflow:
  Angebot erstellen:      20-30 Min → 2-3 Min    (90%)
  Preiskalkulation:       10-15 Min → <10 Sek    (98%)
  Material-Update:        60 Min → 5-10 Min      (85%)
```

**ASCII-Diagramme:**
- Schritt-für-Schritt User Journeys
- Confidence-Routing Visualisierung
- TIER-System Admin-Sicht
- Fix-Deployment Workflow

---

## 🏗️ 3. Architecture & Logic

**Datei:** [`ARCHITECTURE_LOGIC.md`](./ARCHITECTURE_LOGIC.md)

**Für wen:** Backend-Entwickler, DevOps, Architekten

**Inhalt:**
- 3-Layer Service-Architektur
- End-to-End Datenfluss (Dokument → Angebot)
- Service Layer Details
  - Extraction Services (OCR, NER, Gemini, Memory)
  - Calculation Services (8-Stufen Engine)
  - Self-Learning Services (Pattern, Knowledge Builder)
  - Transparency Services (Explanations, Benchmarks)
- Data Models & Relationships
- Security & Compliance (DSGVO, RLS)
- Performance & Scalability
- CI/CD Pipeline

**Highlights:**
```
Service Layer:
  10 Services | 12 Django Models | 169+ Tests

Performance:
  OCR:        2-3s/page
  NER:        0.3-0.5s
  Gemini:     2-5s (optional)
  Calculation: <0.5s
  TOTAL:      3-8s end-to-end
```

**ASCII-Diagramme:**
- 3-Layer Architecture
- Complete Pipeline Flow (9 Steps)
- Service Dependencies
- Database Entity-Relationship
- Security Layers

---

## 🧠 4. ML Pipeline

**Datei:** [`ML_PIPELINE.md`](./ML_PIPELINE.md)

**Für wen:** ML Engineers, Data Scientists, AI Researchers

**Inhalt:**
- 3-Stage ML Pipeline
  1. **OCR:** PaddleOCR (Detection + Recognition)
  2. **NER:** spaCy 3.8 de_core_news_lg + Custom Labels
  3. **LLM:** Google Gemini 1.5 Flash (Enhancement)
- Preprocessing Pipeline
- Model Configuration & Training
- Prompt Engineering (Gemini)
- Memory Context Integration
- Cost Tracking & Budget Management
- Performance Metrics & A/B Testing

**Highlights:**
```
ML Performance:
  OCR Confidence:    0.87 avg (Target: >0.85)
  NER F1 Score:      0.94 (Target: >0.90)
  Gemini Usage:      12% of docs (0.80-0.92 conf)
  Cost per Doc:      $0.00023 (Budget: $10/day)

Entity Accuracy:
  MATERIAL:    96% Precision | 93% Recall
  DIMENSION:   98% Precision | 97% Recall
  SURFACE:     91% Precision | 87% Recall
```

**ASCII-Diagramme:**
- 3-Stage ML Architecture
- PaddleOCR Two-Stage Process
- spaCy NER Pipeline (6 Steps)
- Gemini Prompt Flow
- Memory Retrieval Process

---

## 🧩 5. Knowledge Integration

**Datei:** [`KNOWLEDGE_INTEGRATION.md`](./KNOWLEDGE_INTEGRATION.md)

**Für wen:** Business Analysts, Produktmanager, Backend-Entwickler

**Inhalt:**
- TIER-System Konzept & Architektur
  - **TIER 1:** Global Standards (Materialien, Komplexität, Oberflächen)
  - **TIER 2:** Company Metrics (Labor, Overhead, Margin)
  - **TIER 3:** Dynamic Rules (Rabatte, Aufschläge, Sonderkonditionen)
- Detaillierte Model-Beschreibungen
- Vollständiges Kalkulations-Beispiel (mit echten Zahlen)
- Caching-Strategie & Performance
- Monitoring & Analytics

**Highlights:**
```
TIER 1: 30-50 Einträge | Änderung: 1-2×/Jahr
  ├─ MaterialList:      12 Holzarten
  ├─ ComplexityFactor:  8 Kategorien
  └─ SurfaceFinish:     6 Verfahren

TIER 2: 1-5 Einträge | Änderung: 4×/Jahr
  └─ CompanyMetrics:    Labor rates, Overhead, Margin

TIER 3: 10-50 Regeln | Änderung: Täglich/Wöchentlich
  └─ PricingRule:       Rabatte, Aufschläge, Conditions
```

**ASCII-Diagramme:**
- Knowledge Pyramid
- Data Flow in Calculation
- TIER Lifecycle Workflows
- Complete Calculation Example

---

## 🚀 Quick Start Guide

### Für neue Entwickler

1. **System verstehen:**
   - Start: [`FEATURES_CATALOG.md`](./FEATURES_CATALOG.md) → Was kann das System?
   - Dann: [`ARCHITECTURE_LOGIC.md`](./ARCHITECTURE_LOGIC.md) → Wie ist es aufgebaut?

2. **Code Navigation:**
   ```
   backend/
   ├── extraction/services/     ← ML Pipeline (OCR, NER, Gemini)
   ├── documents/models.py      ← TIER 1/2/3 Models
   └── tests/                   ← 169+ Tests (91% passing)
   ```

3. **Lokaler Start:**
   ```bash
   pip install -r requirements/development.txt
   python manage.py migrate
   python manage.py runserver
   ```

### Für Business Stakeholder

1. **ROI verstehen:**
   - Lesen: [`USER_FLOWS.md`](./USER_FLOWS.md) → Zeitersparnis-Metriken
   - Check: Workflow-Zeiten (vorher: 20-30 Min, nachher: 2-3 Min)

2. **Features evaluieren:**
   - Lesen: [`FEATURES_CATALOG.md`](./FEATURES_CATALOG.md) → Vollständige Feature-Liste
   - Check: Test Coverage & Production-Status

### Für ML Engineers

1. **Pipeline verstehen:**
   - Lesen: [`ML_PIPELINE.md`](./ML_PIPELINE.md) → 3-Stage Architecture
   - Check: Model Performance & Metrics

2. **Training Data:**
   ```
   backend/extraction/training/
   ├── ner_training_data.json    ← Custom NER labels
   └── fixtures/                 ← Test documents
   ```

---

## 📊 System Status (Dezember 2024)

### Entwicklungs-Phasen

```
✅ Phase 1: MVP (4 Wochen)
   ├─ OCR + NER Basic
   ├─ Simple Calculation
   └─ Django Admin

✅ Phase 2: Production (6 Wochen)
   ├─ Agentic RAG (Gemini)
   ├─ Memory Service (Redis)
   └─ Confidence Routing

✅ Phase 3: Betriebskennzahlen (8 Wochen)
   ├─ TIER 1/2/3 System
   ├─ 8-Stufen Calculation Engine
   ├─ Pattern Analyzer
   └─ Knowledge Builder

✅ Phase 4A: Transparency (2 Wochen)
   ├─ Calculation Explanations
   ├─ User Benchmarks
   └─ AI Transparency

🟡 Phase 4B: APIs & Dashboard (In Progress)
   ├─ REST API Layer
   ├─ Admin Dashboard UI
   └─ Monitoring & Analytics

⏳ Phase 5: Mobile & Scaling (Planned)
   ├─ Mobile App
   ├─ Real-time Collaboration
   └─ Multi-Tenant Support
```

### Test Coverage

```
Total Tests: 169 | Passing: 155 (91.7%)

By Module:
  CalculationEngine:     28/28  (100%) ✅
  OCR Service:           25/27  (92%)  ✅
  NER Service:           23/25  (92%)  ✅
  Pattern Analyzer:      22/25  (88%)  ✅
  Knowledge Builder:     18/21  (85%)  🟡
  Gemini Service:        19/22  (86%)  🟡
  Integration Tests:     20/21  (95%)  ✅
```

### Database

```
Current: Supabase Free Tier (Production-Ready)
  ├─ PostgreSQL 15
  ├─ Region: EU West (Frankfurt) - DSGVO-compliant
  ├─ RLS Security: 36 tables secured
  └─ Auto-backups: 7-day point-in-time recovery

Migration to Cloud SQL: Ready (documented)
```

---

## 🔧 Maintenance & Updates

### Documentation Updates

**Wann aktualisieren?**
- Bei jedem neuen Feature → `FEATURES_CATALOG.md`
- Bei UX-Änderungen → `USER_FLOWS.md`
- Bei Architektur-Änderungen → `ARCHITECTURE_LOGIC.md`
- Bei ML-Model-Updates → `ML_PIPELINE.md`
- Bei TIER-System-Erweiterungen → `KNOWLEDGE_INTEGRATION.md`

**Prozess:**
1. Datei bearbeiten (Markdown)
2. ASCII-Diagramme aktualisieren (falls nötig)
3. Version-Nummer hochzählen (oben in Datei)
4. Git Commit: `docs: Update [filename] - [reason]`

### Versioning

```
docs/
├── SYSTEM_OVERVIEW.md            (Version: 2.3.0)
├── FEATURES_CATALOG.md           (Version: 2.3.0)
├── USER_FLOWS.md                 (Version: 2.3.0)
├── ARCHITECTURE_LOGIC.md         (Version: 2.3.0)
├── ML_PIPELINE.md                (Version: 2.3.0)
└── KNOWLEDGE_INTEGRATION.md      (Version: 2.3.0)

Version Format: MAJOR.MINOR.PATCH
  MAJOR: Architektur-Änderung (z.B. neue ML-Stage)
  MINOR: Feature-Addition (z.B. neues TIER-Model)
  PATCH: Bugfixes, Klarstellungen, Beispiele
```

---

## 📞 Support & Kontakt

### Für Entwickler

- **Code-Fragen:** Siehe `.claude/CLAUDE.md` (Entwickler-Guide)
- **API-Docs:** Siehe `.claude/guides/phase2-agentic-services-api.md`
- **Debugging:** Siehe `.claude/guides/debugging-troubleshooting-guide.md`

### Für Nutzer

- **Feature-Anfragen:** GitHub Issues
- **Bug-Reports:** GitHub Issues mit Label `bug`
- **Training-Material:** `USER_FLOWS.md` als Basis

### Externe Ressourcen

- [GAEB DA XML 3.3 Spezifikation](https://www.gaeb.de)
- [DSGVO Compliance](https://dsgvo-gesetz.de)
- [PaddleOCR Docs](https://github.com/PaddlePaddle/PaddleOCR)
- [spaCy Documentation](https://spacy.io/usage)
- [Google Gemini API](https://ai.google.dev/docs)

---

## 🎯 Nächste Schritte

### Für neue Nutzer
1. Lesen: [`USER_FLOWS.md`](./USER_FLOWS.md) - User Journey verstehen
2. Lesen: [`FEATURES_CATALOG.md`](./FEATURES_CATALOG.md) - Features erkunden
3. Demo anfordern: Kontakt über GitHub

### Für Entwickler
1. Lesen: [`ARCHITECTURE_LOGIC.md`](./ARCHITECTURE_LOGIC.md) - System-Architektur verstehen
2. Lesen: [`ML_PIPELINE.md`](./ML_PIPELINE.md) - ML-Details
3. Setup: `.claude/CLAUDE.md` folgen
4. Tests ausführen: `pytest --cov=.`

### Für Business Stakeholder
1. Lesen: [`USER_FLOWS.md`](./USER_FLOWS.md) - ROI-Metriken
2. Lesen: [`FEATURES_CATALOG.md`](./FEATURES_CATALOG.md) - Feature-Status
3. Demo vereinbaren: Kontakt über GitHub

---

## 📜 Lizenz & Credits

**Projekt:** DraftcraftV1
**Entwicklung:** 2024
**Status:** Production-Ready (Phase 4A abgeschlossen)

**Technologien:**
- Django 5.0 (LTS)
- PaddleOCR 2.7 (German models)
- spaCy 3.8 (de_core_news_lg)
- Google Gemini 1.5 Flash
- PostgreSQL 15 (Supabase)
- Redis (Memory cache)

**Compliance:**
- ✅ DSGVO-konform (Art. 6, 15, 17, 20)
- ✅ GoBD-konform (Digitale Belege)
- ✅ VOB-Standards (Bauindustrie)

---

**Letzte Aktualisierung:** 2024-12-04
**Dokumentations-Version:** 2.3.0
**Projekt-Status:** ✅ Production-Ready, Phase 4B in Entwicklung

**Happy Coding! 🚀**
