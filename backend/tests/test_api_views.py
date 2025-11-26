"""Tests for API views."""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document, AuditLog
from extraction.models import ExtractionConfig, ExtractedEntity


@pytest.mark.django_db
class TestDocumentAPI:
    """Tests for Document API endpoints."""

    def setup_method(self):
        """Setup test client and user."""
        self.client = APIClient()

    def test_document_list_requires_auth(self):
        """Test that document list requires authentication."""
        response = self.client.get('/api/v1/documents/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_document_upload(self, authenticated_api_client, authenticated_user):
        """Test document upload."""
        file = SimpleUploadedFile(
            'test.pdf',
            b'PDF content',
            content_type='application/pdf'
        )

        data = {
            'file': file,
            'document_type': 'pdf',
        }

        response = authenticated_api_client.post('/api/v1/documents/', data, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['original_filename'] == 'test.pdf'
        assert response.data['status'] == 'uploaded'

        # Verify audit log created
        logs = AuditLog.objects.filter(action='uploaded')
        assert logs.count() == 1
        assert logs.first().user == authenticated_user

    def test_document_list(self, authenticated_api_client, authenticated_user):
        """Test listing documents for authenticated user."""
        # Create documents
        doc1 = Document.objects.create(
            user=authenticated_user,
            file='test1.pdf',
            original_filename='test1.pdf',
            file_size_bytes=1024,
        )

        doc2 = Document.objects.create(
            user=authenticated_user,
            file='test2.pdf',
            original_filename='test2.pdf',
            file_size_bytes=2048,
        )

        response = authenticated_api_client.get('/api/v1/documents/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_document_retrieve(self, authenticated_api_client, authenticated_user):
        """Test retrieving single document."""
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='uploaded',
        )

        response = authenticated_api_client.get(f'/api/v1/documents/{doc.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['original_filename'] == 'test.pdf'
        assert response.data['status'] == 'uploaded'

    def test_document_isolation(self, authenticated_api_client, authenticated_user, db):
        """Test that users can only see their own documents."""
        from django.contrib.auth.models import User

        # Create another user
        other_user = User.objects.create_user('otheruser', 'other@example.com', 'pass123')

        # Create document for other user
        Document.objects.create(
            user=other_user,
            file='other.pdf',
            original_filename='other.pdf',
            file_size_bytes=1024,
        )

        # Create document for authenticated user
        Document.objects.create(
            user=authenticated_user,
            file='mine.pdf',
            original_filename='mine.pdf',
            file_size_bytes=1024,
        )

        response = authenticated_api_client.get('/api/v1/documents/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['original_filename'] == 'mine.pdf'


@pytest.mark.django_db
class TestEntityAPI:
    """Tests for ExtractedEntity API endpoints."""

    def test_entity_list_requires_auth(self):
        """Test that entity list requires authentication."""
        client = APIClient()
        response = client.get('/api/v1/entities/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_entity_list(self, authenticated_api_client, authenticated_user):
        """Test listing entities for user's documents."""
        # Create document
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
        )

        # Create entities
        ExtractedEntity.objects.create(
            document=doc,
            entity_type='MATERIAL',
            text='Eiche',
            start_offset=0,
            end_offset=5,
            confidence_score=0.95,
        )

        ExtractedEntity.objects.create(
            document=doc,
            entity_type='QUANTITY',
            text='5 m²',
            start_offset=6,
            end_offset=10,
            confidence_score=0.88,
        )

        response = authenticated_api_client.get('/api/v1/entities/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_entity_filter_by_document(self, authenticated_api_client, authenticated_user):
        """Test filtering entities by document."""
        doc1 = Document.objects.create(
            user=authenticated_user,
            file='test1.pdf',
            original_filename='test1.pdf',
            file_size_bytes=1024,
        )

        doc2 = Document.objects.create(
            user=authenticated_user,
            file='test2.pdf',
            original_filename='test2.pdf',
            file_size_bytes=1024,
        )

        # Create entities for doc1
        ExtractedEntity.objects.create(
            document=doc1,
            entity_type='MATERIAL',
            text='Eiche',
            start_offset=0,
            end_offset=5,
            confidence_score=0.95,
        )

        # Create entities for doc2
        ExtractedEntity.objects.create(
            document=doc2,
            entity_type='MATERIAL',
            text='Buche',
            start_offset=0,
            end_offset=5,
            confidence_score=0.92,
        )

        response = authenticated_api_client.get(f'/api/v1/entities/?document_id={doc1.id}')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['text'] == 'Eiche'

    def test_entity_filter_by_type(self, authenticated_api_client, authenticated_user):
        """Test filtering entities by type."""
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
        )

        ExtractedEntity.objects.create(
            document=doc,
            entity_type='MATERIAL',
            text='Eiche',
            start_offset=0,
            end_offset=5,
            confidence_score=0.95,
        )

        ExtractedEntity.objects.create(
            document=doc,
            entity_type='QUANTITY',
            text='5 m²',
            start_offset=6,
            end_offset=10,
            confidence_score=0.88,
        )

        response = authenticated_api_client.get('/api/v1/entities/?entity_type=MATERIAL')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['entity_type'] == 'MATERIAL'


@pytest.mark.django_db
class TestExtractionConfigAPI:
    """Tests for ExtractionConfig API endpoints (admin only)."""

    def test_config_list_requires_admin(self, authenticated_api_client):
        """Test that config list requires admin permission."""
        response = authenticated_api_client.get('/api/v1/extraction-config/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_config_list_admin(self, admin_api_client):
        """Test listing config as admin."""
        ExtractionConfig.objects.create(
            name='german_default',
            language='de',
        )

        response = admin_api_client.get('/api/v1/extraction-config/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_config_create_admin(self, admin_api_client):
        """Test creating config as admin."""
        data = {
            'name': 'german_prod',
            'language': 'de',
            'ocr_enabled': True,
            'ocr_confidence_threshold': 0.7,
            'ner_enabled': True,
            'ner_model': 'de_core_news_lg',
        }

        response = admin_api_client.post('/api/v1/extraction-config/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'german_prod'


@pytest.mark.django_db
class TestAuditLogging:
    """Tests for audit logging in API."""

    def test_upload_creates_audit_log(self, authenticated_api_client, authenticated_user):
        """Test that uploading creates audit log."""
        file = SimpleUploadedFile('test.pdf', b'content')
        response = authenticated_api_client.post(
            '/api/v1/documents/',
            {'file': file, 'document_type': 'pdf'},
            format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Check audit log
        logs = AuditLog.objects.all()
        assert logs.count() == 1
        assert logs.first().action == 'uploaded'
        assert logs.first().user == authenticated_user
