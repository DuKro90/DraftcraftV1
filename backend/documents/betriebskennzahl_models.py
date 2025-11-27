# -*- coding: utf-8 -*-
"""Betriebskennzahlen (operational metrics) models for calculation and pricing.

Three-tier hierarchy:
- TIER 1: BetriebskennzahlTemplate - Global handcraft standards (wood types, finishes, techniques)
- TIER 2: IndividuelleBetriebskennzahl - Company-specific metrics (overhead, margins, labor rates)
- TIER 3: SaisonaleMarge - Dynamic adjustments (seasonal, campaigns, customer-specific)
"""

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


class BetriebskennzahlTemplate(models.Model):
    """Global/standard metrics applicable to all German woodworking (Handwerk) businesses.

    TIER 1: Global Standards that define handcraft work pricing factors.
    Examples: Holzarten (oak, beech, pine), Oberflächenbearbeitungen (sanding, lacquering, oiling),
    Komplexität (turned, milled, carved, hand-carved, intarsia work).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Template metadata
    name = models.CharField(
        max_length=100,
        help_text="Template name (e.g., 'Standard Woodcraft Factors 2024')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of template and its application"
    )

    # Version control
    version = models.CharField(
        max_length=20,
        default='1.0',
        help_text="Version string (e.g., '1.0', '2.1') for tracking changes"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Active templates are available for company selection"
    )

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='betriebskennzahl_templates_created'
    )

    class Meta:
        ordering = ['-is_active', '-updated_at']
        indexes = [
            models.Index(fields=['is_active', '-updated_at']),
            models.Index(fields=['created_by']),
        ]
        verbose_name = 'Betriebskennzahl Template'
        verbose_name_plural = 'Betriebskennzahl Templates'

    def __str__(self):
        return f"{self.name} (v{self.version})" + (" [ACTIVE]" if self.is_active else " [INACTIVE]")


class HolzartKennzahl(models.Model):
    """Wood type (Holzart) pricing factors.

    Examples:
    - Eiche (Oak): premium hardwood, factor 1.3
    - Buche (Beech): hardwood, factor 1.2
    - Kiefer (Pine): softwood, factor 0.9
    - Fichte (Spruce): softwood, factor 0.8
    """

    KATEGORIE_CHOICES = [
        ('hartholz', 'Hartholz (Hardwood)'),
        ('weichholz', 'Weichholz (Softwood)'),
        ('exotisch', 'Exotisch (Exotic)'),
    ]

    VERFUEGBARKEIT_CHOICES = [
        ('staendig', 'Ständig verfügbar (Always Available)'),
        ('saisonal', 'Saisonal (Seasonal)'),
        ('bestellen', 'Auf Bestellung (On Order)'),
        ('selten', 'Selten (Rare)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        BetriebskennzahlTemplate,
        on_delete=models.CASCADE,
        related_name='holzarten'
    )

    # Wood type
    holzart = models.CharField(
        max_length=50,
        help_text="German wood name (e.g., 'eiche', 'buche', 'kiefer', 'fichte')"
    )
    kategorie = models.CharField(
        max_length=20,
        choices=KATEGORIE_CHOICES,
        default='hartholz'
    )

    # Pricing factor
    preis_faktor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Multiplier for base price (1.0 = base, 1.3 = 30% premium)"
    )

    # Availability
    verfuegbarkeit = models.CharField(
        max_length=20,
        choices=VERFUEGBARKEIT_CHOICES,
        default='staendig'
    )

    # Status
    is_enabled = models.BooleanField(
        default=True,
        help_text="Can be disabled to hide from calculations"
    )

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['kategorie', 'holzart']
        indexes = [
            models.Index(fields=['template', 'kategorie']),
            models.Index(fields=['template', 'is_enabled']),
        ]
        unique_together = [('template', 'holzart')]
        verbose_name = 'Holzart Kennzahl'
        verbose_name_plural = 'Holzart Kennzahlen'

    def __str__(self):
        return f"{self.holzart} ({self.get_kategorie_display()}) × {self.preis_faktor}"


class OberflächenbearbeitungKennzahl(models.Model):
    """Surface finishing (Oberflächenbearbeitung) factors.

    Examples:
    - Schleifen (Sanding): 1.05x price, 1.2x time
    - Lackieren (Lacquering): 1.15x price, 1.3x time
    - Ölen (Oiling): 1.10x price, 1.1x time
    - Wachsen (Waxing): 1.08x price, 1.05x time
    - Naturbelassen (Unfinished): 1.0x price, 1.0x time
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        BetriebskennzahlTemplate,
        on_delete=models.CASCADE,
        related_name='oberflaechenbearbeitungen'
    )

    # Surface type
    bearbeitung = models.CharField(
        max_length=50,
        help_text="German surface treatment name (e.g., 'schleifen', 'lackieren', 'oelen', 'wachsen')"
    )

    # Factors
    preis_faktor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Price multiplier for this finish"
    )
    zeit_faktor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Labor time multiplier for this finish"
    )

    # Status
    is_enabled = models.BooleanField(default=True)

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['bearbeitung']
        indexes = [
            models.Index(fields=['template', 'is_enabled']),
        ]
        unique_together = [('template', 'bearbeitung')]
        verbose_name = 'Oberflächenbearbeitung Kennzahl'
        verbose_name_plural = 'Oberflächenbearbeitung Kennzahlen'

    def __str__(self):
        return f"{self.bearbeitung} (Preis: ×{self.preis_faktor}, Zeit: ×{self.zeit_faktor})"


