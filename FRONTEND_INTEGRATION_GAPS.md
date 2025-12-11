# DraftCraft Frontend Integration - Gap Analysis

**Generated:** 2025-12-11
**Status:** Phase 4D Backend Complete, Frontend Partial Integration
**Priority:** Critical for full system functionality

---

## 📊 Executive Summary

### Current State
- ✅ **Backend:** Comprehensive REST API (Phase 4D complete)
- ✅ **Frontend:** React app with components, hooks, routing
- ⚠️ **Integration:** Multiple endpoint/payload mismatches
- ❌ **Auth:** Authentication flow incomplete

### Critical Issues
1. **Auth endpoint mismatch** - Frontend can't login
2. **Calculation API mismatch** - Price calculator won't work
3. **Config endpoint typos** - German umlauts causing 404s
4. **Missing CORS setup** - Cross-origin requests may fail

---

## 🔴 CRITICAL GAPS (Must Fix First)

### 1. Authentication System Mismatch

**Problem:** Frontend and backend use different auth endpoints and payloads

#### Backend (Current)
```
POST /api/auth/token/
{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "token": "abc123...",
  "user": {...},
  "expires_at": "..."
}
```

#### Frontend (Expected)
```
POST /api/v1/auth/login/  ❌ WRONG PATH
{
  "email": "user@example.com",  ❌ WRONG FIELD
  "password": "password123"
}
```

**Impact:** Users cannot login at all

**Solution Options:**
- **A) Change Backend** (Recommended): Add `/api/v1/auth/login/` alias that accepts `email`
- **B) Change Frontend**: Update `useAuth` hook to use `/api/auth/token/` with `username`

---

### 2. Calculation Endpoint Mismatch

**Problem:** Frontend calls non-existent calculation endpoint

#### Backend (Current)
```
POST /api/v1/calculate/price/
POST /api/v1/calculate/multi-material/
POST /api/v1/pauschalen/applicable/
```

#### Frontend (Expected)
```
POST /api/v1/calculations/calculate/  ❌ DOESN'T EXIST
```

**Impact:** Price calculator completely broken

**Solution:**
Update `frontend_new/src/lib/hooks/useCalculation.ts:50` to use correct endpoint:
```typescript
// Change from:
'/api/v1/calculations/calculate/'

// To:
'/api/v1/calculate/price/'
```

---

### 3. Config Endpoints - German Umlaut Issues

**Problem:** URL encoding mismatch for German characters

#### Backend (Current)
```
/api/v1/config/holzarten/        ✅ OK
/api/v1/config/oberflaechen/     ✅ OK (no umlaut in URL)
/api/v1/config/komplexitaet/     ✅ OK (no umlaut in URL)
/api/v1/config/betriebskennzahlen/  ✅ OK
```

#### Frontend (Expected)
```
/api/v1/config/holzarten/        ✅ OK
/api/v1/config/oberflächen/      ❌ UMLAUT (ä → %C3%A4)
/api/v1/config/komplexitäten/    ❌ UMLAUT + PLURAL
```

**Impact:** Config management fails with 404 errors

**Solution:**
Update `frontend_new/src/lib/hooks/useConfig.ts`:
```typescript
// Line 42, 51, 60 - Fix endpoints:
'/api/v1/config/oberflaechen/'     // Remove ä
'/api/v1/config/komplexitaet/'     // Remove ä, use singular
```

---

### 4. CORS Configuration

**Problem:** Frontend (port 5173) calling Backend (port 8000) may fail

**Check Required:**
```python
# backend/config/settings/development.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative
]
```

**If missing, add:**
```python
INSTALLED_APPS = [
    'corsheaders',  # Must be added
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be BEFORE CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    ...
]
```

---

## 🟡 API ENDPOINT MISMATCHES

### Summary Table

