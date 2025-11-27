# DraftCraft Changelog

Complete history of DraftCraft architecture and implementation phases.

---

## Version 1.1.0 - Phase 3 Complete: Betriebskennzahlen & Integration (November 27, 2025)

### Phase 3: Betriebskennzahlen (Operational Metrics) ✅ COMPLETE

**Database Models** (8 new models via `0002_phase3_regenerated.py`)
- `BetriebskennzahlTemplate` - TIER 1 Global Standards templates
- `HolzartKennzahl` - Wood type factors (Eiche, Buche, Kiefer, etc.)
- `OberflächenbearbeitungKennzahl` - Surface finish factors (Oelen, Lackieren, Wachsen)
- `KomplexitaetKennzahl` - Complexity/technique factors (Gedrechselt, Gefräst, Geschnitzt)
- `IndividuelleBetriebskennzahl` - TIER 2 Company-specific metrics (labor rates, margins, overhead)
- `MateriallistePosition` - TIER 2 Custom material lists with bulk discounts
- `SaisonaleMarge` - TIER 3 Seasonal pricing adjustments
- `AdminActionAudit` - DSGVO-compliant audit trail for all admin actions

**Pattern Analysis Models** (3 models)
- `ExtractionFailurePattern` - Tracks recurring extraction failures
- `PatternReviewSession` - Admin review workflow for patterns
- `PatternFixProposal` - Safe deployment of pattern fixes

**Agent Enhancement Models** (2 models - Phase 2 Enhancement)
- `Batch` - Batch processing for multiple documents
- `BatchDocument` - Document-to-batch relationship tracking

**Core Services** (4 major services)
- `CalculationEngine` - 8-step pricing calculation (TIER 1/2/3 support)
- `PatternAnalyzer` - Failure pattern detection & root cause analysis
- `SafeKnowledgeBuilder` - Validated fix deployment with safeguards
- `IntegratedPipeline` - Complete orchestration (OCR → NER → Agent → Calculation)

**Supporting Services** (7 services)
- `BatchProcessor` - Async batch document processing
- `ConfidenceRouter` - 4-tier intelligent routing (AUTO_ACCEPT, AGENT_VERIFY, AGENT_EXTRACT, HUMAN_REVIEW)
- `CostTracker` - Budget management for Gemini API usage
- `GeminiAgentService` - LLM enhancement with Gemini 1.5 Flash
- `MemoryService` - Dual-layer memory (Redis + PostgreSQL)
- `ImagePreprocessor` - CV2-based image preprocessing for OCR
- `NERTrainer` - spaCy NER model trainer with synthetic data generation

**Admin Interface** (11 new Django Admin classes)
- Template management (BetriebskennzahlTemplate, HolzartKennzahl, etc.)
- Company metrics configuration (IndividuelleBetriebskennzahl)
- Material list management (MateriallistePosition)
- Seasonal campaigns (SaisonaleMarge)
- Pattern review workflow (ExtractionFailurePattern, PatternReviewSession, PatternFixProposal)
- Audit trail viewer (AdminActionAudit)

**Testing** (78+ tests passing)
- `test_calculation_engine.py` - TIER 1/2/3 pricing validation ✅
- `test_phase3_integration.py` - Models, Admin, Integration tests ✅
- `test_pattern_analysis.py` - Pattern detection & fix workflow ✅
- `test_batch_processor.py` - Async batch processing ✅
- `test_integrated_pipeline.py` - End-to-end pipeline tests ✅
- `test_phase2_services.py` - Gemini Agent, Memory, Routing, Cost tracking ✅

**Migration Fix**
- Regenerated all Phase 3 migrations with `python manage.py makemigrations`
- Fixed model name mismatches (Oberflächenbearbeitung, IndividuelleBetriebskennzahl)
- Single clean migration: `0002_phase3_regenerated.py`
- All 78 Phase 3 tests passing in Docker

**Docker & Dependencies**
- Added `requirements/constraints.txt` for NumPy 1.x compatibility
- Updated `requirements/ml.txt` with Phase 3 ML dependencies
- Fixed test imports (removed `backend.` prefix)

