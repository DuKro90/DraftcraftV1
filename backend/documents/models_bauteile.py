"""
Standardbauteile Models - Phase 4B

Provides standardized construction components calculation system for German Handwerk.
Supports:
- Multi-trade component catalogs (Tischler, Zimmerer, Polsterer)
- Automatic quantity calculation based on extraction results
- Flexible rule engine (Level 1: Simple arithmetic operations)
- Geometry-based calculations (e.g., ABS edge lengths)
- Version control and audit trail for price matrices
"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class StandardBauteil(models.Model):
    """
    Standardized construction component (e.g., Topfband, ABS-Kante, Griff).

    Examples:
        - Topfband 35mm Standard (Tischler)
        - Sparrenpfettenanker (Zimmerer)
        - Federkern 5-Gang (Polsterer)
    """

    KATEGORIE_CHOICES = [
        ('beschlag', 'Beschläge'),
        ('verbinder', 'Verbindungsmittel'),
        ('kante', 'Kantenbearbeitung'),
        ('befestigung', 'Befestigungsmittel'),
        ('oberflaeche', 'Oberflächenmaterial'),
        ('sonstiges', 'Sonstiges'),
    ]

    GEWERK_CHOICES = [
        ('tischler', 'Tischler/Schreiner'),
        ('zimmerer', 'Zimmerer'),
        ('polsterer', 'Polsterer'),
        ('allgemein', 'Gewerkübergreifend'),
    ]

    EINHEIT_CHOICES = [
        ('stk', 'Stück'),
        ('lfm', 'Laufmeter'),
        ('m2', 'Quadratmeter'),
        ('kg', 'Kilogramm'),
        ('pkt', 'Paket'),
        ('set', 'Set'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identifikation
    artikel_nr = models.CharField(
        max_length=50,
        unique=True,
        help_text="Eindeutige Artikel-Nummer (z.B. HF-12345 für Häfele-Artikel)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Bezeichnung des Bauteils (z.B. 'Topfband 35mm Standard')"
    )
    beschreibung = models.TextField(
        blank=True,
        help_text="Detaillierte Beschreibung, technische Daten"
    )

    # Kategorisierung
    kategorie = models.CharField(
        max_length=20,
        choices=KATEGORIE_CHOICES,
        help_text="Bauteil-Kategorie"
    )
    gewerke = ArrayField(
        models.CharField(max_length=20, choices=GEWERK_CHOICES),
        help_text="Gewerke, für die dieses Bauteil relevant ist (Mehrfachauswahl)"
    )

    # Preisangaben
    einheit = models.CharField(
        max_length=10,
        choices=EINHEIT_CHOICES,
        help_text="Mengeneinheit"
    )
    einzelpreis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Preis pro Einheit (netto, in Euro)"
    )

    # Lieferanten-Info
    lieferant = models.CharField(
        max_length=100,
        blank=True,
        help_text="Hauptlieferant (z.B. Häfele, Wurth)"
    )
    lieferanten_artikel_nr = models.CharField(
        max_length=100,
        blank=True,
        help_text="Artikel-Nummer beim Lieferanten"
    )

    # Status & Verfügbarkeit
    ist_aktiv = models.BooleanField(
        default=True,
        help_text="Aktiv in Kalkulationen verwenden?"
    )
    verfuegbar_ab = models.DateField(
        null=True,
        blank=True,
        help_text="Ab wann ist das Bauteil verfügbar?"
    )
    verfuegbar_bis = models.DateField(
        null=True,
        blank=True,
        help_text="Bis wann ist das Bauteil verfügbar? (z.B. Auslauf-Artikel)"
    )

    # Metadaten
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)
    erstellt_von = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='erstellte_bauteile'
    )

    # Zusätzliche Daten (flexibel)
    zusatz_daten = models.JSONField(
        default=dict,
        blank=True,
        help_text="Zusätzliche Daten (z.B. Gewicht, Abmessungen, technische Specs)"
    )

    class Meta:
        verbose_name = "Standard-Bauteil"
        verbose_name_plural = "Standard-Bauteile"
        ordering = ['kategorie', 'name']
        indexes = [
            models.Index(fields=['kategorie', 'ist_aktiv']),
            models.Index(fields=['artikel_nr']),
        ]

    def __str__(self):
        return f"{self.artikel_nr} - {self.name} ({self.einzelpreis}€/{self.einheit})"


class BauteilRegel(models.Model):
    """
    Calculation rule for determining component quantities.

    Level 1 (Current): Simple arithmetic operations
    - MULTIPLY: factor × component_count
    - ADD: sum of multiple terms
    - SUBTRACT: difference

    Example Rules:
        - "3 Topfbänder pro Tür" = MULTIPLY(3, Tür.anzahl)
        - "2 Griffe pro Tür" = MULTIPLY(2, Tür.anzahl)
        - "4 Bodenhalter pro Einlegeboden" = MULTIPLY(4, Einlegeboden.anzahl)
    """

    OPERATION_CHOICES = [
        ('MULTIPLY', 'Multiplizieren'),
        ('ADD', 'Addieren'),
        ('SUBTRACT', 'Subtrahieren'),
        ('FIXED', 'Fester Wert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Zuordnung
    bauteil = models.ForeignKey(
        StandardBauteil,
        on_delete=models.CASCADE,
        related_name='regeln',
        help_text="Bauteil, für das diese Regel gilt"
    )

    # Regel-Definition
    name = models.CharField(
        max_length=200,
        help_text="Beschreibung der Regel (z.B. 'Topfbänder pro Tür')"
    )

    # Level 1: Simple DSL
    regel_definition = models.JSONField(
        help_text="""
        JSON-Struktur für Regel-Definition.

        Level 1 Beispiele:

        1. MULTIPLY: {"operation": "MULTIPLY", "faktor": 3, "komponente": "Tür", "attribut": "anzahl"}
           → 3 × Anzahl Türen

        2. FIXED: {"operation": "FIXED", "wert": 10}
           → Immer 10 Stück

        3. ADD: {"operation": "ADD", "terme": [
                    {"operation": "MULTIPLY", "faktor": 3, "komponente": "Tür", "attribut": "anzahl"},
                    {"operation": "MULTIPLY", "faktor": 2, "komponente": "Schublade", "attribut": "anzahl"}
                ]}
           → (3 × Türen) + (2 × Schubladen)
        """
    )

    # Priorität (falls mehrere Regeln)
    prioritaet = models.IntegerField(
        default=100,
        help_text="Niedrigere Zahl = höhere Priorität (wird zuerst angewendet)"
    )

    # Status
    ist_aktiv = models.BooleanField(
        default=True,
        help_text="Regel aktiv?"
    )

    # Metadaten
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bauteil-Regel"
        verbose_name_plural = "Bauteil-Regeln"
        ordering = ['bauteil', 'prioritaet']
        indexes = [
            models.Index(fields=['bauteil', 'ist_aktiv']),
        ]

    def __str__(self):
        return f"{self.bauteil.name}: {self.name}"


class BauteilKatalog(models.Model):
    """
    Version-controlled component catalog for a company.

    Allows:
    - Multiple price matrices (e.g., Q4 2024, Q1 2025)
    - Rollback to previous versions
    - Audit trail for price changes
    - Excel/CSV export and import
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identifikation
    name = models.CharField(
        max_length=200,
        help_text="Name des Katalogs (z.B. 'Beschlagskatalog Q1 2025')"
    )
    version = models.CharField(
        max_length=50,
        help_text="Versions-Nummer (z.B. '2025.1', 'Q1-2025')"
    )

    # Zuordnung
    firma = models.ForeignKey(
        'documents.CompanyProfile',
        on_delete=models.CASCADE,
        related_name='bauteil_kataloge',
        null=True,
        blank=True,
        help_text="Firma, der dieser Katalog gehört (leer = global)"
    )
    gewerk = models.CharField(
        max_length=20,
        choices=StandardBauteil.GEWERK_CHOICES,
        help_text="Gewerk für diesen Katalog"
    )

    # Zeitraum
    gueltig_ab = models.DateField(
        help_text="Ab wann ist dieser Katalog gültig?"
    )
    gueltig_bis = models.DateField(
        null=True,
        blank=True,
        help_text="Bis wann ist dieser Katalog gültig? (leer = unbegrenzt)"
    )

    # Bauteile in diesem Katalog
    bauteile = models.ManyToManyField(
        StandardBauteil,
        through='BauteilKatalogPosition',
        related_name='kataloge'
    )

    # Status
    ist_aktiv = models.BooleanField(
        default=True,
        help_text="Ist dieser Katalog aktiv?"
    )
    ist_standard = models.BooleanField(
        default=False,
        help_text="Ist dies der Standard-Katalog für neue Kalkulationen?"
    )

    # Versionierung
    vorgaenger_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nachfolger_versionen',
        help_text="Vorherige Version dieses Katalogs (für Rollback)"
    )

    # Metadaten
    beschreibung = models.TextField(
        blank=True,
        help_text="Änderungen in dieser Version, Notizen"
    )
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)
    erstellt_von = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='erstellte_kataloge'
    )

    class Meta:
        verbose_name = "Bauteil-Katalog"
        verbose_name_plural = "Bauteil-Kataloge"
        ordering = ['-gueltig_ab', 'name']
        unique_together = [['firma', 'version', 'gewerk']]
        indexes = [
            models.Index(fields=['firma', 'gewerk', 'ist_aktiv']),
            models.Index(fields=['gueltig_ab', 'gueltig_bis']),
        ]

    def __str__(self):
        firma_str = f"{self.firma.name} - " if self.firma else "Global - "
        return f"{firma_str}{self.name} (v{self.version})"


