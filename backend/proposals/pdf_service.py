"""PDF generation service for proposals."""
from decimal import Decimal
from datetime import datetime
from io import BytesIO
from typing import Optional
import logging

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, grey, white, black
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from .models import Proposal

logger = logging.getLogger(__name__)


class ProposalPdfService:
    """Service for generating PDF proposals with professional formatting."""

    # German locale settings
    DECIMAL_SEPARATOR = ','
    THOUSAND_SEPARATOR = '.'
    CURRENCY_SYMBOL = '€'

    # Color scheme
    PRIMARY_COLOR = HexColor('#1F4788')  # Professional blue
    ACCENT_COLOR = HexColor('#D4A574')   # Gold accent
    HEADER_BG = HexColor('#F5F5F5')      # Light grey
    TEXT_COLOR = HexColor('#333333')     # Dark grey

    # Page settings
    PAGE_SIZE = A4
    PAGE_WIDTH = PAGE_SIZE[0]
    PAGE_HEIGHT = PAGE_SIZE[1]
    TOP_MARGIN = 1 * cm
    BOTTOM_MARGIN = 1 * cm
    LEFT_MARGIN = 1.5 * cm
    RIGHT_MARGIN = 1.5 * cm

    def __init__(self):
        """Initialize PDF service."""
        pass

    @staticmethod
    def format_currency(amount: Decimal) -> str:
        """
        Format decimal amount as German currency.

        Args:
            amount: Decimal amount to format

        Returns:
            Formatted string like "1.234,56 €"
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        # Round to 2 decimal places
        amount = amount.quantize(Decimal('0.01'))

        # Format with German locale
        formatted = f"{amount:,.2f}".replace(',', '|').replace('.', ',').replace('|', '.')
        return f"{formatted} €"

    @staticmethod
    def format_date(date_obj) -> str:
        """Format date in German style (DD.MM.YYYY)."""
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%d.%m.%Y')
        return str(date_obj)

    @classmethod
    def generate_pdf(cls, proposal: Proposal) -> bytes:
        """
        Generate a professional PDF for a proposal.

        Args:
            proposal: Proposal instance

        Returns:
            PDF content as bytes

        Raises:
            ValueError: If proposal data is invalid
        """
        if not proposal:
            raise ValueError("Proposal instance is required")

        # Create PDF document in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=cls.PAGE_SIZE,
            topMargin=cls.TOP_MARGIN,
            bottomMargin=cls.BOTTOM_MARGIN,
            leftMargin=cls.LEFT_MARGIN,
            rightMargin=cls.RIGHT_MARGIN,
            title=f"Angebot {proposal.proposal_number}",
            author="DraftCraft",
        )

        # Build document elements
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=cls.PRIMARY_COLOR,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=cls.PRIMARY_COLOR,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            spaceBefore=12,
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=cls.TEXT_COLOR,
            spaceAfter=6,
            leading=12,
        )

        # ===== HEADER SECTION =====
        story.append(Paragraph('ANGEBOT', title_style))
        story.append(Spacer(1, 0.2 * cm))

        # Proposal metadata
        metadata_data = [
            ['Angebots-Nr.:', proposal.proposal_number],
            ['Datum:', cls.format_date(proposal.created_at)],
            ['Gültig bis:', cls.format_date(proposal.valid_until) if proposal.valid_until else 'N/A'],
            ['Status:', proposal.get_status_display()],
        ]

        metadata_table = Table(metadata_data, colWidths=[3 * cm, 8 * cm])
        metadata_table.setStyle(
            TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
                ('TEXTCOLOR', (0, 0), (0, -1), cls.PRIMARY_COLOR),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])
        )

        story.append(metadata_table)
        story.append(Spacer(1, 0.5 * cm))

        # ===== CUSTOMER SECTION =====
        story.append(Paragraph('Kunde', heading_style))
        customer_info = []
        if proposal.customer_name:
            customer_info.append(Paragraph(proposal.customer_name, normal_style))
        if proposal.customer_address:
            customer_info.append(Paragraph(proposal.customer_address, normal_style))
        if proposal.customer_email:
            customer_info.append(Paragraph(proposal.customer_email, normal_style))

        if customer_info:
            story.extend(customer_info)
        else:
            story.append(Paragraph('Keine Kundeninformation angegeben', normal_style))

        story.append(Spacer(1, 0.5 * cm))

        # ===== ITEMS/LINES SECTION =====
        story.append(Paragraph('Leistungen', heading_style))

        # Build lines table
        if proposal.lines.exists():
            lines_data = [['Pos.', 'Beschreibung', 'Menge', 'Einheit', 'Einzelpreis', 'Gesamtpreis']]

            for line in proposal.lines.all():
                lines_data.append([
                    str(line.position),
                    line.description[:50],  # Truncate long descriptions
                    f"{line.quantity:.2f}",
                    line.unit,
                    cls.format_currency(line.unit_price),
                    cls.format_currency(line.total),
                ])

            lines_table = Table(
                lines_data,
                colWidths=[0.8 * cm, 6 * cm, 1.5 * cm, 1.5 * cm, 1.8 * cm, 1.8 * cm]
            )
            lines_table.setStyle(
                TableStyle([
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), cls.HEADER_BG),
                    ('TEXTCOLOR', (0, 0), (-1, 0), cls.PRIMARY_COLOR),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                    # Data rows
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#FAFAFA')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, grey),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ])
            )

            story.append(lines_table)
        else:
            story.append(Paragraph('Keine Positionen angegeben', normal_style))

        story.append(Spacer(1, 0.5 * cm))

        # ===== TOTALS SECTION =====
        totals_data = [
            ['Summe netto:', cls.format_currency(proposal.subtotal)],
            ['Mehrwertsteuer (19%):', cls.format_currency(proposal.tax_amount)],
            ['Gesamtsumme:', cls.format_currency(proposal.total)],
        ]

        totals_table = Table(totals_data, colWidths=[6 * cm, 3 * cm])
        totals_table.setStyle(
            TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('TEXTCOLOR', (0, -1), (-1, -1), cls.PRIMARY_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEABOVE', (0, -1), (-1, -1), 2, cls.PRIMARY_COLOR),
                ('LINEBELOW', (0, -1), (-1, -1), 2, cls.PRIMARY_COLOR),
            ])
        )

        # Right-align totals table
        totals_spacer = [[Spacer(1, 1)], [totals_table]]
        totals_wrapper = Table(totals_spacer, colWidths=[cls.PAGE_WIDTH - 2 * cls.LEFT_MARGIN])
        totals_wrapper.setStyle(
            TableStyle([
                ('ALIGN', (0, 1), (0, 1), 'RIGHT'),
                ('VALIGN', (0, 0), (0, -1), 'TOP'),
            ])
        )
        story.append(totals_wrapper)

        story.append(Spacer(1, 0.5 * cm))

        # ===== NOTES SECTION =====
        if proposal.notes:
            story.append(Paragraph('Hinweise', heading_style))
            story.append(Paragraph(proposal.notes, normal_style))
            story.append(Spacer(1, 0.3 * cm))

        # ===== TERMS SECTION =====
        if proposal.terms:
            story.append(Paragraph('Bedingungen', heading_style))
            story.append(Paragraph(proposal.terms, normal_style))
            story.append(Spacer(1, 0.3 * cm))

        # ===== FOOTER =====
        story.append(Spacer(1, 1 * cm))
        footer_text = f"Erstellt mit DraftCraft am {cls.format_date(datetime.now())}"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#999999'),
            alignment=1,  # Center
        )
        story.append(Paragraph(footer_text, footer_style))

        # Build PDF
        try:
            doc.build(story)
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
        except Exception as e:
            logger.exception(f"Error generating PDF for proposal {proposal.id}")
            raise ValueError(f"Failed to generate PDF: {str(e)}")

    @classmethod
    def get_filename(cls, proposal: Proposal) -> str:
        """
        Get suggested filename for proposal PDF.

        Args:
            proposal: Proposal instance

        Returns:
            Filename like "AN-2025-00001.pdf"
        """
        return f"{proposal.proposal_number}.pdf"
