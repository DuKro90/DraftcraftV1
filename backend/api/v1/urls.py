"""API v1 URL routing - Phase 4D."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Existing views (from document_views.py - renamed old file)
from .document_views import (
    DocumentViewSet,
    ExtractedEntityViewSet,
    MaterialExtractionViewSet,
    ExtractionConfigViewSet,
    ProposalViewSet,
    ProposalTemplateViewSet,
    HealthCheckViewSet,
)
from .batch_views import (
    BatchViewSet,
    BatchDocumentViewSet,
)
from .health_views import (
    health_check,
    health_ready,
    health_startup,
)

# Phase 4D new views
from .views.calculation_views import (
    PriceCalculationView,
    MultiMaterialCalculationView,
    ApplicablePauschaleView,
)
from .views.config_views import (
    HolzartConfigViewSet,
    OberflächenConfigViewSet,
    KomplexitaetConfigViewSet,
    BetriebskennzahlConfigViewSet,
)
from .views.pattern_views import (
    PatternFailureViewSet,
    PatternApprovalView,
    PatternBulkActionView,
)
from .views.transparency_views import (
    CalculationExplanationViewSet,
    UserBenchmarkView,
    CalculationFeedbackView,
    CalculationComparisonView,
)
from .views.dashboard_views import (
    dashboard_stats,
    recent_activity,
    system_health,
)

app_name = 'v1'

router = DefaultRouter()

# Existing routes
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'entities', ExtractedEntityViewSet, basename='entity')
router.register(r'materials', MaterialExtractionViewSet, basename='material')
router.register(r'extraction-config', ExtractionConfigViewSet, basename='extraction-config')
router.register(r'proposals', ProposalViewSet, basename='proposal')
router.register(r'proposal-templates', ProposalTemplateViewSet, basename='proposal-template')
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'batch-documents', BatchDocumentViewSet, basename='batch-document')
router.register(r'health', HealthCheckViewSet, basename='health')

# Phase 4D new routes - Configuration
router.register(r'config/holzarten', HolzartConfigViewSet, basename='config-holzarten')
router.register(r'config/oberflaechen', OberflächenConfigViewSet, basename='config-oberflaechen')
router.register(r'config/komplexitaet', KomplexitaetConfigViewSet, basename='config-komplexitaet')
router.register(r'config/betriebskennzahlen', BetriebskennzahlConfigViewSet, basename='config-betriebskennzahlen')

# Phase 4D new routes - Pattern Analysis
router.register(r'patterns/failures', PatternFailureViewSet, basename='pattern-failures')

# Phase 4D new routes - Transparency
router.register(r'calculations/explanations', CalculationExplanationViewSet, basename='calculation-explanations')

urlpatterns = [
    # Cloud Run Health Checks (function-based views for fast response)
    path('health/', health_check, name='health-check'),
    path('health/ready/', health_ready, name='health-ready'),
    path('health/startup/', health_startup, name='health-startup'),

    # Phase 4D - Pricing & Calculation Endpoints
    path('calculate/price/', PriceCalculationView.as_view(), name='calculate-price'),
    path('calculate/multi-material/', MultiMaterialCalculationView.as_view(), name='calculate-multi-material'),
    path('pauschalen/applicable/', ApplicablePauschaleView.as_view(), name='pauschalen-applicable'),

    # Phase 4D - Pattern Management Endpoints
    path('patterns/<uuid:pattern_id>/approve-fix/', PatternApprovalView.as_view(), name='pattern-approve-fix'),
    path('patterns/bulk-action/', PatternBulkActionView.as_view(), name='pattern-bulk-action'),

    # Phase 4D - Transparency Endpoints
    path('benchmarks/user/', UserBenchmarkView.as_view(), name='benchmarks-user'),
    path('feedback/calculation/', CalculationFeedbackView.as_view(), name='feedback-calculation'),
    path('calculations/<uuid:extraction_result_id>/compare-benchmark/', CalculationComparisonView.as_view(), name='calculation-compare-benchmark'),

    # Phase 4D - Admin Dashboard Endpoints (Step 3)
    path('admin/dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('admin/dashboard/activity/', recent_activity, name='dashboard-activity'),
    path('admin/dashboard/health/', system_health, name='dashboard-health'),

    # REST API Routes (router includes all ViewSet routes)
    path('', include(router.urls)),
]
