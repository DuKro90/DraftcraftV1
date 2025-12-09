"""
Django Admin for Betriebspauschalen - Phase 4C

Admin interface for managing operational surcharges (Betriebspauschalen).

Author: Claude Code
Created: December 2025
"""

from django.contrib import admin
from django.utils.html import format_html
from .models_pauschalen import BetriebspauschaleRegel, PauschaleAnwendung


@admin.register(BetriebspauschaleRegel)
class BetriebspauschaleRegelAdmin(admin.ModelAdmin):
    """Admin interface for BetriebspauschaleRegel."""

    list_display = (
        "name",
        "pauschale_typ",
        "berechnungsart",
        "betrag_display",
        "ist_aktiv",
        "prioritaet",
    )
    list_filter = ("pauschale_typ", "berechnungsart", "ist_aktiv")
    search_fields = ("name", "beschreibung")
    readonly_fields = ("id", "erstellt_am", "aktualisiert_am")

    fieldsets = (
        (
            "Identifikation",
            {
                "fields": (
                    "id",
                    "user",
                    "name",
                    "pauschale_typ",
                    "beschreibung",
                )
            },
        ),
        (
            "Berechnung",
            {
                "fields": (
                    "berechnungsart",
                    "betrag",
                    "einheit",
                    "prozentsatz",
                    "konditional_regel",
                ),
                "description": (
                    "Wählen Sie die Berechnungsart und füllen Sie die entsprechenden Felder aus:<br>"
                    "- <b>fest</b>: Nur 'betrag' wird verwendet<br>"
                    "- <b>pro_einheit</b>: 'betrag' × Menge (aus Context)<br>"
                    "- <b>prozent</b>: 'prozentsatz' % vom Auftragswert<br>"
                    "- <b>konditional</b>: JSON-Regel in 'konditional_regel'"
                ),
            },
        ),
        (
            "Anwendungs-Bedingungen",
            {
                "fields": ("min_auftragswert", "max_auftragswert"),
                "description": (
                    "Definieren Sie, für welche Auftragswerte diese Pauschale gilt. "
                    "Leer = keine Einschränkung."
                ),
            },
        ),
        (
            "Status & Zeitraum",
            {
                "fields": (
                    "ist_aktiv",
                    "prioritaet",
                    "gueltig_ab",
                    "gueltig_bis",
                    "erstellt_am",
                    "aktualisiert_am",
                )
            },
        ),
    )

    def betrag_display(self, obj):
        """Display formatted amount based on calculation type."""
        if obj.berechnungsart == "fest":
            return f"{obj.betrag} EUR"
        elif obj.berechnungsart == "pro_einheit":
            return f"{obj.betrag} EUR/{obj.einheit or 'Einheit'}"
        elif obj.berechnungsart == "prozent":
            return f"{obj.prozentsatz}%"
        elif obj.berechnungsart == "konditional":
            return "Konditional"
        return "-"

    betrag_display.short_description = "Betrag"

    def save_model(self, request, obj, form, change):
        """Automatically set user if creating new rule."""
        if not change:  # Creating new object
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(PauschaleAnwendung)
class PauschaleAnwendungAdmin(admin.ModelAdmin):
    """Admin interface for PauschaleAnwendung (applied surcharges)."""

    list_display = (
        "pauschale",
        "extraction_result",
        "berechneter_betrag_display",
        "manuell_ueberschrieben",
        "erstellt_am",
    )
    list_filter = ("manuell_ueberschrieben", "pauschale__pauschale_typ")
    search_fields = ("pauschale__name", "extraction_result__id")
    readonly_fields = ("id", "erstellt_am", "aktualisiert_am")

    fieldsets = (
        (
            "Anwendung",
            {
                "fields": (
                    "id",
                    "extraction_result",
                    "pauschale",
                    "erstellt_am",
                    "aktualisiert_am",
                )
            },
        ),
        (
            "Berechnung",
            {
                "fields": (
                    "berechnungsgrundlage",
                    "berechneter_betrag",
                    "manueller_betrag",
                    "manuell_ueberschrieben",
                )
            },
        ),
        ("Bemerkungen", {"fields": ("bemerkung",)}),
    )

    def berechneter_betrag_display(self, obj):
        """Display calculated or manual amount with formatting."""
        if obj.manuell_ueberschrieben:
            return format_html(
                '<span style="color: orange;">{} EUR (manuell)</span>',
                obj.manueller_betrag or obj.berechneter_betrag,
            )
        else:
            return f"{obj.berechneter_betrag} EUR"

    berechneter_betrag_display.short_description = "Betrag"

    def has_add_permission(self, request):
        """Disable manual creation - applications are created automatically."""
        return False
