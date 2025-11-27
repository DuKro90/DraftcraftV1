"""Tests for batch processing service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone

from documents.models import Batch, BatchDocument, Document
from extraction.services.batch_processor import BatchProcessor, BatchProcessorError


@pytest.fixture
def test_user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_documents(db, test_user):
    """Create test documents."""
    docs = []
    for i in range(3):
        doc = Document.objects.create(
            user=test_user,
            file=f'test_doc_{i}.pdf',
            original_filename=f'test_doc_{i}.pdf',
            file_size_bytes=1024 * 10,
            status='uploaded',
            document_type='pdf'
        )
        docs.append(doc)
    return docs


@pytest.fixture
def batch_processor(test_user):
    """Create batch processor instance."""
    return BatchProcessor(user=test_user)


class TestBatchCreation:
    """Test batch creation functionality."""

    def test_create_batch(self, db, batch_processor):
        """Test creating a new batch."""
        batch = batch_processor.create_batch(
            name='Test Batch',
            description='Test Description'
        )

        assert batch.name == 'Test Batch'
        assert batch.description == 'Test Description'
        assert batch.status == 'pending'
        assert batch.file_count == 0
        assert batch.processed_count == 0
        assert batch.error_count == 0

    def test_create_batch_with_metadata(self, db, batch_processor):
        """Test creating batch with metadata."""
        metadata = {'source': 'api', 'campaign': 'Q4_2024'}

        batch = batch_processor.create_batch(
            name='Batch with Metadata',
            metadata=metadata
        )

        assert batch.metadata == metadata

    def test_create_batch_persists(self, db, batch_processor):
        """Test batch is saved to database."""
        batch = batch_processor.create_batch(name='Persisted Batch')

        # Reload from database
        reloaded = Batch.objects.get(id=batch.id)
        assert reloaded.name == 'Persisted Batch'
        assert reloaded.user == batch_processor.user


class TestAddDocumentsToBatch:
    """Test adding documents to batch."""

    def test_add_single_document(self, db, batch_processor, test_documents):
        """Test adding a single document."""
        batch = batch_processor.create_batch(name='Test Batch')
        doc = test_documents[0]

        added, failed = batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(doc.id)]
        )

        assert added == 1
        assert failed == 0
        assert batch.file_count == 1

    def test_add_multiple_documents(self, db, batch_processor, test_documents):
        """Test adding multiple documents."""
        batch = batch_processor.create_batch(name='Test Batch')
        doc_ids = [str(d.id) for d in test_documents]

        added, failed = batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=doc_ids
        )

        assert added == 3
        assert failed == 0
        assert batch.file_count == 3

    def test_add_nonexistent_document(self, db, batch_processor):
        """Test adding non-existent document."""
        batch = batch_processor.create_batch(name='Test Batch')

        added, failed = batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=['00000000-0000-0000-0000-000000000000']
        )

        assert added == 0
        assert failed == 1

    def test_avoid_duplicate_documents(self, db, batch_processor, test_documents):
        """Test duplicate documents are not added twice."""
        batch = batch_processor.create_batch(name='Test Batch')
        doc = test_documents[0]

        # Add once
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(doc.id)]
        )

        # Try to add again
        added, failed = batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(doc.id)]
        )

        assert added == 0  # Not added again
        assert batch.file_count == 1  # Still only 1

    def test_cannot_add_to_processing_batch(self, db, batch_processor, test_documents):
        """Test cannot add documents to processing batch."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch.status = 'processing'
        batch.save()

        with pytest.raises(BatchProcessorError):
            batch_processor.add_documents_to_batch(
                batch=batch,
                document_ids=[str(test_documents[0].id)]
            )


