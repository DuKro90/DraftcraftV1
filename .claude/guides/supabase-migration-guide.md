# Supabase Migration Guide - Step by Step

**Ziel:** Migration von lokalem Docker PostgreSQL zu Supabase Free Tier
**Dauer:** 30-45 Minuten
**Downtime:** 0 Minuten (paralleler Betrieb möglich)
**Kosten:** $0/Monat (Free Tier)

---

## ✅ Voraussetzungen

Bevor Sie starten, stellen Sie sicher:

- [ ] Sie haben einen Supabase Account: https://supabase.com
- [ ] PostgreSQL Client installiert: `psql --version` (sollte 15.x zeigen)
- [ ] Zugriff auf Ihr lokales Docker-Setup
- [ ] Backup erstellt (siehe unten)

**Installation psql (falls noch nicht vorhanden):**

```bash
# Windows (via Chocolatey)
choco install postgresql

# Oder: Download von https://www.postgresql.org/download/windows/
# Installieren Sie nur "Command Line Tools"
```

---

## 📋 Phase 1: Backup & Vorbereitung (10 Min)

### Schritt 1.1: Aktuellen Datenbestand sichern

```bash
# Terminal öffnen in: C:\Users\dusti\.claude-worktrees\DraftcraftV1\great-roentgen

# 1. Prüfen ob Docker läuft
docker-compose ps

# Erwartete Ausgabe:
# NAME                     STATUS
# draftcraft_postgres      Up
# draftcraft_redis         Up
# draftcraft_web           Up

# 2. Backup erstellen
docker-compose exec postgres pg_dump -U postgres -Fc draftcraft_dev > backups/pre_supabase_backup_$(date +%Y%m%d).dump

# Falls 'backups' Ordner nicht existiert:
mkdir backups

# 3. Backup-Größe prüfen
dir backups

# Erwartete Größe:
# - Leere DB: ~50 KB
# - Mit Testdaten: 100 KB - 5 MB
# - Production: Variiert
```

### Schritt 1.2: Datenbank-Statistiken erfassen

```bash
# Verbindung zu lokaler DB
docker-compose exec postgres psql -U postgres -d draftcraft_dev

# Folgende Queries ausführen:
```

```sql
-- 1. Tabellen-Anzahl
SELECT count(*) FROM information_schema.tables
WHERE table_schema = 'public';

-- 2. Datensatz-Counts (wichtige Tabellen)
SELECT
    'documents' as table_name, COUNT(*) as rows FROM documents_document
UNION ALL
SELECT 'extractions', COUNT(*) FROM extraction_extractionresult
UNION ALL
SELECT 'proposals', COUNT(*) FROM proposals_proposal;

-- 3. Database Size
SELECT pg_size_pretty(pg_database_size('draftcraft_dev')) as db_size;

-- 4. Verwendete Extensions
SELECT extname, extversion FROM pg_extension;

-- 5. Exit
\q
```

**📝 Notieren Sie die Ausgabe:**
```
Tabellen-Anzahl: ___________
Documents: ___________
Extractions: ___________
Proposals: ___________
DB Size: ___________
Extensions: ___________
```

---

## 🌐 Phase 2: Supabase Setup (15 Min)

### Schritt 2.1: Supabase Project erstellen

1. **Browser öffnen:** https://supabase.com/dashboard
2. **Login** mit Ihrem Account
3. **Klick auf "New Project"**

**Projekt-Einstellungen:**
```
Project Name:        draftcraft-prod
Database Password:   [GENERIEREN SIE EIN STARKES PASSWORD!]
                     Mindestens 20 Zeichen, Mix aus Buchstaben/Zahlen/Symbolen
                     WICHTIG: Password notieren - wird nur einmal angezeigt!
Region:              Europe West (eu-west-1) ✅ Frankfurt - DSGVO
Pricing Plan:        Free ($0/month)
```

4. **Klick auf "Create new project"**
5. **Warten** (2-3 Minuten) bis Status = "Active"

### Schritt 2.2: Connection Details kopieren

**Im Supabase Dashboard:**

1. Gehen Sie zu: **Settings** (linkes Menü) → **Database**
2. Scrollen zu: **Connection string**
3. Tab: **URI** auswählen

**Angezeigt wird:**
```
postgres://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres
```

**Extrahieren Sie folgende Werte:**
```bash
DB_HOST=db.abcdefghijklmnop.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[Ihr generiertes Password aus Schritt 2.1]
DB_PORT=5432
DB_SSLMODE=require
```

**📝 Speichern Sie diese in einem sicheren Ort (z.B. 1Password, Bitwarden)**

### Schritt 2.3: Connection Pooler Details (empfohlen für Production)

**Gleiche Seite, scrollen zu: "Connection pooling"**

1. **Mode:** Transaction
2. **Port:** 6543
3. **Connection String kopieren:**

