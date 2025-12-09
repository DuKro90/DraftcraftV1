"""Custom Django admin forms with tooltips for extraction models."""
from django import forms
from .models import ExtractionConfig, ExtractedEntity, MaterialExtraction


class ExtractionConfigAdminForm(forms.ModelForm):
    """Admin form for ExtractionConfig with helpful tooltips."""

    class Meta:
        model = ExtractionConfig
        fields = '__all__'
        help_texts = {
            'name': 'Configuration name (e.g., "Production German OCR", "Development Test Config")',
            'language': 'Primary language for OCR and NER processing (de=German, en=English)',
            'ocr_enabled': 'Enable OCR (Optical Character Recognition) for image/PDF processing',
            'ocr_confidence_threshold': 'Minimum confidence score for OCR results (0.0-1.0, recommended: 0.7)',
            'ocr_use_cuda': 'Use GPU acceleration for OCR (requires CUDA-compatible GPU)',
            'ner_enabled': 'Enable NER (Named Entity Recognition) for extracting structured data',
            'ner_model': 'spaCy model for NER (e.g., "de_core_news_lg" for German)',
            'ner_confidence_threshold': 'Minimum confidence score for NER entities (0.0-1.0, recommended: 0.6)',
            'max_file_size_mb': 'Maximum file size for processing in MB (recommended: 50-100 MB)',
            'timeout_seconds': 'Maximum processing time before timeout (recommended: 300 seconds)',
        }


class ExtractedEntityAdminForm(forms.ModelForm):
    """Admin form for ExtractedEntity with helpful tooltips."""

    class Meta:
        model = ExtractedEntity
        fields = '__all__'
        help_texts = {
            'document': 'Source document from which this entity was extracted',
            'entity_type': 'Type: MATERIAL, QUANTITY, UNIT, PRICE, PERSON, ORGANIZATION, DATE, LOCATION, OTHER',
            'text': 'Extracted text content (e.g., "Eiche massiv", "2.450,80 €")',
            'start_offset': 'Character position where entity starts in document text',
            'end_offset': 'Character position where entity ends in document text',
            'confidence_score': 'NER confidence score (0.0-1.0). Lower scores may need manual review',
            'metadata': 'Additional JSON metadata (e.g., normalized values, alternative interpretations)',
        }


class MaterialExtractionAdminForm(forms.ModelForm):
    """Admin form for MaterialExtraction with helpful tooltips."""

    class Meta:
        model = MaterialExtraction
        fields = '__all__'
        help_texts = {
            'document': 'Source document from which materials were extracted',
            'materials': 'Extracted material names (JSON array, e.g., ["Eiche", "Buche"])',
            'unit': 'Unit of measurement (e.g., "m²", "lfm", "Stk", "kg", "h")',
            'complexity_level': 'Craftsmanship complexity: einfach (simple), mittel (medium), komplex (complex), sehr_komplex (very complex)',
            'surface_finish': 'Surface treatment: naturbelassen, geölt, lackiert, gewachst, gebeizt, klavierlack',
            'dimensions': 'Physical dimensions as JSON (e.g., {"length": 2.5, "width": 0.8, "height": 0.05, "unit": "m"})',
            'additional_features': 'Extra features as JSON (e.g., ["Schublade", "Glastür", "LED-Beleuchtung"])',
            'extraction_confidence': 'Overall extraction quality (0.0-1.0). <0.7 triggers manual review',
            'requires_manual_review': 'Auto-flagged if confidence is low or ambiguous data detected',
            'review_notes': 'Admin notes after manual review (corrections, decisions, observations)',
        }