| Feature | Frontend Expects | Backend Has | Status | Fix Priority |
|---------|-----------------|-------------|--------|--------------|
| **Auth Login** | `/api/v1/auth/login/` | `/api/auth/token/` | ❌ | 🔴 Critical |
| **Auth Register** | `/api/v1/auth/register/` | `/api/auth/register/` | ✅ | - |
| **Auth Logout** | `/api/v1/auth/logout/` | `/api/auth/logout/` | ✅ | - |
| **Calculate Price** | `/api/v1/calculations/calculate/` | `/api/v1/calculate/price/` | ❌ | 🔴 Critical |
| **Documents List** | `/api/v1/documents/` | `/api/v1/documents/` | ✅ | - |
| **Documents Upload** | `/api/v1/documents/upload/` | `/api/v1/documents/upload/` | ⚠️ | 🟡 Verify |
| **Documents Extract** | `/api/v1/documents/{id}/extract/` | `/api/v1/documents/{id}/extract/` | ⚠️ | 🟡 Verify |
| **Config Holzarten** | `/api/v1/config/holzarten/` | `/api/v1/config/holzarten/` | ✅ | - |
| **Config Oberflächen** | `/api/v1/config/oberflächen/` | `/api/v1/config/oberflaechen/` | ❌ | 🔴 Critical |
| **Config Komplexität** | `/api/v1/config/komplexitäten/` | `/api/v1/config/komplexitaet/` | ❌ | 🔴 Critical |
| **Transparency Explanations** | `/api/v1/transparency/explanations/{id}/` | `/api/v1/calculations/explanations/{id}/` | ❌ | 🟡 Medium |
| **Transparency Benchmarks** | `/api/v1/transparency/benchmarks/` | `/api/v1/benchmarks/user/` | ❌ | 🟡 Medium |
| **Transparency Feedback** | `/api/v1/transparency/feedback/` | `/api/v1/feedback/calculation/` | ❌ | 🟡 Medium |
| **Patterns List** | `/api/v1/patterns/failures/` | `/api/v1/patterns/failures/` | ✅ | - |
| **Pattern Approve** | `/api/v1/patterns/{id}/approve-fix/` | `/api/v1/patterns/{id}/approve-fix/` | ✅ | - |

---

## 🟢 MISSING FEATURES

### 1. Document Management Endpoints

**Status:** ⚠️ Partially Implemented

#### Missing Actions:
```python
# backend/api/v1/document_views.py - DocumentViewSet

# Need to verify these exist:
@action(methods=['POST'], detail=True)
def upload(self, request):
    """Upload document file"""
    pass

@action(methods=['POST'], detail=True)
def extract(self, request):
    """Extract data from document"""
    pass

@action(methods=['GET'], detail=True)
def download(self, request, pk=None):
    """Download original document"""
    pass
```

**Check:**
```bash
cd backend
python manage.py show_urls | grep documents
```

---

### 2. Proposal Management

**Status:** ❌ Not Registered in URLs

Frontend has:
- `ProposalForm.tsx`
- `ProposalSuccess.tsx`
- `useProposals` hook

Backend has:
- `ProposalViewSet` defined
- `ProposalTemplateViewSet` defined
- Registered in router ✅

**Action Required:** Verify endpoints work:
```bash
curl http://localhost:8000/api/v1/proposals/
```

---

### 3. Batch Processing

**Status:** ✅ Implemented but not used in Frontend

Backend has full batch support:
```
POST /api/v1/batches/
GET /api/v1/batches/
GET /api/v1/batches/{id}/
POST /api/v1/batches/{id}/process_all/
```

**Action Required:**
- Create `useBatch` hook
- Add BatchUpload component
- Add batch processing UI to DocumentWorkflow

---

### 4. Admin Dashboard Data

**Status:** ✅ Backend complete, needs frontend integration

Backend endpoints exist:
```
GET /api/v1/admin/dashboard/stats/
GET /api/v1/admin/dashboard/activity/
GET /api/v1/admin/dashboard/health/
```

Frontend has:
- `DashboardOverview.tsx`
- `DashboardLayout.tsx`

**Action Required:**
- Create `useAdminDashboard` hook
- Integrate data into DashboardOverview component

---

### 5. Pattern Management Advanced Features

**Status:** ✅ Backend complete, partial frontend

Backend has:
```
GET /api/v1/patterns/failures/
POST /api/v1/patterns/{id}/approve-fix/
POST /api/v1/patterns/bulk-action/
```

Frontend has:
- `PatternManagement.tsx` (basic)

**Missing:**
- Bulk actions UI
- Pattern details modal
- Fix approval workflow

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Critical Fixes (Day 1)

