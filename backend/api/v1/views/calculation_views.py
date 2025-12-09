"""
Calculation API Views - Phase 4D

API endpoints for pricing calculations using CalculationEngine and Pauschalen.
"""
import logging
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from api.v1.serializers.calculation_serializers import (
    PriceCalculationRequestSerializer,
    PriceCalculationResponseSerializer,
    MultiMaterialCalculationSerializer,
    ApplicablePauschaleSerializer,
    ApplicablePauschaleRequestSerializer,
)
from api.v1.permissions import HasActiveBetriebskennzahl
from extraction.services.calculation_engine import CalculationEngine, CalculationError
from extraction.services.multi_material_calculation_service import calculate_multi_material_cost
from documents.services.pauschale_calculation_service import PauschaleCalculationService
from documents.models_pauschalen import BetriebspauschaleRegel
from documents.models import ExtractionResult
from documents.transparency_models import CalculationExplanation, CalculationFactor
from decimal import Decimal

logger = logging.getLogger(__name__)


def create_calculation_explanation(extraction_result, calculation_result, user):
    """
    Create CalculationExplanation and CalculationFactors from calculation result.

    Args:
        extraction_result: ExtractionResult object (can be None)
        calculation_result: Dict from CalculationEngine.calculate_project_price()
        user: User object for benchmarking

    Returns:
        CalculationExplanation object or None if extraction_result is missing
    """
    if not extraction_result:
        logger.warning("Cannot create CalculationExplanation without ExtractionResult")
        return None

    # Determine confidence level based on calculation warnings
    warnings_count = len(calculation_result.get('warnings', []))
    if warnings_count == 0:
        confidence_level = 'high'
        confidence_score = Decimal('0.95')
    elif warnings_count <= 2:
        confidence_level = 'medium'
        confidence_score = Decimal('0.80')
    else:
        confidence_level = 'low'
        confidence_score = Decimal('0.60')

    # Create CalculationExplanation
    explanation = CalculationExplanation.objects.create(
        extraction_result=extraction_result,
        confidence_level=confidence_level,
        confidence_score=confidence_score,
        total_price_eur=calculation_result['total_price_eur'],
        similar_projects_count=0,  # TODO: Calculate from user's project history
        user_average_for_type=None,  # TODO: Get from UserProjectBenchmark
        deviation_from_average_percent=None,  # TODO: Calculate deviation
    )

    # Create CalculationFactors from breakdown
    breakdown = calculation_result.get('breakdown', {})
    factor_order = 0

    # Extract factors from each step
    factor_mappings = [
        ('step_2_wood_type', 'material', 'tier1_global'),
        ('step_3_surface_finish', 'material', 'tier1_global'),
        ('step_4_complexity', 'labor', 'tier1_global'),
        ('step_5_labor', 'labor', 'tier2_company'),
        ('step_6_overhead_and_margin', 'overhead', 'tier2_company'),
        ('step_7_seasonal_adjustments', 'adjustment', 'tier3_dynamic'),
        ('step_8_customer_discounts', 'adjustment', 'tier3_dynamic'),
    ]

    for step_key, category, data_source in factor_mappings:
        step_data = breakdown.get(step_key, {})
        if not step_data or not step_data.get('applied', False):
            continue

        # Calculate impact percentage
        price_before = Decimal(str(step_data.get('price_before_eur', 0)))
        price_after = Decimal(str(step_data.get('price_after_eur', 0)))

        if price_before > 0:
            impact_percent = ((price_after - price_before) / price_before) * 100
        else:
            impact_percent = Decimal('0.00')

        amount_eur = price_after - price_before

        # Create factor
        CalculationFactor.objects.create(
            explanation=explanation,
            factor_name=step_data.get('step_name', step_key),
            factor_category=category,
            amount_eur=abs(amount_eur),
            impact_percent=abs(impact_percent),
            explanation_text=str(step_data.get('details', {})),
            data_source=data_source,
            is_adjustable=True,
            display_order=factor_order,
        )
        factor_order += 1

    logger.info(f"Created CalculationExplanation {explanation.id} with {factor_order} factors")
    return explanation


