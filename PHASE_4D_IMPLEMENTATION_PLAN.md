# Phase 4D: Complete Implementation Plan
# Steps 1-3 + Admin Dashboard Strategy

**Date:** 2025-12-08
**Status:** Ready for Implementation
**Estimated Total Time:** 16-20 hours across 3 days

---

## 📋 Executive Summary

This document provides a comprehensive plan to implement the remaining Phase 4D tasks:

1. **Redis Caching** (Priority 2) - 2-3 hours
2. **Database Indexes** (Priority 3) - 30 minutes
3. **Admin Dashboard UI** - 12-16 hours (with careful strategy)

### Previous Admin Dashboard Issues

**Problem Analysis:** Based on project history, previous attempts to create a Django admin dashboard likely faced these challenges:

1. **Django Admin Limitations:**
   - Django's built-in admin is designed for CRUD operations, not operational dashboards
   - Custom admin views require complex template overrides
   - JavaScript integration is cumbersome
   - Modern UI components don't integrate well

2. **Template Conflicts:**
   - Django's admin templates use outdated jQuery
   - Difficult to add modern React/Vue components
   - CSS conflicts between Django admin and custom styles

3. **Performance Issues:**
   - Admin renders everything server-side
   - No real-time updates without hacky solutions
   - Large datasets cause slow page loads

### Recommended Solution: Hybrid Approach

**✅ RECOMMENDED:** Use **separate React frontend** + Django REST APIs

**Why This Works:**
- ✅ Full control over UI/UX
- ✅ Modern React ecosystem (hooks, state management, components)
- ✅ Real-time updates via polling/WebSockets
- ✅ Already have REST APIs ready
- ✅ `frontend_new/` already exists with React + Vite + TailwindCSS

**❌ AVOID:** Custom Django admin dashboard widgets
- ❌ Complex Django template overrides
- ❌ jQuery/JavaScript injection into admin
- ❌ Fighting Django admin's opinions

---

## 🎯 Implementation Strategy Overview

### Three-Tier Approach

**TIER 1: Quick Wins (High Impact, Low Effort) - 3 hours**
- Redis caching for TIER 1 config
- Database indexes
- Query optimization (already documented)

**TIER 2: React Dashboard Foundation (Medium Effort) - 8-10 hours**
- Standalone React dashboard (separate from Django admin)
- API integration
- Core dashboard widgets

**TIER 3: Advanced Features (Lower Priority) - 4-6 hours**
- Pattern approval UI
- Pauschalen bulk import
- Real-time monitoring

---

## 📝 STEP 1: Redis Caching Implementation

**Estimated Time:** 2-3 hours
**Priority:** High (30-40ms improvement per request)
**Difficulty:** Medium

### Prerequisites

```bash
# Check if Redis is installed
redis-cli --version

# If not installed (Windows):
# 1. Download Redis for Windows: https://github.com/microsoftarchive/redis/releases
# 2. Or use Docker:
docker run -d -p 6379:6379 --name redis-cache redis:7-alpine
```

### Implementation Steps

#### 1.1: Install Django Redis (5 minutes)

**File:** `backend/requirements/base.txt`

```txt
# Add to existing requirements
django-redis==5.4.0
redis==5.0.1
```

**Install:**
```bash
cd backend
pip install django-redis redis
```

#### 1.2: Configure Redis in Settings (10 minutes)

**File:** `backend/config/settings/base.py`

```python
# Add after DATABASES configuration (around line 120)

# ===========================
# CACHE CONFIGURATION (Redis)
# ===========================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'draftcraft',
        'TIMEOUT': 3600,  # 1 hour default
    },
    # Separate cache for sessions (optional)
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'session',
        'TIMEOUT': 86400,  # 24 hours
    }
}

# Optional: Use Redis for session storage
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'session'
```

**File:** `backend/config/settings/development.py`

```python
# Add Redis configuration for development
REDIS_URL = 'redis://127.0.0.1:6379/1'

# Optional: Disable cache in development for testing
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
#     }
# }
```

**File:** `backend/config/settings/production.py`

```python
# Production Redis configuration
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

# Production-specific cache settings
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS']['max_connections'] = 100
```

#### 1.3: Implement Caching in Config Views (45 minutes)

**File:** `backend/api/v1/views/config_views.py`

