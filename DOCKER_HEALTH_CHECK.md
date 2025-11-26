# Docker Health Check Guide

**Purpose:** Automated smoke test for DraftCraft Docker environment
**Status:** Production Ready
**Last Updated:** November 26, 2025

---

## Overview

The Docker Health Check is an automated smoke test that validates all services in the DraftCraft Docker Compose environment are running correctly and communicating properly.

### When to Run

- **After `docker-compose up`** - Verify all services started successfully
- **Before running tests** - Ensure environment is healthy
- **In CI/CD pipelines** - Automated validation before deployments
- **Troubleshooting** - Diagnose service connectivity issues

### What It Tests

✅ **Container Status** (6 services)
- PostgreSQL database
- Redis cache
- Django web application
- Nginx reverse proxy
- Celery worker
- Celery beat scheduler

✅ **Connectivity**
- Database connectivity (SELECT 1 query)
- Redis connectivity (PING command)
- API health endpoint
- Nginx reverse proxy routing
- Authentication enforcement

✅ **Service Health**
- Database migrations applied
- Services responding to requests
- Inter-service communication working

---

## Quick Start

### Prerequisites

```bash
# Ensure Docker and docker-compose are installed
docker --version      # Docker 20.10+
docker-compose --version  # Docker Compose 1.29+

# Ensure ports are available
# Port 80 (Nginx)
# Port 8000 (Django)
# Port 5432 (PostgreSQL)
# Port 6379 (Redis)
```

### Running the Smoke Test

```bash
# Navigate to project root
cd DraftcraftV1

# Make script executable (Linux/Mac only)
chmod +x tests/docker_smoke_test.sh

# Run the smoke test
./tests/docker_smoke_test.sh

# Or using bash directly (cross-platform)
bash tests/docker_smoke_test.sh
```

### Expected Output

**Successful Run (all tests pass):**

```
🚀 DraftCraft Docker Compose Smoke Test
========================================
Start time: Wed Nov 26 10:35:00 UTC 2025
Report will be saved to: DOCKER_SMOKE_TEST_REPORT.md

Phase 1: Checking Container Status
====================================
✅ PostgreSQL container running
✅ Redis container running
✅ Web (Django) container running
✅ Nginx container running
✅ Celery Worker container running
✅ Celery Beat container running

Phase 2: Testing Service Connectivity
======================================
ℹ️  Testing PostgreSQL connectivity...
✅ PostgreSQL connection: OK

ℹ️  Testing Redis connectivity...
✅ Redis connection: OK (PONG)

Phase 3: Testing API Endpoints
===============================
ℹ️  Testing API health endpoint...
✅ API health endpoint: OK

ℹ️  Testing Nginx reverse proxy...
✅ Nginx reverse proxy: OK

ℹ️  Testing authentication enforcement...
✅ Authentication enforcement: OK (401 Unauthorized)

Phase 4: Checking Database Status
==================================
✅ Database migrations: Applied

Test Summary
============
Overall Status: ✅ PASSED
Passed: 11 / 11 tests
Failed: 0 / 11 tests
Success Rate: 100%
Duration: 45s

🎉 All smoke tests PASSED!
Docker environment is healthy and ready for use.
```

**Report File:** `DOCKER_SMOKE_TEST_REPORT.md`

A detailed markdown report is automatically generated with:
- Container status table
- Connectivity test results
- Service summary
- Troubleshooting guide

---

## Understanding the Report

### Container Status Table

```
| Service | Status | Port |
|---------|--------|------|
| PostgreSQL | Running | 5432 |
| Redis | Running | 6379 |
| Web (Django) | Running | 8000 |
| Nginx | Running | 80 |
| Celery Worker | Running | N/A |
| Celery Beat | Running | N/A |
```

**Status Meanings:**
- ✅ **Running** - Container is up and accepting requests
- ⚠️ **Unhealthy** - Container running but not responding (rare)
- ❌ **Stopped** - Container not running

### Connectivity Test Results

```
| Test | Result | Details |
|------|--------|---------|
| PostgreSQL Connection | ✅ PASS | Connected to draftcraft DB |
| Redis Connection | ✅ PASS | PONG response received |
| API Health Endpoint | ✅ PASS | Status: degraded (OCR not installed) |
| Nginx Reverse Proxy | ✅ PASS | Routed through nginx:80 |
| Authentication | ✅ PASS | Returns 401 as expected |
```

**Result Meanings:**
- ✅ **PASS** - Service responded correctly
- ⚠️ **WARNING** - Service responded but with unexpected result
- ❌ **FAIL** - Service did not respond or failed test

### API Health Endpoint Response

The `/api/v1/health/ocr/` endpoint returns OCR/NER service status:

**With ml.txt installed:**
```json
{
  "status": "healthy",
  "ocr_available": true,
  "ner_available": true,
  "message": "OCR/NER services operational"
}
```

