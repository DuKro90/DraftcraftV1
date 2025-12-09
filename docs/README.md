# DraftCraft Documentation Index

Complete guide to all documentation in the DraftCraft project.

**Last Updated:** December 03, 2025
**Project Status:** Phase 4A Complete ✅ | Bulk Upload Added ✅

---

## 📚 Quick Navigation

### For Developers
Start here if you're new to the codebase or need development workflow guidance.

| Document | Purpose |
|----------|---------|
| [../DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) | Complete development workflow, testing, and best practices |
| [../backend/README.md](../backend/README.md) | Backend architecture and module overview |
| [../CHANGELOG.md](../CHANGELOG.md) | Project history and all changes |
| [../backend/BULK_UPLOAD_GUIDE.md](../backend/BULK_UPLOAD_GUIDE.md) | **NEW!** Bulk data upload guide for Betriebskennzahlen |

### For Admin Users
Quick guides for using the admin interface.

| Document | Purpose |
|----------|---------|
| [../backend/BULK_UPLOAD_GUIDE.md](../backend/BULK_UPLOAD_GUIDE.md) | Upload wood types, materials, and pricing data from Excel/CSV |
| [../backend/ADMIN_TOOLTIPS_GUIDE.md](../backend/ADMIN_TOOLTIPS_GUIDE.md) | Understanding admin interface tooltips and help text |

### Example Templates
Pre-generated Excel templates for bulk uploads (located in this folder):

| File | Purpose |
|------|---------|
| [holzarten_example.xlsx](./holzarten_example.xlsx) | Wood types (Eiche, Buche, Kiefer...) |
| [oberflaechen_example.xlsx](./oberflaechen_example.xlsx) | Surface finishes (Geölt, Lackiert...) |
| [komplexitaet_example.xlsx](./komplexitaet_example.xlsx) | Complexity factors (Gefräst, Gedrechselt...) |
| [materialliste_example.xlsx](./materialliste_example.xlsx) | Materials catalog (Screws, Glue, Hardware...) |

### For Deployment
Use these guides for deploying to different environments.

