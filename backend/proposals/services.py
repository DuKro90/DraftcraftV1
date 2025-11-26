"""Proposal generation and pricing calculation services."""
import logging
from decimal import Decimal
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from django.utils import timezone
from documents.models import Document
from extraction.models import MaterialExtraction
from core.constants import (
    GERMAN_WOOD_TYPES,
    COMPLEXITY_FACTORS,
    SURFACE_FACTORS,
    QUALITY_TIERS,
    ADDITIONAL_FEATURES,
    DEFAULT_HOURLY_RATE,
)
from .models import (
    Proposal,
    ProposalLine,
    ProposalTemplate,
    ProposalCalculationLog,
)

logger = logging.getLogger(__name__)


class PricingCalculationError(Exception):
    """Pricing calculation error."""
    pass


class ProposalService:
    """Service for proposal generation from extracted materials."""

    def __init__(self, template: ProposalTemplate = None):
        """Initialize with template (or use defaults)."""
        self.template = template or self._get_default_template()

    def _get_default_template(self) -> ProposalTemplate:
        """Get or create default template."""
        try:
            return ProposalTemplate.objects.filter(is_active=True).first()
        except ProposalTemplate.DoesNotExist:
            return ProposalTemplate(
                name='Default',
                hourly_rate=DEFAULT_HOURLY_RATE,
                profit_margin_percent=Decimal('10'),
                tax_rate_percent=Decimal('19'),
            )

    def generate_proposal(
        self,
        document: Document,
        proposal_number: str = None,
        valid_days: int = 30
    ) -> Proposal:
        """Generate proposal from extracted document.

        Args:
            document: Document with extracted materials
            proposal_number: Custom proposal number (auto-generated if None)
            valid_days: Proposal validity in days

        Returns:
            Generated Proposal object

        Raises:
            PricingCalculationError: If calculation fails
        """
        try:
            # Check for material extraction
            material_data = document.material_extraction
            if not material_data:
                raise PricingCalculationError(
                    "No material extraction found for document"
                )

            # Create proposal
            if not proposal_number:
                proposal_number = self._generate_proposal_number()

            proposal = Proposal.objects.create(
                document=document,
                template=self.template,
                proposal_number=proposal_number,
                valid_until=timezone.now() + timedelta(days=valid_days),
            )

            # Generate lines from extracted materials
            self._generate_proposal_lines(proposal, material_data)

            # Calculate totals
            proposal.recalculate_totals()
            proposal.save()

            logger.info(f"Generated proposal {proposal_number} for document {document.id}")
            return proposal

        except Exception as e:
            logger.exception(f"Error generating proposal for document {document.id}")
            raise PricingCalculationError(f"Proposal generation failed: {str(e)}")

    def _generate_proposal_number(self) -> str:
        """Generate unique proposal number."""
        today = timezone.now()
        year = today.year
        count = Proposal.objects.filter(
            created_at__year=year
        ).count() + 1
        return f"AN-{year}-{count:05d}"

    def _generate_proposal_lines(
        self,
        proposal: Proposal,
        material_data: MaterialExtraction
    ) -> None:
        """Generate proposal lines from material extraction.

        Args:
            proposal: Proposal to add lines to
            material_data: Extracted material specifications
        """
        position = 1

        # Process each material
        for material_type, quantity in material_data.materials.items():
            if not quantity:
                continue

            # Calculate unit price
            unit_price = self.calculate_material_price(
                material_type=material_type,
                quantity=Decimal(str(quantity)),
                unit=material_data.unit or 'm²',
                complexity=material_data.complexity_level or 'simple',
                surface=material_data.surface_finish or 'natural',
            )

            # Create proposal line
            line_total = Decimal(str(quantity)) * unit_price
            ProposalLine.objects.create(
                proposal=proposal,
                position=position,
                description=f"{material_type.title()} {material_data.complexity_level or 'verarbeitet'}",
                quantity=Decimal(str(quantity)),
                unit=material_data.unit or 'm²',
                unit_price=unit_price,
                total=line_total,
            )

            position += 1

        # Add additional features as lines
        if material_data.additional_features:
            for feature in material_data.additional_features:
                if feature in ADDITIONAL_FEATURES:
                    feature_hours = ADDITIONAL_FEATURES[feature]['hours']
                    feature_cost = feature_hours * self.template.hourly_rate

                    ProposalLine.objects.create(
                        proposal=proposal,
                        position=position,
                        description=feature.title(),
                        quantity=feature_hours,
                        unit='h',
                        unit_price=self.template.hourly_rate,
                        total=feature_cost,
                    )
                    position += 1

    def calculate_material_price(
        self,
        material_type: str,
        quantity: Decimal,
        unit: str = 'm²',
        complexity: str = 'simple',
        surface: str = 'natural',
        quality: str = 'standard'
    ) -> Decimal:
        """Calculate unit price for material.

        Formula:
        unit_price = (material_cost + labor_cost) * profit_margin * overhead

        Args:
            material_type: Wood type (eiche, buche, etc.)
            quantity: Quantity
            unit: Unit (m², lfm, etc.)
            complexity: Complexity level
            surface: Surface finish
            quality: Quality tier

        Returns:
            Decimal unit price in EUR

        Raises:
            PricingCalculationError: If calculation fails
        """
        try:
            # Get material specs
            material_key = material_type.lower()
            if material_key not in GERMAN_WOOD_TYPES:
                raise PricingCalculationError(f"Unknown material: {material_type}")

            material_spec = GERMAN_WOOD_TYPES[material_key]
            complexity_spec = COMPLEXITY_FACTORS.get(complexity, COMPLEXITY_FACTORS['simple'])
            surface_spec = SURFACE_FACTORS.get(surface, SURFACE_FACTORS['natural'])
            quality_spec = QUALITY_TIERS.get(quality, QUALITY_TIERS['standard'])

            # Calculate material cost
            base_material_cost = material_spec['base_material_cost_per_sqm']
            surface_surcharge = surface_spec.get('material_surcharge', Decimal('0'))
            total_material_cost = (base_material_cost + surface_surcharge) * quality_spec

            # Calculate labor cost
            base_hours = material_spec['base_time_hours_per_sqm']
            complexity_factor = complexity_spec['time_factor']
            surface_factor = surface_spec['time_factor']
            total_hours = base_hours * complexity_factor * surface_factor

            labor_cost = total_hours * self.template.hourly_rate

            # Apply profit margin and overhead
            total_cost = total_material_cost + labor_cost
            with_margin = total_cost * (1 + self.template.profit_margin_percent / 100)
            with_overhead = with_margin * self.template.overhead_factor

            # Normalize to reasonable precision
            unit_price = with_overhead.quantize(Decimal('0.01'))

            # Log calculation
            ProposalCalculationLog.objects.create(
                proposal=None,  # Set when added to proposal
                material_type=material_type,
                quantity=quantity,
                unit=unit,
                base_material_cost=base_material_cost,
                base_labor_hours=total_hours,
                labor_cost=labor_cost,
                complexity_factor=Decimal(str(complexity_factor)),
                surface_factor=Decimal(str(surface_factor)),
                quality_tier=quality,
                calculated_unit_price=unit_price,
            )

            return unit_price

        except Exception as e:
            logger.exception(
                f"Error calculating price for {material_type} ({quantity}{unit})"
            )
            raise PricingCalculationError(f"Price calculation failed: {str(e)}")

    def update_proposal_prices(self, proposal: Proposal) -> None:
        """Recalculate all prices in proposal.

        Useful when template or prices change.
        """
        for line in proposal.lines.all():
            # Re-extract material info from description
            line.total = line.calculate_total()
            line.save()

        proposal.recalculate_totals()
        proposal.save()

    def finalize_proposal(self, proposal: Proposal, status: str = 'sent') -> Proposal:
        """Finalize proposal and update status.

        Args:
            proposal: Proposal to finalize
            status: New status (sent, accepted, etc.)

        Returns:
            Updated proposal
        """
        proposal.status = status
        proposal.updated_at = timezone.now()
        proposal.save()
        return proposal


