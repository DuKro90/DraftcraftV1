# 🚀 DraftCraft Backend Deployment - Quick Start

**Status:** Backend-Fixes sind committed und gepusht. Deployment-ready!
**Zeitaufwand:** 10-15 Minuten (erstes Mal), 2 Minuten (nachfolgende Deployments)

---

## ⚡ Schnellstart (Copy & Paste)

### 1️⃣ Supabase Credentials holen

Öffnen Sie Ihr [Supabase Dashboard](https://supabase.com/dashboard):

```bash
# Navigation: Project → Settings → Database → Connection Info

# Notieren Sie:
DB_HOST=aws-0-eu-central-1.pooler.supabase.com  # Connection Pooler (Transaction Mode)
DB_PORT=6543                                     # Pooler Port
DB_NAME=postgres                                 # Default
DB_USER=postgres.YOUR_PROJECT_REF               # Ersetzen: YOUR_PROJECT_REF
DB_PASSWORD=YOUR_SUPABASE_PASSWORD              # Aus "Database Password" Feld
```

### 2️⃣ Secrets erstellen (NUR BEIM ERSTEN MAL!)

```bash
# GCP Projekt aktivieren
gcloud config set project draftcraft-production  # Ihre Project-ID anpassen!

# Django SECRET_KEY generieren und speichern
SECRET_VALUE=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
echo -n "$SECRET_VALUE" | gcloud secrets create DJANGO_SECRET_KEY \
  --replication-policy="automatic"

# Supabase DB_PASSWORD speichern
echo -n "YOUR_SUPABASE_PASSWORD" | gcloud secrets create DB_PASSWORD \
  --replication-policy="automatic"

# Encryption Key generieren
ENCRYPTION_KEY=$(python3 -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())")
echo -n "$ENCRYPTION_KEY" | gcloud secrets create ENCRYPTION_KEY \
  --replication-policy="automatic"

# Optional: Gemini API Key (falls AI-Features genutzt werden)
# echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
#   --replication-policy="automatic"
```

### 3️⃣ Backend deployen

**Option A: Mit vorbereitetem Script (empfohlen)**

```bash
# 1. Script anpassen
nano deploy-backend.sh
# Ersetzen Sie:
#   - PROJECT_ID="draftcraft-production" → Ihre GCP Project-ID
#   - DB_HOST, DB_USER → Ihre Supabase-Werte (siehe Schritt 1)

# 2. Ausführbar machen
chmod +x deploy-backend.sh

# 3. Deployen!
./deploy-backend.sh
```

**Option B: Manueller Befehl (Copy & Paste, Werte anpassen)**

```bash
# WICHTIG: Ersetzen Sie ALLE Werte in GROSSBUCHSTABEN!

gcloud run deploy draftcraft-backend \
  --source ./backend \
  --region europe-west3 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="DJANGO_SETTINGS_MODULE=config.settings.production" \
  --set-env-vars="ALLOWED_HOSTS=.run.app,.vercel.app" \
  --set-env-vars="CORS_ALLOWED_ORIGINS=https://draftcraft-v1.vercel.app" \
  --set-env-vars="DB_HOST=YOUR_SUPABASE_HOST" \
  --set-env-vars="DB_PORT=6543" \
  --set-env-vars="DB_NAME=postgres" \
  --set-env-vars="DB_USER=postgres.YOUR_PROJECT_REF" \
  --set-env-vars="DB_SSLMODE=require" \
  --set-secrets="SECRET_KEY=DJANGO_SECRET_KEY:latest" \
  --set-secrets="DB_PASSWORD=DB_PASSWORD:latest" \
  --set-secrets="ENCRYPTION_KEY=ENCRYPTION_KEY:latest" \
  --cpu=1 \
  --memory=512Mi \
  --timeout=300 \
  --max-instances=10 \
  --min-instances=0 \
  --concurrency=80
```

### 4️⃣ Backend-URL notieren

Nach erfolgreichem Deployment wird die URL angezeigt:

```bash
Service [draftcraft-backend] revision [draftcraft-backend-00001-xyz] has been deployed
and is serving 100 percent of traffic.
Service URL: https://draftcraft-backend-920983333114-ew.a.run.app
```

**Diese URL kopieren!** ✂️

### 5️⃣ Vercel Frontend aktualisieren

```bash
# Option A: Vercel Dashboard (empfohlen)
# 1. Öffnen: https://vercel.com/your-team/draftcraft-v1/settings/environment-variables
# 2. Neue Variable hinzufügen:
#    Name: VITE_API_URL
#    Value: https://draftcraft-backend-920983333114-ew.a.run.app  # Ihre Backend-URL
# 3. Redeploy auslösen

# Option B: Vercel CLI
vercel env add VITE_API_URL production
# Paste your backend URL when prompted

# Redeploy
vercel --prod
```

---

## ✅ Erfolgskontrolle

### Backend testen

```bash
# Health Check
curl https://YOUR_BACKEND_URL/api/v1/admin/dashboard/health/

# Erwartete Antwort:
{
  "overall": "healthy",
  "components": {
    "database": {"status": "healthy", ...},
    "cache": {"status": "healthy", ...},
    "processing": {"status": "healthy", ...}
  }
}
```

### Frontend testen

1. Öffnen: `https://draftcraft-v1.vercel.app` (oder Ihre Vercel-URL)
2. Browser DevTools öffnen (F12)
3. Console-Tab prüfen:
   - ✅ **KEINE CORS-Errors** mehr!
   - ✅ **KEINE 404-Errors** für vite.svg!
   - ✅ API-Calls erfolgreich (200 OK)

---

## 🔧 Troubleshooting

### Problem: "Permission denied" bei Secret Manager

```bash
# Service Account Permissions hinzufügen
gcloud projects add-iam-policy-binding draftcraft-production \
  --member="serviceAccount:draftcraft-backend-sa@draftcraft-production.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Problem: "Service account does not exist"

```bash
# Service Account erstellen
gcloud iam service-accounts create draftcraft-backend-sa \
  --display-name="DraftCraft Backend Service Account"

# Secret Manager Access gewähren
gcloud projects add-iam-policy-binding draftcraft-production \
  --member="serviceAccount:draftcraft-backend-sa@draftcraft-production.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Problem: "Cannot connect to database"

```bash
# 1. Supabase Connection String prüfen
# Dashboard → Settings → Database → Connection String (URI)
# Format: postgresql://postgres.REF:[PASSWORD]@HOST:6543/postgres

# 2. Connection Pooler verwenden (nicht Direct Connection!)
DB_HOST=aws-0-eu-central-1.pooler.supabase.com  # ✅ Pooler
DB_PORT=6543                                     # ✅ Pooler Port
# NICHT:
# DB_HOST=db.PROJECT.supabase.co  ❌ Direct Connection
# DB_PORT=5432                    ❌ Direct Port
```

### Problem: "CORS errors persist after deployment"

```bash
# 1. Stelle sicher, dass Backend neu deployed wurde
gcloud run services describe draftcraft-backend --region europe-west3 \
  | grep "Last modified"

# 2. Prüfe CORS-Konfiguration im Backend
gcloud run services describe draftcraft-backend --region europe-west3 \
  | grep CORS_ALLOWED_ORIGINS

# 3. Frontend muss Vercel-URL verwenden (nicht localhost!)
# In Vercel Environment Variables prüfen:
# VITE_API_URL = https://draftcraft-backend-XXX.run.app
```

---

## 📊 Was wurde behoben?

### 1. CORS-Konfiguration (production.py:57-73)

**Vorher (funktioniert nicht):**
```python
CORS_ALLOWED_ORIGINS = [
    'https://draftcraft-v1-*.vercel.app',  # ❌ Wildcards nicht unterstützt!
]
```

**Nachher (funktioniert):**
```python
CORS_ALLOWED_ORIGINS = [
    'https://draftcraft-v1.vercel.app',  # ✅ Exakte URL
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://draftcraft-v1-[a-zA-Z0-9-]+\.vercel\.app$',  # ✅ Regex für Previews
]
```

### 2. Fehlende Assets (frontend_new/public/)

**Erstellt:**
- `vite.svg` - DraftCraft Favicon (behebt 404-Fehler)

### 3. Environment-Variable-Validation

**Problem:** Backend-Start scheiterte wegen fehlender Env-Vars
**Lösung:** Vollständige Env-Var-Konfiguration im Deployment-Script

---

## 🎯 Deployment Checklist

- [ ] Supabase Credentials kopiert (DB_HOST, DB_USER, DB_PASSWORD)
- [ ] GCP Secrets erstellt (DJANGO_SECRET_KEY, DB_PASSWORD, ENCRYPTION_KEY)
- [ ] Backend deployed (via `deploy-backend.sh` oder manuell)
- [ ] Backend-URL kopiert
- [ ] Vercel Env-Variable gesetzt (VITE_API_URL)
- [ ] Frontend redeployed
- [ ] Tests durchgeführt (Health Check, Frontend Console)

---

## 📚 Weiterführende Dokumentation

- **Deployment-Details:** `DEPLOYMENT_CHECKLIST.md`
- **Supabase-Setup:** `.claude/guides/supabase-migration-guide.md`
- **Cloud Run Best Practices:** `DEPLOYMENT_GUIDE.md`
- **Phase 4D Architektur:** `PHASE_4D_COMPLETE.md`

---

**Letzte Aktualisierung:** 2025-12-11
**Git Commit:** `d84ed22` - "fix(cors): Fix CORS configuration for Vercel deployment"
**Status:** ✅ Ready to deploy
