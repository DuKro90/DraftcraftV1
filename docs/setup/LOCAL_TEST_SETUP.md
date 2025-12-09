# Local Test Environment Setup - DraftCraft Phase 2

**Purpose:** Set up a safe local testing environment without breaking existing code.

**Status:** Week 2 Complete - Ready for local validation before Week 3 GCP deployment

---

## Quick Start (Safe Mode)

```bash
# 1. Navigate to backend directory
cd C:\Codes\DraftcraftV1\backend

# 2. Create isolated virtual environment (if not exists)
python -m venv venv_test

# 3. Activate virtual environment
venv_test\Scripts\activate

# 4. Verify isolation (should show venv_test path)
where python

# 5. Install core dependencies only (safe)
pip install --upgrade pip
pip install django==5.0 djangorestframework psycopg2-binary python-decouple
```

---

## Dependency Installation (Incremental Approach)

### Phase 1: Core Django Dependencies (REQUIRED)

```bash
pip install -r requirements/base.txt
```

**Expected contents of `requirements/base.txt`:**
- Django==5.0
- djangorestframework
- psycopg2-binary
- python-decouple
- pillow
- pytest
- pytest-django
- pytest-cov

### Phase 2: Optional ML Dependencies (SKIP FOR NOW)

**DO NOT install these yet** - they're large and may cause conflicts:
- PaddleOCR (requires paddlepaddle, opencv-python)
- spaCy models (large downloads)
- Tesseract

**Why skip?** All ML services have graceful error handling:
```python
# Example from image_preprocessor.py
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    # Service degrades gracefully
```

### Phase 3: Cloud Dependencies (LOCAL FALLBACK)

```bash
# Install Celery for local async processing (instead of Cloud Tasks)
pip install celery redis
```

**Why?** AsyncExecutor already has fallback logic:
```python
# settings.py - Set this for local development
CLOUD_TASKS_ENABLED = False  # Uses Celery instead
```

---

## Database Setup (SQLite for Testing)

### Option A: Use SQLite (Recommended for local tests)

**Edit:** `backend/handwerk_analyzer/settings.py`

```python
# TEMPORARY: Comment out PostgreSQL config
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         ...
#     }
# }

# ADD: SQLite for local testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_test.sqlite3',
    }
}
```

**Then run migrations:**
```bash
python manage.py migrate
python manage.py createsuperuser  # Create test user
```

### Option B: Use PostgreSQL Locally (Advanced)

If you have PostgreSQL installed locally:
```bash
# Create test database
psql -U postgres
CREATE DATABASE draftcraft_test;
CREATE USER draftcraft WITH PASSWORD 'testpass123';
GRANT ALL PRIVILEGES ON DATABASE draftcraft_test TO draftcraft;
\q

# Update settings.py with local credentials
```

---

## Running Tests Safely

### Syntax Validation Only (No dependencies needed)

```bash
# Verify all Python files compile without errors
python -m py_compile api/v1/batch_views.py
python -m py_compile extraction/services/batch_processor.py
python -m py_compile extraction/async_executor.py
python -m py_compile tests/test_batch_api.py
```

### Unit Tests (With minimal dependencies)

```bash
# Install test dependencies
pip install pytest pytest-django pytest-cov

# Run tests for batch API (no ML dependencies required)
pytest tests/test_batch_api.py -v

# Run batch processor tests
pytest tests/test_batch_processor.py -v

# Run synthetic document tests
pytest tests/test_synthetic_documents.py -v
```

### Integration Tests (Skip ML-dependent tests)

```bash
# Run only tests that don't require OCR/NER
pytest tests/ -v -m "not integration" --ignore=tests/test_ocr_service.py --ignore=tests/test_ner_service.py

# Or run specific test classes
pytest tests/test_batch_api.py::TestBatchListEndpoint -v
```

---

## Environment Configuration

### Create `.env` file for local testing

**File:** `backend/.env`

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=handwerk_analyzer.settings
SECRET_KEY=local-test-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite)
DATABASE_URL=sqlite:///db_test.sqlite3

# Cloud Features (DISABLED for local)
CLOUD_TASKS_ENABLED=False
USE_CLOUD_STORAGE=False

# Celery (Local async processing)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ML Features (DISABLED for now)
ENABLE_OCR=False
ENABLE_NER=False

# Logging
LOG_LEVEL=DEBUG
```

### Load environment in settings.py

```python
# handwerk_analyzer/settings.py
from decouple import config

SECRET_KEY = config('SECRET_KEY', default='unsafe-dev-key')
DEBUG = config('DEBUG', default=True, cast=bool)
CLOUD_TASKS_ENABLED = config('CLOUD_TASKS_ENABLED', default=False, cast=bool)
```

---

## Start Local Development Server

```bash
# Activate virtual environment
venv_test\Scripts\activate

