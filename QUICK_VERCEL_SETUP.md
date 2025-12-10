# ⚡ Quick Vercel Setup (5 Minutes)

**Status:** ✅ Code is fixed and pushed to GitHub
**Your Action Required:** Configure 4 environment variables

---

## 🚀 Step 1: Wait for Vercel Build

Vercel should auto-deploy now. Check status:
👉 https://vercel.com/dashboard

**Expected:** Build will succeed (unlike before!)

---

## 🔑 Step 2: Add Environment Variables (REQUIRED)

Go to: **Vercel Dashboard** → **Your Project** → **Settings** → **Environment Variables**

### Required Variables:

```bash
# 1. Backend API URL
VITE_API_URL=https://your-backend-url.run.app

# 2. Supabase URL (already known)
VITE_SUPABASE_URL=https://qnazxcdchsyorognwgfm.supabase.co

# 3. Supabase Anonymous Key
VITE_SUPABASE_ANON_KEY=eyJ...get_from_supabase...

# 4. Node Environment
NODE_ENV=production
```

### Where to Get Values:

**🔹 VITE_API_URL** - Backend Cloud Run URL
```bash
# If backend is deployed:
gcloud run services describe draftcraft-backend \
  --region europe-west3 \
  --format='value(status.url)'

# If backend NOT deployed yet:
# Use: http://localhost:8000 (for now)
# Update later after deploying backend
```

**🔹 VITE_SUPABASE_ANON_KEY** - From Supabase
```bash
# Go to: https://supabase.com/dashboard/project/qnazxcdchsyorognwgfm/settings/api
# Copy: "anon" "public" key (starts with "eyJ...")
```

---

## 🔧 Step 3: Update Backend CORS

Your backend needs to allow Vercel domain:

```bash
# Cloud Run:
gcloud run services update draftcraft-backend \
  --region europe-west3 \
  --update-env-vars CORS_ALLOWED_ORIGINS="https://draftcraft-v1.vercel.app,https://draftcraft-v1-git-*.vercel.app"
```

Or in `backend/config/settings/production.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'https://draftcraft-v1.vercel.app',
    'https://draftcraft-v1-git-*.vercel.app',
]
```

---

## ✅ Step 4: Verify Deployment

1. **Frontend loads:**
   - Visit: https://draftcraft-v1.vercel.app
   - Should see login page

2. **No errors:**
   - Press F12 → Console
   - Should be empty (no red errors)

3. **API works:**
   - Try logging in
   - F12 → Network tab
   - Should see API calls to your backend

---

## 🆘 Troubleshooting

### Problem: "Cannot read property of undefined"
**Cause:** Environment variables not set
**Fix:** Add all 4 env vars in Vercel → Redeploy

### Problem: CORS error in console
**Cause:** Backend doesn't allow Vercel domain
**Fix:** Update CORS settings in backend (Step 3)

### Problem: API calls fail (404)
**Cause:** VITE_API_URL is wrong
**Fix:** Check backend URL, update env var

---

## 📚 Full Guides

- **Complete Setup:** See `VERCEL_SETUP_COMPLETE.md`
- **Deployment Details:** See `DEPLOYMENT_SUCCESS.md`
- **Deployment Checklist:** See `DEPLOYMENT_GUIDE.md`

---

**Time Estimate:** 5-10 minutes
**Difficulty:** Easy (just copy/paste env vars)
**Next:** Enjoy your deployed app! 🎉
