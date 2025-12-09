"""
API Tests for Calculation Endpoints - Phase 4D

Tests for:
- POST /api/v1/calculate/price/
- POST /api/v1/calculate/multi-material/
- GET /api/v1/pauschalen/applicable/
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from documents.models import Document, ExtractionResult
from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    IndividuelleBetriebskennzahl,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
)
from documents.models_pauschalen import BetriebspauschaleRegel


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def betriebskennzahl_template(db):
    """Create Betriebskennzahl template with TIER 1 factors."""
    template = BetriebskennzahlTemplate.objects.create(
        name='Test Template',
        version='1.0',
        description='Test template for unit tests',
        is_active=True
    )

    # Add Holzart factors
    HolzartKennzahl.objects.create(
        template=template,
        holzart='eiche',
        display_name='Eiche',
        preis_faktor=Decimal('1.30'),
        kategorie='hartholz',
        is_enabled=True
    )
    HolzartKennzahl.objects.create(
        template=template,
        holzart='buche',
        display_name='Buche',
        preis_faktor=Decimal('1.20'),
        kategorie='hartholz',
        is_enabled=True
    )

    # Add Oberflächenbearbeitung factors
    OberflächenbearbeitungKennzahl.objects.create(
        template=template,
        bearbeitung='lackieren',
        display_name='Lackieren',
        preis_faktor=Decimal('1.15'),
        zeit_faktor=Decimal('1.20'),
        kategorie='premium',
        is_enabled=True
    )

    # Add Komplexität factors
    KomplexitaetKennzahl.objects.create(
        template=template,
        technik='hand_geschnitzt',
        display_name='Handgeschnitzt',
        preis_faktor=Decimal('2.0'),
        zeit_faktor=Decimal('2.5'),
        schwierigkeitsgrad='hoch',
        kategorie='handwerk',
        is_enabled=True
    )

    return template


@pytest.fixture
def user_config(db, test_user, betriebskennzahl_template):
    """Create user's Betriebskennzahl configuration."""
    return IndividuelleBetriebskennzahl.objects.create(
        user=test_user,
        handwerk_template=betriebskennzahl_template,
        stundensatz_arbeit=Decimal('65.00'),
        gewinnmarge_prozent=Decimal('20.00'),
        betriebskosten_umlage=Decimal('500.00'),
        use_handwerk_standard=True,
        use_custom_materials=False,
        use_seasonal_adjustments=False,
        use_customer_discounts=True,
        use_bulk_discounts=False,
        is_active=True
    )


@pytest.fixture
def test_pauschale(db, test_user):
    """Create test Pauschale rule."""
    return BetriebspauschaleRegel.objects.create(
        user=test_user,
        name='Anfahrt Standard',
        pauschale_typ='anfahrt',
        beschreibung='Standard Anfahrtspauschale',
        berechnungsart='fest',
        betrag=Decimal('50.00'),
        einheit='eur',
        is_active=True
    )


@pytest.mark.django_db
class TestPriceCalculationAPI:
    """Tests for POST /api/v1/calculate/price/"""

    def test_calculate_price_success(self, api_client, test_user, user_config, test_pauschale):
        """Test successful price calculation."""
        # Authenticate
        api_client.force_authenticate(user=test_user)

        # Prepare request data
        data = {
            'extracted_data': {
                'holzart': 'eiche',
                'oberflaeche': 'lackieren',
                'komplexitaet': 'hand_geschnitzt',
                'material_quantity': 10,
                'labor_hours': 40,
                'material_cost_eur': 100.00,
            },
            'customer_type': 'bestehende_kunden',
            'breakdown': True
        }

        # Make request
        url = reverse('api-v1:calculate-price')
        response = api_client.post(url, data, format='json')

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert 'total_price_eur' in response.data
        assert 'base_price_eur' in response.data
        assert 'labor_price_eur' in response.data
        assert 'pauschalen' in response.data
        assert 'breakdown' in response.data
        assert 'tiers_applied' in response.data

        # Check TIER application
        assert response.data['tiers_applied']['tier_1_global'] is True
        assert response.data['tiers_applied']['tier_2_company'] is True

        # Check Pauschalen was applied
        assert response.data['pauschalen']['total'] > 0

        # Check labor calculation
        expected_labor = Decimal('65.00') * 40  # 2600
        assert Decimal(str(response.data['labor_price_eur'])) == expected_labor

    def test_calculate_price_without_config(self, api_client, test_user):
        """Test price calculation fails without Betriebskennzahl config."""
        # Authenticate user without config
        api_client.force_authenticate(user=test_user)

        data = {
            'extracted_data': {
                'holzart': 'eiche',
                'material_cost_eur': 100.00,
            },
            'breakdown': True
        }

        url = reverse('api-v1:calculate-price')
        response = api_client.post(url, data, format='json')

        # Should fail due to HasActiveBetriebskennzahl permission
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_calculate_price_unauthenticated(self, api_client):
        """Test price calculation requires authentication."""
        data = {
            'extracted_data': {'holzart': 'eiche'},
            'breakdown': True
        }

        url = reverse('api-v1:calculate-price')
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_calculate_price_invalid_customer_type(self, api_client, test_user, user_config):
        """Test validation for invalid customer type."""
        api_client.force_authenticate(user=test_user)

        data = {
            'extracted_data': {'holzart': 'eiche'},
            'customer_type': 'invalid_type',  # Invalid
            'breakdown': True
        }

        url = reverse('api-v1:calculate-price')
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'customer_type' in response.data

    def test_calculate_price_with_extraction_result(self, api_client, test_user, user_config, test_pauschale):
        """Test price calculation linked to ExtractionResult."""
        api_client.force_authenticate(user=test_user)

        # Create document and extraction result
        document = Document.objects.create(
            user=test_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1000,
            status='completed'
        )

        extraction_result = ExtractionResult.objects.create(
            document=document,
            ocr_text='Test OCR text',
            confidence_scores={'ocr': 0.95},
            processing_time_ms=1000,
            extracted_data={}
        )

        data = {
            'extracted_data': {
                'holzart': 'eiche',
                'material_cost_eur': 100.00,
                'labor_hours': 10,
            },
            'extraction_result_id': str(extraction_result.id),
            'breakdown': True
        }

        url = reverse('api-v1:calculate-price')
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        # Pauschalen should be applied with context
        assert 'pauschalen' in response.data

    def test_calculate_price_breakdown_disabled(self, api_client, test_user, user_config):
        """Test price calculation without breakdown."""
        api_client.force_authenticate(user=test_user)

        data = {
            'extracted_data': {
                'holzart': 'eiche',
                'material_cost_eur': 100.00,
            },
            'breakdown': False
        }

        url = reverse('api-v1:calculate-price')
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['breakdown'] == {}


