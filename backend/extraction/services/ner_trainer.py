"""NER trainer for fine-tuning German construction models."""
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class ConstructionNERTrainer:
    """Fine-tune spaCy model on German construction terminology."""

    def __init__(self, base_model: str = "de_core_news_lg"):
        """Initialize NER trainer.

        Args:
            base_model: Base spaCy model to fine-tune (default: de_core_news_lg)
        """
        self.base_model = base_model
        self.nlp = None
        self.training_data = []
        self._initialize()

    def _initialize(self):
        """Initialize spaCy model."""
        try:
            import spacy
            self.nlp = spacy.load(self.base_model)
            logger.info(f"Loaded base model: {self.base_model}")
        except OSError:
            logger.error(
                f"Model '{self.base_model}' not found. "
                "Install with: python -m spacy download de_core_news_lg"
            )
            self.nlp = None

    def load_construction_vocabulary(self, vocab_path: str) -> Dict[str, Any]:
        """Load construction vocabulary from JSON.

        Args:
            vocab_path: Path to construction_vocabulary.json

        Returns:
            Dictionary with vocabulary data
        """
        try:
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab = json.load(f)
            logger.info(f"Loaded construction vocabulary from {vocab_path}")
            return vocab
        except FileNotFoundError:
            logger.error(f"Vocabulary file not found: {vocab_path}")
            raise

    def create_training_data_from_documents(
        self,
        documents: List[Dict[str, str]],
        vocab: Dict[str, Any]
    ) -> List[Tuple[str, Dict]]:
        """Create spaCy training data from documents.

        Args:
            documents: List of dicts with 'text' and 'entities' keys
            vocab: Construction vocabulary

        Returns:
            List of (text, entities) tuples in spaCy format
        """
        training_data = []

        for doc in documents:
            text = doc.get('text', '')
            entities = doc.get('entities', [])

            # Convert to spaCy format: (text, {'entities': [(start, end, label), ...]})
            ents_dict = {'entities': []}

            for ent in entities:
                start = ent.get('start')
                end = ent.get('end')
                label = ent.get('label')

                if start is not None and end is not None and label:
                    ents_dict['entities'].append((start, end, label))

            if ents_dict['entities']:
                training_data.append((text, ents_dict))

        logger.info(f"Created {len(training_data)} training examples")
        return training_data

    def add_construction_patterns(self) -> None:
        """Add PhraseMatcher for construction terms.

        This adds pattern matching for exact construction terminology,
        which helps the NER model recognize domain-specific terms.
        """
        if not self.nlp:
            logger.warning("spaCy model not initialized, skipping pattern matching")
            return

        try:
            from spacy.matcher import PhraseMatcher

            matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

            # Load vocabulary
            vocab_path = Path(__file__).parent.parent / "training" / "construction_vocabulary.json"
            vocab = self.load_construction_vocabulary(str(vocab_path))

            # Add patterns for different entity types
            trade_patterns = [self.nlp.make_doc(text) for text in vocab['trade_terms']['de']]
            matcher.add("TRADE", trade_patterns)

            cert_patterns = [self.nlp.make_doc(text) for text in vocab['certifications']]
            matcher.add("CERTIFICATION", cert_patterns)

            wood_patterns = [self.nlp.make_doc(text) for text in vocab['materials']['wood_types']]
            matcher.add("MATERIAL", wood_patterns)

            upholstery_patterns = [
                self.nlp.make_doc(text) for text in vocab['surfaces']['upholstery_materials']
            ]
            matcher.add("SURFACE", upholstery_patterns)

            # Add pipe component
            if "phrase_matcher" not in self.nlp.pipe_names:
                self.nlp.add_pipe("phrase_matcher", before="ner")
            else:
                self.nlp.get_pipe("phrase_matcher").matcher = matcher

            logger.info("Added construction pattern matching to NER pipeline")

        except Exception as e:
            logger.warning(f"Failed to add pattern matching: {str(e)}")

    def train_model(
        self,
        training_data: List[Tuple[str, Dict]],
        iterations: int = 30,
        drop: float = 0.5
    ) -> Optional[Any]:
        """Train the NER model on construction terminology.

        Args:
            training_data: List of (text, {'entities': [(start, end, label), ...]})
            iterations: Number of training iterations
            drop: Dropout rate for regularization

        Returns:
            Trained spaCy model, or None if training failed
        """
        if not self.nlp:
            logger.error("spaCy model not initialized")
            return None

        try:
            from spacy.training import Example

            # Get NER pipeline component
            ner = self.nlp.get_pipe("ner")

            # Add labels to the NER model
            labels = {'TRADE', 'CERTIFICATION', 'MATERIAL', 'QUANTITY', 'PRICE', 'SURFACE', 'DATE', 'LOCATION'}
            for label in labels:
                ner.add_label(label)

            # Training loop
            logger.info(f"Starting NER training for {iterations} iterations...")

            optimizer = self.nlp.create_optimizer()

            for iteration in range(iterations):
                random.shuffle(training_data)
                losses = {}

                for text, annotations in training_data:
                    try:
                        doc = self.nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        self.nlp.update(
                            [example],
                            drop=drop,
                            sgd=optimizer,
                            losses=losses
                        )
                    except Exception as e:
                        logger.debug(f"Error training example: {str(e)}")
                        continue

                if (iteration + 1) % 10 == 0:
                    logger.info(
                        f"Iteration {iteration + 1}/{iterations}, Loss: {losses.get('ner', 0):.4f}"
                    )

            logger.info("NER training completed successfully")
            return self.nlp

        except ImportError:
            logger.error("spacy.training not available")
            return None
        except Exception as e:
            logger.error(f"NER training failed: {str(e)}")
            return None

    def evaluate_model(
        self,
        test_data: List[Tuple[str, Dict]]
    ) -> Dict[str, float]:
        """Evaluate model performance on test data.

        Args:
            test_data: List of (text, {'entities': [(start, end, label), ...]})

        Returns:
            Dictionary with precision, recall, F1 scores per entity type
        """
        if not self.nlp:
            logger.error("spaCy model not initialized")
            return {}

        try:
            from spacy.training import Example
            from spacy.scorer import Scorer

            scorer = Scorer()
            examples = []

            for text, annotations in test_data:
                doc = self.nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)

            # Score examples
            scores = scorer.score_ents(examples)

            logger.info(f"Evaluation results: {scores}")
            return scores

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return {}

    def save_model(self, output_path: str) -> bool:
        """Save fine-tuned model to disk.

        Args:
            output_path: Path to save model

        Returns:
            True if successful, False otherwise
        """
        if not self.nlp:
            logger.error("spaCy model not initialized")
            return False

        try:
            self.nlp.to_disk(output_path)
            logger.info(f"Model saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
            return False

    def load_model(self, model_path: str) -> bool:
        """Load fine-tuned model from disk.

        Args:
            model_path: Path to model directory

        Returns:
            True if successful, False otherwise
        """
        try:
            import spacy
            self.nlp = spacy.load(model_path)
            logger.info(f"Model loaded from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False

    def extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using the trained model.

        Args:
            text: Text to extract entities from

        Returns:
            List of extracted entities with type and confidence
        """
        if not self.nlp:
            logger.error("spaCy model not initialized")
            return []

        try:
            doc = self.nlp(text)

            entities = []
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                })

            logger.debug(f"Extracted {len(entities)} entities from text")
            return entities

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return []

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model.

        Returns:
            Dictionary with model metadata
        """
        if not self.nlp:
            return {}

        try:
            ner = self.nlp.get_pipe("ner")
            labels = ner.labels

            return {
                'model': self.nlp.meta.get('name'),
                'version': self.nlp.meta.get('version'),
                'components': self.nlp.pipe_names,
                'ner_labels': labels,
                'vocab_size': len(self.nlp.vocab),
            }
        except Exception as e:
            logger.warning(f"Failed to get model info: {str(e)}")
            return {}


def create_synthetic_training_data(
    vocab: Dict[str, Any],
    num_examples: int = 50
) -> List[Tuple[str, Dict]]:
    """Create synthetic training examples for NER.

    Args:
        vocab: Construction vocabulary
        num_examples: Number of examples to generate

    Returns:
        List of training examples
    """
    training_data = []

    trade_terms = vocab['trade_terms']['de']
    materials = vocab['materials']['wood_types']
    certifications = vocab['certifications']
    finishes = vocab['surfaces']['finishes']

    # Generate synthetic sentences
    templates = [
        "Die {trade} verwenden hochwertiges {material}.",
        "{trade} spezialisiert sich auf {finish} Möbel.",
        "Dieses Projekt erfüllt die {cert} Anforderungen.",
        "Der {material} wurde mit {finish} behandelt.",
        "Unser Angebot: {material} {trade}arbeiten mit {cert}.",
        "Maßanfertigung durch erfahrene {trade}.",
        "{cert} zertifizierte {trade} für höchste Qualität.",
    ]

    for _ in range(num_examples):
        template = random.choice(templates)
        trade = random.choice(trade_terms)
        material = random.choice(materials)
        cert = random.choice(certifications)
        finish = random.choice(finishes)

        text = template.format(
            trade=trade,
            material=material,
            cert=cert,
            finish=finish
        )

        # Create entities
        entities = []

        # Find and mark entities in text
        if trade in text:
            start = text.find(trade)
            end = start + len(trade)
            entities.append((start, end, 'TRADE'))

        if material in text:
            start = text.find(material)
            end = start + len(material)
            entities.append((start, end, 'MATERIAL'))

        if cert in text:
            start = text.find(cert)
            end = start + len(cert)
            entities.append((start, end, 'CERTIFICATION'))

        if finish in text:
            start = text.find(finish)
            end = start + len(finish)
            entities.append((start, end, 'SURFACE'))

        if entities:
            training_data.append((text, {'entities': entities}))

    return training_data