class BauteilKatalogPosition(models.Model):
    """
    Through-model for BauteilKatalog <-> StandardBauteil with catalog-specific pricing.

    Allows overriding global prices per catalog version.
    """

    katalog = models.ForeignKey(
        BauteilKatalog,
        on_delete=models.CASCADE
    )
    bauteil = models.ForeignKey(
        StandardBauteil,
        on_delete=models.CASCADE
    )

    # Katalog-spezifischer Preis (überschreibt StandardBauteil.einzelpreis)
    katalog_einzelpreis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Preis in diesem Katalog (leer = Standard-Preis verwenden)"
    )

    # Position im Katalog
    position = models.IntegerField(
        default=0,
        help_text="Sortier-Position im Katalog"
    )

    # Verfügbarkeit
    ist_aktiv_in_katalog = models.BooleanField(
        default=True,
        help_text="Ist dieses Bauteil in diesem Katalog aktiv?"
    )

    class Meta:
        verbose_name = "Katalog-Position"
        verbose_name_plural = "Katalog-Positionen"
        ordering = ['katalog', 'position', 'bauteil']
        unique_together = [['katalog', 'bauteil']]

    def __str__(self):
        preis = self.katalog_einzelpreis or self.bauteil.einzelpreis
        return f"{self.katalog.name} - {self.bauteil.name} ({preis}€)"

    def get_preis(self):
        """Return catalog-specific price or fall back to standard price."""
        return self.katalog_einzelpreis or self.bauteil.einzelpreis