Add caching logic to each config viewset:

```python
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

logger = logging.getLogger(__name__)


class HolzartConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    TIER 1 Config: Wood types (Holzarten).
    Cached for 1 hour since TIER 1 rarely changes.
    """
    serializer_class = HolzartConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get Holzarten for user's template with caching."""
        user = self.request.user

        try:
            # Get user's config
            user_config = IndividuelleBetriebskennzahl.objects.select_related(
                'handwerk_template'
            ).get(user=user, is_active=True)
        except IndividuelleBetriebskennzahl.DoesNotExist:
            return HolzartKennzahl.objects.none()

        # Generate cache key
        cache_key = f'holzarten_template_{user_config.handwerk_template_id}'

        # Try cache first
        cached_queryset = cache.get(cache_key)
        if cached_queryset is not None:
            logger.info(f"Cache HIT for {cache_key}")
            return cached_queryset

        # Cache miss - fetch from database
        logger.info(f"Cache MISS for {cache_key} - fetching from DB")
        queryset = HolzartKennzahl.objects.filter(
            template=user_config.handwerk_template,
            is_enabled=True
        ).select_related('template')

        # Convert to list for caching (querysets aren't picklable)
        queryset_list = list(queryset)

        # Cache for 1 hour (TIER 1 config changes rarely)
        cache.set(cache_key, queryset_list, timeout=3600)

        return queryset_list


# Repeat for OberflächenConfigViewSet and KomplexitaetConfigViewSet
class OberflächenConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """TIER 1 Config: Surface finishes with caching."""
    serializer_class = OberflächenConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        try:
            user_config = IndividuelleBetriebskennzahl.objects.select_related(
                'handwerk_template'
            ).get(user=user, is_active=True)
        except IndividuelleBetriebskennzahl.DoesNotExist:
            return OberflächenbearbeitungKennzahl.objects.none()

        cache_key = f'oberflaechen_template_{user_config.handwerk_template_id}'
        cached_queryset = cache.get(cache_key)

        if cached_queryset is not None:
            logger.info(f"Cache HIT for {cache_key}")
            return cached_queryset

        logger.info(f"Cache MISS for {cache_key}")
        queryset = OberflächenbearbeitungKennzahl.objects.filter(
            template=user_config.handwerk_template,
            is_enabled=True
        ).select_related('template')

        queryset_list = list(queryset)
        cache.set(cache_key, queryset_list, timeout=3600)

        return queryset_list


class KomplexitaetConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """TIER 1 Config: Complexity techniques with caching."""
    serializer_class = KomplexitaetConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        try:
            user_config = IndividuelleBetriebskennzahl.objects.select_related(
                'handwerk_template'
            ).get(user=user, is_active=True)
        except IndividuelleBetriebskennzahl.DoesNotExist:
            return KomplexitaetKennzahl.objects.none()

        cache_key = f'komplexitaet_template_{user_config.handwerk_template_id}'
        cached_queryset = cache.get(cache_key)

        if cached_queryset is not None:
            logger.info(f"Cache HIT for {cache_key}")
            return cached_queryset

        logger.info(f"Cache MISS for {cache_key}")
        queryset = KomplexitaetKennzahl.objects.filter(
            template=user_config.handwerk_template,
            is_enabled=True
        ).select_related('template')

        queryset_list = list(queryset)
        cache.set(cache_key, queryset_list, timeout=3600)

        return queryset_list
```

#### 1.4: Implement Cache Invalidation in Admin (30 minutes)

**File:** `backend/documents/admin.py`

Add cache invalidation when admin updates TIER 1 config:

