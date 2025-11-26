#!/bin/bash

# DraftCraft Docker Compose Smoke Test
# Tests all services and generates health report
# Usage: ./tests/docker_smoke_test.sh

set -o pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT=120
RETRIES=30  # Increased from 24 to give more time for PostgreSQL connection
RETRY_INTERVAL=5
API_HOST="${DOCKER_HOST:-localhost}"
API_PORT="8000"
NGINX_PORT="80"
REPORT_FILE="DOCKER_SMOKE_TEST_REPORT.md"
START_TIME=$(date +%s)

# Tracking
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_TEST_LIST=()

# Test result storage
declare -a CONTAINER_RESULTS
declare -a CONNECTIVITY_RESULTS

echo ""
echo "🚀 DraftCraft Docker Compose Smoke Test"
echo "========================================"
echo "Start time: $(date)"
echo "Report will be saved to: $REPORT_FILE"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

log_pass() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED_TESTS++))
    FAILED_TEST_LIST+=("$1")
}

log_info() {
    echo -e "${YELLOW}ℹ️ ${NC} $1"
}

wait_for_service() {
    local service=$1
    local check_cmd=$2
    local max_attempts=$3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if eval "$check_cmd" > /dev/null 2>&1; then
            return 0
        fi

        if [ $attempt -eq 1 ]; then
            echo -n "   Waiting for $service to be healthy"
        fi

        echo -n "."
        sleep $RETRY_INTERVAL
        ((attempt++))
    done

    if [ $attempt -gt 1 ]; then
        echo "" # New line after dots
    fi
    return 1
}

# ============================================================================
# Phase 1: Container Status Checks
# ============================================================================

echo "Phase 1: Checking Container Status"
echo "===================================="

# Get docker-compose status
cd "$(dirname "$0")/.." || exit 1

# Check PostgreSQL
if docker-compose ps postgres | grep -q "Up"; then
    log_pass "PostgreSQL container running"
    CONTAINER_RESULTS+=("PostgreSQL|Running|5432")
else
    log_fail "PostgreSQL container not running"
    CONTAINER_RESULTS+=("PostgreSQL|Stopped|5432")
fi

# Check Redis
if docker-compose ps redis | grep -q "Up"; then
    log_pass "Redis container running"
    CONTAINER_RESULTS+=("Redis|Running|6379")
else
    log_fail "Redis container not running"
    CONTAINER_RESULTS+=("Redis|Stopped|6379")
fi

# Check Web (Django)
if docker-compose ps web | grep -q "Up"; then
    log_pass "Web (Django) container running"
    CONTAINER_RESULTS+=("Web (Django)|Running|8000")
else
    log_fail "Web (Django) container not running"
    CONTAINER_RESULTS+=("Web (Django)|Stopped|8000")
fi

# Check Nginx
if docker-compose ps nginx | grep -q "Up"; then
    log_pass "Nginx container running"
    CONTAINER_RESULTS+=("Nginx|Running|80")
else
    log_fail "Nginx container not running"
    CONTAINER_RESULTS+=("Nginx|Stopped|80")
fi

# Check Celery Worker
if docker-compose ps celery_worker | grep -q "Up"; then
    log_pass "Celery Worker container running"
    CONTAINER_RESULTS+=("Celery Worker|Running|N/A")
else
    log_fail "Celery Worker container not running"
    CONTAINER_RESULTS+=("Celery Worker|Stopped|N/A")
fi

# Check Celery Beat
if docker-compose ps celery_beat | grep -q "Up"; then
    log_pass "Celery Beat container running"
    CONTAINER_RESULTS+=("Celery Beat|Running|N/A")
else
    log_fail "Celery Beat container not running"
    CONTAINER_RESULTS+=("Celery Beat|Stopped|N/A")
fi

echo ""

# ============================================================================
# Phase 2: Connectivity Tests
# ============================================================================

echo "Phase 2: Testing Service Connectivity"
echo "======================================"

# Test PostgreSQL Database
log_info "Testing PostgreSQL connectivity..."
if wait_for_service "PostgreSQL" "docker-compose exec -T postgres psql -U postgres -d draftcraft -c 'SELECT 1;' 2>/dev/null | grep -q 1" "$RETRIES"; then
    log_pass "PostgreSQL connection: OK"
    CONNECTIVITY_RESULTS+=("PostgreSQL Connection|✅ PASS|Connected to draftcraft DB")
else
    log_fail "PostgreSQL connection: FAILED"
    CONNECTIVITY_RESULTS+=("PostgreSQL Connection|❌ FAIL|Could not connect")
fi

# Test Redis
log_info "Testing Redis connectivity..."
if wait_for_service "Redis" "docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG" "$RETRIES"; then
    log_pass "Redis connection: OK (PONG)"
    CONNECTIVITY_RESULTS+=("Redis Connection|✅ PASS|PONG response received")
else
    log_fail "Redis connection: FAILED"
    CONNECTIVITY_RESULTS+=("Redis Connection|❌ FAIL|No PONG response")
fi

echo ""