```bash
# Für höhere Connections (Production):
DB_HOST_POOLED=aws-0-eu-west-1.pooler.supabase.com
DB_PORT_POOLED=6543
```

**Vorerst nutzen wir Direct Connection (Port 5432) - Pooler später für Production**

---

## 🔌 Phase 3: Connection Testing (5 Min)

### Schritt 3.1: Test mit psql

```bash
# Ersetzen Sie [YOUR-PASSWORD] mit Ihrem echten Password
psql "postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres"
```

**Erwartete Ausgabe:**
```
psql (15.x)
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256)
Type "help" for help.

postgres=>
```

**Falls Fehler:**

❌ **Error: "connection timeout"**
```bash
# Lösung: Firewall blockiert Port 5432
# Windows: Windows Defender Firewall > Ausgehende Regeln > PostgreSQL erlauben
```

❌ **Error: "password authentication failed"**
```bash
# Lösung: Password falsch - prüfen Sie Supabase Dashboard
# Settings > Database > Reset database password
```

❌ **Error: "SSL required"**
```bash
# Lösung: SSL-Modus fehlt
psql "postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres?sslmode=require"
```

### Schritt 3.2: Basis-Checks

**In der psql Session:**

```sql
-- 1. PostgreSQL Version
SELECT version();
-- Erwartung: PostgreSQL 15.x

-- 2. Verfügbare Extensions
SELECT * FROM pg_available_extensions WHERE name IN ('vector', 'postgis', 'uuid-ossp');
-- vector: ✅ Für ML (Phase 4)
-- uuid-ossp: ✅ Für UUIDs

-- 3. Current Database
SELECT current_database();
-- Erwartung: postgres

-- 4. Exit
\q
```

---

## 🔧 Phase 4: Django Configuration (5 Min)

### Schritt 4.1: Environment File erstellen

**Erstellen Sie: `.env.supabase`**

```bash
# In: C:\Users\dusti\.claude-worktrees\DraftcraftV1\great-roentgen\backend

# Kopieren Sie .env zu .env.supabase
copy .env .env.supabase

# Öffnen Sie .env.supabase in Editor
```

**Ersetzen Sie Database-Variablen:**

```bash
# ============================================================================
# DATABASE CONFIGURATION - SUPABASE
# ============================================================================
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[IHR-SUPABASE-PASSWORD]
DB_HOST=db.abcdefghijklmnop.supabase.co
DB_PORT=5432
DB_SSLMODE=require

# Optional: Connection Pooler (für Production später)
# DB_HOST=aws-0-eu-west-1.pooler.supabase.com
# DB_PORT=6543

# ============================================================================
# ALLE ANDEREN EINSTELLUNGEN BLEIBEN GLEICH
# ============================================================================
DEBUG=True
SECRET_KEY=django-insecure-development-only-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
# ... rest bleibt unverändert
```

### Schritt 4.2: Django Connection Test

```bash
# Terminal in: C:\Users\dusti\.claude-worktrees\DraftcraftV1\great-roentgen\backend

# Aktivieren Sie .env.supabase
set DJANGO_ENV_FILE=.env.supabase

# Test database connection
python manage.py check --database default

# Erwartete Ausgabe:
# System check identified no issues (0 silenced).
```

**Falls Fehler:**

❌ **Error: "No module named 'psycopg2'"**
```bash
# Lösung: psycopg2 installieren
pip install psycopg2-binary
```

❌ **Error: "SSL connection required"**
```bash
# Lösung: DB_SSLMODE in .env.supabase überprüfen
# Muss sein: DB_SSLMODE=require
```

---

## 📊 Phase 5: Schema Migration (5 Min)

### Schritt 5.1: Django Migrations ausführen

```bash
# Noch in: C:\Users\dusti\.claude-worktrees\DraftcraftV1\great-roentgen\backend

# 1. Migrations anzeigen
python manage.py showmigrations

# Erwartung: Alle [ ] (noch nicht angewendet)

# 2. Migrations ausführen
python manage.py migrate

# Erwartete Ausgabe:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   Applying admin.0001_initial... OK
#   ... (insgesamt ~40-50 Migrations)
#   Applying extraction.0001_initial... OK
#   Applying extraction.0002_... OK
#   Applying documents.0001_initial... OK
#   Applying proposals.0001_initial... OK

# 3. Verify Migrations
python manage.py showmigrations

# Erwartung: Alle [X] (angewendet)
```

### Schritt 5.2: Schema Verification

```bash
# Verbindung zu Supabase
psql "postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres"
```

```sql
-- 1. Tabellen-Count (sollte ~40-50 sein)
SELECT count(*) FROM information_schema.tables
WHERE table_schema = 'public';

-- 2. Wichtige Tabellen prüfen
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'documents_%'
ORDER BY table_name;

-- Erwartung:
-- documents_document
-- documents_documentauditlog
-- etc.

-- 3. Constraints prüfen
SELECT
    conname as constraint_name,
    contype as constraint_type,
    conrelid::regclass as table_name
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
LIMIT 10;

-- 4. Exit
\q
```

