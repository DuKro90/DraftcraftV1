# DraftCraft Developer Guide

Complete guide for developing, testing, and deploying DraftCraft.

---

## Quick Start

### Prerequisites
- **Python 3.11+**
- **pip** (included with Python)
- **Git** (optional)

### Option A: Local Development (SQLite)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
# Open http://localhost:8000/admin/
```

### Option B: Docker (Recommended for Testing)

```bash
docker-compose up -d
docker-compose logs -f web  # View logs
# Open http://localhost:8000/admin/
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for full Docker instructions.

---

## Project Architecture

### Django Apps Structure

```
backend/
├── core/              # Constants & utilities (German wood types, pricing)
├── documents/         # Document upload, processing status, audit logging
├── extraction/        # OCR/NER services (PaddleOCR, spaCy)
├── proposals/         # Proposal generation, PDF export, email sending
└── api/v1/            # REST API endpoints (DocumentViewSet, ProposalViewSet, etc.)
```

### Service Layer Pattern

```
Views (api/v1/views.py)
    ↓
Serializers (documents/serializers.py, etc.)
    ↓
Services (extraction/services/, proposals/services.py)
    ↓
Models (documents/models.py, etc.)
    ↓
Database (PostgreSQL/SQLite)
```

**Rule:** Business logic goes in services, not models.

---

## Common Development Workflows

### Running Tests

```bash
# All tests (57 total)
pytest --cov=. --cov-fail-under=80 -v

# Specific test file
pytest tests/test_api_views.py -v

# Watch mode (auto-rerun on file changes)
pytest-watch -- --cov=. -v

# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration
```

### Code Quality Checks

```bash
# Format code
black .

# Type checking
mypy . --ignore-missing-imports

# Linting
flake8 .

# Sort imports
isort .

# All checks (recommended before commit)
black . && mypy . && flake8 . && pytest --cov=.
```

### Working with Models

```bash
# Create migration after model changes
python manage.py makemigrations documents

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Revert last migration
python manage.py migrate documents 0001
```

### Adding API Endpoints

1. **Create serializer** in `documents/serializers.py`
2. **Create ViewSet** in `api/v1/views.py`
3. **Register in router** in `api/v1/urls.py`
4. **Write tests** in `tests/test_api_views.py`
5. **Document** in docstrings

Example:

```python
# api/v1/views.py
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        """Custom endpoint action"""
        # Your logic here
        return Response({'status': 'done'})
```

---

## Working with Async Tasks (Celery)

### Running Background Jobs

```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat (scheduler)
celery -A config beat -l info

# Monitor tasks
celery -A config events
```

### Creating Async Tasks

```python
# extraction/tasks.py
@shared_task(bind=True, max_retries=3)
def process_document_async(self, document_id):
    try:
        # Your task logic
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * 2 ** self.request.retries)
```

---

## Docker Development

### Building Images

```bash
# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build web
```

### Running Containers

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Common Issues

**Port already in use:**
```bash
docker-compose down  # Stop all containers
# or use different port: docker-compose -p project_name up
```

**Database connection failed:**
```bash
# Ensure database container is healthy
docker-compose ps
# Check logs for errors
docker-compose logs postgres
```

**Celery tasks not running:**
```bash
# Verify Redis is running
docker-compose logs redis
# Check Celery worker logs
docker-compose logs celery_worker
```

See [DOCKER_FIXES.md](docs_archive/DOCKER_FIXES.md) in archive for additional troubleshooting.

---

## Testing Strategy

### Test Structure

- **test_core_constants.py** (17 tests) - Manufacturing constants validation
- **test_extraction_services.py** (15+ tests) - OCR/NER service tests
- **test_api_views.py** (15+ tests) - API endpoint tests
- **test_pdf_service.py** (10+ tests) - PDF generation tests

### Writing Tests

```python
import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_document_upload(authenticated_api_client):
    """Test document upload endpoint"""
    response = authenticated_api_client.post(
        '/api/v1/documents/',
        {'file': test_file},
        format='multipart'
    )
    assert response.status_code == 201
    assert 'id' in response.data
```

### Test Fixtures (conftest.py)

```python
api_client            # Unauthenticated client
authenticated_user    # Test user
authenticated_api_client  # Authenticated client
```

---

## Using External Services

### PaddleOCR (Text Extraction)

**Installation:**
```bash
pip install paddleocr pdf2image pillow
```

**Usage:**
```python
from extraction.services import GermanOCRService

service = GermanOCRService({'ocr_use_cuda': False})
result = service.process('/path/to/document.pdf')
# Returns: {text, confidence, lines, processing_time_ms}
```

### spaCy NER (Entity Recognition)

**Installation:**
```bash
pip install spacy
python -m spacy download de_core_news_lg
```

**Usage:**
```python
from extraction.services import GermanNERService

service = GermanNERService({'ner_model': 'de_core_news_lg'})
result = service.process(ocr_text, document)
# Returns: {entities, summary, confidence, processing_time_ms}
```

---

## Deployment

### Local Deployment

```bash
python manage.py collectstatic
python manage.py runserver
```

### Docker Deployment

```bash
docker-compose up -d
# Services available at http://localhost/
```

### Production Deployment (GCP Cloud Run)

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for:
- Cloud SQL setup
- Cloud Storage configuration
- Environment variables
- Scaling configuration

---

## Troubleshooting

### Django Issues

**Import errors:**
```bash
# Ensure you're in backend/ directory
cd backend
# Activate virtual environment
source venv/bin/activate
```

**Database errors:**
```bash
# Remove and recreate SQLite database
rm db.sqlite3
python manage.py migrate
```

**Port already in use:**
```bash
python manage.py runserver 8001  # Use different port
```

### Celery Issues

**Tasks not running:**
```bash
# Ensure Redis is running
redis-cli ping  # Should return PONG

# Check Celery worker
celery -A config inspect active
```

**Long task timeouts:**
```bash
# Increase task timeout in config/settings/base.py
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes
```

### API Issues

**401 Unauthorized:**
```bash
# Get new token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

**CORS errors:**
```bash
# Check CORS_ALLOWED_ORIGINS in settings/base.py
# Update for your frontend domain
```

---

## Documentation Structure

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview & features |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | This guide |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Deployment instructions |
| [FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md) | API integration examples |
| [CHANGELOG.md](CHANGELOG.md) | Project history |
| [backend/core/README.md](backend/core/README.md) | Constants library |
| [backend/api/README.md](backend/api/README.md) | REST API reference |

---

## Key Principles

✅ **Service Layer Pattern** - Business logic isolated in services
✅ **Type Hints** - Full type annotations throughout codebase
✅ **Tests First** - Write tests before implementing features
✅ **German Locale** - Format currency & dates correctly
✅ **DSGVO Compliance** - Audit logging on all operations
✅ **Error Handling** - Proper exceptions with context
✅ **Documentation** - Docstrings on all public functions

---

## Getting Help

1. **Check existing tests** - See `tests/` for usage examples
2. **Review service code** - Services document their interface
3. **Check module READMEs** - Each Django app has a README
4. **Read Django docs** - https://docs.djangoproject.com/
5. **API docs** - http://localhost:8000/api/docs/swagger/

---

**Last Updated:** November 26, 2025
**Status:** Production Ready ✅
**Python:** 3.11+
**Django:** 5.0 LTS