# Start Django dev server
python manage.py runserver

# Server runs at: http://127.0.0.1:8000/
```

**Test API endpoints:**
```bash
# In another terminal (or use Postman/curl)

# 1. Create user token (Django admin or API)
# http://127.0.0.1:8000/admin/

# 2. Test batch endpoints
curl http://127.0.0.1:8000/api/v1/batches/
```

---

## Running Celery Locally (For Async Processing)

### Install Redis (Windows)

**Option 1: WSL2**
```bash
wsl
sudo apt update
sudo apt install redis-server
redis-server
```

**Option 2: Memurai (Windows native)**
- Download from https://www.memurai.com/
- Install and start service

### Start Celery Worker

```bash
# Terminal 1: Start Celery worker
celery -A handwerk_analyzer worker -l info --pool=solo

# Terminal 2: Django dev server
python manage.py runserver

# Terminal 3: Redis (if using WSL)
wsl redis-server
```

---

## Test Workflow (Without Breaking Code)

### 1. Syntax Validation (Safest)

```bash
# Check all new files compile
for file in api/v1/batch_views.py extraction/services/batch_processor.py extraction/async_executor.py; do
    echo "Checking $file..."
    python -m py_compile "$file"
done
```

### 2. Import Tests (Check dependencies)

```bash
python manage.py shell

# Try importing services
from extraction.services.batch_processor import BatchProcessor
from extraction.async_executor import AsyncExecutor
from api.v1.batch_views import BatchViewSet

# If imports work, basic structure is good
```

### 3. Database Migrations

```bash
# Check for migration issues
python manage.py makemigrations --dry-run

# Apply migrations
python manage.py migrate

# Verify models
python manage.py shell
>>> from documents.models import Batch, BatchDocument
>>> Batch.objects.count()
0
```

### 4. Run Subset of Tests

```bash
# Start with simple tests
pytest tests/test_batch_api.py::TestBatchListEndpoint::test_list_batches_authenticated -v

# If successful, expand
pytest tests/test_batch_api.py -v

# Full suite (will skip ML-dependent tests)
pytest tests/ -v --ignore=tests/test_ocr_service.py
```

---

## Troubleshooting

### Issue 1: ModuleNotFoundError for cv2

**Error:**
```
ModuleNotFoundError: No module named 'cv2'
```

**Solution:**
```bash
# Option A: Skip ML tests
pytest tests/ --ignore=tests/test_image_preprocessor.py

# Option B: Install OpenCV (large dependency)
pip install opencv-python
```

### Issue 2: Database errors

**Error:**
```
django.db.utils.OperationalError: no such table: documents_batch
```

**Solution:**
```bash
# Run migrations
python manage.py migrate

# If still fails, check DATABASES in settings.py
python manage.py showmigrations
```

### Issue 3: Cloud Tasks import errors

**Error:**
```
ModuleNotFoundError: No module named 'google.cloud.tasks_v2'
```

**Solution:**
This is expected! AsyncExecutor has fallback logic:
```python
# .env file
CLOUD_TASKS_ENABLED=False

# This uses Celery instead (install with: pip install celery redis)
```

### Issue 4: Celery not starting

**Error:**
```
Error: Invalid command 'worker'
```

**Solution:**
```bash
# Install Celery
pip install celery redis

# Windows-specific: Use solo pool
celery -A handwerk_analyzer worker -l info --pool=solo
```

---

## Validation Checklist

Before proceeding to Week 3 (GCP deployment), verify:

- [ ] Virtual environment activated (`venv_test`)
- [ ] Core dependencies installed (`pip list | grep django`)
- [ ] Database migrations applied (`python manage.py showmigrations`)
- [ ] Django server starts (`python manage.py runserver`)
- [ ] Batch API endpoints accessible (`http://127.0.0.1:8000/api/v1/batches/`)
- [ ] Syntax validation passes for all new files
- [ ] At least 10 tests pass (`pytest tests/test_batch_api.py -v`)
- [ ] No import errors in Django shell
- [ ] `.env` file configured for local development

---

## Next Steps After Local Validation

Once local tests pass:

1. **Week 3.1:** Set up GCP infrastructure (Cloud SQL, Cloud Run, Cloud Tasks)
2. **Week 3.2:** Create Terraform configs for infrastructure as code
3. **Week 3.3:** Configure CI/CD pipeline (Cloud Build, GitHub Actions)
4. **Week 3.4:** Deploy to GCP staging environment

---

## Quick Reference Commands

```bash
# Activate environment
venv_test\Scripts\activate

# Start Django
python manage.py runserver

# Run tests
pytest tests/test_batch_api.py -v

# Check migrations
python manage.py showmigrations

# Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser
```

---

**Last Updated:** 2025-11-26
**Phase:** 2 Week 2 Complete - Local Testing Before GCP Deployment