class TestStartProcessing:
    """Test starting batch processing."""

    @patch('extraction.async_executor.AsyncExecutor.process_document')
    def test_start_processing_queues_documents(
        self,
        mock_process,
        db,
        batch_processor,
        test_documents
    ):
        """Test starting processing queues all documents."""
        mock_process.return_value = 'task-123'

        batch = batch_processor.create_batch(name='Test Batch')
        doc_ids = [str(d.id) for d in test_documents]
        batch_processor.add_documents_to_batch(batch=batch, document_ids=doc_ids)

        queued = batch_processor.start_processing(batch)

        assert queued == 3
        assert batch.status == 'processing'
        assert mock_process.call_count == 3

    @patch('extraction.async_executor.AsyncExecutor.process_document')
    def test_queued_documents_have_task_ids(
        self,
        mock_process,
        db,
        batch_processor,
        test_documents
    ):
        """Test queued documents store task IDs."""
        mock_process.return_value = 'task-123'

        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        batch_processor.start_processing(batch)

        batch_doc = BatchDocument.objects.first()
        assert batch_doc.status == 'queued'
        assert batch_doc.cloud_task_id == 'task-123'

    def test_cannot_process_empty_batch(self, db, batch_processor):
        """Test cannot process batch with no documents."""
        batch = batch_processor.create_batch(name='Empty Batch')

        with pytest.raises(BatchProcessorError):
            batch_processor.start_processing(batch)

    def test_cannot_reprocess_completed_batch(self, db, batch_processor, test_documents):
        """Test cannot re-process completed batch."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )
        batch.status = 'completed'
        batch.save()

        with pytest.raises(BatchProcessorError):
            batch_processor.start_processing(batch)


class TestUpdateDocumentStatus:
    """Test updating document status during processing."""

    def test_update_document_to_completed(self, db, batch_processor, test_documents):
        """Test marking document as completed."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        batch_doc = BatchDocument.objects.first()
        batch_processor.update_document_status(
            batch_doc_id=str(batch_doc.id),
            status='completed'
        )

        batch_doc.refresh_from_db()
        assert batch_doc.status == 'completed'
        assert batch_doc.processed_at is not None

    def test_update_document_to_failed(self, db, batch_processor, test_documents):
        """Test marking document as failed with error."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        batch_doc = BatchDocument.objects.first()
        batch_processor.update_document_status(
            batch_doc_id=str(batch_doc.id),
            status='failed',
            error_message='OCR confidence too low'
        )

        batch_doc.refresh_from_db()
        assert batch_doc.status == 'failed'
        assert batch_doc.error_message == 'OCR confidence too low'
        assert batch_doc.processed_at is not None

    def test_update_nonexistent_document(self, db, batch_processor):
        """Test error when document not found."""
        with pytest.raises(BatchProcessorError):
            batch_processor.update_document_status(
                batch_doc_id='00000000-0000-0000-0000-000000000000',
                status='completed'
            )


class TestBatchProgress:
    """Test batch progress tracking."""

    def test_get_batch_status(self, db, batch_processor, test_documents):
        """Test getting batch status."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(d.id) for d in test_documents]
        )

        status = batch_processor.get_batch_status(batch)

        assert status['batch_id'] == str(batch.id)
        assert status['file_count'] == 3
        assert status['processed_count'] == 0
        assert status['error_count'] == 0
        assert status['progress_percentage'] == 0.0

    def test_progress_percentage_calculation(self, db, batch_processor, test_documents):
        """Test progress percentage calculation."""
        batch = batch_processor.create_batch(name='Test Batch')
        doc_ids = [str(d.id) for d in test_documents]
        batch_processor.add_documents_to_batch(batch=batch, document_ids=doc_ids)

        # Mark some as completed
        batch_docs = BatchDocument.objects.filter(batch=batch)
        batch_docs[0].status = 'completed'
        batch_docs[0].save()

        assert batch.progress_percentage == pytest.approx(33.33, rel=1e-2)

    def test_batch_completion_detection(self, db, batch_processor, test_documents):
        """Test batch marks as completed when all docs done."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        batch_doc = BatchDocument.objects.first()
        batch_processor.update_document_status(
            batch_doc_id=str(batch_doc.id),
            status='completed'
        )

        batch.refresh_from_db()
        assert batch.status == 'completed'
        assert batch.completed_at is not None

    def test_batch_partial_failure_detection(self, db, batch_processor, test_documents):
        """Test batch marks as partial_failure with some failures."""
        batch = batch_processor.create_batch(name='Test Batch')
        doc_ids = [str(d.id) for d in test_documents]
        batch_processor.add_documents_to_batch(batch=batch, document_ids=doc_ids)

        batch_docs = BatchDocument.objects.filter(batch=batch)
        # Mark first as completed
        batch_processor.update_document_status(
            batch_doc_id=str(batch_docs[0].id),
            status='completed'
        )

        # Mark second as failed
        batch_processor.update_document_status(
            batch_doc_id=str(batch_docs[1].id),
            status='failed'
        )

        batch.refresh_from_db()
        assert batch.status == 'partial_failure'


class TestBatchCancellation:
    """Test batch cancellation."""

    def test_cancel_pending_batch(self, db, batch_processor, test_documents):
        """Test cancelling a pending batch."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        result = batch_processor.cancel_batch(batch)

        assert result is True
        batch.refresh_from_db()
        assert batch.status == 'failed'
        assert batch.completed_at is not None

    def test_cancel_cannot_recancel(self, db, batch_processor, test_documents):
        """Test cannot cancel already completed batch."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        # Already completed
        batch.status = 'completed'
        batch.save()

        result = batch_processor.cancel_batch(batch)

        assert result is False


class TestRetryFailedDocument:
    """Test retrying failed documents."""

    @patch('extraction.async_executor.AsyncExecutor.process_document')
    def test_retry_failed_document(
        self,
        mock_process,
        db,
        batch_processor,
        test_documents
    ):
        """Test retrying a failed document."""
        mock_process.return_value = 'task-retry-123'

        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        batch_doc = BatchDocument.objects.first()
        batch_doc.status = 'failed'
        batch_doc.error_message = 'Original error'
        batch_doc.save()

        task_id = batch_processor.retry_failed_document(str(batch_doc.id))

        assert task_id == 'task-retry-123'
        batch_doc.refresh_from_db()
        assert batch_doc.status == 'queued'
        assert batch_doc.error_message == ''

    def test_cannot_retry_completed_document(self, db, batch_processor, test_documents):
        """Test cannot retry completed document."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(test_documents[0].id)]
        )

        batch_doc = BatchDocument.objects.first()
        batch_doc.status = 'completed'
        batch_doc.save()

        result = batch_processor.retry_failed_document(str(batch_doc.id))

        assert result is None