class PriceCalculationView(views.APIView):
    """
    Calculate project price using CalculationEngine (8-step workflow).

    POST /api/v1/calculate/price/
    {
        "extracted_data": {
            "holzart": "eiche",
            "oberflaeche": "lackieren",
            "komplexitaet": "hand_geschnitzt",
            "material_sku": "EICHE-25MM",
            "material_quantity": 10,
            "labor_hours": 40,
            "distanz_km": 25
        },
        "customer_type": "bestehende_kunden",
        "breakdown": true,
        "extraction_result_id": "uuid-optional"
    }

    Returns complete pricing with TIER 1/2/3 factors and Pauschalen.
    """

    permission_classes = [IsAuthenticated, HasActiveBetriebskennzahl]

    @extend_schema(
        request=PriceCalculationRequestSerializer,
        responses={200: PriceCalculationResponseSerializer},
        summary="Calculate project price",
        description="Calculate complete project price using 8-step workflow with TIER 1/2/3 factors and Pauschalen",
        tags=['Pricing'],
    )
    def post(self, request):
        """Calculate project price."""
        serializer = PriceCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Initialize calculation engine for user
            engine = CalculationEngine(user=request.user)

            # Get extraction_result if provided
            extraction_result = None
            extraction_result_id = serializer.validated_data.get('extraction_result_id')
            if extraction_result_id:
                try:
                    extraction_result = ExtractionResult.objects.get(
                        id=extraction_result_id,
                        document__user=request.user  # Ensure ownership
                    )
                except ExtractionResult.DoesNotExist:
                    return Response(
                        {
                            'detail': f'ExtractionResult nicht gefunden: {extraction_result_id}',
                            'error_code': 'extraction_result_not_found'
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Calculate price
            result = engine.calculate_project_price(
                extracted_data=serializer.validated_data['extracted_data'],
                quantity=serializer.validated_data.get('quantity'),
                customer_type=serializer.validated_data.get('customer_type', 'neue_kunden'),
                breakdown=serializer.validated_data.get('breakdown', True),
                extraction_result=extraction_result,
            )

            # Create CalculationExplanation for transparency (Phase 4A integration)
            explanation = create_calculation_explanation(
                extraction_result=extraction_result,
                calculation_result=result,
                user=request.user
            )

            # Add transparency IDs to result
            result['calculation_id'] = str(explanation.id) if explanation else None
            result['extraction_result_id'] = str(extraction_result.id) if extraction_result else None

            # Log calculation
            logger.info(
                f"Price calculated for user {request.user.id}: "
                f"{result['total_price_eur']} EUR "
                f"(Pauschalen: {result['pauschalen']['total']} EUR, "
                f"Explanation: {result['calculation_id']})"
            )

            # Return result
            response_serializer = PriceCalculationResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.validated_data, status=status.HTTP_200_OK)

        except CalculationError as e:
            logger.warning(f"Calculation error for user {request.user.id}: {e}")
            return Response(
                {
                    'detail': str(e),
                    'error_code': 'calculation_error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception(f"Unexpected error in price calculation for user {request.user.id}")
            return Response(
                {
                    'detail': 'Ein unerwarteter Fehler ist aufgetreten bei der Preisberechnung.',
                    'error_code': 'internal_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MultiMaterialCalculationView(views.APIView):
    """
    Calculate price for multi-material projects (Phase 4C).

    POST /api/v1/calculate/multi-material/
    {
        "materials": [
            {
                "holzart": "eiche",
                "oberflaeche": "lackieren",
                "laenge_mm": 2000,
                "breite_mm": 800,
                "hoehe_mm": 25,
                "menge": 4
            },
            {
                "holzart": "buche",
                "oberflaeche": "oelen",
                "laenge_mm": 1500,
                "breite_mm": 600,
                "hoehe_mm": 18,
                "menge": 8
            }
        ],
        "customer_type": "bestehende_kunden",
        "breakdown": true
    }

    Returns pricing for each material component and total.
    """

    permission_classes = [IsAuthenticated, HasActiveBetriebskennzahl]

    @extend_schema(
        request=MultiMaterialCalculationSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Calculate multi-material price",
        description="Calculate price for projects with multiple materials/components",
        tags=['Pricing'],
    )
    def post(self, request):
        """Calculate multi-material price."""
        serializer = MultiMaterialCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Prepare extracted_data with materials list
            extracted_data = {
                'materials': serializer.validated_data['materials']
            }

            # Calculate using multi-material service
            result = calculate_multi_material_cost(
                user=request.user,
                extracted_data=extracted_data
            )

            # Log calculation
            logger.info(
                f"Multi-material price calculated for user {request.user.id}: "
                f"{result['total_material_cost']} EUR for {len(serializer.validated_data['materials'])} materials"
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error in multi-material calculation for user {request.user.id}")
            return Response(
                {
                    'detail': f'Multi-Material-Berechnung fehlgeschlagen: {str(e)}',
                    'error_code': 'multi_material_error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ApplicablePauschaleView(views.APIView):
    """
    Get applicable Pauschalen for given context.

    GET /api/v1/pauschalen/applicable/?auftragswert=5000&distanz_km=30&montage_stunden=8

    Returns list of all Pauschalen with their applicability and calculated amounts.
    """

    permission_classes = [IsAuthenticated, HasActiveBetriebskennzahl]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='auftragswert',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Project value in EUR',
                required=False,
            ),
            OpenApiParameter(
                name='distanz_km',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Distance in km',
                required=False,
            ),
            OpenApiParameter(
                name='montage_stunden',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Installation hours',
                required=False,
            ),
            OpenApiParameter(
                name='material_menge',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Material quantity (m³, etc.)',
                required=False,
            ),
        ],
        responses={200: ApplicablePauschaleSerializer(many=True)},
        summary="Get applicable Pauschalen",
        description="Returns all Pauschalen with applicability for given context",
        tags=['Pricing'],
    )
    def get(self, request):
        """Get applicable Pauschalen."""
        # Validate query params
        params_serializer = ApplicablePauschaleRequestSerializer(data=request.query_params)
        params_serializer.is_valid(raise_exception=True)

        try:
            # Build context
            context = {}
            if params_serializer.validated_data.get('auftragswert'):
                context['auftragswert'] = float(params_serializer.validated_data['auftragswert'])
            if params_serializer.validated_data.get('distanz_km'):
                context['distanz_km'] = float(params_serializer.validated_data['distanz_km'])
            if params_serializer.validated_data.get('montage_stunden'):
                context['montage_stunden'] = float(params_serializer.validated_data['montage_stunden'])
            if params_serializer.validated_data.get('material_menge'):
                context['material_menge'] = float(params_serializer.validated_data['material_menge'])

            # Get all active Pauschalen for user
            pauschalen = BetriebspauschaleRegel.objects.filter(
                user=request.user,
                is_active=True
            )

            # Check applicability for each
            results = []
            for pauschale in pauschalen:
                applies = self._check_applicability(pauschale, context)
                calculated_amount = None
                reason = None

                if applies:
                    calculated_amount, reason = self._calculate_amount(pauschale, context)

                results.append({
                    'regel_id': pauschale.id,
                    'name': pauschale.name,
                    'pauschale_typ': pauschale.pauschale_typ,
                    'berechnungsart': pauschale.berechnungsart,
                    'betrag_eur': pauschale.betrag,
                    'beschreibung': pauschale.beschreibung,
                    'applies': applies,
                    'calculated_amount_eur': calculated_amount,
                    'reason': reason or ('Applies' if applies else 'Does not apply'),
                })

            # Serialize results
            serializer = ApplicablePauschaleSerializer(data=results, many=True)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error getting applicable Pauschalen for user {request.user.id}")
            return Response(
                {
                    'detail': f'Fehler beim Abrufen der Pauschalen: {str(e)}',
                    'error_code': 'pauschalen_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _check_applicability(self, pauschale, context):
        """Check if Pauschale applies to given context."""
        # Always applicable for 'fest', 'prozent', 'pro_einheit'
        if pauschale.berechnungsart in ['fest', 'prozent', 'pro_einheit']:
            return True

        # For konditional, evaluate DSL regel
        if pauschale.berechnungsart == 'konditional' and pauschale.dsl_regel:
            try:
                from documents.services.bauteil_regel_engine import BauteilRegelEngine
                engine = BauteilRegelEngine()
                return engine.evaluate(pauschale.dsl_regel, context)
            except Exception as e:
                logger.warning(f"Error evaluating DSL for Pauschale {pauschale.id}: {e}")
                return False

        return False

    def _calculate_amount(self, pauschale, context):
        """Calculate Pauschale amount for given context."""
        try:
            if pauschale.berechnungsart == 'fest':
                return float(pauschale.betrag), 'Fester Betrag'

            elif pauschale.berechnungsart == 'prozent':
                auftragswert = context.get('auftragswert', 0)
                amount = Decimal(str(auftragswert)) * (pauschale.betrag / Decimal('100'))
                return float(amount), f'{pauschale.betrag}% vom Auftragswert'

            elif pauschale.berechnungsart == 'pro_einheit':
                # Get quantity from context based on pauschale type
                quantity = 0
                if pauschale.pauschale_typ == 'anfahrt':
                    quantity = context.get('distanz_km', 0)
                elif pauschale.pauschale_typ == 'montage':
                    quantity = context.get('montage_stunden', 0)
                elif pauschale.pauschale_typ == 'entsorgung':
                    quantity = context.get('material_menge', 0)

                amount = pauschale.betrag * Decimal(str(quantity))
                return float(amount), f'{pauschale.betrag} EUR × {quantity} {pauschale.einheit}'

            elif pauschale.berechnungsart == 'konditional':
                # For conditional, use DSL to calculate
                from documents.services.bauteil_regel_engine import BauteilRegelEngine
                engine = BauteilRegelEngine()
                result = engine.evaluate(pauschale.dsl_regel, context)

                if isinstance(result, (int, float)):
                    return float(result), 'Berechnet via DSL-Regel'
                else:
                    return float(pauschale.betrag), 'Standard-Betrag (DSL gab boolean zurück)'

        except Exception as e:
            logger.warning(f"Error calculating Pauschale amount for {pauschale.id}: {e}")
            return float(pauschale.betrag), f'Fehler bei Berechnung: {str(e)}'

        return 0.0, 'Keine Berechnung möglich'