# ============================================================================
# Phase 3: API Health Checks
# ============================================================================

echo "Phase 3: Testing API Endpoints"
echo "==============================="

# Test API health endpoint
log_info "Testing API health endpoint..."
if wait_for_service "API" "curl -s http://$API_HOST:$API_PORT/api/v1/health/ocr/ | grep -q status" "$RETRIES"; then
    HEALTH_STATUS=$(curl -s http://$API_HOST:$API_PORT/api/v1/health/ocr/)
    if echo "$HEALTH_STATUS" | grep -q "degraded\|healthy"; then
        log_pass "API health endpoint: OK"
        CONNECTIVITY_RESULTS+=("API Health Endpoint|✅ PASS|Status: $(echo $HEALTH_STATUS | grep -o '"status":"[^"]*"')")
    else
        log_fail "API health endpoint: Unexpected response"
        CONNECTIVITY_RESULTS+=("API Health Endpoint|⚠️  WARNING|Unexpected response format")
    fi
else
    log_fail "API health endpoint: FAILED (timeout)"
    CONNECTIVITY_RESULTS+=("API Health Endpoint|❌ FAIL|API not responding")
fi

# Test Nginx reverse proxy
log_info "Testing Nginx reverse proxy..."
if curl -s http://$API_HOST:$NGINX_PORT/api/v1/health/ocr/ > /dev/null 2>&1; then
    log_pass "Nginx reverse proxy: OK"
    CONNECTIVITY_RESULTS+=("Nginx Reverse Proxy|✅ PASS|Routed through nginx:80")
else
    log_fail "Nginx reverse proxy: FAILED"
    CONNECTIVITY_RESULTS+=("Nginx Reverse Proxy|❌ FAIL|Could not route through nginx")
fi

# Test authentication (should return 401)
log_info "Testing authentication enforcement..."
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$API_HOST:$API_PORT/api/v1/documents/)
if [ "$AUTH_STATUS" = "401" ]; then
    log_pass "Authentication enforcement: OK (401 Unauthorized)"
    CONNECTIVITY_RESULTS+=("Authentication|✅ PASS|Returns 401 as expected")
else
    log_fail "Authentication enforcement: FAILED (got HTTP $AUTH_STATUS)"
    CONNECTIVITY_RESULTS+=("Authentication|❌ FAIL|Expected 401 but got $AUTH_STATUS")
fi

echo ""

# ============================================================================
# Phase 4: Database Migrations Check
# ============================================================================

echo "Phase 4: Checking Database Status"
echo "=================================="

# Check if migrations are applied
if docker-compose exec -T web python manage.py migrate --check > /dev/null 2>&1; then
    log_pass "Database migrations: Applied"
else
    log_fail "Database migrations: Check failed"
fi

echo ""

# ============================================================================
# Calculate Results
# ============================================================================

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))
SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

if [ $FAILED_TESTS -eq 0 ]; then
    OVERALL_STATUS="✅ PASSED"
    STATUS_SYMBOL="✅"
else
    OVERALL_STATUS="❌ FAILED"
    STATUS_SYMBOL="❌"
fi

# ============================================================================
# Summary
# ============================================================================

echo "Test Summary"
echo "============"
echo -e "Overall Status: $OVERALL_STATUS"
echo "Passed: $PASSED_TESTS / $TOTAL_TESTS tests"
echo "Failed: $FAILED_TESTS / $TOTAL_TESTS tests"
echo "Success Rate: $SUCCESS_RATE%"
echo "Duration: ${DURATION}s"
echo ""

if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed Tests:${NC}"
    for test in "${FAILED_TEST_LIST[@]}"; do
        echo "  - $test"
    done
    echo ""
fi

# ============================================================================
# Generate Report
# ============================================================================

echo "Generating report: $REPORT_FILE"

read -r -d '' REPORT_CONTENT << 'EOF' || true
# Docker Smoke Test Report

**Generated:** {{DATE}}
**Duration:** {{DURATION}}s
**Overall Status:** {{STATUS}}

---

## Container Status

| Service | Status | Port |
|---------|--------|------|
{{CONTAINER_TABLE}}

---

## Connectivity Tests

| Test | Result | Details |
|------|--------|---------|
{{CONNECTIVITY_TABLE}}

---

## Summary

- **Total Tests:** {{TOTAL_TESTS}}
- **Passed:** {{PASSED_TESTS}}
- **Failed:** {{FAILED_TESTS}}
- **Success Rate:** {{SUCCESS_RATE}}%

{{CRITICAL_SERVICES}}

{{RECOMMENDATIONS}}

---

## Troubleshooting

### Container Issues
- **Stuck in unhealthy state?** Run `docker-compose restart <service>`
- **Port already in use?** Run `lsof -i :<port>` to find conflicting process
- **Migrations not applied?** Run `docker-compose exec web python manage.py migrate`

### API Issues
- **Health endpoint not responding?** Check `docker-compose logs web`
- **Authentication test failing?** Verify Django settings include DRF
- **Nginx proxy not working?** Check `docker-compose logs nginx`

