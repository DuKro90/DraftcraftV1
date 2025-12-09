"""
Transparency & Explanation API Views - Phase 4D

API endpoints for AI transparency (Phase 4A models).
Provides calculation explanations, benchmarks, and feedback mechanisms.
"""
import logging
from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from api.v1.serializers.transparency_serializers import (
    CalculationExplanationSerializer,
    UserBenchmarkSerializer,
    CalculationFeedbackSerializer,
    CalculationComparisonSerializer,
    ExplanationRegenerateSerializer,
)
from api.v1.permissions import IsOwner
from documents.transparency_models import (
    CalculationExplanation,
    UserProjectBenchmark,
)
from documents.models import ExtractionResult
from decimal import Decimal

logger = logging.getLogger(__name__)


class CalculationExplanationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Calculation explanation management.

    GET /api/v1/calculations/{id}/explanation/

    Returns AI-generated explanations for pricing calculations.
    """

    serializer_class = CalculationExplanationSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Get explanations for user's calculations."""
        return CalculationExplanation.objects.filter(
            extraction_result__document__user=self.request.user
        ).select_related('extraction_result__document').prefetch_related('faktoren')

    @extend_schema(
        summary="Get calculation explanation",
        description="Get AI-generated explanation for a specific calculation",
        tags=['Transparency'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="List calculation explanations",
        description="Get all calculation explanations for user's projects",
        tags=['Transparency'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class UserBenchmarkView(views.APIView):
    """
    User project benchmarks.

    GET /api/v1/benchmarks/user/

    Returns user's historical project data for price comparison.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserBenchmarkSerializer(many=True)},
        summary="Get user benchmarks",
        description="Get user's historical project benchmarks for price comparison",
        tags=['Transparency'],
    )
    def get(self, request):
        """Get user's benchmarks."""
        try:
            benchmarks = UserProjectBenchmark.objects.filter(
                user=request.user
            ).order_by('-letztes_projekt_datum')

            serializer = UserBenchmarkSerializer(benchmarks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error retrieving benchmarks for user {request.user.id}")
            return Response(
                {
                    'detail': f'Fehler beim Abrufen der Benchmarks: {str(e)}',
                    'error_code': 'benchmark_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CalculationFeedbackView(views.APIView):
    """
    Submit feedback on calculation.

    POST /api/v1/feedback/calculation/
    {
        "extraction_result_id": "uuid",
        "calculation_id": "uuid",
        "feedback_type": "zu_hoch",
        "erwarteter_preis_eur": 3500.00,
        "kommentare": "Preis scheint 20% zu hoch für diese Komplexität"
    }

    Stores user feedback for machine learning improvement.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CalculationFeedbackSerializer,
        responses={201: OpenApiTypes.OBJECT},
        summary="Submit calculation feedback",
        description="Submit feedback on calculation accuracy for ML improvement",
        tags=['Transparency'],
    )
    def post(self, request):
        """Submit calculation feedback."""
        serializer = CalculationFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Verify user owns the ExtractionResult
            extraction_result_id = serializer.validated_data['extraction_result_id']
            try:
                extraction_result = ExtractionResult.objects.get(
                    id=extraction_result_id,
                    document__user=request.user
                )
            except ExtractionResult.DoesNotExist:
                return Response(
                    {
                        'detail': f'ExtractionResult nicht gefunden oder keine Berechtigung: {extraction_result_id}',
                        'error_code': 'not_found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Store feedback in ExtractionResult metadata
            if not extraction_result.metadata:
                extraction_result.metadata = {}

            if 'feedback' not in extraction_result.metadata:
                extraction_result.metadata['feedback'] = []

            extraction_result.metadata['feedback'].append({
                'user_id': request.user.id,
                'feedback_type': serializer.validated_data['feedback_type'],
                'erwarteter_preis_eur': float(serializer.validated_data.get('erwarteter_preis_eur', 0)),
                'kommentare': serializer.validated_data.get('kommentare', ''),
                'faktoren_bewertung': serializer.validated_data.get('faktoren_bewertung', {}),
                'timestamp': timezone.now().isoformat(),
            })

            extraction_result.save()

            # Log feedback
            logger.info(
                f"Calculation feedback received from user {request.user.id}: "
                f"type={serializer.validated_data['feedback_type']}, "
                f"extraction_result={extraction_result_id}"
            )

            # TODO Phase 5: Integrate with ML pipeline for pattern learning

            return Response(
                {
                    'success': True,
                    'message': 'Feedback erfolgreich gespeichert. Vielen Dank!',
                    'extraction_result_id': str(extraction_result_id),
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.exception(f"Error storing calculation feedback for user {request.user.id}")
            return Response(
                {
                    'detail': f'Fehler beim Speichern des Feedbacks: {str(e)}',
                    'error_code': 'feedback_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CalculationComparisonView(views.APIView):
    """
    Compare calculation with benchmark.

    GET /api/v1/calculations/{extraction_result_id}/compare-benchmark/

    Returns comparison between current price and user's historical averages.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: CalculationComparisonSerializer},
        summary="Compare with benchmark",
        description="Compare calculation with user's historical project benchmarks",
        tags=['Transparency'],
    )
    def get(self, request, extraction_result_id):
        """Compare calculation with benchmark."""
        try:
            # Get ExtractionResult
            try:
                extraction_result = ExtractionResult.objects.get(
                    id=extraction_result_id,
                    document__user=request.user
                )
            except ExtractionResult.DoesNotExist:
                return Response(
                    {
                        'detail': f'ExtractionResult nicht gefunden: {extraction_result_id}',
                        'error_code': 'not_found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get current price from extraction result
            current_price = Decimal(str(extraction_result.extracted_data.get('calculated_price', 0)))

            if current_price <= 0:
                return Response(
                    {
                        'detail': 'Keine Preisberechnung für dieses Ergebnis gefunden.',
                        'error_code': 'no_calculation'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get project type from extracted data
            projekttyp = extraction_result.extracted_data.get('projekttyp', 'standard')

            # Get benchmark
            try:
                benchmark = UserProjectBenchmark.objects.get(
                    user=request.user,
                    projekttyp=projekttyp
                )
            except UserProjectBenchmark.DoesNotExist:
                return Response(
                    {
                        'detail': f'Kein Benchmark gefunden für Projekttyp: {projekttyp}',
                        'error_code': 'no_benchmark'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Calculate comparison
            benchmark_avg = benchmark.durchschnittspreis_eur
            difference_eur = current_price - benchmark_avg
            difference_percent = float((difference_eur / benchmark_avg) * 100) if benchmark_avg > 0 else 0
            is_above_average = current_price > benchmark_avg

            # Generate explanation
            if is_above_average:
                explanation = (
                    f"Ihr Preis liegt {abs(difference_percent):.1f}% über dem Durchschnitt "
                    f"Ihrer {benchmark.anzahl_projekte} ähnlichen Projekte. "
                    f"Dies könnte auf höhere Komplexität, bessere Materialqualität, "
                    f"oder saisonale Faktoren zurückzuführen sein."
                )
            else:
                explanation = (
                    f"Ihr Preis liegt {abs(difference_percent):.1f}% unter dem Durchschnitt "
                    f"Ihrer {benchmark.anzahl_projekte} ähnlichen Projekte. "
                    f"Dies könnte auf Mengenrabatte, einfachere Ausführung, "
                    f"oder Kundentreue-Rabatte zurückzuführen sein."
                )

            # Identify factors causing difference
            factors_causing_difference = []
            extracted_data = extraction_result.extracted_data

            if extracted_data.get('holzart') == 'eiche':
                factors_causing_difference.append({
                    'factor': 'Holzart',
                    'value': 'Eiche (Premium)',
                    'impact': 'Erhöht Preis um ~30%'
                })

            if extracted_data.get('komplexitaet') == 'hand_geschnitzt':
                factors_causing_difference.append({
                    'factor': 'Komplexität',
                    'value': 'Handgeschnitzt',
                    'impact': 'Erhöht Preis um ~100%'
                })

            # Build response
            comparison = {
                'current_price_eur': float(current_price),
                'benchmark_avg_eur': float(benchmark_avg),
                'difference_eur': float(difference_eur),
                'difference_percent': difference_percent,
                'is_above_average': is_above_average,
                'explanation': explanation,
                'factors_causing_difference': factors_causing_difference,
                'sample_size': benchmark.anzahl_projekte,
            }

            serializer = CalculationComparisonSerializer(data=comparison)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error comparing calculation with benchmark for user {request.user.id}")
            return Response(
                {
                    'detail': f'Fehler beim Vergleichen: {str(e)}',
                    'error_code': 'comparison_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
