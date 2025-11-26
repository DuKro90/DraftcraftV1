"""German Named Entity Recognition service using spaCy."""
import logging
from typing import Dict, List, Any, Tuple

from .base_service import BaseExtractionService, ExtractionServiceError
from ..models import ExtractedEntity
from documents.models import Document

logger = logging.getLogger(__name__)


class GermanNERService(BaseExtractionService):
    """Named Entity Recognition service for German text using spaCy."""

    def __init__(self, config: Dict[str, Any], timeout_seconds: int = 300):
        """Initialize NER service.

        Args:
            config: Configuration dictionary with ner_* settings
            timeout_seconds: Maximum processing time
        """
        super().__init__(config, timeout_seconds)
        self.nlp = None
        self._initialize()

    def _initialize(self):
        """Initialize spaCy model."""
        try:
            import spacy

            model_name = self.config.get('ner_model', 'de_core_news_lg')
            self.nlp = spacy.load(model_name)
            logger.info(f"GermanNERService initialized with {model_name}")
        except ImportError:
            logger.warning(
                "spaCy not installed. "
                "Install with: pip install spacy"
            )
            self.nlp = None
        except OSError:
            logger.warning(
                f"spaCy model not found. Install with: "
                f"python -m spacy download {self.config.get('ner_model')}"
            )
            self.nlp = None

    def process(self, text: str, document: Document = None) -> Dict[str, Any]:
        """Extract named entities from text.

        Args:
            text: Text to process
            document: Optional Document instance to link entities

        Returns:
            Dictionary with:
                - entities: List of extracted entities
                - summary: Entity counts by type
                - confidence: Average confidence
                - processing_time_ms: Processing time

        Raises:
            ExtractionServiceError: If processing fails
        """
        if not text or not text.strip():
            raise ExtractionServiceError("Empty text provided")

        if not self.nlp:
            raise ExtractionServiceError(
                "spaCy model not available. "
                "Install with: python -m spacy download de_core_news_lg"
            )

        try:
            entities, processing_time_ms = self._measure_time(
                self._extract_entities,
                text
            )

            summary = self._count_entities(entities)

            result = {
                'entities': entities,
                'summary': summary,
                'confidence': self._calculate_confidence(entities),
                'processing_time_ms': processing_time_ms,
            }

            # Save to database if document provided
            if document:
                self._save_entities(document, entities)

            return result

        except Exception as e:
            raise ExtractionServiceError(f"NER processing failed: {str(e)}")

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text.

        Args:
            text: Text to process

        Returns:
            List of entity dictionaries
        """
        doc = self.nlp(text)
        entities = []

        confidence_threshold = self.config.get('ner_confidence_threshold', 0.7)

        for ent in doc.ents:
            # Map spaCy entity types to our types
            entity_type = self._map_entity_type(ent.label_)

            entities.append({
                'text': ent.text,
                'type': entity_type,
                'spacy_label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': self._estimate_confidence(ent),
            })

        # Filter by confidence threshold
        entities = [
            e for e in entities
            if e['confidence'] >= confidence_threshold
        ]

        return entities

    def _map_entity_type(self, spacy_label: str) -> str:
        """Map spaCy label to our entity types.

        Args:
            spacy_label: spaCy entity label

        Returns:
            Our entity type
        """
        mapping = {
            'PER': 'PERSON',
            'ORG': 'ORGANIZATION',
            'LOC': 'LOCATION',
            'DATE': 'DATE',
            'MONEY': 'PRICE',
            'PERCENT': 'QUANTITY',
            'QUANTITY': 'QUANTITY',
        }
        return mapping.get(spacy_label, 'OTHER')

    def _estimate_confidence(self, ent) -> float:
        """Estimate confidence for entity.

        Args:
            ent: spaCy entity

        Returns:
            Confidence score 0-1
        """
        # spaCy doesn't provide direct confidence scores
        # We estimate based on entity type and text length
        base_confidence = 0.8
        length_factor = min(len(ent.text) / 50, 1.0)
        return base_confidence + (length_factor * 0.2)

    def _count_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count entities by type.

        Args:
            entities: List of entities

        Returns:
            Count by entity type
        """
        counts = {}
        for ent in entities:
            entity_type = ent['type']
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts

    def _calculate_confidence(self, entities: List[Dict[str, Any]]) -> float:
        """Calculate average confidence.

        Args:
            entities: List of entities

        Returns:
            Average confidence 0-1
        """
        if not entities:
            return 0.0

        total_confidence = sum(e['confidence'] for e in entities)
        return total_confidence / len(entities)

    def _save_entities(
        self,
        document: Document,
        entities: List[Dict[str, Any]]
    ) -> None:
        """Save extracted entities to database.

        Args:
            document: Document instance
            entities: List of extracted entities
        """
        for ent_data in entities:
            ExtractedEntity.objects.create(
                document=document,
                entity_type=ent_data['type'],
                text=ent_data['text'],
                start_offset=ent_data['start'],
                end_offset=ent_data['end'],
                confidence_score=ent_data['confidence'],
                metadata={
                    'spacy_label': ent_data['spacy_label'],
                },
            )
        logger.info(
            f"Saved {len(entities)} entities for document {document.id}"
        )
