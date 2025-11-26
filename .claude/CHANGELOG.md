# Changelog - German Handwerk Document Analysis System

Alle wesentlichen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

---

## [Unreleased]

### In Entwicklung
- Enterprise Security Features
- Performance Optimization
- Comprehensive Monitoring

---

## [1.0.0] - 2025-11-20

### Phase 1 MVP - Abgeschlossen ✅

#### Added
- **OCR Service** (`extraction/services/ocr_service.py`)
  - PaddleOCR Integration mit deutschen Modellen
  - Multi-page PDF Support
  - Confidence Scoring
  - Performance: <2s pro A4-Seite
  
- **NER Service** (`extraction/services/ner_service.py`)
  - spaCy de_core_news_lg Integration
  - Custom German Handwerk Entities (HOLZART, MATERIAL, MENGE, PREIS)
  - Pattern-based Extraction für deutsche Formate
  - Confidence Scoring pro Entity-Type
  
- **Django Models** (`documents/models.py`)
  - Document Model mit DSGVO-Feldern
  - ExtractionResult Model mit JSONField
  - AuditLog Model für Compliance
  - Automatic retention policies
  
- **REST API** (`api/v1/`)
  - Document Upload Endpoint
  - List/Detail Endpoints mit Filtering
  - Status Tracking Endpoint
  - DSGVO-konforme Löschung
  - OpenAPI Documentation (Swagger/Redoc)
  
- **Django Admin Interface**
  - Custom DocumentAdmin mit Bulk Actions
  - ExtractionResultAdmin mit JSON-Visualization
  - German Localization
  - CSV Export Functionality

#### Testing
- Unit Tests für alle Services (Coverage: 82%)
- Integration Tests für API Endpoints
- Fixtures für deutsche Test-Daten
- Mock-Integration für PaddleOCR

#### Infrastructure
- Django 5.0 Project Setup
- PostgreSQL 15 Database
- Split Settings (development/production)
- Docker Configuration
- GitHub Actions CI/CD

#### Performance Metrics
- OCR: 1.8s durchschnittlich pro Seite
- NER: 180ms für 1000 Wörter
- API Response: 420ms durchschnittlich
- Success Rate: 94%

---

## [0.5.0] - 2025-11-15

### Phase 2 Preparation - Cloud Tasks Integration

#### Added
- **Cloud Tasks Service** (`core/services/task_service.py`)
  - Async document processing
  - Retry logic mit exponential backoff
  - Dead letter queue für permanent failures
  - DSGVO-konforme Task-Metadaten

- **Task Handler** (`api/internal_views.py`)
  - DocumentProcessingTaskView für Cloud Tasks
  - Service Account Authentication
  - Error Handling und Logging

#### Changed
- Document Upload Flow: Synchron → Asynchron
- Processing Status Tracking erweitert
- API Responses mit estimated completion time

#### Infrastructure
- Cloud Tasks Queues konfiguriert (europe-west3)
- Service Accounts für Task Processing
- IAM Permissions aktualisiert

#### Performance Impact
- Response Time: 30s → <100ms (Upload)
- Throughput: 1 → 10-20 Dokumente/Minute
- Resource Efficiency: 60% Reduktion bei Idle-Zeit

---

## [0.4.0] - 2025-11-10

### GAEB XML Integration

#### Added
- **GAEB Service** (`extraction/services/gaeb_service.py`)
  - GAEB DA XML 3.3 Parser
  - VOB-konforme Strukturen
  - Deutsche Mengeneinheiten
  - Preiskalkulation mit MwSt
  
- **GAEB Models** (Enhanced `documents/models.py`)
  - document_type field mit GAEB_XML choice
  - GAEB-specific fields in ExtractionResult
  - project_name, lv_number, position_count

#### Testing
- GAEB Parser Unit Tests
- Sample GAEB XML Test Files
- Edge Cases für malformed XML

#### Performance
- Parsing: <5s für Standard-LV (100 Positionen)
- Memory: <256MB für große LVs
- Namespace Auto-Detection (3.1, 3.2, 3.3)

#### Documentation
- GAEB Integration Guide
- Sample Files für Testing
- API Documentation Update

---

## [0.3.0] - 2025-11-05

### Enhanced Security & DSGVO Compliance

#### Added
- **Encryption Service** (`core/security/encryption_service.py`)
  - AES-256 Encryption
  - Key Management via Secret Manager
  - Pseudonymization für User-IDs

