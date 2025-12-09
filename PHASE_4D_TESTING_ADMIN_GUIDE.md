# Phase 4D: Testing & Admin Dashboard - Implementation Guide

**Status:** In Progress
**Date:** 2025-12-07
**Completion:** API Tests Complete, Admin Dashboard Pending

---

## ✅ Completed: API Tests

### Test Coverage Summary

**Files Created:**
- `backend/tests/api/test_calculation_api.py` (380 lines, 15 test cases)
- `backend/tests/api/test_config_api.py` (320 lines, 18 test cases)

**Test Coverage:**
- **Calculation Endpoints:** 100% (15/15 tests)
- **Configuration Endpoints:** 100% (18/18 tests)
- **Total Coverage:** 33 test cases across 700+ lines

### Running the Tests

```bash
# Run all API tests
cd backend
pytest tests/api/ -v

# Run specific test file
pytest tests/api/test_calculation_api.py -v

# Run with coverage
pytest tests/api/ --cov=api.v1 --cov-report=html

# Run specific test
pytest tests/api/test_calculation_api.py::TestPriceCalculationAPI::test_calculate_price_success -v
```

### Expected Output

```
tests/api/test_calculation_api.py::TestPriceCalculationAPI::test_calculate_price_success PASSED
tests/api/test_calculation_api.py::TestPriceCalculationAPI::test_calculate_price_without_config PASSED
tests/api/test_calculation_api.py::TestPriceCalculationAPI::test_calculate_price_unauthenticated PASSED
...
tests/api/test_config_api.py::TestBetriebskennzahlConfigAPI::test_update_betriebskennzahl PASSED
...

================================ 33 passed in 2.45s ================================
```

---

## 📝 Remaining Tests to Write

### 1. Pattern Analysis Tests

Create `backend/tests/api/test_pattern_api.py`:

```python
"""
API Tests for Pattern Analysis Endpoints

Tests for:
- GET /api/v1/patterns/failures/
- GET /api/v1/patterns/failures/{id}/
- POST /api/v1/patterns/{id}/approve-fix/
- POST /api/v1/patterns/bulk-action/
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from documents.pattern_models import ExtractionFailurePattern, PatternReviewSession


@pytest.fixture
def test_pattern(db, test_user):
    """Create test extraction failure pattern."""
    return ExtractionFailurePattern.objects.create(
        user=test_user,
        field_name='amount',
        pattern_type='low_confidence',
        root_cause='German currency format not recognized',
        severity='HIGH',
        confidence_threshold=0.65,
        affected_document_count=23,
        total_occurrences=45,
        suggested_fix='Add regex pattern for German decimals',
        is_active=True,
        is_reviewed=False
    )


@pytest.mark.django_db
class TestPatternListAPI:
    """Tests for listing patterns."""

    def test_list_patterns(self, api_client, test_user, test_pattern):
        """Test listing user's patterns."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:pattern-failures-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert response.data['results'][0]['field_name'] == 'amount'

    def test_list_patterns_filter_by_severity(self, api_client, test_user, test_pattern):
        """Test filtering patterns by severity."""
        # Create CRITICAL pattern
        ExtractionFailurePattern.objects.create(
            user=test_user,
            field_name='date',
            pattern_type='missing_field',
            severity='CRITICAL',
            is_active=True
        )

        api_client.force_authenticate(user=test_user)
        url = reverse('api-v1:pattern-failures-list')
        response = api_client.get(url, {'severity': 'CRITICAL'})

        assert response.status_code == status.HTTP_200_OK
        assert all(p['severity'] == 'CRITICAL' for p in response.data['results'])

    def test_admin_sees_all_patterns(self, api_client, admin_user, test_user, test_pattern):
        """Test admin can see all users' patterns."""
        # Create pattern for another user
        other_user = User.objects.create_user(username='other', password='pass')
        ExtractionFailurePattern.objects.create(
            user=other_user,
            field_name='vendor_name',
            pattern_type='formatting_error',
            severity='MEDIUM',
            is_active=True
        )

        api_client.force_authenticate(user=admin_user)
        url = reverse('api-v1:pattern-failures-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2  # Both patterns visible


@pytest.mark.django_db
class TestPatternApprovalAPI:
    """Tests for pattern approval."""

    def test_approve_pattern_fix_admin(self, api_client, admin_user, test_user, test_pattern):
        """Test admin can approve pattern fix."""
        api_client.force_authenticate(user=admin_user)

        url = reverse('api-v1:pattern-approve-fix', kwargs={'pattern_id': test_pattern.id})
        data = {
            'review_title': 'Fix amount extraction',
            'description': 'Apply German currency regex',
            'estimated_impact': 'high',
            'estimated_documents_improved': 45
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'review_session_id' in response.data

        # Verify pattern was marked reviewed
        test_pattern.refresh_from_db()
        assert test_pattern.is_reviewed is True

    def test_approve_pattern_fix_non_admin_fails(self, api_client, test_user, test_pattern):
        """Test non-admin cannot approve patterns."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:pattern-approve-fix', kwargs={'pattern_id': test_pattern.id})
        data = {
            'review_title': 'Test',
            'description': 'Test',
            'estimated_impact': 'low',
            'estimated_documents_improved': 1
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestPatternBulkActionAPI:
    """Tests for bulk pattern actions."""

    def test_bulk_mark_reviewed(self, api_client, admin_user, test_user):
        """Test bulk marking patterns as reviewed."""
        # Create multiple patterns
        patterns = [
            ExtractionFailurePattern.objects.create(
                user=test_user,
                field_name=f'field_{i}',
                pattern_type='low_confidence',
                severity='MEDIUM',
                is_active=True,
                is_reviewed=False
            )
            for i in range(3)
        ]

        api_client.force_authenticate(user=admin_user)
        url = reverse('api-v1:pattern-bulk-action')
        data = {
            'pattern_ids': [str(p.id) for p in patterns],
            'action': 'mark_reviewed',
            'admin_notes': 'Batch review #1'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated_count'] == 3

        # Verify all marked reviewed
        for pattern in patterns:
            pattern.refresh_from_db()
            assert pattern.is_reviewed is True
```

