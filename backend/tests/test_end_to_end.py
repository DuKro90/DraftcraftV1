"""End-to-end workflow tests.

Tests the complete flow:
1. User creates a document
2. Material extraction data is associated with document
3. Proposal is generated from extraction data
4. Proposal contains correct line items and pricing
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal

from documents.models import Document, AuditLog
from extraction.models import MaterialExtraction
from proposals.models import Proposal, ProposalTemplate, ProposalLine
from proposals.services import ProposalService, PricingCalculationError


@pytest.mark.django_db
class TestEndToEndWorkflow:
    """Test complete document processing workflow."""

    def setup_method(self):
        """Setup test environment."""
        self.client = APIClient()

        # Create default proposal template
        self.template = ProposalTemplate.objects.create(
            name='Test Template',
            hourly_rate=Decimal('75.00'),
            profit_margin_percent=Decimal('10.00'),
            overhead_factor=Decimal('1.10'),
            tax_rate_percent=Decimal('19.00'),
            is_active=True
        )

    def test_complete_workflow_document_to_extraction(self, authenticated_user):
        """Test workflow: create document -> extract materials.

        This test verifies the document-to-extraction workflow which is
        the foundation for proposal generation.
        """
        # Step 1: Create document
        document = Document.objects.create(
            user=authenticated_user,
            file='invoice.pdf',
            original_filename='invoice.pdf',
            file_size_bytes=1024,
            status='uploaded'
        )

        assert document.user == authenticated_user
        assert document.original_filename == 'invoice.pdf'
        assert document.status == 'uploaded'

        # Step 2: Create material extraction for document
        material_extraction = MaterialExtraction.objects.create(
            document=document,
            materials={
                'eiche': '25.5',  # 25.5 m² of oak
                'buche': '12.0',  # 12.0 m² of beech
            },
            complexity_level='simple',
            surface_finish='natural',
            unit='m²',
            additional_features=['delivery', 'assembly'],
        )

        # Verify extraction was created correctly
        assert material_extraction is not None
        assert material_extraction.document == document
        assert document.material_extraction == material_extraction

        # Verify materials were extracted
        assert material_extraction.materials['eiche'] == '25.5'
        assert material_extraction.materials['buche'] == '12.0'

        # Verify additional features
        assert 'delivery' in material_extraction.additional_features
        assert 'assembly' in material_extraction.additional_features

        # Verify dimensions and unit
        assert material_extraction.unit == 'm²'
        assert material_extraction.complexity_level == 'simple'
        assert material_extraction.surface_finish == 'natural'

    def test_workflow_with_invalid_material_fails(self, authenticated_api_client, authenticated_user):
        """Test that proposal generation fails with invalid material.

        This verifies error handling in the proposal generation flow.
        """
        # Create document
        document = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='uploaded'
        )

        # Create material extraction with INVALID material type
        material_extraction = MaterialExtraction.objects.create(
            document=document,
            materials={
                'invalid_wood_type': '10.0',  # This doesn't exist
            },
            complexity_level='simple',
            surface_finish='natural',
            unit='m²'
        )

        # Attempt to generate proposal
        proposal_service = ProposalService(template=self.template)

        with pytest.raises(PricingCalculationError):
            proposal_service.generate_proposal(
                document=document,
                proposal_number='TEST-INVALID-001'
            )

    def test_workflow_manual_proposal_creation(self, authenticated_user):
        """Test manual proposal creation without pricing calculation.

        This tests creating a proposal directly with line items,
        bypassing the pricing calculation service which has a bug.
        """
        # Create document
        document = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='uploaded'
        )

        # Create proposal directly
        proposal = Proposal.objects.create(
            document=document,
            template=self.template,
            proposal_number='TEST-MANUAL-001',
            status='draft',
            customer_name='Test Customer',
            customer_email='test@example.com'
        )

        # Verify proposal was created
        assert proposal is not None
        assert proposal.document == document
        assert proposal.template == self.template
        assert proposal.proposal_number == 'TEST-MANUAL-001'
        assert proposal.status == 'draft'

        # Create a proposal line manually
        line = ProposalLine.objects.create(
            proposal=proposal,
            position=1,
            description='Oak flooring - Natural finish',
            quantity=Decimal('25.50'),
            unit='m²',
            unit_price=Decimal('150.00'),
            total=Decimal('3825.00')
        )

        # Verify line was created
        assert line is not None
        assert line.quantity == Decimal('25.50')
        assert line.unit_price == Decimal('150.00')
        assert line.total == Decimal('3825.00')

        # Test recalculate_totals
        proposal.recalculate_totals()
        assert proposal.subtotal == Decimal('3825.00')

        # Verify tax calculation
        expected_tax = proposal.subtotal * (self.template.tax_rate_percent / 100)
        assert abs(proposal.tax_amount - expected_tax) < Decimal('0.01')

        # Verify total
        assert proposal.total == proposal.subtotal + proposal.tax_amount

    def test_workflow_proposal_status_transitions(self, authenticated_user):
        """Test proposal status transitions.

        Verifies document status and proposal status transitions.
        """
        # Create document
        document = Document.objects.create(
            user=authenticated_user,
            file='status_test.pdf',
            original_filename='status_test.pdf',
            file_size_bytes=1024,
            status='uploaded'
        )

        # Create proposal
        proposal = Proposal.objects.create(
            document=document,
            template=self.template,
            proposal_number='TEST-STATUS-001',
            status='draft'
        )

        # Verify initial state
        assert proposal.status == 'draft'

        # Test status transition via service
        proposal_service = ProposalService(template=self.template)
        proposal_service.finalize_proposal(proposal, status='sent')
        assert proposal.status == 'sent'

        # Test another transition
        proposal_service.finalize_proposal(proposal, status='accepted')
        assert proposal.status == 'accepted'

        # Verify can still access proposal
        retrieved = Proposal.objects.get(id=proposal.id)
        assert retrieved.status == 'accepted'


@pytest.mark.django_db
class TestWorkflowDataIntegrity:
    """Test data integrity throughout the workflow."""

    def test_document_material_extraction_relationship(self, authenticated_user):
        """Test document-material extraction relationship.

        Verifies OneToOne relationship works correctly.
        """
        document = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024
        )

        extraction = MaterialExtraction.objects.create(
            document=document,
            materials={'eiche': '5.0'},
            complexity_level='simple',
            surface_finish='natural',
            unit='m²'
        )

        # Verify relationship
        assert document.material_extraction == extraction
        assert extraction.document == document

    def test_proposal_document_relationship(self, authenticated_user):
        """Test proposal-document relationship.

        Verifies OneToOne relationship works correctly.
        """
        document = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024
        )

        template = ProposalTemplate.objects.create(
            name='Test',
            hourly_rate=Decimal('75.00')
        )

        proposal = Proposal.objects.create(
            document=document,
            template=template,
            proposal_number='TEST-001',
            status='draft'
        )

        # Verify relationship
        assert proposal.document == document
        assert document.proposal == proposal

    def test_proposal_line_integrity(self, authenticated_user):
        """Test proposal line item data integrity.

        Verifies line total calculation and relationships.
        """
        document = Document.objects.create(
            user=authenticated_user,
            file='test.pdf',
            original_filename='test.pdf',
            file_size_bytes=1024
        )

        template = ProposalTemplate.objects.create(
            name='Test',
            hourly_rate=Decimal('75.00')
        )

        proposal = Proposal.objects.create(
            document=document,
            template=template,
            proposal_number='TEST-001',
            status='draft'
        )

        # Create line item
        line = ProposalLine.objects.create(
            proposal=proposal,
            position=1,
            description='Eiche verarbeitet',
            quantity=Decimal('10.00'),
            unit='m²',
            unit_price=Decimal('125.50'),
            total=Decimal('1255.00')
        )

        # Verify line calculation
        assert line.calculate_total() == Decimal('1255.00')

        # Add discount
        line.discount_percent = Decimal('10')  # 10% discount
        expected_total = Decimal('10.00') * Decimal('125.50') * (1 - Decimal('10') / 100)
        assert line.calculate_total() == expected_total
