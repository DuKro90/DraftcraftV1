# German Handwerk Document Analysis System - Claude Development Guide

**Version:** 2.3.0
**Letzte Aktualisierung:** December 1, 2025
**Projekt-Status:** Phase 4A - Transparency Models ✅ COMPLETED
**Database:** Supabase (Production-ready with RLS Security)

---

## 📋 Projekt-Kontext

### Was ist dieses System?

Django 5.0 Anwendung für die **intelligente Extraktion strukturierter Daten** aus deutschen Bau-Dokumenten. Entwickelt speziell für Handwerksbetriebe (Schreiner, Zimmerer, Polsterer) mit 30-100 Angeboten pro Woche.

**Kern-Funktionen:**
- 🔍 OCR-Texterkennung mit PaddleOCR (deutsche Modelle)
- 🧠 NER-Extraktion mit spaCy (deutsche Handwerks-Terminologie)
- 📄 GAEB XML Parsing für Bauindustrie-Standards
- 🔐 DSGVO-konforme Datenhaltung mit Audit-Logging
- ☁️ Cloud-Native auf Google Cloud Platform (europa-west3)

### Aktuelle Entwicklungsphase

**Phase 1 MVP (4 Wochen) - ✅ ABGESCHLOSSEN**
**Phase 2 Production (6 Wochen) - ✅ ABGESCHLOSSEN**
**Phase 2 Enhancement: Agentic RAG - ✅ ABGESCHLOSSEN**
**Phase 3 - Betriebskennzahlen & Integration (8 Wochen) - ✅ ABGESCHLOSSEN**
**Phase 4A - Transparency Models (2 Wochen) - ✅ ABGESCHLOSSEN**

➡️ **Nächste Phase:** Phase 4B - REST APIs & Admin Dashboard

➡️ Siehe `.claude/guides/` für detaillierte Service-Dokumentation
➡️ Siehe `docs/phases/` für alle Phase-Dokumentationen
➡️ Siehe `docs/completed/` für Supabase RLS Migration

---

## 🛠️ Technologie-Stack

### Backend Core
```python
Django==5.0              # LTS, deutsche Lokalisierung
PostgreSQL==15           # Supabase (Free Tier) / Cloud SQL, DSGVO-konform
PaddleOCR==3.2.0        # Deutsche OCR-Modelle
spaCy==3.8.0            # de_core_news_lg
Django REST Framework    # API Layer
```

### Database Options

**Option 1: Supabase (Current/Development)**
```bash
Region: Europe West (eu-west-1 Frankfurt)  # DSGVO-Compliance
- Free Tier: 500MB Database, 60 Connections
- Auto-backups: 7 days point-in-time recovery
- Connection Pooler: Port 6543 (production)
- Cost: $0/month
```

**Option 2: Google Cloud SQL (Production-ready)**
```bash
Region: europe-west3 (Frankfurt)  # DSGVO-Compliance
- Cloud SQL PostgreSQL 15
- Auto-scaling & High Availability
```

➡️ **Migration Guide:** Siehe `.claude/guides/supabase-migration-guide.md` für vollständige Anleitung

### Cloud Infrastructure (GCP)
```bash
Region: europe-west3 (Frankfurt)  # DSGVO-Compliance
- Cloud Run (Serverless Auto-Scaling)
- Cloud Tasks (Async Processing)
- Cloud Storage (Document Storage)
- Secret Manager (Konfiguration)
```

### Development Tools
```bash
pytest                   # Testing Framework
Black                    # Code Formatting (line-length=88)
mypy                     # Type Checking
vulture                  # Unused Code Detection
```

---

## 🇩🇪 Deutsche Handwerk-Spezifika (Quick Reference)

### Compliance-Anforderungen
- **DSGVO**: Art. 6, 15, 17, 20 (Einwilligung, Auskunft, Löschung, Portabilität)
- **GoBD**: Aufbewahrungspflichten für digitale Belege
- **VOB**: Vergabe- und Vertragsordnung für Bauleistungen

### Wichtigste Datenformate

