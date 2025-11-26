# Phase 2: Short-Term Value Delivery
**Duration:** Month 1 (80-100 hours)
**Goal:** High-value features, UX improvements, deployment prep
**Risk Level:** LOW-MEDIUM
**Status:** Planned (Starts after Phase 1 completion)

---

## Overview

Phase 2 focuses on delivering immediate business value through enhanced OCR accuracy, batch processing, and GCP staging deployment. These features directly improve user experience and operational efficiency.

**Total Effort:** 80-100 hours over 4 weeks
**Team:** 1 Backend Dev + 1 DevOps Engineer + 0.5 QA
**Critical Path:** OCR improvements → Batch processing → GCP deployment

---

## 2.1: Enhanced OCR Accuracy (CRITICAL)
**Effort:** 44 hours | **Timeline:** Week 1-2

### 2.1.1: German Construction Vocabulary Training
**Priority:** CRITICAL | **Effort:** 20 hours

**Objective:** Improve NER recognition accuracy from 85% → 92% with custom German construction terminology.

**Key Tasks:**
1. Analyze current NER errors on 100+ documents
2. Create training dataset with German construction terms
3. Fine-tune spaCy model with custom entities:
   - TRADE: Tischler, Schreiner, Tischlermeister
   - CERTIFICATION: DIN, ISO, EN standards
   - MATERIAL: Additional wood species
4. Test on validation set
5. Update extraction service to use custom model

**Files to Create:**
- `backend/extraction/training/german_construction_vocab.json`
- `backend/extraction/training/training_data.json`
- `backend/extraction/models/` (store trained model)

**Success Criteria:**
- NER accuracy ≥ 92% on test set
- TRADE entity recognition ≥ 95%
- CERTIFICATION recognition ≥ 90%
- Processing time increased < 5%

---

### 2.1.2: OCR Preprocessing Pipeline
**Priority:** HIGH | **Effort:** 16 hours

**Objective:** Improve OCR accuracy on poor-quality scans through automatic preprocessing.

**Key Tasks:**
1. Implement image preprocessing:
   - Deskew (rotate to correct angle)
   - Denoise (remove scan artifacts)
   - Contrast enhancement
   - Binarization (black & white)
2. Create preprocessing service
3. Add confidence-based retry logic:
   - If OCR confidence < 0.7, apply preprocessing and retry
4. Test on 50+ low-quality document samples

**Files to Create:**
- `backend/extraction/services/image_preprocessor.py`

**Dependencies:**
- opencv-python==4.8.1.78
- scikit-image==0.22.0
- numpy

**Success Criteria:**
- Preprocessed images improve OCR accuracy by 10-15%
- Processing time < 5 seconds per page
- Automatic fallback works correctly

---

### 2.1.3: Confidence Threshold Tuning
**Priority:** MEDIUM | **Effort:** 8 hours

**Objective:** Optimize confidence thresholds based on actual error analysis.

**Key Tasks:**
1. Analyze confidence scores from 100+ processed documents
2. Calculate false positive/negative rates for each threshold
3. Determine optimal thresholds per entity type
4. Add confidence explanation in API responses
5. Create admin interface to adjust thresholds

**Files to Modify:**
- `backend/extraction/services/ner_service.py`
- `backend/api/v1/serializers.py`

**Success Criteria:**
- Thresholds based on empirical data
- False positive rate < 5%
- Users understand confidence scores in responses

---

## 2.2: Batch Processing (CRITICAL)
**Effort:** 36 hours | **Timeline:** Week 2-3

### 2.2.1: Bulk Upload Endpoint
**Priority:** CRITICAL | **Effort:** 12 hours

**Objective:** Create API endpoint for uploading and processing 50+ documents simultaneously.

**Key Tasks:**
1. Create Batch model in documents/models.py
2. Implement bulk upload endpoint: `POST /api/v1/documents/bulk_upload/`
3. Accept:
   - Multiple file upload (form-data)
   - ZIP archive with documents
   - CSV with metadata
4. Return batch_id for tracking
5. Create batch serializer

**Files to Create:**
- Backend: Update `documents/models.py` (add Batch model)
- Backend: Update `documents/serializers.py`
- Backend: Update `api/v1/views.py` (add bulk endpoint)