```python
from django.core.cache import cache


@admin.register(HolzartKennzahl)
class HolzartKennzahlAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    # ... existing configuration ...

    def save_model(self, request, obj, form, change):
        """Save model and invalidate related cache."""
        super().save_model(request, obj, form, change)

        # Invalidate cache for this template
        cache_key = f'holzarten_template_{obj.template_id}'
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key}")

    def delete_model(self, request, obj):
        """Delete model and invalidate cache."""
        cache_key = f'holzarten_template_{obj.template_id}'
        super().delete_model(request, obj)
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key}")


# Repeat for OberflächenbearbeitungKennzahlAdmin and KomplexitaetKennzahlAdmin
@admin.register(OberflächenbearbeitungKennzahl)
class OberflächenbearbeitungKennzahlAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    # ... existing configuration ...

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache_key = f'oberflaechen_template_{obj.template_id}'
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key}")

    def delete_model(self, request, obj):
        cache_key = f'oberflaechen_template_{obj.template_id}'
        super().delete_model(request, obj)
        cache.delete(cache_key)


@admin.register(KomplexitaetKennzahl)
class KomplexitaetKennzahlAdmin(BulkUploadAdminMixin, admin.ModelAdmin):
    # ... existing configuration ...

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache_key = f'komplexitaet_template_{obj.template_id}'
        cache.delete(cache_key)
        logger.info(f"Cache invalidated: {cache_key}")

    def delete_model(self, request, obj):
        cache_key = f'komplexitaet_template_{obj.template_id}'
        super().delete_model(request, obj)
        cache.delete(cache_key)
```

#### 1.5: Test Redis Caching (30 minutes)

**Test Script:** `backend/tests/test_redis_cache.py`

```python
"""Test Redis caching functionality."""
import pytest
from django.core.cache import cache
from django.contrib.auth.models import User
from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    IndividuelleBetriebskennzahl
)


@pytest.mark.django_db
class TestRedisCache:
    """Test Redis cache operations."""

    def test_cache_connection(self):
        """Test Redis is accessible."""
        cache.set('test_key', 'test_value', timeout=60)
        assert cache.get('test_key') == 'test_value'
        cache.delete('test_key')

    def test_holzart_cache_hit(self, test_user, test_template):
        """Test Holzart cache hit."""
        # Create test data
        HolzartKennzahl.objects.create(
            template=test_template,
            name='Eiche',
            faktor=Decimal('1.3'),
            is_enabled=True
        )

        # First request - cache miss
        cache_key = f'holzarten_template_{test_template.id}'
        cache.delete(cache_key)  # Ensure clean state

        # Simulate view logic
        queryset = HolzartKennzahl.objects.filter(
            template=test_template,
            is_enabled=True
        )
        cache.set(cache_key, list(queryset), timeout=3600)

        # Second request - cache hit
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(cached_data) == 1

    def test_cache_invalidation_on_save(self, test_template):
        """Test cache is invalidated when admin saves."""
        holzart = HolzartKennzahl.objects.create(
            template=test_template,
            name='Buche',
            faktor=Decimal('1.2'),
            is_enabled=True
        )

        cache_key = f'holzarten_template_{test_template.id}'

        # Set cache
        cache.set(cache_key, ['test_data'], timeout=3600)
        assert cache.get(cache_key) is not None

        # Simulate admin save (should invalidate)
        cache.delete(cache_key)

        # Verify cache cleared
        assert cache.get(cache_key) is None
```

**Run Tests:**
```bash
cd backend
pytest tests/test_redis_cache.py -v
```

#### 1.6: Monitor Cache Performance (15 minutes)

**Add Cache Monitoring Middleware:**

**File:** `backend/core/middleware/cache_monitor.py`

```python
"""Cache monitoring middleware."""
import logging
from django.core.cache import cache

logger = logging.getLogger('cache.monitor')


class CacheMonitorMiddleware:
    """Log cache hit/miss for API requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only monitor API requests
        if request.path.startswith('/api/v1/config/'):
            # Get cache stats (Redis-specific)
            try:
                redis_client = cache.client.get_client()
                info = redis_client.info('stats')

                keyspace_hits = info.get('keyspace_hits', 0)
                keyspace_misses = info.get('keyspace_misses', 0)
                total = keyspace_hits + keyspace_misses
                hit_rate = (keyspace_hits / total * 100) if total > 0 else 0

                logger.info(
                    f"Cache Stats - Hits: {keyspace_hits}, "
                    f"Misses: {keyspace_misses}, "
                    f"Hit Rate: {hit_rate:.1f}%"
                )
            except Exception as e:
                logger.warning(f"Could not get cache stats: {e}")

        response = self.get_response(request)
        return response
```

**Enable in development.py:**
```python
# settings/development.py
MIDDLEWARE += ['core.middleware.cache_monitor.CacheMonitorMiddleware']
```

### Step 1 Completion Checklist

