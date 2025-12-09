# DraftCraft API - Quick Reference Guide

**Version:** 1.0.0 (Phase 4D)
**Base URL:** `http://localhost:8000/api/v1/` (Development)
**Authentication:** Token-based (`Authorization: Token <token>`)

---

## 🔐 Authentication

### Get API Token

```bash
POST /api/auth/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

# Response
{
  "token": "abc123def456..."
}
```

### Use Token in Requests

```bash
curl -H "Authorization: Token abc123def456..." \
     http://localhost:8000/api/v1/config/holzarten/
```

---

## 💰 Pricing & Calculation Endpoints

### Calculate Project Price

```bash
POST /api/v1/calculate/price/
Authorization: Token <token>
Content-Type: application/json

{
  "extracted_data": {
    "holzart": "eiche",
    "oberflaeche": "lackieren",
    "komplexitaet": "hand_geschnitzt",
    "material_sku": "EICHE-25MM",
    "material_quantity": 10,
    "labor_hours": 40,
    "distanz_km": 25
  },
  "customer_type": "bestehende_kunden",
  "breakdown": true
}

# Response: PriceCalculationResponseSerializer
{
  "total_price_eur": 4850.00,
  "base_price_eur": 1000.00,
  "material_price_eur": 1950.00,
  "labor_price_eur": 2800.00,
  "pauschalen": {
    "pauschalen": [...],
    "total": 50.00
  },
  "breakdown": { /* 8-step details */ },
  "tiers_applied": {
    "tier_1_global": true,
    "tier_2_company": true,
    "tier_3_dynamic": true
  }
}
```

### Multi-Material Calculation

```bash
POST /api/v1/calculate/multi-material/
Authorization: Token <token>

{
  "materials": [
    {
      "holzart": "eiche",
      "oberflaeche": "lackieren",
      "laenge_mm": 2000,
      "breite_mm": 800,
      "hoehe_mm": 25,
      "menge": 4
    },
    {
      "holzart": "buche",
      "oberflaeche": "oelen",
      "laenge_mm": 1500,
      "breite_mm": 600,
      "hoehe_mm": 18,
      "menge": 8
    }
  ],
  "customer_type": "bestehende_kunden"
}
```

### Get Applicable Pauschalen

```bash
GET /api/v1/pauschalen/applicable/?auftragswert=5000&distanz_km=30
Authorization: Token <token>

# Response
[
  {
    "regel_id": "uuid",
    "name": "Anfahrt Standard",
    "pauschale_typ": "anfahrt",
    "berechnungsart": "fest",
    "betrag_eur": 50.00,
    "applies": true,
    "calculated_amount_eur": 50.00,
    "reason": "Fester Betrag"
  },
  ...
]
```

---

## ⚙️ Configuration Endpoints

### Get Wood Types (TIER 1)

```bash
GET /api/v1/config/holzarten/
Authorization: Token <token>

# Response
[
  {
    "id": 1,
    "holzart": "eiche",
    "display_name": "Eiche",
    "preis_faktor": 1.30,
    "kategorie": "hartholz",
    "beschreibung": "Premium hardwood",
    "is_enabled": true
  },
  ...
]
```

### Get Surface Finishes (TIER 1)

```bash
GET /api/v1/config/oberflaechen/
Authorization: Token <token>
```

### Get Complexity Techniques (TIER 1)

```bash
GET /api/v1/config/komplexitaet/
Authorization: Token <token>
```

### Get Company Metrics (TIER 2)

```bash
GET /api/v1/config/betriebskennzahlen/
Authorization: Token <token>

# Response
{
  "id": "uuid",
  "template_name": "Schreiner Standard v2.0",
  "stundensatz_arbeit": 65.00,
  "gewinnmarge_prozent": 20.00,
  "betriebskosten_umlage": 500.00,
  "use_handwerk_standard": true,
  "use_custom_materials": true,
  "use_seasonal_adjustments": false,
  "use_customer_discounts": true,
  "is_active": true
}
```

### Update Company Metrics (TIER 2)

```bash
PATCH /api/v1/config/betriebskennzahlen/update_config/
Authorization: Token <token>
Content-Type: application/json

{
  "stundensatz_arbeit": 75.00,
  "gewinnmarge_prozent": 25.0,
  "use_seasonal_adjustments": true
}

# Response: Updated config
```

---

## 🔍 Pattern Analysis Endpoints

### List Extraction Failure Patterns

