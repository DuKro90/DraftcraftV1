#!/bin/bash
# DraftCraft Backend Deployment zu Google Cloud Run
#
# Dieses Script deployed das Django-Backend mit allen erforderlichen Environment-Variablen
# und nutzt Google Secret Manager für sensitive Daten.
#
# WICHTIG: Vor dem ersten Deployment:
# 1. Secrets im Secret Manager erstellen (siehe unten)
# 2. Variablen in diesem Script anpassen (PROJECT_ID, REGION, etc.)
# 3. Script ausführbar machen: chmod +x deploy-backend.sh
# 4. Deployment starten: ./deploy-backend.sh

set -e  # Exit bei Fehler

# ========================================
# KONFIGURATION - DIESE WERTE ANPASSEN!
# ========================================

PROJECT_ID="draftcraft-production"  # Ihre GCP Project-ID
REGION="europe-west3"               # Frankfurt (DSGVO-konform)
SERVICE_NAME="draftcraft-backend"

# Supabase Database (Free Tier)
# Diese Werte finden Sie in: Supabase Dashboard → Settings → Database
DB_HOST="aws-0-eu-central-1.pooler.supabase.com"  # Ihre Supabase Connection Pooler URL
DB_PORT="6543"                                     # Connection Pooler Port (6543 für Pooler, 5432 für Direct)
DB_NAME="postgres"                                 # Default Supabase DB name
DB_USER="postgres.YOUR_SUPABASE_PROJECT_REF"      # Format: postgres.PROJECT_REF
DB_SSLMODE="require"                              # Supabase benötigt SSL

# Frontend CORS (Vercel)
ALLOWED_HOSTS=".run.app,.vercel.app"
CORS_ALLOWED_ORIGINS="https://draftcraft-v1.vercel.app"

# Optional: Gemini API (für AI-Features)
GEMINI_API_KEY_SECRET="GEMINI_API_KEY"  # Secret Manager name (wenn vorhanden)

# ========================================
# SCHRITT 1: Secrets im Secret Manager erstellen (EINMALIG!)
# ========================================
# Diese Befehle nur beim ERSTEN Deployment ausführen!
# Danach auskommentieren oder überspringen.

echo "🔐 Checking if secrets exist..."

# SECRET_KEY generieren und speichern
# SECRET_VALUE=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# echo -n "$SECRET_VALUE" | gcloud secrets create DJANGO_SECRET_KEY \
#   --project=$PROJECT_ID \
#   --replication-policy="automatic"

# DB_PASSWORD (aus Supabase Dashboard → Settings → Database → Password)
# echo -n "YOUR_SUPABASE_PASSWORD" | gcloud secrets create DB_PASSWORD \
#   --project=$PROJECT_ID \
#   --replication-policy="automatic"

# Optional: Gemini API Key
# echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
#   --project=$PROJECT_ID \
#   --replication-policy="automatic"

# ENCRYPTION_KEY generieren (32 bytes base64)
# ENCRYPTION_KEY=$(python3 -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())")
# echo -n "$ENCRYPTION_KEY" | gcloud secrets create ENCRYPTION_KEY \
#   --project=$PROJECT_ID \
#   --replication-policy="automatic"

echo "✅ Secrets check complete (skip if already created)"

# ========================================
# SCHRITT 2: GCP Projekt aktivieren
# ========================================

echo "🚀 Setting GCP project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# ========================================
# SCHRITT 3: Cloud Run Deployment
# ========================================

echo "📦 Deploying to Cloud Run..."

gcloud run deploy $SERVICE_NAME \
  --source ./backend \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --service-account="${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars="DJANGO_SETTINGS_MODULE=config.settings.production" \
  --set-env-vars="ALLOWED_HOSTS=${ALLOWED_HOSTS}" \
  --set-env-vars="CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}" \
  --set-env-vars="DB_HOST=${DB_HOST}" \
  --set-env-vars="DB_PORT=${DB_PORT}" \
  --set-env-vars="DB_NAME=${DB_NAME}" \
  --set-env-vars="DB_USER=${DB_USER}" \
  --set-env-vars="DB_SSLMODE=${DB_SSLMODE}" \
  --set-secrets="SECRET_KEY=DJANGO_SECRET_KEY:latest" \
  --set-secrets="DB_PASSWORD=DB_PASSWORD:latest" \
  --set-secrets="ENCRYPTION_KEY=ENCRYPTION_KEY:latest" \
  --cpu=1 \
  --memory=512Mi \
  --timeout=300 \
  --max-instances=10 \
  --min-instances=0 \
  --concurrency=80

# Optional: Gemini API Key hinzufügen (falls AI-Features genutzt werden)
# Auskommentieren, wenn nicht benötigt:
# gcloud run services update $SERVICE_NAME \
#   --region $REGION \
#   --set-secrets="GEMINI_API_KEY=${GEMINI_API_KEY_SECRET}:latest"

echo ""
echo "✅ Deployment erfolgreich!"
echo ""
echo "🌐 Backend URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
echo ""
echo "📋 Nächste Schritte:"
echo "1. Backend-URL kopieren"
echo "2. In Vercel: VITE_API_URL Environment Variable setzen"
echo "3. Frontend auf Vercel neu deployen"
echo ""
