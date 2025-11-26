# DraftCraft Performance Baseline Report

**Report Date:** November 26, 2025
**Phase:** Phase 1 MVP Load Testing
**Status:** Baseline Setup Complete - Ready for Manual Testing

---

## Executive Summary

This document outlines the performance baseline testing infrastructure established for the DraftCraft API during Phase 1 MVP verification. The load testing framework (Locust 2.32.0) is fully configured and ready to be executed against the production-like Docker environment.

### Key Metrics to Track

| Metric | Phase 1 Target | Phase 2 Goal |
|--------|---|---|
| API Response Time (avg) | <500ms | <300ms |
| API Response Time (p95) | <1000ms | <500ms |
| Throughput | 40-60 req/s | 100+ req/s |
| Success Rate | >95% | >99% |
| Document Processing | 10-20 docs/min | 50+ docs/min |

---

## Test Infrastructure

### Components Deployed

#### 1. Load Testing Framework
- **Tool:** Locust 2.32.0 (compatible with Python 3.11)
- **Location:** `backend/tests/load_test.py`
- **Framework Features:**
  - Token-based authentication
  - Three user types (ReadHeavy, WriteHeavy, Mixed)
  - Realistic weight distribution (60/20/20)
  - Event handlers for test lifecycle logging

#### 2. Test Configuration Files
- **Configuration:** `backend/tests/fixtures/loadtest_data.json`
- **Setup Script:** `backend/tests/fixtures/setup_loadtest_data.py`
- **Execution Guide:** `backend/tests/LOAD_TEST_GUIDE.md`
- **Sample Data:** `backend/tests/fixtures/sample_load_test.pdf` (269 KB)

#### 3. Test Data
- Sample PDF document: 3x3 solution request (realistic user document)
- Test User: `loadtest_user` with API authentication
- Pre-created test documents and proposals in database

#### 4. CI/CD Integration
- **Workflow:** `.github/workflows/load-test.yml`
- **Frequency:** Manual trigger + weekly automated runs
- **Scope:** Moderate load test (20 users, 1 minute) for CI/CD pipeline

---

## Test Scenarios Defined

### Scenario 1: Warm-up (Lightweight Baseline)
**Purpose:** Verify system responsiveness and establish baseline metrics

| Parameter | Value |
|-----------|-------|
| Duration | 2 minutes |
| Concurrent Users | 10 |
| User Spawn Rate | 2 users/second |
| Expected Avg Response | <200ms |
| Expected P95 Response | <400ms |
| Expected Success Rate | 99% |

**User Distribution:**
- ReadHeavyUser (6 users, 60%)
- WriteHeavyUser (2 users, 20%)
- MixedUser (2 users, 20%)

### Scenario 2: Target Load (Production Volume)
**Purpose:** Simulate expected weekly production volume (30-100 proposals/week)

| Parameter | Value |
|-----------|-------|
| Duration | 5 minutes |
| Concurrent Users | 50 |
| User Spawn Rate | 5 users/second |
| Expected Avg Response | <500ms |
| Expected P95 Response | <1000ms |
| Expected Success Rate | >95% |

**User Distribution:**
- ReadHeavyUser (30 users, 60%)
- WriteHeavyUser (10 users, 20%)
- MixedUser (10 users, 20%)

### Scenario 3: Stress Test (Breaking Point)
**Purpose:** Identify performance degradation and breaking point

| Parameter | Value |
|-----------|-------|
| Duration | 3 minutes |
| Concurrent Users | 100 |
| User Spawn Rate | 10 users/second |
| Expected Avg Response | <1500ms |
| Expected P95 Response | <3000ms |
| Expected Success Rate | >80% |

**User Distribution:**
- ReadHeavyUser (60 users, 60%)
- WriteHeavyUser (20 users, 20%)
- MixedUser (20 users, 20%)

---

## API Endpoints Under Test

### Critical Endpoints (High Priority)

| Endpoint | Method | Purpose | Test Weight |
|----------|--------|---------|------------|
| `/api/auth/token/` | POST | User authentication | Initial |
| `/api/v1/documents/` | POST | Document upload | Write-heavy |
| `/api/v1/documents/{id}/process/` | POST | OCR/NER processing | Write-heavy |
| `/api/v1/documents/` | GET | List documents | Read-heavy |

### Secondary Endpoints (Read Operations)

| Endpoint | Method | Purpose | Test Weight |
|----------|--------|---------|------------|
| `/api/v1/documents/{id}/` | GET | Document details | Read-heavy |
| `/api/v1/proposals/` | GET | List proposals | Read-heavy |
| `/api/v1/health/ocr/` | GET | Service health | Health check |

---