class TestBatchErrorReporting:
    """Test error reporting from batch."""

    def test_get_batch_errors(self, db, batch_processor, test_documents):
        """Test getting errors from failed documents."""
        batch = batch_processor.create_batch(name='Test Batch')
        doc_ids = [str(d.id) for d in test_documents]
        batch_processor.add_documents_to_batch(batch=batch, document_ids=doc_ids)

        # Mark some as failed
        batch_docs = BatchDocument.objects.filter(batch=batch)
        batch_docs[0].status = 'failed'
        batch_docs[0].error_message = 'OCR failed'
        batch_docs[0].save()

        errors = batch_processor.get_batch_errors(batch)

        assert len(errors) == 1
        assert errors[0]['document_name'] == test_documents[0].original_filename
        assert errors[0]['error_message'] == 'OCR failed'

    def test_get_batch_errors_limit(self, db, batch_processor, test_documents):
        """Test error limit on retrieval."""
        batch = batch_processor.create_batch(name='Test Batch')
        batch_processor.add_documents_to_batch(
            batch=batch,
            document_ids=[str(d.id) for d in test_documents]
        )

        # Mark all as failed
        BatchDocument.objects.filter(batch=batch).update(
            status='failed',
            error_message='Test error'
        )

        errors = batch_processor.get_batch_errors(batch, limit=1)

        assert len(errors) == 1


@pytest.mark.integration
class TestBatchProcessorIntegration:
    """Integration tests for batch processor."""

    @patch('extraction.async_executor.AsyncExecutor.process_document')
    def test_full_batch_workflow(
        self,
        mock_process,
        db,
        batch_processor,
        test_documents
    ):
        """Test complete batch workflow."""
        mock_process.return_value = 'task-123'

        # Create batch
        batch = batch_processor.create_batch(
            name='Integration Test Batch',
            description='Testing full workflow'
        )

        # Add documents
        doc_ids = [str(d.id) for d in test_documents]
        batch_processor.add_documents_to_batch(batch=batch, document_ids=doc_ids)

        # Start processing
        queued = batch_processor.start_processing(batch)
        assert queued == 3

        # Get status
        status = batch_processor.get_batch_status(batch)
        assert status['status'] == 'processing'

        # Simulate completion
        for batch_doc in BatchDocument.objects.filter(batch=batch):
            batch_processor.update_document_status(
                batch_doc_id=str(batch_doc.id),
                status='completed'
            )

        # Check final status
        batch.refresh_from_db()
        assert batch.status == 'completed'
