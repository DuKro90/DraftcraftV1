# ⚡ Vercel Manual Setup (2 Minutes)

**Why Manual?** Monorepo configurations work better through Vercel Dashboard than vercel.json

---

## 🎯 Quick Setup Steps

### 1. Go to Vercel Project Settings

👉 https://vercel.com/dashboard → Your Project → **Settings** → **General**

### 2. Configure Build Settings

Scroll to **Build & Development Settings** and set:

| Setting | Value |
|---------|-------|
| **Framework Preset** | `Vite` |
| **Root Directory** | `frontend_new` ⚠️ **CRITICAL** |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

**Save Changes**

### 3. Add Environment Variables

Go to **Settings** → **Environment Variables**

Click **Add New** and add each of these:

```bash
# Variable 1
Name:  VITE_API_URL
Value: https://your-backend.run.app
Apply to: All (Production, Preview, Development)

# Variable 2
Name:  VITE_SUPABASE_URL
Value: https://qnazxcdchsyorognwgfm.supabase.co
Apply to: All

# Variable 3
Name:  VITE_SUPABASE_ANON_KEY
Value: [Get from Supabase Dashboard]
Apply to: All

# Variable 4
Name:  NODE_ENV
Value: production
Apply to: Production only
```

**Save Changes**

### 4. Redeploy

Go to **Deployments** tab:
1. Click on the latest failed deployment
2. Click **⋮** (three dots)
3. Click **Redeploy**
4. ✅ Check "Use existing Build Cache"
5. Click **Redeploy**

---

## 🎉 Success!

Build should now succeed with output like:

```
✓ 2503 modules transformed
✓ built in 8.33s
Deployment ready
```

Visit your site at: **https://draftcraft-v1.vercel.app**

---

## 🔑 Getting Missing Values

**VITE_API_URL** (Backend):
```bash
# If deployed:
gcloud run services describe draftcraft-backend --region europe-west3 --format='value(status.url)'

# If not deployed yet:
# Use http://localhost:8000 for now
```

**VITE_SUPABASE_ANON_KEY**:
```bash
# Go to: https://supabase.com/dashboard/project/qnazxcdchsyorognwgfm/settings/api
# Copy: "anon" "public" key (starts with eyJ...)
```

---

## 🆘 Troubleshooting

**Problem:** Build fails with "Cannot find module"
- **Fix:** Check that Root Directory = `frontend_new` (exactly)

**Problem:** Build fails with "tsc: command not found"
- **Fix:** Build Command should be just `npm run build` (package.json handles it)

**Problem:** "Invalid configuration" error
- **Fix:** Make sure Output Directory = `dist` (not `frontend_new/dist`)

**Problem:** App loads but API fails
- **Fix:** Check environment variables are set and applied to Production

---

**Time:** 2 minutes
**Difficulty:** Easy (just copy/paste settings)
**Result:** ✅ Working deployment!