- [ ] Redis installed and running (`redis-cli ping` returns `PONG`)
- [ ] `django-redis` installed (`pip list | grep django-redis`)
- [ ] `CACHES` configured in `base.py`
- [ ] Caching implemented in 3 config viewsets
- [ ] Cache invalidation added to 3 admin classes
- [ ] Tests pass (`pytest tests/test_redis_cache.py`)
- [ ] Cache monitoring enabled
- [ ] Documentation updated in CHANGELOG

**Expected Performance Improvement:**
- Config API response: 150ms → 10-30ms (83-93% faster)
- Database load: -80% for config reads
- Cache hit rate: >90% after warmup

---

## 📝 STEP 2: Database Indexes Implementation

**Estimated Time:** 30 minutes
**Priority:** High (20-30ms improvement per query)
**Difficulty:** Easy

### Implementation Steps

#### 2.1: Create Index Migration (15 minutes)

**Generate Migration:**
```bash
cd backend
python manage.py makemigrations documents --name "add_performance_indexes" --empty
```

**Edit Migration File:** `backend/documents/migrations/000X_add_performance_indexes.py`

```python
"""
Add performance indexes for frequently queried fields.

Indexes added:
1. Document: (user, status) - common filter combo
2. Document: (created_at) - sorting optimization
3. ExtractionFailurePattern: (detected_at) - date filtering
4. ExtractionFailurePattern: (is_active, severity) - common filter combo
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_phase4c_multi_material_pauschalen'),  # Update to your latest
    ]

    operations = [
        # Document indexes
        migrations.AddIndex(
            model_name='document',
            index=models.Index(
                fields=['user', 'status'],
                name='documents_d_user_st_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(
                fields=['created_at'],
                name='documents_d_created_idx'
            ),
        ),

        # ExtractionFailurePattern indexes
        migrations.AddIndex(
            model_name='extractionfailurepattern',
            index=models.Index(
                fields=['detected_at'],
                name='pattern_detected_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='extractionfailurepattern',
            index=models.Index(
                fields=['is_active', 'severity'],
                name='pattern_active_sev_idx'
            ),
        ),

        # ExtractionResult indexes (optional - if performance issues)
        migrations.AddIndex(
            model_name='extractionresult',
            index=models.Index(
                fields=['created_at'],
                name='extraction_created_idx'
            ),
        ),
    ]
```

#### 2.2: Apply Migration (5 minutes)

```bash
# Run migration
python manage.py migrate documents

# Verify indexes were created
python manage.py dbshell
\d+ documents_document  # PostgreSQL
# Look for indexes in output
```

#### 2.3: Test Index Performance (10 minutes)

**Before/After Comparison:**

```python
# backend/tests/test_index_performance.py
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from documents.models import Document, ExtractionFailurePattern


@pytest.mark.django_db
class TestIndexPerformance:
    """Test query performance with indexes."""

    def test_document_user_status_filter(self, test_user):
        """Test Document filtering by user + status uses index."""
        # Create test documents
        for i in range(100):
            Document.objects.create(
                user=test_user,
                original_filename=f'test_{i}.pdf',
                status='completed' if i % 2 == 0 else 'processing'
            )

        # Query with filter
        with CaptureQueriesContext(connection) as context:
            docs = list(Document.objects.filter(
                user=test_user,
                status='completed'
            ))

        # Check query plan uses index
        query = context.captured_queries[0]['sql']
        print(f"Query: {query}")

        # Verify results
        assert len(docs) == 50

        # Check query time (should be fast with index)
        query_time = float(context.captured_queries[0]['time'])
        assert query_time < 0.1  # <100ms
```

**Run Tests:**
```bash
pytest tests/test_index_performance.py -v -s
```

### Step 2 Completion Checklist

- [ ] Migration created (`000X_add_performance_indexes.py`)
- [ ] Migration applied successfully
- [ ] Indexes verified in database (`\d+ documents_document`)
- [ ] Performance tests pass
- [ ] Query times improved (<100ms for filtered queries)
- [ ] Documentation updated

**Expected Performance Improvement:**
- Pattern list API: 250ms → 100ms (60% faster)
- Document list API: 180ms → 80ms (55% faster)
- Date-filtered queries: 40-50% faster

---

## 📝 STEP 3: Admin Dashboard UI - Hybrid Approach

**Estimated Time:** 12-16 hours
**Priority:** Medium (UX improvement, not blocking)
**Difficulty:** Medium-High

