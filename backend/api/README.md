# API Module

REST API layer with Django REST Framework.

## Status: Phase 2.5 ✅

Complete REST API with document processing, extraction results, and async tasks.

## Authentication

**Token-based authentication:**
```bash
# Get token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/documents/
```

## Endpoints

### Documents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/documents/` | GET | List user's documents |
| `/api/v1/documents/` | POST | Upload new document |
| `/api/v1/documents/{id}/` | GET | Get document details |
| `/api/v1/documents/{id}/` | PUT | Update document |
| `/api/v1/documents/{id}/` | DELETE | Delete document (DSGVO) |
| `/api/v1/documents/{id}/process/` | POST | Trigger OCR/NER extraction |
| `/api/v1/documents/{id}/extraction_summary/` | GET | Get extraction results |
| `/api/v1/documents/{id}/audit_logs/` | GET | Get audit trail |

### Entities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/entities/` | GET | List extracted entities |
| `/api/v1/entities/?document_id={id}` | GET | Filter by document |
| `/api/v1/entities/?entity_type=MATERIAL` | GET | Filter by type |

### Materials

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/materials/` | GET | List material extractions |

### Configuration

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/extraction-config/` | GET | List configs | Admin |
| `/api/v1/extraction-config/` | POST | Create config | Admin |
| `/api/v1/extraction-config/{id}/` | PUT | Update config | Admin |

### Documentation

| Endpoint | Description |
|----------|-------------|
| `/api/docs/swagger/` | OpenAPI Swagger UI |
| `/api/docs/redoc/` | ReDoc documentation |
| `/api/schema/` | OpenAPI schema |

## Request/Response Examples

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@invoice.pdf"

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "invoice.pdf",
  "status": "uploaded",
  "file_size_display": "1.23 MB",
  "created_at": "2025-11-26T12:00:00Z"
}
```

### Process Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/{id}/process/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "extraction_result": {
    "ocr_text": "...",
    "confidence": 0.89,
    "extracted_data": {...}
  }
}
```

## Architecture

```
api/v1/
├── __init__.py
├── views.py          # ViewSets for documents, entities, materials
├── serializers.py    # DRF serializers (in documents/, extraction/)
└── urls.py           # Router configuration
```

### ViewSets

- **DocumentViewSet** - Full CRUD + custom actions (process, extraction_summary, audit_logs)
- **ExtractedEntityViewSet** - Read-only with filtering (document_id, entity_type)
- **MaterialExtractionViewSet** - Read-only
- **ExtractionConfigViewSet** - Admin only (CRUD)

### Serializers

- **DocumentUploadSerializer** - File upload validation
- **DocumentListSerializer** - Minimal fields for lists
- **DocumentDetailSerializer** - Full document with extraction results
- **ExtractedEntitySerializer** - Entity data with confidence
- **MaterialExtractionSerializer** - Material specs
- **ExtractionConfigSerializer** - Service configuration
- **ExtractionSummarySerializer** - Extraction results summary

## Features

✅ **Token Authentication** - Secure API access
✅ **User Isolation** - Users only see their own documents
✅ **Pagination** - Automatic for list endpoints
✅ **Filtering** - By document_id, entity_type, etc.
✅ **Async Processing** - Celery tasks for long-running operations
✅ **Audit Logging** - DSGVO-compliant access tracking
✅ **Error Handling** - Proper HTTP status codes
✅ **OpenAPI Schema** - Swagger + ReDoc documentation

## Tests

```bash
# All API tests
pytest tests/test_api_views.py -v

# Specific test class
pytest tests/test_api_views.py::TestDocumentAPI -v

# With coverage
pytest tests/test_api_views.py --cov=api --cov-report=html
```

## Usage with Async Tasks

### Sync Processing (Blocking)
```python
response = client.post(f'/api/v1/documents/{doc_id}/process/')
# Wait for response (max timeout)
```

### Async Processing (Background Job)
```python
# Future: Trigger async task
response = client.post(f'/api/v1/documents/{doc_id}/process_async/')
# Immediate response with task_id
# Poll /api/v1/documents/{doc_id}/task_status/
```
