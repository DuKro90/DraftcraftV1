# DraftCraft V1 - Deployment Checklist

**Zielplattform:** Google Cloud Run + Supabase + Firebase Hosting/Cloud Storage
**Region:** europe-west3 (Frankfurt, DSGVO-konform)
**Deployment-Typ:** Semi-Automated CI/CD

---

## ✅ Pre-Deployment Checklist

### Phase 1: Infrastructure Setup (Manual)

#### Google Cloud Platform

- [ ] **GCP Projekt erstellen**
  ```bash
  gcloud projects create draftcraft-prod --name="DraftCraft Production"
  gcloud config set project draftcraft-prod
  ```

- [ ] **Billing Account verknüpfen**
  - Console: [https://console.cloud.google.com/billing](https://console.cloud.google.com/billing)

- [ ] **APIs aktivieren**
  ```bash
  gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com \
    sql-component.googleapis.com
  ```

- [ ] **Service Account erstellen**
  ```bash
  gcloud iam service-accounts create draftcraft-runner \
    --display-name="DraftCraft Cloud Run Service Account"
  ```

- [ ] **IAM Permissions zuweisen**
  ```bash
  # Cloud SQL Client
  gcloud projects add-iam-policy-binding draftcraft-prod \
    --member="serviceAccount:draftcraft-runner@draftcraft-prod.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

  # Secret Manager Accessor
  gcloud projects add-iam-policy-binding draftcraft-prod \
    --member="serviceAccount:draftcraft-runner@draftcraft-prod.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

  # Storage Admin
  gcloud projects add-iam-policy-binding draftcraft-prod \
    --member="serviceAccount:draftcraft-runner@draftcraft-prod.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
  ```

---

#### Google Secret Manager

- [ ] **Django Secret Key generieren und speichern**
  ```bash
  # Generiere Secret Key
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

  # Speichere in Secret Manager
  echo -n "YOUR_GENERATED_SECRET_KEY" | gcloud secrets create DJANGO_SECRET_KEY \
    --data-file=- \
    --replication-policy="automatic"
  ```

- [ ] **Encryption Key generieren und speichern**
  ```bash
  # Generiere 32-byte Fernet Key
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

  # Speichere in Secret Manager
  echo -n "YOUR_GENERATED_ENCRYPTION_KEY" | gcloud secrets create ENCRYPTION_KEY \
    --data-file=- \
    --replication-policy="automatic"
  ```

- [ ] **Gemini API Key speichern**
  ```bash
  echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
    --data-file=- \
    --replication-policy="automatic"
  ```

- [ ] **SendGrid API Key speichern** (optional)
  ```bash
  echo -n "YOUR_SENDGRID_API_KEY" | gcloud secrets create SENDGRID_API_KEY \
    --data-file=- \
    --replication-policy="automatic"
  ```

- [ ] **Sentry DSN speichern** (optional)
  ```bash
  echo -n "YOUR_SENTRY_DSN" | gcloud secrets create SENTRY_DSN \
    --data-file=- \
    --replication-policy="automatic"
  ```

---

#### Google Cloud Storage

- [ ] **Media Files Bucket erstellen**
  ```bash
  gsutil mb -c STANDARD -l europe-west3 gs://draftcraft-media-prod
  gsutil iam ch serviceAccount:draftcraft-runner@draftcraft-prod.iam.gserviceaccount.com:roles/storage.objectAdmin gs://draftcraft-media-prod
  ```

- [ ] **Static Files Bucket erstellen** (für Frontend)
  ```bash
  gsutil mb -c STANDARD -l europe-west3 gs://draftcraft-static-prod
  gsutil iam ch allUsers:objectViewer gs://draftcraft-static-prod
  gsutil web set -m index.html -e 404.html gs://draftcraft-static-prod
  ```

- [ ] **CORS konfigurieren** (für Frontend API Calls)
  ```bash
  cat > cors.json << EOF
  [
    {
      "origin": ["https://your-domain.com"],
      "method": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
      "responseHeader": ["Content-Type", "Authorization"],
      "maxAgeSeconds": 3600
    }
  ]
  EOF

  gsutil cors set cors.json gs://draftcraft-media-prod
  ```

---

#### Supabase Database

- [ ] **Supabase Projekt verifizieren**
  - URL: `https://app.supabase.com`
  - Region: eu-west-1 (Frankfurt) ✅
  - Free Tier: 500MB (aktueller Status prüfen)

- [ ] **Connection String kopieren**
  - Settings → Database → Connection String (Transaction Mode)
  - Format: `postgresql://postgres.PROJECT_ID:PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres`

- [ ] **DB Password in Secret Manager speichern**
  ```bash
  echo -n "YOUR_SUPABASE_PASSWORD" | gcloud secrets create DB_PASSWORD \
    --data-file=- \
    --replication-policy="automatic"
  ```

- [ ] **RLS Policies aktiviert verifizieren**
  - Supabase Console → Database → Policies
  - 36 Tables sollten Policies haben

- [ ] **Backups verifizieren**
  - Supabase Console → Database → Backups
  - 7 Tage PITR aktiv

---

### Phase 2: Backend Deployment

#### Code Vorbereitung

- [ ] **Environment Variables in `cloudbuild.yaml` aktualisieren**
  ```yaml
  # Öffne cloudbuild.yaml und aktualisiere:
  - '--set-cloudsql-instances=${_CLOUD_SQL_CONNECTION}'  # ENTFERNEN (Supabase)
  - '--set-env-vars=DJANGO_SETTINGS_MODULE=config.settings.production'
  - '--set-env-vars=ALLOWED_HOSTS=draftcraft-XXXXXX-ew.a.run.app,your-domain.com'
  - '--set-env-vars=DB_HOST=aws-0-eu-west-1.pooler.supabase.com'
  - '--set-env-vars=DB_PORT=6543'
  - '--set-env-vars=DB_NAME=postgres'
  - '--set-env-vars=DB_USER=postgres.YOUR_PROJECT_ID'
  - '--set-env-vars=DB_SSLMODE=require'
  - '--set-env-vars=GCS_BUCKET_NAME=draftcraft-media-prod'
  ```

- [ ] **CORS Origins in `production.py` setzen**
  ```python
  # backend/config/settings/production.py
  CORS_ALLOWED_ORIGINS = [
      'https://your-domain.com',
      'https://draftcraft-XXXXXX-ew.a.run.app',  # Cloud Run URL
  ]
  ```

- [ ] **`backend/config/settings/production.py` prüfen**
  - SECRET_KEY aus Environment ✅
  - DEBUG = False ✅
  - ALLOWED_HOSTS aus Environment ✅
  - Supabase Database Config ✅

#### Docker Build & Deploy

- [ ] **Lokal Docker Build testen**
  ```bash
  cd C:\Dev\Projects\Web\DraftcraftV1
  docker build -t draftcraft-backend:test .
  docker run -p 8000:8000 --env-file .env.production draftcraft-backend:test
  ```

- [ ] **Tests ausführen**
  ```bash
  docker run draftcraft-backend:test pytest
  # Expected: 97/107 tests passing (91%)
  ```

- [ ] **Cloud Build triggern**
  ```bash
  gcloud builds submit --config=cloudbuild.yaml --region=europe-west3
  ```

- [ ] **Deployment verifizieren**
  ```bash
  gcloud run services describe draftcraft --region=europe-west3
  # Check: Status = READY
  ```

- [ ] **Backend Health Check**
  ```bash
  curl https://draftcraft-XXXXXX-ew.a.run.app/health/
  # Expected: {"status": "healthy"}

  curl https://draftcraft-XXXXXX-ew.a.run.app/api/v1/health/
  # Expected: {"database": "healthy", "cache": "..."}
  ```

- [ ] **Django Admin Login testen**
  ```bash
  # Öffne: https://draftcraft-XXXXXX-ew.a.run.app/admin/
  # Username: admin
  # Password: (aus Secret Manager oder neu erstellen)
  ```

- [ ] **Django Superuser erstellen** (falls nötig)
  ```bash
  gcloud run services update draftcraft --region=europe-west3 --command=/bin/bash
  python manage.py createsuperuser
  ```

---

### Phase 3: Frontend Deployment

#### Code Vorbereitung

- [ ] **`.env.production` aktualisieren**
  ```bash
  # frontend_new/.env.production
  VITE_API_URL=https://draftcraft-XXXXXX-ew.a.run.app
  NODE_ENV=production
  ```

- [ ] **Frontend lokal bauen und testen**
  ```bash
  cd frontend_new
  npm run build
  # Check: dist/ Verzeichnis erstellt
  ```

- [ ] **Dockerfile testen**
  ```bash
  docker build -t draftcraft-frontend:test -f Dockerfile \
    --build-arg VITE_API_URL=https://draftcraft-XXXXXX-ew.a.run.app .

  docker run -p 8080:8080 draftcraft-frontend:test
  # Öffne: http://localhost:8080
  ```

#### Deploy Options

**Option A: Google Cloud Storage + CDN (Empfohlen für Static SPA)**

- [ ] **Build Artefakte hochladen**
  ```bash
  cd frontend_new
  npm run build
  gsutil -m rsync -r -d dist/ gs://draftcraft-static-prod/
  ```

- [ ] **Cloud CDN aktivieren**
  ```bash
  gcloud compute backend-buckets create draftcraft-frontend-bucket \
    --gcs-bucket-name=draftcraft-static-prod

  gcloud compute url-maps create draftcraft-frontend-map \
    --default-backend-bucket=draftcraft-frontend-bucket

  gcloud compute target-https-proxies create draftcraft-frontend-proxy \
    --url-map=draftcraft-frontend-map \
    --ssl-certificates=YOUR_SSL_CERT

  gcloud compute forwarding-rules create draftcraft-frontend-rule \
    --global \
    --target-https-proxy=draftcraft-frontend-proxy \
    --ports=443
  ```

**Option B: Firebase Hosting (Einfacher)**

- [ ] **Firebase CLI installieren**
  ```bash
  npm install -g firebase-tools
  firebase login
  ```

- [ ] **Firebase Projekt initialisieren**
  ```bash
  cd frontend_new
  firebase init hosting
  # Public directory: dist
  # Single-page app: Yes
  # GitHub deploys: No
  ```

- [ ] **Deployen**
  ```bash
  npm run build
  firebase deploy --only hosting
  ```

- [ ] **Custom Domain hinzufügen** (optional)
  ```bash
  firebase hosting:channel:deploy production
  # Firebase Console → Hosting → Add custom domain
  ```

**Option C: Cloud Run (Wenn dynamisches Rendering nötig)**

- [ ] **Docker Image bauen**
  ```bash
  cd frontend_new
  docker build -t gcr.io/draftcraft-prod/draftcraft-frontend:latest .
  docker push gcr.io/draftcraft-prod/draftcraft-frontend:latest
  ```

- [ ] **Cloud Run Service erstellen**
  ```bash
  gcloud run deploy draftcraft-frontend \
    --image=gcr.io/draftcraft-prod/draftcraft-frontend:latest \
    --region=europe-west3 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --port=8080 \
    --set-env-vars=VITE_API_URL=https://draftcraft-XXXXXX-ew.a.run.app
  ```

#### Frontend Health Check

- [ ] **Website laden**
  - Öffne: https://your-domain.com oder Cloud Run URL
  - Check: Keine Console Errors

- [ ] **Login testen**
  - Navigiere zu /login
  - Login mit Test-User
  - Check: Token in LocalStorage

- [ ] **Document Upload testen**
  - Navigiere zu /documents
  - Upload Test PDF
  - Check: Processing Status → Completed

- [ ] **Admin Dashboard testen**
  - Navigiere zu /admin/dashboard
  - Check: Stats laden korrekt
  - Check: Recent Activity angezeigt

---

### Phase 4: Security Hardening

#### SSL/TLS

- [ ] **Custom Domain SSL Zertifikat**
  ```bash
  # Cloud Run stellt automatisch Let's Encrypt Zertifikate aus
  gcloud run services update draftcraft \
    --region=europe-west3 \
    --custom-domain=api.your-domain.com
  ```

- [ ] **DNS Records aktualisieren**
  - A Record: api.your-domain.com → Cloud Run IP
  - CNAME Record: www.your-domain.com → Cloud Run URL

#### CORS & Security Headers

- [ ] **CORS Production Origins testen**
  ```bash
  curl -H "Origin: https://your-domain.com" \
       -H "Access-Control-Request-Method: POST" \
       -H "Access-Control-Request-Headers: Authorization" \
       -X OPTIONS \
       https://api.your-domain.com/api/v1/documents/

  # Expected: Access-Control-Allow-Origin: https://your-domain.com
  ```

- [ ] **Security Headers verifizieren**
  ```bash
  curl -I https://your-domain.com
  # Check:
  # - X-Frame-Options: SAMEORIGIN
  # - X-Content-Type-Options: nosniff
  # - X-XSS-Protection: 1; mode=block
  ```

#### Rate Limiting (Backend)

- [ ] **Django Ratelimit installieren**
  ```bash
  # backend/requirements/production.txt
  echo "django-ratelimit==4.1.0" >> backend/requirements/production.txt
  ```

- [ ] **Ratelimit Middleware hinzufügen**
  ```python
  # backend/config/settings/production.py
  MIDDLEWARE = [
      # ...
      'django_ratelimit.middleware.RatelimitMiddleware',
  ]

  # Ratelimit Config
  RATELIMIT_ENABLE = True
  RATELIMIT_USE_CACHE = 'default'  # Redis
  ```

- [ ] **API Endpoints schützen**
  ```python
  # backend/api/v1/views.py
  from django_ratelimit.decorators import ratelimit

  @ratelimit(key='ip', rate='100/h', method='POST')
  def document_upload_view(request):
      # ...
  ```

#### DSGVO Compliance

- [ ] **Cookie Consent Banner hinzufügen** (Frontend)
  - npm install react-cookie-consent
  - Component erstellen

- [ ] **Privacy Policy Page erstellen**
  - /privacy Route
  - Datenschutzerklärung Text (Anwalt konsultieren!)

- [ ] **Data Export Endpoint implementieren** (Backend)
  ```python
  # backend/api/v1/views.py
  @api_view(['GET'])
  def export_user_data(request):
      # DSGVO Art. 20: Datenübertragbarkeit
      # Return JSON with all user data
  ```

- [ ] **Data Deletion Endpoint implementieren** (Backend)
  ```python
  # backend/api/v1/views.py
  @api_view(['DELETE'])
  def delete_user_data(request):
      # DSGVO Art. 17: Recht auf Löschung
      # Mark user for deletion, async cleanup
  ```

---

### Phase 5: Monitoring & Observability

#### Sentry Error Tracking

- [ ] **Sentry Projekt erstellen**
  - [https://sentry.io/signup/](https://sentry.io/signup/)
  - Projekt: draftcraft-prod

- [ ] **Sentry DSN in Secret Manager speichern**
  ```bash
  echo -n "YOUR_SENTRY_DSN" | gcloud secrets create SENTRY_DSN \
    --data-file=- \
    --replication-policy="automatic"
  ```

- [ ] **Sentry Backend Integration testen**
  ```python
  # Test Error
  def test_sentry(request):
      1 / 0  # Trigger error
  ```

- [ ] **Sentry Frontend Integration**
  ```bash
  npm install @sentry/react
  ```

  ```typescript
  // frontend_new/src/main.tsx
  import * as Sentry from '@sentry/react'

  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: 'production',
    tracesSampleRate: 0.1,
  })
  ```

#### Cloud Monitoring

- [ ] **Uptime Check erstellen**
  ```bash
  gcloud monitoring uptime-configs create draftcraft-api-health \
    --resource-labels=project_id=draftcraft-prod \
    --http-check-path=/health/ \
    --monitored-resource=uptime-check-config
  ```

- [ ] **Alert Policy erstellen**
  ```bash
  # Console: Monitoring → Alerting → Create Policy
  # Condition: Uptime Check Failure
  # Notification: Email an admin@your-domain.com
  ```

#### Logging

- [ ] **Cloud Logging testen**
  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=draftcraft" \
    --limit 50 \
    --format json
  ```

- [ ] **Log-basierte Metriken erstellen**
  - Console: Logging → Metrics → Create Metric
  - Metric 1: 500 Errors Count
  - Metric 2: Average Response Time
  - Metric 3: Document Processing Time

---

### Phase 6: Performance Optimization (Optional)

#### Redis / Memorystore

- [ ] **Memorystore Redis Instanz erstellen** (wenn Celery benötigt)
  ```bash
  gcloud redis instances create draftcraft-redis \
    --size=1 \
    --region=europe-west3 \
    --redis-version=redis_7_0 \
    --tier=basic
  ```

- [ ] **Redis URL in Cloud Run setzen**
  ```bash
  REDIS_HOST=$(gcloud redis instances describe draftcraft-redis \
    --region=europe-west3 \
    --format="value(host)")

  gcloud run services update draftcraft \
    --region=europe-west3 \
    --set-env-vars=REDIS_URL=redis://$REDIS_HOST:6379/0
  ```

#### CDN für API (Optional)

- [ ] **Cloud CDN für API aktivieren**
  ```bash
  # Nur für GET Requests sinnvoll
  # Console: Network Services → Cloud CDN → Add Origin
  ```

---

## 🧪 Post-Deployment Tests

### Smoke Tests

- [ ] **Backend Health Check**
  ```bash
  curl https://api.your-domain.com/health/
  curl https://api.your-domain.com/api/v1/health/
  ```

- [ ] **Frontend Ladezeit**
  - Öffne: https://your-domain.com
  - Chrome DevTools → Performance
  - Target: <3s Initial Load

- [ ] **Document Upload E2E**
  1. Login
  2. Upload Test PDF (Invoice)
  3. Wait for Processing
  4. Check Extraction Results
  5. Generate Proposal
  6. Download PDF

- [ ] **Admin Dashboard**
  1. Login als Admin
  2. Navigate to /admin/dashboard
  3. Check Stats Display
  4. Check Pattern Management

- [ ] **API Authentication**
  ```bash
  # Ohne Token → 401
  curl https://api.your-domain.com/api/v1/documents/

  # Mit Token → 200
  curl -H "Authorization: Token YOUR_TOKEN" \
    https://api.your-domain.com/api/v1/documents/
  ```

### Load Testing (Optional)

- [ ] **Apache Bench Test**
  ```bash
  ab -n 1000 -c 10 https://api.your-domain.com/health/
  # Target: <200ms average response time
  ```

- [ ] **Document Upload Stress Test**
  ```bash
  # Use locust.io or k6.io
  # Simulate 10 concurrent users uploading documents
  ```

---

## 📊 Success Criteria

### Backend

- [x] Health checks return 200 OK
- [x] Django Admin accessible
- [x] Database connection working
- [x] Media files upload to Cloud Storage
- [x] Secrets loaded from Secret Manager
- [x] Logging to Cloud Logging

### Frontend

- [x] Website loads in <3s
- [x] No console errors
- [x] API calls reach backend
- [x] Authentication flow works
- [x] Document upload successful

### Security

- [x] HTTPS enforced
- [x] CORS configured correctly
- [x] Security headers present
- [x] No secrets in code
- [x] Rate limiting active

### Monitoring

- [x] Sentry receiving errors
- [x] Uptime checks configured
- [x] Alert policies active
- [x] Cloud Logging working

---

## 🚨 Rollback Plan

### Backend Rollback

```bash
# List deployments
gcloud run revisions list --service=draftcraft --region=europe-west3

# Rollback to previous revision
gcloud run services update-traffic draftcraft \
  --region=europe-west3 \
  --to-revisions=PREVIOUS_REVISION=100
```

### Frontend Rollback

**Option A: Cloud Storage**
```bash
# Keep backup of previous build
gsutil -m rsync -r gs://draftcraft-static-prod/ gs://draftcraft-static-prod-backup/
# Rollback
gsutil -m rsync -r gs://draftcraft-static-prod-backup/ gs://draftcraft-static-prod/
```

**Option B: Firebase Hosting**
```bash
firebase hosting:rollback
```

### Database Rollback

```bash
# Supabase Console → Database → Backups → Restore to PITR
# Timestamp: YYYY-MM-DD HH:MM:SS
```

---

## 📞 Emergency Contacts

- **Technical Lead:** YOUR_NAME (your@email.com)
- **GCP Support:** [https://console.cloud.google.com/support](https://console.cloud.google.com/support)
- **Supabase Support:** [https://supabase.com/support](https://supabase.com/support)
- **Sentry Support:** [https://sentry.io/support](https://sentry.io/support)

---

## 📝 Post-Deployment

- [ ] **Dokumentation aktualisieren**
  - Deployment URLs
  - Secret Names
  - Contact Info

- [ ] **Team Onboarding**
  - Access zu GCP Console
  - Access zu Supabase
  - Access zu Sentry

- [ ] **User Training**
  - Admin Dashboard Guide
  - Document Upload Workflow
  - Troubleshooting Common Issues

- [ ] **Monitoring Dashboard erstellen**
  - Google Cloud Monitoring Dashboard
  - Key Metrics: Requests/s, Errors, Latency
  - Link: [https://console.cloud.google.com/monitoring](https://console.cloud.google.com/monitoring)

---

**Checklist Status:** ⬜ Not Started
**Last Updated:** 2025-12-08
**Next Review:** Nach erstem Production Deployment
