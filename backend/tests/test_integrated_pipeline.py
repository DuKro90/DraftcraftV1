# -*- coding: utf-8 -*-
"""Tests for integrated extraction pipeline (Phase 2 + Phase 3)."""

import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from documents.models import Document, ExtractionResult
from documents.pattern_models import (
    ExtractionFailurePattern,
    PatternReviewSession,
    PatternFixProposal,
)
from documents.betriebskennzahl_models import (
    IndividuelleBetriebskennzahl,
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    MateriallistePosition,
)
from extraction.services.integrated_pipeline import (
    IntegratedExtractionPipeline,
    IntegratedPipelineException,
)


@pytest.mark.django_db
class TestIntegratedPipelineInitialization:
    """Tests for pipeline initialization."""

    def test_initialization_with_complete_config(self):
        """Test pipeline initializes with complete user configuration."""
        user = User.objects.create_user(username='integrated_user', password='testpass')
        config = IndividuelleBetriebskennzahl.objects.create(user=user)

        pipeline = IntegratedExtractionPipeline(user)

        assert pipeline.user == user
        assert pipeline.calculator is not None
        assert pipeline.pattern_analyzer is not None
        assert pipeline.knowledge_builder is not None

    def test_initialization_fails_without_config(self):
        """Test pipeline fails without user configuration."""
        user = User.objects.create_user(username='no_config_user', password='testpass')

        with pytest.raises(IntegratedPipelineException):
            IntegratedExtractionPipeline(user)

    def test_initialization_sets_up_all_services(self):
        """Test all services are properly initialized."""
        user = User.objects.create_user(username='service_user', password='testpass')
        IndividuelleBetriebskennzahl.objects.create(user=user)

        pipeline = IntegratedExtractionPipeline(user)

        # All services should be initialized
        assert pipeline.calculator is not None
        assert pipeline.pattern_analyzer is not None
        assert pipeline.knowledge_builder is not None


@pytest.mark.django_db
class TestProcessExtractionResult:
    """Tests for processing extraction results through pipeline."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='process_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.pipeline = IntegratedExtractionPipeline(self.user)

        self.document = Document.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='invoice'
        )

    def test_process_extraction_basic(self):
        """Test basic extraction processing."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test document',
            extracted_data={
                'amount': '100.00',
                'vendor': 'Test Vendor',
                'date': '15.11.2024'
            },
            confidence_scores={
                'amount': 0.95,
                'vendor': 0.80,
                'date': 0.85
            }
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=False,
            calculate_pricing=False
        )

        assert result['success'] is True
        assert result['extraction']['id'] == str(extraction.id)
        assert result['patterns'] is not None

    def test_process_with_knowledge_fixes_disabled(self):
        """Test processing without applying knowledge fixes."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={'test': 'data'},
            confidence_scores={'test': 0.90}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=False,
            calculate_pricing=False
        )

        assert result['knowledge_applied'] == []

    def test_process_with_pricing_calculation(self):
        """Test processing with pricing calculation."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={
                'material_sku': 'TEST-001',
                'material_quantity': 5,
                'holzart': 'eiche',
                'surface_finish': 'lackieren',
                'complexity': 'gefräst',
                'labor_hours': 8
            },
            confidence_scores={'amount': 0.90}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=False,
            calculate_pricing=True
        )

        assert result['pricing'] is not None
        assert 'total_price_eur' in result['pricing']

    def test_process_returns_extraction_data(self):
        """Test that result includes serialized extraction."""
        extracted_data = {
            'amount': '250.50',
            'vendor': 'Handwerk GmbH',
        }
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Full text',
            extracted_data=extracted_data,
            confidence_scores={'amount': 0.92, 'vendor': 0.88}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            calculate_pricing=False
        )

        assert result['extraction']['extracted_data'] == extracted_data
        assert result['extraction']['confidence_scores']['amount'] == 0.92

    def test_process_includes_timestamp(self):
        """Test that processing includes timestamp."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={}
        )

        result = self.pipeline.process_extraction_result(extraction, calculate_pricing=False)

        assert 'enrichments_timestamp' in result
        assert result['enrichments_timestamp'] is not None

    def test_process_includes_notes(self):
        """Test that processing includes notes."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={'test': 'data'},
            confidence_scores={'test': 0.90}
        )

        result = self.pipeline.process_extraction_result(extraction, calculate_pricing=False)

        assert 'processing_notes' in result
        assert isinstance(result['processing_notes'], list)


@pytest.mark.django_db
class TestPipelinePatternAnalysis:
    """Tests for pattern analysis in pipeline."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='pattern_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.pipeline = IntegratedExtractionPipeline(self.user)

        self.document = Document.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='invoice'
        )

    def test_pattern_analysis_included(self):
        """Test that pattern analysis is included in result."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={'amount': '100'},
            confidence_scores={'amount': 0.75}  # Low confidence
        )

        result = self.pipeline.process_extraction_result(extraction, calculate_pricing=False)

        assert result['patterns'] is not None
        assert 'low_confidence_patterns' in result['patterns']
        assert 'summary' in result['patterns']