| Document | Purpose |
|----------|---------|
| [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Docker, GCP Cloud Run, Kubernetes deployment |
| [setup/LOCAL_TEST_SETUP.md](./setup/LOCAL_TEST_SETUP.md) | Local development environment setup |
| [testing/DOCKER_SMOKE_TEST_REPORT.md](./testing/DOCKER_SMOKE_TEST_REPORT.md) | Docker deployment validation |

### For Frontend Integration
| Document | Purpose |
|----------|---------|
| [../FRONTEND_INTEGRATION_GUIDE.md](../FRONTEND_INTEGRATION_GUIDE.md) | Complete API integration guide with examples |
| [../backend/api/README.md](../backend/api/README.md) | REST API endpoints reference |

---

## 🏗️ Project Architecture

### Phase Implementation Documentation

**Phase 2 - Agentic RAG Enhancement**
| Document | Purpose |
|----------|---------|
| [phases/phase2_agentic_rag_guide.md](./phases/phase2_agentic_rag_guide.md) | Detailed planning guide (German) |
| [phases/phase2_implementation_summary.md](./phases/phase2_implementation_summary.md) | Implementation summary with usage examples |
| [phases/phase2_validation_report.md](./phases/phase2_validation_report.md) | Validation and testing results |

**What is Phase 2 Enhancement?**
- Intelligent extraction enhancement with Google Gemini Flash 1.5
- Dual-layer memory architecture (Redis + PostgreSQL)
- 4-tier confidence routing (auto-accept → human review)
- Budget management and cost tracking

**Phase 3 - Betriebskennzahlen (Advanced Pricing)**
| Document | Purpose |
|----------|---------|
| [phases/phase3_integration_summary.md](./phases/phase3_integration_summary.md) | Complete integration architecture |
| [phases/phase3_testing_summary.md](./phases/phase3_testing_summary.md) | Testing approach and coverage |
| [phases/phase3_test_validation.md](./phases/phase3_test_validation.md) | Validation results and metrics |

**What is Phase 3?**
- 8-step pricing calculation engine (TIER 1/2/3)
- Pattern analysis for extraction failures
- Safe knowledge building and deployment
- Integrated pipeline orchestrating complete workflow

---

## 🧪 Testing Documentation

### Test Reports
| Document | Purpose |
|----------|---------|
| [testing/DOCKER_SMOKE_TEST_REPORT.md](./testing/DOCKER_SMOKE_TEST_REPORT.md) | Docker deployment smoke tests |
| [testing/DOCKER_HEALTH_CHECK.md](./testing/DOCKER_HEALTH_CHECK.md) | Container health validation |
| [testing/PERFORMANCE_BASELINE.md](./testing/PERFORMANCE_BASELINE.md) | Performance benchmarks |
| [testing/README.md](./testing/README.md) | Testing strategy overview |

### Test Suites
| Location | Purpose |
|----------|---------|
| [../backend/tests/](../backend/tests/) | Complete test suite (169+ tests) |
| [../backend/tests/README.md](../backend/tests/README.md) | Testing patterns and fixtures |
| [../backend/tests/LOAD_TEST_GUIDE.md](../backend/tests/LOAD_TEST_GUIDE.md) | Load testing procedures |

**Coverage:** 85%+ across all modules

---

## 📖 Module-Specific Documentation

### Core Modules
| Module | Documentation |
|--------|--------------|
| Core Constants | [../backend/core/README.md](../backend/core/README.md) |
| Document Management | [../backend/documents/README.md](../backend/documents/README.md) |
| Extraction Services | [../backend/extraction/README.md](../backend/extraction/README.md) |
| Proposal Generation | [../backend/proposals/README.md](../backend/proposals/README.md) |
| REST API | [../backend/api/README.md](../backend/api/README.md) |

---

## 📋 Setup & Configuration

### Environment Setup
| Document | Purpose |
|----------|---------|
| [setup/LOCAL_TEST_SETUP.md](./setup/LOCAL_TEST_SETUP.md) | Local development with SQLite |
| [../backend/.env.example](../backend/.env.example) | Environment variables template |

### Requirements
| File | Purpose |
|------|---------|
| [../backend/requirements/base.txt](../backend/requirements/base.txt) | Core dependencies |
| [../backend/requirements/development.txt](../backend/requirements/development.txt) | Development tools |
| [../backend/requirements/ml.txt](../backend/requirements/ml.txt) | Machine learning dependencies |

---

## 🗂️ Archived Documentation

Historical documentation for completed phases and superseded guides.

### Archived Phases
| Document | Purpose |
|----------|---------|
| [archived_phases/PHASE_1_CHECKLIST.md](./archived_phases/PHASE_1_CHECKLIST.md) | Phase 1 task checklist (historical) |
| [archived_phases/PHASE_2_CHECKLIST.md](./archived_phases/PHASE_2_CHECKLIST.md) | Phase 2 task checklist (historical) |
| [archived_phases/ROADMAP_OVERVIEW.md](./archived_phases/ROADMAP_OVERVIEW.md) | Original project roadmap |
| [archived_phases/README.md](./archived_phases/README.md) | Archive index |

### Other Archives
- `../docs_archive/` - Superseded documentation and reports

---

## 🔍 Finding What You Need

### I want to...

**...set up my development environment**
→ Start with [../DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)

**...understand the project architecture**
→ Read [../README.md](../README.md) then [phases/](./phases/)

**...deploy to production**
→ Follow [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)

**...integrate the API**
→ Use [../FRONTEND_INTEGRATION_GUIDE.md](../FRONTEND_INTEGRATION_GUIDE.md)

**...understand Phase 2/3 features**
→ Check [phases/](./phases/) documentation

**...run tests**
→ See [testing/README.md](./testing/README.md)

**...understand a specific module**
→ Check module README in [../backend/](../backend/)

---

## 📝 Documentation Standards

### When to Update Documentation

- ✅ **Always:** Update when adding new features
- ✅ **Always:** Update when changing architecture
- ✅ **Always:** Update when fixing major bugs
- ✅ **Always:** Update version numbers and dates

### Documentation Locations

| Type | Location | Example |
|------|----------|---------|
| **Project Overview** | Root | README.md, DEVELOPER_GUIDE.md |
| **Phase Documentation** | docs/phases/ | phase3_integration_summary.md |
| **Module Documentation** | backend/{module}/ | backend/extraction/README.md |
| **Test Documentation** | docs/testing/ | DOCKER_SMOKE_TEST_REPORT.md |
| **Setup Guides** | docs/setup/ | LOCAL_TEST_SETUP.md |
| **Claude Development** | .claude/ | CLAUDE.md, guides/ |
| **Archives** | docs/archived_phases/ | PHASE_1_CHECKLIST.md |

---

## 🆘 Getting Help

### Common Questions

**Q: Where is the API documentation?**
A: Interactive API docs at `http://localhost:8000/api/docs/swagger/` or see [../backend/api/README.md](../backend/api/README.md)

**Q: How do I run tests?**
A: `pytest --cov=. --cov-fail-under=80 -v` or see [testing/README.md](./testing/README.md)

**Q: How do I deploy to GCP?**
A: See [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md#gcp-cloud-run-deployment)

**Q: What are the Phase 2/3 enhancements?**
A: See [phases/phase2_implementation_summary.md](./phases/phase2_implementation_summary.md) and [phases/phase3_integration_summary.md](./phases/phase3_integration_summary.md)

**Q: Where are old/archived docs?**
A: See [archived_phases/](./archived_phases/) and `../docs_archive/`

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Total Documentation Files** | 40+ markdown files |
| **Code Files** | 50+ Python files |
| **Lines of Code** | 10,000+ |
| **Test Cases** | 169+ |
| **Test Coverage** | 85%+ |
| **Phases Complete** | 3/3 ✅ |
| **API Endpoints** | 20+ |

---

**Last Updated:** November 27, 2025
**Maintained By:** Development Team
**Status:** ✅ Complete and Current
