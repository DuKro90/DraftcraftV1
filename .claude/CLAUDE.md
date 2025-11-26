# German Handwerk Document Analysis System - Claude Development Guide

**Version:** 1.0.0  
**Letzte Aktualisierung:** November 26, 2025
**Projekt-Status:** Phase 2 In Progress (Backend 100% Complete)  

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
- Synchrone Verarbeitung
- Basis OCR/NER Services
- Django Admin Interface
- REST API Endpoints

**Phase 2 Production (6 Wochen) - ✅ ABGESCHLOSSEN**
- Async Processing mit Cloud Tasks
- Enterprise Security & DSGVO Compliance
- GAEB XML Integration
- Performance Optimization
- Blue-Green Deployment

**Phase 2 Enhancement - 🚧 IN ARBEIT**
- Weitere Features und Optimierungen

➡️ Siehe [docs/archived_phases/](../../docs/archived_phases/) für abgeschlossene Phasen-Dokumentation

---

## 🛠️ Technologie-Stack

### Backend Core
```python
Django==5.0              # LTS, deutsche Lokalisierung
PostgreSQL==15           # Cloud SQL, DSGVO-konform
PaddleOCR==3.2.0        # Deutsche OCR-Modelle
spaCy==3.8.0            # de_core_news_lg
Django REST Framework    # API Layer
```

### Cloud Infrastructure (GCP)
```bash
Region: europe-west3 (Frankfurt)  # DSGVO-Compliance
- Cloud Run (Serverless Auto-Scaling)
- Cloud SQL PostgreSQL 15
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

## 🇩🇪 Deutsche Handwerk-Spezifika

### Compliance-Anforderungen
- **DSGVO**: Art. 6, 15, 17, 20 (Einwilligung, Auskunft, Löschung, Portabilität)
- **GoBD**: Aufbewahrungspflichten für digitale Belege
- **VOB**: Vergabe- und Vertragsordnung für Bauleistungen

### Deutsche Datenformate

#### Zahlen & Währung
```python
# Preise: 1.234,56 € (Punkt Tausender, Komma Dezimal)
def parse_german_currency(amount: str) -> Decimal:
    return Decimal(amount.replace('.', '').replace(',', '.'))

# Beispiel: "1.250,50 €" → Decimal("1250.50")
```

#### Datums-Formate
```python
# DD.MM.YYYY (deutsches Standard-Format)
DATE_FORMAT = 'd.m.Y'
DATETIME_FORMAT = 'd.m.Y H:i'
TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'
```

#### Mengeneinheiten
```python
DEUTSCHE_EINHEITEN = {
    'm²': 'Quadratmeter',
    'lfm': 'Laufende Meter', 
    'Stk': 'Stück',
    'kg': 'Kilogramm',
    'h': 'Stunden (Arbeit)'
}
```

### Holzarten & Handwerks-Terminologie

```python
# extraction/services/ner_service.py - Wichtige Vokabular-Listen

HOLZARTEN = {
    'eiche': {'kategorie': 'hartholz', 'faktor': 1.3},
    'buche': {'kategorie': 'hartholz', 'faktor': 1.2},
    'kiefer': {'kategorie': 'weichholz', 'faktor': 0.9},
    'fichte': {'kategorie': 'weichholz', 'faktor': 0.8}
}

KOMPLEXITÄTS_FAKTOREN = {
    'gedrechselt': 1.25,
    'gefräst': 1.15,
    'geschnitzt': 1.5,
    'handgeschnitzt': 2.0
}

OBERFLÄCHEN_FAKTOREN = {
    'lackiert': 1.15,
    'geölt': 1.10,
    'gewachst': 1.08,
    'naturbelassen': 1.0
}
```

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
│   │   └── gaeb_service.py
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
    
    # Test logic hier
    result = ocr_service.process_pdf("test.pdf")
    assert 'Rechnung Nr.: RE-2024-001' in result.full_text
    assert result.confidence > 0.9
```

---

## 🚀 Häufige Entwicklungsaufgaben

### 1. Neues OCR-Feature implementieren