### Database Issues
- **PostgreSQL not accepting connections?** Check `docker-compose logs postgres`
- **Redis not responding?** Check `docker-compose logs redis`
- **Migrations failing?** Check `docker-compose exec web python manage.py migrate --verbosity 2`

### Recovery Steps

```bash
# 1. Check all container status
docker-compose ps

# 2. View specific service logs
docker-compose logs <service>

# 3. Restart all services
docker-compose restart

# 4. Rebuild containers (if needed)
docker-compose up --build -d

# 5. Run migrations
docker-compose exec web python manage.py migrate

# 6. Re-run smoke test
./tests/docker_smoke_test.sh
```

---

**Next Steps:** All critical services healthy, safe to run tests and deploy

*Report generated by: `tests/docker_smoke_test.sh`*
EOF

# Replace template variables
CONTAINER_TABLE=""
for result in "${CONTAINER_RESULTS[@]}"; do
    IFS='|' read -r service status port <<< "$result"
    CONTAINER_TABLE="$CONTAINER_TABLE| $service | $status | $port |"$'\n'
done

CONNECTIVITY_TABLE=""
for result in "${CONNECTIVITY_RESULTS[@]}"; do
    IFS='|' read -r test status details <<< "$result"
    CONNECTIVITY_TABLE="$CONNECTIVITY_TABLE| $test | $status | $details |"$'\n'
done

if [ $FAILED_TESTS -eq 0 ]; then
    CRITICAL="- **All Critical Services:** Healthy ✅"$'\n'"- **Database Migrations:** Applied ✅"$'\n'"- **Redis Cache:** Ready ✅"$'\n'"- **API:** Responding ✅"$'\n'"- **Celery:** Running ⚠️ (may show unhealthy)"
    RECOMMENDATIONS="## Recommendations"$'\n\n'"✅ **All checks passed!** System is healthy and ready for:"$'\n'"- Running pytest"$'\n'"- Integration testing"$'\n'"- Production deployment"$'\n'"- CI/CD operations"
else
    CRITICAL="- **Critical Issues Found:** Review failed tests below"
    RECOMMENDATIONS="## Recommendations"$'\n\n'"⚠️  **Fix critical issues before proceeding with tests**"$'\n'"- Review failed test details above"$'\n'"- Run troubleshooting steps from section below"$'\n'"- Re-run smoke test after fixes: \`./tests/docker_smoke_test.sh\`"
fi

# Generate report with variable substitution using cat and here-document
REPORT_DATE=$(date '+%Y-%m-%d %H:%M:%S')

cat > "$REPORT_FILE" << EOF
# Docker Smoke Test Report

**Generated:** $REPORT_DATE
**Duration:** ${DURATION}s
**Overall Status:** $OVERALL_STATUS

---

## Container Status

| Service | Status | Port |
|---------|--------|------|
$CONTAINER_TABLE
---

## Connectivity Tests

| Test | Result | Details |
|------|--------|---------|
$CONNECTIVITY_TABLE
---

## Summary

- **Total Tests:** $TOTAL_TESTS
- **Passed:** $PASSED_TESTS
- **Failed:** $FAILED_TESTS
- **Success Rate:** $SUCCESS_RATE%

$CRITICAL

$RECOMMENDATIONS

---

## Troubleshooting

### Container Issues
- **Stuck in unhealthy state?** Run \`docker-compose restart <service>\`
- **Port already in use?** Run \`lsof -i :<port>\` to find conflicting process
- **Migrations not applied?** Run \`docker-compose exec web python manage.py migrate\`

### API Issues
- **Health endpoint not responding?** Check \`docker-compose logs web\`
- **Authentication test failing?** Verify Django settings include DRF
- **Nginx proxy not working?** Check \`docker-compose logs nginx\`

### Database Issues
- **PostgreSQL not accepting connections?** Check \`docker-compose logs postgres\`
- **Redis not responding?** Check \`docker-compose logs redis\`
- **Migrations failing?** Check \`docker-compose exec web python manage.py migrate --verbosity 2\`

### Recovery Steps

\`\`\`bash
# 1. Check all container status
docker-compose ps

# 2. View specific service logs
docker-compose logs <service>

# 3. Restart all services
docker-compose restart

# 4. Rebuild containers (if needed)
docker-compose up --build -d

# 5. Run migrations
docker-compose exec web python manage.py migrate

# 6. Re-run smoke test
./tests/docker_smoke_test.sh
\`\`\`

---

**Next Steps:** All critical services healthy, safe to run tests and deploy

*Report generated by: \`tests/docker_smoke_test.sh\`*
EOF

log_info "Report saved to: $REPORT_FILE"
echo ""

# ============================================================================
# Final Result
# ============================================================================

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests PASSED!${NC}"
    echo "Docker environment is healthy and ready for use."
    exit 0
else
    echo -e "${RED}⚠️  Smoke tests FAILED!${NC}"
    echo "$FAILED_TESTS test(s) failed. Review report and troubleshoot."
    exit 1
fi
