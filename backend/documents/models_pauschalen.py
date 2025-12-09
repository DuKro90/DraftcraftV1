"""
Betriebspauschalen Models - Phase 4C

Fixed and conditional business expense rules (An-/Abfahrt, Entsorgung, Montage, etc.)
Extends TIER 2/3 calculation with fixed costs that aren't material-based.

Supports:
- Fixed amounts (e.g., 50€ Anfahrt)
- Conditional rules (e.g., IF Distanz > 50km THEN 100€ ELSE 50€)
- Per-unit costs (e.g., 80€ per m³ Entsorgung)
- Minimum order surcharges (e.g., +200€ if order < 1000€)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class BetriebspauschaleRegel(models.Model):
    """
    Business expense rule with conditional logic.

    Examples:
        - Anfahrt: 50€ (< 50km), 100€ (> 50km)
        - Entsorgung: 80€ pro m³
        - Montage: 150€ Grundpauschale
        - Kleinauftragszuschlag: 200€ (bei < 1000€ Auftragswert)
    """

    PAUSCHALE_TYP_CHOICES = [
        ('anfahrt', 'Anfahrt'),
        ('entsorgung', 'Entsorgung'),
        ('montage', 'Montage/Installation'),
        ('kleinauftrag', 'Kleinauftragszuschlag'),
        ('verpackung', 'Verpackung/Versand'),
        ('planung', 'Planungs-/Beratungskosten'),
        ('miete', 'Geräte-/Werkzeugmiete'),
        ('genehmigung', 'Genehmigungsgebühren'),
        ('sonstiges', 'Sonstige Pauschale'),
    ]

    BERECHNUNGSART_CHOICES = [
        ('fest', 'Fester Betrag'),
        ('pro_einheit', 'Pro Einheit (m³, km, etc.)'),
        ('prozent', 'Prozentsatz vom Auftragswert'),
        ('konditional', 'Konditional (IF-THEN-ELSE)'),
    ]

    EINHEIT_CHOICES = [
        ('eur', 'EUR'),
        ('km', 'Kilometer'),
        ('m3', 'Kubikmeter'),
        ('h', 'Stunden'),
        ('stk', 'Stück'),
        ('prozent', 'Prozent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Zuordnung
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='betriebspauschalen',
        help_text="Firma/User für diese Pauschale"
    )

    # Identifikation
    name = models.CharField(
        max_length=200,
        help_text="Name der Pauschale (z.B. 'Anfahrt Standard')"
    )
    pauschale_typ = models.CharField(
        max_length=20,
        choices=PAUSCHALE_TYP_CHOICES,
        help_text="Art der Pauschale"
    )
    beschreibung = models.TextField(
        blank=True,
        help_text="Detaillierte Beschreibung"
    )

    # Berechnungs-Logik
    berechnungsart = models.CharField(
        max_length=20,
        choices=BERECHNUNGSART_CHOICES,
        default='fest',
        help_text="Wie wird diese Pauschale berechnet?"
    )

    # Für 'fest' und 'pro_einheit'
    betrag = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Betrag in EUR (für 'fest') oder Preis pro Einheit (für 'pro_einheit')"
    )

    # Für 'pro_einheit'
    einheit = models.CharField(
        max_length=20,
        choices=EINHEIT_CHOICES,
        default='eur',
        help_text="Einheit für 'pro_einheit' Berechnung"
    )

    # Für 'prozent'
    prozentsatz = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Prozentsatz (z.B. 5.00 für 5%)"
    )

    # Für 'konditional' - verwendet Level 2 DSL
    konditional_regel = models.JSONField(
        null=True,
        blank=True,
        help_text="""
        JSON-Regel für konditionale Logik (Level 2 DSL).

        Beispiel:
        {
            "operation": "IF_THEN_ELSE",
            "bedingung": {
                "operation": "GREATER_THAN",
                "links": {"quelle": "distanz_km"},
                "rechts": 50
            },
            "dann": {"betrag": 100.00},
            "sonst": {"betrag": 50.00}
        }
        """
    )

    # Anwendungs-Bedingungen
    min_auftragswert = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimaler Auftragswert für Anwendung (leer = keine Bedingung)"
    )
    max_auftragswert = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximaler Auftragswert für Anwendung (leer = keine Bedingung)"
    )

    # Status & Priorität
    ist_aktiv = models.BooleanField(
        default=True,
        help_text="Ist diese Pauschale aktiv?"
    )
    prioritaet = models.IntegerField(
        default=100,
        help_text="Niedrigere Zahl = höhere Priorität (bei mehreren Pauschalen gleichen Typs)"
    )

    # Zeitliche Gültigkeit
    gueltig_ab = models.DateField(
        null=True,
        blank=True,
        help_text="Ab wann ist diese Pauschale gültig?"
    )
    gueltig_bis = models.DateField(
        null=True,
        blank=True,
        help_text="Bis wann ist diese Pauschale gültig?"
    )

    # Metadaten
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    # Zusätzliche Daten
    zusatz_daten = models.JSONField(
        default=dict,
        blank=True,
        help_text="Zusätzliche Konfiguration (z.B. Distanzberechnung, Entsorgungsklassen)"
    )

    class Meta:
        verbose_name = "Betriebspauschale-Regel"
        verbose_name_plural = "Betriebspauschale-Regeln"
        ordering = ['pauschale_typ', 'prioritaet', 'name']
        indexes = [
            models.Index(fields=['user', 'ist_aktiv']),
            models.Index(fields=['pauschale_typ', 'ist_aktiv']),
            models.Index(fields=['gueltig_ab', 'gueltig_bis']),
        ]

    def __str__(self):
        if self.berechnungsart == 'fest':
            return f"{self.name}: {self.betrag}€"
        elif self.berechnungsart == 'pro_einheit':
            return f"{self.name}: {self.betrag}€/{self.get_einheit_display()}"
        elif self.berechnungsart == 'prozent':
            return f"{self.name}: {self.prozentsatz}%"
        else:
            return f"{self.name} (konditional)"

    def is_applicable_for_order(self, auftragswert: Decimal, datum: 'date' = None) -> bool:
        """
        Check if this rule is applicable for a given order value and date.

        Args:
            auftragswert: Order value in EUR
            datum: Date to check (default: today)

        Returns:
            True if applicable
        """
        from datetime import date as date_module

        if not self.ist_aktiv:
            return False

        # Check order value range
        if self.min_auftragswert and auftragswert < self.min_auftragswert:
            return False
        if self.max_auftragswert and auftragswert > self.max_auftragswert:
            return False

        # Check validity period
        if datum is None:
            datum = date_module.today()

        if self.gueltig_ab and datum < self.gueltig_ab:
            return False
        if self.gueltig_bis and datum > self.gueltig_bis:
            return False

        return True


class PauschaleAnwendung(models.Model):
    """
    Record of applied business expense to a specific extraction/calculation.

    Tracks which expenses were applied and with what amounts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Zuordnung
    extraction_result = models.ForeignKey(
        'documents.ExtractionResult',
        on_delete=models.CASCADE,
        related_name='pauschale_anwendungen',
        help_text="Extraction zu der diese Pauschale gehört"
    )

    pauschale = models.ForeignKey(
        BetriebspauschaleRegel,
        on_delete=models.CASCADE,
        related_name='anwendungen',
        help_text="Angewendete Pauschale-Regel"
    )

    # Berechnungs-Details
    berechnungsgrundlage = models.JSONField(
        help_text="""
        Grundlage für Berechnung (z.B. {'distanz_km': 75, 'entsorgung_m3': 2.5})
        """
    )

    menge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Menge (für 'pro_einheit'), leer für 'fest'"
    )

    berechneter_betrag = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Errechneter Betrag in EUR"
    )

    # User-Editierbarkeit
    manuell_ueberschrieben = models.BooleanField(
        default=False,
        help_text="Wurde der Betrag manuell überschrieben?"
    )

    manueller_betrag = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manuell überschriebener Betrag"
    )

    # Notizen
    notizen = models.TextField(
        blank=True,
        help_text="Notizen zur Anwendung"
    )

    # Metadaten
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pauschale-Anwendung"
        verbose_name_plural = "Pauschale-Anwendungen"
        ordering = ['-erstellt_am']
        indexes = [
            models.Index(fields=['extraction_result', 'erstellt_am']),
        ]

    def __str__(self):
        betrag = self.get_final_betrag()
        return f"{self.pauschale.name}: {betrag}€"

    def get_final_betrag(self) -> Decimal:
        """Return final amount (manual override if exists, otherwise calculated)."""
        if self.manuell_ueberschrieben and self.manueller_betrag is not None:
            return self.manueller_betrag
        return self.berechneter_betrag