**Claude Code Prompt Template:**
```
Implementiere ein neues OCR-Feature für das German Handwerk System.

Kontext:
- File: extraction/services/ocr_service.py
- Aktueller Stand: [beschreibe current state]
- Neue Anforderung: [specific requirement]

Deutsche Anforderungen:
- Umlaute (ä,ö,ü,ß) korrekt behandeln
- Deutsche Zahlenformate (1.234,56)
- Performance: <2 Sekunden pro A4-Seite

Implementierung:
1. Erweitere GermanHandwerkOCRService um [functionality]
2. Füge Unit Tests mit Mock PaddleOCR hinzu
3. Dokumentiere neue Parameter in docstring
4. Update CHANGELOG.md mit Änderungen

Code Style: Service Layer Pattern, Type Hints, Comprehensive Docstrings
Testing: pytest mit fixtures aus tests/fixtures/german_documents.py
```

### 2. GAEB XML Parser erweitern

**Claude Code Prompt Template:**
```
Erweitere den GAEB XML Parser für das German Handwerk System.

Kontext:
- File: extraction/services/gaeb_service.py
- Standard: GAEB DA XML 3.3
- Neue Requirements: [specify what to add]

Deutsche Bau-Standards:
- VOB-konforme Leistungsbeschreibungen
- Deutsche Mengeneinheiten (m², lfm, Stk)
- Preisstrukturen (Netto/Brutto, 19% MwSt)

Implementierung:
1. Erweitere GAEBService.parse_gaeb_xml()
2. Füge Validierung für deutsche Standards hinzu
3. Error Handling für malformed XML
4. Unit Tests mit echten GAEB Beispiel-Dateien
5. Deutsche Lokalisierung der Fehlermeldungen

Code Style: Service Layer Pattern, Type Hints
Testing: Nutze tests/fixtures/sample_gaeb.xml
```

### 3. Django Migration erstellen

**Claude Code Prompt Template:**
```
Erstelle eine Django Migration für das German Handwerk System.

Kontext:
- Aktuelle Models: documents/models.py
- Änderung: [describe change needed]
- DSGVO Compliance: Audit-Felder erforderlich

Deutsche Requirements:
- created_at/updated_at Timestamps (DSGVO Audit)
- retention_until Feld für automatische Löschung
- Encryption Support für sensitive Daten

Implementierung:
1. Analysiere aktuelle Model-Struktur
2. Erstelle optimale Migration mit Indexes
3. DSGVO-konforme Felder ergänzen
4. Teste Migration up/down paths
5. Dokumentiere Änderungen in .claude/CHANGELOG.md

Verwende deutsche Feldnamen wo sinnvoll.
```

### 4. REST API Endpoint hinzufügen

**Claude Code Prompt Template:**
```
Erstelle einen neuen REST API Endpoint für das German Handwerk System.

Kontext:
- File: api/v1/views.py
- Neue Funktionalität: [describe endpoint purpose]
- Authentication: Token-based

Deutsche API Standards:
- Fehlermeldungen auf Deutsch
- Deutsche Feldnamen in JSON responses
- DSGVO-konform (keine PII in Logs)

Implementierung:
1. Erstelle Serializer mit deutschen Feldnamen
2. Implementiere View mit Error Handling
3. Füge Rate Limiting hinzu (100 req/hour)
4. API Tests mit deutscher Test-Daten
5. OpenAPI Documentation (Swagger)

Response Format:
{
  "erfolg": true,
  "nachricht": "Dokument erfolgreich verarbeitet",
  "daten": { ... }
}
```

---

## 📦 Repository-Management

### Vor neuer Entwicklung - Cleanup Check

```bash
#!/bin/bash
# Führe diesen Check vor jeder neuen Feature-Entwicklung aus

# 1. Repository-Status prüfen
git status
git log --oneline -5

# 2. Ungenutzte Files identifizieren
vulture . --min-confidence 80 > unused_code_report.txt

# 3. Test Coverage prüfen
pytest --cov=. --cov-report=term-missing --cov-fail-under=80

# 4. Code Quality Check
black --check .
mypy .
```

### Archivierungs-Workflow

**Wann archivieren?**
- Code nicht verwendet seit 30+ Tagen
- Experimentelle Features wurden verworfen
- Alte Migration-Files (>6 Monate)
- Veraltete API-Versionen
- Test-Files für entfernte Features