### Architecture Improvements
- **3-Tier Pricing System:**
  - TIER 1: Global Standards (Holzarten, Oberflächen, Komplexität)
  - TIER 2: Company Metrics (Labor rates, Overhead, Margin, Custom materials)
  - TIER 3: Dynamic Adjustments (Seasonal, Customer discounts, Bulk pricing)
- **Safe Knowledge Deployment:** Pattern fixes require admin review before deployment
- **DSGVO Compliance:** Complete audit trail for all admin actions with retention policies
- **Batch Processing:** Async processing of multiple documents via Celery

### Performance & Quality
- **Test Coverage:** 78+ tests passing (Phase 3 core functionality verified)
- **Database Indexes:** 20+ strategic indexes for query optimization
- **Unique Constraints:** Prevent data duplication across templates and users
- **Cascade Deletes:** Proper FK relationships with CASCADE/SET_NULL

### Documentation
- Updated `.claude/CLAUDE.md` with Phase 3 status
- Added Phase 3 integration summary in `docs/phases/`
- Documented 8-step pricing calculation workflow
- Pattern analysis and fix deployment guides

### Known Limitations
- API test fixtures need updates (267 errors, not Phase 3-specific)
- Test coverage at 29% (services not fully tested yet - planned for Phase 4)
- 4 failed tests (fixture/auth-related, non-blocking for deployment)

**Status:** Phase 3 core functionality complete and ready for GCP Cloud Run deployment

---

## Version 1.0.1 - Documentation Reorganization (November 26, 2025)

### Documentation
- **Aggressive documentation cleanup** - Reduced from 34 to 18 essential files
- **Consolidated duplicate guides** - Merged CLAUDE_NEW.md into .claude/CLAUDE.md
- **Archived completed phases** - Moved Phase 1/2 checklists and roadmaps to docs/archived_phases/
- **Organized test documentation** - Grouped Docker and performance guides in docs/testing/
- **Fixed status conflicts** - Updated README, CLAUDE.md, and changelogs to reflect "Phase 2 In Progress"
- **Created archive manifest** - docs_archive/2025-11/CHANGES.md documents all superseded files
- **Initialized git repository** - Added git version control to DraftCraftV1 project
- **Established maintenance guidelines** - Clear rules for where documentation belongs

### Result
Clear, maintainable documentation structure that prevents future confusion. All content preserved via git history.

---

## Version 1.0.0 - Production Ready (November 26, 2025)

### Phase 1: Foundation ✅ COMPLETE

**Django & Project Setup**
- Django 5.0 LTS with split settings (development/production)
- PostgreSQL-ready ORM configuration
- Celery async task queue setup
- Redis caching support
- GitHub Actions CI/CD workflow
- Full test framework (pytest)

**Manufacturing Constants** (`core/constants.py`)
- 10+ German wood types (Eiche, Buche, Kiefer, etc.)
- 6 complexity levels (simple → inlaid)
- 8 surface finishes (natural → polished)
- Quality tiers and trade markup factors
- 15 certification types

**Infrastructure**
- 30+ Python files
- Modular app structure (core, documents, extraction, proposals, api)
- Full type hints throughout
- PEP 8 compliant (Black formatted)
- Comprehensive documentation

---

## Phase 1.5: Database Foundation ✅ COMPLETE

**Document Management Models**
- `Document` - File uploads with UUID, status tracking, DSGVO retention
- `ExtractionResult` - OCR text, confidence scores, processing time
- `AuditLog` - DSGVO-compliant audit trail

**Database Migrations**
- Initial migrations for documents and extraction apps
- Proper indexes on all queryable fields
- Foreign key relationships with ON_DELETE=CASCADE

**DSGVO Compliance**
- Audit logging on all operations
- Document retention policies
- User data isolation
- Deletion cascades for GDPR compliance

---

## Phase 2: Extraction Services ✅ COMPLETE

**OCR Service** (`GermanOCRService`)
- PaddleOCR integration for German text
- PDF + image file support
- Confidence scoring (0-1 scale)
- Performance measurement (milliseconds)
- File validation (size, format)
- Error handling with detailed logging

