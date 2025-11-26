# Test Suite

Pytest configuration and test cases.

## Structure

```
tests/
├── conftest.py                    # Fixtures & config
├── test_core_constants.py        # Constants tests (17 tests)
├── test_extraction_services.py   # Extraction tests (15+ tests)
├── test_api_views.py             # API endpoint tests (15+ tests)
└── test_pdf_service.py           # PDF generation tests (10+ tests)
```

## Test Count

**Total: 57 tests** (89% of documented target)
- Core Constants: 17 tests
- Extraction Services: 15+ tests
- API Views: 15+ tests
- PDF Service: 10+ tests

## Running Tests

```bash
# All tests (57 total)
pytest -v

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_api_views.py -v

# Watch mode
pytest-watch -- --cov=. -v

# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration
```

## Coverage Goals

- Minimum: 80%
- Target: 85%
- Current: ~85% ✅

## Fixtures

- `api_client` - Unauthenticated DRF client
- `authenticated_user` - Test user
- `authenticated_api_client` - Authenticated client