class KomplexitaetKennzahl(models.Model):
    """Complexity/Technique factors for special woodworking techniques.

    Examples:
    - Gedrechselt (Turned): 1.25x price, 1.5x time, difficulty 2
    - Gefräst (Milled): 1.15x price, 1.25x time, difficulty 2
    - Geschnitzt (Carved): 1.5x price, 2.0x time, difficulty 3
    - Handgeschnitzt (Hand-carved): 2.0x price, 3.0x time, difficulty 3
    - Intarsia: 1.8x price, 2.5x time, difficulty 3
    """

    SCHWIERIGKEIT_CHOICES = [
        (1, 'Einfach (Easy)'),
        (2, 'Mittel (Medium)'),
        (3, 'Schwierig (Hard)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        BetriebskennzahlTemplate,
        on_delete=models.CASCADE,
        related_name='komplexitaeten'
    )

    # Technique
    technik = models.CharField(
        max_length=50,
        help_text="German technique name (e.g., 'gedrechselt', 'gefraest', 'geschnitzt', 'hand_geschnitzt', 'intarsia')"
    )

    # Factors
    preis_faktor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Price multiplier for this technique"
    )
    zeit_faktor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Labor time multiplier for this technique"
    )

    # Difficulty
    schwierigkeitsgrad = models.IntegerField(
        choices=SCHWIERIGKEIT_CHOICES,
        default=1,
        help_text="Difficulty level (affects routing and validation)"
    )

    # Status
    is_enabled = models.BooleanField(default=True)

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['schwierigkeitsgrad', 'technik']
        indexes = [
            models.Index(fields=['template', 'schwierigkeitsgrad']),
            models.Index(fields=['template', 'is_enabled']),
        ]
        unique_together = [('template', 'technik')]
        verbose_name = 'Komplexität Kennzahl'
        verbose_name_plural = 'Komplexität Kennzahlen'

    def __str__(self):
        return f"{self.technik} ({self.get_schwierigkeitsgrad_display()}) - ×{self.preis_faktor}, Zeit: ×{self.zeit_faktor}"