**Archivierungs-Prozess:**

```bash
# 1. Erstelle Archiv-Ordner für aktuellen Monat
ARCHIVE_DATE=$(date +%Y-%m)
mkdir -p archive/$ARCHIVE_DATE/{deprecated_code,old_migrations,experimental}

# 2. Verschiebe Files mit Git (behält History)
git mv old_feature.py archive/$ARCHIVE_DATE/deprecated_code/
git mv 0001_old_migration.py archive/$ARCHIVE_DATE/old_migrations/

# 3. Dokumentiere Archivierung
cat >> archive/$ARCHIVE_DATE/CHANGES.md << EOF
# Archivierung $(date +%Y-%m-%d)

## Deprecated Code
- \`old_feature.py\`: Ersetzt durch new_feature.py
  - Grund: Performance-Verbesserung mit async processing
  - Dependencies: Keine
  - Migration: Siehe migration_guide.md

## Old Migrations
- \`0001_old_migration.py\`: Superseded durch 0025_consolidated.py
  - Status: Safe to archive (>6 Monate alt)
  - Rollback: Nicht mehr möglich
EOF

# 4. Commit mit klarer Message
git add .
git commit -m "archive: Move deprecated files to archive/$ARCHIVE_DATE

- Moved unused views to deprecated_code/
- Archived old migrations >6 months
- See archive/$ARCHIVE_DATE/CHANGES.md for details"
```

### Automatische Archivierung (GitHub Actions)

Siehe `.github/workflows/cleanup.yml` - Läuft monatlich am 1. um 02:00 Uhr

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

# Django Shell mit erweiterter Ausgabe
python manage.py shell_plus

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

## 🔍 Debugging & Troubleshooting

### Häufige Probleme & Lösungen

#### 1. OCR schlechte Qualität für deutsche Texte

**Problem:** PaddleOCR erkennt deutsche Umlaute falsch

**Lösung:**
```python
# Preprocessing hinzufügen vor OCR
from PIL import Image, ImageEnhance

def preprocess_for_german_ocr(image_path: str) -> Image:
    img = Image.open(image_path)
    
    # Contrast enhancement für deutsche Fraktur-Schrift
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    return img

# OCR mit deutschen Modellen
ocr = PaddleOCR(
    lang='german',  # Explizit deutsche Modelle
    use_gpu=False,
    show_log=False,
    enable_mkldnn=True,  # CPU-Optimierung
    use_dilation=True    # Bessere Erkennung für kleine Texte
)
```

#### 2. GAEB XML Encoding-Fehler

**Problem:** Umlaute werden falsch dargestellt

**Lösung:**
```python
import xml.etree.ElementTree as ET

def parse_gaeb_safe(file_path: str) -> ET.Element:
    """Sicheres Parsen mit Encoding-Fallback"""
    
    # Erst UTF-8 versuchen
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return ET.fromstring(content)
    except UnicodeDecodeError:
        # Fallback für alte Windows-1252 GAEB Files
        with open(file_path, 'r', encoding='windows-1252') as f:
            content = f.read()
        return ET.fromstring(content)
```

#### 3. Performance-Probleme bei großen PDFs

**Problem:** OCR dauert >10 Sekunden pro Seite

**Lösung:**
```python
# Batch Processing mit Progress Tracking
def process_large_pdf(pdf_path: Path) -> OCRResult:
    """Optimierte Verarbeitung für große PDFs"""
    
    images = convert_from_path(
        pdf_path,
        dpi=300,  # Nicht höher für Geschwindigkeit
        fmt='jpeg',
        thread_count=2  # Memory-Optimierung
    )
    
    # Parallel processing für Seiten
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(process_page, images))
    
    return combine_results(results)
```

---

## 📊 Performance-Benchmarks

### Erwartete Performance-Ziele