## User Behavior Profiles

### ReadHeavyUser (60% of load)
**Simulates:** Business users browsing documents and proposals

**Task Distribution:**
- List Documents (40%) - Most frequent operation
- List Proposals (30%)
- Retrieve Document Details (20%)
- Health Check (10%) - Lightweight monitoring

**Inter-request Wait Time:** 1-3 seconds

### WriteHeavyUser (20% of load)
**Simulates:** Administrative staff uploading and processing documents

**Task Distribution:**
- Upload Document (50%)
- Process Document (30%)
- Check Processing Status (20%)

**Inter-request Wait Time:** 1-3 seconds

### MixedUser (20% of load)
**Simulates:** Power users with balanced operations

**Task Distribution:**
- List Documents (20%)
- Upload Document (20%)
- Process Document (15%)
- List Proposals (15%)

**Inter-request Wait Time:** 1-3 seconds

---

## Performance Targets (from CLAUDE.md)

### Phase 1 MVP Requirements

| Metric | Target | Rationale |
|--------|--------|-----------|
| OCR Processing | <2s per A4 page | Real-time user feedback |
| API List Response | <0.5s | User experience |
| Memory Usage | <512MB | Cloud Run constraints |
| Success Rate | >95% | Acceptable error tolerance |
| Document Throughput | 10-20 docs/min | Weekly volume handling |

### Phase 2 Production Targets

| Metric | Goal | Improvement |
|--------|------|------------|
| OCR Processing | <1s per page | 50% improvement |
| API List Response | <0.3s | 40% improvement |
| Memory Usage | <400MB | Optimization |
| Success Rate | >99% | Higher reliability |
| Document Throughput | 50+ docs/min | 3x improvement |

---

## Test Execution Instructions

### Quick Start

```bash
# 1. Navigate to project directory
cd C:\Codes\DraftcraftV1

# 2. Verify Docker services
docker-compose ps

# 3. Create test user and data
docker-compose exec web python manage.py create_loadtest_user
docker-compose exec web python tests/fixtures/setup_loadtest_data.py

# 4. Run warm-up test
cd backend
python -m locust -f tests/load_test.py --host=http://localhost:8000 --headless \
  --users 10 --spawn-rate 2 --run-time 2m --csv tests/reports/warmup

# 5. Review results
# Open: backend/tests/reports/warmup_report.html
```

### Full Test Suite Execution

See `backend/tests/LOAD_TEST_GUIDE.md` for comprehensive instructions including:
- Prerequisites verification
- Setup phase walkthrough
- Detailed command for each scenario
- Result interpretation guide
- Troubleshooting section

---

## Expected Results Structure

After running tests, the following files will be generated:

```
backend/tests/reports/
├── warmup.csv                 # Warm-up test metrics
├── warmup_report.html         # Warm-up test charts
├── target_load.csv            # Target load test metrics
├── target_load_report.html    # Target load test charts
├── stress_test.csv            # Stress test metrics
└── stress_test_report.html    # Stress test charts
```

### CSV Report Format

```
Type,Name,# requests,# failures,Median response time,Average response time,...
GET,[READ] List Documents,245,0,120,145,...
POST,[WRITE] Upload Document,78,2,450,520,...
```

### HTML Report Features

- Real-time request/second throughput chart
- Response time percentiles (50th, 95th, 99th)
- Active users over test duration
- Failure rate analysis
- Per-endpoint detailed metrics

---

## Baseline Metrics Placeholder

The following section will be populated after running the load tests:

### Warm-up Results

| Metric | Measured | Target | Status |
|--------|----------|--------|--------|
| Avg Response Time | - | <200ms | PENDING |
| P95 Response Time | - | <400ms | PENDING |
| Throughput | - | 8-12 req/s | PENDING |
| Success Rate | - | 99% | PENDING |

### Target Load Results

| Metric | Measured | Target | Status |
|--------|----------|--------|--------|
| Avg Response Time | - | <500ms | PENDING |
| P95 Response Time | - | <1000ms | PENDING |
| Throughput | - | 40-60 req/s | PENDING |
| Success Rate | - | >95% | PENDING |

### Stress Test Results

| Metric | Measured | Target | Status |
|--------|----------|--------|--------|
| Avg Response Time | - | <1500ms | PENDING |
| P95 Response Time | - | <3000ms | PENDING |
| Throughput | - | 60-80 req/s | PENDING |
| Success Rate | - | >80% | PENDING |

---

## Endpoint Performance Analysis

To be populated after test execution. Template for each endpoint:

### Example: GET /api/v1/documents/

**Warm-up Performance:**
- Requests: [PENDING]
- Failures: [PENDING]
- Avg Response: [PENDING]
- P95 Response: [PENDING]