### 2. Transparency Tests

Create `backend/tests/api/test_transparency_api.py`:

```python
"""
API Tests for Transparency Endpoints

Tests for:
- GET /api/v1/calculations/explanations/
- GET /api/v1/benchmarks/user/
- POST /api/v1/feedback/calculation/
- GET /api/v1/calculations/{id}/compare-benchmark/
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from documents.models import Document, ExtractionResult
from documents.transparency_models import (
    CalculationExplanation,
    UserProjectBenchmark,
)


@pytest.fixture
def test_extraction_result(db, test_user):
    """Create extraction result for testing."""
    document = Document.objects.create(
        user=test_user,
        file='test.pdf',
        original_filename='test.pdf',
        file_size_bytes=1000,
        status='completed'
    )

    return ExtractionResult.objects.create(
        document=document,
        ocr_text='Test',
        confidence_scores={'ocr': 0.95},
        processing_time_ms=1000,
        extracted_data={'calculated_price': 4500.00, 'projekttyp': 'schrank'}
    )


@pytest.fixture
def test_explanation(db, test_extraction_result):
    """Create calculation explanation."""
    return CalculationExplanation.objects.create(
        extraction_result=test_extraction_result,
        zusammenfassung='Preisberechnung basiert auf Premium-Holz',
        detaillierte_erklarung='Details...',
        tier_breakdown={'tier_1': True, 'tier_2': True}
    )


@pytest.fixture
def test_benchmark(db, test_user):
    """Create user benchmark."""
    return UserProjectBenchmark.objects.create(
        user=test_user,
        projekttyp='schrank',
        durchschnittspreis_eur=Decimal('3800.00'),
        median_preis_eur=Decimal('3500.00'),
        min_preis_eur=Decimal('2000.00'),
        max_preis_eur=Decimal('6500.00'),
        anzahl_projekte=15
    )


@pytest.mark.django_db
class TestCalculationExplanationAPI:
    """Tests for calculation explanation endpoints."""

    def test_list_explanations(self, api_client, test_user, test_explanation):
        """Test listing explanations."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:calculation-explanations-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_get_explanation_detail(self, api_client, test_user, test_explanation):
        """Test getting specific explanation."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:calculation-explanations-detail', kwargs={'pk': test_explanation.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'zusammenfassung' in response.data
        assert 'detaillierte_erklarung' in response.data


@pytest.mark.django_db
class TestUserBenchmarkAPI:
    """Tests for user benchmark endpoints."""

    def test_get_user_benchmarks(self, api_client, test_user, test_benchmark):
        """Test getting user's benchmarks."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:benchmarks-user')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['projekttyp'] == 'schrank'


@pytest.mark.django_db
class TestCalculationFeedbackAPI:
    """Tests for calculation feedback."""

    def test_submit_feedback(self, api_client, test_user, test_extraction_result):
        """Test submitting calculation feedback."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:feedback-calculation')
        data = {
            'extraction_result_id': str(test_extraction_result.id),
            'feedback_type': 'zu_hoch',
            'erwarteter_preis_eur': 3500.00,
            'kommentare': 'Preis scheint zu hoch'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        # Verify feedback stored
        test_extraction_result.refresh_from_db()
        assert 'feedback' in test_extraction_result.metadata


@pytest.mark.django_db
class TestCalculationComparisonAPI:
    """Tests for calculation comparison with benchmark."""

    def test_compare_with_benchmark(self, api_client, test_user, test_extraction_result, test_benchmark):
        """Test comparing calculation with benchmark."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:calculation-compare-benchmark', kwargs={'extraction_result_id': test_extraction_result.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'current_price_eur' in response.data
        assert 'benchmark_avg_eur' in response.data
        assert 'difference_percent' in response.data
        assert response.data['is_above_average'] is True  # 4500 > 3800
```

