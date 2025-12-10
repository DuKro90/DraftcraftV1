# Vercel Configuration (Manual Setup Required)

**Action Required:** Configure these settings in Vercel Dashboard

---

## 🔧 Step 1: Project Settings

Go to: **Vercel Dashboard** → **Your Project** → **Settings** → **General**

### Build & Development Settings:

```
Framework Preset:        Vite
Root Directory:          frontend_new
Build Command:           npm run build
Output Directory:        dist
Install Command:         npm install
Development Command:     npm run dev
```

**IMPORTANT:** Make sure "Root Directory" is set to `frontend_new`

---

## 🔑 Step 2: Environment Variables

Go to: **Settings** → **Environment Variables**

Add these variables for **Production**, **Preview**, and **Development**:

```bash
VITE_API_URL=https://your-backend.run.app
VITE_SUPABASE_URL=https://qnazxcdchsyorognwgfm.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
NODE_ENV=production
```

### Where to Get Values:

**VITE_API_URL:**
```bash
gcloud run services describe draftcraft-backend \
  --region europe-west3 \
  --format='value(status.url)'
```

**VITE_SUPABASE_ANON_KEY:**
- Go to: https://supabase.com/dashboard/project/qnazxcdchsyorognwgfm/settings/api
- Copy the "anon" "public" key

---

## 🚀 Step 3: Trigger Deployment

After configuring the settings:

1. Go to **Deployments** tab
2. Click **Redeploy** on the latest deployment
3. Check "Use existing Build Cache"
4. Click **Redeploy**

---

## ✅ Expected Build Output

```bash
Running "npm install"...
added 360 packages

Running "npm run build"...
vite v5.4.21 building for production...
✓ 2503 modules transformed
✓ built in 8.33s
```

---

## 🆘 If Build Still Fails

### Check Root Directory
- Ensure "Root Directory" = `frontend_new` (not blank)
- Clear build cache and redeploy

### Check Build Command
- Should be just: `npm run build` (not `tsc -b && vite build`)
- This is already configured in package.json

### Check Environment Variables
- All 4 variables must be set
- Apply to all environments (Production, Preview, Development)

---

**Why no vercel.json?** Vercel's dashboard configuration is more reliable for monorepo setups.
