"""Tests for PDF generation service."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from proposals.models import Proposal, ProposalTemplate, ProposalLine
from proposals.pdf_service import ProposalPdfService
from documents.models import Document
from django.contrib.auth.models import User


@pytest.mark.unit
class TestProposalPdfService:
    """Tests for ProposalPdfService."""

    def test_format_currency_german_locale(self):
        """Test German locale currency formatting."""
        # Test various amounts
        assert ProposalPdfService.format_currency(Decimal('1000.50')) == '1.000,50 €'
        assert ProposalPdfService.format_currency(Decimal('100.00')) == '100,00 €'
        assert ProposalPdfService.format_currency(Decimal('1234567.89')) == '1.234.567,89 €'
        assert ProposalPdfService.format_currency(Decimal('0.01')) == '0,01 €'

    def test_format_currency_with_float(self):
        """Test that float inputs are converted to Decimal."""
        result = ProposalPdfService.format_currency(1234.56)
        assert result == '1.234,56 €'

    def test_format_date_german_format(self):
        """Test German date formatting (DD.MM.YYYY)."""
        test_date = datetime(2025, 11, 26)
        assert ProposalPdfService.format_date(test_date) == '26.11.2025'

        test_date2 = datetime(2025, 1, 5)
        assert ProposalPdfService.format_date(test_date2) == '05.01.2025'

    def test_format_date_with_string(self):
        """Test that string dates are returned as-is."""
        result = ProposalPdfService.format_date('2025-11-26')
        assert result == '2025-11-26'

    @pytest.mark.django_db
    @pytest.mark.integration
    def test_generate_pdf_basic(self):
        """Test PDF generation with basic proposal."""
        # Create test user and document
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        document = Document.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='completed'
        )

        # Create proposal template
        template = ProposalTemplate.objects.create(
            name='Test Template',
            hourly_rate=Decimal('75.00'),
            profit_margin_percent=Decimal('10'),
            overhead_factor=Decimal('1.10'),
            tax_rate_percent=Decimal('19'),
        )

        # Create proposal
        proposal = Proposal.objects.create(
            document=document,
            template=template,
            proposal_number='AN-2025-00001',
            customer_name='Test Customer',
            customer_email='test@example.com',
            subtotal=Decimal('1000.00'),
            tax_amount=Decimal('190.00'),
            total=Decimal('1190.00'),
            valid_until=datetime.now().date() + timedelta(days=30),
        )

        # Add proposal line
        ProposalLine.objects.create(
            proposal=proposal,
            position=1,
            description='Test Service',
            quantity=Decimal('5.00'),
            unit='h',
            unit_price=Decimal('200.00'),
            total=Decimal('1000.00'),
        )

        # Generate PDF
        pdf_content = ProposalPdfService.generate_pdf(proposal)

        # Verify PDF content
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        # PDF files start with %PDF magic bytes
        assert pdf_content.startswith(b'%PDF')

    @pytest.mark.django_db
    @pytest.mark.integration
    def test_generate_pdf_with_notes_and_terms(self):
        """Test PDF generation with notes and terms."""
        user = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        document = Document.objects.create(
            user=user,
            original_filename='test2.pdf',
            file_size_bytes=1024,
            status='completed'
        )

        template = ProposalTemplate.objects.create(
            name='Template with Notes',
            hourly_rate=Decimal('50.00'),
        )

        proposal = Proposal.objects.create(
            document=document,
            template=template,
            proposal_number='AN-2025-00002',
            customer_name='Another Customer',
            subtotal=Decimal('500.00'),
            tax_amount=Decimal('95.00'),
            total=Decimal('595.00'),
            notes='This is a test note for the proposal.',
            terms='Payment due within 30 days. Standard terms apply.',
        )

        ProposalLine.objects.create(
            proposal=proposal,
            position=1,
            description='Consulting Services',
            quantity=Decimal('10.00'),
            unit='h',
            unit_price=Decimal('50.00'),
            total=Decimal('500.00'),
        )

        # Generate PDF
        pdf_content = ProposalPdfService.generate_pdf(proposal)

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF')

    @pytest.mark.django_db
    @pytest.mark.integration
    def test_generate_pdf_empty_proposal(self):
        """Test PDF generation with proposal that has no lines."""
        user = User.objects.create_user(
            username='testuser3',
            password='testpass123'
        )
        document = Document.objects.create(
            user=user,
            original_filename='test3.pdf',
            file_size_bytes=1024,
            status='completed'
        )

        template = ProposalTemplate.objects.create(
            name='Empty Template',
            hourly_rate=Decimal('75.00'),
        )

        proposal = Proposal.objects.create(
            document=document,
            template=template,
            proposal_number='AN-2025-00003',
            subtotal=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            total=Decimal('0.00'),
        )

        # Generate PDF (with no lines)
        pdf_content = ProposalPdfService.generate_pdf(proposal)

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF')

    def test_generate_pdf_invalid_proposal(self):
        """Test PDF generation with invalid proposal raises error."""
        with pytest.raises(ValueError):
            ProposalPdfService.generate_pdf(None)

    @pytest.mark.django_db
    def test_get_filename(self):
        """Test filename generation for proposals."""
        user = User.objects.create_user(
            username='testuser4',
            password='testpass123'
        )
        document = Document.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='completed'
        )

        proposal = Proposal.objects.create(
            document=document,
            proposal_number='AN-2025-00123',
            subtotal=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            total=Decimal('0.00'),
        )

        filename = ProposalPdfService.get_filename(proposal)
        assert filename == 'AN-2025-00123.pdf'

    @pytest.mark.django_db
    @pytest.mark.integration
    def test_pdf_contains_proposal_data(self):
        """Test that PDF contains proposal data (basic string check)."""
        user = User.objects.create_user(
            username='testuser5',
            password='testpass123'
        )
        document = Document.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='completed'
        )

        template = ProposalTemplate.objects.create(
            name='Data Check Template',
        )

        proposal = Proposal.objects.create(
            document=document,
            template=template,
            proposal_number='AN-2025-00999',
            customer_name='PDF Test Customer',
            customer_email='pdf@test.com',
            subtotal=Decimal('999.99'),
            tax_amount=Decimal('189.99'),
            total=Decimal('1189.98'),
        )

        ProposalLine.objects.create(
            proposal=proposal,
            position=1,
            description='PDF Test Service',
            quantity=Decimal('1.00'),
            unit='Stk',
            unit_price=Decimal('999.99'),
            total=Decimal('999.99'),
        )

        pdf_content = ProposalPdfService.generate_pdf(proposal)
        pdf_text = pdf_content.decode('latin-1')  # Basic PDF text decoding

        # Verify that proposal number appears in PDF
        assert 'AN-2025-00999' in pdf_text or b'AN-2025-00999' in pdf_content

    @pytest.mark.django_db
    @pytest.mark.integration
    def test_pdf_generation_multiple_lines(self):
        """Test PDF generation with multiple proposal lines."""
        user = User.objects.create_user(
            username='testuser6',
            password='testpass123'
        )
        document = Document.objects.create(
            user=user,
            original_filename='test.pdf',
            file_size_bytes=1024,
            status='completed'
        )

        template = ProposalTemplate.objects.create(
            name='Multi-line Template',
        )

        proposal = Proposal.objects.create(
            document=document,
            template=template,
            proposal_number='AN-2025-00555',
            customer_name='Multi-Service Customer',
            subtotal=Decimal('3000.00'),
            tax_amount=Decimal('570.00'),
            total=Decimal('3570.00'),
        )

        # Add multiple lines
        for i in range(1, 4):
            ProposalLine.objects.create(
                proposal=proposal,
                position=i,
                description=f'Service {i}',
                quantity=Decimal('10.00'),
                unit='h',
                unit_price=Decimal('100.00'),
                total=Decimal('1000.00'),
            )

        pdf_content = ProposalPdfService.generate_pdf(proposal)

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF')
