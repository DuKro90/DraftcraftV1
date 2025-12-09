# -*- coding: utf-8 -*-
"""Unit tests for transparency models (Phase 4A)."""

import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import IntegrityError

from documents.models import Document, ExtractionResult
from documents.transparency_models import (
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark,
)


@pytest.mark.django_db
class TestCalculationExplanation:
    """Tests for CalculationExplanation model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(username='testuser', password='testpass')

    @pytest.fixture
    def document(self, user):
        """Create test document."""
        return Document.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='completed'
        )

    @pytest.fixture
    def extraction_result(self, document):
        """Create test extraction result."""
        return ExtractionResult.objects.create(
            document=document,
            ocr_text='Test text',
            extracted_data={'holzart': 'eiche', 'oberflaeche': 'geölt'},
            confidence_scores={'holzart': 0.95, 'oberflaeche': 0.88}
        )

    def test_create_explanation_high_confidence(self, extraction_result):
        """Test creating explanation with high confidence."""
        explanation = CalculationExplanation.objects.create(
            extraction_result=extraction_result,
            confidence_level='high',
            confidence_score=Decimal('0.850'),
            total_price_eur=Decimal('2500.00'),
            similar_projects_count=10
        )

        assert explanation.confidence_level == 'high'
        assert explanation.confidence_score == Decimal('0.850')
        assert explanation.total_price_eur == Decimal('2500.00')
        assert explanation.is_high_confidence()
        assert not explanation.requires_manual_review()

    def test_create_explanation_low_confidence(self, extraction_result):
        """Test creating explanation with low confidence."""
        explanation = CalculationExplanation.objects.create(
            extraction_result=extraction_result,
            confidence_level='low',
            confidence_score=Decimal('0.550'),
            total_price_eur=Decimal('2500.00')
        )

        assert explanation.confidence_level == 'low'
        assert not explanation.is_high_confidence()
        assert explanation.requires_manual_review()

    def test_deviation_calculation(self, extraction_result):
        """Test deviation from average calculation."""
        explanation = CalculationExplanation.objects.create(
            extraction_result=extraction_result,
            confidence_level='high',
            confidence_score=Decimal('0.800'),
            total_price_eur=Decimal('2750.00'),
            user_average_for_type=Decimal('2500.00'),
            deviation_from_average_percent=Decimal('10.00')
        )

        direction = explanation.get_deviation_direction()
        assert '↑' in direction
        assert '10.0%' in direction

    def test_one_to_one_constraint(self, extraction_result):
        """Test that one ExtractionResult can only have one Explanation."""
        CalculationExplanation.objects.create(
            extraction_result=extraction_result,
            confidence_level='high',
            confidence_score=Decimal('0.800'),
            total_price_eur=Decimal('2500.00')
        )

        # Attempting to create second explanation should fail
        with pytest.raises(IntegrityError):
            CalculationExplanation.objects.create(
                extraction_result=extraction_result,
                confidence_level='medium',
                confidence_score=Decimal('0.700'),
                total_price_eur=Decimal('2600.00')
            )

    def test_string_representation(self, extraction_result):
        """Test __str__ method."""
        explanation = CalculationExplanation.objects.create(
            extraction_result=extraction_result,
            confidence_level='high',
            confidence_score=Decimal('0.850'),
            total_price_eur=Decimal('2500.00')
        )

        str_repr = str(explanation)
        assert 'test.pdf' in str_repr
        assert 'Hohe Sicherheit' in str_repr


@pytest.mark.django_db
class TestCalculationFactor:
    """Tests for CalculationFactor model."""

    @pytest.fixture
    def explanation(self, extraction_result):
        """Create test explanation."""
        user = User.objects.create_user(username='testuser', password='testpass')
        document = Document.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size_bytes=1024
        )
        extraction = ExtractionResult.objects.create(document=document)
        return CalculationExplanation.objects.create(
            extraction_result=extraction,
            confidence_level='high',
            confidence_score=Decimal('0.800'),
            total_price_eur=Decimal('2500.00')
        )

    def test_create_factor(self, explanation):
        """Test creating a calculation factor."""
        factor = CalculationFactor.objects.create(
            explanation=explanation,
            factor_name='Materialkosten',
            factor_category='material',
            amount_eur=Decimal('1200.00'),
            impact_percent=Decimal('48.00'),
            explanation_text='Eiche-Massivholz: 10 Bretter à 120€',
            data_source='tier2_company',
            is_adjustable=True,
            display_order=0
        )

        assert factor.factor_name == 'Materialkosten'
        assert factor.amount_eur == Decimal('1200.00')
        assert factor.impact_percent == Decimal('48.00')
        assert factor.is_major_factor()  # >10% impact

    def test_minor_factor(self, explanation):
        """Test factor with minor impact."""
        factor = CalculationFactor.objects.create(
            explanation=explanation,
            factor_name='Saisonrabatt',
            factor_category='overhead',
            amount_eur=Decimal('50.00'),
            impact_percent=Decimal('2.00'),
            explanation_text='Winter-Rabatt',
            data_source='tier3_dynamic',
            display_order=5
        )

        assert not factor.is_major_factor()  # <10% impact

    def test_source_badge(self, explanation):
        """Test data source badge generation."""
        factor = CalculationFactor.objects.create(
            explanation=explanation,
            factor_name='Holzart-Aufpreis',
            factor_category='material',
            amount_eur=Decimal('300.00'),
            impact_percent=Decimal('12.00'),
            explanation_text='Eiche: Premium-Hartholz',
            data_source='tier1_global',
            display_order=1
        )

        assert factor.get_source_badge() == 'Standard'

    def test_ordering(self, explanation):
        """Test that factors are ordered by display_order and impact_percent."""
        # Create factors with different orders
        CalculationFactor.objects.create(
            explanation=explanation,
            factor_name='Factor C',
            factor_category='material',
            amount_eur=Decimal('100.00'),
            impact_percent=Decimal('10.00'),
            explanation_text='Test',
            data_source='tier1_global',
            display_order=2
        )
        CalculationFactor.objects.create(
            explanation=explanation,
            factor_name='Factor A',
            factor_category='labor',
            amount_eur=Decimal('500.00'),
            impact_percent=Decimal('50.00'),
            explanation_text='Test',
            data_source='tier2_company',
            display_order=0
        )
        CalculationFactor.objects.create(
            explanation=explanation,
            factor_name='Factor B',
            factor_category='overhead',
            amount_eur=Decimal('200.00'),
            impact_percent=Decimal('20.00'),
            explanation_text='Test',
            data_source='tier2_company',
            display_order=1
        )

        factors = list(explanation.factors.all())
        assert factors[0].factor_name == 'Factor A'  # display_order=0
        assert factors[1].factor_name == 'Factor B'  # display_order=1
        assert factors[2].factor_name == 'Factor C'  # display_order=2


@pytest.mark.django_db
class TestUserProjectBenchmark:
    """Tests for UserProjectBenchmark model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(username='craftsman', password='testpass')

    def test_create_benchmark(self, user):
        """Test creating a benchmark."""
        benchmark = UserProjectBenchmark.objects.create(
            user=user,
            project_type='Badezimmer-Fliesen',
            total_projects=5,
            average_price_eur=Decimal('2500.00'),
            min_price_eur=Decimal('2200.00'),
            max_price_eur=Decimal('2800.00'),
            average_margin_percent=Decimal('21.5')
        )

        assert benchmark.project_type == 'Badezimmer-Fliesen'
        assert benchmark.total_projects == 5
        assert benchmark.has_sufficient_data()  # >= 3 projects

    def test_insufficient_data(self, user):
        """Test benchmark with insufficient data."""
        benchmark = UserProjectBenchmark.objects.create(
            user=user,
            project_type='Küche-Elektrik',
            total_projects=2,
            average_price_eur=Decimal('1500.00'),
            min_price_eur=Decimal('1400.00'),
            max_price_eur=Decimal('1600.00'),
            average_margin_percent=Decimal('18.0')
        )

        assert not benchmark.has_sufficient_data()  # <3 projects

    def test_calculate_deviation(self, user):
        """Test deviation calculation."""
        benchmark = UserProjectBenchmark.objects.create(
            user=user,
            project_type='Test-Project',
            total_projects=10,
            average_price_eur=Decimal('2000.00'),
            min_price_eur=Decimal('1800.00'),
            max_price_eur=Decimal('2200.00'),
            average_margin_percent=Decimal('20.0')
        )

        # Test 10% above average
        deviation = benchmark.calculate_deviation(Decimal('2200.00'))
        assert deviation == Decimal('10.00')

        # Test 10% below average
        deviation = benchmark.calculate_deviation(Decimal('1800.00'))
        assert deviation == Decimal('-10.00')

        # Test exactly at average
        deviation = benchmark.calculate_deviation(Decimal('2000.00'))
        assert deviation == Decimal('0.00')

    def test_unique_user_project_type(self, user):
        """Test that user + project_type must be unique."""
        UserProjectBenchmark.objects.create(
            user=user,
            project_type='Badezimmer',
            total_projects=5,
            average_price_eur=Decimal('2500.00'),
            min_price_eur=Decimal('2200.00'),
            max_price_eur=Decimal('2800.00'),
            average_margin_percent=Decimal('21.0')
        )

        # Attempting to create duplicate should fail
        with pytest.raises(IntegrityError):
            UserProjectBenchmark.objects.create(
                user=user,
                project_type='Badezimmer',
                total_projects=6,
                average_price_eur=Decimal('2600.00'),
                min_price_eur=Decimal('2300.00'),
                max_price_eur=Decimal('2900.00'),
                average_margin_percent=Decimal('22.0')
            )

    def test_price_range_text(self, user):
        """Test price range text generation."""
        benchmark = UserProjectBenchmark.objects.create(
            user=user,
            project_type='Test',
            total_projects=5,
            average_price_eur=Decimal('2500.00'),
            min_price_eur=Decimal('2200.00'),
            max_price_eur=Decimal('2800.00'),
            average_margin_percent=Decimal('20.0')
        )

        price_range = benchmark.get_price_range_text()
        assert '2200.00€' in price_range
        assert '2800.00€' in price_range
