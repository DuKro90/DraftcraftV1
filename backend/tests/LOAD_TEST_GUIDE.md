# DraftCraft Load Testing Guide

**Purpose:** Establish performance baselines for the DraftCraft API using Locust load testing framework.

**Last Updated:** November 26, 2025

---

## Overview

This guide provides instructions for running load tests against the DraftCraft API. Three test scenarios are defined to establish baseline performance metrics:

1. **Warm-up** (10 users, 2 minutes) - Lightweight baseline
2. **Target Load** (50 users, 5 minutes) - Expected production volume
3. **Stress Test** (100 users, 3 minutes) - Breaking point identification

---

## Prerequisites

### System Requirements

- Python 3.10+
- Docker and Docker Compose running (all services up)
- 2GB+ available RAM
- Network access to localhost:8000 (Django API)

### Verify Docker Services

```bash
# Check all services are running
docker-compose ps

# Expected output - all services should be "Up":
# PostgreSQL    Up
# Redis         Up
# Web (Django)  Up
# Nginx         Up
# Celery Worker Up
# Celery Beat   Up
```

### Install Locust

Locust should already be installed from `requirements/development.txt`:

```bash
# Verify installation
python -c "import locust; print(f'Locust {locust.__version__} installed')"
```

### Verify API Health

```bash
# Check API is responding
curl http://localhost:8000/api/v1/health/ocr/

# Expected response:
# {"status":"degraded","ocr_available":false,"ner_available":false}
```

---

## Setup Phase (Before Running Tests)

### Step 1: Create Load Test User and Token

```bash
# Generate load test user with authentication token
cd backend
python manage.py create_loadtest_user

# Output will display:
# Username: loadtest_user
# Password: LoadTest2024!Secure
# Token: <long-token-string>
```

**Save the token** - you'll need it if running tests manually with authentication debugging.

### Step 2: Create Sample Test Data

```bash
# Create sample documents and proposals
cd backend
python tests/fixtures/setup_loadtest_data.py

# Output will show:
# - Load test user created/found
# - 5 sample documents created
# - 3 sample proposals created
```

### Step 3: Verify Load Test File

```bash
# Syntax check
python -m py_compile tests/load_test.py

# Import check
python -c "from tests.load_test import ReadHeavyUser, WriteHeavyUser, MixedUser; print('Load test file OK')"
```

---

## Running Load Tests

### Method 1: Headless Mode (Recommended for Automation)

#### Warm-up Scenario (10 users, 2 min)

```bash
cd "C:\Codes\DraftcraftV1"

python -m locust \
  -f backend/tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 10 \
  --spawn-rate 2 \
  --run-time 2m \
  --csv backend/tests/reports/warmup \
  --html backend/tests/reports/warmup_report.html \
  --loglevel INFO
```

Expected behavior:
- Spawns 10 users at 2 users/second
- Authenticates each user
- Runs for 2 minutes
- Generates CSV and HTML reports

#### Target Load Scenario (50 users, 5 min)

```bash
python -m locust \
  -f backend/tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --csv backend/tests/reports/target_load \
  --html backend/tests/reports/target_load_report.html \
  --loglevel INFO
```

Expected behavior:
- Spawns 50 users at 5 users/second
- Runs for 5 minutes (steady state)
- Should see mix of read/write operations
- Reports give endpoint-level performance

#### Stress Test Scenario (100 users, 3 min)

```bash
python -m locust \
  -f backend/tests/load_test.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 3m \
  --csv backend/tests/reports/stress_test \
  --html backend/tests/reports/stress_test_report.html \
  --loglevel INFO
```

Expected behavior:
- Spawns 100 users at 10 users/second
- May see increased response times
- May see some failures (up to 10% acceptable)
- Identifies breaking point

### Method 2: Web UI (Interactive Mode)

For interactive testing with real-time metrics:

```bash
cd "C:\Codes\DraftcraftV1"

python -m locust \
  -f backend/tests/load_test.py \
  --host=http://localhost:8000
```

Then:
1. Open browser: http://localhost:8089
2. Enter users and spawn rate
3. Start test
4. View real-time charts and statistics
5. Stop test when satisfied

---

## Interpreting Results

### CSV Reports

Generated files like `warmup.csv` contain:

```
Type,Name,# requests,# failures,Median response time,Average response time,Min response time,Max response time,Average Content Size,Requests/s
GET,[READ] List Documents,245,0,120,145,98,512,4096,2.1
POST,[WRITE] Upload Document,78,2,450,520,400,1200,1024,0.7
```

**Key Metrics:**
- **# requests:** Total requests to this endpoint
- **# failures:** Failed requests (5xx errors, timeouts)
- **Median response time:** 50th percentile latency (ms)
- **Average response time:** Mean latency (ms)
- **Requests/s:** Throughput (requests per second)

### HTML Reports

Open the `.html` file in browser to see:
- **Requests/s Chart:** Throughput over time
- **Response Times Chart:** 50th, 66th, 75th, 90th, 95th, 99th percentiles
- **Users Chart:** Number of active users over time
- **Failure Rates:** Any failed requests highlighted

### Expected Performance Targets

#### Warm-up (10 users, 2 min)

