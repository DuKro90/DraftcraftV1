# Vercel Frontend Deployment - Quick Start

**Voraussetzungen:**
- ✅ GitHub Repository: `DuKro90/DraftcraftV1` (gepusht)
- ✅ Backend Cloud Run URL: (kommt nach Backend-Deployment)
- ✅ Supabase Credentials: (siehe unten)

---

## 🚀 Schritt-für-Schritt Anleitung

### 1. Vercel Account einrichten

1. **Gehe zu:** https://vercel.com
2. **Sign up with GitHub**
3. **Autorisiere Vercel** Zugriff auf deine Repositories

---

### 2. Projekt importieren

1. **Click:** "Add New Project"
2. **Import Git Repository:**
   - Wähle: `DuKro90/DraftcraftV1`
   - Click: "Import"

---

### 3. Projekt konfigurieren

**Configure Project Settings:**

```
Project Name: draftcraft-v1
Framework Preset: Vite
Root Directory: frontend_new
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

---

### 4. Environment Variables hinzufügen

**Click "Environment Variables" (vor dem Deploy!):**

Füge diese 3 Variables hinzu:

#### Variable 1: Backend API URL
```
Name: VITE_API_URL
Value: https://BACKEND-URL-KOMMT-SPÄTER.run.app
Environment: Production, Preview, Development
```
**⚠️ WICHTIG:** Lass dies erstmal leer oder nutze Placeholder. Wir updaten es nachdem Backend deployed ist!

#### Variable 2: Supabase URL
```
Name: VITE_SUPABASE_URL
Value: https://qnazxcdchsyorognwgfm.supabase.co
Environment: Production, Preview, Development
```

#### Variable 3: Supabase Anon Key
```
Name: VITE_SUPABASE_ANON_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFuYXp4Y2RjaHN5b3JvZ253Z2ZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNjI5NzUsImV4cCI6MjA3OTkzODk3NX0.PE3t_6pMwnCa_2p-nT-g_suMYfqmiamKDlmuJi7Koo8
Environment: Production, Preview, Development
```

---

### 5. Deploy!

1. **Click:** "Deploy"
2. **Warte:** ~2-3 Minuten
3. **Ergebnis:**
   - ✅ Production URL: `https://draftcraft-v1.vercel.app`
   - ✅ Preview URLs für branches

---

## 🔄 Nach Backend Deployment

**Sobald Cloud Run Backend live ist:**

1. **Kopiere Backend URL** (z.B. `https://draftcraft-backend-abc123.run.app`)

2. **Update Vercel Environment Variable:**
   - Gehe zu: https://vercel.com/dukro90/draftcraft-v1/settings/environment-variables
   - Finde: `VITE_API_URL`
   - Click: "Edit"
   - Neuer Value: `https://draftcraft-backend-abc123.run.app` (DEINE URL!)
   - Save

3. **Redeploy triggern:**
   - Gehe zu: Deployments
   - Latest Deployment → "..." → "Redeploy"
   - ODER: Push einen neuen Commit zu GitHub

---

## 🧪 Testing

### Frontend testen

1. **Öffne:** `https://draftcraft-v1.vercel.app`
2. **Erwartung:**
   - ✅ Login-Seite lädt
   - ✅ Keine Console-Errors (F12 → Console)
   - ❌ API Calls fehlschlagen (normal, solange Backend nicht deployed ist)

### Backend Connection testen (nach Backend Deployment)

1. **Browser Console öffnen** (F12)
2. **Network Tab** → Filter: "Fetch/XHR"
3. **Login versuchen:**
   - ✅ Request geht zu `https://draftcraft-backend-abc123.run.app/api/v1/auth/login/`
   - ✅ Keine CORS Errors
   - ✅ Response kommt zurück (200 oder 401)

---

## 🔒 CORS Check

**Falls CORS Errors erscheinen:**

1. **Backend CORS Settings prüfen:**
   ```bash
   # In Cloud Run → draftcraft-backend → Edit & Deploy New Revision
   # Environment Variables → CORS_ALLOWED_ORIGINS
   # Wert sollte sein: https://draftcraft-v1.vercel.app
   ```

2. **Vercel Domain zu Backend hinzufügen:**
   ```
   CORS_ALLOWED_ORIGINS=https://draftcraft-v1.vercel.app,https://draftcraft-v1-git-*.vercel.app
   ```

---

## 🎯 Nächste Schritte nach Deployment

### 1. Custom Domain (Optional)

**Domain kaufen:** draftcraft.de (~10€/Jahr)

**In Vercel konfigurieren:**
1. Settings → Domains
2. Add Domain: `draftcraft.de`
3. DNS Records aktualisieren:
   - CNAME: `www` → `cname.vercel-dns.com`
   - A: `@` → Vercel IP

**Ergebnis:** `https://draftcraft.de` → Frontend

---

### 2. Analytics aktivieren

**Vercel Analytics (kostenlos für Hobby):**
1. Project Settings → Analytics
2. Enable Analytics
3. 500k Events/Monat kostenlos

---

### 3. Preview Deployments nutzen

**Bei jedem Branch Push:**
```bash
git checkout -b feature/new-dashboard
# ... changes ...
git push origin feature/new-dashboard
```

**Vercel erstellt automatisch:**
- Preview URL: `https://draftcraft-v1-git-feature-new-dashboard.vercel.app`
- Comment in GitHub PR mit Link
- Isolierte Test-Umgebung

---

## 📊 Environment Variables Übersicht

| Variable | Wert | Wann benötigt |
|----------|------|---------------|
| `VITE_API_URL` | Cloud Run Backend URL | **Nach Backend Deploy** |
| `VITE_SUPABASE_URL` | `https://qnazxcdchsyorognwgfm.supabase.co` | **Jetzt** |
| `VITE_SUPABASE_ANON_KEY` | JWT Token (siehe oben) | **Jetzt** |
| `NODE_ENV` | `production` | Auto-gesetzt |

---

## 🐛 Troubleshooting

### Problem: Build fails mit "Module not found"

**Lösung:**
```bash
# Lokal testen:
cd frontend_new
npm install
npm run build

# Falls Fehler → Dependencies fehlen
# Füge zu package.json hinzu und committe
```

### Problem: "Failed to fetch" im Browser

**Ursachen:**
1. ❌ Backend noch nicht deployed → Warte auf Cloud Run
2. ❌ `VITE_API_URL` falsch gesetzt → Check Vercel Settings
3. ❌ CORS Error → Check Backend CORS_ALLOWED_ORIGINS

**Fix:**
- Browser Console (F12) → Network Tab → Check Request URL
- Vercel Settings → Environment Variables → Validate `VITE_API_URL`

### Problem: Blank page / White screen

**Ursachen:**
1. JavaScript Error → Check Browser Console
2. Routing Issue → Check `vite.config.ts`

**Fix:**
```bash
# Vercel Logs ansehen:
# Project → Deployments → Latest → View Function Logs
# Oder Browser Console für Client-Side Errors
```

---

## 📞 Support

**Vercel Dokumentation:**
- https://vercel.com/docs/frameworks/vite

**Status Dashboard:**
- Vercel: https://www.vercel-status.com/
- Supabase: https://status.supabase.com/

---

**Deployment Status:**
- ⏳ Backend: Wartet auf Cloud Run Build
- ⏳ Frontend: Bereit für Vercel Deployment

**Nächster Schritt:**
1. Warte auf Cloud Run Backend → Erhalte URL
2. Deploy Frontend zu Vercel
3. Update `VITE_API_URL` in Vercel
4. Teste complete Stack!

🚀 **Let's go!**