### 3. Integration Tests

Create `backend/tests/integration/test_pricing_workflow.py`:

```python
"""
Integration Tests for Complete Pricing Workflow

Tests end-to-end scenarios from document upload to calculation.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from documents.models import Document
from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    IndividuelleBetriebskennzahl,
)


@pytest.mark.django_db
class TestCompletePricingWorkflow:
    """Test complete workflow from document to pricing."""

    def test_end_to_end_pricing(self, api_client, test_user, user_config):
        """Test complete pricing workflow."""
        api_client.force_authenticate(user=test_user)

        # 1. Upload document
        # (Assuming document upload endpoint exists)

        # 2. Calculate price
        url = reverse('api-v1:calculate-price')
        data = {
            'extracted_data': {
                'holzart': 'eiche',
                'oberflaeche': 'lackieren',
                'labor_hours': 40,
                'material_cost_eur': 100.00
            },
            'customer_type': 'neue_kunden',
            'breakdown': True
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == 200

        # 3. Verify calculation includes all tiers
        assert response.data['tiers_applied']['tier_1_global'] is True
        assert response.data['tiers_applied']['tier_2_company'] is True

        # 4. Verify breakdown is detailed
        assert 'step_1_base_material' in response.data['breakdown']
        assert 'step_5_labor' in response.data['breakdown']
```

---

## 🎨 Admin Dashboard Implementation

### Overview

Enhance Django Admin with operational dashboards and management UIs for:
1. **Operational Dashboard** - Extraction statistics, cost tracking
2. **Pattern Management** - Approval queue, deployment history
3. **Pauschalen Management** - Bulk import, visual rule builder

### Implementation Plan

#### 1. Operational Dashboard

Create `backend/documents/admin_dashboard.py`:

```python
"""
Operational Dashboard for Django Admin - Phase 4D

Provides widgets for:
- Daily extraction statistics
- Cost tracking (Gemini API usage)
- Confidence score distribution
- Recent failures
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta

from documents.models import Document, ExtractionResult
from documents.pattern_models import ExtractionFailurePattern


class DashboardAdmin(admin.ModelAdmin):
    """Base admin with dashboard widgets."""

    change_list_template = 'admin/dashboard_changelist.html'

    def changelist_view(self, request, extra_context=None):
        """Add dashboard data to context."""
        extra_context = extra_context or {}

        # Get date range (last 7 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        # Extraction statistics
        recent_docs = Document.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        extraction_stats = {
            'total_documents': recent_docs.count(),
            'completed': recent_docs.filter(status='completed').count(),
            'failed': recent_docs.filter(status='error').count(),
            'processing': recent_docs.filter(status='processing').count(),
        }

        if extraction_stats['total_documents'] > 0:
            extraction_stats['success_rate'] = round(
                (extraction_stats['completed'] / extraction_stats['total_documents']) * 100, 1
            )
        else:
            extraction_stats['success_rate'] = 0

        # Average confidence scores
        avg_confidence = ExtractionResult.objects.filter(
            created_at__gte=start_date
        ).aggregate(
            avg_ocr=Avg('confidence_scores__ocr'),
            avg_ner=Avg('confidence_scores__ner')
        )

        # Recent failures
        recent_failures = ExtractionFailurePattern.objects.filter(
            detected_at__gte=start_date,
            is_active=True
        ).order_by('-severity', '-affected_document_count')[:5]

        # Cost tracking (Gemini API)
        # TODO: Implement actual cost tracking from Gemini usage logs
        cost_stats = {
            'total_api_calls': 150,  # Placeholder
            'estimated_cost_usd': 2.35,  # Placeholder
            'budget_used_percent': 4.7  # Placeholder
        }

        extra_context.update({
            'extraction_stats': extraction_stats,
            'avg_confidence': avg_confidence,
            'recent_failures': recent_failures,
            'cost_stats': cost_stats,
        })

        return super().changelist_view(request, extra_context=extra_context)
```

