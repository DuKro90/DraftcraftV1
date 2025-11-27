"""Tests for synthetic document factory."""
import pytest
from django.contrib.auth.models import User

from documents.models import Document
from tests.fixtures.test_document_factory import SyntheticDocumentFactory


@pytest.fixture
def test_user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


class TestSyntheticDocumentFactory:
    """Test synthetic document generation."""

    def test_create_text_document(self, db, test_user):
        """Test creating a single text document."""
        doc = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='invoice'
        )

        assert doc.id is not None
        assert doc.user == test_user
        assert doc.status == 'uploaded'
        assert doc.document_type == 'txt'
        assert doc.file_size_bytes > 0
        assert 'RECHNUNG' in doc.file.read().decode('utf-8')

    def test_create_different_document_types(self, db, test_user):
        """Test creating different document types."""
        types = ['invoice', 'estimate', 'offer']

        for doc_type in types:
            doc = SyntheticDocumentFactory.create_text_document(
                user=test_user,
                document_type=doc_type,
                include_keywords=True
            )

            assert doc.document_type == 'txt'
            assert doc.file_size_bytes > 0

            # Check content contains German terms
            content = doc.file.read().decode('utf-8')
            assert len(content) > 100

    def test_document_includes_keywords(self, db, test_user):
        """Test documents include construction keywords."""
        doc = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='invoice',
            include_keywords=True
        )

        content = doc.file.read().decode('utf-8')

        # Check for German construction terms
        keywords = ['Tischler', 'Schreiner', 'Holz', 'Oberfläche', 'EUR']
        assert any(keyword in content for keyword in keywords)

    def test_create_batch_documents(self, db, test_user):
        """Test creating batch of documents."""
        docs = SyntheticDocumentFactory.create_batch_documents(
            user=test_user,
            count=5,
            document_type='invoice'
        )

        assert len(docs) == 5
        for doc in docs:
            assert doc.user == test_user
            assert doc.status == 'uploaded'

    def test_batch_documents_are_different(self, db, test_user):
        """Test batch documents have different content."""
        docs = SyntheticDocumentFactory.create_batch_documents(
            user=test_user,
            count=3
        )

        contents = [doc.file.read().decode('utf-8') for doc in docs]

        # Check that not all contents are identical
        assert contents[0] != contents[1] or contents[1] != contents[2]

    def test_documents_with_variations(self, db, test_user):
        """Test creating documents with variations."""
        docs = SyntheticDocumentFactory.create_documents_with_variations(
            user=test_user,
            count=4,
            with_errors=False
        )

        assert len(docs) == 4
        for doc in docs:
            assert doc.user == test_user
            assert doc.file_size_bytes > 0

    def test_german_numbers_format(self, db, test_user):
        """Test German number formatting in documents."""
        doc = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='invoice'
        )

        content = doc.file.read().decode('utf-8')

        # Check for German number format (1.234,56)
        assert any(char in content for char in [',', '.'])

    def test_german_date_format(self, db, test_user):
        """Test German date formatting in documents."""
        doc = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='invoice'
        )

        content = doc.file.read().decode('utf-8')

        # Check for German date format (DD.MM.YYYY)
        assert '2024' in content
        assert '.' in content  # Date separator

    def test_invoice_structure(self, db, test_user):
        """Test invoice has proper structure."""
        doc = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='invoice'
        )

        content = doc.file.read().decode('utf-8')

        # Check for invoice elements
        required_elements = ['RECHNUNG', 'Rechnungsnummer:', 'EUR', 'Summe']
        for element in required_elements:
            assert element in content, f"Missing element: {element}"

    def test_estimate_structure(self, db, test_user):
        """Test estimate has proper structure."""
        doc = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='estimate'
        )

        content = doc.file.read().decode('utf-8')

        # Check for estimate elements
        required_elements = ['KOSTENVORANSCHLAG', 'Material', 'Verarbeitung']
        assert any(element in content for element in required_elements)

    def test_document_ownership(self, db, test_user):
        """Test documents belong to correct user."""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

        doc1 = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='invoice'
        )
        doc2 = SyntheticDocumentFactory.create_text_document(
            user=user2,
            document_type='invoice'
        )

        assert doc1.user == test_user
        assert doc2.user == user2
        assert doc1.user != doc2.user


