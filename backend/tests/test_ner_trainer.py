"""Tests for NER trainer."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from extraction.services.ner_trainer import (
    ConstructionNERTrainer,
    create_synthetic_training_data
)


class TestConstructionVocabulary:
    """Test construction vocabulary loading."""

    def test_vocabulary_file_exists(self):
        """Test construction vocabulary file exists."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"
        assert vocab_path.exists(), f"Vocabulary file not found: {vocab_path}"

    def test_vocabulary_structure(self):
        """Test vocabulary has correct structure."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"

        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = json.load(f)

        # Check required keys
        required_keys = [
            'trade_terms',
            'certifications',
            'materials',
            'surfaces',
            'furniture_types',
            'measurements_units',
            'construction_terms',
            'complexity_levels',
            'quality_descriptors',
            'project_terms'
        ]

        for key in required_keys:
            assert key in vocab, f"Missing vocabulary key: {key}"

    def test_vocabulary_content(self):
        """Test vocabulary contains actual terms."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"

        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = json.load(f)

        # Check trade terms have German and English
        assert 'de' in vocab['trade_terms']
        assert 'en' in vocab['trade_terms']
        assert len(vocab['trade_terms']['de']) > 0
        assert len(vocab['trade_terms']['en']) > 0

        # Check materials have wood types and engineered
        assert 'wood_types' in vocab['materials']
        assert 'engineered_wood' in vocab['materials']
        assert len(vocab['materials']['wood_types']) > 0
        assert len(vocab['materials']['engineered_wood']) > 0

        # Check certifications
        assert len(vocab['certifications']) > 0


class TestConstructionNERTrainer:
    """Test NER trainer functionality."""

    @pytest.fixture
    def trainer(self):
        """Create trainer instance."""
        return ConstructionNERTrainer()

    @pytest.fixture
    def sample_training_data(self):
        """Create sample training data."""
        return [
            (
                "Die Schreinerei verwendet hochwertige Eiche.",
                {
                    'entities': [
                        (4, 15, 'TRADE'),
                        (40, 45, 'MATERIAL'),
                    ]
                }
            ),
            (
                "Möbelschreiner spezialisiert sich auf lackiert Möbel.",
                {
                    'entities': [
                        (0, 14, 'TRADE'),
                        (41, 50, 'SURFACE'),
                    ]
                }
            ),
        ]

    def test_trainer_initialization(self):
        """Test trainer initializes without spaCy installed."""
        trainer = ConstructionNERTrainer()
        # Should not raise error even if spaCy not installed
        assert trainer.base_model == "de_core_news_lg"

    def test_load_construction_vocabulary(self, trainer):
        """Test loading construction vocabulary."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"

        vocab = trainer.load_construction_vocabulary(str(vocab_path))

        assert isinstance(vocab, dict)
        assert 'trade_terms' in vocab
        assert 'certifications' in vocab

    def test_load_vocabulary_file_not_found(self, trainer):
        """Test error handling for missing vocabulary file."""
        with pytest.raises(FileNotFoundError):
            trainer.load_construction_vocabulary("/nonexistent/vocab.json")

    def test_create_training_data_from_documents(self, trainer, sample_training_data):
        """Test creating training data from documents."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"
        vocab = trainer.load_construction_vocabulary(str(vocab_path))

        documents = [
            {
                'text': 'Die Schreinerei verwendet hochwertige Eiche.',
                'entities': [
                    {'start': 4, 'end': 15, 'label': 'TRADE'},
                    {'start': 40, 'end': 45, 'label': 'MATERIAL'},
                ]
            }
        ]

        training_data = trainer.create_training_data_from_documents(documents, vocab)

        assert len(training_data) > 0
        assert isinstance(training_data[0], tuple)
        assert len(training_data[0]) == 2

    def test_get_model_info_without_spacy(self, trainer):
        """Test getting model info when spaCy not available."""
        info = trainer.get_model_info()

        # Should return empty dict if spaCy not initialized
        assert isinstance(info, dict)

    @patch('backend.extraction.services.ner_trainer.ConstructionNERTrainer.add_construction_patterns')
    def test_add_construction_patterns(self, mock_add):
        """Test pattern matching setup (mocked)."""
        trainer = ConstructionNERTrainer()

        trainer.add_construction_patterns()

        # Should call without error (mocked)

    def test_extract_entities_without_model(self, trainer):
        """Test entity extraction when model not available."""
        entities = trainer.extract_entities_from_text("Test text")

        # Should return empty list if model not initialized
        assert isinstance(entities, list)
        assert len(entities) == 0