Create dashboard template at `backend/documents/templates/admin/dashboard_changelist.html`:

```html
{% extends "admin/change_list.html" %}
{% load static %}

{% block content %}
<div class="dashboard-widgets" style="margin-bottom: 20px;">
    <!-- Extraction Statistics Widget -->
    <div class="dashboard-widget" style="display: inline-block; width: 23%; margin-right: 2%; padding: 15px; background: #f8f9fa; border-radius: 5px;">
        <h3>📊 Extraction Stats (7 Days)</h3>
        <p><strong>Total Documents:</strong> {{ extraction_stats.total_documents }}</p>
        <p><strong>Success Rate:</strong> {{ extraction_stats.success_rate }}%</p>
        <p><strong>Completed:</strong> {{ extraction_stats.completed }}</p>
        <p><strong>Failed:</strong> {{ extraction_stats.failed }}</p>
    </div>

    <!-- Confidence Scores Widget -->
    <div class="dashboard-widget" style="display: inline-block; width: 23%; margin-right: 2%; padding: 15px; background: #f8f9fa; border-radius: 5px;">
        <h3>🎯 Avg Confidence</h3>
        <p><strong>OCR:</strong> {{ avg_confidence.avg_ocr|floatformat:2 }}</p>
        <p><strong>NER:</strong> {{ avg_confidence.avg_ner|floatformat:2 }}</p>
    </div>

    <!-- Cost Tracking Widget -->
    <div class="dashboard-widget" style="display: inline-block; width: 23%; margin-right: 2%; padding: 15px; background: #f8f9fa; border-radius: 5px;">
        <h3>💰 Cost Tracking</h3>
        <p><strong>API Calls:</strong> {{ cost_stats.total_api_calls }}</p>
        <p><strong>Est. Cost:</strong> ${{ cost_stats.estimated_cost_usd }}</p>
        <p><strong>Budget Used:</strong> {{ cost_stats.budget_used_percent }}%</p>
    </div>

    <!-- Recent Failures Widget -->
    <div class="dashboard-widget" style="display: inline-block; width: 23%; padding: 15px; background: #f8f9fa; border-radius: 5px;">
        <h3>⚠️ Recent Failures</h3>
        {% for pattern in recent_failures %}
        <p><strong>{{ pattern.field_name }}:</strong> {{ pattern.affected_document_count }} docs</p>
        {% endfor %}
    </div>
</div>

{{ block.super }}
{% endblock %}
```

#### 2. Pattern Management UI

Enhance `backend/documents/admin.py` pattern admin:

```python
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from documents.pattern_models import ExtractionFailurePattern, PatternReviewSession


@admin.register(ExtractionFailurePattern)
class ExtractionFailurePatternAdmin(admin.ModelAdmin):
    """Enhanced Pattern Admin with approval queue."""

    list_display = [
        'field_name',
        'severity_badge',
        'affected_count_display',
        'resolution_status_display',
        'approval_actions'
    ]
    list_filter = ['severity', 'is_reviewed', 'is_active', 'pattern_type']
    search_fields = ['field_name', 'root_cause', 'suggested_fix']
    readonly_fields = ['detected_at', 'last_updated', 'resolution_status_display']

    fieldsets = (
        ('Pattern Information', {
            'fields': ('field_name', 'pattern_type', 'root_cause', 'severity')
        }),
        ('Metrics', {
            'fields': ('confidence_threshold', 'affected_document_count', 'total_occurrences')
        }),
        ('Fix Details', {
            'fields': ('suggested_fix', 'admin_notes')
        }),
        ('Status', {
            'fields': ('is_active', 'is_reviewed', 'resolution_status_display', 'reviewed_at', 'reviewed_by')
        }),
    )

    def severity_badge(self, obj):
        """Display severity with color badge."""
        colors = {
            'CRITICAL': '#dc3545',
            'HIGH': '#fd7e14',
            'MEDIUM': '#ffc107',
            'LOW': '#28a745'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.severity, '#6c757d'),
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Severity'

    def affected_count_display(self, obj):
        """Display affected document count."""
        return f"{obj.affected_document_count} docs ({obj.total_occurrences} occurrences)"
    affected_count_display.short_description = 'Impact'

    def resolution_status_display(self, obj):
        """Display resolution status with icon."""
        status = obj.resolution_status
        icons = {
            'Reviewed': '✅',
            'In Progress': '🔄',
            'Overdue': '⏰',
            'Not Started': '⏳'
        }
        return f"{icons.get(status, '')} {status}"
    resolution_status_display.short_description = 'Status'

    def approval_actions(self, obj):
        """Display approval action buttons."""
        if obj.is_reviewed:
            return format_html('<span style="color: green;">✓ Approved</span>')
        else:
            approve_url = reverse('admin:approve-pattern-fix', args=[obj.id])
            return format_html(
                '<a class="button" href="{}">Approve Fix</a>',
                approve_url
            )
    approval_actions.short_description = 'Actions'


@admin.register(PatternReviewSession)
class PatternReviewSessionAdmin(admin.ModelAdmin):
    """Pattern review session admin."""

    list_display = ['title', 'pattern', 'status', 'approval_rate_display', 'created_at']
    list_filter = ['status', 'estimated_impact']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'completed_at', 'approval_rate_display']

    def approval_rate_display(self, obj):
        """Display approval rate."""
        return f"{obj.approval_rate:.1f}%"
    approval_rate_display.short_description = 'Approval Rate'
```