```python
# Zahlen & Währung: 1.234,56 € (Punkt Tausender, Komma Dezimal)
def parse_german_currency(amount: str) -> Decimal:
    return Decimal(amount.replace('.', '').replace(',', '.'))

# Datum: DD.MM.YYYY
DATE_FORMAT = 'd.m.Y'
TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'

# Mengeneinheiten
DEUTSCHE_EINHEITEN = {
    'm²': 'Quadratmeter',
    'lfm': 'Laufende Meter',
    'Stk': 'Stück',
    'kg': 'Kilogramm',
    'h': 'Stunden (Arbeit)'
}
```

### Handwerks-Terminologie (Basis)

```python
# Wichtigste Holzarten & Faktoren
HOLZARTEN_BASIC = {
    'eiche': 1.3,    # Hartholz, teuer
    'buche': 1.2,    # Hartholz
    'kiefer': 0.9,   # Weichholz
    'fichte': 0.8    # Weichholz, günstig
}

# Komplexität
KOMPLEXITÄTS_FAKTOREN_BASIC = {
    'gefräst': 1.15,
    'gedrechselt': 1.25,
    'geschnitzt': 1.5,
    'hand_geschnitzt': 2.0
}

# Oberflächen
OBERFLÄCHEN_FAKTOREN_BASIC = {
    'naturbelassen': 1.0,
    'geölt': 1.10,
    'lackiert': 1.15,
    'klavierlack': 1.6  # Premium
}
```

**📚 Vollständige Listen:** Siehe `.claude/guides/german-handwerk-reference.md` für:
- Alle Holzarten mit Eigenschaften & Verwendung
- Detaillierte Komplexitäts-Multiplikatoren
- Oberflächenbearbeitungs-Details
- GAEB-Begriffe & VOB-Standards
- NER Entity Labels

---

## 📝 Code-Standards

### Python Style Guide

```python
# PEP 8 mit Black-Kompatibilität (max line length 88)
# Type hints PFLICHT für alle Funktionen

from typing import Dict, List, Optional
from decimal import Decimal

def extract_document(
    file_path: str,
    language: str = 'de'
) -> Dict[str, any]:
    """
    Extrahiert strukturierte Daten aus deutschen Bau-Dokumenten.

    Args:
        file_path: Pfad zur PDF/GAEB-Datei
        language: Sprache für OCR (default: 'de')

    Returns:
        Dict mit extracted_data, confidence_scores, processing_time

    Raises:
        DocumentProcessingError: Bei OCR/NER Fehlern

    Example:
        >>> result = extract_document("rechnung.pdf")
        >>> print(result['confidence_scores'])
    """
    pass
```

### Django Patterns

**✅ VERWENDE:**
- Class-based Views (nicht Function-based)
- Service Layer Pattern für Business Logic
- Comprehensive Docstrings
- Type Hints überall

**❌ VERMEIDE:**
- Business Logic in models.py oder views.py
- Hardcoded Strings (nutze gettext für deutsche Texte)
- Direkte External API Calls in Views (nutze Services)

### Verzeichnis-Struktur

```
handwerk_analyzer/
├── documents/              # Document Models & Views
├── extraction/
│   ├── services/          # ✅ Business Logic HIER
│   │   ├── ocr_service.py
│   │   ├── ner_service.py
│   │   ├── gemini_agent_service.py
│   │   ├── calculation_engine.py
│   │   └── integrated_pipeline.py
│   └── models.py          # ❌ KEINE Business Logic
├── api/                   # REST API Layer
├── core/
│   ├── utils/            # Shared Utilities
│   ├── security/         # Encryption, DSGVO
│   └── monitoring/       # Metrics, Logging
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 🧪 Testing-Anforderungen

### Coverage-Ziele
```bash
# Minimum 80% Code Coverage
pytest --cov=. --cov-report=html --cov-fail-under=80

# Test-Pyramide:
# - 70-80% Unit Tests
# - 15-20% Integration Tests
# - 5-10% E2E Tests
```

### Test-Fixtures für deutsche Daten

```python
# tests/fixtures/german_documents.py