**Without ml.txt installed (expected):**
```json
{
  "status": "degraded",
  "ocr_available": false,
  "ner_available": false,
  "message": "Install ML dependencies: pip install -r ml.txt"
}
```

This is normal. OCR/NER are optional in Phase 1.

---

## Troubleshooting

### Issue: Container Shows "Unhealthy"

**Symptom:** `docker-compose ps` shows container as unhealthy

**Solution:**
```bash
# Restart the container
docker-compose restart <service>

# Wait 30 seconds
sleep 30

# Check status
docker-compose ps <service>

# If still unhealthy, check logs
docker-compose logs <service>
```

**Common Causes:**
- Service startup taking too long (restart helps)
- Resource constraints (increase Docker memory)
- Port conflicts (see below)

### Issue: Port Already in Use

**Symptom:** Error like "Address already in use" or "Ports conflict"

**Solution:**
```bash
# Find process using port (Linux/Mac)
lsof -i :8000    # Django port
lsof -i :80      # Nginx port
lsof -i :5432    # PostgreSQL port
lsof -i :6379    # Redis port

# Windows alternative:
netstat -ano | findstr :8000

# Stop the conflicting process or use different ports
# Edit docker-compose.yml to use different ports
```

**Example docker-compose.yml modification:**
```yaml
web:
  ports:
    - "8001:8000"  # Changed from 8000 to 8001

nginx:
  ports:
    - "8080:80"    # Changed from 80 to 8080
```

Then update `.env` or your test script:
```bash
API_PORT="8001"
NGINX_PORT="8080"
```

### Issue: Database Connectivity Failed

**Symptom:** "PostgreSQL connection: FAILED"

**Solution:**
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify database exists
docker-compose exec postgres psql -U postgres -d draftcraft -c "SELECT 1;"

# If database doesn't exist, create it
docker-compose exec postgres createdb -U postgres draftcraft

# Run migrations
docker-compose exec web python manage.py migrate
```

**Common Causes:**
- PostgreSQL not fully started (wait 10-15 seconds)
- Database not created yet (run migrations)
- Credentials mismatch in settings

### Issue: Redis Connection Failed

**Symptom:** "Redis connection: FAILED"

**Solution:**
```bash
# Check Redis logs
docker-compose logs redis

# Test Redis manually
docker-compose exec redis redis-cli ping

# If not responding, restart
docker-compose restart redis
```

**Common Causes:**
- Redis not started (wait for startup)
- Port conflict (check with lsof)
- Redis memory limit exceeded

### Issue: API Health Endpoint Returns Nothing

**Symptom:** "API health endpoint: FAILED (timeout)"

**Solution:**
```bash
# Check if Django container is running
docker-compose ps web

# Check Django logs
docker-compose logs web

# Try accessing endpoint directly
curl http://localhost:8000/api/v1/health/ocr/

# If 404, ensure migrations are run
docker-compose exec web python manage.py migrate

# If 500 error, check logs for details
docker-compose logs web --tail=50
```

**Common Causes:**
- Django still starting up (wait 20-30 seconds)
- Migrations not applied
- Dependencies missing
- Database not initialized

### Issue: Nginx Proxy Test Failed

**Symptom:** "Nginx reverse proxy: FAILED"

**Solution:**
```bash
# Check Nginx logs
docker-compose logs nginx

# Verify Nginx is running
docker-compose ps nginx

# Test Nginx directly
curl http://localhost:80/api/v1/health/ocr/

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Restart Nginx
docker-compose restart nginx
```

**Common Causes:**
- Nginx not started
- Port 80 conflict
- Backend (Django) not accessible
- Configuration error in nginx.conf

### Issue: Authentication Test Failed

**Symptom:** "Authentication enforcement: FAILED (got HTTP 200)"

**Solution:**
```bash
# This means unauthenticated access is returning 200 (wrong)
# It should return 401 Unauthorized

# Check DRF permissions configuration
docker-compose exec web python manage.py shell
# Then test: from rest_framework.test import APIClient
#           client = APIClient()
#           response = client.get('/api/v1/documents/')
#           print(response.status_code)  # Should be 401

# Check Django settings
grep -n "DEFAULT_PERMISSION_CLASSES" backend/config/settings/base.py
# Should include IsAuthenticated

# Verify API views have authentication
grep -n "permission_classes.*IsAuthenticated" backend/api/v1/views.py
```

**Common Causes:**
- Permissions not configured in views
- AllowAny permission overriding authentication
- Swagger documentation allowing unauthenticated access

### Issue: Migrations Check Failed

**Symptom:** "Database migrations: Check failed"

**Solution:**
```bash
# Check migration status
docker-compose exec web python manage.py migrate --check

# Apply pending migrations
docker-compose exec web python manage.py migrate

