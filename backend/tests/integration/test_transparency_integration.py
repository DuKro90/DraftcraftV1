# -*- coding: utf-8 -*-
"""Integration tests for Phase 4A Transparency features."""

import pytest
from decimal import Decimal
from django.contrib.auth.models import User

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
from extraction.services.integrated_pipeline import IntegratedExtractionPipeline
from extraction.services.explanation_service import ExplanationService


@pytest.mark.django_db
class TestTransparencyIntegration:
    """Integration tests for complete transparency workflow."""

    @pytest.fixture
    def user_with_config(self):
        """Create user with complete betriebskennzahl configuration."""
        user = User.objects.create_user(username='meister_mueller', password='testpass')

        # Create template
        template = BetriebskennzahlTemplate.objects.create(
            name='Standard Schreinerei 2024',
            version='1.0',
            is_active=True
        )

        # Create individual config
        IndividuelleBetriebskennzahl.objects.create(
            user=user,
            betrieb_name='Schreinerei Müller GmbH',
            template=template,
            stundensatz=Decimal('75.00'),
            gemeinkosten_prozent=Decimal('15.0'),
            gewinnmarge_prozent=Decimal('20.0'),
            is_active=True
        )

        return user

    @pytest.fixture
    def document_with_extraction(self, user_with_config):
        """Create document with extraction result."""
        document = Document.objects.create(
            user=user_with_config,
            original_filename='angebot_badezimmer.pdf',
            file_size_bytes=4096,
            status='completed'
        )

        extraction = ExtractionResult.objects.create(
            document=document,
            ocr_text='Angebot Badezimmer Fliesenarbeiten',
            extracted_data={
                'holzart': 'eiche',
                'oberflaeche': 'geölt',
                'material_sku': 'EICHE-25MM-PREMIUM',
                'raum_typ': 'Badezimmer',
                'arbeitstyp': 'Fliesen',
                'quantity': 15,
                'labor_hours': 20
            },
            confidence_scores={
                'holzart': 0.94,
                'oberflaeche': 0.89,
                'material_sku': 0.91,
                'quantity': 0.87
            }
        )

        return document, extraction

    def test_complete_pipeline_with_explanation(self, user_with_config, document_with_extraction):
        """Test complete pipeline from extraction to explanation."""
        document, extraction = document_with_extraction

        # Initialize pipeline
        pipeline = IntegratedExtractionPipeline(user_with_config)

        # Process extraction (without actual pricing since we don't have full setup)
        # This is a simplified test - full test would need MateriallistePosition etc.

        # Manually create explanation to test the flow
        explainer = ExplanationService(user_with_config)

        mock_calculation = {
            'total_price_eur': Decimal('3200.00'),
            'breakdown': {
                'material_cost': Decimal('1500.00'),
                'labor_cost': Decimal('1000.00'),
                'overhead': Decimal('300.00'),
                'profit_margin': Decimal('400.00'),
                'material_sku': 'EICHE-25MM-PREMIUM',
                'quantity': 15,
                'unit_price': Decimal('100.00'),
                'labor_hours': 20,
                'labor_rate_per_hour': Decimal('50.00')
            },
            'metadata': {
                'similar_projects_count': 5
            }
        }

        explanation = explainer.create_explanation(extraction, mock_calculation)

        # Verify explanation was created
        assert explanation is not None
        assert explanation.total_price_eur == Decimal('3200.00')
        assert explanation.extraction_result == extraction

        # Verify factors were created
        factors = explanation.factors.all()
        assert factors.count() >= 2  # At least material and labor

        # Verify Progressive Disclosure - factors sorted by impact
        first_factor = factors.first()
        assert first_factor.display_order == 0

    def test_benchmark_creation_and_update_workflow(self, user_with_config, document_with_extraction):
        """Test benchmark creation and incremental update workflow."""
        document, extraction = document_with_extraction

        explainer = ExplanationService(user_with_config)

        # First project - benchmark should be created
        benchmark1 = explainer.update_benchmark_after_completion(
            'Badezimmer-Fliesen',
            Decimal('2800.00'),
            Decimal('20.0')
        )

        assert benchmark1.total_projects == 1
        assert benchmark1.average_price_eur == Decimal('2800.00')

        # Second project - benchmark should be updated
        benchmark2 = explainer.update_benchmark_after_completion(
            'Badezimmer-Fliesen',
            Decimal('3200.00'),
            Decimal('22.0')
        )

        assert benchmark2.id == benchmark1.id  # Same benchmark object
        assert benchmark2.total_projects == 2
        # Average should be (2800 + 3200) / 2 = 3000
        assert benchmark2.average_price_eur == Decimal('3000.00')
        assert benchmark2.max_price_eur == Decimal('3200.00')
        assert benchmark2.min_price_eur == Decimal('2800.00')

        # Third project - continue update
        benchmark3 = explainer.update_benchmark_after_completion(
            'Badezimmer-Fliesen',
            Decimal('2600.00'),  # Lower than previous
            Decimal('19.0')
        )

        assert benchmark3.total_projects == 3
        # Average should be (2800 + 3200 + 2600) / 3 = 2866.67
        assert benchmark3.average_price_eur == Decimal('2866.67')
        assert benchmark3.min_price_eur == Decimal('2600.00')
        assert benchmark3.has_sufficient_data()  # >= 3 projects

    def test_explanation_with_benchmark_comparison(self, user_with_config, document_with_extraction):
        """Test explanation generation with existing benchmark for comparison."""
        document, extraction = document_with_extraction

        # Create existing benchmark
        UserProjectBenchmark.objects.create(
            user=user_with_config,
            project_type='Badezimmer-Fliesen',
            total_projects=8,
            average_price_eur=Decimal('2900.00'),
            min_price_eur=Decimal('2600.00'),
            max_price_eur=Decimal('3200.00'),
            average_margin_percent=Decimal('20.5')
        )

        explainer = ExplanationService(user_with_config)

        mock_calculation = {
            'total_price_eur': Decimal('3200.00'),  # Above average
            'breakdown': {
                'material_cost': Decimal('1500.00'),
                'labor_cost': Decimal('1000.00'),
                'overhead': Decimal('300.00'),
                'profit_margin': Decimal('400.00')
            },
            'metadata': {}
        }

        explanation = explainer.create_explanation(extraction, mock_calculation)

        # Should have comparison data
        assert explanation.similar_projects_count == 8
        assert explanation.user_average_for_type == Decimal('2900.00')

        # Deviation should be positive (above average)
        # (3200 - 2900) / 2900 * 100 = 10.34%
        assert explanation.deviation_from_average_percent > Decimal('10.0')
        assert explanation.deviation_from_average_percent < Decimal('11.0')

        # Check deviation display
        deviation_display = explanation.get_deviation_direction()
        assert '↑' in deviation_display

    def test_multiple_users_independent_benchmarks(self):
        """Test that benchmarks are user-specific and independent."""
        # Create two users
        user1 = User.objects.create_user(username='craftsman1', password='pass1')
        user2 = User.objects.create_user(username='craftsman2', password='pass2')

        # Create templates and configs for both
        for user in [user1, user2]:
            template = BetriebskennzahlTemplate.objects.create(
                name=f'Template {user.username}',
                version='1.0',
                is_active=True
            )
            IndividuelleBetriebskennzahl.objects.create(
                user=user,
                betrieb_name=f'Betrieb {user.username}',
                template=template,
                stundensatz=Decimal('75.00'),
                gemeinkosten_prozent=Decimal('15.0'),
                gewinnmarge_prozent=Decimal('20.0'),
                is_active=True
            )

        explainer1 = ExplanationService(user1)
        explainer2 = ExplanationService(user2)

        # User 1 creates benchmark
        benchmark1 = explainer1.update_benchmark_after_completion(
            'Badezimmer-Fliesen',
            Decimal('2800.00'),
            Decimal('20.0')
        )

        # User 2 creates benchmark for same project type
        benchmark2 = explainer2.update_benchmark_after_completion(
            'Badezimmer-Fliesen',
            Decimal('3500.00'),  # Different price
            Decimal('25.0')
        )

        # Benchmarks should be different
        assert benchmark1.id != benchmark2.id
        assert benchmark1.user == user1
        assert benchmark2.user == user2
        assert benchmark1.average_price_eur != benchmark2.average_price_eur

        # Each user should only see their own benchmark
        user1_benchmarks = UserProjectBenchmark.objects.filter(user=user1)
        user2_benchmarks = UserProjectBenchmark.objects.filter(user=user2)

        assert user1_benchmarks.count() == 1
        assert user2_benchmarks.count() == 1

    def test_confidence_levels_affect_explanation(self, user_with_config, document_with_extraction):
        """Test that different confidence levels produce appropriate explanations."""
        document, extraction = document_with_extraction
        explainer = ExplanationService(user_with_config)

        # High confidence scenario
        extraction.confidence_scores = {'holzart': 0.95, 'oberflaeche': 0.92, 'material_sku': 0.94}
        extraction.extracted_data = {
            'holzart': 'eiche',
            'oberflaeche': 'geölt',
            'material_sku': 'EICHE-25MM'
        }
        extraction.save()

        high_conf_calc = {
            'total_price_eur': Decimal('3000.00'),
            'breakdown': {},
            'metadata': {'similar_projects_count': 10}
        }

        high_explanation = explainer.create_explanation(extraction, high_conf_calc)
        assert high_explanation.confidence_score >= Decimal('0.7')

        # Low confidence scenario - create new extraction
        document2 = Document.objects.create(
            user=user_with_config,
            original_filename='test2.pdf',
            file_size_bytes=1024
        )
        low_extraction = ExtractionResult.objects.create(
            document=document2,
            confidence_scores={'holzart': 0.45},  # Very low
            extracted_data={'holzart': 'unknown'}  # Missing required fields
        )

        low_conf_calc = {
            'total_price_eur': Decimal('3000.00'),
            'breakdown': {},
            'metadata': {'similar_projects_count': 0}
        }

        low_explanation = explainer.create_explanation(low_extraction, low_conf_calc)
        assert low_explanation.confidence_score < Decimal('0.7')
        assert low_explanation.requires_manual_review()

    def test_factor_ordering_by_impact(self, user_with_config, document_with_extraction):
        """Test that factors are correctly ordered by impact for Progressive Disclosure."""
        document, extraction = document_with_extraction
        explainer = ExplanationService(user_with_config)

        # Create calculation with various factors
        calculation = {
            'total_price_eur': Decimal('5000.00'),
            'breakdown': {
                'material_cost': Decimal('2000.00'),  # 40% impact
                'labor_cost': Decimal('1500.00'),      # 30% impact
                'wood_type_adjustment': Decimal('500.00'),  # 10% impact
                'complexity_adjustment': Decimal('500.00'), # 10% impact
                'overhead': Decimal('300.00'),         # 6% impact
                'profit_margin': Decimal('200.00'),    # 4% impact
                'material_sku': 'TEST',
                'quantity': 10,
                'unit_price': Decimal('200.00'),
                'labor_hours': 20,
                'labor_rate_per_hour': Decimal('75.00'),
                'wood_type': 'eiche',
                'wood_factor': Decimal('1.3'),
                'complexity_technique': 'hand_geschnitzt',
                'complexity_factor': Decimal('1.5')
            },
            'metadata': {}
        }

        explanation = explainer.create_explanation(extraction, calculation)
        factors = list(explanation.factors.all()[:5])  # Top 5

        # First factor should have highest impact
        assert factors[0].impact_percent >= factors[1].impact_percent
        assert factors[1].impact_percent >= factors[2].impact_percent

        # All top factors should be major factors (>= 10%)
        for factor in factors[:3]:
            assert factor.is_major_factor()