SAMPLE_INVOICE_TEXT = '''
Rechnung Nr.: RE-2024-001
Firma: Schreinerei Müller GmbH
Datum: 15.11.2024
Gesamtbetrag: 2.450,80 €
USt-IdNr.: DE123456789
'''

SAMPLE_GAEB_DATA = {
    'ordnungszahl': '01.001',
    'kurztext': 'Schalung für Fundament',
    'menge': Decimal('25.5'),
    'einheit': 'm²',
    'einheitspreis': Decimal('45.50')
}
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

@patch('extraction.services.PaddleOCR')
def test_ocr_extraction(mock_ocr):
    """Test OCR mit gemocktem PaddleOCR"""
    mock_ocr.return_value.ocr.return_value = [
        [[[0, 0], [100, 30]], ['Rechnung Nr.: RE-2024-001', 0.95]]
    ]

    result = ocr_service.process_pdf("test.pdf")
    assert 'Rechnung Nr.: RE-2024-001' in result.full_text
    assert result.confidence > 0.9
```

---

## 🚀 Häufige Entwicklungsaufgaben (Quick Prompts)

### 1. Neues OCR-Feature

```
Implementiere ein neues OCR-Feature für das German Handwerk System.

Kontext:
- File: extraction/services/ocr_service.py
- Deutsche Anforderungen: Umlaute (ä,ö,ü,ß), Zahlenformate (1.234,56)
- Performance: <2 Sekunden pro A4-Seite

Implementierung:
1. Erweitere GermanHandwerkOCRService um [functionality]
2. Unit Tests mit Mock PaddleOCR
3. Dokumentiere in docstring
4. Update CHANGELOG.md

Code Style: Service Layer Pattern, Type Hints
```

### 2. Django Migration

```
Erstelle eine Django Migration für das German Handwerk System.

Kontext:
- Aktuelle Models: documents/models.py
- DSGVO Compliance: Audit-Felder erforderlich

Deutsche Requirements:
- created_at/updated_at Timestamps
- retention_until für automatische Löschung
- Encryption Support für sensitive Daten

Verwende deutsche Feldnamen wo sinnvoll.
```

### 3. REST API Endpoint

```
Erstelle einen neuen REST API Endpoint.

Kontext:
- File: api/v1/views.py
- Authentication: Token-based

Deutsche API Standards:
- Fehlermeldungen auf Deutsch
- Deutsche Feldnamen in JSON responses
- DSGVO-konform (keine PII in Logs)

Response Format:
{
  "erfolg": true,
  "nachricht": "Dokument erfolgreich verarbeitet",
  "daten": { ... }
}
```

**📚 Weitere Templates:** Siehe alte Version für GAEB Parser & komplexere Prompts

---

## 🔧 Development Commands

### Lokale Entwicklung

```bash
# Virtual Environment Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements/development.txt
python -m spacy download de_core_news_lg

# Database Setup
python manage.py migrate
python manage.py loaddata fixtures/german_test_data.json

# Development Server
python manage.py runserver

# Tests ausführen
pytest --cov=. --cov-report=html
pytest tests/unit/  # Nur Unit Tests
pytest -k "test_german" # Tests mit "german" im Namen
```

### Production Commands (GCP)

```bash
# Deploy zu Cloud Run (europe-west3)
gcloud run deploy handwerk-analyzer \
  --region europe-west3 \
  --allow-unauthenticated \
  --set-env-vars DJANGO_SETTINGS_MODULE=handwerk_analyzer.settings.production

# Database Migration (Cloud SQL)
gcloud sql connect handwerk-db --user=postgres
python manage.py migrate --settings=handwerk_analyzer.settings.production

# Logs anzeigen
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

---

## 🐋 Docker Build & Deployment

### ⚠️ KRITISCHE REGELN für Docker