@pytest.mark.django_db
class TestPipelineKnowledgeApplication:
    """Tests for knowledge fix application in pipeline."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='knowledge_user', password='testpass')
        self.deployer = User.objects.create_user(username='deployer_kb', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.pipeline = IntegratedExtractionPipeline(self.user)

        self.document = Document.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='invoice'
        )

        # Create pattern and fix
        self.pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        self.session = PatternReviewSession.objects.create(
            pattern=self.pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

    def test_knowledge_fixes_reported_in_result(self):
        """Test that ready knowledge fixes are reported."""
        # Create ready fix
        proposal = PatternFixProposal.objects.create(
            pattern=self.pattern,
            review_session=self.session,
            title='Fix Amount',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={'amount': '100'},
            confidence_scores={'amount': 0.90}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=True,
            calculate_pricing=False
        )

        assert len(result['knowledge_applied']) > 0
        fix_info = result['knowledge_applied'][0]
        assert fix_info['title'] == 'Fix Amount'
        assert fix_info['status'] == 'ready_for_deployment'

    def test_no_knowledge_fixes_if_none_ready(self):
        """Test that no fixes are reported if none are ready."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={'amount': '100'},
            confidence_scores={'amount': 0.90}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=True,
            calculate_pricing=False
        )

        assert result['knowledge_applied'] == []


@pytest.mark.django_db
class TestPipelinePricingIntegration:
    """Tests for pricing calculation in pipeline."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='pricing_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            stundensatz_arbeit=Decimal('95.00'),
            gewinnmarge_prozent=Decimal('25.00')
        )
        self.pipeline = IntegratedExtractionPipeline(self.user)

        self.document = Document.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='invoice'
        )

    def test_pricing_calculation_in_pipeline(self):
        """Test pricing is calculated in pipeline."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={
                'material_quantity': 5,
                'labor_hours': 8
            },
            confidence_scores={}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=False,
            calculate_pricing=True
        )

        assert result['pricing'] is not None
        assert 'total_price_eur' in result['pricing']
        assert isinstance(result['pricing']['total_price_eur'], (int, float))

    def test_pricing_skipped_if_disabled(self):
        """Test pricing is skipped when disabled."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={
                'material_quantity': 5,
                'labor_hours': 8
            },
            confidence_scores={}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=False,
            calculate_pricing=False
        )

        assert result['pricing'] is None

    def test_pricing_includes_breakdown(self):
        """Test pricing includes calculation breakdown."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={
                'material_quantity': 10,
                'labor_hours': 5
            },
            confidence_scores={}
        )

        result = self.pipeline.process_extraction_result(
            extraction,
            calculate_pricing=True
        )

        assert result['pricing'] is not None
        assert 'breakdown' in result['pricing']


@pytest.mark.django_db
class TestPipelineStatus:
    """Tests for pipeline status reporting."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='status_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.pipeline = IntegratedExtractionPipeline(self.user)

    def test_pipeline_status(self):
        """Test getting pipeline status."""
        status = self.pipeline.get_pipeline_status()

        assert status['user'] == self.user.username
        assert status['calculator_configured'] is True
        assert status['pattern_analyzer_active'] is True
        assert 'ready_to_deploy_fixes' in status
        assert 'deployment_summary' in status

    def test_pipeline_status_counts_ready_fixes(self):
        """Test pipeline status reports ready fixes."""
        pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='test',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        session = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )

        # Create ready fix
        PatternFixProposal.objects.create(
            pattern=pattern,
            review_session=session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='test',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        status = self.pipeline.get_pipeline_status()

        assert status['ready_to_deploy_fixes'] == 1


@pytest.mark.django_db
class TestExtractionRecommendations:
    """Tests for extraction recommendations."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='rec_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.pipeline = IntegratedExtractionPipeline(self.user)

        self.document = Document.objects.create(
            user=self.user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            document_type='invoice'
        )

    def test_recommendations_include_quality_issues(self):
        """Test recommendations include quality issues."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={'amount': '100', 'vendor': 'Test'},
            confidence_scores={
                'amount': 0.75,  # Low
                'vendor': 0.85
            }
        )

        recommendations = self.pipeline.get_extraction_recommendations(extraction)

        assert 'extraction_quality' in recommendations
        assert len(recommendations['extraction_quality']) > 0

    def test_recommendations_include_knowledge_improvements(self):
        """Test recommendations include knowledge improvements."""
        # Create ready fix
        pattern = ExtractionFailurePattern.objects.create(
            user=self.user,
            field_name='amount',
            pattern_type='low_confidence',
            root_cause='Test'
        )
        session = PatternReviewSession.objects.create(
            pattern=pattern,
            admin_user=self.user,
            title='Test',
            description='Test'
        )
        PatternFixProposal.objects.create(
            pattern=pattern,
            review_session=session,
            title='Test',
            description='Test',
            fix_type='confidence_threshold',
            affected_field='amount',
            status='validated',
            test_success_rate=Decimal('0.90'),
            confidence_score=Decimal('0.85')
        )

        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={},
            confidence_scores={}
        )

        recommendations = self.pipeline.get_extraction_recommendations(extraction)

        assert 'knowledge_improvements' in recommendations
        assert len(recommendations['knowledge_improvements']) > 0

    def test_recommendations_include_pricing_notes(self):
        """Test recommendations include pricing information."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={
                'material_quantity': 5,
                'labor_hours': 0  # Edge case
            },
            confidence_scores={}
        )

        recommendations = self.pipeline.get_extraction_recommendations(extraction)

        assert 'pricing_notes' in recommendations