---

## 📦 Phase 6: Daten-Migration (Optional - 5 Min)

**Nur ausführen wenn Sie existierende Daten haben!**

### Schritt 6.1: Daten von lokal exportieren

```bash
# Falls Sie Testdaten in lokalem Docker haben:

# 1. Nur Daten exportieren (ohne Schema)
docker-compose exec postgres pg_dump -U postgres -a -Fc draftcraft_dev > backups/data_only_$(date +%Y%m%d).dump

# -a = data only (keine CREATE TABLE statements)
```

### Schritt 6.2: Daten zu Supabase importieren

```bash
# 1. Restore zu Supabase
pg_restore \
  -h db.xxx.supabase.co \
  -U postgres \
  -d postgres \
  -a \
  --disable-triggers \
  backups/data_only_20250128.dump

# Password eingeben wenn gefragt

# --disable-triggers: Verhindert constraint violations während import
```

### Schritt 6.3: Data Integrity Check

```bash
# Verbindung zu Supabase
psql "postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres"
```

```sql
-- 1. Row Counts vergleichen mit Phase 1 Notizen
SELECT
    'documents' as table_name, COUNT(*) as rows FROM documents_document
UNION ALL
SELECT 'extractions', COUNT(*) FROM extraction_extractionresult
UNION ALL
SELECT 'proposals', COUNT(*) FROM proposals_proposal;

-- Vergleichen Sie mit Ihren Notizen aus Phase 1!

-- 2. Sample Data prüfen
SELECT id, created_at, file_path
FROM documents_document
ORDER BY created_at DESC
LIMIT 5;

-- 3. Exit
\q
```

---

## 🧪 Phase 7: Application Testing (10 Min)

### Schritt 7.1: Django Development Server starten

```bash
# Terminal in: C:\Users\dusti\.claude-worktrees\DraftcraftV1\great-roentgen\backend

# Mit Supabase .env
set DJANGO_ENV_FILE=.env.supabase
python manage.py runserver

# Erwartete Ausgabe:
# Django version 5.0.x, using settings 'config.settings.development'
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.
```

### Schritt 7.2: Health Check

**Browser öffnen:** http://127.0.0.1:8000/health/

**Erwartete Antwort:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-28T10:30:00Z"
}
```

### Schritt 7.3: Django Admin

1. **Admin User erstellen:**

```bash
# In neuem Terminal (Server läuft weiter)
cd C:\Users\dusti\.claude-worktrees\DraftcraftV1\great-roentgen\backend
set DJANGO_ENV_FILE=.env.supabase
python manage.py createsuperuser

# Eingabe:
# Username: admin
# Email: admin@draftcraft.de
# Password: [Sicheres Password]
# Password (again): [Wiederholen]
```

2. **Admin Login testen:**

**Browser:** http://127.0.0.1:8000/admin/

- Login mit admin/password
- Gehen Sie zu: **Documents** → **Documents** → **Add Document**
- Upload ein Test-PDF
- **Save**

3. **Verify in Supabase:**

```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres"
```

```sql
-- Prüfen ob Dokument gespeichert wurde
SELECT id, file_path, created_at FROM documents_document ORDER BY created_at DESC LIMIT 1;

-- Sollte Ihr gerade hochgeladenes Dokument zeigen!
\q
```

### Schritt 7.4: API Testing

**Browser oder curl:**

```bash
# 1. Token generieren (falls noch nicht vorhanden)
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Response:
# {"token": "abc123..."}

# 2. API Test - Documents list
curl http://127.0.0.1:8000/api/v1/documents/ \
  -H "Authorization: Token abc123..."

# Erwartung: JSON mit Dokumenten-Liste
```

---

## ✅ Phase 8: Monitoring Setup (5 Min)

### Schritt 8.1: Supabase Dashboard Monitoring

**Im Supabase Dashboard:**

1. **Database** → **Usage**
   - Aktueller Storage: _____ MB / 500 MB
   - Active Connections: _____ / 60
   - Bandwidth: _____ MB

2. **Database** → **Backups**
   - Automatische Daily Backups: ✅ Enabled
   - Point-in-time Recovery: 7 Tage

3. **Settings** → **Billing**
   - Current Plan: Free
   - Limits anzeigen

### Schritt 8.2: Alert Setup

**Supabase Dashboard:**

1. **Settings** → **Notifications**
2. **Email Alerts aktivieren für:**
   - [ ] Database 80% voll
   - [ ] Connection limit erreicht
   - [ ] Backup failed

---

## 🎯 Phase 9: Production Vorbereitung (Optional)

### Schritt 9.1: Environment Variables für Cloud Run

**Datei erstellen: `deployment/supabase.env`**

```bash
# Production Environment Variables für Cloud Run