```
1. NIEMALS Features deaktivieren oder optional machen um Probleme zu umgehen
2. NIEMALS OCR-Funktionalität entfernen - es ist Core-Feature
3. IMMER Root Cause fixen, keine Workarounds
4. VOR Änderungen an funktionierendem Code: User fragen und Trade-offs erklären
5. ALLE 169+ Tests müssen nach Fix weiterhin bestehen
6. Target-Umgebung ist Google Cloud Run (headless, kein GUI)
```

### Docker OpenCV/NumPy Fix (Quick Reference)

**Problem:** OpenCV 4.6.x ist binär inkompatibel mit NumPy 2.x

**Lösung (3 Schritte):**

1. **Constraints File:** `requirements/constraints.txt`
   ```txt
   numpy>=1.21.0,<2.0.0
   ```

2. **ML Requirements:** `requirements/ml.txt`
   ```txt
   opencv-python-headless==4.6.0.66  # WICHTIG: headless für Cloud Run
   paddleocr==2.7.0.3
   # NumPy wird über constraints gesteuert
   ```

3. **Dockerfile:** NumPy ZUERST installieren
   ```dockerfile
   RUN pip install --no-cache-dir "numpy==1.26.4"
   RUN pip install --no-cache-dir "opencv-python-headless==4.6.0.66" --no-deps
   RUN pip install --no-cache-dir -c /app/requirements/constraints.txt -r /app/requirements/ml.txt
   ```

### Docker Build Commands

```bash
# Cleanup & Build
docker-compose down && docker system prune -f
docker-compose build --no-cache web
docker-compose up -d

# Version Check
docker-compose exec web pip list | grep -E "numpy|opencv|paddle"
# Erwartete Ausgabe:
# numpy                    1.26.4
# opencv-python-headless   4.6.0.66
# paddleocr                2.7.0.3

# Test Suite
docker-compose exec web pytest tests/ -v
```

**📚 Detaillierter Guide:** Siehe `.claude/claude code docker build guide.md` für:
- Vollständiges Dockerfile
- Troubleshooting Steps
- Build Validierungs-Checkliste
- Erfolgreiche Build-Ausgabe

---

## 🔍 Debugging & Troubleshooting (Top 3 Probleme)

### 1. OCR schlechte Qualität für deutsche Texte

**Problem:** PaddleOCR erkennt deutsche Umlaute falsch

**Quick Fix:**
```python
from PIL import Image, ImageEnhance

def preprocess_for_german_ocr(image_path: str) -> Image:
    img = Image.open(image_path)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    return img

ocr = PaddleOCR(
    lang='german',
    use_gpu=False,
    enable_mkldnn=True,
    use_dilation=True
)
```

### 2. GAEB XML Encoding-Fehler

**Problem:** Umlaute falsch dargestellt

**Quick Fix:**
```python
import xml.etree.ElementTree as ET

def parse_gaeb_safe(file_path: str) -> ET.Element:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return ET.fromstring(f.read())
    except UnicodeDecodeError:
        # Fallback für alte Windows-1252 GAEB Files
        with open(file_path, 'r', encoding='windows-1252') as f:
            return ET.fromstring(f.read())
```

### 3. Performance-Probleme bei großen PDFs

**Problem:** OCR dauert >10 Sekunden pro Seite

**Quick Fix:**
```python
from concurrent.futures import ThreadPoolExecutor

def process_large_pdf(pdf_path: Path) -> OCRResult:
    images = convert_from_path(
        pdf_path,
        dpi=300,  # Nicht höher
        fmt='jpeg',
        thread_count=2
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(process_page, images))

    return combine_results(results)
```

**📚 Weitere Probleme:** Siehe `.claude/guides/debugging-troubleshooting-guide.md` für:
- Fraktur-Schrift OCR
- Multi-Column Layout
- Database Performance
- Memory Issues
- Redis Connection Problems
- Test Debugging

---

## 💰 Phase 2 & Phase 3 Services (Übersicht)

### Phase 2: Agentic RAG Services

**Implementierte Services:**
1. **GeminiAgentService** - LLM Enhancement mit Gemini 1.5 Flash
2. **MemoryService** - Dual-Layer Memory (Redis + PostgreSQL)
3. **ConfidenceRouter** - 4-Tier Intelligent Routing
4. **CostTracker** - Budget Management

