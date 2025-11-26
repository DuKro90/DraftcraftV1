"""API views for document processing and extraction."""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import FileResponse
import logging

from documents.models import Document, ExtractionResult, AuditLog
from documents.serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    AuditLogSerializer,
)
from extraction.models import ExtractedEntity, MaterialExtraction, ExtractionConfig
from extraction.serializers import (
    ExtractedEntitySerializer,
    MaterialExtractionSerializer,
    ExtractionConfigSerializer,
    ExtractionSummarySerializer,
)
from extraction.services import GermanOCRService, GermanNERService
from extraction.services.base_service import ExtractionServiceError

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for document management."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DocumentUploadSerializer
        elif self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentListSerializer

    def get_queryset(self):
        """Return documents for current user."""
        return Document.objects.filter(user=self.request.user).select_related(
            'extraction_result'
        ).prefetch_related('extracted_entities', 'audit_logs')

    def perform_create(self, serializer):
        """Save document with user."""
        serializer.save(user=self.request.user)
        # Log upload
        AuditLog.objects.create(
            document=serializer.instance,
            user=self.request.user,
            action='uploaded',
            details={'filename': serializer.instance.original_filename}
        )

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process document with OCR/NER extraction.

        POST /api/v1/documents/{id}/process/
        """
        document = self.get_object()

        # Validate document status
        if document.status != 'uploaded':
            return Response(
                {'detail': f'Document status is {document.status}, not uploaded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update status
            document.status = 'processing'
            document.save()

            # Get extraction config (or use defaults)
            try:
                config = ExtractionConfig.objects.get(language='de')
                config_dict = {
                    'ocr_use_cuda': config.ocr_use_cuda,
                    'ocr_confidence_threshold': config.ocr_confidence_threshold,
                    'ner_model': config.ner_model,
                    'ner_confidence_threshold': config.ner_confidence_threshold,
                    'max_file_size_mb': config.max_file_size_mb,
                }
            except ExtractionConfig.DoesNotExist:
                config_dict = {'max_file_size_mb': 50}

            # OCR processing
            ocr_service = GermanOCRService(config_dict)
            ocr_result = ocr_service.process(document.file.path)

            # NER processing
            ner_service = GermanNERService(config_dict)
            ner_result = ner_service.process(ocr_result['text'], document)

            # Create/update ExtractionResult
            extraction_result, created = ExtractionResult.objects.get_or_create(
                document=document,
                defaults={
                    'ocr_text': ocr_result['text'],
                    'confidence_scores': {
                        'ocr': ocr_result['confidence'],
                        'ner': ner_result['confidence'],
                    },
                    'processing_time_ms': ocr_result['processing_time_ms'] + ner_result['processing_time_ms'],
                    'extracted_data': {
                        'entities': ner_result['summary'],
                        'entity_count': len(ner_result['entities']),
                    }
                }
            )

            if not created:
                extraction_result.ocr_text = ocr_result['text']
                extraction_result.confidence_scores = {
                    'ocr': ocr_result['confidence'],
                    'ner': ner_result['confidence'],
                }
                extraction_result.processing_time_ms = ocr_result['processing_time_ms'] + ner_result['processing_time_ms']
                extraction_result.extracted_data = {
                    'entities': ner_result['summary'],
                    'entity_count': len(ner_result['entities']),
                }
                extraction_result.save()

            # Create MaterialExtraction if needed
            if ner_result['entities']:
                material_data = self._extract_material_specs(ner_result['entities'])
                MaterialExtraction.objects.update_or_create(
                    document=document,
                    defaults={
                        'materials': material_data.get('materials', {}),
                        'complexity_level': material_data.get('complexity_level', ''),
                        'surface_finish': material_data.get('surface_finish', ''),
                        'extraction_confidence': ner_result['confidence'],
                        'requires_manual_review': ner_result['confidence'] < 0.8,
                    }
                )

            # Update document status
            document.status = 'completed'
            document.save()

            # Log processing
            AuditLog.objects.create(
                document=document,
                user=request.user,
                action='processed',
                details={
                    'ocr_confidence': ocr_result['confidence'],
                    'ner_confidence': ner_result['confidence'],
                    'entity_count': len(ner_result['entities']),
                }
            )

            serializer = DocumentDetailSerializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ExtractionServiceError as e:
            document.status = 'error'
            document.save()

            # Log error
            AuditLog.objects.create(
                document=document,
                user=request.user,
                action='processed',
                details={'error': str(e)}
            )

            return Response(
                {'detail': f'Extraction failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Unexpected error processing document {pk}")
            document.status = 'error'
            document.save()
            return Response(
                {'detail': 'Unexpected error during processing'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _extract_material_specs(self, entities):
        """Extract material specifications from entities."""
        material_data = {}
        materials = {}

        for entity in entities:
            if entity['type'] == 'MATERIAL':
                materials[entity['text'].lower()] = 1.0
            elif entity['type'] == 'QUANTITY':
                material_data['quantity'] = entity['text']

        material_data['materials'] = materials
        return material_data

    @action(detail=True, methods=['get'])
    def extraction_summary(self, request, pk=None):
        """Get extraction summary for document.

        GET /api/v1/documents/{id}/extraction_summary/
        """
        document = self.get_object()

        try:
            extraction = document.extraction_result
            entities = document.extracted_entities.all()
            material_extraction = document.material_extraction

            entity_types = {}
            for entity in entities:
                entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1

            summary_data = {
                'document_id': str(document.id),
                'original_filename': document.original_filename,
                'status': document.status,
                'ocr_confidence': extraction.confidence_scores.get('ocr', 0) if extraction else 0,
                'entity_count': entities.count(),
                'entity_types': entity_types,
                'materials_found': material_extraction.materials if material_extraction else {},
                'processing_time_ms': extraction.processing_time_ms if extraction else 0,
                'requires_review': material_extraction.requires_manual_review if material_extraction else False,
                'created_at': extraction.created_at if extraction else document.created_at,
            }

            serializer = ExtractionSummarySerializer(summary_data)
            return Response(serializer.data)

        except AttributeError:
            return Response(
                {'detail': 'No extraction results for this document'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def audit_logs(self, request, pk=None):
        """Get audit logs for document.

        GET /api/v1/documents/{id}/audit_logs/
        """
        document = self.get_object()
        logs = document.audit_logs.all()
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)


class ExtractedEntityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for extracted entities (read-only)."""

    serializer_class = ExtractedEntitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return entities from user's documents."""
        document_ids = Document.objects.filter(user=self.request.user).values_list('id', flat=True)
        return ExtractedEntity.objects.filter(document_id__in=document_ids)

    def get_queryset_filtered(self):
        """Filter by document_id and entity_type if provided."""
        queryset = self.get_queryset()

        document_id = self.request.query_params.get('document_id')
        if document_id:
            queryset = queryset.filter(document_id=document_id)

        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to apply filters."""
        self.queryset = self.get_queryset_filtered()
        return super().list(request, *args, **kwargs)


class MaterialExtractionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for material extractions (read-only)."""

    serializer_class = MaterialExtractionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return material extractions from user's documents."""
        document_ids = Document.objects.filter(user=self.request.user).values_list('id', flat=True)
        return MaterialExtraction.objects.filter(document_id__in=document_ids)


class ExtractionConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for extraction configuration (admin only)."""

    serializer_class = ExtractionConfigSerializer
    queryset = ExtractionConfig.objects.all()
    permission_classes = [permissions.IsAdminUser]


# Proposal endpoints
from proposals.models import Proposal, ProposalTemplate
from proposals.serializers import (
    ProposalDetailSerializer,
    ProposalListSerializer,
    ProposalTemplateSerializer,
    ProposalCreateSerializer,
    ProposalSendSerializer,
)
from proposals.services import ProposalService, ProposalEmailService
from proposals.pdf_service import ProposalPdfService


class ProposalViewSet(viewsets.ModelViewSet):
    """ViewSet for proposal management."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProposalCreateSerializer
        elif self.action == 'retrieve':
            return ProposalDetailSerializer
        elif self.action == 'send':
            return ProposalSendSerializer
        return ProposalListSerializer

    def get_queryset(self):
        """Return proposals for user's documents."""
        document_ids = Document.objects.filter(user=self.request.user).values_list('id', flat=True)
        return Proposal.objects.filter(document_id__in=document_ids).select_related('template')

    def create(self, request, *args, **kwargs):
        """Create proposal from document.

        POST /api/v1/proposals/
        {
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "template_id": 1,
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "valid_days": 30
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            document = Document.objects.get(id=serializer.validated_data['document_id'])

            # Get template
            template_id = serializer.validated_data.get('template_id')
            template = None
            if template_id:
                try:
                    template = ProposalTemplate.objects.get(id=template_id)
                except ProposalTemplate.DoesNotExist:
                    pass

            # Generate proposal
            service = ProposalService(template)
            proposal = service.generate_proposal(
                document=document,
                valid_days=serializer.validated_data.get('valid_days', 30)
            )

            # Update customer info
            proposal.customer_name = serializer.validated_data.get('customer_name', '')
            proposal.customer_email = serializer.validated_data.get('customer_email', '')
            proposal.save()

            output_serializer = ProposalDetailSerializer(proposal)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Document.DoesNotExist:
            return Response(
                {'detail': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error creating proposal")
            return Response(
                {'detail': f'Proposal generation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send proposal via email.

        POST /api/v1/proposals/{id}/send/
        {
            "recipient_email": "customer@example.com",
            "message": "Here is your proposal..."
        }
        """
        proposal = self.get_object()
        serializer = ProposalSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('recipient_email') or proposal.customer_email

        if not email:
            return Response(
                {'detail': 'No email address provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = ProposalEmailService.send_proposal(proposal, email)

        if success:
            return Response(
                {'detail': 'Proposal sent successfully'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': 'Failed to send proposal'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download proposal as PDF.

        GET /api/v1/proposals/{id}/download_pdf/

        Returns:
            PDF file as attachment
        """
        proposal = self.get_object()

        try:
            # Generate PDF
            pdf_content = ProposalPdfService.generate_pdf(proposal)
            filename = ProposalPdfService.get_filename(proposal)

            # Return as file download
            response = FileResponse(
                iter(pdf_content),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            logger.exception(f"Error generating PDF for proposal {pk}")
            return Response(
                {'detail': f'PDF generation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class HealthCheckViewSet(viewsets.ViewSet):
    """Health check endpoints for system components."""

    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='ocr')
    def health_ocr(self, request):
        """Check OCR service health.

        Returns:
            - status: 'healthy' if OCR service is available, 'degraded' if optional
            - ocr_available: boolean
            - ner_available: boolean
            - error_message: error details if not healthy
        """
        try:
            # Try to initialize OCR service
            ocr_config = {'ocr_use_cuda': False}
            ocr_service = GermanOCRService(ocr_config)
            ocr_available = ocr_service.ocr is not None

            # Try to initialize NER service
            ner_config = {'ner_model': 'de_core_news_lg'}
            ner_service = GermanNERService(ner_config)
            ner_available = ner_service.nlp is not None

            # System is healthy if at least OCR is available
            if ocr_available or ner_available:
                return Response({
                    'status': 'healthy',
                    'ocr_available': ocr_available,
                    'ner_available': ner_available,
                    'message': 'OCR/NER services operational'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'degraded',
                    'ocr_available': ocr_available,
                    'ner_available': ner_available,
                    'message': 'Install ML dependencies: pip install -r ml.txt'
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error checking OCR health")
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Error initializing OCR services'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProposalTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for proposal templates (admin only)."""

    serializer_class = ProposalTemplateSerializer
    queryset = ProposalTemplate.objects.all()
    permission_classes = [permissions.IsAdminUser]
