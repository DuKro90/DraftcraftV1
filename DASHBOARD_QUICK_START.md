# Admin Dashboard - Quick Start Guide

**⚡ 5-Minute Setup & Demo**

---

## 🚀 Option 1: Development Mode (Recommended)

### Step 1: Start Backend

```bash
# In project root
docker-compose up -d

# Verify backend is running
curl http://localhost:8000/api/v1/admin/dashboard/health/
```

**Expected Response:**
```json
{
  "overall": "healthy",
  "components": { ... }
}
```

### Step 2: Start Frontend

```bash
# In new terminal
cd frontend_new
npm install  # Only needed first time
npm run dev
```

**You should see:**
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

### Step 3: Access Dashboard

1. **Open Browser:** http://localhost:5173/admin/dashboard
2. **Login** (if not authenticated)
3. **View Dashboard!**

---

## 📱 What You'll See

### Dashboard Overview (`/admin/dashboard`)

```
┌─────────────────────────────────────────────────────┐
│  DraftCraft Admin     👤 Admin ▼                   │
├─────────────────────────────────────────────────────┤
│  ☰ Übersicht                                        │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────┐  │
│  │ Gesamt   │ │ Aktive   │ │ Ø        │ │Aktive│ │
│  │ Dokumente│ │ Muster   │ │Konfidenz │ │Nutzer│ │
│  │ 1,247    │ │ 12       │ │ 87.3%    │ │ 45   │ │
│  └──────────┘ └──────────┘ └──────────┘ └─────┘  │
│                                                     │
│  ┌─────────────────────┐ ┌──────────────────────┐ │
│  │ Dokumente (7 Tage)  │ │ Muster nach Schwere  │ │
│  │                     │ │                      │ │
│  │  [Line Chart]       │ │   [Pie Chart]        │ │
│  └─────────────────────┘ └──────────────────────┘ │
│                                                     │
│  ┌─ Letzte Aktivitäten ─────────────────────────┐ │
│  │ ✓ Dokument erfolgreich verarbeitet          │ │
│  │ ⚠ Neues Muster erkannt                       │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Pattern Management (`/admin/patterns`)

```
┌─────────────────────────────────────────────────────┐
│  Muster-Verwaltung                🔄 Aktualisieren  │
├─────────────────────────────────────────────────────┤
│  Schweregrad: [Alle ▼]  Status: [Nur aktive]       │
│                                                     │
│  ┌─ CRITICAL ──────────────────────────────────┐   │
│  │ amount: German currency format (3 Vorkommen)│   │
│  │ [Click to expand...]                        │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─ HIGH ──────────────────────────────────────┐   │
│  │ date: DD.MM.YYYY not recognized (5 Vorkommen│   │
│  │ [Click to expand...]                        │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Key Features to Test

### 1. Dashboard Overview

**Stats Cards:**
- ✅ Total documents count
- ✅ Today's processed count
- ✅ Active pattern count with critical badge
- ✅ Average confidence percentage
- ✅ Active users count

**Charts:**
- ✅ 7-day document trend (line chart)
- ✅ Pattern severity breakdown (pie chart)

**Activity Feed:**
- ✅ Recent document uploads
- ✅ Pattern detections
- ✅ Processing errors
- ✅ Color-coded severity

**Auto-Refresh:**
- ✅ Stats refresh every 30 seconds
- ✅ Health indicator updates every 30 seconds

### 2. Pattern Management

**List Features:**
- ✅ Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Toggle active/inactive patterns
- ✅ Expand/collapse pattern cards
- ✅ View pattern details
- ✅ See suggested fixes
- ✅ View example documents

**Actions:**
- ✅ Approve pattern fix
- ✅ Reject pattern fix (with notes)
- ✅ Real-time list updates

### 3. System Health

**Health Indicator** (bottom of sidebar):
- 🟢 Green: Healthy
- 🟡 Yellow: Degraded
- 🔴 Red: Unhealthy
- ⚪ Gray: Unknown

**Components Monitored:**
- Database connection
- Redis cache
- Processing error rate

---

## 🔧 Troubleshooting

### Issue: "Failed to fetch dashboard stats"

**Cause:** Backend not running or CORS issue

**Fix:**
```bash
# Check backend is running
docker-compose ps

# Check backend logs
docker-compose logs web

# Restart if needed
docker-compose restart web
```

### Issue: "Cannot GET /admin/dashboard"

**Cause:** Frontend not running

**Fix:**
```bash
cd frontend_new
npm run dev
```

### Issue: "Unauthorized (401)"

**Cause:** Not logged in or token expired

**Fix:**
1. Go to http://localhost:5173/login
2. Login with admin credentials
3. Navigate back to dashboard

### Issue: Charts not showing data

**Cause:** No data in database

**Fix:**
```bash
# Add test data (if available)
docker-compose exec web python manage.py loaddata fixtures/test_data.json

# Or upload some documents via main app
# Then check dashboard again
```

---

## 📊 API Testing (Without Frontend)

### Test Backend Directly

**1. Health Check (Any authenticated user):**

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/admin/dashboard/health/
```

**2. Dashboard Stats (Admin only):**

```bash
curl -H "Authorization: Token YOUR_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/dashboard/stats/
```

**3. Recent Activity (Admin only):**

```bash
curl -H "Authorization: Token YOUR_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/dashboard/activity/
```

**4. Pattern List:**

```bash
curl -H "Authorization: Token YOUR_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/patterns/failures/?severity=CRITICAL
```

---

## 🚢 Production Deployment

### Option 1: Separate Frontend + Backend

**Backend (already running):**
```bash
# No changes needed - backend is already deployed
```

**Frontend (static hosting):**
```bash
cd frontend_new
npm run build

# Upload dist/ folder to:
# - Netlify
# - Vercel
# - AWS S3 + CloudFront
# - nginx static server
```

**Set Environment Variable:**
```env
VITE_API_URL=https://your-backend-domain.com
```

### Option 2: Serve from Django

**Add to Django settings:**
```python
# settings.py
STATICFILES_DIRS = [
    BASE_DIR / 'frontend_new' / 'dist',
]
```

**Build frontend:**
```bash
cd frontend_new
npm run build
```

**Collect static:**
```bash
python manage.py collectstatic --noinput
```

---

## 📱 Mobile Testing

The dashboard is fully responsive!

**Test on mobile:**
1. Find your local IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Open on phone: `http://YOUR_IP:5173/admin/dashboard`
3. Sidebar auto-collapses on mobile
4. Charts resize to fit screen
5. Touch-friendly buttons

---

## 🎨 Customization

### Change Theme Colors

Edit `frontend_new/src/components/admin/DashboardLayout.tsx`:

```typescript
// Change sidebar active color from blue to your brand color
const isActive = location.pathname === item.path
return (
  <Link
    className={`... ${
      isActive
        ? 'bg-purple-50 text-purple-600'  // ← Change here
        : 'text-gray-700 hover:bg-gray-100'
    }`}
  >
```

### Add Custom Dashboard Widgets

Create new component in `frontend_new/src/components/admin/`:

```typescript
// CustomWidget.tsx
export const CustomWidget: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">Custom Widget</h3>
      {/* Your content here */}
    </div>
  )
}
```

Add to `DashboardOverview.tsx`:
```typescript
import { CustomWidget } from '@/components/admin/CustomWidget'

// In render:
<CustomWidget />
```

---

## ✅ Quick Checklist

Before showing to stakeholders:

- [ ] Backend running (`docker-compose ps`)
- [ ] Frontend running (`npm run dev`)
- [ ] Can access `/admin/dashboard`
- [ ] Stats cards show data
- [ ] Charts render properly
- [ ] Activity feed has items
- [ ] Pattern list loads
- [ ] Health indicator is green
- [ ] Sidebar navigation works
- [ ] Mobile responsive (test on phone)

---

## 🎉 Demo Script (2 Minutes)

**1. Overview (30 seconds)**
> "This is the new admin dashboard. At a glance, we see 1,247 documents processed, 12 active patterns, and 87% average confidence."

**2. Charts (30 seconds)**
> "Here's our 7-day trend showing document processing volume. And this pie chart breaks down pattern severity - 3 critical issues need attention."

**3. Activity Feed (30 seconds)**
> "Real-time activity shows what's happening right now - successful document processing, new patterns detected, and any errors."

**4. Pattern Management (30 seconds)**
> "In the pattern management view, we can see all extraction failures, filter by severity, and approve or reject automated fixes."

---

**Ready to test?** → http://localhost:5173/admin/dashboard

**Questions?** → See `PHASE_4D_REACT_DASHBOARD_COMPLETE.md`

---

**Last Updated:** 2025-12-08
**Version:** 1.0
**Status:** ✅ Production Ready