- [ ] **Fix Auth Endpoint**
  - [ ] Option A: Add `/api/v1/auth/login/` alias in backend
  - [ ] OR Option B: Update frontend to use `/api/auth/token/`
  - [ ] Update auth payload handling (username vs email)
  - [ ] Test login/logout flow

- [ ] **Fix Calculation Endpoint**
  - [ ] Update `useCalculation.ts` line 50
  - [ ] Test price calculator component
  - [ ] Test multi-material calculator

- [ ] **Fix Config Endpoints**
  - [ ] Update `useConfig.ts` line 51, 60
  - [ ] Remove umlauts from URLs
  - [ ] Test all config management pages

- [ ] **Verify CORS Setup**
  - [ ] Check `settings/development.py`
  - [ ] Add `corsheaders` if missing
  - [ ] Test cross-origin requests

---

### Phase 2: Transparency Integration (Day 2)

- [ ] **Fix Transparency Endpoints**
  - [ ] Update `useTransparency.ts` endpoint paths
  - [ ] Map to correct backend URLs:
    - `/api/v1/calculations/explanations/` (backend)
    - `/api/v1/benchmarks/user/` (backend)
    - `/api/v1/feedback/calculation/` (backend)
  - [ ] Test CalculationExplanationViewer component
  - [ ] Test BenchmarkComparison component

- [ ] **Integrate Transparency into Calculator**
  - [ ] Use `PriceCalculatorWithTransparency.tsx`
  - [ ] Show real-time factor explanations
  - [ ] Display confidence badges

---

### Phase 3: Complete Document Workflow (Day 3)

- [ ] **Verify Document Endpoints**
  - [ ] Test upload endpoint with real file
  - [ ] Test extract endpoint
  - [ ] Add download endpoint if missing
  - [ ] Handle extraction results properly

- [ ] **Add Batch Processing**
  - [ ] Create `useBatch.ts` hook
  - [ ] Add BatchUpload component
  - [ ] Add batch status tracking
  - [ ] Integrate into DocumentWorkflow page

---

### Phase 4: Admin Dashboard (Day 4)

- [ ] **Create Admin Hooks**
  - [ ] `useAdminDashboard` for stats
  - [ ] `usePatternManagement` for patterns
  - [ ] `useSystemHealth` for monitoring

- [ ] **Integrate Dashboard Data**
  - [ ] Stats cards with real data
  - [ ] Recent activity feed
  - [ ] System health indicators
  - [ ] Pattern management table

---

### Phase 5: Polish & Testing (Day 5)

- [ ] **Error Handling**
  - [ ] Add proper error boundaries
  - [ ] Toast notifications for API errors
  - [ ] Loading states for all async operations
  - [ ] Retry logic for failed requests

- [ ] **Testing**
  - [ ] Test all user workflows end-to-end
  - [ ] Test with real PDF documents
  - [ ] Test calculation accuracy
  - [ ] Test pattern management workflow

- [ ] **Documentation**
  - [ ] Update API documentation
  - [ ] Create frontend setup guide
  - [ ] Document environment variables
  - [ ] Add troubleshooting section

---

## 🛠️ QUICK FIX SCRIPT

### Option 1: Fix Frontend (Recommended)

```bash
# File: frontend_new/src/lib/hooks/useAuth.ts
# Line 44: Change endpoint
- const response = await apiClient.post<AuthResponse>('/api/v1/auth/login/', credentials)
+ const response = await apiClient.post<AuthResponse>('/api/auth/token/', {
+   username: credentials.email,
+   password: credentials.password
+ })

# File: frontend_new/src/lib/hooks/useCalculation.ts
# Line 50: Change endpoint
- '/api/v1/calculations/calculate/',
+ '/api/v1/calculate/price/',

# File: frontend_new/src/lib/hooks/useConfig.ts
# Line 42: Fix oberflächen endpoint
- const response = await apiClient.get('/api/v1/config/oberflächen/')
+ const response = await apiClient.get('/api/v1/config/oberflaechen/')

# Line 51, 60: Fix komplexität endpoints
- const response = await apiClient.get('/api/v1/config/komplexitäten/')
+ const response = await apiClient.get('/api/v1/config/komplexitaet/')
```

### Option 2: Add Backend Aliases (Alternative)