@pytest.mark.django_db
class TestMultiMaterialCalculationAPI:
    """Tests for POST /api/v1/calculate/multi-material/"""

    def test_multi_material_success(self, api_client, test_user, user_config):
        """Test successful multi-material calculation."""
        api_client.force_authenticate(user=test_user)

        data = {
            'materials': [
                {
                    'holzart': 'eiche',
                    'oberflaeche': 'lackieren',
                    'laenge_mm': 2000,
                    'breite_mm': 800,
                    'hoehe_mm': 25,
                    'menge': 4
                },
                {
                    'holzart': 'buche',
                    'oberflaeche': 'lackieren',
                    'laenge_mm': 1500,
                    'breite_mm': 600,
                    'hoehe_mm': 18,
                    'menge': 8
                }
            ],
            'customer_type': 'neue_kunden',
            'breakdown': True
        }

        url = reverse('api-v1:calculate-multi-material')
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_material_cost' in response.data
        assert 'material_breakdown' in response.data
        assert len(response.data['material_breakdown']) == 2

    def test_multi_material_missing_required_fields(self, api_client, test_user, user_config):
        """Test validation for missing required fields."""
        api_client.force_authenticate(user=test_user)

        data = {
            'materials': [
                {
                    'holzart': 'eiche',
                    # Missing dimensions
                }
            ]
        }

        url = reverse('api-v1:calculate-multi-material')
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'materials' in response.data

    def test_multi_material_invalid_dimensions(self, api_client, test_user, user_config):
        """Test validation for invalid dimensions."""
        api_client.force_authenticate(user=test_user)

        data = {
            'materials': [
                {
                    'holzart': 'eiche',
                    'laenge_mm': -100,  # Invalid negative
                    'breite_mm': 800,
                    'hoehe_mm': 25,
                }
            ]
        }

        url = reverse('api-v1:calculate-multi-material')
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestApplicablePauschaleAPI:
    """Tests for GET /api/v1/pauschalen/applicable/"""

    def test_get_applicable_pauschalen(self, api_client, test_user, user_config, test_pauschale):
        """Test getting applicable Pauschalen."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:pauschalen-applicable')
        response = api_client.get(url, {
            'auftragswert': 5000,
            'distanz_km': 30,
        })

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Check first Pauschale
        pauschale = response.data[0]
        assert 'regel_id' in pauschale
        assert 'name' in pauschale
        assert 'applies' in pauschale
        assert pauschale['name'] == 'Anfahrt Standard'
        assert pauschale['applies'] is True
        assert pauschale['calculated_amount_eur'] == 50.00

    def test_applicable_pauschalen_no_context(self, api_client, test_user, user_config, test_pauschale):
        """Test getting Pauschalen without context parameters."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:pauschalen-applicable')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_applicable_pauschalen_unauthenticated(self, api_client):
        """Test requires authentication."""
        url = reverse('api-v1:pauschalen-applicable')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_applicable_pauschalen_filters_inactive(self, api_client, test_user, user_config):
        """Test that inactive Pauschalen are not returned."""
        api_client.force_authenticate(user=test_user)

        # Create inactive Pauschale
        BetriebspauschaleRegel.objects.create(
            user=test_user,
            name='Inactive Pauschale',
            pauschale_typ='montage',
            berechnungsart='fest',
            betrag=Decimal('100.00'),
            is_active=False  # Inactive
        )

        url = reverse('api-v1:pauschalen-applicable')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should not include inactive Pauschale
        pauschale_names = [p['name'] for p in response.data]
        assert 'Inactive Pauschale' not in pauschale_names
