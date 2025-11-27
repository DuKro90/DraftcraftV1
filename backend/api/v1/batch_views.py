"""API views for batch document processing."""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging

from documents.models import Batch, BatchDocument
from documents.serializers import (
    BatchListSerializer,
    BatchDetailSerializer,
    BatchCreateSerializer,
    BatchDocumentSerializer,
)
from extraction.services.batch_processor import BatchProcessor, BatchProcessorError

logger = logging.getLogger(__name__)


class BatchViewSet(viewsets.ModelViewSet):
    """ViewSet for batch document processing.

    Endpoints:
    - GET /api/v1/batches/ - List user's batches
    - POST /api/v1/batches/ - Create new batch
    - GET /api/v1/batches/{id}/ - Get batch details
    - POST /api/v1/batches/{id}/add-documents/ - Add documents to batch
    - POST /api/v1/batches/{id}/start-processing/ - Start async processing
    - GET /api/v1/batches/{id}/status/ - Get batch progress
    - GET /api/v1/batches/{id}/errors/ - Get batch errors
    - POST /api/v1/batches/{id}/cancel/ - Cancel batch
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return BatchCreateSerializer
        elif self.action == 'retrieve':
            return BatchDetailSerializer
        return BatchListSerializer

    def get_queryset(self):
        """Return batches for current user."""
        return Batch.objects.filter(user=self.request.user).prefetch_related(
            'documents__document'
        )

    def perform_create(self, serializer):
        """Create batch for current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_documents(self, request, pk=None):
        """Add documents to a batch.

        POST /api/v1/batches/{id}/add-documents/
        Body: {
            "document_ids": ["uuid1", "uuid2", ...]
        }
        """
        batch = self.get_object()

        # Validate batch state
        if batch.status not in ['pending', 'partial_failure']:
            return Response(
                {
                    'detail': f'Cannot add documents to batch with status "{batch.status}"'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        document_ids = request.data.get('document_ids', [])

        if not document_ids:
            return Response(
                {'detail': 'document_ids is required and must not be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            processor = BatchProcessor(user=request.user)
            added, failed = processor.add_documents_to_batch(
                batch=batch,
                document_ids=document_ids
            )

            return Response(
                {
                    'success': True,
                    'added': added,
                    'failed': failed,
                    'batch_id': str(batch.id),
                    'file_count': batch.file_count,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error adding documents to batch: {str(e)}")
            return Response(
                {'detail': f'Error adding documents: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        """Start async processing for batch.

        POST /api/v1/batches/{id}/start-processing/
        """
        batch = self.get_object()

        if batch.status != 'pending':
            return Response(
                {
                    'detail': f'Batch must be in pending status, currently "{batch.status}"'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            processor = BatchProcessor(user=request.user)
            queued = processor.start_processing(batch)

            return Response(
                {
                    'success': True,
                    'batch_id': str(batch.id),
                    'documents_queued': queued,
                    'status': batch.status,
                    'estimated_completion': batch.estimated_completion.isoformat() if batch.estimated_completion else None,
                },
                status=status.HTTP_200_OK
            )

        except BatchProcessorError as e:
            logger.warning(f"Batch processing error: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error starting batch processing: {str(e)}")
            return Response(
                {'detail': f'Error starting processing: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get batch processing status and progress.

        GET /api/v1/batches/{id}/status/
        """
        batch = self.get_object()

        try:
            processor = BatchProcessor(user=request.user)
            batch_status = processor.get_batch_status(batch)

            return Response(batch_status, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting batch status: {str(e)}")
            return Response(
                {'detail': f'Error getting status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def errors(self, request, pk=None):
        """Get errors from failed documents in batch.

        GET /api/v1/batches/{id}/errors/
        """
        batch = self.get_object()

        limit = request.query_params.get('limit', 100)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 100

        try:
            processor = BatchProcessor(user=request.user)
            errors = processor.get_batch_errors(batch, limit=limit)

            return Response(
                {
                    'batch_id': str(batch.id),
                    'error_count': len(errors),
                    'errors': errors,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error getting batch errors: {str(e)}")
            return Response(
                {'detail': f'Error getting errors: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel batch processing.

        POST /api/v1/batches/{id}/cancel/
        """
        batch = self.get_object()

        try:
            processor = BatchProcessor(user=request.user)
            success = processor.cancel_batch(batch)

            if success:
                return Response(
                    {
                        'success': True,
                        'batch_id': str(batch.id),
                        'status': batch.status,
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'success': False,
                        'detail': f'Cannot cancel batch with status "{batch.status}"',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Error cancelling batch: {str(e)}")
            return Response(
                {'detail': f'Error cancelling batch: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def retry_document(self, request, pk=None):
        """Retry a failed document in batch.

        POST /api/v1/batches/{id}/retry-document/
        Body: {
            "batch_document_id": "uuid"
        }
        """
        batch = self.get_object()
        batch_document_id = request.data.get('batch_document_id')

        if not batch_document_id:
            return Response(
                {'detail': 'batch_document_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify document belongs to this batch
        try:
            batch_doc = BatchDocument.objects.get(id=batch_document_id, batch=batch)
        except BatchDocument.DoesNotExist:
            return Response(
                {'detail': 'Document not found in this batch'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            processor = BatchProcessor(user=request.user)
            task_id = processor.retry_failed_document(batch_document_id)

            if task_id:
                return Response(
                    {
                        'success': True,
                        'batch_document_id': batch_document_id,
                        'new_task_id': task_id,
                        'status': 'queued',
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'success': False,
                        'detail': 'Failed to queue retry',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Error retrying document: {str(e)}")
            return Response(
                {'detail': f'Error retrying document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing batch documents (read-only).

    Endpoints:
    - GET /api/v1/batch-documents/ - List all batch documents
    - GET /api/v1/batch-documents/{id}/ - Get batch document details
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BatchDocumentSerializer

    def get_queryset(self):
        """Return batch documents for current user's batches."""
        return BatchDocument.objects.filter(
            batch__user=self.request.user
        ).select_related('batch', 'document')
