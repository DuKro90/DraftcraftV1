"""Proposal generation models."""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from documents.models import Document
from core.constants import (
    GERMAN_WOOD_TYPES,
    COMPLEXITY_FACTORS,
    SURFACE_FACTORS,
    QUALITY_TIERS,
    DEFAULT_HOURLY_RATE,
    DEFAULT_PROFIT_MARGIN,
    DEFAULT_TAX_RATE,
)


class ProposalTemplate(models.Model):
    """Template for proposal generation."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    # Pricing config
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=DEFAULT_HOURLY_RATE,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    profit_margin_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=DEFAULT_PROFIT_MARGIN,
        validators=[MinValueValidator(Decimal('0'))]
    )
    overhead_factor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.10'),
        validators=[MinValueValidator(Decimal('1.0'))]
    )
    tax_rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=DEFAULT_TAX_RATE,
        validators=[MinValueValidator(Decimal('0'))]
    )

    # Display settings
    currency = models.CharField(max_length=3, default='EUR')
    decimal_separator = models.CharField(max_length=1, default=',')
    thousand_separator = models.CharField(max_length=1, default='.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-is_active', '-updated_at']

    def __str__(self):
        return f"{self.name} ({self.hourly_rate}€/h)"

    def format_price(self, price: Decimal) -> str:
        """Format price according to template settings."""
        if not isinstance(price, Decimal):
            price = Decimal(str(price))

        # Format with 2 decimals
        formatted = f"{price:.2f}"

        # Replace separators
        formatted = formatted.replace('.', '|TEMP|')  # Temp placeholder
        formatted = formatted.replace(',', self.decimal_separator)
        formatted = formatted.replace('|TEMP|', self.thousand_separator)

        return f"{formatted} {self.currency}"


class Proposal(models.Model):
    """Generated proposal document."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='proposal'
    )
    template = models.ForeignKey(
        ProposalTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='proposals'
    )

    # Proposal info
    proposal_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Customer info (from document metadata or manual entry)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_address = models.TextField(blank=True)
    customer_email = models.EmailField(blank=True)

    # Pricing
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        default=Decimal('0')
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        default=Decimal('0')
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        default=Decimal('0')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'status']),
            models.Index(fields=['proposal_number']),
        ]

    def __str__(self):
        return f"Proposal {self.proposal_number}"

    def recalculate_totals(self):
        """Recalculate totals from lines."""
        self.subtotal = sum(
            line.total for line in self.lines.all()
        ) or Decimal('0')

        if self.template:
            tax_rate = self.template.tax_rate_percent / 100
            self.tax_amount = self.subtotal * tax_rate
            self.total = self.subtotal + self.tax_amount
        else:
            self.tax_amount = Decimal('0')
            self.total = self.subtotal


class ProposalLine(models.Model):
    """Line item in proposal."""

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='lines'
    )

    position = models.IntegerField(default=1)  # Order in proposal
    description = models.CharField(max_length=500)

    # Quantity & Unit
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit = models.CharField(max_length=20)  # m², lfm, Stk, etc.

    # Pricing
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )

    class Meta:
        ordering = ['proposal', 'position']
        unique_together = [['proposal', 'position']]

    def __str__(self):
        return f"{self.description} ({self.quantity} {self.unit})"

    def calculate_total(self) -> Decimal:
        """Calculate line total with discount."""
        subtotal = self.quantity * self.unit_price
        discount = subtotal * (self.discount_percent / 100)
        return subtotal - discount


class ProposalCalculationLog(models.Model):
    """Log of proposal pricing calculations for audit."""

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='calculation_logs'
    )

    # Input data
    material_type = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)

    # Calculation breakdown
    base_material_cost = models.DecimalField(max_digits=10, decimal_places=2)
    base_labor_hours = models.DecimalField(max_digits=10, decimal_places=2)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2)

    # Factors applied
    complexity_factor = models.DecimalField(max_digits=4, decimal_places=2)
    surface_factor = models.DecimalField(max_digits=4, decimal_places=2)
    quality_tier = models.CharField(max_length=50, blank=True)

    # Result
    calculated_unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Calculation: {self.material_type} @ {self.calculated_unit_price}€/{self.unit}"