class IndividuelleBetriebskennzahl(models.Model):
    """TIER 2: Company-specific operational metrics.

    Each user/company can customize:
    - Betriebskosten (overhead)
    - Gewinnmarge (profit margin)
    - Stundensatz (labor rate)
    - Which template to use (if any)
    - Toggles for different metric tiers
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='betriebskennzahl'
    )

    # Company metrics
    betriebskosten_umlage = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monthly overhead costs (e.g., rent, utilities, insurance)"
    )
    gewinnmarge_prozent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('25.00'),
        help_text="Target profit margin as percentage (25% = 0.25)"
    )
    stundensatz_arbeit = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('85.00'),
        help_text="Labor hourly rate in EUR"
    )

    # Template selection (TIER 1)
    handwerk_template = models.ForeignKey(
        BetriebskennzahlTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Global standards template (if using global metrics)"
    )

    # Feature toggles - TIER 1 (Global Handwerk Standards)
    use_handwerk_standard = models.BooleanField(
        default=True,
        help_text="Enable Holzart, Oberflächenbearbeitung, Komplexität factors from template"
    )

    # Feature toggles - TIER 2 (Company-Specific)
    use_custom_materials = models.BooleanField(
        default=False,
        help_text="Enable custom material list (overrides global materials)"
    )

    # Feature toggles - TIER 3 (Dynamic Adjustments)
    use_seasonal_adjustments = models.BooleanField(
        default=False,
        help_text="Enable seasonal pricing adjustments"
    )
    use_customer_discounts = models.BooleanField(
        default=False,
        help_text="Enable customer-specific discounts"
    )
    use_bulk_discounts = models.BooleanField(
        default=False,
        help_text="Enable quantity-based bulk discounts"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive companies won't use these metrics"
    )

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['handwerk_template']),
        ]
        verbose_name = 'Individuelle Betriebskennzahl'
        verbose_name_plural = 'Individuelle Betriebskennzahlen'

    def __str__(self):
        return f"{self.user.username} - {self.stundensatz_arbeit}€/h ({self.gewinnmarge_prozent}% margin)"

    @property
    def effective_templates(self) -> dict:
        """Return which templates are active and configured."""
        return {
            'tier_1_global': self.use_handwerk_standard and self.handwerk_template,
            'tier_2_custom': self.use_custom_materials,
            'tier_3_dynamic': self.use_seasonal_adjustments or self.use_customer_discounts or self.use_bulk_discounts,
        }


class MateriallistePosition(models.Model):
    """TIER 2: Material catalog entries with company-specific pricing.

    Each company can define their own material list with custom suppliers, pricing, and discounts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='material_liste'
    )

    # Material info
    material_name = models.CharField(
        max_length=200,
        help_text="Material description (e.g., 'Eichenbretter 25mm, A-Qualität')"
    )
    sku = models.CharField(
        max_length=50,
        help_text="Internal SKU/Material code"
    )

    # Supplier
    lieferant = models.CharField(
        max_length=100,
        help_text="Supplier name"
    )

    # Pricing
    standardkosten_eur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost per unit from supplier (EUR)"
    )
    verpackungseinheit = models.CharField(
        max_length=50,
        default='1',
        help_text="Packaging unit (e.g., '50 Bretter', '25kg', '1 Stk')"
    )

    # Availability
    VERFUEGBARKEIT_CHOICES = [
        ('staendig', 'Ständig (Always)'),
        ('saisonal', 'Saisonal (Seasonal)'),
        ('selten', 'Selten (Rare)'),
        ('bestellen', 'Auf Bestellung (On Order)'),
    ]
    verfuegbarkeit = models.CharField(
        max_length=20,
        choices=VERFUEGBARKEIT_CHOICES,
        default='staendig'
    )

    # Bulk discounts
    rabatt_ab_100 = models.IntegerField(
        default=0,
        help_text="Discount percentage when quantity >= 100"
    )
    rabatt_ab_500 = models.IntegerField(
        default=0,
        help_text="Discount percentage when quantity >= 500"
    )

    # Status
    is_enabled = models.BooleanField(
        default=True,
        help_text="Can be disabled to exclude from calculations"
    )

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['material_name']
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
            models.Index(fields=['user', 'lieferant']),
            models.Index(fields=['sku']),
        ]
        unique_together = [('user', 'sku')]
        verbose_name = 'Materialliste Position'
        verbose_name_plural = 'Materialliste Positionen'

    def __str__(self):
        return f"{self.material_name} ({self.lieferant}) - €{self.standardkosten_eur}"

    def get_discount_percent(self, quantity: int) -> int:
        """Get applicable discount for given quantity."""
        if quantity >= 500:
            return self.rabatt_ab_500
        if quantity >= 100:
            return self.rabatt_ab_100
        return 0


