# DraftCraft Backend

Django 5.0 application for German document processing and proposal generation.

## Quick Start

```bash
cd backend

# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install (choose one)
pip install -r requirements/base.txt              # Minimal
pip install -r requirements/development.txt       # Development
pip install -r requirements/full.txt              # With OCR/NER

# Database & Run
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://localhost:8000/admin/` or `http://localhost:8000/api/docs/swagger/`

## Project Structure

| Module | Purpose | Status |
|--------|---------|--------|
| **core** | Manufacturing constants (woods, pricing, etc.) | ✅ Complete |
| **documents** | Document upload, processing, audit logging | ✅ Complete |
| **extraction** | OCR/NER services (PaddleOCR, spaCy) | ✅ Complete |
| **proposals** | Proposal generation, PDF export, email | ✅ Complete |
| **api** | REST API endpoints (20+) | ✅ Complete |

## Key Stats

- **57 tests** passing (~85% coverage)
- **10 Django models**
- **20+ API endpoints**
- **6 ViewSets**
- **3 Service layers**
- **Type hints:** 100%
- **Documentation:** 10+ READMEs

## Development

```bash
# Tests
pytest --cov=. -v

# Code quality
black . && mypy . && flake8 .

# Migrations
python manage.py makemigrations

# Django shell
python manage.py shell
```

## Requirements Files

See [requirements/README.md](requirements/README.md) for detailed explanation:

- `base.txt` - Core Django app (minimal)
- `development.txt` - Dev tools (pytest, Black, mypy)
- `production.txt` - GCP Cloud Run ready
- `full.txt` - Complete install with OCR/NER

## Module Documentation

- [core/README.md](core/README.md) - Constants library
- [documents/README.md](documents/README.md) - Document models
- [extraction/README.md](extraction/README.md) - OCR/NER services
- [proposals/README.md](proposals/README.md) - Proposal generation
- [api/README.md](api/README.md) - REST API reference
- [tests/README.md](tests/README.md) - Testing guide
- [requirements/README.md](requirements/README.md) - Dependencies

## Full Documentation

See root directory for comprehensive guides:
- **[DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)** - Complete development guide
- **[README.md](../README.md)** - Project overview
- **[DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Deployment instructions