**API Example:**
```
POST /api/v1/documents/bulk_upload/
Content-Type: multipart/form-data

file: [doc1.pdf, doc2.pdf, ...]
description: "Q4 2025 project quotes"
```

**Success Criteria:**
- Upload works with 50+ files
- Individual file validation
- Clear error messages for invalid files
- Batch tracking works

---

### 2.2.2: Batch Processing Service
**Priority:** CRITICAL | **Effort:** 16 hours

**Objective:** Process documents in parallel with progress tracking.

**Key Tasks:**
1. Create batch processing service
2. Implement Celery task group for parallel processing
3. Add progress tracking: "5/50 documents processed"
4. Queue management (limit concurrent jobs)
5. Error handling (skip bad files, continue with others)

**Files to Create:**
- `backend/documents/batch_service.py`
- Update `backend/extraction/tasks.py`

**Features:**
- Process up to 50 documents in parallel
- Real-time progress updates
- Automatic retry on temporary failures
- Detailed error reporting per document

**Success Criteria:**
- Processes 50 documents in < 5 minutes
- Progress updates every 5-10 seconds
- 99% of valid documents processed
- Clear error messages for failures

---

### 2.2.3: Batch Status & Results
**Priority:** HIGH | **Effort:** 8 hours

**Objective:** API endpoints for batch status and results retrieval.

**Key Tasks:**
1. Create status endpoint: `GET /api/v1/batches/{id}/status/`
2. Create results endpoint: `GET /api/v1/batches/{id}/results/`
3. Email notification when batch complete
4. CSV export of results
5. Results caching (1 hour)

**API Examples:**
```
GET /api/v1/batches/batch-12345/status/
→ {
    "status": "processing",
    "progress": "23/50",
    "estimated_time_remaining": "5 minutes",
    "errors": 2
  }

GET /api/v1/batches/batch-12345/results/
→ [
    {"document_id": 1, "status": "success"},
    {"document_id": 2, "status": "failed", "error": "..."},
    ...
  ]
```

**Success Criteria:**
- Status updates in real-time
- Results retrievable for 48 hours
- Email notifications working
- CSV export accurate

---

## 2.3: GCP Cloud Run Deployment
**Effort:** 28 hours | **Timeline:** Week 3-4

### 2.3.1: Cloud Run Configuration
**Priority:** CRITICAL | **Effort:** 12 hours

**Objective:** Set up CI/CD pipeline for GCP Cloud Run deployment.

**Key Tasks:**
1. Create `cloudbuild.yaml` for CI/CD
2. Set up Docker image building
3. Configure Secret Manager integration
4. Create Terraform scripts for infrastructure
5. Test build pipeline

**Files to Create:**
- `cloudbuild.yaml`
- `terraform/main.tf`
- `terraform/variables.tf`
- `terraform/outputs.tf`

**CI/CD Steps:**
1. Push to main branch
2. Build Docker image
3. Run tests
4. Deploy to staging
5. Run smoke tests
6. Deploy to production

**Success Criteria:**
- Build completes in < 10 minutes
- All tests pass before deployment
- Deployment to staging/production automated
- Rollback capability works

---

### 2.3.2: Production Readiness Checklist
**Priority:** CRITICAL | **Effort:** 8 hours

**Objective:** Verify all production requirements met.

**Key Tasks:**
1. Create `GCP_DEPLOYMENT_CHECKLIST.md`
2. Verify secrets in Secret Manager:
   - DATABASE_URL
   - SECRET_KEY
   - ALLOWED_HOSTS
   - Email credentials
3. Configure Cloud SQL (PostgreSQL 15)
4. Set up Cloud Storage for documents
5. Enable Cloud Logging
6. Configure error reporting (Sentry)
7. Set up monitoring and alerts

**Files to Create:**
- `GCP_DEPLOYMENT_CHECKLIST.md`
- `docs/GCP_SETUP_GUIDE.md`

**Checklist Items:**
- [ ] Secrets configured in Secret Manager
- [ ] Database connection tested
- [ ] File storage working (Cloud Storage)
- [ ] Logging enabled and working
- [ ] Error tracking (Sentry) active
- [ ] Health checks configured
- [ ] SSL/TLS enabled
- [ ] Rate limiting configured
- [ ] Backups configured
- [ ] Monitoring alerts set up