```bash
GET /api/v1/patterns/failures/
GET /api/v1/patterns/failures/?severity=CRITICAL
GET /api/v1/patterns/failures/?is_reviewed=false
GET /api/v1/patterns/failures/?field_name=amount

Authorization: Token <token>

# Response
[
  {
    "id": "uuid",
    "field_name": "amount",
    "pattern_type": "low_confidence",
    "root_cause": "German currency format not recognized",
    "severity": "HIGH",
    "severity_display": "High - Important to fix",
    "confidence_threshold": 0.65,
    "affected_document_count": 23,
    "total_occurrences": 45,
    "suggested_fix": "Add regex pattern for German decimals",
    "is_reviewed": false,
    "resolution_status": "Not Started"
  },
  ...
]
```

### Get Pattern Details

```bash
GET /api/v1/patterns/failures/{pattern_id}/
Authorization: Token <token>

# Includes review_sessions
```

### Approve Pattern Fix (Admin Only)

```bash
POST /api/v1/patterns/{pattern_id}/approve-fix/
Authorization: Token <admin-token>
Content-Type: application/json

{
  "review_title": "Fix low-confidence amount extraction",
  "description": "Apply regex pattern for German currency formats",
  "estimated_impact": "high",
  "estimated_documents_improved": 45,
  "scheduled_deployment": "2025-12-15T10:00:00Z"
}

# Response
{
  "success": true,
  "message": "Pattern-Fix erfolgreich genehmigt",
  "review_session_id": "uuid"
}
```

### Bulk Pattern Actions (Admin Only)

```bash
POST /api/v1/patterns/bulk-action/
Authorization: Token <admin-token>

{
  "pattern_ids": ["uuid1", "uuid2"],
  "action": "mark_reviewed",
  "admin_notes": "Reviewed batch #1"
}

# Actions: mark_reviewed, mark_inactive, mark_active, set_severity
```

---

## 📊 Transparency & Explanation Endpoints

### Get Calculation Explanations

```bash
GET /api/v1/calculations/explanations/
GET /api/v1/calculations/explanations/{explanation_id}/
Authorization: Token <token>

# Response
{
  "id": "uuid",
  "zusammenfassung": "Preisberechnung basiert auf...",
  "detaillierte_erklarung": "Der Preis setzt sich wie folgt zusammen...",
  "faktoren": [
    {
      "faktor_name": "Holzart",
      "faktor_wert": 1.30,
      "beschreibung": "Eiche ist ein Premium-Hartholz",
      "auswirkung_prozent": 30.0
    },
    ...
  ],
  "tier_breakdown": {...},
  "preisvergleich_benchmark": {...}
}
```

### Get User Benchmarks

```bash
GET /api/v1/benchmarks/user/
Authorization: Token <token>

# Response
[
  {
    "projekttyp": "schrank",
    "durchschnittspreis_eur": 3800.00,
    "median_preis_eur": 3500.00,
    "min_preis_eur": 2000.00,
    "max_preis_eur": 6500.00,
    "anzahl_projekte": 15,
    "letztes_projekt_datum": "2025-11-20"
  },
  ...
]
```

### Submit Calculation Feedback

```bash
POST /api/v1/feedback/calculation/
Authorization: Token <token>

{
  "extraction_result_id": "uuid",
  "feedback_type": "zu_hoch",
  "erwarteter_preis_eur": 3500.00,
  "kommentare": "Preis scheint 20% zu hoch für diese Komplexität"
}

# Feedback types: zu_hoch, zu_niedrig, genau_richtig, faktor_fehlt, faktor_falsch
```

### Compare with Benchmark

```bash
GET /api/v1/calculations/{extraction_result_id}/compare-benchmark/
Authorization: Token <token>

# Response
{
  "current_price_eur": 4500.00,
  "benchmark_avg_eur": 3800.00,
  "difference_eur": 700.00,
  "difference_percent": 18.4,
  "is_above_average": true,
  "explanation": "Ihr Preis liegt 18% über dem Durchschnitt...",
  "factors_causing_difference": [...]
}
```

---

## 📄 Document Processing Endpoints (Existing)

### Upload Document

```bash
POST /api/v1/documents/
Authorization: Token <token>
Content-Type: multipart/form-data

file: <file>
```

### Process Document (OCR + NER)

```bash
POST /api/v1/documents/{document_id}/process/
Authorization: Token <token>

# Triggers OCR → NER → ExtractionResult creation
```

### Get Document Details

```bash
GET /api/v1/documents/{document_id}/
Authorization: Token <token>
```

### Get Extraction Summary

```bash
GET /api/v1/documents/{document_id}/extraction_summary/
Authorization: Token <token>
```

---

## 🛠️ Development Tools

### OpenAPI Schema

```bash
# JSON Schema
GET /api/schema/

# Swagger UI (Interactive)
http://localhost:8000/api/docs/swagger/

# ReDoc UI (Documentation)
http://localhost:8000/api/docs/redoc/
```