```python
# Phase 1 MVP
OCR_TIME_PER_PAGE = 2.0    # Sekunden pro A4-Seite
NER_TIME_PER_1000_WORDS = 0.2  # Sekunden
API_RESPONSE_TIME = 0.5    # Sekunden für List-Endpoints
MAX_MEMORY_USAGE = 512     # MB (Cloud Run Limit)

# Phase 2 Production
ASYNC_THROUGHPUT = 10-20   # Dokumente pro Minute
SUCCESS_RATE = 0.95        # 95% erfolgreich verarbeitet
OCR_CONFIDENCE_TARGET = 0.85  # Minimum Confidence Score
```

### Performance Monitoring

```python
# core/monitoring/performance.py

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_performance(threshold_seconds: float = 2.0):
    """Decorator für Performance-Monitoring"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            
            if duration > threshold_seconds:
                logger.warning(
                    f"{func.__name__} took {duration:.2f}s "
                    f"(threshold: {threshold_seconds}s)"
                )
            
            return result
        return wrapper
    return decorator

# Usage
@monitor_performance(threshold_seconds=2.0)
def process_document(doc_id: str) -> Result:
    pass
```

---

## 🔗 Wichtige Ressourcen

### Interne Dokumentation
- `.claude/phase-guides/phase1-mvp.md` - MVP Development Guide
- `.claude/phase-guides/phase2-production.md` - Production Hardening
- `.claude/phase-guides/deployment-guide.md` - GCP Infrastructure
- `.claude/CHANGELOG.md` - Alle Projekt-Änderungen

### Externe Standards
- [GAEB DA XML 3.3 Spezifikation](https://www.gaeb.de)
- [DSGVO Art. 6, 15, 17, 20](https://dsgvo-gesetz.de)
- [VOB/A & VOB/B](https://www.deutsche-vergabe.de)
- [GoBD](https://www.bundesfinanzministerium.de/gobd)

### Python Libraries Dokumentation
- [PaddleOCR Docs](https://github.com/PaddlePaddle/PaddleOCR)
- [spaCy German Models](https://spacy.io/models/de)
- [Django 5.0 Release Notes](https://docs.djangoproject.com/en/5.0/)

---

## 📝 Änderungs-Tracking

**WICHTIG:** Alle Verzeichnis-Änderungen MÜSSEN dokumentiert werden!

### Bei jeder Änderung:

1. **Während der Entwicklung:** Dokumentiere in `.claude/CHANGELOG.md`
2. **Bei Archivierung:** Erstelle `archive/YYYY-MM/CHANGES.md`
3. **Bei neuen Features:** Update `CLAUDE.md` + CHANGELOG

**Template für CHANGELOG-Einträge:**

```markdown
## [2025-11-20] - Feature: GAEB XML Integration

### Added
- `extraction/services/gaeb_service.py` - GAEB 3.3 Parser
- `tests/fixtures/sample_gaeb.xml` - Test-Daten
- GAEB-specific fields in `documents/models.py`

### Changed
- `extraction/services/base_service.py` - Extended for GAEB support
- `api/v1/serializers.py` - Added GAEB response format

### Deprecated
- `extraction/legacy_parser.py` → Moved to `archive/2025-11/deprecated_code/`

### Performance
- GAEB parsing: <5 Sekunden für Standard-LV
- Memory: <256MB für 100-Position LV

### DSGVO Impact
- Keine PII in GAEB-Daten (nur Projekt-Metadaten)
- Standard retention policy applies (365 Tage)
```

---

## 🎯 Nächste Schritte

### Aktueller Task-Status

**Phase 2 Production - Woche 7/10:**
- ✅ Cloud Tasks Async Processing
- ✅ GAEB XML Integration
- 🚧 Enterprise Security & DSGVO
- ⏳ Performance Optimization
- ⏳ Blue-Green Deployment

### Prioritäten für diese Woche

1. **Enterprise Security Implementation**
   - Encryption Service (AES-256)
   - DSGVO Compliance Service
   - Enhanced Audit Logging

2. **Performance Optimization**
   - Caching Strategy
   - Database Tuning
   - Custom Metrics

3. **Monitoring Setup**
   - Sentry Integration
   - Business KPI Dashboard
   - Alerting Policies

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

**Dieses CLAUDE.md ist ein lebendes Dokument. Update es bei jeder größeren Änderung!**

**Letzte Aktualisierung:** 2025-11-26
**Nächster Review:** Während Phase 2 Meilensteine
