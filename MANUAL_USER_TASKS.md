# DraftCraft V1 - Manual User Tasks

**Diese Aufgaben KÖNNEN NICHT von Claude automatisiert werden und erfordern manuelle Durchführung.**

---

## 🔐 Kategorie 1: Account & Service Registrierung

### 1.1 Google Cloud Platform Account

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 15 Minuten
**Kosten:** Kostenlos (mit $300 Free Credits)

**Schritte:**
1. Gehe zu [https://cloud.google.com/free](https://cloud.google.com/free)
2. Klicke auf "Get started for free"
3. Registriere mit Google Account oder erstelle neuen Account
4. Verifiziere Identität (Kreditkarte erforderlich, wird nicht belastet im Free Tier)
5. Akzeptiere Terms of Service
6. Notiere dir:
   - Projekt-ID (wird später benötigt)
   - Billing Account ID

**Wichtig:** Wähle **Frankfurt (europe-west3)** als Standard-Region (DSGVO-konform)

---

### 1.2 Supabase Account Verifizierung

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 5 Minuten
**Kosten:** €0 (Free Tier)

**Schritte:**
1. Gehe zu [https://app.supabase.com](https://app.supabase.com)
2. Verifiziere dass dein Projekt in **eu-west-1 (Frankfurt)** Region ist
3. Kopiere Connection String:
   - Settings → Database → Connection String → Transaction Mode
   - Format: `postgresql://postgres.PROJECT_ID:PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres`
4. Speichere Credentials sicher (z.B. in Password Manager)

**Notizen:**
- Connection Pooler Port: **6543** (wichtig für Production)
- SSL Mode: **require**

---

### 1.3 SendGrid Account (Email-Versand)

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 10 Minuten
**Kosten:** €0 (100 Emails/Tag kostenlos)

**Schritte:**
1. Gehe zu [https://sendgrid.com/](https://sendgrid.com/)
2. Registriere Account
3. Verifiziere Email-Adresse
4. Erstelle API Key:
   - Settings → API Keys → Create API Key
   - Name: "DraftCraft Production"
   - Permissions: Full Access (oder Mail Send only)
5. Kopiere API Key sofort (wird nur einmal angezeigt!)
6. Sender Identity verifizieren:
   - Settings → Sender Authentication → Verify Single Sender
   - Email: noreply@your-domain.com

**Alternative:** AWS SES (günstiger bei hohem Volumen, aber komplexer Setup)

---

### 1.4 Sentry Account (Error Tracking)

**Status:** ⬜ Optional
**Geschätzter Aufwand:** 5 Minuten
**Kosten:** €0 (5,000 Errors/Monat kostenlos)

**Schritte:**
1. Gehe zu [https://sentry.io/signup/](https://sentry.io/signup/)
2. Registriere Account
3. Erstelle neues Projekt:
   - Platform: Django (Backend)
   - Platform: React (Frontend - separates Projekt)
   - Name: draftcraft-backend / draftcraft-frontend
4. Kopiere DSN (Data Source Name) für beide Projekte
   - Format: `https://xxxxx@o123456.ingest.sentry.io/789012`

---

## 💳 Kategorie 2: Zahlungsinformationen

### 2.1 GCP Billing Account Setup

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 5 Minuten
**Erforderlich:** Kreditkarte oder Bankkonto

**Schritte:**
1. GCP Console → Billing → [https://console.cloud.google.com/billing](https://console.cloud.google.com/billing)
2. Klicke "Add billing account"
3. Eingabe Zahlungsinformationen
4. Verknüpfe Billing Account mit deinem Projekt

**Budget Alerts einrichten:**
1. Billing → Budgets & Alerts → Create Budget
2. Budget: €50/Monat
3. Alert bei 50%, 90%, 100%
4. Notification Email: your-email@domain.com

**Kostenüberwachung:**
- Erwartete monatliche Kosten: €25-50 (ohne Redis)
- Free Tier Credits: $300 (gültig 90 Tage)

---

### 2.2 Supabase Upgrade Plan (falls nötig)

**Status:** ⬜ Optional
**Kosten:** €25/Monat (Pro Plan)
**Wann erforderlich:** Wenn Database >500MB

**Schritte:**
1. Supabase Console → Settings → Billing
2. Upgrade auf "Pro" Plan
3. Vorteile:
   - 8GB Database
   - Daily Backups (7 Tage)
   - Email Support
   - Priorität Support

---

## 🌐 Kategorie 3: Domain & DNS

### 3.1 Domain Registrierung

**Status:** ⬜ Optional
**Geschätzter Aufwand:** 15 Minuten
**Kosten:** €10-20/Jahr

**Schritte:**
1. Wähle Domain Registrar:
   - Google Domains (einfachste Integration mit GCP)
   - Namecheap
   - Cloudflare
2. Suche nach verfügbarer Domain (z.B. draftcraft.de)
3. Kaufe Domain für 1-2 Jahre
4. Aktiviere Domain Privacy (WHOIS Protection)

---

### 3.2 DNS Konfiguration

**Status:** ⬜ Optional (nur mit Custom Domain)
**Geschätzter Aufwand:** 10 Minuten

**Schritte:**
1. Nach Backend Deployment, hole Cloud Run URL:
   ```
   gcloud run services describe draftcraft --region=europe-west3 --format="value(status.url)"
   ```
2. Erstelle DNS Records bei deinem Registrar:

   **A Record (Root Domain):**
   ```
   Name: @
   Type: A
   Value: [Cloud Run IP]
   TTL: 3600
   ```

   **CNAME Record (API Subdomain):**
   ```
   Name: api
   Type: CNAME
   Value: draftcraft-XXXXXX-ew.a.run.app.
   TTL: 3600
   ```

   **CNAME Record (www Subdomain):**
   ```
   Name: www
   Type: CNAME
   Value: draftcraft-static-prod.storage.googleapis.com.
   TTL: 3600
   ```

3. Warte auf DNS Propagation (5-60 Minuten)
4. Verifiziere mit: `nslookup api.your-domain.com`

---

### 3.3 SSL Zertifikat (Cloud Run Managed)

**Status:** ⬜ Automatisch nach DNS Setup
**Aufwand:** 0 (automatisch)

**Schritte:**
1. Cloud Run erstellt automatisch Let's Encrypt Zertifikat
2. Verifiziere HTTPS funktioniert:
   ```
   curl -I https://api.your-domain.com/health/
   ```
3. Kein manuelles Renewal nötig (automatisch)

---

## 🔑 Kategorie 4: Secrets & Keys Generierung

### 4.1 Django Secret Key generieren

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 2 Minuten

**Schritte:**
1. Öffne Terminal/PowerShell
2. Führe aus:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. Kopiere Output (50 Zeichen String)
4. Speichere in Google Secret Manager (siehe DEPLOYMENT_CHECKLIST.md)

**Beispiel Output:**
```
django-insecure-j8k#3n$x@9m!p2&q5r^s*t6u+v7w=y8z
```

---

### 4.2 Encryption Key generieren

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 2 Minuten

**Schritte:**
1. Öffne Terminal/PowerShell
2. Installiere cryptography (falls nicht vorhanden):
   ```bash
   pip install cryptography
   ```
3. Führe aus:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
4. Kopiere Output (44 Zeichen Base64 String)
5. Speichere in Google Secret Manager

**Beispiel Output:**
```
3xK7m9N2pQ4rS5tU6vW7xY8zA1bC2dE3fG4hI5jK6lM=
```

---

### 4.3 Gemini API Key

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 5 Minuten
**Kosten:** Pay-as-you-go (Free Tier vorhanden)

**Schritte:**
1. Gehe zu [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Klicke "Create API Key"
3. Wähle GCP Projekt (oder erstelle neues)
4. Kopiere API Key
5. Speichere in Google Secret Manager

**Rate Limits (Free Tier):**
- 60 Requests/Minute
- 1,500 Requests/Day

---

## 🛠️ Kategorie 5: GCP Console Aktionen

### 5.1 IAM Service Account erstellen

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 10 Minuten

**Schritte:**
1. GCP Console → IAM & Admin → Service Accounts
2. Klicke "Create Service Account"
3. Name: `draftcraft-runner`
4. Description: "Service Account für Cloud Run Backend"
5. Klicke "Create and Continue"
6. Grant Roles:
   - Cloud SQL Client
   - Secret Manager Secret Accessor
   - Storage Admin
   - Logging Writer
7. Klicke "Done"

**Wichtig:** Service Account Email notieren:
```
draftcraft-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

### 5.2 APIs aktivieren

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 5 Minuten

**Schritte:**
1. GCP Console → APIs & Services → Library
2. Suche und aktiviere folgende APIs:
   - ✅ Cloud Run API
   - ✅ Cloud Build API
   - ✅ Secret Manager API
   - ✅ Cloud Storage API
   - ✅ Cloud Logging API
   - ✅ Cloud Monitoring API
   - ✅ Container Registry API

**Alternative (via gcloud CLI):**
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  containerregistry.googleapis.com
```

---

### 5.3 Cloud Storage Buckets erstellen

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 5 Minuten

**Via Console:**
1. GCP Console → Cloud Storage → Browser
2. Klicke "Create Bucket"

**Bucket 1: Media Files**
- Name: `draftcraft-media-prod`
- Location: `europe-west3 (Frankfurt)`
- Storage Class: `Standard`
- Access Control: `Uniform`
- Public Access: `Not public`

**Bucket 2: Static Frontend**
- Name: `draftcraft-static-prod`
- Location: `europe-west3`
- Storage Class: `Standard`
- Access Control: `Uniform`
- Public Access: `Public to internet` ⚠️

3. Nach Erstellung:
   - Bucket 1: IAM → Add → draftcraft-runner@... → Storage Object Admin
   - Bucket 2: IAM → Add → allUsers → Storage Object Viewer

---

### 5.4 Secret Manager Secrets erstellen

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 10 Minuten

**Via Console:**
1. GCP Console → Security → Secret Manager
2. Klicke "Create Secret"

**Secret 1: DJANGO_SECRET_KEY**
- Name: `DJANGO_SECRET_KEY`
- Secret Value: [von Schritt 4.1]
- Replication: `Automatic`

**Secret 2: ENCRYPTION_KEY**
- Name: `ENCRYPTION_KEY`
- Secret Value: [von Schritt 4.2]

**Secret 3: DB_PASSWORD**
- Name: `DB_PASSWORD`
- Secret Value: [Supabase Password]

**Secret 4: GEMINI_API_KEY**
- Name: `GEMINI_API_KEY`
- Secret Value: [von Schritt 4.3]

**Secret 5: SENDGRID_API_KEY** (optional)
- Name: `SENDGRID_API_KEY`
- Secret Value: [von Schritt 1.3]

**Secret 6: SENTRY_DSN** (optional)
- Name: `SENTRY_DSN`
- Secret Value: [von Schritt 1.4]

3. Für jeden Secret:
   - Klicke auf Secret Name
   - Permissions Tab
   - Add Principal: `draftcraft-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com`
   - Role: `Secret Manager Secret Accessor`

---

## 📊 Kategorie 6: Monitoring & Alerts Setup

### 6.1 Uptime Check erstellen

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 5 Minuten

**Schritte:**
1. GCP Console → Monitoring → Uptime Checks
2. Klicke "Create Uptime Check"
3. Konfiguration:
   - Title: `DraftCraft API Health`
   - Protocol: `HTTPS`
   - Resource Type: `URL`
   - Hostname: `api.your-domain.com` (oder Cloud Run URL)
   - Path: `/health/`
   - Check Frequency: `1 minute`
4. Alert & Notification:
   - Erstelle neue Notification Channel (Email)
   - Email: `your-email@domain.com`
5. Klicke "Create"

---

### 6.2 Alert Policy erstellen

**Status:** ⬜ To Do
**Geschätzter Aufwand:** 5 Minuten

**Schritte:**
1. GCP Console → Monitoring → Alerting → Create Policy
2. Klicke "Add Condition"

**Alert 1: High Error Rate**
- Metric: `Cloud Run Revision` → `Request Count`
- Filter: `response_code_class = 5xx`
- Condition: `Rate of change > 10 per minute`
- Duration: `1 minute`

**Alert 2: High Latency**
- Metric: `Cloud Run Revision` → `Request Latency`
- Condition: `p95 latency > 3000ms`
- Duration: `2 minutes`

**Alert 3: Memory Usage**
- Metric: `Cloud Run Revision` → `Memory Utilization`
- Condition: `> 85%`
- Duration: `5 minutes`

3. Notification Channels:
   - Email: `your-email@domain.com`
   - (Optional) Slack/PagerDuty Integration

---

### 6.3 Log-based Metrics

**Status:** ⬜ Optional
**Geschätzter Aufwand:** 5 Minuten

**Schritte:**
1. GCP Console → Logging → Logs-based Metrics
2. Klicke "Create Metric"

**Metric 1: Document Processing Time**
- Name: `document_processing_time`
- Metric Type: `Distribution`
- Filter:
  ```
  resource.type="cloud_run_revision"
  jsonPayload.event="document_processed"
  ```
- Field: `jsonPayload.processing_time_ms`

**Metric 2: Extraction Failures**
- Name: `extraction_failures`
- Metric Type: `Counter`
- Filter:
  ```
  resource.type="cloud_run_revision"
  severity="ERROR"
  jsonPayload.event="extraction_failed"
  ```

---

## 🧪 Kategorie 7: Testing Accounts erstellen

### 7.1 Test User Account (Django)

**Status:** ⬜ To Do nach Backend Deployment
**Geschätzter Aufwand:** 3 Minuten

**Schritte:**
1. Nach Backend Deployment, öffne Cloud Shell
2. Führe aus:
   ```bash
   gcloud run services proxy draftcraft --region=europe-west3
   ```
3. In neuem Terminal Tab:
   ```bash
   curl -X POST http://localhost:8080/admin/auth/user/add/ \
     -d "username=testuser&password=TestPassword123!&email=test@example.com"
   ```
4. Verifiziere Login:
   ```bash
   curl -X POST http://localhost:8080/api/auth/token/ \
     -d "username=testuser&password=TestPassword123!"
   ```

**Credentials speichern:**
- Username: `testuser`
- Password: `TestPassword123!`
- Token: [Kopiere aus Response]

---

### 7.2 Admin Superuser erstellen

**Status:** ⬜ To Do nach Backend Deployment
**Geschätzter Aufwand:** 3 Minuten

**Schritte:**
1. Cloud Shell:
   ```bash
   gcloud run services proxy draftcraft --region=europe-west3
   ```
2. In Container Shell:
   ```bash
   python manage.py createsuperuser
   ```
3. Eingaben:
   - Username: `admin`
   - Email: `admin@your-domain.com`
   - Password: [Sicheres Password wählen, mind. 8 Zeichen]
   - Password (again): [Wiederholen]

4. Verifiziere Login:
   - Öffne: `https://api.your-domain.com/admin/`
   - Login mit admin Credentials

---

## 🎨 Kategorie 8: Branding & Assets (Optional)

### 8.1 Favicon & Logo erstellen

**Status:** ⬜ Optional
**Geschätzter Aufwand:** 30-60 Minuten (oder Design Service)

**Benötigte Dateien:**
- `favicon.ico` (32x32, 16x16)
- `logo.svg` (Vektorgrafik)
- `logo-192.png` (für PWA)
- `logo-512.png` (für PWA)

**Schritte:**
1. Design Tool (Figma, Canva, Adobe Illustrator)
2. Export in benötigten Formaten
3. Optimierung mit TinyPNG
4. Platzierung:
   - Frontend: `frontend_new/public/favicon.ico`
   - Frontend: `frontend_new/public/logo192.png`

---

### 8.2 Email Templates designen

**Status:** ⬜ Optional
**Geschätzter Aufwand:** 2-4 Stunden

**Benötigte Templates:**
- Welcome Email (Neuer User)
- Password Reset
- Proposal Sent (Angebot versendet)
- Document Processed (Verarbeitung abgeschlossen)

**Schritte:**
1. Design in HTML/CSS (oder verwende MJML Framework)
2. Test mit Litmus oder Email on Acid
3. Platzierung: `backend/templates/emails/`

---

## 📱 Kategorie 9: Mobile Testing (Optional)

### 9.1 iOS Testing

**Status:** ⬜ Optional
**Erforderlich:** iPhone/iPad oder Simulator

**Schritte:**
1. Öffne Safari auf iOS Device
2. Navigate zu `https://your-domain.com`
3. Test Funktionen:
   - Login
   - Document Upload (Kamera/Dateien)
   - Responsive Design
4. Add to Home Screen Test (PWA)

---

### 9.2 Android Testing

**Status:** ⬜ Optional
**Erforderlich:** Android Device oder Emulator

**Schritte:**
1. Öffne Chrome auf Android
2. Navigate zu `https://your-domain.com`
3. Test Funktionen (siehe iOS)
4. Add to Home Screen Test (PWA)

---

## 📋 Kategorie 10: Legal & Compliance (WICHTIG)

### 10.1 Datenschutzerklärung erstellen

**Status:** ⬜ PFLICHT (DSGVO)
**Geschätzter Aufwand:** 4-8 Stunden (oder Anwalt beauftragen)

**Benötigte Inhalte:**
- Verantwortlicher (Betreiber)
- Datenverarbeitung (welche Daten, warum, wie lange)
- Rechte der Nutzer (Auskunft, Löschung, Widerspruch)
- Cookies & Tracking
- Drittanbieter (Google Cloud, Supabase, SendGrid)

**Tools:**
- activeMind AG Generator (kostenlos, einfach)
- e-recht24.de Generator (kostenpflichtig, besser)
- Rechtsanwalt (€500-1500, am sichersten)

**Platzierung:**
- Frontend Page: `/privacy`
- Link im Footer

---

### 10.2 Impressum erstellen

**Status:** ⬜ PFLICHT (Deutschland)
**Geschätzter Aufwand:** 30 Minuten

**Benötigte Angaben:**
- Name & Adresse (Betreiber)
- Kontakt (Email, Telefon)
- Handelsregister-Nummer (falls GmbH/UG)
- USt-IdNr. (falls vorhanden)
- Verantwortlicher für Inhalte

**Platzierung:**
- Frontend Page: `/impressum`
- Link im Footer

---

### 10.3 AGB erstellen

**Status:** ⬜ Empfohlen
**Geschätzter Aufwand:** 4-8 Stunden (oder Anwalt)

**Benötigte Inhalte:**
- Leistungsumfang
- Vertragsabschluss
- Preise & Zahlung
- Haftungsausschluss
- Kündigung

**Empfehlung:** Rechtsanwalt für gewerbliche Nutzung

---

## 🎓 Kategorie 11: User Onboarding Material

### 11.1 User Guide schreiben

**Status:** ⬜ Empfohlen
**Geschätzter Aufwand:** 4-6 Stunden

**Kapitel:**
1. Getting Started (Registrierung, Login)
2. Document Upload (Schritt-für-Schritt)
3. Extraction Results verstehen
4. Proposal generieren & versenden
5. Admin Dashboard nutzen
6. Troubleshooting

**Format:** Markdown oder PDF
**Platzierung:** `/docs` Route oder Download

---

### 11.2 Video Tutorials (Optional)

**Status:** ⬜ Optional
**Geschätzter Aufwand:** 8-16 Stunden

**Videos:**
1. "Quick Start: Ersten Auftrag erstellen" (3-5 Min)
2. "Admin Dashboard Tour" (5-7 Min)
3. "Configuration Management" (4-6 Min)

**Tools:** Loom, Camtasia, OBS Studio

---

## 📞 Kategorie 12: Support Setup

### 12.1 Support Email erstellen

**Status:** ⬜ Empfohlen
**Geschätzter Aufwand:** 15 Minuten

**Schritte:**
1. Erstelle Email: `support@your-domain.com`
2. Konfiguriere Email Forwarding zu persönlicher Email
3. Oder: Richte Help Desk Software ein (Zendesk, Freshdesk)

---

### 12.2 FAQ Seite erstellen

**Status:** ⬜ Empfohlen
**Geschätzter Aufwand:** 2-3 Stunden

**Typische Fragen:**
- Wie lade ich ein Dokument hoch?
- Warum ist die Extraktion fehlgeschlagen?
- Wie ändere ich meine Betriebskennzahlen?
- Wie exportiere ich meine Daten?
- Wie kann ich meinen Account löschen?

**Platzierung:** `/faq` Route

---

## ✅ Checkliste Übersicht

### Kritisch (Before Go-Live)
- [ ] GCP Account & Billing (1.1, 2.1)
- [ ] Supabase Verifizierung (1.2)
- [ ] Secrets generieren (4.1, 4.2, 4.3)
- [ ] GCP IAM & Service Account (5.1, 5.2)
- [ ] Cloud Storage Buckets (5.3)
- [ ] Secret Manager Setup (5.4)
- [ ] Admin Superuser erstellen (7.2)
- [ ] Datenschutzerklärung (10.1)
- [ ] Impressum (10.2)

### Wichtig (First Week)
- [ ] SendGrid Account (1.3)
- [ ] Custom Domain (3.1, 3.2)
- [ ] Uptime Checks (6.1)
- [ ] Alert Policies (6.2)
- [ ] Test User Account (7.1)
- [ ] User Guide (11.1)
- [ ] Support Email (12.1)

### Optional (Later)
- [ ] Sentry Account (1.4)
- [ ] Favicon & Logo (8.1)
- [ ] Email Templates (8.2)
- [ ] Mobile Testing (9.1, 9.2)
- [ ] AGB (10.3)
- [ ] Video Tutorials (11.2)
- [ ] FAQ Page (12.2)

---

**Total Estimated Time (Critical):** 2-3 Stunden
**Total Estimated Time (All):** 10-15 Stunden

**Last Updated:** 2025-12-08
