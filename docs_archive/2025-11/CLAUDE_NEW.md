# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 📋 Project Overview

**DraftCraft** is a production-ready document processing and proposal generation system for German-speaking craftspeople (Schreiner, Polsterer, etc.). It combines OCR/NER text extraction with intelligent pricing and proposal generation.

### Core Tech Stack
- **Backend:** Django 5.0 LTS + Django REST Framework
- **Database:** PostgreSQL 15 (development: SQLite)
- **OCR/NER:** PaddleOCR + spaCy (de_core_news_lg)
- **Task Queue:** Celery + Redis
- **Deployment:** Docker Compose, GCP Cloud Run
- **Testing:** pytest (85% coverage, 64+ test cases)

### Project Status: ✅ PRODUCTION READY
All 4 phases complete:
- Phase 1 (Foundation) ✅
- Phase 2 (Extraction) ✅
- Phase 3 (Proposals & PDF) ✅
- Phase 4 (Deployment) ✅

---

## 🏗️ Architecture Overview

### Directory Structure
```
DraftcraftV1/
├── backend/                    # Django application
│   ├── config/                # Django settings
│   │   ├── settings/
│   │   │   ├── base.py        # Shared config
│   │   │   ├── development.py # Local (SQLite by default)
│   │   │   └── production.py  # GCP Cloud Run
│   │   ├── celery.py          # Celery configuration
│   │   ├── urls.py            # Root URL routing
│   │   └── wsgi.py            # WSGI entry point
│   ├── core/                  # Constants & utilities
│   │   └── constants.py       # German wood types, pricing factors
│   ├── documents/             # Document management
│   │   ├── models.py          # Document, ExtractionResult, AuditLog
│   │   ├── serializers.py     # REST API serializers
│   │   └── admin.py           # Django admin interface
│   ├── extraction/            # OCR/NER services
│   │   ├── models.py          # ExtractionConfig, ExtractedEntity
│   │   ├── services.py        # GermanOCRService, GermanNERService
│   │   └── admin.py
│   ├── proposals/             # Proposal generation
│   │   ├── models.py          # Proposal, ProposalLine, ProposalTemplate
│   │   ├── services.py        # ProposalService, ProposalEmailService
│   │   ├── pdf_service.py     # ProposalPdfService (reportlab)
│   │   └── admin.py
│   ├── api/v1/                # REST API layer
│   │   ├── views.py           # DocumentViewSet, ProposalViewSet, etc. (6 ViewSets)
│   │   ├── urls.py            # Router registration
│   │   └── serializers.py     # API field mappings
│   ├── tests/                 # Test suite (64+ tests, 85% coverage)
│   │   ├── conftest.py        # pytest fixtures
│   │   ├── test_core_constants.py
│   │   ├── test_extraction_services.py
│   │   ├── test_api_views.py
│   │   ├── test_pdf_service.py
│   │   └── fixtures/
│   ├── requirements/          # Dependency management
│   │   ├── base.txt           # Core (Django, DRF, PDF)
│   │   ├── development.txt    # + testing tools
│   │   ├── production.txt     # GCP-optimized
│   │   └── ml.txt             # + PaddleOCR, spaCy
│   ├── pytest.ini
│   ├── manage.py
│   └── .env / .env.example
├── Dockerfile                 # Multi-stage production build
├── docker-compose.yml         # Full local stack (Postgres, Redis, Celery)
├── nginx.conf                 # Reverse proxy config
├── README.md                  # Project overview
├── DEVELOPER_GUIDE.md         # Development workflows
├── DEPLOYMENT_GUIDE.md        # Deployment instructions
└── FRONTEND_INTEGRATION_GUIDE.md  # API integration examples
```

### Service Layer Pattern

Business logic is isolated in service classes:

```
REST Request
    ↓
ViewSet (api/v1/views.py)
    ↓
Serializer (validates input)
    ↓
Service Layer (extraction/services.py, proposals/services.py)
    ↓
Models (documents/models.py, etc.)
    ↓
Database (PostgreSQL/SQLite)
```

**Key Rule:** Never put business logic in models or views - always use services.

---

## 🚀 Common Development Commands

### Local Setup (Development)

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (choose one)
pip install -r requirements/development.txt      # Recommended for dev
pip install -r requirements/full.txt             # Includes OCR/NER
pip install -r requirements/ml.txt               # ML models only

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver
# Visit: http://localhost:8000/admin/ or http://localhost:8000/api/docs/swagger/
```

### Testing

```bash
# Run all tests (85% coverage target)
pytest --cov=. --cov-fail-under=80 -v

# Run specific test file
pytest tests/test_pdf_service.py -v

