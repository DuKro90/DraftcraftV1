"""Tests for extraction services."""
import pytest
from decimal import Decimal
from extraction.services import GermanOCRService, GermanNERService
from extraction.services.base_service import ExtractionServiceError
from extraction.models import ExtractionConfig, ExtractedEntity, MaterialExtraction
from documents.models import Document


@pytest.mark.unit
class TestGermanOCRService:
    """Tests for GermanOCRService."""

    def test_initialization(self):
        """Test OCR service initialization."""
        config = {'ocr_use_cuda': False, 'max_file_size_mb': 50}
        service = GermanOCRService(config)
        assert service.config == config
        assert service.timeout_seconds == 300

    def test_initialization_with_timeout(self):
        """Test OCR service initialization with custom timeout."""
        config = {}
        service = GermanOCRService(config, timeout_seconds=600)
        assert service.timeout_seconds == 600

    def test_invalid_file_path(self):
        """Test error handling for invalid file path."""
        config = {'max_file_size_mb': 50}
        service = GermanOCRService(config)

        with pytest.raises(ExtractionServiceError, match="File not found"):
            service.process("/nonexistent/file.pdf")

    def test_extraction_config_creation(self, db):
        """Test ExtractionConfig model."""
        config = ExtractionConfig.objects.create(
            name='german_default',
            language='de',
            ocr_enabled=True,
            ocr_confidence_threshold=0.6,
            ner_enabled=True,
            ner_model='de_core_news_lg',
        )
        assert config.name == 'german_default'
        assert config.language == 'de'
        assert config.ocr_enabled is True
        assert str(config) == 'german_default (de)'


@pytest.mark.unit
class TestGermanNERService:
    """Tests for GermanNERService."""

    def test_initialization(self):
        """Test NER service initialization."""
        config = {'ner_model': 'de_core_news_lg', 'ner_confidence_threshold': 0.7}
        service = GermanNERService(config)
        assert service.config == config
        assert service.timeout_seconds == 300

    def test_empty_text_error(self):
        """Test error handling for empty text."""
        config = {}
        service = GermanNERService(config)

        with pytest.raises(ExtractionServiceError, match="Empty text"):
            service.process("")

    def test_entity_mapping(self):
        """Test entity type mapping."""
        config = {}
        service = GermanNERService(config)

        assert service._map_entity_type('PER') == 'PERSON'
        assert service._map_entity_type('ORG') == 'ORGANIZATION'
        assert service._map_entity_type('LOC') == 'LOCATION'
        assert service._map_entity_type('DATE') == 'DATE'
        assert service._map_entity_type('MONEY') == 'PRICE'
        assert service._map_entity_type('QUANTITY') == 'QUANTITY'
        assert service._map_entity_type('UNKNOWN') == 'OTHER'

    def test_count_entities(self):
        """Test entity counting."""
        config = {}
        service = GermanNERService(config)

        entities = [
            {'type': 'MATERIAL', 'text': 'Eiche', 'confidence': 0.9},
            {'type': 'QUANTITY', 'text': '5', 'confidence': 0.85},
            {'type': 'MATERIAL', 'text': 'Buche', 'confidence': 0.88},
        ]

        counts = service._count_entities(entities)
        assert counts['MATERIAL'] == 2
        assert counts['QUANTITY'] == 1

    def test_calculate_confidence(self):
        """Test confidence calculation."""
        config = {}
        service = GermanNERService(config)

        entities = [
            {'type': 'MATERIAL', 'text': 'Eiche', 'confidence': 0.9},
            {'type': 'QUANTITY', 'text': '5', 'confidence': 0.8},
        ]

        confidence = service._calculate_confidence(entities)
        assert confidence == 0.85  # Average of 0.9 and 0.8

    def test_calculate_confidence_empty(self):
        """Test confidence calculation with empty entities."""
        config = {}
        service = GermanNERService(config)

        confidence = service._calculate_confidence([])
        assert confidence == 0.0


@pytest.mark.unit
class TestExtractedEntity:
    """Tests for ExtractedEntity model."""

    def test_entity_creation(self, db, authenticated_user):
        """Test creating an extracted entity."""
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='pdf',
        )

        entity = ExtractedEntity.objects.create(
            document=doc,
            entity_type='MATERIAL',
            text='Eiche',
            start_offset=0,
            end_offset=5,
            confidence_score=0.92,
        )

        assert entity.entity_type == 'MATERIAL'
        assert entity.text == 'Eiche'
        assert entity.confidence_score == 0.92
        assert str(entity) == 'MATERIAL: Eiche'

    def test_entity_metadata(self, db, authenticated_user):
        """Test entity metadata storage."""
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='pdf',
        )

        entity = ExtractedEntity.objects.create(
            document=doc,
            entity_type='QUANTITY',
            text='5 m²',
            start_offset=10,
            end_offset=15,
            confidence_score=0.88,
            metadata={'normalized_value': 5.0, 'unit': 'm²'},
        )

        assert entity.metadata['normalized_value'] == 5.0
        assert entity.metadata['unit'] == 'm²'


@pytest.mark.unit
class TestMaterialExtraction:
    """Tests for MaterialExtraction model."""

    def test_material_extraction_creation(self, db, authenticated_user):
        """Test creating material extraction record."""
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='pdf',
        )

        materials = MaterialExtraction.objects.create(
            document=doc,
            materials={'eiche': 3.0, 'buche': 2.0},
            complexity_level='milled',
            surface_finish='painted',
            additional_features=['assembly'],
            dimensions={'width': 80, 'height': 120, 'depth': 40},
            unit='cm',
            extraction_confidence=0.89,
        )

        assert materials.materials['eiche'] == 3.0
        assert materials.complexity_level == 'milled'
        assert materials.extraction_confidence == 0.89
        assert 'assembly' in materials.additional_features

    def test_material_extraction_manual_review(self, db, authenticated_user):
        """Test manual review flag."""
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='pdf',
        )

        materials = MaterialExtraction.objects.create(
            document=doc,
            materials={},
            requires_manual_review=True,
            review_notes='Complex specifications require manual verification',
        )

        assert materials.requires_manual_review is True
        assert 'Complex' in materials.review_notes


@pytest.mark.integration
class TestExtractionWorkflow:
    """Integration tests for extraction workflow."""

    def test_document_entity_relationship(self, db, authenticated_user):
        """Test relationship between Document and ExtractedEntity."""
        doc = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='pdf',
        )

        # Create multiple entities
        entities_data = [
            ('MATERIAL', 'Eiche', 0, 5, 0.92),
            ('QUANTITY', '3', 6, 7, 0.85),
            ('UNIT', 'm²', 8, 10, 0.90),
        ]

        for ent_type, text, start, end, conf in entities_data:
            ExtractedEntity.objects.create(
                document=doc,
                entity_type=ent_type,
                text=text,
                start_offset=start,
                end_offset=end,
                confidence_score=conf,
            )

        # Query relationships
        entities = doc.extracted_entities.all()
        assert entities.count() == 3

        materials = entities.filter(entity_type='MATERIAL')
        assert materials.count() == 1
        assert materials.first().text == 'Eiche'

    def test_extraction_config_defaults(self, db):
        """Test ExtractionConfig default values."""
        config = ExtractionConfig.objects.create(name='test_config')

        assert config.language == 'de'
        assert config.ocr_enabled is True
        assert config.ocr_confidence_threshold == 0.6
        assert config.ner_enabled is True
        assert config.ner_model == 'de_core_news_lg'
        assert config.ner_confidence_threshold == 0.7
        assert config.max_file_size_mb == 50
        assert config.timeout_seconds == 300