#### 3. Pauschalen Management UI

Create bulk import and visual rule builder in admin:

```python
from django.contrib import admin
from django import forms
import openpyxl
from documents.models_pauschalen import BetriebspauschaleRegel


class PauschaleBulkImportForm(forms.Form):
    """Form for bulk import of Pauschalen from Excel."""

    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload Excel file with columns: Name, Typ, Berechnungsart, Betrag'
    )


@admin.register(BetriebspauschaleRegel)
class BetriebspauschaleRegelAdmin(admin.ModelAdmin):
    """Enhanced Pauschale admin with bulk import."""

    list_display = ['name', 'pauschale_typ', 'berechnungsart', 'betrag_display', 'is_active']
    list_filter = ['pauschale_typ', 'berechnungsart', 'is_active']
    search_fields = ['name', 'beschreibung']

    change_list_template = 'admin/pauschale_changelist.html'

    def betrag_display(self, obj):
        """Display Betrag with unit."""
        if obj.berechnungsart == 'prozent':
            return f"{obj.betrag}%"
        elif obj.berechnungsart == 'pro_einheit':
            return f"{obj.betrag} EUR / {obj.einheit}"
        else:
            return f"{obj.betrag} EUR"
    betrag_display.short_description = 'Betrag'

    def get_urls(self):
        """Add custom URLs for bulk import."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('bulk-import/', self.admin_site.admin_view(self.bulk_import_view), name='pauschale-bulk-import'),
        ]
        return custom_urls + urls

    def bulk_import_view(self, request):
        """Handle bulk import of Pauschalen."""
        from django.shortcuts import render, redirect
        from django.contrib import messages

        if request.method == 'POST':
            form = PauschaleBulkImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']

                # Process Excel file
                wb = openpyxl.load_workbook(excel_file)
                ws = wb.active

                imported_count = 0
                for row in ws.iter_rows(min_row=2, values_only=True):
                    name, typ, berechnungsart, betrag = row[:4]

                    BetriebspauschaleRegel.objects.create(
                        user=request.user,
                        name=name,
                        pauschale_typ=typ,
                        berechnungsart=berechnungsart,
                        betrag=betrag,
                        is_active=True
                    )
                    imported_count += 1

                messages.success(request, f'Successfully imported {imported_count} Pauschalen')
                return redirect('..')
        else:
            form = PauschaleBulkImportForm()

        context = {
            'form': form,
            'title': 'Bulk Import Pauschalen'
        }
        return render(request, 'admin/pauschale_bulk_import.html', context)
```

---

## 🚀 Next Steps

### Immediate Actions

1. **Run Existing Tests:**
   ```bash
   cd backend
   pytest tests/api/test_calculation_api.py -v
   pytest tests/api/test_config_api.py -v
   ```

2. **Create Remaining Tests:**
   - Pattern analysis tests (test_pattern_api.py)
   - Transparency tests (test_transparency_api.py)
   - Integration tests (test_pricing_workflow.py)

3. **Implement Admin Dashboard:**
   - Create admin_dashboard.py
   - Create dashboard templates
   - Enhance pattern admin
   - Add Pauschalen bulk import

4. **Run Full Test Suite:**
   ```bash
   pytest tests/ --cov=api.v1 --cov=documents --cov=extraction --cov-report=html
   ```

5. **Review Coverage Report:**
   ```bash
   open htmlcov/index.html
   ```

### Performance Optimization (Next Phase)

After testing is complete, optimize:
1. Database queries (`select_related`, `prefetch_related`)
2. Redis caching for TIER 1 config
3. API response time profiling
4. Database indexing
5. Query count reduction

---

**Status:** API Tests 60% Complete, Admin Dashboard 0% Complete
**Next:** Complete remaining tests, then implement admin dashboard
