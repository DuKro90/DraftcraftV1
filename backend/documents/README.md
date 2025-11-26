# Documents Module

Document management, upload, processing, and DSGVO compliance.

## Models

- **Document** - Uploaded file + processing status
- **ExtractionResult** - OCR/NER results
- **AuditLog** - DSGVO audit trail

## Features (Phase 1.5+)

- File upload & storage
- Processing status tracking
- Extraction result storage
- DSGVO compliance logging

## Tests

```bash
pytest tests/test_core_constants.py  # Uses Document model
```
