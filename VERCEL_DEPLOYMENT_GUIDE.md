# DraftCraft Deployment Guide: Vercel + Google Cloud Run

**Architecture:**
- 🎨 **Frontend:** Vercel (Global CDN)
- ⚙️ **Backend:** Google Cloud Run (europe-west3, Frankfurt)
- 🗄️ **Database:** Supabase PostgreSQL (eu-west-1, Frankfurt)

---

## 📦 Prerequisites

### 1. GitHub Repository
```bash
# Push code to GitHub
git remote set-url origin https://github.com/DuKro90/DraftcraftV1.git
git push -u origin master
```

### 2. Google Cloud Setup
- **Project:** draftcraftsupport
- **Region:** europe-west3 (Frankfurt - DSGVO compliant)
- **URL:** https://console.cloud.google.com/welcome?project=draftcraftsupport

### 3. Supabase Database
- **URL:** https://qnazxcdchsyorognwgfm.supabase.co
- **Region:** eu-west-1 (Frankfurt)
- **Connection:**
  - Direct: `qnazxcdchsyorognwgfm.supabase.co:5432`
  - Pooler: `qnazxcdchsyorognwgfm.supabase.co:6543` (Production)

---

## 🚀 Part 1: Backend Deployment (Google Cloud Run)

### Step 1: Prepare Environment Variables

Create a `.env.production` file (DO NOT commit!):

```bash
# Database (Supabase)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_supabase_password
DB_HOST=qnazxcdchsyorognwgfm.supabase.co
DB_PORT=6543  # Connection Pooler for production

# Django
SECRET_KEY=your_random_secret_key_here
ALLOWED_HOSTS=.run.app,draftcraft-v1.vercel.app
DJANGO_SETTINGS_MODULE=config.settings.production

# CORS (Vercel Frontend)
CORS_ALLOWED_ORIGINS=https://draftcraft-v1.vercel.app,https://draftcraft-v1-git-*.vercel.app

# GCP
GCP_PROJECT_ID=draftcraftsupport
GCS_BUCKET_NAME=draftcraft-documents-eu

# Optional: Email (SendGrid)
SENDGRID_API_KEY=your_sendgrid_key
EMAIL_HOST=smtp.sendgrid.net

# Optional: Monitoring
SENTRY_DSN=your_sentry_dsn
```

**Generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 2: Deploy to Cloud Run

```bash
# Navigate to backend directory
cd backend

# Set environment variables in Cloud Run
gcloud run deploy draftcraft-backend \
  --source . \
  --region europe-west3 \
  --allow-unauthenticated \
  --platform managed \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "$(cat .env.production | tr '\n' ',' | sed 's/,$//')"

# OR use Secret Manager (recommended for production):
# 1. Create secrets
gcloud secrets create django-secret-key --data-file=- <<< "your_secret_key"
gcloud secrets create db-password --data-file=- <<< "your_db_password"

# 2. Deploy with secrets
gcloud run deploy draftcraft-backend \
  --source . \
  --region europe-west3 \
  --allow-unauthenticated \
  --update-secrets DB_PASSWORD=db-password:latest \
  --update-secrets SECRET_KEY=django-secret-key:latest \
  --set-env-vars DB_HOST=qnazxcdchsyorognwgfm.supabase.co,DB_PORT=6543,DB_NAME=postgres,DB_USER=postgres
```

### Step 3: Get Backend URL

```bash
# After deployment, get the URL
gcloud run services describe draftcraft-backend --region europe-west3 --format='value(status.url)'

# Example output:
# https://draftcraft-backend-abc123xyz.run.app
```

**Save this URL** - you'll need it for Vercel!

### Step 4: Run Database Migrations

```bash
# Option 1: Via Cloud Run Job
gcloud run jobs create draftcraft-migrate \
  --region europe-west3 \
  --image gcr.io/draftcraftsupport/draftcraft-backend:latest \
  --command python,manage.py,migrate \
  --set-env-vars DJANGO_SETTINGS_MODULE=config.settings.production

gcloud run jobs execute draftcraft-migrate --region europe-west3

# Option 2: Via local connection (requires Supabase credentials)
export DATABASE_URL=postgresql://postgres:PASSWORD@qnazxcdchsyorognwgfm.supabase.co:5432/postgres
python manage.py migrate --settings=config.settings.production
```

---

## 🎨 Part 2: Frontend Deployment (Vercel)

### Step 1: Connect GitHub to Vercel