**Target Load Performance:**
- Requests: [PENDING]
- Failures: [PENDING]
- Avg Response: [PENDING]
- P95 Response: [PENDING]

**Stress Test Performance:**
- Requests: [PENDING]
- Failures: [PENDING]
- Avg Response: [PENDING]
- P95 Response: [PENDING]

---

## Resource Utilization Analysis

### Expected Resource Usage During Tests

**Warm-up (10 users):**
- CPU: ~15-25%
- Memory: ~150-200MB
- Database Connections: ~10-15
- Network: ~1-2 Mbps

**Target Load (50 users):**
- CPU: ~40-60%
- Memory: ~300-400MB
- Database Connections: ~40-50
- Network: ~5-10 Mbps

**Stress Test (100 users):**
- CPU: ~70-90%
- Memory: ~450-500MB
- Database Connections: ~80-100
- Network: ~10-20 Mbps

### Container Health During Tests

Monitor Docker metrics:

```bash
# Watch container performance
docker stats

# Check logs for errors
docker-compose logs web --tail=50
docker-compose logs postgres
docker-compose logs redis
```

---

## Comparison to Phase 1 Targets

| Metric | Phase 1 Target | Expected Baseline | Status |
|--------|---|---|---|
| API Response (<0.5s) | >95% requests | To be measured | PENDING |
| Success Rate | >95% | To be measured | PENDING |
| Memory Usage | <512MB | To be measured | PENDING |
| Throughput | 40+ req/s target | To be measured | PENDING |

---

## Phase 2 Optimization Priorities

Based on baseline results, Phase 2 should focus on:

### High Priority (If baseline misses targets)
1. Database query optimization
2. API response caching (Redis)
3. Connection pooling optimization
4. Gunicorn worker tuning

### Medium Priority (For improvement)
1. Pagination optimization
2. Bulk operation endpoints
3. Async processing architecture
4. Load balancing setup

### Low Priority (Enhancement)
1. CDN integration
2. Advanced caching strategies
3. Query result compression
4. Monitoring/alerting setup

---

## Continuous Monitoring Plan

### Weekly Baseline Runs

The GitHub Actions workflow (`.github/workflows/load-test.yml`) will:
- Run automatically every Monday at 02:00 UTC
- Execute moderate load test (20 users, 1 minute)
- Generate report and commit to repository
- Alert on performance degradation

### Trend Analysis

Track metrics over time to identify:
- Performance regressions
- Gradual degradation
- Seasonal patterns
- Impact of code changes

### Alert Thresholds

Set up alerts if:
- Avg response time increases >20%
- Success rate drops below 90%
- P95 response time exceeds 2000ms
- Throughput decreases >30%

---

## Appendix: Reproducibility Steps

### Full Reproduction from Scratch

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Wait for services
sleep 30

# 3. Run migrations
docker-compose exec web python manage.py migrate

# 4. Create test user
docker-compose exec web python manage.py create_loadtest_user

# 5. Setup test data
cd backend
python tests/fixtures/setup_loadtest_data.py

# 6. Create reports directory
mkdir -p tests/reports

# 7. Run warm-up
python -m locust -f tests/load_test.py --host=http://localhost:8000 --headless \
  --users 10 --spawn-rate 2 --run-time 2m --csv tests/reports/warmup
```

### Docker Environment Requirements

```bash
# Verify all services running
docker-compose ps
# Expected: all services "Up"

# Verify API responding
curl http://localhost:8000/api/v1/health/ocr/

# Verify database
docker-compose exec postgres psql -U postgres -d draftcraft -c "SELECT 1;"

# Verify Redis
docker-compose exec redis redis-cli ping
```

---

## Next Steps

1. **Run Manual Tests:** Execute all 3 scenarios following `LOAD_TEST_GUIDE.md`
2. **Collect Metrics:** Record all CSV and HTML report data
3. **Populate Baseline:** Update this document with actual results
4. **Analyze:** Compare to targets and identify bottlenecks
5. **Plan Phase 2:** Create optimization tasks based on findings

---

## References

- **Execution Guide:** `backend/tests/LOAD_TEST_GUIDE.md`
- **Load Test Code:** `backend/tests/load_test.py`
- **Test Configuration:** `backend/tests/fixtures/loadtest_data.json`
- **Performance Targets:** `.claude/CLAUDE.md` (Performance Benchmarks section)
- **Project Standards:** `.claude/CLAUDE.md`

---

**Status:** Ready for Testing
**Last Updated:** November 26, 2025
**Next Review:** After manual baseline tests complete
**Phase:** Phase 1 MVP Load Testing Infrastructure
