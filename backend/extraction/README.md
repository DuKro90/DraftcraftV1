# Extraction Module

OCR & NER text/entity extraction services for German documents.

## Status: Phase 2 ✅

Complete implementation with:

- **GermanOCRService** - PaddleOCR text extraction (PDF, images)
- **GermanNERService** - spaCy named entity recognition
- **ExtractionConfig** - Service configuration model
- **ExtractedEntity** - NER result storage
- **MaterialExtraction** - Manufacturing-specific extraction

## Architecture

```
services/
├── __init__.py
├── base_service.py      # BaseExtractionService ABC
├── ocr_service.py       # GermanOCRService
└── ner_service.py       # GermanNERService
```

Service layer pattern - business logic isolated, models are data only.

## Usage

### OCR Service

```python
from extraction.services import GermanOCRService

config = {'ocr_use_cuda': False, 'max_file_size_mb': 50}
service = GermanOCRService(config)

result = service.process('/path/to/document.pdf')
# Returns: {'text': '...', 'confidence': 0.85, 'lines': [...], 'processing_time_ms': 1234}
```

### NER Service

```python
from extraction.services import GermanNERService
from documents.models import Document

config = {'ner_model': 'de_core_news_lg', 'ner_confidence_threshold': 0.7}
service = GermanNERService(config)

document = Document.objects.first()
result = service.process(ocr_text, document)
# Returns: {'entities': [...], 'summary': {...}, 'confidence': 0.82, 'processing_time_ms': 456}
```

## Models

| Model | Purpose |
|-------|---------|
| **ExtractionConfig** | Service settings & thresholds |
| **ExtractedEntity** | Individual NER results |
| **MaterialExtraction** | Manufacturing specs extraction |

## Tests

```bash
pytest tests/test_extraction_services.py
pytest tests/test_extraction_services.py -m unit
pytest tests/test_extraction_services.py -m integration
```

## Dependencies

- `paddleocr` - OCR (install: `pip install paddleocr`)
- `spacy` - NER (install: `pip install spacy && python -m spacy download de_core_news_lg`)
- `pdf2image` - PDF handling (install: `pip install pdf2image pillow`)