### Health Checks

```bash
GET /api/v1/health/
GET /api/v1/health/ready/
GET /api/v1/health/startup/
GET /api/v1/health/ocr/
```

---

## 🔑 Common Query Parameters

### Filtering

```bash
?severity=CRITICAL
?is_reviewed=true
?field_name=amount
?document_id=uuid
```

### Pagination

```bash
?page=2
?page_size=50  # Max 100
```

### Ordering

```bash
?ordering=-created_at  # Descending
?ordering=severity     # Ascending
```

---

## 🚨 Error Responses

### Standard Error Format

```json
{
  "detail": "Human-readable error message in German",
  "error_code": "machine_readable_code"
}
```

### Common Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `not_found` | 404 | Resource not found |
| `permission_denied` | 403 | Insufficient permissions |
| `validation_error` | 400 | Invalid request data |
| `calculation_error` | 400 | Calculation failed |
| `no_configuration` | 404 | User has no Betriebskennzahl |
| `internal_error` | 500 | Server error |

### Example Errors

```json
// Missing required field
{
  "extracted_data": {
    "holzart": ["Dieses Feld ist erforderlich."]
  }
}

// Permission denied
{
  "detail": "Sie müssen der Eigentümer dieser Ressource sein.",
  "error_code": "permission_denied"
}

// Calculation error
{
  "detail": "User hat keine Betriebskennzahl konfiguriert.",
  "error_code": "no_configuration"
}
```

---

## 📋 Complete Endpoint List

### Pricing
- `POST /calculate/price/`
- `POST /calculate/multi-material/`
- `GET /pauschalen/applicable/`

### Configuration
- `GET /config/holzarten/`
- `GET /config/oberflaechen/`
- `GET /config/komplexitaet/`
- `GET /config/betriebskennzahlen/`
- `PATCH /config/betriebskennzahlen/update_config/`

### Pattern Analysis
- `GET /patterns/failures/`
- `GET /patterns/failures/{id}/`
- `POST /patterns/{id}/approve-fix/`
- `POST /patterns/bulk-action/`

### Transparency
- `GET /calculations/explanations/`
- `GET /calculations/explanations/{id}/`
- `GET /benchmarks/user/`
- `POST /feedback/calculation/`
- `GET /calculations/{id}/compare-benchmark/`

### Documents (Existing)
- `POST /documents/`
- `GET /documents/`
- `GET /documents/{id}/`
- `POST /documents/{id}/process/`
- `GET /documents/{id}/extraction_summary/`

---

## 💡 Tips & Best Practices

### 1. Always Include Breakdown

```python
# Get detailed calculation steps for transparency
{
  "extracted_data": {...},
  "breakdown": true  # Include this!
}
```

### 2. Use extraction_result_id for Pauschalen

```python
# Link calculation to ExtractionResult for automatic Pauschalen
{
  "extracted_data": {...},
  "extraction_result_id": "uuid"  # Enables context-aware Pauschalen
}
```

### 3. Query Applicable Pauschalen Before Calculation

```python
# Preview what expenses will be applied
GET /pauschalen/applicable/?auftragswert=5000&distanz_km=30
```

### 4. Handle Missing Config Gracefully

```python
# Check if user has config before calculation
GET /config/betriebskennzahlen/

# If 404, guide user to configure first
```

### 5. Use Filters to Reduce Payload

```python
# Don't fetch all patterns at once
GET /patterns/failures/?severity=CRITICAL&is_reviewed=false
```

---

## 🔄 Typical Workflow

### Complete Pricing Workflow

```python
# 1. Upload document
POST /documents/
→ {document_id}

# 2. Process document (OCR + NER)
POST /documents/{document_id}/process/
→ {extraction_result_id, extracted_data}

# 3. Calculate price
POST /calculate/price/
{
  "extracted_data": <from step 2>,
  "extraction_result_id": <from step 2>,
  "customer_type": "bestehende_kunden",
  "breakdown": true
}
→ {total_price_eur, breakdown, pauschalen}

# 4. Get explanation
GET /calculations/explanations/?extraction_result_id=<step 2>
→ {zusammenfassung, detaillierte_erklarung}

# 5. Compare with benchmark
GET /calculations/{extraction_result_id}/compare-benchmark/
→ {difference_percent, explanation}

# 6. Submit feedback (optional)
POST /feedback/calculation/
{
  "extraction_result_id": <step 2>,
  "feedback_type": "genau_richtig"
}
```

---

**For full API documentation, visit:** `http://localhost:8000/api/docs/swagger/`

**Last Updated:** 2025-12-07