**Routing-Tiers:**
- `AUTO_ACCEPT` (0.92+) → $0 cost
- `AGENT_VERIFY` (0.80-0.92) → ~$0.0001
- `AGENT_EXTRACT` (0.70-0.80) → ~$0.00025
- `HUMAN_REVIEW` (<0.70) → $0 cost

**📚 Complete API:** Siehe `.claude/guides/phase2-agentic-services-api.md` für:
- Vollständige Methodensignaturen
- Code-Beispiele
- Integration Workflows
- Testing

### Phase 3: Betriebskennzahlen System

**Implementierte Services:**
1. **CalculationEngine** - 8-step pricing mit TIER 1/2/3
2. **PatternAnalyzer** - Failure detection & root cause analysis
3. **SafeKnowledgeBuilder** - Validated fix deployment
4. **IntegratedPipeline** - Complete orchestration

**TIER System:**
- **TIER 1:** Global Standards (Holzarten, Oberflächen, Komplexität)
- **TIER 2:** Company Metrics (Labor rates, Overhead, Margin)
- **TIER 3:** Dynamic (Seasonal, Customer discounts)

**📚 Code Examples:** Siehe `.claude/guides/phase3-betriebskennzahlen-examples.md` für:
- Detaillierte Pricing-Szenarien
- Pattern Analysis Workflows
- Safe Deployment Examples
- Complete Integration Patterns

---

## 📦 Repository-Management

### Vor neuer Entwicklung - Cleanup Check

```bash
# 1. Repository-Status
git status && git log --oneline -5

# 2. Test Coverage
pytest --cov=. --cov-report=term-missing --cov-fail-under=80

# 3. Code Quality
black --check . && mypy .
```

### Archivierung (Wann?)

- Code nicht verwendet seit 30+ Tagen
- Experimentelle Features wurden verworfen
- Alte Migration-Files (>6 Monate)
- Veraltete API-Versionen

**Prozess:**
```bash
ARCHIVE_DATE=$(date +%Y-%m)
mkdir -p archive/$ARCHIVE_DATE/{deprecated_code,old_migrations}

git mv old_feature.py archive/$ARCHIVE_DATE/deprecated_code/

# Dokumentiere in archive/$ARCHIVE_DATE/CHANGES.md
git commit -m "archive: Move deprecated files to archive/$ARCHIVE_DATE"
```

---

## 📝 Änderungs-Tracking

**WICHTIG:** Alle Änderungen MÜSSEN dokumentiert werden!

### Bei jeder Änderung:

1. **Während der Entwicklung:** Dokumentiere in `.claude/CHANGELOG.md`
2. **Bei Archivierung:** Erstelle `archive/YYYY-MM/CHANGES.md`
3. **Bei neuen Features:** Update `CLAUDE.md` + CHANGELOG

**Template für CHANGELOG-Einträge:**

```markdown
## [2025-11-27] - Feature: GAEB XML Integration

### Added
- `extraction/services/gaeb_service.py` - GAEB 3.3 Parser
- `tests/fixtures/sample_gaeb.xml` - Test-Daten

### Changed
- `extraction/services/base_service.py` - Extended for GAEB support

### Performance
- GAEB parsing: <5 Sekunden für Standard-LV
- Memory: <256MB für 100-Position LV
```

---

## ⚠️ Wichtige Hinweise

### Vor jedem Commit

```bash
# 1. Code formatieren
black .

# 2. Type checking
mypy .

# 3. Tests ausführen
pytest --cov=. --cov-fail-under=80

# 4. CHANGELOG aktualisieren
# Füge Änderungen zu .claude/CHANGELOG.md hinzu

# 5. Commit mit aussagekräftiger Message
git commit -m "feat(gaeb): Add GAEB XML 3.3 parser

- Implemented GermanGAEBService with VOB compliance
- Added unit tests with sample GAEB files
- Performance: <5s for standard LV processing
- See CHANGELOG.md for details"
```