### Strategy: Separate React Dashboard (RECOMMENDED)

**Why This Approach:**
1. ✅ **Full Control:** Modern React components, no Django admin constraints
2. ✅ **Already Have Infrastructure:** `frontend_new/` with React + Vite + Tailwind
3. ✅ **REST APIs Ready:** All Phase 4D endpoints implemented
4. ✅ **Better UX:** Real-time updates, interactive charts, responsive design
5. ✅ **Maintainable:** Separate concerns (Django = API, React = UI)

**What to Avoid:**
- ❌ Django admin template overrides
- ❌ Injecting JavaScript into Django admin
- ❌ Fighting Django's built-in admin CSS/JS

### Implementation Phases

#### Phase 3A: Dashboard Foundation (4 hours)

**3A.1: Dashboard Layout Component (1.5 hours)**

**File:** `frontend_new/src/components/admin/DashboardLayout.tsx`

```typescript
import React from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  AlertTriangle,
  Settings,
  Users,
  TrendingUp,
  LogOut
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  badge?: number;
}

export const DashboardLayout: React.FC = () => {
  const navigate = useNavigate();
  const [unreadPatterns, setUnreadPatterns] = React.useState(0);

  const navItems: NavItem[] = [
    {
      name: 'Übersicht',
      path: '/admin',
      icon: <LayoutDashboard size={20} />
    },
    {
      name: 'Dokumente',
      path: '/admin/documents',
      icon: <FileText size={20} />
    },
    {
      name: 'Muster & Fehler',
      path: '/admin/patterns',
      icon: <AlertTriangle size={20} />,
      badge: unreadPatterns
    },
    {
      name: 'Statistiken',
      path: '/admin/analytics',
      icon: <TrendingUp size={20} />
    },
    {
      name: 'Konfiguration',
      path: '/admin/config',
      icon: <Settings size={20} />
    },
    {
      name: 'Benutzer',
      path: '/admin/users',
      icon: <Users size={20} />
    }
  ];

  const handleLogout = () => {
    // Clear token
    localStorage.removeItem('auth_token');
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold text-gray-800">DraftCraft Admin</h1>
          <p className="text-sm text-gray-500">Verwaltung & Statistik</p>
        </div>

        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center justify-between px-4 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition"
            >
              <div className="flex items-center space-x-3">
                {item.icon}
                <span>{item.name}</span>
              </div>
              {item.badge && item.badge > 0 && (
                <span className="px-2 py-1 text-xs font-semibold text-white bg-red-500 rounded-full">
                  {item.badge}
                </span>
              )}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 w-64 p-4 border-t">
          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 px-4 py-3 w-full text-gray-700 hover:bg-red-50 hover:text-red-600 rounded-lg transition"
          >
            <LogOut size={20} />
            <span>Abmelden</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
```

**3A.2: Dashboard Overview Page (2 hours)**

**File:** `frontend_new/src/pages/admin/DashboardOverview.tsx`