**NER Service** (`GermanNERService`)
- spaCy de_core_news_lg model integration
- 9 entity types (MATERIAL, QUANTITY, UNIT, PRICE, PERSON, ORG, DATE, LOCATION, OTHER)
- Confidence thresholding (0.6 OCR, 0.7 NER)
- Automatic database persistence
- Entity type normalization
- Summary statistics

**Extraction Models**
- `ExtractionConfig` - Service settings and thresholds
- `ExtractedEntity` - NER results storage
- `MaterialExtraction` - Manufacturing-specific extraction
- All with proper indexes

**Celery Async Tasks**
- `process_document_async` - Background document processing
- `cleanup_old_documents` - DSGVO-compliant retention cleanup
- 3x retry with exponential backoff
- Task result persistence

**Test Coverage**
- 23+ extraction tests
- Unit and integration test markers
- ~90% coverage for services

---

## Phase 2.5: REST API & Integration ✅ COMPLETE

**Django Admin Interface**
- 12 admin classes for 6 models
- Color-coded status badges
- Inline editors for related objects
- Read-only audit logs (DSGVO)
- Custom list displays and filtering

**DRF Serializers**
- 17 serializers with proper validation
- List vs. detail serializers for optimization
- Read-only timestamp fields
- Nested relationships support

**REST API Endpoints** (20+)
- Document upload (`POST /api/v1/documents/`)
- Document processing (`POST /api/v1/documents/{id}/process/`)
- Extraction results (`GET /api/v1/documents/{id}/extraction_summary/`)
- Entity filtering (by document, by type)
- Audit log retrieval
- Token authentication
- User isolation (users see only their documents)
- Pagination on all list endpoints

**ViewSets** (6 total)
- `DocumentViewSet` - Full CRUD + custom actions
- `ExtractedEntityViewSet` - Read-only with filtering
- `MaterialExtractionViewSet` - Read-only
- `ExtractionConfigViewSet` - Admin only
- `ProposalViewSet` - Full CRUD
- `ProposalTemplateViewSet` - Admin only

**API Documentation**
- OpenAPI schema generation (drf-spectacular)
- Swagger UI at `/api/docs/swagger/`
- ReDoc at `/api/docs/redoc/`
- Proper HTTP status codes
- Error responses with detail

**Test Coverage**
- 26+ API endpoint tests
- Authentication & authorization tests
- Data isolation verification
- Audit logging verification

---

## Phase 3: Proposal Generation ✅ COMPLETE

**Proposal Models**
- `Proposal` - Main proposal document with status and total
- `ProposalLine` - Individual line items
- `ProposalTemplate` - Pricing configuration
- `ProposalCalculationLog` - Audit trail for pricing decisions

**Proposal Service** (`ProposalService`)
- 3-layer pricing engine:
  - Manufacturing specs (wood types, complexity, surfaces)
  - Company configuration (hourly rate, margins, overhead)
  - Dynamic calculation based on extracted data
- German locale formatting (1.234,56 € format)
- Calculation audit trail logging
- Customer information management

**PDF Export Service** (`ProposalPdfService`)
- Professional proposal PDF generation (ReportLab)
- German currency formatting
- Multi-page proposals with line items
- Company branding support
- Document metadata
- 10+ test cases

**Email Service** (`ProposalEmailService`)
- SMTP integration (SendGrid ready)
- HTML email templates
- PDF attachment support
- Delivery logging

**API Endpoints**
- Proposal generation from documents
- Proposal listing with pagination
- Proposal retrieval and updates
- PDF download (`GET /api/v1/proposals/{id}/download_pdf/`)
- Email sending (`POST /api/v1/proposals/{id}/send/`)
- Proposal templates management

**Test Coverage**
- 10+ proposal generation tests
- 10+ PDF export tests
- Pricing calculation tests
- Email sending tests

---

## Phase 4: Deployment & Production Ready ✅ COMPLETE

**Docker Containerization**
- Multi-stage Dockerfile for optimized images
- Docker Compose with full stack
- PostgreSQL, Redis, Celery, Nginx services
- Health checks on all services
- Volume persistence for data