# Run by marker
pytest -m unit -v                    # Unit tests only
pytest -m integration -v             # Integration tests only
pytest -m "not slow" -v              # Skip slow tests

# Watch mode (requires pytest-watch)
pytest-watch -- --cov=. -v

# Coverage report (HTML)
pytest --cov=. --cov-report=html
# Open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy . --ignore-missing-imports

# Linting
flake8 .

# Import sorting
isort .

# All checks (before commit)
black . && mypy . --ignore-missing-imports && pytest --cov=. --cov-fail-under=80
```

### Django Migrations

```bash
# After modifying models
python manage.py makemigrations documents

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Revert to specific migration
python manage.py migrate documents 0001
```

### Docker Development

```bash
# Build all services
docker-compose build

# Start all services (includes Django, Postgres, Redis, Celery)
docker-compose up -d

# View logs
docker-compose logs -f web                # Django logs
docker-compose logs -f celery_worker      # Celery worker logs
docker-compose logs -f postgres           # Database logs

# Stop all services
docker-compose down

# Clean up (remove volumes)
docker-compose down -v

# Execute command in container
docker-compose exec web python manage.py migrate
```

### Celery Tasks (Background Jobs)

```bash
# Start Celery worker (inside docker or local)
celery -A config worker -l info

# Start Celery Beat (scheduler)
celery -A config beat -l info

# Monitor tasks
celery -A config events

# Inspect active tasks
celery -A config inspect active
```

---

## 🔑 Key Architecture Decisions

### 1. **Service Layer Pattern**
All business logic (OCR, NER, proposal generation) is in service classes in `extraction/services.py` and `proposals/services.py`. This keeps models and views focused on data structure and routing.

### 2. **Async Task Processing**
Heavy operations (document processing, PDF generation) use Celery + Redis. Views return immediately; clients poll for results.

### 3. **German Locale Handling**
Currency formats (1.234,56 €) and date formats (DD.MM.YYYY) are handled centrally in constants and serializers. Always use `parse_german_currency()` for parsing, format with German locale.

### 4. **Multi-Database Support**
- **Development:** SQLite (no setup needed, perfect for local work)
- **Production:** PostgreSQL (configured via environment variables)

Settings auto-detect based on `DJANGO_SETTINGS_MODULE` environment variable.

### 5. **DSGVO Compliance**
- Audit logging on all document operations (documents/models.py:AuditLog)
- User data isolation (all queries filtered by request.user)
- Document retention policies configurable per user

---

## 📚 Module Documentation

### `core/constants.py`
German craftsmanship data:
- **HOLZARTEN** - Wood types (Eiche, Kiefer, etc.) with complexity factors
- **KOMPLEXITÄTS_FAKTOREN** - Complexity multipliers (gedrechselt, gefräst, etc.)
- **OBERFLÄCHEN_FAKTOREN** - Surface treatment multipliers (lackiert, geölt, etc.)
- Helper functions: `parse_german_currency()`, `format_german_price()`

### `documents/models.py`
- **Document** - Uploaded PDF/image with metadata
- **ExtractionResult** - OCR/NER output with confidence scores
- **AuditLog** - DSGVO-compliant operation tracking

### `extraction/services.py`
- **GermanOCRService** - PaddleOCR wrapper (handles German text, Umlauts)
- **GermanNERService** - spaCy entity recognition (wood types, prices, etc.)

### `proposals/services.py`
- **ProposalService** - 3-layer pricing engine (manufacturing specs → company config → dynamic price)
- **ProposalPdfService** - PDF generation with reportlab (German formatting)
- **ProposalEmailService** - Email delivery integration

### `api/v1/views.py`
6 main ViewSets:
- **DocumentViewSet** - Upload, list, retrieve, process documents
- **ProposalViewSet** - Generate, list, retrieve, download PDF, send email
- **ExtractionResultViewSet** - View extraction results
- **UserViewSet** - User management
- **CustomerViewSet** - Customer database
- **AuditLogViewSet** - Audit trail (read-only)

---

## 🧪 Testing Guide

### Test Structure
- **Unit tests** (70-80%) - Test services in isolation with mocks
- **Integration tests** (15-20%) - Test API endpoints with database
- **E2E tests** (5-10%) - Full workflow tests

### Test File Organization
```
tests/
├── conftest.py                    # Fixtures: api_client, authenticated_user, etc.
├── test_core_constants.py         # Constants validation
├── test_extraction_services.py    # OCR/NER service tests
├── test_api_views.py              # REST API endpoint tests
├── test_pdf_service.py            # PDF generation tests
└── fixtures/                      # Sample files (PDFs, images)
```

### Writing Tests

```python
import pytest
from rest_framework.test import APIClient