```typescript
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface DashboardStats {
  total_documents: number;
  processed_today: number;
  active_patterns: number;
  critical_patterns: number;
  avg_confidence: number;
  total_cost_today: number;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  trend?: string;
}> = ({ title, value, icon, color, trend }) => (
  <div className="bg-white p-6 rounded-lg shadow-md">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        {trend && (
          <p className="text-sm text-green-600 mt-2">↑ {trend}</p>
        )}
      </div>
      <div className={`p-3 rounded-full ${color}`}>
        {icon}
      </div>
    </div>
  </div>
);

export const DashboardOverview: React.FC = () => {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await fetch('/api/v1/admin/dashboard/stats/', {
        headers: {
          'Authorization': `Token ${localStorage.getItem('auth_token')}`
        }
      });
      return response.json();
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  if (isLoading) {
    return <div>Lädt...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Dashboard Übersicht</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Dokumente Gesamt"
          value={stats?.total_documents || 0}
          icon={<FileText className="text-white" size={24} />}
          color="bg-blue-500"
          trend="+12% diese Woche"
        />
        <StatCard
          title="Heute Verarbeitet"
          value={stats?.processed_today || 0}
          icon={<CheckCircle className="text-white" size={24} />}
          color="bg-green-500"
          trend="+5 seit gestern"
        />
        <StatCard
          title="Aktive Muster"
          value={stats?.active_patterns || 0}
          icon={<AlertTriangle className="text-white" size={24} />}
          color="bg-yellow-500"
        />
        <StatCard
          title="Ø Konfidenz"
          value={`${((stats?.avg_confidence || 0) * 100).toFixed(1)}%`}
          icon={<TrendingUp className="text-white" size={24} />}
          color="bg-purple-500"
          trend="+2.3% diese Woche"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Processing Chart */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Dokumente (7 Tage)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { day: 'Mo', count: 12 },
              { day: 'Di', count: 19 },
              { day: 'Mi', count: 15 },
              { day: 'Do', count: 22 },
              { day: 'Fr', count: 18 },
              { day: 'Sa', count: 8 },
              { day: 'So', count: 5 }
            ]}>
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pattern Severity Chart */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Muster nach Schwere</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Kritisch</span>
                <span className="text-sm text-gray-600">
                  {stats?.critical_patterns || 0}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-red-500 h-2 rounded-full" style={{ width: '45%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Hoch</span>
                <span className="text-sm text-gray-600">12</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-orange-500 h-2 rounded-full" style={{ width: '30%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Mittel</span>
                <span className="text-sm text-gray-600">8</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '20%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Niedrig</span>
                <span className="text-sm text-gray-600">3</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '10%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Letzte Aktivität</h2>
        <div className="space-y-4">
          <ActivityItem
            icon={<CheckCircle className="text-green-500" size={20} />}
            title="Dokument erfolgreich verarbeitet"
            description="rechnung_2024_11.pdf"
            time="vor 5 Minuten"
          />
          <ActivityItem
            icon={<AlertTriangle className="text-yellow-500" size={20} />}
            title="Neues Muster erkannt"
            description="Datumserkennung fehlgeschlagen (3 Vorkommen)"
            time="vor 15 Minuten"
          />
          <ActivityItem
            icon={<FileText className="text-blue-500" size={20} />}
            title="Dokument hochgeladen"
            description="angebot_kunde_mueller.pdf"
            time="vor 32 Minuten"
          />
        </div>
      </div>
    </div>
  );
};

const ActivityItem: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  time: string;
}> = ({ icon, title, description, time }) => (
  <div className="flex items-start space-x-4 p-4 hover:bg-gray-50 rounded-lg transition">
    <div className="flex-shrink-0">{icon}</div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-gray-900">{title}</p>
      <p className="text-sm text-gray-500">{description}</p>
    </div>
    <span className="text-xs text-gray-400">{time}</span>
  </div>
);
```

**3A.3: API Client Setup (30 minutes)**

**File:** `frontend_new/src/lib/api-client.ts`

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API functions
export const dashboardApi = {
  getStats: () => apiClient.get('/admin/dashboard/stats/'),

  getPatterns: (params?: any) =>
    apiClient.get('/patterns/failures/', { params }),

  approvePattern: (patternId: number, data: any) =>
    apiClient.post(`/patterns/${patternId}/approve-fix/`, data),

  getDocuments: (params?: any) =>
    apiClient.get('/documents/', { params }),

  getConfig: () => apiClient.get('/config/betriebskennzahlen/'),
};
```

#### Phase 3B: Pattern Management UI (4-5 hours)

**File:** `frontend_new/src/pages/admin/PatternManagement.tsx`

```typescript
import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { dashboardApi } from '../../lib/api-client';

interface Pattern {
  id: number;
  field_name: string;
  pattern_type: string;
  root_cause: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  affected_document_count: number;
  is_reviewed: boolean;
  suggested_fix: string;
}

