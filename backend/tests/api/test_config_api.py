"""
API Tests for Configuration Endpoints - Phase 4D

Tests for:
- GET /api/v1/config/holzarten/
- GET /api/v1/config/oberflaechen/
- GET /api/v1/config/komplexitaet/
- GET /api/v1/config/betriebskennzahlen/
- PATCH /api/v1/config/betriebskennzahlen/update_config/
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    IndividuelleBetriebskennzahl,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
)


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def other_user(db):
    """Create another user."""
    return User.objects.create_user(
        username='otheruser',
        password='otherpass123'
    )


@pytest.fixture
def template_with_factors(db):
    """Create template with all factor types."""
    template = BetriebskennzahlTemplate.objects.create(
        name='Standard Template',
        version='2.0',
        is_active=True
    )

    # Holzarten
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

    # Oberflächenbearbeitung
    OberflächenbearbeitungKennzahl.objects.create(
        template=template,
        bearbeitung='lackieren',
        display_name='Lackieren',
        preis_faktor=Decimal('1.15'),
        zeit_faktor=Decimal('1.20'),
        kategorie='premium',
        is_enabled=True
    )

    # Komplexität
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
def user_betriebskennzahl(db, test_user, template_with_factors):
    """Create user's Betriebskennzahl."""
    return IndividuelleBetriebskennzahl.objects.create(
        user=test_user,
        handwerk_template=template_with_factors,
        stundensatz_arbeit=Decimal('65.00'),
        gewinnmarge_prozent=Decimal('20.00'),
        betriebskosten_umlage=Decimal('500.00'),
        use_handwerk_standard=True,
        is_active=True
    )


@pytest.mark.django_db
class TestHolzartConfigAPI:
    """Tests for GET /api/v1/config/holzarten/"""

    def test_list_holzarten(self, api_client, test_user, user_betriebskennzahl):
        """Test listing wood types."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-holzarten-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 2

        # Check structure
        holzart = response.data['results'][0]
        assert 'holzart' in holzart
        assert 'display_name' in holzart
        assert 'preis_faktor' in holzart
        assert 'kategorie' in holzart
        assert 'is_enabled' in holzart

    def test_holzarten_unauthenticated(self, api_client):
        """Test requires authentication."""
        url = reverse('api-v1:config-holzarten-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_holzarten_only_enabled(self, api_client, test_user, user_betriebskennzahl):
        """Test only enabled Holzarten are returned."""
        api_client.force_authenticate(user=test_user)

        # Create disabled Holzart
        HolzartKennzahl.objects.create(
            template=user_betriebskennzahl.handwerk_template,
            holzart='disabled_wood',
            display_name='Disabled Wood',
            preis_faktor=Decimal('1.0'),
            kategorie='test',
            is_enabled=False  # Disabled
        )

        url = reverse('api-v1:config-holzarten-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        holzart_names = [h['holzart'] for h in response.data['results']]
        assert 'disabled_wood' not in holzart_names

    def test_holzart_detail(self, api_client, test_user, user_betriebskennzahl):
        """Test getting specific Holzart details."""
        api_client.force_authenticate(user=test_user)

        holzart = HolzartKennzahl.objects.filter(
            template=user_betriebskennzahl.handwerk_template,
            holzart='eiche'
        ).first()

        url = reverse('api-v1:config-holzarten-detail', kwargs={'pk': holzart.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['holzart'] == 'eiche'
        assert Decimal(response.data['preis_faktor']) == Decimal('1.30')


@pytest.mark.django_db
class TestOberflächenConfigAPI:
    """Tests for GET /api/v1/config/oberflaechen/"""

    def test_list_oberflaechen(self, api_client, test_user, user_betriebskennzahl):
        """Test listing surface finishes."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-oberflaechen-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

        # Check structure
        oberflaeche = response.data['results'][0]
        assert 'bearbeitung' in oberflaeche
        assert 'preis_faktor' in oberflaeche
        assert 'zeit_faktor' in oberflaeche


