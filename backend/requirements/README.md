# DraftCraft Requirements Files

This directory contains different Python dependency specifications for different use cases.

## File Descriptions

### base.txt (Core Dependencies)
**Use for:** Minimal installation, basic Django application
**Size:** ~27 packages
**Installation time:** ~2 minutes
**Includes:**
- Django 5.0 + DRF
- PostgreSQL/SQLite drivers
- Celery + Redis
- PDF generation (ReportLab)
- API documentation
- JSON logging
- CORS support
- Storage backends

**Does NOT include:**
- OCR/NER capabilities
- Development tools (pytest, Black, mypy)
- Database-specific tools

```bash
pip install -r base.txt
```

### development.txt (Development Tools)
**Use for:** Local development, testing, code quality
**Extends:** base.txt
**Additional packages:**
- pytest + pytest-django (testing)
- pytest-cov (coverage reporting)
- Black (code formatting)
- mypy (type checking)
- flake8 (linting)
- isort (import sorting)
- django-debug-toolbar (debugging)
- Faker (test data)
- factory-boy (test factories)

```bash
pip install -r development.txt
```

### production.txt (Production Dependencies)
**Use for:** GCP Cloud Run, traditional servers
**Extends:** base.txt
**Additional packages:**
- gunicorn (WSGI server)
- whitenoise (static file serving)
- google-cloud-logging (Cloud Logging)
- sentry-sdk (error tracking)
- psycopg2-binary (PostgreSQL driver)

```bash
pip install -r production.txt
```

### ml.txt (ML/OCR Dependencies) ⭐ NEW
**Use for:** Adding OCR and NER capabilities to any environment
**Extends:** base.txt
**Additional packages:**
- paddleocr (OCR text extraction from documents)
- spacy (named entity recognition)
- pdf2image (PDF document handling)
- opencv-python (image preprocessing)
- scikit-image (advanced image processing)

**Note:** First installation will download large model files (~500MB total)

**Installation steps:**

```bash
# Step 1: Install ML dependencies
pip install -r ml.txt

# Step 2: Download spaCy German model
python -m spacy download de_core_news_lg

# Step 3: Done! Run tests to verify OCR works
pytest tests/test_extraction_services.py -v
```

### full.txt (Complete Installation) ⭐ LEGACY
**Use for:** Complete installation with all dependencies (includes ml.txt)
**Extends:** base.txt
**Note:** Equivalent to installing both base.txt + ml.txt

For new installations, prefer using `ml.txt` instead of `full.txt` for better clarity.

## Quick Decision Matrix

| Use Case | Recommended | Installation Time |
|----------|-------------|-------------------|
| Local development (SQLite) | `development.txt` | ~5 min |
| Testing API endpoints | `base.txt` | ~2 min |
| Add OCR/NER to development | `development.txt` + `ml.txt` | +15 min |
| Testing all OCR/NER features | `ml.txt` + `development.txt` | ~20 min |
| Production deployment | `production.txt` | ~3 min |
| Docker container (lightweight) | `base.txt` | in Dockerfile |
| Docker container (full OCR) | `ml.txt` | in Dockerfile |

## Installation Examples

### Quick Start (API Testing Only)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r base.txt
python manage.py migrate
python manage.py runserver
```

### Full Development (with OCR/NER)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r development.txt  # Includes base.txt
pip install -r ml.txt           # Add OCR/NER (preferred over full.txt)
python -m spacy download de_core_news_lg
python manage.py migrate
python manage.py runserver
```

### Local Testing (All Features)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r full.txt  # Includes base.txt
pip install -r development.txt  # Add dev tools
python -m spacy download de_core_news_lg
python manage.py migrate
pytest --cov=. -v
```

## Dependency Details

### Heavy Dependencies (> 50MB after installation)

| Package | Size | Purpose | Required |
|---------|------|---------|----------|
| paddleocr | 200MB+ | OCR text extraction | Optional |
| spacy (model) | 40MB | Named entity recognition | Optional |
| pytorch (paddleocr dep) | 100MB+ | ML framework | Optional (via paddleocr) |

⚠️ **Note:** OCR dependencies are optional. Basic testing can be done with `base.txt` only.

### Lightweight Dependencies (< 10MB)

- Django 5.0
- DRF
- Celery
- Redis
- psycopg2
- ReportLab
- All others

## Update Instructions

To update a specific requirements file:

```bash
# Update base dependencies only
pip install --upgrade -r base.txt

# Update development tools
pip install --upgrade -r development.txt

# Update all (base + OCR)
pip install --upgrade -r full.txt
```

## Troubleshooting

### PaddleOCR installation fails

```bash
# Try binary version
pip install paddleocr==2.7.0.3

# If still failing, you can skip it
# pip install -r base.txt  # Use basic version
```

### spaCy model download fails

```bash
# Try manual download
python -m spacy download de_core_news_lg

# If network issues, try with proxy
pip install -r base.txt --proxy=your-proxy
```

### Out of disk space during installation

Reduce installation size by using `base.txt`:
```bash
pip install -r base.txt  # Skip OCR (500MB+ saved)
```

## Compatibility

- **Python:** 3.11+
- **Operating Systems:** Linux, macOS, Windows
- **Database:** PostgreSQL 15+ (SQLite for dev)
- **Redis:** 7.0+ (for Celery)

---

**Last Updated:** November 26, 2025
**Status:** Production Ready ✅