class GeometrieBerechnung(models.Model):
    """
    Automatic geometry-based calculations (e.g., ABS edge lengths).

    Stores calculated dimensions with user-editable checkboxes.
    Linked to extraction results for automatic pre-population.
    """

    KANTEN_TYP_CHOICES = [
        ('korpus_außen', 'Korpus Außenkanten'),
        ('korpus_innen', 'Korpus Innenkanten'),
        ('tür_außen', 'Tür Außenkanten'),
        ('einlegeboden_vorder', 'Einlegeboden Vorderkante'),
        ('einlegeboden_seite', 'Einlegeboden Seitenkanten'),
        ('schublade_außen', 'Schublade Außenkanten'),
        ('rueckseite', 'Rückseite (meist unsichtbar)'),
        ('sonstiges', 'Sonstiges'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Zuordnung zu Extraktion
    extraction_result = models.ForeignKey(
        'documents.ExtractionResult',
        on_delete=models.CASCADE,
        related_name='geometrie_berechnungen',
        help_text="Zugeordnetes Extraktions-Ergebnis"
    )

    # Bauteil-Typ (z.B. ABS-Kante)
    bauteil = models.ForeignKey(
        StandardBauteil,
        on_delete=models.CASCADE,
        related_name='geometrie_berechnungen',
        help_text="Bauteil, für das diese Geometrie berechnet wird"
    )

    # Kanten-Spezifikation
    kanten_typ = models.CharField(
        max_length=30,
        choices=KANTEN_TYP_CHOICES,
        help_text="Art der Kante"
    )

    # Berechnung
    formel = models.TextField(
        help_text="Formel für Berechnung (dokumentarisch)"
    )
    berechnete_laenge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Automatisch berechnete Länge (in lfm)"
    )

    # User-Editierbarkeit
    ist_aktiviert = models.BooleanField(
        default=True,
        help_text="Soll diese Kante bekanntet werden? (Checkbox für User)"
    )
    manuell_ueberschrieben = models.BooleanField(
        default=False,
        help_text="Hat der User die Länge manuell geändert?"
    )
    manuelle_laenge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manuell überschriebene Länge (falls abweichend)"
    )

    # Komponenten-Daten (zur Dokumentation)
    komponenten_daten = models.JSONField(
        default=dict,
        help_text="Ursprungs-Daten aus Extraktion (z.B. {'typ': 'Tür', 'höhe': 2.0, 'breite': 1.0})"
    )

    # Metadaten
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Geometrie-Berechnung"
        verbose_name_plural = "Geometrie-Berechnungen"
        ordering = ['extraction_result', 'kanten_typ']
        indexes = [
            models.Index(fields=['extraction_result', 'ist_aktiviert']),
        ]

    def __str__(self):
        laenge = self.manuelle_laenge if self.manuell_ueberschrieben else self.berechnete_laenge
        status = "✓" if self.ist_aktiviert else "✗"
        return f"{status} {self.kanten_typ}: {laenge} lfm"

    def get_final_laenge(self):
        """Return manual length if overridden, otherwise calculated length."""
        if self.manuell_ueberschrieben and self.manuelle_laenge:
            return self.manuelle_laenge
        return self.berechnete_laenge


class CompanyProfile(models.Model):
    """
    Company profile for multi-tenant support.

    Note: This is a placeholder. You may already have a Company model.
    If so, replace references to this model with your existing one.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    gewerk = models.CharField(
        max_length=20,
        choices=StandardBauteil.GEWERK_CHOICES
    )

    # User-Zuordnung
    users = models.ManyToManyField(User, related_name='company_profiles')

    erstellt_am = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Firmen"

    def __str__(self):
        return self.name
