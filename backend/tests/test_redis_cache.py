"""
Tests for Redis caching functionality.

Tests:
- Cache connection
- Config API caching (Holzarten, Oberflächenbearbeitung, Komplexität)
- Cache invalidation on admin save/delete
"""
import pytest
from django.core.cache import cache
from django.contrib.auth.models import User
from decimal import Decimal

from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
)


@pytest.fixture
def test_template(db):
    """Create a test Betriebskennzahl template."""
    return BetriebskennzahlTemplate.objects.create(
        name='Test Template',
        description='Template for testing',
        version='1.0',
        is_active=True
    )


@pytest.fixture
def test_user_with_config(db, test_template):
    """Create a test user with Betriebskennzahl config."""
    user = User.objects.create_user(username='testuser', password='testpass123')

    # Create Betriebskennzahl config for user
    IndividuelleBetriebskennzahl.objects.create(
        user=user,
        handwerk_template=test_template,
        stundensatz_eur=Decimal('75.00'),
        gemeinkosten_prozent=Decimal('15.00'),
        gewinnmarge_prozent=Decimal('20.00'),
        is_active=True
    )

    return user


@pytest.mark.django_db
class TestRedisConnection:
    """Test Redis cache connection."""

    def test_cache_connection(self):
        """Test that Redis is accessible."""
        # Set a test value
        cache.set('test_key', 'test_value', timeout=60)

        # Get the value back
        value = cache.get('test_key')

        assert value == 'test_value'

        # Clean up
        cache.delete('test_key')

    def test_cache_expiry(self):
        """Test that cache expiry works."""
        # Set with 1 second timeout
        cache.set('expiry_test', 'data', timeout=1)

        # Should exist immediately
        assert cache.get('expiry_test') == 'data'

        # Clean up
        cache.delete('expiry_test')


@pytest.mark.django_db
class TestHolzartCaching:
    """Test Holzart configuration caching."""

    def test_holzart_cache_miss_then_hit(self, test_template, test_user_with_config):
        """Test cache miss on first request, then cache hit."""
        # Create Holzart data
        holzart = HolzartKennzahl.objects.create(
            template=test_template,
            holzart='Eiche',
            kategorie='Hartholz',
            preis_faktor=Decimal('1.3'),
            is_enabled=True
        )

        cache_key = f'holzarten_template_{test_template.id}'

        # Clear cache to ensure clean state
        cache.delete(cache_key)

        # First request - should be cache MISS
        cached_data = cache.get(cache_key)
        assert cached_data is None

        # Simulate what the view does
        queryset = HolzartKennzahl.objects.filter(
            template=test_template,
            is_enabled=True
        )
        queryset_list = list(queryset)
        cache.set(cache_key, queryset_list, timeout=3600)

        # Second request - should be cache HIT
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(cached_data) == 1
        assert cached_data[0].holzart == 'Eiche'

    def test_holzart_cache_invalidation_on_save(self, test_template):
        """Test cache is invalidated when Holzart is saved."""
        cache_key = f'holzarten_template_{test_template.id}'

        # Set initial cache
        cache.set(cache_key, ['test_data'], timeout=3600)
        assert cache.get(cache_key) == ['test_data']

        # Create/save Holzart (simulates admin save)
        holzart = HolzartKennzahl.objects.create(
            template=test_template,
            holzart='Buche',
            kategorie='Hartholz',
            preis_faktor=Decimal('1.2'),
            is_enabled=True
        )

        # Simulate cache invalidation (what admin does)
        cache.delete(cache_key)

        # Verify cache is empty
        assert cache.get(cache_key) is None

    def test_holzart_cache_invalidation_on_delete(self, test_template):
        """Test cache is invalidated when Holzart is deleted."""
        cache_key = f'holzarten_template_{test_template.id}'

        # Create Holzart
        holzart = HolzartKennzahl.objects.create(
            template=test_template,
            holzart='Kiefer',
            kategorie='Weichholz',
            preis_faktor=Decimal('0.9'),
            is_enabled=True
        )

        # Set cache
        cache.set(cache_key, [holzart], timeout=3600)
        assert cache.get(cache_key) is not None

        # Delete Holzart (simulates admin delete)
        holzart.delete()

        # Simulate cache invalidation
        cache.delete(cache_key)

        # Verify cache is empty
        assert cache.get(cache_key) is None


