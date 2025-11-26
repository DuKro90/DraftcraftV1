"""Pytest configuration and shared fixtures."""
import os
import django
import pytest
from django.conf import settings

# Setup Django before running tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """Create test user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def authenticated_api_client(authenticated_user):
    """API client with authenticated user."""
    client = APIClient()
    client.force_authenticate(user=authenticated_user)
    return client


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )
    return user


@pytest.fixture
def admin_api_client(admin_user):
    """API client with admin user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF for testing."""
    return 'tests/fixtures/sample_invoice.pdf'


@pytest.fixture
def sample_gaeb_xml_path():
    """Path to sample GAEB XML for testing."""
    return 'tests/fixtures/sample_gaeb.xml'