class ProposalEmailService:
    """Service for sending proposals via email."""

    @staticmethod
    def send_proposal(proposal: Proposal, recipient_email: str) -> bool:
        """Send proposal to customer.

        Args:
            proposal: Proposal to send
            recipient_email: Customer email address

        Returns:
            True if sent successfully
        """
        from django.core.mail import EmailMessage
        from django.conf import settings

        try:
            # Build email
            subject = f"Angebot {proposal.proposal_number}"
            message = f"""
Sehr geehrte Damen und Herren,

anbei erhalten Sie unser Angebot für Ihr Projekt.

Angebotsnummer: {proposal.proposal_number}
Gültig bis: {proposal.valid_until}

Summe: {proposal.template.format_price(proposal.total)}

Mit freundlichen Grüßen,
Ihr Handwerksbetrieb
            """

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )

            # Attach PDF if available
            try:
                pdf = ProposalPdfService.generate_pdf(proposal)
                email.attach(f"{proposal.proposal_number}.pdf", pdf, "application/pdf")
            except NotImplementedError:
                pass

            email.send()
            proposal.status = 'sent'
            proposal.save()

            logger.info(f"Proposal {proposal.proposal_number} sent to {recipient_email}")
            return True

        except Exception as e:
            logger.exception(f"Error sending proposal {proposal.proposal_number}")
            return False