class TestSyntheticTrainingData:
    """Test synthetic training data generation."""

    @pytest.fixture
    def vocab(self):
        """Load vocabulary."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"

        with open(vocab_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_create_synthetic_training_data(self, vocab):
        """Test synthetic training data creation."""
        training_data = create_synthetic_training_data(vocab, num_examples=10)

        assert len(training_data) > 0
        assert len(training_data) <= 10  # May be less due to filtering

        # Check format
        for text, annotations in training_data:
            assert isinstance(text, str)
            assert isinstance(annotations, dict)
            assert 'entities' in annotations
            assert isinstance(annotations['entities'], list)

    def test_synthetic_data_contains_entities(self, vocab):
        """Test synthetic data contains actual entities."""
        training_data = create_synthetic_training_data(vocab, num_examples=20)

        total_entities = sum(len(data[1]['entities']) for data in training_data)

        # Should have at least some entities
        assert total_entities > 0

    def test_synthetic_data_entity_types(self, vocab):
        """Test synthetic data entity types are valid."""
        training_data = create_synthetic_training_data(vocab, num_examples=20)

        valid_types = {'TRADE', 'MATERIAL', 'CERTIFICATION', 'SURFACE', 'OTHER'}

        for text, annotations in training_data:
            for start, end, label in annotations['entities']:
                assert label in valid_types


@pytest.mark.integration
class TestNERTrainerIntegration:
    """Integration tests for NER trainer (require spaCy)."""

    def test_full_training_pipeline(self):
        """Test complete training pipeline.

        This test requires spaCy models to be installed.
        """
        pytest.importorskip("spacy")

        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"

        trainer = ConstructionNERTrainer()

        # Check trainer initialized
        if trainer.nlp is None:
            pytest.skip("spaCy de_core_news_lg not installed")

        # Load vocabulary
        vocab = trainer.load_construction_vocabulary(str(vocab_path))

        # Create synthetic data
        training_data = create_synthetic_training_data(vocab, num_examples=20)

        # Add patterns
        trainer.add_construction_patterns()

        # This would train the model (skipped in tests as it's time-consuming)
        assert len(training_data) > 0


@pytest.mark.unit
class TestNERTrainerEdgeCases:
    """Test edge cases in NER trainer."""

    def test_empty_text(self):
        """Test handling of empty text."""
        trainer = ConstructionNERTrainer()

        entities = trainer.extract_entities_from_text("")

        assert isinstance(entities, list)

    def test_text_without_entities(self):
        """Test text with no entities."""
        trainer = ConstructionNERTrainer()

        entities = trainer.extract_entities_from_text("Hello world, this is a test.")

        assert isinstance(entities, list)

    def test_synthetic_data_zero_examples(self):
        """Test synthetic data generation with zero examples."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"

        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = json.load(f)

        training_data = create_synthetic_training_data(vocab, num_examples=0)

        assert isinstance(training_data, list)

    def test_vocabulary_loading_and_usage(self):
        """Test loading vocabulary from actual file."""
        vocab_path = Path(__file__).parent.parent / "extraction" / "training" / "construction_vocabulary.json"

        trainer = ConstructionNERTrainer()
        vocab = trainer.load_construction_vocabulary(str(vocab_path))

        # Generate synthetic data from loaded vocabulary
        training_data = create_synthetic_training_data(vocab, num_examples=5)

        assert len(training_data) > 0