@pytest.mark.django_db
class TestProcessingReport:
    """Tests for processing reports."""

    def setup_method(self):
        """Setup test data."""
        self.user = User.objects.create_user(username='report_user', password='testpass')
        self.config = IndividuelleBetriebskennzahl.objects.create(user=self.user)
        self.pipeline = IntegratedExtractionPipeline(self.user)

        self.document = Document.objects.create(
            user=self.user,
            original_filename='invoice.pdf',
            file_size_bytes=2048,
            document_type='invoice'
        )

    def test_processing_report_generation(self):
        """Test generating processing report."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Invoice text',
            extracted_data={'amount': '500', 'vendor': 'Test'},
            confidence_scores={'amount': 0.95, 'vendor': 0.85}
        )

        report = self.pipeline.create_processing_report(extraction)

        assert 'Extraction Processing Report' in report
        assert 'invoice.pdf' in report
        assert 'Extracted Data' in report
        assert 'Pattern Analysis' in report

    def test_report_includes_all_sections(self):
        """Test report includes all major sections."""
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Test',
            extracted_data={'test': 'data'},
            confidence_scores={'test': 0.90}
        )

        report = self.pipeline.create_processing_report(extraction)

        assert 'Document' in report
        assert 'Extracted Data' in report
        assert 'Pattern Analysis' in report
        assert 'Knowledge Fixes' in report
        assert 'Pricing' in report


@pytest.mark.django_db
class TestPipelineEndToEnd:
    """End-to-end pipeline tests."""

    def setup_method(self):
        """Setup complete test scenario."""
        self.user = User.objects.create_user(username='e2e_user', password='testpass')
        self.deployer = User.objects.create_user(username='deployer_e2e', password='testpass')

        # Setup configuration
        self.config = IndividuelleBetriebskennzahl.objects.create(
            user=self.user,
            stundensatz_arbeit=Decimal('90.00'),
            gewinnmarge_prozent=Decimal('30.00'),
            use_handwerk_standard=True,
            use_custom_materials=False,
            use_seasonal_adjustments=False,
            use_customer_discounts=True,
            use_bulk_discounts=False
        )

        self.pipeline = IntegratedExtractionPipeline(self.user)

        # Setup document
        self.document = Document.objects.create(
            user=self.user,
            original_filename='angebot.pdf',
            file_size_bytes=3072,
            document_type='offer'
        )

    def test_complete_pipeline_workflow(self):
        """Test complete end-to-end pipeline."""
        # Create extraction with realistic data
        extraction = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Angebot für Schreinerarbeit',
            extracted_data={
                'amount': '1500.00',
                'vendor': 'Schreinerei Müller',
                'material_quantity': 20,
                'labor_hours': 12,
                'holzart': 'eiche',
                'surface_finish': 'lackieren',
                'complexity': 'gefräst',
            },
            confidence_scores={
                'amount': 0.92,
                'vendor': 0.88,
                'material_quantity': 0.85,
                'labor_hours': 0.90,
                'holzart': 0.95,
                'surface_finish': 0.92,
                'complexity': 0.88,
            }
        )

        # Process through complete pipeline
        result = self.pipeline.process_extraction_result(
            extraction,
            apply_knowledge_fixes=True,
            calculate_pricing=True
        )

        # Verify complete result
        assert result['success'] is True
        assert result['extraction'] is not None
        assert result['patterns'] is not None
        assert result['pricing'] is not None
        assert len(result['processing_notes']) > 0
        assert result['enrichments_timestamp'] is not None

    def test_multiple_documents_independent(self):
        """Test processing multiple documents independently."""
        doc1 = ExtractionResult.objects.create(
            document=self.document,
            ocr_text='Document 1',
            extracted_data={'amount': '100'},
            confidence_scores={'amount': 0.90}
        )

        doc2 = ExtractionResult.objects.create(
            document=Document.objects.create(
                user=self.user,
                original_filename='doc2.pdf',
                file_size_bytes=1024,
                document_type='invoice'
            ),
            ocr_text='Document 2',
            extracted_data={'amount': '200'},
            confidence_scores={'amount': 0.85}
        )

        result1 = self.pipeline.process_extraction_result(doc1, calculate_pricing=False)
        result2 = self.pipeline.process_extraction_result(doc2, calculate_pricing=False)

        assert result1['extraction']['id'] == str(doc1.id)
        assert result2['extraction']['id'] == str(doc2.id)
        assert result1['extraction']['id'] != result2['extraction']['id']