| Metric | Target | Acceptable |
|--------|--------|-----------|
| Avg Response Time | <200ms | <300ms |
| P95 Response Time | <400ms | <500ms |
| Success Rate | 99% | >95% |
| Throughput | 8-12 req/s | >5 req/s |

#### Target Load (50 users, 5 min)

| Metric | Target | Acceptable |
|--------|--------|-----------|
| Avg Response Time | <500ms | <800ms |
| P95 Response Time | <1000ms | <1500ms |
| Success Rate | 95% | >90% |
| Throughput | 40-60 req/s | >30 req/s |

#### Stress Test (100 users, 3 min)

| Metric | Target | Acceptable |
|--------|--------|-----------|
| Avg Response Time | <1500ms | <2500ms |
| P95 Response Time | <3000ms | <5000ms |
| Success Rate | 90% | >80% |
| Throughput | Increasing then plateau | No continuous increase |

---

## Understanding User Distribution

The load test simulates realistic usage patterns:

### ReadHeavyUser (60% of users)
- **Behavior:** Browse documents and proposals
- **Task weights:**
  - List Documents (40%) - Most common
  - List Proposals (30%)
  - Retrieve Details (20%)
  - Health Check (10%)
- **Real-world:** Business users checking document status

### WriteHeavyUser (20% of users)
- **Behavior:** Upload and process documents
- **Task weights:**
  - Upload Document (50%)
  - Process Document (30%)
  - Check Status (20%)
- **Real-world:** Administrative staff adding new documents

### MixedUser (20% of users)
- **Behavior:** Balanced operations
- **Real-world:** Power users who both browse and manage

---

## Troubleshooting

### Issue: "Connection refused" on localhost:8000

**Solution:**
```bash
# Verify Django container is running
docker-compose ps web

# Check if API is responding
curl http://localhost:8000/api/v1/health/ocr/

# If not, restart
docker-compose restart web
docker-compose logs -f web
```

### Issue: "Authentication failed" errors

**Solution:**
```bash
# Recreate load test user
cd backend
python manage.py create_loadtest_user --reset

# Verify user exists in database
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(username='loadtest_user').exists()
True
```

### Issue: "No such file or directory: sample_load_test.pdf"

**Solution:**
```bash
# Verify PDF exists
ls -lh backend/tests/fixtures/sample_load_test.pdf

# If missing, copy from training data
python -c "
import shutil
from pathlib import Path
src = Path('Trainings_Daten').rglob('*.pdf')[0]
dst = Path('backend/tests/fixtures/sample_load_test.pdf')
shutil.copy(src, dst)
print(f'Copied {src} to {dst}')
"
```

### Issue: Tests running very slowly or timing out

**Solution:**
1. Check system resources: `docker stats`
2. Reduce spawn rate: `--spawn-rate 1`
3. Reduce number of users: `--users 10`
4. Check Django logs: `docker-compose logs web`

### Issue: High failure rate (>20%)

**Possible causes:**
1. Database connection pool exhausted
2. Django worker processes overwhelmed
3. Missing test data

**Debug:**
```bash
# Check Django logs
docker-compose logs web --tail=100

# Check PostgreSQL connections
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Restart containers
docker-compose restart
```

---

## Advanced Usage

### Custom Test Duration

```bash
# Run for 10 minutes
python -m locust -f tests/load_test.py --host=http://localhost:8000 --headless \
  --users 50 --spawn-rate 5 --run-time 10m
```

### Custom Host

```bash
# Test against staging environment
python -m locust -f tests/load_test.py --host=https://staging-api.example.com --headless \
  --users 50 --spawn-rate 5 --run-time 5m
```

### Debugging with Verbose Logging

```bash
# Enable detailed logging
python -m locust -f tests/load_test.py --host=http://localhost:8000 --headless \
  --users 10 --spawn-rate 2 --run-time 2m --loglevel DEBUG
```

---

## Performance Optimization Tips

Based on load test results, consider these optimizations:

### If Response Times > 1000ms
1. Add database query caching
2. Implement API response caching (Redis)
3. Add pagination limits
4. Optimize slow endpoints (profile first)

### If Throughput < 30 req/s
1. Increase Gunicorn workers (`WEB_WORKERS` env var)
2. Enable database connection pooling
3. Add load balancer for multiple instances
4. Profile application bottlenecks

### If Error Rate > 5%
1. Increase database connection pool
2. Add timeout handling
3. Implement rate limiting gracefully
4. Check resource limits (memory, CPU, disk)

---

## Next Steps

1. **Run all three scenarios** and save reports to `PERFORMANCE_BASELINE.md`
2. **Compare results to targets** listed in CLAUDE.md
3. **Identify bottlenecks** from slow endpoints
4. **Create Phase 2 optimization tasks** for any targets not met
5. **Schedule weekly runs** via CI/CD for trend tracking

---

## Support & Resources

- Locust Documentation: https://docs.locust.io
- DraftCraft Architecture: `.claude/CLAUDE.md`
- Performance Targets: `.claude/CLAUDE.md` (Performance Benchmarks section)
- CI/CD Integration: `.github/workflows/load-test.yml`

---

**Last Updated:** November 26, 2025
**Created by:** Load Testing Baseline Setup
**Phase:** Phase 1 MVP Verification