- **DSGVO Service** (`core/services/dsgvo_service.py`)
  - Right to Erasure (Art. 17)
  - Right to Data Portability (Art. 20)
  - Consent Management
  - Breach Notification Logging

- **Enhanced Audit Logging** (`core/models.py`)
  - Legal Basis Tracking
  - DSGVO Article References
  - Comprehensive Action Logging

#### Changed
- All models erweitert mit encryption support
- API Endpoints mit DSGVO operations
- Admin Interface mit compliance features

#### Security
- Secret Manager Integration
- Master Key Rotation Support
- Encrypted Field Support

---

## [0.2.0] - 2025-11-01

### Repository Structure & Development Workflow

#### Added
- **Archive System**
  - `archive/` Verzeichnis-Struktur
  - Monatliche Archivierungs-Ordner
  - CHANGES.md Templates
  - Automatische Archivierung via GitHub Actions

- **Development Documentation**
  - CLAUDE.md Main Guide
  - Phase-Guides in `.claude/phase-guides/`
  - Deployment Guide
  - CHANGELOG.md (dieses Dokument)

- **Code Quality Tools**
  - Black Formatter Integration
  - mypy Type Checking
  - vulture für Unused Code Detection
  - Pre-commit Hooks

#### Changed
- Reorganized Project Structure
- Enhanced Testing Framework
- Improved CI/CD Pipeline

#### Infrastructure
- GitHub Actions für Cleanup
- Automated Code Quality Checks
- Monthly Archive Scheduling

---

## [0.1.0] - 2025-10-25

### Initial Project Setup

#### Added
- Django 5.0 Project Initialization
- Basic Models (Document, ExtractionResult)
- PostgreSQL Database Configuration
- Basic OCR Integration (proof of concept)
- Development Environment Setup

#### Infrastructure
- Docker Setup
- Docker Compose Configuration
- Requirements Split (base/dev/prod)
- Basic CI/CD Pipeline

#### Documentation
- README.md
- Basic setup instructions
- Initial architecture documentation

---

## Änderungs-Kategorien

### Typen von Änderungen

- **Added** - Neue Features
- **Changed** - Änderungen an bestehenden Features
- **Deprecated** - Features die bald entfernt werden
- **Removed** - Entfernte Features
- **Fixed** - Bug Fixes
- **Security** - Sicherheits-relevante Änderungen
- **Performance** - Performance-Verbesserungen
- **Infrastructure** - Infrastruktur & DevOps
- **Documentation** - Dokumentations-Änderungen

### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: Neues Feature
- `fix`: Bug Fix
- `docs`: Dokumentation
- `style`: Code-Formatierung
- `refactor`: Code-Umstrukturierung
- `perf`: Performance-Verbesserung
- `test`: Tests hinzufügen/ändern
- `chore`: Build/Tool-Änderungen
- `archive`: Archivierung

**Beispiel:**
```
feat(gaeb): Add GAEB XML 3.3 parser

- Implemented GermanGAEBService with VOB compliance
- Added unit tests with sample GAEB files
- Performance: <5s for standard LV processing
- Memory efficient for large LVs (100+ positions)

Closes #42
See docs/gaeb-integration.md for details
```

---

## Review-Prozess

### Vor jedem Release

- [ ] Alle Tests passing (Unit, Integration, E2E)
- [ ] Code Coverage ≥ 80%
- [ ] Performance Benchmarks erfüllt
- [ ] DSGVO Compliance Review
- [ ] Security Scan durchgeführt
- [ ] Dokumentation aktualisiert
- [ ] CHANGELOG.md aktualisiert
- [ ] Version-Nummer erhöht (semver)

### Monatliches Review

- [ ] Archivierung alter/ungenutzter Files
- [ ] CHANGES.md für Archiv erstellt
- [ ] Dependencies aktualisiert
- [ ] Security Updates geprüft
- [ ] Performance Metrics analysiert
- [ ] Cost Optimization Review

---

## Kontakt & Support

**Maintainer:** Dustin (German Handwerk System)  
**Repository:** [GitHub Repository Link]  
**Documentation:** `.claude/` Verzeichnis  

**Für Fragen oder Issues:**
- Erstelle ein GitHub Issue
- Kontaktiere das Development Team
- Siehe CLAUDE.md für Development Guidelines

---

**Letzte Aktualisierung:** 2025-11-20  
**Nächster Review:** Bei Phase 2 Abschluss (Woche 10)
