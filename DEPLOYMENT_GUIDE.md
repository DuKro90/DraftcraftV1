# 🚀 Deployment Guide - DraftCraft Backend

Complete production deployment guide for DraftCraft backend on Docker, Kubernetes, GCP Cloud Run, and traditional servers.

---

## 📋 Table of Contents

1. [Docker & Docker Compose Setup](#docker--docker-compose-setup)
2. [Local Docker Deployment](#local-docker-deployment)
3. [Production Environment Setup](#production-environment-setup)
4. [GCP Cloud Run Deployment](#gcp-cloud-run-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring & Logging](#monitoring--logging)
7. [Security Hardening](#security-hardening)
8. [Troubleshooting](#troubleshooting)

---

## Docker & Docker Compose Setup

### Prerequisites

- **Docker** - [Install](https://docs.docker.com/get-docker/)
- **Docker Compose** - Included with Docker Desktop
- **Git** - For cloning the repository
- **Disk space** - At least 10GB for images and volumes

### Available Files

- `Dockerfile` - Multi-stage build for production
- `docker-compose.yml` - Complete stack (Django, PostgreSQL, Redis, Celery, Nginx)
- `nginx.conf` - Reverse proxy configuration

### Architecture

```
┌─────────────────────────────────────────────┐
│              Nginx (Reverse Proxy)          │
│              Port 80/443                    │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   ┌────▼───┐  ┌──▼──┐  ┌───▼──┐
   │ Django │  │ API │  │Static│
   │ Web    │  │Docs │  │Files │
   │ 8000   │  │     │  │      │
   └────┬───┘  └─────┘  └──────┘
        │
   ┌────┴───────────────────────────┐
   │                                 │
┌──▼────┐                      ┌────▼──┐
│ Celery│                      │Postgres│
│Worker │                      │ 5432   │
└───────┘                      └────┬───┘
        │                            │
   ┌────▼──────────────────────────▼┐
   │    Redis (Cache & Broker)      │
   │    Port 6379                   │
   └────────────────────────────────┘
```

---

## Local Docker Deployment

### 1. Build Images

```bash
cd C:\Codes\DraftcraftV1

# Build Docker image
docker build -t draftcraft:latest .

# Verify image
docker images | grep draftcraft
```

### 2. Start Stack with Docker Compose

```bash
# Start all services in background
docker-compose up -d

# Check status
docker-compose ps

# Expected output:
# NAME                    STATUS
# draftcraft_postgres     Up 2 minutes (healthy)
# draftcraft_redis        Up 2 minutes (healthy)
# draftcraft_web          Up 1 minute
# draftcraft_celery_worker   Up 1 minute
# draftcraft_celery_beat     Up 1 minute
# draftcraft_nginx        Up 1 minute
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100
```

### 4. Access Application

| Service | URL | Credentials |
|---------|-----|-------------|
| Django Admin | `http://localhost:8000/admin/` | admin/admin |
| API Docs (Swagger) | `http://localhost:8000/api/docs/swagger/` | - |
| API Docs (ReDoc) | `http://localhost:8000/api/docs/redoc/` | - |
| Nginx | `http://localhost/` | - |
| PostgreSQL | `localhost:5432` | postgres/postgres |
| Redis | `localhost:6379` | - |

### 5. Create Admin User

```bash
# Inside running container
docker-compose exec web python manage.py createsuperuser

# Or directly
docker-compose run --rm web python manage.py createsuperuser \
  --username admin \
  --email admin@example.com \
  --noinput
```

### 6. Stop Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

---

## Production Environment Setup

### 1. Create Production .env File

```bash
# backend/.env.production (NEVER commit this!)
DEBUG=False
SECRET_KEY=your-secure-random-key-here-use-python-secrets
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-ip.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=draftcraft_prod
DB_USER=draftcraft_user
DB_PASSWORD=secure_password_here
DB_HOST=your-postgres-host
DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-sendgrid-key...
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# File Storage (GCS recommended for production)
GCS_BUCKET_NAME=draftcraft-documents-prod
GCP_PROJECT_ID=your-gcp-project-id

# Celery/Redis
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0

# Monitoring
SENTRY_DSN=https://key@sentry.io/project-id
DJANGO_LOG_LEVEL=INFO

# Encryption
ENCRYPTION_ENABLED=True
ENCRYPTION_KEY=your-32-byte-hex-key-here
```

### 2. Generate Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Production Requirements

```bash
# Use production requirements
pip install -r backend/requirements/production.txt

# Which includes:
# - gunicorn (WSGI server)
# - whitenoise (static files)
# - google-cloud-storage (GCS support)
# - sentry-sdk (error tracking)
# - psycopg2 (PostgreSQL driver)
```

### 4. Database Setup

```bash
# On PostgreSQL server
createdb draftcraft_prod
createuser draftcraft_user
ALTER USER draftcraft_user WITH PASSWORD 'secure_password_here';
ALTER ROLE draftcraft_user SET client_encoding TO 'utf8';
ALTER ROLE draftcraft_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE draftcraft_user SET default_transaction_deferrable TO on;
ALTER ROLE draftcraft_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE draftcraft_prod TO draftcraft_user;
```

### 5. Redis Setup

```bash
# Using Docker
docker run -d \
  --name draftcraft_redis_prod \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --appendonly yes

# Or install on host
# Ubuntu/Debian: sudo apt-get install redis-server
```

### 6. Static Files

```bash
# Collect static files (Django admin, API docs, etc.)
python manage.py collectstatic --noinput

# Serve with Nginx or WhiteNoise
```

### 7. Database Migrations

```bash
# Run migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

---

## GCP Cloud Run Deployment

**🌍 Region:** This guide uses `europe-west3` (Frankfurt, Germany) for GDPR compliance and low-latency access from Europe. All GCP resources (Cloud Run, Cloud SQL, Cloud Storage, Cloud Tasks) should be in the same region for optimal performance.

### Prerequisites

- **Google Cloud Project** - [Create](https://console.cloud.google.com/)
- **gcloud CLI** - [Install](https://cloud.google.com/sdk/docs/install)
- **Docker** - [Install](https://docs.docker.com/get-docker/)
- **GCP services enabled**:
  - Cloud Run API
  - Cloud SQL Admin API
  - Cloud Storage API
  - Secret Manager API

### 1. Setup GCP Project

```bash
# Set project
PROJECT_ID="your-project-id"
REGION="europe-west3"  # Or your preferred region

gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  cloudsql.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  containerregistry.googleapis.com
```

### 2. Create Cloud SQL Instance (PostgreSQL 15)

```bash
# Create instance (30GB, 1 shared CPU for dev, 2+ CPUs for prod)
gcloud sql instances create draftcraft-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-auto-increase \
  --storage-auto-increase-limit=100 \
  --enable-bin-log \
  --backup-start-time=02:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=03

# Create database
gcloud sql databases create draftcraft \
  --instance=draftcraft-db

# Create user
gcloud sql users create draftcraft \
  --instance=draftcraft-db \
  --password=secure_password_here

# Get connection name (you'll need this)
gcloud sql instances describe draftcraft-db --format='value(connectionName)'
```

### 3. Create Cloud Storage Bucket

```bash
# For document storage
gsutil mb -l $REGION gs://draftcraft-documents-prod

# Set permissions
gsutil iam ch serviceAccount:your-project@appspot.gserviceaccount.com:objectAdmin \
  gs://draftcraft-documents-prod
```

### 4. Store Secrets in Secret Manager

```bash
# Create secrets for sensitive data
echo "django-insecure-your-secret-key" | gcloud secrets create SECRET_KEY --data-file=-

echo "secure_db_password" | gcloud secrets create DB_PASSWORD --data-file=-

echo "your-sendgrid-api-key" | gcloud secrets create EMAIL_HOST_PASSWORD --data-file=-

echo "your-sentry-dsn" | gcloud secrets create SENTRY_DSN --data-file=-

# List secrets
gcloud secrets list
```

### 5. Build and Push Docker Image

```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Build image with GCP registry
docker build -t gcr.io/$PROJECT_ID/draftcraft:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/draftcraft:latest

# Verify
gcloud container images list
```

### 6. Create Cloud Run Service

```bash
# Deploy to Cloud Run
gcloud run deploy draftcraft \
  --image gcr.io/$PROJECT_ID/draftcraft:latest \
  --platform managed \
  --region $REGION \
  --memory 1Gi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars="DEBUG=False" \
  --set-env-vars="ALLOWED_HOSTS=draftcraft-xxxx.run.app" \
  --set-cloudsql-instances=$CONNECTION_NAME \
  --service-account=draftcraft@$PROJECT_ID.iam.gserviceaccount.com

# Get service URL
gcloud run services describe draftcraft --region $REGION --format='value(status.url)'
```

### 7. Set Environment Variables via Secret Manager

```bash
# Grant Cloud Run service account access to secrets
SERVICE_ACCOUNT="draftcraft@$PROJECT_ID.iam.gserviceaccount.com"

for secret in SECRET_KEY DB_PASSWORD EMAIL_HOST_PASSWORD SENTRY_DSN; do
  gcloud secrets add-iam-policy-binding $secret \
    --member=serviceAccount:$SERVICE_ACCOUNT \
    --role=roles/secretmanager.secretAccessor
done

# Update Cloud Run service to use secrets
gcloud run services update draftcraft \
  --region $REGION \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest,DB_PASSWORD=DB_PASSWORD:latest" \
  --update-env-vars="EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD},SENTRY_DSN=${SENTRY_DSN}"
```

### 8. Run Database Migrations

```bash
# Create task runner (one-off job)
gcloud run jobs create draftcraft-migrate \
  --image gcr.io/$PROJECT_ID/draftcraft:latest \
  --region $REGION \
  --tasks 1 \
  --parallelism 1 \
  --set-cloudsql-instances=$CONNECTION_NAME \
  --command "python,manage.py,migrate"

# Execute migration
gcloud run jobs execute draftcraft-migrate --region $REGION

# Check status
gcloud run jobs describe draftcraft-migrate --region $REGION
```

### 9. Setup Scheduled Tasks (Celery Beat)

```bash
# For background jobs, use Cloud Tasks or Cloud Scheduler
# Example: Run cleanup task daily at 2 AM

gcloud scheduler jobs create pubsub draftcraft-cleanup \
  --schedule="0 2 * * *" \
  --topic=draftcraft-tasks \
  --message-body='{"task":"extraction.tasks.cleanup_old_documents"}'
```

### 10. Configure Custom Domain (Optional)

```bash
# Map custom domain to Cloud Run
gcloud run domain-mappings create \
  --service=draftcraft \
  --domain=api.your-domain.com \
  --region=$REGION
```

---

## Kubernetes Deployment

### Prerequisites

- **kubectl** - [Install](https://kubernetes.io/docs/tasks/tools/)
- **Kubernetes cluster** - GKE, EKS, or on-prem
- **Container registry** - GCP Container Registry or Docker Hub

### 1. Create Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: draftcraft-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: draftcraft-web
  template:
    metadata:
      labels:
        app: draftcraft-web
    spec:
      containers:
      - name: draftcraft
        image: gcr.io/your-project/draftcraft:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "False"
        - name: DB_HOST
          value: "postgres-service"
        - name: DB_PORT
          value: "5432"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Deploy

```bash
# Create namespace
kubectl create namespace draftcraft

# Apply manifests
kubectl apply -f k8s/deployment.yaml -n draftcraft

# Check status
kubectl get pods -n draftcraft

# View logs
kubectl logs -f deployment/draftcraft-web -n draftcraft
```

---

## Monitoring & Logging

### 1. Django Logging

Logs are written to:
- `logs/django.log` - Application logs
- `logs/error.log` - Error logs
- `logs/access.log` - HTTP access logs

### 2. Sentry Error Tracking

```python
# Already configured in settings/production.py
# Set SENTRY_DSN environment variable

# Example Sentry event
try:
    do_something()
except Exception as e:
    import sentry_sdk
    sentry_sdk.capture_exception(e)
```

### 3. GCP Logging

```bash
# View Cloud Run logs
gcloud run logs read draftcraft --region=europe-west3

# With filtering
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=draftcraft" --limit=50
```

### 4. Health Checks

```bash
# Health endpoint
curl https://api.your-domain.com/health/

# Database health
curl https://api.your-domain.com/health/db/

# Cache health
curl https://api.your-domain.com/health/cache/
```

### 5. Monitoring Dashboard

Setup dashboards in:
- **GCP**: Cloud Monitoring
- **Prometheus**: Scrape `/metrics/` endpoint (requires django-prometheus)
- **DataDog**: Agent-based monitoring
- **New Relic**: APM integration

---

## Security Hardening

### 1. HTTPS/TLS

```bash
# Required! Only use HTTPS in production
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
HSTS_SECONDS=31536000
HSTS_INCLUDE_SUBDOMAINS=True
```

### 2. Database

```bash
# Use strong passwords (20+ characters)
# Enable SSL connections to database
# Restrict firewall to application servers only
# Regular backups with encryption
# Point-in-time recovery enabled
```

### 3. API Keys & Secrets

```bash
# Never commit .env to Git
# Use Secret Manager for production secrets
# Rotate keys regularly
# Monitor secret access logs
```

### 4. Rate Limiting

```python
# Already configured in DRF settings
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### 5. CORS

```bash
# Only allow trusted origins
CORS_ALLOWED_ORIGINS=https://your-frontend.com

# Never use wildcard in production
CORS_ALLOWED_ORIGINS != "*"
```

### 6. SQL Injection Prevention

✅ All queries use parameterized statements (ORM)
✅ No raw SQL without parameters
✅ Input validation on all endpoints

### 7. XSS Protection

✅ Content Security Policy headers configured
✅ All user input escaped in responses
✅ JSON responses (not JSON-P)

---

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs web

# Test database connection
docker-compose exec web python manage.py dbshell

# Run migrations
docker-compose exec web python manage.py migrate

# Check settings
docker-compose exec web python manage.py check
```

### Database connection errors

```bash
# Verify credentials
docker-compose exec postgres psql -U postgres -d draftcraft_dev

# Check environment variables
docker-compose exec web env | grep DB_

# Rebuild database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE draftcraft_dev;"
```

### Celery tasks not running

```bash
# Check broker connection
docker-compose exec celery_worker celery -A config inspect active

# Verify Redis
docker-compose exec redis redis-cli ping

# Restart workers
docker-compose restart celery_worker celery_beat
```

### Static files not serving

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Check file permissions
docker-compose exec web ls -la /app/staticfiles/
```

### Memory issues

```bash
# Increase memory limits in docker-compose.yml
# web:
#   deploy:
#     resources:
#       limits:
#         memory: 2G

# Restart containers
docker-compose up -d --force-recreate
```

---

## Performance Optimization

### 1. Database

```bash
# Add indexes
python manage.py sqlsequencereset documents | python manage.py dbshell

# Analyze queries
django-debug-toolbar (development only)
```

### 2. Caching

```bash
# Redis caching enabled
# Documents, entities, extraction results cached
# TTL: 1 hour (configurable)
```

### 3. CDN

```bash
# Static files via CloudFlare/CloudFront
# Media files via CDN
# GCS signed URLs for private documents
```

### 4. Compression

```bash
# Gzip compression enabled in Nginx
# Database compression enabled
# Image optimization recommended
```

---

## Backup & Disaster Recovery

### Database Backups

```bash
# GCP Cloud SQL automatic backups (daily)
gcloud sql backups list --instance=draftcraft-db

# Manual backup
gcloud sql backups create --instance=draftcraft-db

# Point-in-time recovery
gcloud sql backups restore BACKUP_ID --instance=draftcraft-db
```

### Document Backups

```bash
# GCS versioning enabled
gsutil versioning set on gs://draftcraft-documents-prod

# Daily export
gsutil -m cp -r gs://draftcraft-documents-prod gs://draftcraft-documents-backup/
```

---

## Rollback Procedures

### Docker Image

```bash
# Previous image
docker tag draftcraft:v1.0.0-stable draftcraft:latest
docker push draftcraft:latest

# Cloud Run rollback
gcloud run services update-traffic draftcraft --to-revisions=REVISION_1=100
```

### Database

```bash
# Restore from backup
gcloud sql backups restore BACKUP_ID --instance=draftcraft-db

# Point-in-time recovery
gcloud sql backups create --backup-kind BACKUP_ID --instance=draftcraft-db
```

---

## Scaling Guide

### Horizontal Scaling

```bash
# Cloud Run: Auto-scales to 1000 concurrent requests
gcloud run services update draftcraft \
  --max-instances=100 \
  --memory=2Gi \
  --cpu=2

# Kubernetes: Horizontal Pod Autoscaler
kubectl autoscale deployment draftcraft-web --min=3 --max=10 -n draftcraft
```

### Vertical Scaling

```bash
# Increase container resources
gcloud run services update draftcraft --memory=2Gi --cpu=2
```

### Database Scaling

```bash
# Upgrade instance type
gcloud sql instances patch draftcraft-db --tier=db-n1-standard-4
```

---

**Last Updated:** November 26, 2025
**Status:** Production Ready
**Version:** 1.0.0