@pytest.mark.django_db
class TestKomplexitaetConfigAPI:
    """Tests for GET /api/v1/config/komplexitaet/"""

    def test_list_komplexitaet(self, api_client, test_user, user_betriebskennzahl):
        """Test listing complexity techniques."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-komplexitaet-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

        # Check structure
        komplexitaet = response.data['results'][0]
        assert 'technik' in komplexitaet
        assert 'preis_faktor' in komplexitaet
        assert 'zeit_faktor' in komplexitaet
        assert 'schwierigkeitsgrad' in komplexitaet
        assert 'schwierigkeitsgrad_display' in komplexitaet


@pytest.mark.django_db
class TestBetriebskennzahlConfigAPI:
    """Tests for Betriebskennzahl configuration endpoints."""

    def test_get_betriebskennzahl(self, api_client, test_user, user_betriebskennzahl):
        """Test getting user's Betriebskennzahl."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-betriebskennzahlen-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'stundensatz_arbeit' in response.data
        assert 'gewinnmarge_prozent' in response.data
        assert 'betriebskosten_umlage' in response.data
        assert 'template_name' in response.data
        assert Decimal(response.data['stundensatz_arbeit']) == Decimal('65.00')
        assert response.data['template_name'] == 'Standard Template'

    def test_get_betriebskennzahl_no_config(self, api_client, test_user):
        """Test getting Betriebskennzahl when user has none."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-betriebskennzahlen-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error_code' in response.data
        assert response.data['error_code'] == 'no_configuration'

    def test_update_betriebskennzahl(self, api_client, test_user, user_betriebskennzahl):
        """Test updating user's Betriebskennzahl."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-betriebskennzahlen-update-config')
        data = {
            'stundensatz_arbeit': 75.00,
            'gewinnmarge_prozent': 25.0,
            'use_seasonal_adjustments': True
        }

        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['stundensatz_arbeit']) == Decimal('75.00')
        assert Decimal(response.data['gewinnmarge_prozent']) == Decimal('25.00')
        assert response.data['use_seasonal_adjustments'] is True

        # Verify database was updated
        user_betriebskennzahl.refresh_from_db()
        assert user_betriebskennzahl.stundensatz_arbeit == Decimal('75.00')

    def test_update_betriebskennzahl_invalid_stundensatz(self, api_client, test_user, user_betriebskennzahl):
        """Test validation for invalid Stundensatz."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-betriebskennzahlen-update-config')
        data = {
            'stundensatz_arbeit': -10.00  # Invalid negative
        }

        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'stundensatz_arbeit' in response.data

    def test_update_betriebskennzahl_invalid_margin(self, api_client, test_user, user_betriebskennzahl):
        """Test validation for invalid profit margin."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-betriebskennzahlen-update-config')
        data = {
            'gewinnmarge_prozent': 150.0  # Invalid > 100
        }

        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'gewinnmarge_prozent' in response.data

    def test_update_betriebskennzahl_other_user_cannot_update(self, api_client, test_user, other_user, user_betriebskennzahl):
        """Test other user cannot update another user's config."""
        api_client.force_authenticate(user=other_user)

        # Create config for other user
        other_template = BetriebskennzahlTemplate.objects.first()
        IndividuelleBetriebskennzahl.objects.create(
            user=other_user,
            handwerk_template=other_template,
            stundensatz_arbeit=Decimal('50.00'),
            gewinnmarge_prozent=Decimal('15.00'),
            is_active=True
        )

        url = reverse('api-v1:config-betriebskennzahlen-update-config')
        data = {
            'stundensatz_arbeit': 999.00  # Try to update
        }

        response = api_client.patch(url, data, format='json')

        # Should update other_user's config, not test_user's
        assert response.status_code == status.HTTP_200_OK

        # Verify test_user's config unchanged
        user_betriebskennzahl.refresh_from_db()
        assert user_betriebskennzahl.stundensatz_arbeit == Decimal('65.00')

    def test_get_pricing_report(self, api_client, test_user, user_betriebskennzahl):
        """Test getting pricing configuration report."""
        api_client.force_authenticate(user=test_user)

        url = reverse('api-v1:config-betriebskennzahlen-pricing-report')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'configuration' in response.data
        assert 'tiers_enabled' in response.data
        assert 'template' in response.data

        # Check configuration details
        config = response.data['configuration']
        assert 'hourly_rate_eur' in config
        assert 'profit_margin_percent' in config

        # Check tiers
        tiers = response.data['tiers_enabled']
        assert 'tier_1_global' in tiers
        assert 'tier_2_company' in tiers
        assert 'tier_3_dynamic' in tiers