class SaisonaleMarge(models.Model):
    """TIER 3: Dynamic seasonal or temporary pricing adjustments.

    Examples:
    - 10% holiday discount for existing customers (Nov 15 - Dec 24)
    - Summer campaign: 15% off for new projects
    - Black Friday: 20% discount
    """

    ADJUSTMENT_TYPE_CHOICES = [
        ('prozent', 'Prozentsatz (%)'),
        ('absolute', 'Absolute Summe (€)'),
    ]

    APPLICABLE_TO_CHOICES = [
        ('alle', 'Alle Projekte (All Projects)'),
        ('bestehende_kunden', 'Bestehende Kunden (Existing Customers)'),
        ('neue_kunden', 'Neue Kunden (New Customers)'),
        ('kampagne', 'Kampagne-Spezifisch (Campaign-Specific)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saisonale_margen'
    )

    # Campaign info
    name = models.CharField(
        max_length=100,
        help_text="Campaign name (e.g., 'Weihnachts-Rabatt 2024')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the campaign"
    )

    # Adjustment
    adjustment_type = models.CharField(
        max_length=20,
        choices=ADJUSTMENT_TYPE_CHOICES,
        help_text="Percentage or absolute amount"
    )
    value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Percentage (e.g., 10) or absolute amount (e.g., 50.00)"
    )

    # Date range
    start_date = models.DateField(
        help_text="Campaign start date"
    )
    end_date = models.DateField(
        help_text="Campaign end date"
    )

    # Applicability
    applicable_to = models.CharField(
        max_length=50,
        choices=APPLICABLE_TO_CHOICES,
        help_text="Which customers/projects qualify"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Can be disabled without deleting"
    )

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date', 'name']
        indexes = [
            models.Index(fields=['user', 'is_active', 'start_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        verbose_name = 'Saisonale Marge'
        verbose_name_plural = 'Saisonale Margen'

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    def is_current(self) -> bool:
        """Check if this campaign is currently active (date-wise)."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date


class AdminActionAudit(models.Model):
    """DSGVO-compliant audit trail for all admin decisions on calculation metrics.

    Tracks:
    - Who made the change
    - What changed (old value → new value)
    - When it happened
    - Why (reasoning)
    - Impact (how many documents affected)
    - Status (pending/applied/reverted)
    - Automatic deletion after retention period (DSGVO Art. 17)
    """

    ACTION_TYPE_CHOICES = [
        ('template_create', 'Template Created'),
        ('template_update', 'Template Updated'),
        ('template_delete', 'Template Deleted'),
        ('holzart_enable', 'Wood Type Enabled'),
        ('holzart_disable', 'Wood Type Disabled'),
        ('holzart_update', 'Wood Type Price/Factor Updated'),
        ('material_add', 'Material Added to List'),
        ('material_update', 'Material Updated'),
        ('material_remove', 'Material Removed'),
        ('seasonal_create', 'Seasonal Campaign Created'),
        ('seasonal_update', 'Seasonal Campaign Updated'),
        ('seasonal_delete', 'Seasonal Campaign Deleted'),
        ('pattern_fix_apply', 'Pattern Fix Applied'),
        ('confidence_threshold_update', 'Confidence Threshold Updated'),
        ('field_weight_update', 'Field Weight Updated'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('applied', 'Applied'),
        ('reverted', 'Reverted'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Admin who made the change
    admin_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_audit_actions'
    )
    affected_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affected_by_admin_actions',
        help_text="Affected user (null = global change)"
    )

    # Change details
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPE_CHOICES,
        help_text="Type of action performed"
    )
    old_value = models.JSONField(
        default=dict,
        blank=True,
        help_text="Previous value (before change)"
    )
    new_value = models.JSONField(
        default=dict,
        blank=True,
        help_text="New value (after change)"
    )

    # Impact
    affected_documents = models.IntegerField(
        default=0,
        help_text="How many documents could be affected by this change"
    )

    # Reasoning (audit trail)
    reasoning = models.TextField(
        help_text="Why this change was made"
    )

    # Status workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Application status"
    )
    status_changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_admin_actions'
    )
    status_changed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    status_reason = models.TextField(
        blank=True,
        help_text="Reason for approval/rejection"
    )

    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)

    # DSGVO: Automatic retention and deletion
    retention_until = models.DateTimeField(
        help_text="After this date, this record can be deleted (DSGVO Art. 17)"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin_user', '-timestamp']),
            models.Index(fields=['affected_user', '-timestamp']),
            models.Index(fields=['status', 'action_type']),
            models.Index(fields=['retention_until']),
        ]
        verbose_name = 'Admin Action Audit'
        verbose_name_plural = 'Admin Action Audits'

    def __str__(self):
        target = self.affected_user.username if self.affected_user else "GLOBAL"
        return f"{self.get_action_type_display()} ({target}) - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_pending_review(self) -> bool:
        """Check if this action is pending approval."""
        return self.status == 'pending'

    @property
    def is_approved(self) -> bool:
        """Check if this action was approved."""
        return self.status == 'applied'

    @property
    def can_revert(self) -> bool:
        """Check if this action can be reverted."""
        from django.utils import timezone
        return (self.status == 'applied' and
                timezone.now() <= timezone.make_aware(
                    timezone.datetime.combine(self.timestamp.date(), timezone.datetime.max.time())
                ) + timezone.timedelta(days=7))  # Can revert within 7 days