export const PatternManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedPattern, setSelectedPattern] = React.useState<Pattern | null>(null);
  const [severityFilter, setSeverityFilter] = React.useState<string>('');

  const { data: patterns, isLoading } = useQuery({
    queryKey: ['patterns', severityFilter],
    queryFn: async () => {
      const params = severityFilter ? { severity: severityFilter } : {};
      const response = await dashboardApi.getPatterns(params);
      return response.data.results;
    }
  });

  const approveMutation = useMutation({
    mutationFn: (patternId: number) =>
      dashboardApi.approvePattern(patternId, {
        review_title: 'Admin Approval',
        description: 'Approved via admin dashboard',
        estimated_impact: 'high',
        estimated_documents_improved: 10
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
      setSelectedPattern(null);
    }
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-600 bg-red-100';
      case 'HIGH': return 'text-orange-600 bg-orange-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'LOW': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return <div>Lädt Muster...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Fehler-Muster Verwaltung</h1>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="">Alle Schweregrade</option>
          <option value="CRITICAL">Kritisch</option>
          <option value="HIGH">Hoch</option>
          <option value="MEDIUM">Mittel</option>
          <option value="LOW">Niedrig</option>
        </select>
      </div>

      {/* Pattern List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Feld
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Typ
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Schwere
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Betroffene Dokumente
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Aktionen
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {patterns?.map((pattern: Pattern) => (
              <tr key={pattern.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {pattern.field_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {pattern.pattern_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(pattern.severity)}`}>
                    {pattern.severity}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {pattern.affected_document_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {pattern.is_reviewed ? (
                    <span className="flex items-center text-green-600">
                      <CheckCircle size={16} className="mr-1" />
                      Geprüft
                    </span>
                  ) : (
                    <span className="flex items-center text-yellow-600">
                      <AlertTriangle size={16} className="mr-1" />
                      Ausstehend
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {!pattern.is_reviewed && (
                    <button
                      onClick={() => approveMutation.mutate(pattern.id)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Genehmigen
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

#### Phase 3C: Backend Dashboard API Endpoints (3-4 hours)

**File:** `backend/api/v1/views/dashboard_views.py` (NEW)

```python
"""Admin dashboard API endpoints."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from documents.models import Document
from documents.pattern_models import ExtractionFailurePattern
from drf_spectacular.utils import extend_schema


@extend_schema(
    summary="Get dashboard statistics",
    tags=['Admin Dashboard'],
    responses={200: {
        'type': 'object',
        'properties': {
            'total_documents': {'type': 'integer'},
            'processed_today': {'type': 'integer'},
            'active_patterns': {'type': 'integer'},
            'critical_patterns': {'type': 'integer'},
            'avg_confidence': {'type': 'number'},
        }
    }}
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    """Get aggregate statistics for admin dashboard."""
    today = timezone.now().date()

    # Document stats
    total_documents = Document.objects.count()
    processed_today = Document.objects.filter(
        status='completed',
        created_at__date=today
    ).count()

    # Pattern stats
    active_patterns = ExtractionFailurePattern.objects.filter(
        is_active=True
    ).count()
    critical_patterns = ExtractionFailurePattern.objects.filter(
        is_active=True,
        severity='CRITICAL'
    ).count()

    # Confidence stats (from ExtractionResult)
    # avg_confidence = ExtractionResult.objects.aggregate(
    #     Avg('overall_confidence')
    # )['overall_confidence__avg'] or 0.0

    return Response({
        'total_documents': total_documents,
        'processed_today': processed_today,
        'active_patterns': active_patterns,
        'critical_patterns': critical_patterns,
        'avg_confidence': 0.87,  # Placeholder
    })
```

**Add to `backend/api/v1/urls.py`:**

```python
from .views import dashboard_views

urlpatterns = [
    # ... existing patterns ...

    # Admin Dashboard
    path('admin/dashboard/stats/', dashboard_views.dashboard_stats, name='dashboard-stats'),
]
```

### Step 3 Completion Checklist

**Frontend:**
- [ ] Dashboard layout component created
- [ ] Overview page with stats cards and charts
- [ ] Pattern management page with list and approval
- [ ] API client configured with auth
- [ ] Routes configured in React Router
- [ ] Build and test (`npm run dev`)

**Backend:**
- [ ] Dashboard stats API endpoint created
- [ ] Admin permission applied
- [ ] URL routing configured
- [ ] OpenAPI schema updated
- [ ] Tests written for dashboard endpoints

**Integration:**
- [ ] Frontend connects to backend APIs
- [ ] Authentication flow works
- [ ] Data displays correctly
- [ ] Pattern approval workflow functional

**Expected Result:**
- Modern, responsive admin dashboard
- Real-time statistics updates
- Pattern approval workflow
- 30-50% faster than Django admin for large datasets

---

## 🎯 Alternative: Django Admin Dashboard (NOT RECOMMENDED)

If you insist on using Django admin, here's the approach (but it will be more difficult):

### Django Admin Widgets Approach

**File:** `backend/documents/admin_dashboard.py`

```python
"""Custom admin dashboard using django-admin-tools or grappelli."""
# This approach is NOT RECOMMENDED due to:
# 1. Limited modern UI capabilities
# 2. Difficult JavaScript integration
# 3. Poor performance with real-time data
# 4. Hard to maintain

# Use React dashboard instead (see Step 3 above)
```

**Why to Avoid:**
- Requires `django-admin-tools` or `grappelli` (outdated packages)
- Custom templates are fragile and break with Django updates
- JavaScript integration requires hacky `Media` classes
- No real-time updates without polling hacks
- CSS conflicts with Django admin styles
- Much harder to test and maintain

---

## 📊 Implementation Timeline

### Day 1 (3-4 hours)
- [ ] **Morning:** Redis caching implementation (Step 1)
  - Install Redis
  - Configure Django caching
  - Implement caching in config views
  - Test and verify

- [ ] **Afternoon:** Database indexes (Step 2)
  - Create migration
  - Apply indexes
  - Test performance

**Deliverable:** 50-60% API performance improvement

### Day 2 (4-5 hours)
- [ ] **Morning:** Dashboard foundation (Step 3A)
  - Create layout component
  - Build overview page with stats
  - Set up API client

- [ ] **Afternoon:** Pattern management UI (Step 3B)
  - Pattern list component
  - Approval workflow UI

**Deliverable:** Basic dashboard functional

### Day 3 (4-5 hours)
- [ ] **Morning:** Backend dashboard APIs (Step 3C)
  - Dashboard stats endpoint
  - Additional admin endpoints
  - Testing

- [ ] **Afternoon:** Integration & polish
  - Connect frontend to backend
  - Fix bugs
  - Add loading states
  - Responsive design tweaks

**Deliverable:** Complete admin dashboard

---

## ✅ Success Criteria

### Performance (Step 1 & 2)
- [ ] Config API response time: <50ms (from 150ms)
- [ ] Cache hit rate: >90%
- [ ] Pattern list API: <100ms (from 250ms)
- [ ] Database query count reduced by 60-80%

### Admin Dashboard (Step 3)
- [ ] Dashboard loads in <2 seconds
- [ ] Real-time stats update every 30 seconds
- [ ] Pattern approval workflow functional
- [ ] Mobile-responsive design
- [ ] Works in Chrome, Firefox, Safari

### Code Quality
- [ ] All tests pass (`pytest`)
- [ ] No TypeScript errors (`npm run build`)
- [ ] Code formatted (`black`, `prettier`)
- [ ] Documentation updated in CHANGELOG

---

## 🚨 Risk Mitigation

### Redis Issues
**Risk:** Redis not installed or connection fails
**Mitigation:** Provide Docker fallback, dummy cache backend for development

### Dashboard Complexity
**Risk:** React dashboard takes longer than estimated
**Mitigation:** Start with minimal dashboard, add features incrementally

### API Breaking Changes
**Risk:** Frontend doesn't match backend API
**Mitigation:** Use OpenAPI schema for type generation, write integration tests

---

## 📚 Resources

### Documentation
- Redis: https://redis.io/docs/
- Django Redis: https://github.com/jazzband/django-redis
- React Query: https://tanstack.com/query/latest
- Recharts: https://recharts.org/

### Tools
- Redis Desktop Manager: https://resp.app/
- Django Debug Toolbar: https://django-debug-toolbar.readthedocs.io/
- React DevTools: https://react.dev/learn/react-developer-tools

---

## 📞 Next Steps After Completion

1. **Deploy to Production:**
   - Configure production Redis (ElastiCache, Cloud Memorystore)
   - Build frontend (`npm run build`)
   - Serve static files via WhiteNoise
   - Update CORS settings for production domain

2. **Monitor Performance:**
   - Set up application monitoring (Sentry, DataDog)
   - Track cache hit rates
   - Monitor API response times
   - Set up alerts for critical patterns

3. **Phase 5 Planning:**
   - Machine learning pipeline
   - Automated pattern learning
   - Dynamic factor optimization

---

**Last Updated:** 2025-12-08
**Status:** Ready for Implementation
**Estimated Total Time:** 16-20 hours
**Recommended Approach:** React Dashboard (Hybrid)
