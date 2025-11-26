# 🚀 Local Development Setup Guide - DraftCraft Backend

Complete step-by-step guide for setting up the DraftCraft Django backend on your local machine.

---

## 📋 Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **pip** - Usually included with Python
- **Git** - For version control (optional)
- **PostgreSQL 15** (optional) - For production-like testing
- **Redis** (optional) - For Celery async tasks (we'll use eager mode for testing)

**For Windows Users:**
- Use PowerShell or Command Prompt
- Path separators will work with both `/` and `\`

---

## ✅ Step 1: Environment Setup (5 mins)

### 1.1 Create Virtual Environment

```bash
cd C:\Codes\DraftcraftV1\backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate
```

✅ You should see `(venv)` in your terminal prompt.

### 1.2 Verify Python Version

```bash
python --version
# Should output: Python 3.11.x or higher

pip --version
# Should output: pip XX.X from ...
```

---

## 📦 Step 2: Install Dependencies (15-30 mins)

### 2.1 Install Development Requirements

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all development dependencies
pip install -r requirements/development.txt

# This installs:
# - Django 5.0 + DRF
# - PostgreSQL driver (psycopg2)
# - Celery + Redis
# - PaddleOCR for text extraction
# - spaCy for NER (spaCy models download separately)
# - Testing tools (pytest, pytest-django)
# - Code quality (Black, mypy, flake8)
```

**⏱️ Note:** First install can take 10-20 minutes due to:
- PaddleOCR downloading models (~200MB)
- spaCy building C extensions
- Other dependencies

### 2.2 Download spaCy German Model

```bash
# This is required for Named Entity Recognition
python -m spacy download de_core_news_lg

# Verify it works
python -c "import spacy; nlp = spacy.load('de_core_news_lg'); print('✅ spaCy model loaded')"
```

**🌍 Note:** ~40MB download. It extracts to your Python site-packages directory.

---

## 🗄️ Step 3: Configure Database (2 mins)

### 3.1 Check .env File

```bash
# The .env file is already created at:
# C:\Codes\DraftcraftV1\backend\.env

# Review it:
cat .env

# For local development, it uses SQLite (db.sqlite3)
# No PostgreSQL setup required! 🎉
```

### 3.2 Optional: Use PostgreSQL Instead

If you have PostgreSQL 15 running locally:

```bash
# Edit .env file and change:
# From:
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# To:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=draftcraft_dev
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Then run:
createdb draftcraft_dev  # Create database
```

---

## 🔧 Step 4: Run Database Migrations (1 min)

```bash
# Apply all migrations to create tables
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, documents, extraction, proposals, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ... (more migrations)
#   Applying proposals.0001_initial... OK
```

✅ This creates `db.sqlite3` with all tables.

---

## 👤 Step 5: Create Admin User (1 min)

```bash
# Create superuser account for Django admin
python manage.py createsuperuser

# It will ask:
# Username: admin
# Email: admin@example.com
# Password: (enter something secure for testing)
# Password (again):
# Superuser created successfully.
```

✅ You'll use this to log in to Django admin at `/admin/`

---

## 🧪 Step 6: Run Full Test Suite (5-10 mins)

### 6.1 Run All Tests

```bash
# Run tests with coverage report
pytest --cov=. --cov-fail-under=80 -v

# -v = verbose output (show each test)
# --cov=. = measure code coverage for all files
# --cov-fail-under=80 = fail if coverage < 80%

# Expected output:
# tests/test_core_constants.py::test_wood_types_valid_structure PASSED
# tests/test_extraction_services.py::test_ocr_service_initialization PASSED
# ...
# ============= 64 passed in XX.XXs =============
# Coverage: 85%
```

### 6.2 Run Specific Test File (Testing)

```bash
# Test only extraction services
pytest tests/test_extraction_services.py -v

# Test only API endpoints
pytest tests/test_api_views.py -v

# Test constants
pytest tests/test_core_constants.py -v
```

### 6.3 Run Tests with Watch (Auto-rerun on file change)

```bash
# Watch for file changes and re-run tests
pytest-watch -- --cov=. -v
```

---

## 🌐 Step 7: Start Development Server (1 min)

### 7.1 Run Django Development Server

```bash
# Start the server
python manage.py runserver

# Expected output:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.
```

### 7.2 Access the Application

Open your browser and navigate to:

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:8000/` | Home page |
| `http://localhost:8000/admin/` | Django admin (use superuser credentials) |
| `http://localhost:8000/api/docs/swagger/` | **Interactive API docs (Swagger UI)** |
| `http://localhost:8000/api/docs/redoc/` | Alternative API docs (ReDoc) |
| `http://localhost:8000/api/schema/` | OpenAPI JSON schema |

---

## 🔌 Step 8: Test API Endpoints (5 mins)

### 8.1 Get Authentication Token

```bash
# In another terminal:
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Response:
# {"token": "abc123def456..."}

# Save this token for the next requests
export TOKEN="abc123def456..."
```

### 8.2 Test Document Upload Endpoint

```bash
# Create a test document (text file)
echo "Eiche, kompliziert, 5 m²" > test_doc.txt

# Upload it
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Token $TOKEN" \
  -F "file=@test_doc.txt"

# Response:
# {"id": "550e8400-...", "status": "uploaded", ...}

# Save the ID for next steps
export DOC_ID="550e8400-..."
```

### 8.3 Test Document Processing (OCR + NER)

```bash
# Process the document
curl -X POST http://localhost:8000/api/v1/documents/$DOC_ID/process/ \
  -H "Authorization: Token $TOKEN"

# This will:
# 1. Run PaddleOCR to extract text
# 2. Run spaCy NER to identify entities
# 3. Extract material specifications
# 4. Save results to database

# Response:
# {"id": "...", "status": "completed", "extraction_result": {...}}
```

### 8.4 Test Proposal Generation

```bash
# Generate a proposal from the processed document
curl -X POST http://localhost:8000/api/v1/proposals/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "'$DOC_ID'",
    "customer_name": "Max Mustermann",
    "customer_email": "max@example.de",
    "valid_days": 30
  }'

# Response includes the full proposal with calculated prices
```

### 8.5 Alternative: Use Swagger UI

Instead of curl, you can use the interactive Swagger UI:
1. Go to `http://localhost:8000/api/docs/swagger/`
2. Click "Authorize" and enter your token
3. Try each endpoint directly from the browser
4. See real-time request/response

---

## 🐛 Step 9: Code Quality Checks

### 9.1 Format Code with Black

```bash
# Auto-format all Python files
black .

# Check formatting without changes
black --check .
```

### 9.2 Type Checking with mypy

```bash
# Check type hints
mypy .

# Check specific file
mypy documents/models.py
```

### 9.3 Linting with flake8

```bash
# Check for style issues
flake8 .

# Ignore specific errors
flake8 . --ignore=E501,W503
```

### 9.4 Import Sorting with isort

```bash
# Sort imports
isort .

# Check without changes
isort --check-only .
```

---

## 📊 Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'django'`

**Solution:**
```bash
# Verify virtual environment is activated
which python  # Should show path inside venv/
pip list      # Should show Django in the list

# If not, reinstall:
pip install -r requirements/development.txt
```

### Problem: `psycopg2` installation fails on Windows

**Solution:**
```bash
# This is expected - we use SQLite for local testing
# If you need PostgreSQL, install pre-built binary:
pip install psycopg2-binary
```

### Problem: `spacy` model download fails

**Solution:**
```bash
# Try downloading directly:
python -m spacy download de_core_news_lg

# Or download manually:
# https://github.com/explosion/spacy-models/releases
# Then load manually: spacy.load('/path/to/model')
```

### Problem: Port 8000 already in use

**Solution:**
```bash
# Use a different port:
python manage.py runserver 8001
```

### Problem: Database locked (SQLite)

**Solution:**
```bash
# Remove the SQLite database and recreate it:
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Problem: PaddleOCR model download fails

**Solution:**
```bash
# Models are downloaded on first use to ~/.paddleocr/
# If download fails, you can manually download from:
# https://github.com/PaddlePaddle/PaddleOCR

# For testing, you can mock the OCR service:
# See tests/test_extraction_services.py for examples
```

---

## 🎉 Success Checklist

After completing all steps, verify:

- [ ] Virtual environment activated (`(venv)` in prompt)
- [ ] All dependencies installed (`pip list` shows Django, pytest, etc.)
- [ ] spaCy model loaded (`python -c "import spacy; spacy.load('de_core_news_lg')"`)
- [ ] Migrations applied (`python manage.py showmigrations` shows all as `[X]`)
- [ ] Superuser created (can log in to `/admin/`)
- [ ] Tests pass (`pytest` shows "64 passed" or similar)
- [ ] Django server starts (`python manage.py runserver` shows "Starting development server")
- [ ] API accessible (`curl http://localhost:8000/api/docs/swagger/`)
- [ ] Token auth works (can get token via `/api/auth/token/`)
- [ ] Documents endpoint works (can POST to `/api/v1/documents/`)

---

## 📚 Next Steps

1. **Explore Django Admin** (`/admin/`)
   - Create documents, templates, proposals manually
   - See how data is structured

2. **Test API with Swagger** (`/api/docs/swagger/`)
   - Try all endpoints interactively
   - See real request/response examples

3. **Review Code Structure**
   - Read `backend/README.md` for module overview
   - Explore service classes in each app
   - Review tests for usage patterns

4. **Continue with Option 2** (PDF Export)
   - Implement ProposalPdfService
   - Add PDF download endpoint

---

## 🆘 Getting Help

- **Django Documentation:** https://docs.djangoproject.com/
- **DRF Documentation:** https://www.django-rest-framework.org/
- **spaCy Documentation:** https://spacy.io/
- **PaddleOCR Documentation:** https://github.com/PaddlePaddle/PaddleOCR

---

**Last Updated:** November 26, 2025
**Status:** ✅ Production Ready
