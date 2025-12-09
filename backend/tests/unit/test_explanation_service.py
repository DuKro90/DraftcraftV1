# -*- coding: utf-8 -*-
"""Unit tests for ExplanationService (Phase 4A)."""

import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from unittest.mock import Mock, patch

from documents.models import Document, ExtractionResult
from documents.betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    IndividuelleBetriebskennzahl,
)
from documents.transparency_models import (
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark,
)
from extraction.services.explanation_service import ExplanationService


@pytest.mark.django_db
class TestExplanationService:
    """Tests for ExplanationService."""

    @pytest.fixture
    def user(self):
        """Create test user with betriebskennzahl config."""
        user = User.objects.create_user(username='craftsman', password='testpass')

        # Create template and individual config
        template = BetriebskennzahlTemplate.objects.create(
            name='Test Template',
            version='1.0',
            is_active=True
        )
        IndividuelleBetriebskennzahl.objects.create(
            user=user,
            betrieb_name='Test Handwerk GmbH',
            template=template,
            stundensatz=Decimal('75.00'),
            gemeinkosten_prozent=Decimal('15.0'),
            gewinnmarge_prozent=Decimal('20.0'),
            is_active=True
        )

        return user

    @pytest.fixture
    def document(self, user):
        """Create test document."""
        return Document.objects.create(
            user=user,
            original_filename='angebot.pdf',
            file_size_bytes=2048,
            status='completed'
        )

    @pytest.fixture
    def extraction_result(self, document):
        """Create test extraction result."""
        return ExtractionResult.objects.create(
            document=document,
            ocr_text='Angebot Test',
            extracted_data={
                'holzart': 'eiche',
                'oberflaeche': 'geölt',
                'material_sku': 'EICHE-25MM',
                'raum_typ': 'Badezimmer',
                'arbeitstyp': 'Fliesen'
            },
            confidence_scores={
                'holzart': 0.95,
                'oberflaeche': 0.88,
                'material_sku': 0.92
            }
        )

    @pytest.fixture
    def calculation_result(self):
        """Create mock calculation result."""
        return {
            'total_price_eur': Decimal('2850.00'),
            'breakdown': {
                'material_cost': Decimal('1200.00'),
                'labor_cost': Decimal('900.00'),
                'wood_type_adjustment': Decimal('150.00'),
                'complexity_adjustment': Decimal('200.00'),
                'overhead': Decimal('250.00'),
                'profit_margin': Decimal('150.00'),
                'material_sku': 'EICHE-25MM',
                'quantity': 10,
                'unit_price': Decimal('120.00'),
                'labor_hours': 12,
                'labor_rate_per_hour': Decimal('75.00'),
                'wood_type': 'eiche',
                'wood_factor': Decimal('1.3'),
                'complexity_technique': 'gefräst',
                'complexity_factor': Decimal('1.15')
            },
            'metadata': {
                'similar_projects_count': 8
            }
        }

    def test_create_explanation_high_confidence(self, user, extraction_result, calculation_result):
        """Test creating explanation with high confidence."""
        explainer = ExplanationService(user)
        explanation = explainer.create_explanation(extraction_result, calculation_result)

        assert explanation.total_price_eur == Decimal('2850.00')
        assert explanation.confidence_level in ['high', 'medium', 'low']
        assert explanation.confidence_score >= Decimal('0.0')
        assert explanation.confidence_score <= Decimal('1.0')

    def test_explanation_creates_factors(self, user, extraction_result, calculation_result):
        """Test that explanation creates calculation factors."""
        explainer = ExplanationService(user)
        explanation = explainer.create_explanation(extraction_result, calculation_result)

        factors = explanation.factors.all()
        assert factors.count() > 0

        # Check that factors are sorted by display_order
        display_orders = [f.display_order for f in factors]
        assert display_orders == sorted(display_orders)

    def test_confidence_calculation_complete_data(self, user, extraction_result, calculation_result):
        """Test confidence calculation with complete data."""
        explainer = ExplanationService(user)
        confidence = explainer._calculate_confidence(extraction_result, calculation_result)

        # With good extraction scores, all required fields, and history
        assert confidence >= Decimal('0.7')  # Should be reasonably high

    def test_confidence_calculation_missing_fields(self, user, extraction_result, calculation_result):
        """Test confidence calculation with missing required fields."""
        # Remove required fields
        extraction_result.extracted_data = {'holzart': 'eiche'}  # Missing oberflaeche, material_sku
        extraction_result.save()

        explainer = ExplanationService(user)
        confidence = explainer._calculate_confidence(extraction_result, calculation_result)

        # Confidence should be lower due to missing fields
        assert confidence < Decimal('1.0')

    def test_determine_project_type(self, user):
        """Test project type determination."""
        explainer = ExplanationService(user)

        # Test with full data
        project_type = explainer._determine_project_type({
            'raum_typ': 'Badezimmer',
            'arbeitstyp': 'Fliesen',
            'holzart': 'eiche'
        })
        assert project_type == 'Badezimmer-Fliesen-eiche'

        # Test with partial data
        project_type = explainer._determine_project_type({
            'raum_typ': 'Küche',
            'arbeitstyp': 'Elektrik'
        })
        assert project_type == 'Küche-Elektrik'

        # Test with minimal data
        project_type = explainer._determine_project_type({
            'raum_typ': 'Wohnzimmer'
        })
        assert project_type == 'Wohnzimmer'

    def test_update_benchmark_first_project(self, user):
        """Test benchmark update for first project of type."""
        explainer = ExplanationService(user)

        benchmark = explainer.update_benchmark_after_completion(
            'Badezimmer-Fliesen',
            Decimal('2850.00'),
            Decimal('21.5')
        )

        assert benchmark.total_projects == 1
        assert benchmark.average_price_eur == Decimal('2850.00')
        assert benchmark.min_price_eur == Decimal('2850.00')
        assert benchmark.max_price_eur == Decimal('2850.00')
        assert benchmark.average_margin_percent == Decimal('21.5')

    def test_update_benchmark_multiple_projects(self, user):
        """Test benchmark update with existing projects."""
        explainer = ExplanationService(user)

        # Create initial benchmark
        UserProjectBenchmark.objects.create(
            user=user,
            project_type='Badezimmer-Fliesen',
            total_projects=2,
            average_price_eur=Decimal('2500.00'),
            min_price_eur=Decimal('2400.00'),
            max_price_eur=Decimal('2600.00'),
            average_margin_percent=Decimal('20.0')
        )

        # Add new project
        benchmark = explainer.update_benchmark_after_completion(
            'Badezimmer-Fliesen',
            Decimal('2850.00'),  # Higher than previous
            Decimal('22.0')
        )

        assert benchmark.total_projects == 3
        # Average should increase
        assert benchmark.average_price_eur > Decimal('2500.00')
        # Max should update
        assert benchmark.max_price_eur == Decimal('2850.00')
        # Min should stay same
        assert benchmark.min_price_eur == Decimal('2400.00')

    def test_factor_explanations_handwerker_sprache(self, user, extraction_result, calculation_result):
        """Test that factor explanations use craftsman-friendly language."""
        explainer = ExplanationService(user)
        explanation = explainer.create_explanation(extraction_result, calculation_result)

        factors = explanation.factors.all()

        # Check that German terms are used
        factor_names = [f.factor_name for f in factors]
        assert any('Material' in name or 'Zeit' in name or 'Holz' in name for name in factor_names)

        # Check explanations are in German
        for factor in factors:
            assert factor.explanation_text  # Not empty
            # Should contain German terms, not technical jargon
            assert not 'labor_hours' in factor.explanation_text.lower()
            assert not 'unit_price' in factor.explanation_text.lower()

    def test_missing_calculation_result_raises_error(self, user, extraction_result):
        """Test that missing total_price_eur raises ValueError."""
        explainer = ExplanationService(user)

        invalid_result = {'breakdown': {}}  # Missing total_price_eur

        with pytest.raises(ValueError, match='total_price_eur'):
            explainer.create_explanation(extraction_result, invalid_result)

    def test_explanation_with_benchmark_comparison(self, user, extraction_result, calculation_result):
        """Test explanation with existing benchmark for comparison."""
        # Create existing benchmark
        UserProjectBenchmark.objects.create(
            user=user,
            project_type='Badezimmer-Fliesen',
            total_projects=10,
            average_price_eur=Decimal('2600.00'),
            min_price_eur=Decimal('2400.00'),
            max_price_eur=Decimal('2800.00'),
            average_margin_percent=Decimal('20.0')
        )

        explainer = ExplanationService(user)
        explanation = explainer.create_explanation(extraction_result, calculation_result)

        # Should have comparison data
        assert explanation.similar_projects_count == 10
        assert explanation.user_average_for_type == Decimal('2600.00')
        assert explanation.deviation_from_average_percent is not None

    def test_get_confidence_level_thresholds(self, user):
        """Test confidence level determination thresholds."""
        explainer = ExplanationService(user)

        assert explainer._get_confidence_level(Decimal('0.85')) == 'high'
        assert explainer._get_confidence_level(Decimal('0.80')) == 'high'
        assert explainer._get_confidence_level(Decimal('0.79')) == 'medium'
        assert explainer._get_confidence_level(Decimal('0.65')) == 'medium'
        assert explainer._get_confidence_level(Decimal('0.59')) == 'low'
        assert explainer._get_confidence_level(Decimal('0.30')) == 'low'