1. Go to https://vercel.com
2. Sign up/Login with GitHub
3. Click **"Add New Project"**
4. **Import Git Repository:**
   - Select: `DuKro90/DraftcraftV1`
   - Framework Preset: **Vite**
   - Root Directory: `frontend_new`

### Step 2: Configure Build Settings

**In Vercel Project Settings:**

```bash
# Build & Development Settings
Framework Preset: Vite
Root Directory: frontend_new
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### Step 3: Add Environment Variables

**In Vercel → Settings → Environment Variables:**

| Variable | Value | Environment |
|----------|-------|-------------|
| `VITE_API_URL` | `https://draftcraft-backend-abc123xyz.run.app` | Production |
| `VITE_SUPABASE_URL` | `https://qnazxcdchsyorognwgfm.supabase.co` | All |
| `VITE_SUPABASE_ANON_KEY` | `your_anon_key` | All |
| `NODE_ENV` | `production` | Production |

**Get Supabase Anon Key:**
```bash
# Go to: https://supabase.com/dashboard/project/qnazxcdchsyorognwgfm/settings/api
# Copy: "anon" "public" key
```

### Step 4: Deploy

```bash
# Vercel will auto-deploy on git push
git push origin master

# OR deploy manually via Vercel CLI
npm i -g vercel
cd frontend_new
vercel --prod
```

### Step 5: Get Frontend URL

After deployment, Vercel provides:
- **Production:** `https://draftcraft-v1.vercel.app`
- **Preview Deploys:** `https://draftcraft-v1-git-BRANCH.vercel.app`

---

## 🔗 Part 3: Connect Frontend & Backend

### Update Backend CORS (if needed)

If your Vercel URL is different, update backend:

```bash
# Update production.py CORS settings
gcloud run services update draftcraft-backend \
  --region europe-west3 \
  --update-env-vars CORS_ALLOWED_ORIGINS=https://draftcraft-v1.vercel.app,https://draftcraft-v1-git-*.vercel.app
```

### Test Connection

```bash
# Test backend health
curl https://draftcraft-backend-abc123xyz.run.app/api/v1/health/

# Test from frontend
# Open: https://draftcraft-v1.vercel.app
# Check browser console for API calls
```

---

## 🧪 Testing the Deployment

### 1. Backend Health Check

```bash
curl https://draftcraft-backend-abc123xyz.run.app/api/v1/health/

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-09T..."
}
```

### 2. Frontend Functionality

**Test these features:**
- ✅ Login page loads
- ✅ Registration form works
- ✅ Document upload (check API calls in Network tab)
- ✅ Dashboard displays data
- ✅ No CORS errors in browser console

### 3. Database Connection

```bash
# Check backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=draftcraft-backend" \
  --limit 50 \
  --format json

# Look for:
# - "Database connection successful"
# - No "FATAL: no pg_hba.conf entry" errors
```

---

## 📊 Production Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Internet                         │
└────────────┬────────────────────────┬────────────────┘
             │                        │
             ▼                        ▼
   ┌─────────────────┐      ┌──────────────────┐
   │  Vercel CDN     │      │  Google Cloud    │
   │  (Global)       │      │  Load Balancer   │
   │                 │      │  (europe-west3)  │
   │  Frontend       │─────▶│                  │
   │  React/Vite     │ API  │  Cloud Run       │
   └─────────────────┘      │  Django          │
                            └────────┬─────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  Supabase       │
                            │  PostgreSQL     │
                            │  (eu-west-1)    │
                            │  + RLS Security │
                            └─────────────────┘
```

**Latency:**
- Frontend (Vercel CDN): ~10-50ms (global)
- Backend (Cloud Run): ~100-200ms (Europe)
- Database (Supabase): ~5-20ms (same region as backend)

---

## 🔒 Security Checklist

### Before Going Live:

- [ ] **CORS:** Only allow `https://draftcraft-v1.vercel.app`
- [ ] **HTTPS:** Force SSL (already enabled on Cloud Run + Vercel)
- [ ] **Secrets:** Use Google Secret Manager (not env vars)
- [ ] **Database:** Enable Supabase RLS policies
- [ ] **Rate Limiting:** Enable in Django REST Framework
- [ ] **API Keys:** Rotate Supabase anon key if exposed
- [ ] **Monitoring:** Set up Sentry for error tracking
- [ ] **Backups:** Enable Supabase daily backups

### DSGVO Compliance:

- [x] **Data Location:** EU only (frankfurt/eu-west-1)
- [ ] **Privacy Policy:** Add to frontend
- [ ] **Cookie Consent:** Implement if tracking users
- [ ] **Data Retention:** 365 days (configured in Django)
- [ ] **Right to Deletion:** Implement user data export/delete endpoints

---

## 💰 Cost Estimation

### Monthly Costs (Low Traffic: ~1000 users/month)

| Service | Tier | Cost |
|---------|------|------|
| **Vercel** | Hobby (Free) | **$0** |
| **Google Cloud Run** | 2M requests free | **$0-5** |
| **Supabase** | Free Tier | **$0** |
| **Total** | | **~$0-5/month** |

### Scaling Costs (High Traffic: ~10k users/month)

| Service | Tier | Cost |
|---------|------|------|
| **Vercel** | Pro (if needed) | $20/month |
| **Google Cloud Run** | Pay-as-you-go | $20-50/month |
| **Supabase** | Pro | $25/month |
| **Total** | | **~$65-95/month** |

---

## 🐛 Troubleshooting

### Issue 1: CORS Errors

**Symptom:** Browser console shows `Access-Control-Allow-Origin` error

**Fix:**
```bash
# Check backend CORS settings
gcloud run services describe draftcraft-backend --region europe-west3 --format='value(spec.template.spec.containers[0].env)'

# Update if needed
gcloud run services update draftcraft-backend \
  --region europe-west3 \
  --update-env-vars CORS_ALLOWED_ORIGINS=https://draftcraft-v1.vercel.app
```

### Issue 2: Database Connection Failed

**Symptom:** Backend logs show `FATAL: no pg_hba.conf entry`

**Fix:**
```bash
# 1. Use Connection Pooler (port 6543, not 5432)
# 2. Check Supabase firewall:
#    Settings → Database → Connection Pooling → Enable
# 3. Update DB_HOST:
DB_HOST=qnazxcdchsyorognwgfm.supabase.co
DB_PORT=6543
```

### Issue 3: Frontend Build Fails

**Symptom:** Vercel build fails with `Module not found`

**Fix:**
```bash
# 1. Check package.json in frontend_new/
# 2. Ensure all dependencies are listed
# 3. Clear Vercel cache: Settings → General → Clear Cache
# 4. Redeploy
```

### Issue 4: API 404 Errors

**Symptom:** Frontend can't reach backend endpoints

**Fix:**
```bash
# 1. Verify VITE_API_URL in Vercel env vars
# 2. Check backend URL is correct:
curl https://draftcraft-backend-abc123xyz.run.app/api/v1/documents/

# 3. Check Django URL routing:
python manage.py show_urls | grep api/v1
```

---

## 🔄 Continuous Deployment

### Automatic Deployments:

**Frontend (Vercel):**
```bash
# Auto-deploys on every push to master
git push origin master
# → https://draftcraft-v1.vercel.app (Production)

# Preview deploys on feature branches
git checkout -b feature/new-dashboard
git push origin feature/new-dashboard
# → https://draftcraft-v1-git-feature-new-dashboard.vercel.app
```

**Backend (Cloud Run):**
```bash
# Option 1: Manual deploy
cd backend
gcloud run deploy draftcraft-backend --source . --region europe-west3

# Option 2: Set up Cloud Build trigger (automated)
# See: https://cloud.google.com/run/docs/continuous-deployment-with-cloud-build
```

---

## 📞 Support & Next Steps

### Add Custom Domain (Optional)

**Buy Domain:** draftcraft.de (~10€/year)

**Configure DNS:**
```bash
# Vercel:
# 1. Settings → Domains → Add Domain
# 2. Add CNAME: draftcraft.de → cname.vercel-dns.com

# Cloud Run:
# 1. Cloud Run → Manage Custom Domains
# 2. Add: api.draftcraft.de → draftcraft-backend
```

**Result:**
- `https://draftcraft.de` → Frontend
- `https://api.draftcraft.de` → Backend

### Enable Monitoring

**Sentry (Error Tracking):**
```bash
# 1. Sign up: https://sentry.io
# 2. Add DSN to backend env vars
# 3. Already configured in production.py
```

**Vercel Analytics:**
```bash
# 1. Enable in Vercel Dashboard
# 2. Free tier: 500k events/month
```

---

**Last Updated:** 2025-12-09
**Status:** ✅ Ready for deployment
**Architecture:** Vercel (Frontend) + Cloud Run (Backend) + Supabase (Database)
