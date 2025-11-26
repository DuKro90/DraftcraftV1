# Docker Container Issues - Fixed

## Summary

Successfully resolved persistent Docker container restart loop affecting the DraftCraft backend. All services (web, celery_worker, celery_beat, postgres, redis, nginx) now running stably without restarts.

## Issues Identified and Fixed

### 1. **Missing Python Dependencies**
- **Problem**: Docker build was using `development.txt` but missing critical packages for production settings
- **Solution**: Added the following to `backend/requirements/base.txt`:
  - `gunicorn==21.2.0` (WSGI application server)
  - `whitenoise==6.6.0` (static file serving)
  - `django-storages==1.14.2` (cloud storage support)
  - `google-cloud-storage==2.10.0` (GCS integration)

### 2. **Malformed Logging Configuration**
- **Problem**: `backend/config/settings/base.py` had duplicate and malformed `django.db.backends` logging handler definitions
- **Solution**: Removed invalid handler definitions in lines 231-234
- **File**: `backend/config/settings/base.py`

### 3. **Missing Celery Application Initialization**
- **Problem**: Docker container couldn't find Celery app - `celery -A config` command failed
- **Solution**: Created `backend/config/celery.py` with proper Celery initialization
- **Also Updated**: `backend/config/__init__.py` to export celery app at module level

### 4. **Missing drf-spectacular Dependency**
- **Problem**: `config/settings/base.py` references `drf_spectacular` in REST_FRAMEWORK but package wasn't in requirements
- **Solution**: Added `drf-spectacular==0.27.0` to `backend/requirements/base.txt`

### 5. **Missing Health Check Module**
- **Problem**: `config/urls.py` includes `health_check` package but it wasn't installed
- **Solution**: Made health check endpoint optional with try/except pattern in `config/urls.py`

### 6. **Google Cloud Logging Configuration Error**
- **Problem**: `config/settings/production.py` unconditionally configured google.cloud.logging handler without installing the dependency
- **Solution**: Made handler conditional - only configures if `google-cloud-logging` is available
- **File**: `backend/config/settings/production.py` (lines 76-85)

### 7. **Strict SSL Requirements for Development**
- **Problem**: Production settings required SSL for database connections, breaking local Docker dev environment
- **Solution**: Made SSL mode configurable via `DB_SSLMODE` environment variable (defaults to 'disable' for Docker)
- **File**: `backend/config/settings/production.py` (line 34)

### 8. **Overly Strict Security Headers**
- **Problem**: Production settings enforced HSTS and SSL redirect, breaking local development
- **Solution**: Made security headers conditional on `SECURE_COOKIES` environment variable (not set in Docker)
- **File**: `backend/config/settings/production.py` (lines 60-72)

### 9. **Missing WSGI Application Module**
- **Problem**: Gunicorn couldn't load `config.wsgi` application module
- **Solution**: Created `backend/config/wsgi.py` with standard Django WSGI application factory

### 10. **Static Files Storage Configuration**
- **Problem**: Production settings tried to use whitenoise storage without conditional check
- **Solution**: Commented out optional whitenoise storage to use Django's default ManifestStaticFilesStorage
- **File**: `backend/config/settings/production.py` (lines 74-77)

## Files Modified

| File | Changes |
|------|---------|
| `backend/config/settings/base.py` | Removed malformed logging handler definitions |
| `backend/config/settings/production.py` | Made GCS, cloud logging, SSL, and security headers conditional |
| `backend/config/celery.py` | **Created** - Celery app initialization |
| `backend/config/__init__.py` | Updated to expose Celery app |
| `backend/config/urls.py` | Made health_check endpoint optional |
| `backend/config/wsgi.py` | **Created** - Standard Django WSGI application |
| `backend/requirements/base.txt` | Added missing dependencies (gunicorn, whitenoise, django-storages, google-cloud-storage) |

## Deployment Configuration Changes

### Environment Variables Used in Docker

When setting `DJANGO_SETTINGS_MODULE=config.settings.production`, the following variables control production behavior:

```env
# Database
DB_SSLMODE=disable          # Set to "require" for actual GCP production
DB_NAME=draftcraft_dev
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432

# Security (only apply strict rules if this is true)
SECURE_COOKIES=false        # Set to "true" for actual production

# Static Files (using default storage, not whitenoise)
# whitenoise storage is commented out for Docker compatibility

# Cloud Storage (optional)
# GCS_BUCKET_NAME=your-bucket
# GCP_PROJECT_ID=your-project
```

## Testing the Fix

### Verify All Services Running

```bash
cd /path/to/DraftcraftV1
docker-compose ps
```

Expected output: All services `Up` with no `Restarting` status

### Check Web Service Logs

```bash
docker-compose logs web
```

Expected: Should see gunicorn startup messages like:
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Using worker: sync
[INFO] Booting worker with pid: 17
[INFO] Booting worker with pid: 18
```

### Verify API Endpoint

```bash
curl http://localhost:8000/api/schema/
```

Should return the OpenAPI schema (not health check since it's optional)

## Architecture

The Docker setup uses Django's production settings but makes them flexible for development:

1. **Django Settings**: Uses `config.settings.production` in Docker
2. **Conditional Features**: Production-only features (SSL, cloud services) are conditional
3. **Development Compatibility**: Runs with local postgres/redis instead of GCP services
4. **Future Production Ready**: Already has placeholder configs for GCS, Cloud Logging, Sentry

## Known Limitations

- OCR/NLP features (paddleocr, spacy, pdf2image) are commented out in `backend/requirements/development.txt`
  - These require heavy system dependencies and long compilation times
  - See `DOCKER_FIXES.md` reminder in knowledge base for future setup

- Health check endpoint (`/health/`) is optional since the package isn't installed
  - Docker's built-in healthchecks in `docker-compose.yml` still work

## Next Steps

1. ✅ **Docker Services Stable**: All containers running without restarts
2. **Model Migrations Pending**: Run `python manage.py makemigrations` for apps with model changes
3. **OCR Dependencies**: Install paddleocr/spacy later when system dependencies are available
4. **Frontend Integration**: Connect React frontend to running backend API

## Related Documentation

- [LOCAL_SETUP_GUIDE.md](backend/LOCAL_SETUP_GUIDE.md) - Local development setup
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Overall project status