# Use pytest fixtures from conftest.py
@pytest.mark.django_db
def test_document_upload(authenticated_api_client):
    """Test uploading a document"""
    response = authenticated_api_client.post(
        '/api/v1/documents/',
        {'file': test_file, 'name': 'test.pdf'},
        format='multipart'
    )
    assert response.status_code == 201
    assert 'id' in response.data

@pytest.mark.integration
def test_full_workflow(authenticated_api_client):
    """Test document upload → processing → proposal generation"""
    # 1. Upload document
    doc_resp = authenticated_api_client.post('/api/v1/documents/', ...)
    doc_id = doc_resp.data['id']

    # 2. Process document (OCR/NER)
    proc_resp = authenticated_api_client.post(f'/api/v1/documents/{doc_id}/process/')
    assert proc_resp.status_code == 200

    # 3. Generate proposal
    prop_resp = authenticated_api_client.post('/api/v1/proposals/', {
        'document_id': doc_id,
        'customer_id': customer_id
    })
    assert prop_resp.status_code == 201
```

### Available Fixtures (conftest.py)
```python
authenticated_api_client  # DRF test client with auth token
authenticated_user        # Test user with token
api_client               # Unauthenticated client
sample_pdf_file          # Test document (PDF)
sample_image_file        # Test document (Image)
```

---

## 🔗 REST API Reference

### Authentication
```bash
POST /api/auth/token/
# Request: {"username": "user", "password": "pass"}
# Response: {"token": "abc123..."}

# Use token: Authorization: Token abc123...
```

### Documents (20+ Endpoints via ViewSets)
```bash
POST   /api/v1/documents/                    # Upload document
GET    /api/v1/documents/                    # List documents
GET    /api/v1/documents/{id}/               # Get document
POST   /api/v1/documents/{id}/process/       # Extract (OCR+NER)
GET    /api/v1/documents/{id}/extraction_summary/  # Get results
DELETE /api/v1/documents/{id}/               # Delete document
```

### Proposals
```bash
POST   /api/v1/proposals/                    # Generate proposal
GET    /api/v1/proposals/                    # List proposals
GET    /api/v1/proposals/{id}/               # Get proposal
GET    /api/v1/proposals/{id}/download_pdf/  # Download PDF
POST   /api/v1/proposals/{id}/send/          # Send via email
```

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/api/docs/swagger/
- **ReDoc:** http://localhost:8000/api/docs/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

---

## 🔐 Security Considerations

### Before Production Deployment
- [ ] Change `SECRET_KEY` (settings/production.py)
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` for your domain
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS for frontend domain
- [ ] Store secrets in environment variables or Secret Manager
- [ ] Enable database backups
- [ ] Setup monitoring (Sentry, Cloud Logging)
- [ ] Configure rate limiting

### Built-in Security Features
- ✅ Token authentication (DRF)
- ✅ User data isolation (multi-tenancy)
- ✅ CSRF protection (Django middleware)
- ✅ XSS protection (Django templates)
- ✅ SQL injection prevention (ORM)
- ✅ DSGVO audit logging

---

## 🐳 Docker & Deployment

### Local Docker (Recommended for Testing)
```bash
docker-compose up -d
# Full stack: Django, PostgreSQL, Redis, Celery, Nginx
# Access: http://localhost:8000
```

### GCP Cloud Run (Production)
Configured in `config/settings/production.py`:
- Connects to Cloud SQL PostgreSQL
- Uses Cloud Storage for media files
- Reads secrets from Secret Manager
- Horizontal auto-scaling via Cloud Run

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for full instructions.

---

## 📊 Performance Targets

### Expected Response Times
- Document upload: < 1 second
- OCR processing: 5-30 seconds (depends on image quality)
- NER processing: 2-10 seconds
- Proposal generation: < 1 second
- PDF download: < 2 seconds
- API response (cached): < 100ms

### Database
- PostgreSQL 15 with indexes on all query fields
- Atomic transactions enabled (`ATOMIC_REQUESTS=True`)
- Connection pooling via django-db-backends

### Caching
- Redis for Celery result backend and session cache
- Query result caching (can be added to services)

---

## 🔧 Troubleshooting

### Common Issues

**Port 8000 already in use:**
```bash
python manage.py runserver 8001  # Use different port
# OR
docker-compose down  # Stop containers
```

**Import errors after code changes:**
```bash
cd backend
deactivate  # Exit venv
source venv/bin/activate  # Restart venv
python manage.py migrate  # Ensure DB is synced
```

**Database connection failed:**
```bash
# Check PostgreSQL is running
docker-compose logs postgres
# or locally: psql -U postgres -h localhost
```