```python
# File: backend/api/v1/urls.py
# Add auth aliases
urlpatterns = [
    # Add login alias for frontend compatibility
    path('auth/login/', auth_views.obtain_auth_token, name='auth-login'),

    # Add calculation alias
    path('calculations/calculate/', PriceCalculationView.as_view(), name='calculate-alias'),

    # ... rest of patterns
]
```

---

## 🎯 RECOMMENDED APPROACH

### Strategy: Frontend Fixes First

**Why:**
1. ✅ Faster - just update hook files
2. ✅ No backend deployment needed
3. ✅ Backend API is already production-ready
4. ✅ Follows backend's German naming conventions

### Steps:
```bash
# 1. Fix frontend hooks (15 minutes)
cd frontend_new/src/lib/hooks
# Apply fixes to: useAuth.ts, useCalculation.ts, useConfig.ts

# 2. Test locally (10 minutes)
npm run dev
# Test: Login -> Upload Document -> Calculate Price -> View Config

# 3. Deploy (5 minutes)
npm run build
# Deploy to Vercel/Netlify/Cloud Run
```

---

## 📁 FILES TO MODIFY

### Frontend (Priority Order)

1. **`frontend_new/src/lib/hooks/useAuth.ts`** (Critical)
   - Line 44: Change endpoint to `/api/auth/token/`
   - Line 56: Change register to `/api/auth/register/`
   - Update payload field from `email` to `username`

2. **`frontend_new/src/lib/hooks/useCalculation.ts`** (Critical)
   - Line 50: Change endpoint to `/api/v1/calculate/price/`

3. **`frontend_new/src/lib/hooks/useConfig.ts`** (Critical)
   - Line 42: Change to `/api/v1/config/oberflaechen/`
   - Line 51: Change to `/api/v1/config/komplexitaet/`

4. **`frontend_new/src/lib/hooks/useTransparency.ts`** (Medium)
   - Line 62: Change to `/api/v1/calculations/explanations/`
   - Line 74: Change to `/api/v1/benchmarks/user/`
   - Line 82: Change to `/api/v1/feedback/calculation/`

5. **`frontend_new/.env`** (Check)
   - Ensure `VITE_API_URL` points to correct backend

### Backend (If choosing Option 2)

1. **`backend/api/v1/urls.py`**
   - Add auth login alias
   - Add calculation alias (optional)

2. **`backend/config/settings/development.py`**
   - Verify CORS settings
   - Add frontend URL to `CORS_ALLOWED_ORIGINS`

---

## 🚀 DEPLOYMENT CHECKLIST

### Before Deployment

- [ ] All critical endpoint mismatches fixed
- [ ] CORS configured for production domain
- [ ] Environment variables set in production
- [ ] Database migrations applied (Supabase)
- [ ] Static files configured (WhiteNoise/Cloud Storage)

### Production Environment Variables

#### Backend (.env.production)
```bash
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<generate-new-secure-key>
DATABASE_URL=<supabase-postgres-url>
ALLOWED_HOSTS=draftcraft-backend.run.app,api.draftcraft.de
CORS_ALLOWED_ORIGINS=https://draftcraft.vercel.app,https://www.draftcraft.de
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-key.json
```

#### Frontend (.env.production)
```bash
VITE_API_URL=https://draftcraft-backend.run.app
NODE_ENV=production
```

---

## 🎓 NEXT STEPS

### Immediate Actions (Today)
1. Review this document with team
2. Decide: Fix frontend or add backend aliases?
3. Apply critical fixes (Auth, Calculation, Config)
4. Test login and basic workflows

### This Week
1. Complete transparency integration
2. Add batch processing UI
3. Polish admin dashboard
4. End-to-end testing

### Next Sprint
1. Advanced features (pattern analysis UI)
2. Performance optimization
3. User acceptance testing
4. Production deployment

---

## 📞 SUPPORT

**Questions about:**
- Backend API: See `backend/api/v1/urls.py` for all endpoints
- Frontend hooks: See `frontend_new/src/lib/hooks/`
- Authentication: See `backend/api/v1/auth_views.py`
- CORS issues: Check browser DevTools Network tab

**Testing:**
```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend_new
npm run dev

# Test auth
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

---

**Document Status:** Ready for Implementation
**Last Updated:** 2025-12-11
**Next Review:** After Phase 1 completion
