# Phase 1 - Quick Start Guide
**Execute Tasks in This Order** | **Time: 2 weeks**

---

## ⏱️ Time Estimate

- **Day 1:** 4 hours (Stub removal + OCR deps)
- **Day 2:** 6 hours (E2E test + Docker test)
- **Day 3:** 5 hours (Load testing + quick wins)
- **Day 4-5:** 2 hours (Documentation)
- **TOTAL:** 20-30 hours over 2 weeks

---

## 📋 Task Checklist (In Order)

### Day 1 (4 hours)

**Task 1: Remove Stub Code** (1 hour) ⏱️
```
File: backend/proposals/services.py
Line: 301-304 (NotImplementedError)
Action: Delete or replace with import
Test: pytest tests/test_pdf_service.py -v
Commit: "Remove NotImplementedError stub for PDF generation"
```

**Task 2: Split OCR Dependencies** (3 hours) ⏱️
```
Create: backend/requirements/ml.txt
Update: backend/requirements/development.txt
Update: backend/requirements/README.md
Test: pytest tests/test_extraction_services.py -v
Commit: "Split OCR/ML dependencies to requirements/ml.txt"
```

**Task 3: OCR Health Check** (included in Task 2) ⏱️
```
File: backend/api/v1/views.py → Add health_ocr() function
File: backend/api/v1/urls.py → Add route
Test: curl http://localhost:8000/api/v1/health/ocr/
Commit: "Add OCR health check endpoint"
```

---

### Day 2 (6 hours)

**Task 4: End-to-End Test** (4 hours) ⏱️
```
Create: backend/tests/test_end_to_end.py
Create: tests/fixtures/sample_document.pdf
Test: pytest tests/test_end_to_end.py -v
Commit: "Add end-to-end workflow integration test"
```

**Task 5: Docker Smoke Test** (2 hours) ⏱️
```
Create: tests/docker_smoke_test.sh
Run: ./tests/docker_smoke_test.sh
Create: DOCKER_HEALTH_CHECK.md
Commit: "Add Docker Compose smoke test"
```

---

### Day 3 (5 hours)

**Task 6: Load Testing** (6 hours, continues to Week 2) ⏱️
```
Install: pip install locust
Create: backend/tests/load_test.py
Run: locust -f tests/load_test.py --host=http://localhost:8000
Create: PERFORMANCE_BASELINE.md
Commit: "Add load testing baseline with Locust"
```

**Task 7: Rate Limiting** (2 hours) ⏱️
```
Create: tests/test_rate_limiting.py
Test: pytest tests/test_rate_limiting.py -v
Commit: "Verify API rate limiting configuration"
```

**Task 8: Error Messages** (3 hours) ⏱️
```
Create: backend/api/error_codes.py
Create: tests/test_error_messages.py
Update: config/settings/base.py
Commit: "Improve API error messages with error codes"
```

---

### Day 4-5 (2 hours)

**Task 9: Frontend Documentation** (2 hours) ⏱️
```
Create: FRONTEND_STATUS.md
Review with team
Commit: "Document existing frontend status and gaps"
```

**Task 10: Roadmap Update** (1 hour) ⏱️
```
Review phase 1 results
Update documentation
Commit: "Update roadmap with Phase 1 results"
```

---

## 🎯 Success Checklist

At the end of Phase 1, verify:

- [ ] No `NotImplementedError` in proposals/services.py
- [ ] `ml.txt` file created with OCR dependencies
- [ ] `GET /api/v1/health/ocr/` endpoint working
- [ ] End-to-end test passing
- [ ] Docker smoke test passing
- [ ] Load test baseline documented
- [ ] Rate limiting tests passing
- [ ] Error messages consistent
- [ ] `FRONTEND_STATUS.md` created
- [ ] All commits pushed

---

## 🚀 Getting Started NOW

### Step 1: Setup
```bash
cd C:\Codes\DraftcraftV1
git status  # Check for uncommitted changes
```

### Step 2: Start with Task 1
```bash
code backend/proposals/services.py
# Navigate to line 301
# Review the NotImplementedError block (lines 280-304)
# Delete the entire class (simplest approach)
```

### Step 3: Test
```bash
pytest tests/test_pdf_service.py -v
```

### Step 4: Commit
```bash
git add backend/proposals/services.py
git commit -m "Remove NotImplementedError stub for PDF generation"
```

---

## 📞 If You Get Stuck

**Task 1 (Stub removal):**
- Check what other code imports this class: `grep -r "ProposalPdfService" --include="*.py"`
- If nothing imports it, safe to delete
- If something imports, replace with: `from .pdf_service import ProposalPdfService`

**Task 2 (OCR dependencies):**
- Check what goes in ml.txt: Look at existing development.txt commented lines
- Verify services handle missing imports gracefully

**Task 4 (E2E test):**
- Find correct API endpoint names in `backend/api/v1/urls.py`
- Adjust test to match actual endpoint names
- May need to adjust expected response format

**Task 5 (Docker):**
- If script fails, run individual checks:
  - `docker-compose ps`
  - `docker-compose logs web`
  - `curl http://localhost/api/v1/health/`

**Task 6 (Load test):**
- If Locust won't start, check Django is running:
  - `python manage.py runserver` in separate terminal
- Adjust spawn rate if getting connection errors

---

## 📚 Full Instructions

For **complete detailed instructions** with all code examples, see:
- **`PHASE_1_CHECKLIST.md`** ← Start here for full details

For **overview of all 4 phases**, see:
- **`ROADMAP_OVERVIEW.md`** ← For big picture

---

## ⏰ Time-Box Strategy

**If running behind:**
1. Priority 1 (CRITICAL): Tasks 1, 2, 4, 5
2. Priority 2 (HIGH): Tasks 3, 6, 7
3. Priority 3 (MEDIUM): Tasks 8, 9, 10

**Minimum viable Phase 1 (12 hours):**
- Task 1: Stub removal (1 hr)
- Task 2: OCR deps split (3 hrs)
- Task 4: E2E test (4 hrs)
- Task 5: Docker test (2 hrs)
- Task 9: Frontend docs (2 hrs)

---

## 🎓 Learning Resources

- Django REST Framework: https://www.django-rest-framework.org/
- Pytest: https://docs.pytest.org/
- Docker: https://docs.docker.com/
- Locust: https://locust.io/

---

## Next Phase

Once Phase 1 is complete (by Dec 16), start Phase 2:
- See `PHASE_2_CHECKLIST.md`
- Focus on OCR accuracy improvements
- Batch processing implementation
- GCP staging deployment

---

**Ready? Start with Task 1 now!** 🚀
