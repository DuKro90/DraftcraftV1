"""API v1 URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet,
    ExtractedEntityViewSet,
    MaterialExtractionViewSet,
    ExtractionConfigViewSet,
    ProposalViewSet,
    ProposalTemplateViewSet,
    HealthCheckViewSet,
)

app_name = 'v1'

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'entities', ExtractedEntityViewSet, basename='entity')
router.register(r'materials', MaterialExtractionViewSet, basename='material')
router.register(r'extraction-config', ExtractionConfigViewSet, basename='extraction-config')
router.register(r'proposals', ProposalViewSet, basename='proposal')
router.register(r'proposal-templates', ProposalTemplateViewSet, basename='proposal-template')
router.register(r'health', HealthCheckViewSet, basename='health')

urlpatterns = [
    path('', include(router.urls)),
]