**Celery tasks not executing:**
```bash
# Verify Redis is running
redis-cli ping  # Should return PONG
# Check Celery worker
docker-compose logs celery_worker
```

**OCR/NER models not downloading:**
```bash
# Manually download spaCy model
python -m spacy download de_core_news_lg
# PaddleOCR downloads on first use (internet required)
```

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| [README.md](./README.md) | Project overview & quick start |
| [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) | Development workflows & patterns |
| [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | Docker, GCP, Kubernetes deployment |
| [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md) | API integration examples |
| [backend/README.md](./backend/README.md) | Backend module overview |
| [backend/core/README.md](./backend/core/README.md) | Constants library |
| [backend/documents/README.md](./backend/documents/README.md) | Document models |
| [backend/extraction/README.md](./backend/extraction/README.md) | OCR/NER services |
| [backend/proposals/README.md](./backend/proposals/README.md) | Proposal generation |
| [backend/api/README.md](./backend/api/README.md) | REST API reference |
| [backend/tests/README.md](./backend/tests/README.md) | Testing guide |

---

## 🎯 Code Style Guidelines

### Python Standards
- **Type hints required** on all functions
- **Docstrings required** on all public methods (Google style)
- **Black formatting** (line length: 88)
- **PEP 8 compliance** enforced by flake8

### Django Patterns
- ✅ Use Class-based Views (not function-based)
- ✅ Isolate business logic in Service classes
- ✅ Write comprehensive docstrings with Args/Returns/Raises
- ❌ Never put business logic in models
- ❌ Never call external services from views (use services)
- ❌ Never hardcode strings (use constants or gettext for i18n)

### Example Service Method
```python
class GermanOCRService:
    """Extract text from German documents using PaddleOCR."""

    def process(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF or image using German OCR models.

        Args:
            file_path: Path to PDF or image file

        Returns:
            Dictionary with keys:
            - text: Extracted text
            - confidence: Average confidence score (0-1)
            - lines: List of text lines with bounding boxes
            - processing_time_ms: Execution time

        Raises:
            DocumentProcessingError: If OCR fails
            FileNotFoundError: If file doesn't exist
        """
        # Implementation...
```

---

## ⚙️ Environment Variables

### Development (.env)
```bash
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
SECRET_KEY=insecure-dev-key-only
ALLOWED_HOSTS=localhost,127.0.0.1

# SQLite (default)
# No database config needed

# Email (console output in dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production (Config Vars)
```bash
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=<generate-with-django.core.management.utils.get_random_secret_key>
ALLOWED_HOSTS=yourdomain.com

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=draftcraft_prod
DB_USER=postgres
DB_PASSWORD=<secure-password>
DB_HOST=cloud-sql-proxy
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
```

---

## 🔄 Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make code changes** following code style guidelines

3. **Run tests & quality checks**
   ```bash
   black . && mypy . && pytest --cov=. --cov-fail-under=80
   ```

4. **Update CHANGELOG.md** if making significant changes

5. **Commit with clear message**
   ```bash
   git commit -m "feat: Add new feature

   - Description of changes
   - Why it was needed"
   ```

6. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

---

## 📝 Key Files to Read First

**To understand the system architecture:**
1. [backend/config/settings/base.py](./backend/config/settings/base.py) - Django configuration
2. [backend/api/v1/views.py](./backend/api/v1/views.py) - REST API endpoints
3. [backend/extraction/services.py](./backend/extraction/services.py) - OCR/NER logic
4. [backend/proposals/services.py](./backend/proposals/services.py) - Pricing & generation

**To run tests:**
1. [backend/pytest.ini](./backend/pytest.ini) - Test configuration
2. [backend/tests/conftest.py](./backend/tests/conftest.py) - Pytest fixtures

**To deploy:**
1. [docker-compose.yml](./docker-compose.yml) - Local stack configuration
2. [Dockerfile](./Dockerfile) - Production image
3. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Detailed deployment steps

---

## ✨ Quick Reference

### Most Common Tasks

| Task | Command |
|------|---------|
| Start development server | `python manage.py runserver` |
| Run all tests | `pytest --cov=. -v` |
| Format code | `black .` |
| Check types | `mypy . --ignore-missing-imports` |
| Create migration | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Access API docs | http://localhost:8000/api/docs/swagger/ |
| Access admin panel | http://localhost:8000/admin/ |
| Start Docker stack | `docker-compose up -d` |
| View Docker logs | `docker-compose logs -f web` |

---

**Last Updated:** November 2025
**Status:** ✅ Production Ready
**Python:** 3.11+
**Django:** 5.0 LTS
**Test Coverage:** 85%

For questions or issues, refer to the relevant README in the documentation directory or check test files for usage examples.