# Database - Supabase Connection Pooler (empfohlen für Production)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[IHR-SUPABASE-PASSWORD]
DB_HOST=aws-0-eu-west-1.pooler.supabase.com
DB_PORT=6543
DB_SSLMODE=require

# Django
DEBUG=False
SECRET_KEY=[GENERIEREN-SIE-NEUEN-KEY]
ALLOWED_HOSTS=.run.app,.draftcraft.de

# Security
SECURE_COOKIES=true
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# ... rest Ihrer Production-Settings
```

### Schritt 9.2: Cloud Run Deployment

```bash
# Später, wenn Sie zu Production deployen:

# 1. Secret Manager (für sensible Daten)
gcloud secrets create supabase-db-password \
  --data-file=- <<EOF
[IHR-SUPABASE-PASSWORD]
EOF

# 2. Cloud Run ENV vars updaten
gcloud run services update draftcraft \
  --region europe-west3 \
  --set-env-vars "DB_HOST=aws-0-eu-west-1.pooler.supabase.com,DB_NAME=postgres,DB_USER=postgres,DB_PORT=6543,DB_SSLMODE=require" \
  --set-secrets "DB_PASSWORD=supabase-db-password:latest"

# 3. Deploy
gcloud builds submit --tag gcr.io/[PROJECT-ID]/draftcraft
gcloud run deploy draftcraft --image gcr.io/[PROJECT-ID]/draftcraft
```

---

## 📊 Erfolgs-Checkliste

**Testen Sie alle Punkte:**

- [ ] ✅ psql Connection zu Supabase funktioniert
- [ ] ✅ Django migrations erfolgreich (alle [X])
- [ ] ✅ Django Admin login funktioniert
- [ ] ✅ Test-Dokument upload funktioniert
- [ ] ✅ Dokument in Supabase sichtbar
- [ ] ✅ API endpoints antworten
- [ ] ✅ Health check zeigt "database: connected"
- [ ] ✅ Backup vorhanden (lokales Docker)
- [ ] ✅ Supabase Dashboard Monitoring aktiv
- [ ] ✅ Email Alerts konfiguriert

**Falls alle ✅ → Migration erfolgreich! 🎉**

---

## 🔄 Rollback Plan (falls nötig)

**Falls Probleme auftreten:**

### Option A: Zurück zu lokalem Docker (sofort)

```bash
# 1. .env.supabase → .env zurückkopieren
copy .env.local .env

# 2. Docker restart
docker-compose down
docker-compose up -d

# 3. Server restart
python manage.py runserver

# Zeit: 2 Minuten
```

### Option B: Supabase Daten löschen und neu starten

```bash
# 1. Alle Tabellen droppen
psql "postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres" -c "
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
"

# 2. Migrations neu ausführen
python manage.py migrate

# Zeit: 5 Minuten
```

---

## 📞 Support & Troubleshooting

### Häufige Probleme

**1. "Too many connections"**
```bash
# Lösung: Connection Pooler nutzen
DB_HOST=aws-0-eu-west-1.pooler.supabase.com
DB_PORT=6543
```

**2. "SSL SYSCALL error"**
```bash
# Lösung: Connection timeout erhöhen
# In .env.supabase:
DB_CONN_MAX_AGE=300  # Reduziert von 600
```

**3. "Relation does not exist"**
```bash
# Lösung: Migrations neu ausführen
python manage.py migrate --run-syncdb
```

### Hilfe-Ressourcen

- **Supabase Docs:** https://supabase.com/docs/guides/database
- **Supabase Status:** https://status.supabase.com/
- **Community:** https://github.com/supabase/supabase/discussions
- **Django Postgres:** https://docs.djangoproject.com/en/5.0/ref/databases/#postgresql-notes

---

## 🎓 Nächste Schritte

Nach erfolgreicher Migration:

1. **Monitoring beobachten** (7 Tage)
   - Database Size Wachstum
   - Connection Patterns
   - Query Performance

2. **Backup-Strategie testen**
   - Point-in-time Recovery testen
   - Restore-Prozedur dokumentieren

3. **Performance Benchmarking**
   - Response times vergleichen (lokal vs Supabase)
   - Query execution times messen

4. **Cost Tracking**
   - Monatliche Usage tracken
   - Entscheiden: Free bleiben vs Upgrade zu Pro ($25/mo)

5. **Phase 4 vorbereiten**
   - pgvector Extension aktivieren (für ML Training)
   - Admin UI Hardening
   - Frontend Implementation starten

---

**Version:** 1.0
**Erstellt:** 2025-01-28
**Getestet für:** Django 5.0, PostgreSQL 15, Supabase Free Tier