**Success Criteria:**
- All checklist items completed
- Manual deployment successful
- All health checks passing
- Logs viewable in Cloud Logging

---

### 2.3.3: Staging Environment
**Priority:** HIGH | **Effort:** 8 hours

**Objective:** Deploy to GCP staging for UAT before production.

**Key Tasks:**
1. Create separate GCP project for staging
2. Deploy via Cloud Run with smaller instances (0.5 CPU, 512MB RAM)
3. Use staging database
4. Set up staging DNS (staging-draftcraft.example.com)
5. Configure monitoring for staging
6. Test deployment process

**Success Criteria:**
- Staging environment accessible
- Can upload and process documents
- API responding normally
- Database persisting data
- 24+ hours uptime confirmed
- Ready for UAT with beta users

---

## 2.4: Feature Improvements
**Effort:** 20 hours | **Timeline:** Week 4

### 2.4.1: Advanced Search & Filtering
**Priority:** MEDIUM | **Effort:** 12 hours

**Objective:** Enable users to find documents quickly with advanced filters.

**Key Tasks:**
1. Implement PostgreSQL full-text search
2. Create filter classes for:
   - Date range (created_at)
   - Status (uploaded, processing, processed)
   - Customer name
   - Proposal amount
3. Add search endpoint: `GET /api/v1/documents/search/`
4. Optimize queries with indexes

**Files to Modify:**
- `backend/api/v1/filters.py` (new)
- `backend/api/v1/views.py`
- `backend/documents/models.py`

**Search Example:**
```
GET /api/v1/documents/search/?q=Eiche&date_from=2025-01-01&status=processed
```

**Success Criteria:**
- Search returns results in < 200ms
- All filters work correctly
- Pagination works for large result sets
- Index usage optimized

---

### 2.4.2: Proposal Versioning
**Priority:** LOW | **Effort:** 8 hours

**Objective:** Track proposal changes over time.

**Key Tasks:**
1. Add version field to Proposal model
2. Create ProposalVersion model for history
3. Auto-increment version on each save
4. API endpoint to list versions
5. Ability to view/restore previous versions

**Files to Modify:**
- `backend/proposals/models.py`
- `backend/proposals/serializers.py`
- `backend/api/v1/views.py`

**Success Criteria:**
- Version history tracked
- Can view previous versions
- Can restore previous version
- Audit trail complete

---

## Phase 2 Success Criteria

- [x] OCR accuracy improved by 7+ percentage points (85% → 92%+)
- [x] Batch processing handles 50+ documents reliably
- [x] GCP staging environment deployed successfully
- [x] Search finds documents in < 200ms
- [x] 3-5 beta users onboarded and testing

---

## Phase 2 Timeline

| Week | Focus | Tasks | Hours | Status |
|------|-------|-------|-------|--------|
| 1 | OCR | Vocabulary training | 20 | Ready |
| 2 | OCR + Batch | Preprocessing + bulk upload | 24 | Ready |
| 2-3 | Batch | Processing service | 16 | Ready |
| 3-4 | Deployment | Cloud Run + staging | 28 | Ready |
| 4 | Features | Search + versioning | 20 | Ready |
| | **TOTAL** | | **80-100** | **Ready** |

---

## Phase 2 Dependencies

**Must Complete Phase 1 First:**
- Docker stable ✓
- Health checks working ✓
- Error messages consistent ✓

**External Requirements:**
- GCP project created
- Cloud SQL instance provisioned
- Cloud Storage bucket created
- Secret Manager configured

---

## Next Steps

After Phase 2 completion:
1. Beta user feedback collection
2. Phase 2 metrics review
3. Begin Phase 3: React Frontend

---

## Success Metrics to Track

**OCR Accuracy:**
- Baseline: 85%
- Target: 92%
- Measurement: Manual validation on 100+ documents

**Batch Processing:**
- Target: 50 documents in 5 minutes
- Success: 99% completion rate
- Measurement: Locust load testing

**GCP Deployment:**
- Target: < 10 min deployment time
- Success: Zero-downtime deployments
- Measurement: Cloud Run metrics

**Search Performance:**
- Target: < 200ms response time
- Success: Pagination works for 1M+ documents
- Measurement: Load testing

---

**Phase 2 roadmap complete. Ready to execute after Phase 1.**