# View migration status
docker-compose exec web python manage.py showmigrations

# If stuck on specific migration
docker-compose exec web python manage.py migrate <app> <migration_number>
```

**Common Causes:**
- New migrations haven't been applied
- Database schema out of sync
- Migration files corrupted or conflicting

---

## Manual Testing Commands

If the automated script fails, test each service manually:

```bash
# 1. PostgreSQL
docker-compose exec postgres psql -U postgres -d draftcraft -c "SELECT version();"

# 2. Redis
docker-compose exec redis redis-cli ping
docker-compose exec redis redis-cli info

# 3. Django API
curl -v http://localhost:8000/api/v1/health/ocr/

# 4. Nginx
curl -v http://localhost:80/api/v1/health/ocr/

# 5. Authentication (should return 401)
curl -v http://localhost:8000/api/v1/documents/

# 6. Full container status
docker-compose ps
docker-compose ps --services

# 7. Container health details
docker-compose ps | grep "health\|Up"
```

---

## Advanced Troubleshooting

### Enable Debug Logging

```bash
# Set Django debug logging
docker-compose exec web bash
export DEBUG=True
export LOG_LEVEL=DEBUG
python manage.py runserver 0.0.0.0:8000

# View all logs with timestamps
docker-compose logs --timestamps

# Follow logs in real-time
docker-compose logs -f web
```

### Access Container Shells

```bash
# Django shell for testing
docker-compose exec web python manage.py shell

# PostgreSQL psql
docker-compose exec postgres psql -U postgres

# Redis CLI
docker-compose exec redis redis-cli

# Bash shell in web container
docker-compose exec web bash
```

### Performance Profiling

```bash
# Check resource usage
docker stats

# Check container processes
docker-compose exec web ps aux

# Check open ports
docker-compose exec web netstat -tlnp
```

---

## Full System Reset

If all else fails, perform a complete reset:

```bash
# 1. Stop all containers
docker-compose down

# 2. Remove volumes (WARNING: deletes database!)
docker-compose down -v

# 3. Rebuild images
docker-compose build --no-cache

# 4. Start fresh
docker-compose up -d

# 5. Wait for startup
sleep 30

# 6. Run migrations
docker-compose exec web python manage.py migrate

# 7. Run smoke test again
./tests/docker_smoke_test.sh
```

---

## Next Steps After Successful Health Check

Once all tests pass:

### ✅ Safe to Proceed With:
- Running pytest: `docker-compose exec web pytest`
- Integration testing: Full workflow validation
- API testing: Postman or curl requests
- Production deployment: All systems verified
- CI/CD workflows: Automated testing

### 🔧 Optional Enhancements:
- Install ML dependencies: `pip install -r requirements/ml.txt`
- Enable debug toolbar: Set `DEBUG=True`
- Configure monitoring: Sentry, Prometheus
- Setup backups: Database snapshots

---

## Monitoring & Maintenance

### Regular Health Checks

Run the smoke test periodically:
```bash
# Daily (via cron)
0 0 * * * /path/to/DraftcraftV1/tests/docker_smoke_test.sh

# Before deployments
./tests/docker_smoke_test.sh

# After configuration changes
./tests/docker_smoke_test.sh
```

### Container Restarts

Safe container restart procedure:
```bash
# Restart one service
docker-compose restart web

# Restart all services
docker-compose restart

# Restart with logs
docker-compose restart web && docker-compose logs -f web
```

### View Historical Reports

```bash
# List all reports
ls -lh DOCKER_SMOKE_TEST_REPORT*.md

# Compare reports
diff DOCKER_SMOKE_TEST_REPORT.md.old DOCKER_SMOKE_TEST_REPORT.md

# Archive reports
mkdir -p reports
mv DOCKER_SMOKE_TEST_REPORT.md reports/DOCKER_SMOKE_TEST_REPORT_$(date +%Y%m%d).md
```

---

## Support & Documentation

### Related Documentation

- [Docker Compose Setup](docker-compose.yml) - Service configuration
- [Requirements Files](backend/requirements/README.md) - Dependency management
- [Development Guide](.claude/CLAUDE.md) - Project standards
- [API Documentation](http://localhost:8000/api/docs/swagger/) - Swagger UI

### Useful Commands Reference

```bash
# Quick reference card
docker-compose --help          # Docker Compose help
docker-compose ps              # List containers
docker-compose logs -f <svc>   # Follow logs
docker-compose exec <svc> bash # Access container
docker-compose up -d           # Start in background
docker-compose down            # Stop all services
docker-compose build           # Rebuild images
docker-compose pull            # Pull latest images
```

---

**Status:** ✅ Production Ready
**Last Verified:** November 26, 2025
**Next Review:** After Phase 2 completion

For questions or issues, review the Troubleshooting section above or check `docker-compose logs` for error details.