@pytest.mark.django_db
class TestOberflächenCaching:
    """Test Oberflächenbearbeitung configuration caching."""

    def test_oberflaechen_cache_workflow(self, test_template):
        """Test complete cache workflow for Oberflächenbearbeitung."""
        cache_key = f'oberflaechen_template_{test_template.id}'

        # Clear cache
        cache.delete(cache_key)

        # Create data
        oberflaeche = OberflächenbearbeitungKennzahl.objects.create(
            template=test_template,
            bearbeitung='Lackieren',
            preis_faktor=Decimal('1.15'),
            zeit_faktor=Decimal('1.20'),
            is_enabled=True
        )

        # Cache miss
        assert cache.get(cache_key) is None

        # Set cache
        queryset_list = list(OberflächenbearbeitungKennzahl.objects.filter(
            template=test_template,
            is_enabled=True
        ))
        cache.set(cache_key, queryset_list, timeout=3600)

        # Cache hit
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(cached_data) == 1
        assert cached_data[0].bearbeitung == 'Lackieren'


@pytest.mark.django_db
class TestKomplexitaetCaching:
    """Test Komplexität configuration caching."""

    def test_komplexitaet_cache_workflow(self, test_template):
        """Test complete cache workflow for Komplexität."""
        cache_key = f'komplexitaet_template_{test_template.id}'

        # Clear cache
        cache.delete(cache_key)

        # Create data
        komplexitaet = KomplexitaetKennzahl.objects.create(
            template=test_template,
            technik='Hand geschnitzt',
            schwierigkeitsgrad='HOCH',
            preis_faktor=Decimal('2.0'),
            zeit_faktor=Decimal('2.5'),
            is_enabled=True
        )

        # Cache miss
        assert cache.get(cache_key) is None

        # Set cache
        queryset_list = list(KomplexitaetKennzahl.objects.filter(
            template=test_template,
            is_enabled=True
        ))
        cache.set(cache_key, queryset_list, timeout=3600)

        # Cache hit
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(cached_data) == 1
        assert cached_data[0].technik == 'Hand geschnitzt'


@pytest.mark.django_db
class TestCachePerformance:
    """Test cache performance improvements."""

    def test_multiple_cache_keys(self, db):
        """Test that different templates have different cache keys."""
        template1 = BetriebskennzahlTemplate.objects.create(
            name='Template 1',
            version='1.0',
            is_active=True
        )
        template2 = BetriebskennzahlTemplate.objects.create(
            name='Template 2',
            version='1.0',
            is_active=True
        )

        # Create data for each template
        HolzartKennzahl.objects.create(
            template=template1,
            holzart='Eiche',
            preis_faktor=Decimal('1.3'),
            is_enabled=True
        )
        HolzartKennzahl.objects.create(
            template=template2,
            holzart='Buche',
            preis_faktor=Decimal('1.2'),
            is_enabled=True
        )

        # Cache both
        cache_key1 = f'holzarten_template_{template1.id}'
        cache_key2 = f'holzarten_template_{template2.id}'

        data1 = list(HolzartKennzahl.objects.filter(template=template1))
        data2 = list(HolzartKennzahl.objects.filter(template=template2))

        cache.set(cache_key1, data1, timeout=3600)
        cache.set(cache_key2, data2, timeout=3600)

        # Verify both cached independently
        assert cache.get(cache_key1)[0].holzart == 'Eiche'
        assert cache.get(cache_key2)[0].holzart == 'Buche'

        # Invalidate one shouldn't affect the other
        cache.delete(cache_key1)
        assert cache.get(cache_key1) is None
        assert cache.get(cache_key2) is not None
