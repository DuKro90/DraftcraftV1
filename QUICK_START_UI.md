# Quick Start Guide - DraftCraft UI

**5-Minute Setup** | Get the frontend running in minutes

---

## Prerequisites ✅

You already have:
- ✅ Node.js v22.21.0
- ✅ Python 3.14.0
- ✅ Backend code in `C:\Codes\DraftcraftV1\backend`

---

## Step 1: Install Frontend Dependencies (2 minutes)

```bash
cd C:\Codes\DraftcraftV1\frontend_new
npm install
```

**Expected output:**
```
added 150+ packages in 30s
```

---

## Step 2: Configure Environment (30 seconds)

```bash
# Create .env file
copy .env.example .env
```

**File content (`.env`):**
```
VITE_API_URL=http://localhost:8000
```

---

## Step 3: Start Backend (1 minute)

Open a **new terminal**:

```bash
cd C:\Codes\DraftcraftV1\backend
python manage.py runserver
```

**Expected output:**
```
Django version 5.0.x
Starting development server at http://127.0.0.1:8000/
```

✅ Backend running on: http://localhost:8000

---

## Step 4: Start Frontend (1 minute)

In your **original terminal**:

```bash
cd C:\Codes\DraftcraftV1\frontend_new
npm run dev
```

**Expected output:**
```
VITE v5.4.9  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

✅ Frontend running on: http://localhost:5173

---

## Step 5: Open Application (30 seconds)

### Login
1. Open browser: http://localhost:5173
2. You'll see the login page
3. Use credentials from Django admin (default: `admin` / your password)

### Test Workflow
1. Click "Workflow" in navigation
2. Upload a test document (PDF/image)
3. Watch automatic processing
4. Review extraction results
5. Generate proposal
6. Download PDF

---

## Troubleshooting 🔧

### Problem: `npm install` fails

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Try again
npm install
```

---

### Problem: Backend not accessible

**Check 1:** Is Django running?
```bash
# You should see server logs in terminal
```

**Check 2:** CORS configured?
```python
# backend/config/settings/development.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # ← Add this if missing
]
```

**Fix:** Add `'http://localhost:5173'` to `CORS_ALLOWED_ORIGINS`, then restart Django

---

### Problem: TypeScript errors

**Solution:**
```bash
# Clear build cache
rm -rf node_modules/.vite

# Restart dev server
npm run dev
```

---

### Problem: "Cannot find module" errors

**Solution:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

---

## Quick Commands Reference

### Development
```bash
# Start frontend
npm run dev

# Start backend
cd backend && python manage.py runserver

# Run both in Docker
docker-compose up
```

### Build
```bash
# Production build
npm run build

# Preview production build
npm run preview
```

### Testing
```bash
# Run tests
npm run test

# Run E2E tests
npm run test:e2e
```

---

## File Structure (What You Just Created)

```
frontend_new/
├── src/               # All source code
│   ├── components/    # UI components
│   ├── pages/         # Main pages
│   ├── lib/           # Utilities, API client
│   └── types/         # TypeScript types
├── public/            # Static files
├── package.json       # Dependencies
├── vite.config.ts     # Build config
└── README.md          # Full documentation
```

---

## Next Steps

### For Development:
1. Read `frontend_new/README.md` for detailed docs
2. Explore components in `src/components/`
3. Check API client in `src/lib/api/client.ts`

### For Testing:
1. Upload a real PDF document
2. Test the complete workflow
3. Try downloading the proposal PDF
4. Send a test email

### For Customization:
1. Colors: Edit `tailwind.config.js`
2. API URL: Edit `.env`
3. Components: Modify `src/components/`

---

## Important URLs

| Service | URL |
|---------|-----|
| Frontend (React) | http://localhost:5173 |
| Backend (Django) | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin/ |
| API Docs (Swagger) | http://localhost:8000/api/docs/swagger/ |

---

## Demo Workflow

### 1. Upload Document
- Click "Workflow" in navigation
- Drag-and-drop a PDF or click "Select File"
- Click "Hochladen und Analysieren"

### 2. Watch Processing
- Automatic OCR + NER extraction
- Progress indicator shows status
- Results appear after ~5-10 seconds

### 3. Review Results
- See confidence score (%)
- View extracted entities
- Check materials found
- Click "Weiter zum Angebot"

### 4. Generate Proposal
- Customer data auto-filled from extraction
- Review/edit customer information
- Click "Angebot generieren"

### 5. Download/Send
- Download PDF proposal
- Or send via email
- Start new document

---

## Success Indicators ✅

You'll know it's working when:
- ✅ Login page loads at http://localhost:5173
- ✅ Can authenticate with Django credentials
- ✅ Workflow page shows 4-step indicator
- ✅ File upload accepts PDF/images
- ✅ Processing shows live status
- ✅ Extraction results display confidence scores
- ✅ Proposal form auto-fills customer data
- ✅ PDF downloads successfully

---

## Getting Help

### Check Logs
**Frontend errors:**
- Open browser DevTools (F12)
- Check Console tab

**Backend errors:**
- Check terminal running Django
- Look for Python traceback

### Common Issues
1. **401 Unauthorized**: Login credentials incorrect
2. **CORS Error**: Add frontend URL to `CORS_ALLOWED_ORIGINS`
3. **500 Server Error**: Check Django logs for Python errors
4. **Network Error**: Ensure backend is running

---

## Documentation

- **Full Frontend Guide**: `frontend_new/README.md`
- **Implementation Summary**: `FRONTEND_IMPLEMENTATION_SUMMARY.md`
- **Architecture Strategy**: `docs/phases/PHASE4B_UI_DEVELOPMENT_STRATEGY.md`
- **Backend API**: `FRONTEND_INTEGRATION_GUIDE.md`

---

**Status:** ✅ Ready to Run
**Time to Complete:** ~5 minutes
**Last Updated:** 2025-12-02

Happy coding! 🎉
