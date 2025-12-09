"""
Configuration API Views - Phase 4D

API endpoints for managing configuration (TIER 1 global factors, TIER 2 company metrics).
Implements Redis caching for TIER 1 config (rarely changes).
"""
import logging
from django.core.cache import cache
from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from api.v1.serializers.config_serializers import (
    HolzartConfigSerializer,
    OberflächenConfigSerializer,
    KomplexitaetConfigSerializer,
    BetriebskennzahlConfigSerializer,
    BetriebskennzahlUpdateSerializer,
)
from api.v1.permissions import IsAdminOrReadOnly, CanModifyConfiguration
from documents.betriebskennzahl_models import (
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
    BetriebskennzahlTemplate,
)

logger = logging.getLogger(__name__)


class HolzartConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Holzart (wood type) configuration - Read-only.

    GET /api/v1/config/holzarten/
    GET /api/v1/config/holzarten/{id}/

    Returns TIER 1 global wood type factors.
    Admins can modify in Django Admin.
    """

    serializer_class = HolzartConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get active Holzarten for user's template with Redis caching."""
        user = self.request.user
        template_id = None

        # Try to get user's template
        try:
            user_config = IndividuelleBetriebskennzahl.objects.select_related(
                'handwerk_template', 'user'
            ).get(user=user)
            if user_config.handwerk_template:
                template_id = user_config.handwerk_template_id
        except IndividuelleBetriebskennzahl.DoesNotExist:
            # Fallback to default template
            try:
                default_template = BetriebskennzahlTemplate.objects.filter(
                    is_active=True
                ).order_by('-version').first()
                if default_template:
                    template_id = default_template.id
            except Exception as e:
                logger.warning(f"Error getting default template: {e}")

        if not template_id:
            return HolzartKennzahl.objects.none()

        # Check cache first
        cache_key = f'holzarten_template_{template_id}'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.info(f"Cache HIT for {cache_key}")
            return cached_data

        # Cache miss - fetch from database
        logger.info(f"Cache MISS for {cache_key} - fetching from DB")
        queryset = HolzartKennzahl.objects.select_related(
            'template'
        ).filter(
            template_id=template_id,
            is_enabled=True
        ).order_by('kategorie', 'holzart')

        # Convert to list for caching (QuerySets aren't picklable)
        queryset_list = list(queryset)

        # Cache for 1 hour (TIER 1 config changes rarely)
        cache.set(cache_key, queryset_list, timeout=3600)
        logger.info(f"Cached {len(queryset_list)} Holzarten for template {template_id}")

        return queryset_list

    @extend_schema(
        summary="List wood types",
        description="Get all active wood type configuration factors (TIER 1)",
        tags=['Configuration'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get wood type details",
        description="Get specific wood type configuration",
        tags=['Configuration'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class OberflächenConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Oberflächenbearbeitung (surface finish) configuration - Read-only.

    GET /api/v1/config/oberflaechen/
    GET /api/v1/config/oberflaechen/{id}/

    Returns TIER 1 global surface finish factors.
    """

    serializer_class = OberflächenConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get active Oberflächenbearbeitung for user's template with Redis caching."""
        user = self.request.user
        template_id = None

        try:
            user_config = IndividuelleBetriebskennzahl.objects.select_related(
                'handwerk_template', 'user'
            ).get(user=user)
            if user_config.handwerk_template:
                template_id = user_config.handwerk_template_id
        except IndividuelleBetriebskennzahl.DoesNotExist:
            # Fallback to default template
            try:
                default_template = BetriebskennzahlTemplate.objects.filter(
                    is_active=True
                ).order_by('-version').first()
                if default_template:
                    template_id = default_template.id
            except Exception:
                pass

        if not template_id:
            return OberflächenbearbeitungKennzahl.objects.none()

        # Check cache first
        cache_key = f'oberflaechen_template_{template_id}'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.info(f"Cache HIT for {cache_key}")
            return cached_data

        # Cache miss - fetch from database
        logger.info(f"Cache MISS for {cache_key} - fetching from DB")
        queryset = OberflächenbearbeitungKennzahl.objects.select_related(
            'template'
        ).filter(
            template_id=template_id,
            is_enabled=True
        ).order_by('kategorie', 'bearbeitung')

        queryset_list = list(queryset)
        cache.set(cache_key, queryset_list, timeout=3600)
        logger.info(f"Cached {len(queryset_list)} Oberflächenbearbeitungen for template {template_id}")

        return queryset_list

    @extend_schema(
        summary="List surface finishes",
        description="Get all active surface finish configuration factors (TIER 1)",
        tags=['Configuration'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get surface finish details",
        description="Get specific surface finish configuration",
        tags=['Configuration'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class KomplexitaetConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Komplexität (complexity/technique) configuration - Read-only.

    GET /api/v1/config/komplexitaet/
    GET /api/v1/config/komplexitaet/{id}/

    Returns TIER 1 global complexity technique factors.
    """

    serializer_class = KomplexitaetConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get active Komplexität for user's template with Redis caching."""
        user = self.request.user
        template_id = None

        try:
            user_config = IndividuelleBetriebskennzahl.objects.select_related(
                'handwerk_template', 'user'
            ).get(user=user)
            if user_config.handwerk_template:
                template_id = user_config.handwerk_template_id
        except IndividuelleBetriebskennzahl.DoesNotExist:
            # Fallback to default template
            try:
                default_template = BetriebskennzahlTemplate.objects.filter(
                    is_active=True
                ).order_by('-version').first()
                if default_template:
                    template_id = default_template.id
            except Exception:
                pass

        if not template_id:
            return KomplexitaetKennzahl.objects.none()

        # Check cache first
        cache_key = f'komplexitaet_template_{template_id}'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.info(f"Cache HIT for {cache_key}")
            return cached_data

        # Cache miss - fetch from database
        logger.info(f"Cache MISS for {cache_key} - fetching from DB")
        queryset = KomplexitaetKennzahl.objects.select_related(
            'template'
        ).filter(
            template_id=template_id,
            is_enabled=True
        ).order_by('schwierigkeitsgrad', 'technik')

        queryset_list = list(queryset)
        cache.set(cache_key, queryset_list, timeout=3600)
        logger.info(f"Cached {len(queryset_list)} Komplexitäten for template {template_id}")

        return queryset_list

    @extend_schema(
        summary="List complexity techniques",
        description="Get all active complexity technique configuration factors (TIER 1)",
        tags=['Configuration'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get complexity technique details",
        description="Get specific complexity technique configuration",
        tags=['Configuration'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class BetriebskennzahlConfigViewSet(viewsets.ViewSet):
    """
    Betriebskennzahl (company metrics) configuration - User-specific.

    GET /api/v1/config/betriebskennzahlen/
    PATCH /api/v1/config/betriebskennzahlen/

    Returns and updates TIER 2 company-specific metrics.
    Each user can modify their own configuration.
    """

    permission_classes = [IsAuthenticated, CanModifyConfiguration]

    @extend_schema(
        responses={200: BetriebskennzahlConfigSerializer},
        summary="Get company metrics",
        description="Get user's Betriebskennzahl configuration (TIER 2)",
        tags=['Configuration'],
    )
    def list(self, request):
        """Get user's Betriebskennzahl configuration."""
        try:
            config = IndividuelleBetriebskennzahl.objects.get(user=request.user)
            serializer = BetriebskennzahlConfigSerializer(config)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except IndividuelleBetriebskennzahl.DoesNotExist:
            return Response(
                {
                    'detail': 'Sie haben noch keine Betriebskennzahl-Konfiguration. '
                              'Bitte wenden Sie sich an den Administrator.',
                    'error_code': 'no_configuration'
                },
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=BetriebskennzahlUpdateSerializer,
        responses={200: BetriebskennzahlConfigSerializer},
        summary="Update company metrics",
        description="Update user's Betriebskennzahl configuration (partial update)",
        tags=['Configuration'],
    )
    @action(detail=False, methods=['patch'])
    def update_config(self, request):
        """Update user's Betriebskennzahl configuration (partial)."""
        try:
            config = IndividuelleBetriebskennzahl.objects.get(user=request.user)

            # Validate update data
            update_serializer = BetriebskennzahlUpdateSerializer(data=request.data)
            update_serializer.is_valid(raise_exception=True)

            # Apply updates
            for field, value in update_serializer.validated_data.items():
                setattr(config, field, value)

            config.save()

            # Log update
            logger.info(
                f"Betriebskennzahl updated for user {request.user.id}: "
                f"fields={list(update_serializer.validated_data.keys())}"
            )

            # Return updated config
            response_serializer = BetriebskennzahlConfigSerializer(config)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except IndividuelleBetriebskennzahl.DoesNotExist:
            return Response(
                {
                    'detail': 'Keine Betriebskennzahl-Konfiguration gefunden.',
                    'error_code': 'no_configuration'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.exception(f"Error updating Betriebskennzahl for user {request.user.id}")
            return Response(
                {
                    'detail': f'Fehler beim Aktualisieren der Konfiguration: {str(e)}',
                    'error_code': 'update_error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Get pricing report",
        description="Get summary of current pricing configuration and enabled tiers",
        tags=['Configuration'],
    )
    @action(detail=False, methods=['get'])
    def pricing_report(self, request):
        """Get pricing configuration report."""
        try:
            from extraction.services.calculation_engine import CalculationEngine

            engine = CalculationEngine(user=request.user)
            report = engine.get_pricing_report()

            return Response(report, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error generating pricing report for user {request.user.id}")
            return Response(
                {
                    'detail': f'Fehler beim Generieren des Berichts: {str(e)}',
                    'error_code': 'report_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