class TestGAEBData:
    """Test GAEB (German construction standard) data generation."""

    def test_get_sample_gaeb_data(self):
        """Test GAEB data generation."""
        data = SyntheticDocumentFactory.get_sample_gaeb_data()

        # Check required fields
        required_fields = [
            'ordnungszahl', 'kurztext', 'langtext', 'material',
            'menge', 'einheit', 'einheitspreis', 'gesamtpreis'
        ]

        for field in required_fields:
            assert field in data
            assert data[field] is not None

    def test_gaeb_material_from_vocabulary(self):
        """Test GAEB data uses German materials."""
        data = SyntheticDocumentFactory.get_sample_gaeb_data()

        materials = SyntheticDocumentFactory.MATERIALS['Holzarten']
        assert data['material'] in materials

    def test_gaeb_multiple_generations_vary(self):
        """Test multiple GAEB generations produce different data."""
        data_sets = [
            SyntheticDocumentFactory.get_sample_gaeb_data()
            for _ in range(3)
        ]

        # At least some variation expected
        materials = [d['material'] for d in data_sets]
        amounts = [d['menge'] for d in data_sets]

        # Check variation exists
        assert len(set(materials)) > 1 or len(set(amounts)) > 1


class TestGermanTestData:
    """Test German terminology test data."""

    def test_get_german_test_data_samples(self):
        """Test getting German terminology samples."""
        samples = SyntheticDocumentFactory.get_german_test_data_samples()

        assert len(samples) > 0

        # Check structure
        for sample in samples:
            assert 'german' in sample
            assert 'english' in sample
            assert 'category' in sample

    def test_german_data_categories(self):
        """Test German data has valid categories."""
        samples = SyntheticDocumentFactory.get_german_test_data_samples()

        categories = set(s['category'] for s in samples)

        # Should have multiple categories
        assert len(categories) > 1
        assert 'Handwerk' in categories or 'Material' in categories

    def test_german_terms_non_empty(self):
        """Test all German terms are non-empty."""
        samples = SyntheticDocumentFactory.get_german_test_data_samples()

        for sample in samples:
            assert len(sample['german']) > 0
            assert len(sample['english']) > 0
            assert len(sample['category']) > 0


@pytest.mark.integration
class TestSyntheticDocumentsIntegration:
    """Integration tests for synthetic document generation."""

    def test_batch_creation_and_storage(self, db, test_user):
        """Test creating and storing batch of synthetic documents."""
        # Create batch
        docs = SyntheticDocumentFactory.create_batch_documents(
            user=test_user,
            count=10
        )

        # Verify all stored
        stored_docs = Document.objects.filter(user=test_user)
        assert stored_docs.count() >= 10

        # Verify content accessible
        for doc in docs:
            doc.refresh_from_db()
            assert doc.file_size_bytes > 0

    def test_different_document_types_in_batch(self, db, test_user):
        """Test batch with mixed document types."""
        # Create various types
        invoice = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='invoice'
        )
        estimate = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='estimate'
        )
        offer = SyntheticDocumentFactory.create_text_document(
            user=test_user,
            document_type='offer'
        )

        docs = [invoice, estimate, offer]

        # All should be accessible
        for doc in docs:
            retrieved = Document.objects.get(id=doc.id)
            assert retrieved.user == test_user

    def test_large_batch_generation(self, db, test_user):
        """Test generating large batch of documents."""
        docs = SyntheticDocumentFactory.create_batch_documents(
            user=test_user,
            count=50
        )

        assert len(docs) == 50

        # Sample check
        assert docs[0].user == test_user
        assert docs[49].user == test_user
        assert docs[0].id != docs[49].id
