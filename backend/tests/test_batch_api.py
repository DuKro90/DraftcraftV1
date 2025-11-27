"""Tests for batch API endpoints."""
import pytest
import json
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from documents.models import Batch, BatchDocument, Document


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create test user with token."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    Token.objects.create(user=user)
    return user


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Create authenticated API client."""
    token = Token.objects.get(user=test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


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
def test_batch(db, test_user):
    """Create test batch."""
    return Batch.objects.create(
        user=test_user,
        name='Test Batch',
        status='pending'
    )


class TestBatchListEndpoint:
    """Test batch list endpoint."""

    def test_list_batches_unauthenticated(self, api_client):
        """Test list batches requires authentication."""
        response = api_client.get('/api/v1/batches/')
        assert response.status_code == 401

    def test_list_batches_authenticated(self, db, authenticated_client, test_user):
        """Test listing batches for authenticated user."""
        # Create batches
        batch1 = Batch.objects.create(user=test_user, name='Batch 1', status='pending')
        batch2 = Batch.objects.create(user=test_user, name='Batch 2', status='processing')

        response = authenticated_client.get('/api/v1/batches/')

        assert response.status_code == 200
        data = response.json()
        assert len(data['results']) == 2
        assert data['results'][0]['name'] in ['Batch 1', 'Batch 2']

    def test_list_batches_only_own(self, db, authenticated_client, test_user):
        """Test user only sees own batches."""
        user2 = User.objects.create_user(username='user2', password='pass')

        # Create batches for both users
        Batch.objects.create(user=test_user, name='My Batch', status='pending')
        Batch.objects.create(user=user2, name='Other Batch', status='pending')

        response = authenticated_client.get('/api/v1/batches/')

        assert response.status_code == 200
        data = response.json()
        assert len(data['results']) == 1
        assert data['results'][0]['name'] == 'My Batch'


class TestBatchCreateEndpoint:
    """Test batch creation endpoint."""

    def test_create_batch(self, authenticated_client):
        """Test creating a batch."""
        response = authenticated_client.post('/api/v1/batches/', {
            'name': 'New Batch',
            'description': 'Test batch',
            'metadata': {'source': 'api'}
        })

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'New Batch'
        assert data['description'] == 'Test batch'

    def test_create_batch_minimal(self, authenticated_client):
        """Test creating batch with minimal data."""
        response = authenticated_client.post('/api/v1/batches/', {
            'name': 'Minimal Batch'
        })

        assert response.status_code == 201
        assert response.json()['name'] == 'Minimal Batch'


class TestAddDocumentsEndpoint:
    """Test adding documents to batch endpoint."""

    def test_add_documents_to_batch(self, authenticated_client, test_batch, test_documents):
        """Test adding documents to batch."""
        doc_ids = [str(d.id) for d in test_documents]

        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['added'] == 3

    def test_add_documents_empty_list(self, authenticated_client, test_batch):
        """Test adding empty document list fails."""
        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': []},
            format='json'
        )

        assert response.status_code == 400

    def test_add_documents_missing_field(self, authenticated_client, test_batch):
        """Test missing document_ids field."""
        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {},
            format='json'
        )

        assert response.status_code == 400

    def test_add_documents_nonexistent(self, authenticated_client, test_batch):
        """Test adding non-existent documents."""
        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': ['00000000-0000-0000-0000-000000000000']},
            format='json'
        )

        assert response.status_code == 200
        assert response.json()['added'] == 0
        assert response.json()['failed'] == 1

    def test_cannot_add_to_completed_batch(self, db, authenticated_client, test_user, test_documents):
        """Test cannot add documents to completed batch."""
        batch = Batch.objects.create(user=test_user, name='Completed', status='completed')
        doc_ids = [str(d.id) for d in test_documents]

        response = authenticated_client.post(
            f'/api/v1/batches/{batch.id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )

        assert response.status_code == 400


class TestStartProcessingEndpoint:
    """Test start processing endpoint."""

    @patch('extraction.async_executor.AsyncExecutor.process_document')
    def test_start_processing(self, mock_process, authenticated_client, test_batch, test_documents):
        """Test starting batch processing."""
        mock_process.return_value = 'task-123'

        # Add documents first
        doc_ids = [str(d.id) for d in test_documents]
        authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )

        # Start processing
        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/start-processing/',
            {},
            format='json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['documents_queued'] == 3

    def test_start_processing_empty_batch(self, authenticated_client, test_batch):
        """Test cannot process empty batch."""
        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/start-processing/',
            {},
            format='json'
        )

        assert response.status_code == 400

    def test_cannot_reprocess_batch(self, db, authenticated_client, test_user, test_documents):
        """Test cannot re-process already processing batch."""
        batch = Batch.objects.create(user=test_user, name='Processing', status='processing')

        response = authenticated_client.post(
            f'/api/v1/batches/{batch.id}/start-processing/',
            {},
            format='json'
        )

        assert response.status_code == 400


class TestBatchStatusEndpoint:
    """Test batch status endpoint."""

    def test_get_batch_status(self, db, authenticated_client, test_batch, test_documents):
        """Test getting batch status."""
        # Add documents
        doc_ids = [str(d.id) for d in test_documents]
        authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )

        response = authenticated_client.get(
            f'/api/v1/batches/{test_batch.id}/status/'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['batch_id'] == str(test_batch.id)
        assert data['file_count'] == 3
        assert data['progress_percentage'] == 0.0

    def test_status_progress_calculation(self, db, authenticated_client, test_batch, test_documents):
        """Test progress percentage in status."""
        # Add and mark one as complete
        doc_ids = [str(d.id) for d in test_documents]
        authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )

        # Mark one as completed
        batch_doc = BatchDocument.objects.first()
        batch_doc.status = 'completed'
        batch_doc.save()

        response = authenticated_client.get(
            f'/api/v1/batches/{test_batch.id}/status/'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['processed_count'] == 1


class TestBatchErrorsEndpoint:
    """Test batch errors endpoint."""

    def test_get_batch_errors(self, db, authenticated_client, test_batch, test_documents):
        """Test getting batch errors."""
        # Add documents
        doc_ids = [str(d.id) for d in test_documents]
        authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )

        # Mark one as failed
        batch_doc = BatchDocument.objects.first()
        batch_doc.status = 'failed'
        batch_doc.error_message = 'OCR failed'
        batch_doc.save()

        response = authenticated_client.get(
            f'/api/v1/batches/{test_batch.id}/errors/'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['error_count'] == 1
        assert len(data['errors']) == 1
        assert data['errors'][0]['error_message'] == 'OCR failed'

    def test_get_errors_with_limit(self, db, authenticated_client, test_user):
        """Test error limit parameter."""
        batch = Batch.objects.create(user=test_user, name='Test', status='processing')

        # Create multiple failures
        for i in range(5):
            doc = Document.objects.create(
                user=test_user,
                file=f'doc_{i}.pdf',
                original_filename=f'doc_{i}.pdf',
                file_size_bytes=100,
                status='uploaded'
            )
            bd = BatchDocument.objects.create(
                batch=batch,
                document=doc,
                status='failed',
                error_message=f'Error {i}'
            )

        response = authenticated_client.get(
            f'/api/v1/batches/{batch.id}/errors/?limit=2'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['error_count'] == 2


class TestBatchCancelEndpoint:
    """Test batch cancellation endpoint."""

    def test_cancel_pending_batch(self, authenticated_client, test_batch):
        """Test cancelling pending batch."""
        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/cancel/',
            {},
            format='json'
        )

        assert response.status_code == 200
        assert response.json()['success'] is True

        test_batch.refresh_from_db()
        assert test_batch.status == 'failed'

    def test_cannot_cancel_completed_batch(self, db, authenticated_client, test_user):
        """Test cannot cancel completed batch."""
        batch = Batch.objects.create(user=test_user, name='Completed', status='completed')

        response = authenticated_client.post(
            f'/api/v1/batches/{batch.id}/cancel/',
            {},
            format='json'
        )

        assert response.status_code == 400


class TestRetryDocumentEndpoint:
    """Test retry document endpoint."""

    @patch('extraction.async_executor.AsyncExecutor.process_document')
    def test_retry_failed_document(self, mock_process, db, authenticated_client, test_user):
        """Test retrying a failed document."""
        mock_process.return_value = 'task-retry'

        batch = Batch.objects.create(user=test_user, name='Test', status='processing')
        doc = Document.objects.create(
            user=test_user,
            file='doc.pdf',
            original_filename='doc.pdf',
            file_size_bytes=100,
            status='uploaded'
        )
        batch_doc = BatchDocument.objects.create(
            batch=batch,
            document=doc,
            status='failed',
            error_message='Original error'
        )

        response = authenticated_client.post(
            f'/api/v1/batches/{batch.id}/retry-document/',
            {'batch_document_id': str(batch_doc.id)},
            format='json'
        )

        assert response.status_code == 200
        assert response.json()['success'] is True
        assert response.json()['new_task_id'] == 'task-retry'

    def test_retry_missing_document_id(self, authenticated_client, test_batch):
        """Test retry with missing document_id."""
        response = authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/retry-document/',
            {},
            format='json'
        )

        assert response.status_code == 400

    def test_retry_document_not_in_batch(self, db, authenticated_client, test_user):
        """Test retry document from different batch."""
        batch1 = Batch.objects.create(user=test_user, name='Batch1', status='processing')
        batch2 = Batch.objects.create(user=test_user, name='Batch2', status='processing')

        doc = Document.objects.create(
            user=test_user,
            file='doc.pdf',
            original_filename='doc.pdf',
            file_size_bytes=100,
            status='uploaded'
        )
        batch_doc = BatchDocument.objects.create(
            batch=batch2,
            document=doc,
            status='failed'
        )

        response = authenticated_client.post(
            f'/api/v1/batches/{batch1.id}/retry-document/',
            {'batch_document_id': str(batch_doc.id)},
            format='json'
        )

        assert response.status_code == 404


class TestBatchDetailEndpoint:
    """Test batch detail endpoint."""

    def test_get_batch_detail(self, db, authenticated_client, test_batch, test_documents):
        """Test getting batch details."""
        # Add documents
        doc_ids = [str(d.id) for d in test_documents]
        authenticated_client.post(
            f'/api/v1/batches/{test_batch.id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )

        response = authenticated_client.get(f'/api/v1/batches/{test_batch.id}/')

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Test Batch'
        assert data['file_count'] == 3
        assert len(data['documents']) == 3


@pytest.mark.integration
class TestBatchAPIIntegration:
    """Integration tests for batch API."""

    @patch('extraction.async_executor.AsyncExecutor.process_document')
    def test_full_batch_workflow_via_api(self, mock_process, authenticated_client, test_user, test_documents):
        """Test complete batch workflow via API."""
        mock_process.return_value = 'task-123'

        # Create batch
        response = authenticated_client.post('/api/v1/batches/', {
            'name': 'Integration Batch'
        })
        assert response.status_code == 201
        batch_id = response.json()['id']

        # Add documents
        doc_ids = [str(d.id) for d in test_documents]
        response = authenticated_client.post(
            f'/api/v1/batches/{batch_id}/add-documents/',
            {'document_ids': doc_ids},
            format='json'
        )
        assert response.status_code == 200

        # Start processing
        response = authenticated_client.post(
            f'/api/v1/batches/{batch_id}/start-processing/',
            {},
            format='json'
        )
        assert response.status_code == 200

        # Get status
        response = authenticated_client.get(f'/api/v1/batches/{batch_id}/status/')
        assert response.status_code == 200
        assert response.json()['status'] == 'processing'