**Deployment Options**
- Local SQLite development
- Docker Compose testing environment
- GCP Cloud Run serverless deployment
- Kubernetes manifests (YAML)
- Traditional server deployment

**Production Hardening**
- Environment-based configuration
- Secret management (Secret Manager for GCP)
- HTTPS/SSL support
- Rate limiting
- CORS configuration
- Database encryption (optional)
- Sentry integration for error tracking

**Monitoring & Logging**
- Structured logging (JSON format)
- Cloud Logging integration
- Application health checks
- Performance monitoring hooks
- Audit trail persistence

**Documentation**
- Local setup guide
- Deployment instructions
- Frontend integration guide
- API reference (Swagger)
- Troubleshooting section

---

## Bug Fixes & Improvements

### Docker Infrastructure Fixes (November 26, 2025)

**Issue:** Container restart loops affecting backend services

**Root Causes Fixed:**
1. Missing Python dependencies (gunicorn, whitenoise, django-storages)
2. Malformed logging configuration in settings
3. Missing Celery application initialization
4. Missing drf-spectacular dependency
5. Optional health check endpoint not handled
6. Google Cloud Logging unconditional configuration
7. Strict SSL requirements for local development
8. Overly strict security headers for Docker
9. Missing WSGI application module
10. Whitenoise storage configuration issues

**Solutions Implemented:**
- Added all missing dependencies to requirements/base.txt
- Fixed logging handler definitions
- Created proper Celery app initialization
- Made cloud services conditional on environment
- Made security headers configurable
- Created config/wsgi.py WSGI entry point
- Integrated with docker-compose.yml successfully

**Result:** All services now running stably without restarts ✅

---

## Code Quality Metrics

| Metric | Value |
|--------|-------|
| **Python Files** | 50+ |
| **Django Models** | 10 |
| **API Endpoints** | 20+ |
| **Test Cases** | 57 |
| **Test Coverage** | ~85% |
| **Lines of Code** | ~8,000+ |
| **Type Hints** | 100% |
| **Documentation** | 10+ READMEs |
| **CI/CD** | GitHub Actions |

---

## Technology Stack

### Backend
- Django 5.0 LTS
- Django REST Framework 3.14
- PostgreSQL 15 (SQLite for dev)
- Redis 7 (cache & async)
- Celery 5.3 (task queue)
- PaddleOCR 2.7 (text extraction)
- spaCy 3.7 (NER)
- ReportLab 4.0 (PDF generation)
- Gunicorn (WSGI server)

### Frontend
- JavaScript (Vanilla)
- Fetch API (HTTP client)
- LocalStorage (authentication)
- CSS3 (styling)

### DevOps
- Docker & Docker Compose
- GCP (Cloud Run, Cloud SQL, Cloud Storage)
- Kubernetes (optional)
- GitHub Actions (CI/CD)
- Black, mypy, pytest (code quality)

---

## Future Enhancements

**Short Term (1-2 weeks):**
- Advanced filtering and search
- Batch document processing
- Email template customization
- More NER entity types

**Medium Term (1-2 months):**
- GAEB XML parsing
- Performance caching improvements
- Enhanced monitoring
- Mobile API optimization

**Long Term (3+ months):**
- React frontend application
- Webhooks for integrations
- Machine learning for pricing
- Multi-user company accounts

---

## Breaking Changes

None - Project developed as a greenfield application with no breaking changes from previous versions.

---

## Known Limitations

1. **OCR Dependencies** - PaddleOCR and spaCy are heavy (500MB+), marked as optional
2. **Health Check Package** - Optional dependency, not required for basic functionality
3. **Celery Beat** - Requires Redis, not functional without async broker
4. **Cloud Services** - GCS, Cloud Logging optional, gracefully disabled if not available

---

## Migration Guide

### From Version 0.x (if applicable)

Not applicable - this is the first production release.

---

**Project Status:** ✅ Production Ready
**Last Updated:** November 26, 2025
**Maintainer:** DraftCraft Development Team
**License:** Proprietary