### NIEMALS committen ohne:

- ❌ Tests für neue Features
- ❌ Docstrings für neue Funktionen
- ❌ CHANGELOG.md Update
- ❌ Type Hints
- ❌ DSGVO-Check für neue Datenfelder

---

## 🔗 Wichtige Ressourcen

### Interne Dokumentation

**Guide-Dateien:**
- `.claude/guides/german-handwerk-reference.md` - Vollständige Terminologie
- `.claude/guides/phase2-agentic-services-api.md` - Phase 2 API Docs
- `.claude/guides/phase3-betriebskennzahlen-examples.md` - Phase 3 Code-Beispiele
- `.claude/guides/debugging-troubleshooting-guide.md` - Advanced Debugging
- `.claude/guides/supabase-migration-guide.md` - Supabase Database Migration (30-45 Min)

**Projekt-Dokumentation:**
- `.claude/CHANGELOG.md` - Alle Projekt-Änderungen
- `.claude/claude code docker build guide.md` - Docker Build Details
- `PHASE3_INTEGRATION_SUMMARY.md` - Phase 3 Architecture
- `PHASE3_TEST_VALIDATION.md` - Test Coverage Report

### Externe Standards
- [GAEB DA XML 3.3 Spezifikation](https://www.gaeb.de)
- [DSGVO Art. 6, 15, 17, 20](https://dsgvo-gesetz.de)
- [VOB/A & VOB/B](https://www.deutsche-vergabe.de)
- [PaddleOCR Docs](https://github.com/PaddlePaddle/PaddleOCR)
- [Django 5.0 Release Notes](https://docs.djangoproject.com/en/5.0/)

---

## 🎯 Nächste Schritte

### Aktueller Task-Status

**Phase 3: Betriebskennzahlen & Integration - ✅ VERIFIED**
- ✅ 8 Models (TIER 1/2/3)
- ✅ 4 Services (CalculationEngine, PatternAnalyzer, SafeKnowledgeBuilder, IntegratedPipeline)
- ✅ 11 Django Admin Classes
- ✅ **Test Results: 97/107 PASSING (91%)**
  - CalculationEngine: 28/28 (100%)
  - Pattern/Knowledge/Pipeline: 69/79 (87%)
- ✅ Complete Integration Documentation

**Phase 4A: Transparency Models - ✅ COMPLETED**
- ✅ 3 Models (CalculationExplanation, CalculationFactor, UserProjectBenchmark)
- ✅ ExplanationService for AI transparency
- ✅ Django Admin integration
- ✅ Unit & Integration tests

**Database & Security - ✅ PRODUCTION-READY**
- ✅ Supabase RLS Security (36 tables secured)
- ✅ All migrations applied and tested
- ✅ Test-compatible RLS migration

**Repository Cleanup - ✅ COMPLETED (2025-12-01)**
- ✅ Organized documentation (docs/phases/, docs/completed/)
- ✅ Updated .gitignore for sensitive files
- ✅ Removed temporary error logs
- ✅ Fixed Phase 3 tests (CalculationEngine 100% pass)

### Nächste Phase: Phase 4B - REST APIs & Admin Dashboard (Planned)

**Prioritäten:**
1. **REST API Layer** - Extraction, Pattern, Knowledge, Pricing, Transparency endpoints
2. **Admin Dashboard UI** - Pattern review, Fix approval, Deployment management
3. **Monitoring & Analytics** - Extraction quality, Pattern frequency, Cost analysis
4. **Frontend Integration** - React/Vue dashboard for Handwerker

---

**Dieses CLAUDE.md ist ein lebendes Dokument. Update es bei jeder größeren Änderung!**

**Letzte Aktualisierung:** 2025-12-01
**Version:** 2.3.0 - Phase 3 VERIFIED + Supabase Production-Ready
**Status:** ✅ Deployment-ready, Phase 3 tested, RLS security enabled
**Nächste Phase:** Phase 4B - REST APIs & Admin Dashboard (Planned)
