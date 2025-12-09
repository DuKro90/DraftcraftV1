"""
Django Admin for Standardbauteile - Phase 4B

Features:
- Bulk-edit capabilities (Excel/Sheets compatible)
- Version control for catalogs
- Inline editing for rules and catalog positions
- Visual preview of geometry calculations
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, Q
from django.urls import reverse
from django.http import HttpResponse
import csv
import json
from decimal import Decimal

from .models_bauteile import (
    StandardBauteil,
    BauteilRegel,
    BauteilKatalog,
    BauteilKatalogPosition,
    GeometrieBerechnung,
    CompanyProfile,
)


# =============================================================================
# INLINE ADMINS
# =============================================================================

class BauteilRegelInline(admin.TabularInline):
    """Inline admin for BauteilRegel."""
    model = BauteilRegel
    extra = 1
    fields = ('name', 'regel_definition', 'prioritaet', 'ist_aktiv')
    classes = ('collapse',)


class BauteilKatalogPositionInline(admin.TabularInline):
    """Inline admin for catalog positions."""
    model = BauteilKatalogPosition
    extra = 0
    fields = ('bauteil', 'katalog_einzelpreis', 'position', 'ist_aktiv_in_katalog')
    autocomplete_fields = ['bauteil']
    ordering = ['position']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('bauteil')


# =============================================================================
# STANDARD BAUTEIL ADMIN
# =============================================================================

@admin.register(StandardBauteil)
class StandardBauteilAdmin(admin.ModelAdmin):
    """
    Admin for StandardBauteil with bulk-edit capabilities.

    Features:
    - Bulk actions: Activate/Deactivate, Export to CSV
    - Search by article number, name, supplier
    - Filter by category, trade, status
    """

    list_display = (
        'artikel_nr',
        'name_kurz',
        'kategorie_badge',
        'gewerke_display',
        'preis_display',
        'lieferant',
        'status_badge',
        'verwendung_count'
    )
    list_filter = (
        'kategorie',
        'gewerke',
        'ist_aktiv',
        'verfuegbar_ab',
    )
    search_fields = (
        'artikel_nr',
        'name',
        'beschreibung',
        'lieferant',
        'lieferanten_artikel_nr'
    )
    readonly_fields = ('id', 'erstellt_am', 'aktualisiert_am')
    autocomplete_fields = ['erstellt_von']
    inlines = [BauteilRegelInline]

    fieldsets = (
        ('Identifikation', {
            'fields': ('id', 'artikel_nr', 'name', 'beschreibung')
        }),
        ('Kategorisierung', {
            'fields': ('kategorie', 'gewerke')
        }),
        ('Preisangaben', {
            'fields': ('einheit', 'einzelpreis')
        }),
        ('Lieferanten-Info', {
            'fields': ('lieferant', 'lieferanten_artikel_nr'),
            'classes': ('collapse',)
        }),
        ('Verfügbarkeit', {
            'fields': ('ist_aktiv', 'verfuegbar_ab', 'verfuegbar_bis')
        }),
        ('Zusätzliche Daten', {
            'fields': ('zusatz_daten',),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': ('erstellt_am', 'aktualisiert_am', 'erstellt_von'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'activate_bauteile',
        'deactivate_bauteile',
        'export_to_csv',
        'duplicate_for_new_gewerk'
    ]

    def name_kurz(self, obj):
        """Truncated name for list display."""
        if len(obj.name) > 50:
            return obj.name[:47] + '...'
        return obj.name
    name_kurz.short_description = 'Name'

    def kategorie_badge(self, obj):
        """Colored badge for category."""
        colors = {
            'beschlag': '#3498db',
            'verbinder': '#2ecc71',
            'kante': '#e74c3c',
            'befestigung': '#f39c12',
            'oberflaeche': '#9b59b6',
            'sonstiges': '#95a5a6',
        }
        color = colors.get(obj.kategorie, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_kategorie_display()
        )
    kategorie_badge.short_description = 'Kategorie'

    def gewerke_display(self, obj):
        """Display trades as comma-separated list."""
        if not obj.gewerke:
            return '-'
        # Get display names
        gewerk_dict = dict(StandardBauteil.GEWERK_CHOICES)
        display_names = [gewerk_dict.get(g, g) for g in obj.gewerke]
        return ', '.join(display_names[:2]) + ('...' if len(display_names) > 2 else '')
    gewerke_display.short_description = 'Gewerke'

    def preis_display(self, obj):
        """Format price with unit."""
        return format_html(
            '<strong>{:.2f} €</strong> / {}',
            obj.einzelpreis,
            obj.get_einheit_display()
        )
    preis_display.short_description = 'Preis'

    def status_badge(self, obj):
        """Active/Inactive badge."""
        if obj.ist_aktiv:
            return format_html(
                '<span style="color: green;">● Aktiv</span>'
            )
        return format_html(
            '<span style="color: red;">● Inaktiv</span>'
        )
    status_badge.short_description = 'Status'

    def verwendung_count(self, obj):
        """Count how many catalogs use this component."""
        count = obj.kataloge.count()
        return f"{count} Katalog{'e' if count != 1 else ''}"
    verwendung_count.short_description = 'Verwendung'

    # =========================================================================
    # BULK ACTIONS
    # =========================================================================

    @admin.action(description='Aktivieren (Bulk)')
    def activate_bauteile(self, request, queryset):
        """Bulk activate components."""
        updated = queryset.update(ist_aktiv=True)
        self.message_user(
            request,
            f'{updated} Bauteil(e) wurden aktiviert.'
        )

    @admin.action(description='Deaktivieren (Bulk)')
    def deactivate_bauteile(self, request, queryset):
        """Bulk deactivate components."""
        updated = queryset.update(ist_aktiv=False)
        self.message_user(
            request,
            f'{updated} Bauteil(e) wurden deaktiviert.'
        )

    @admin.action(description='Export als CSV (Excel-kompatibel)')
    def export_to_csv(self, request, queryset):
        """
        Export components to CSV (Excel/Sheets compatible).

        CSV format with UTF-8 BOM for Excel compatibility.
        """
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="bauteile_export.csv"'

        writer = csv.writer(response, delimiter=';')  # Excel prefers semicolon for German locale

        # Header
        writer.writerow([
            'Artikel-Nr',
            'Name',
            'Beschreibung',
            'Kategorie',
            'Gewerke',
            'Einheit',
            'Einzelpreis (EUR)',
            'Lieferant',
            'Lieferanten Artikel-Nr',
            'Aktiv',
            'Verfügbar ab',
            'Verfügbar bis'
        ])

        # Data rows
        for bauteil in queryset:
            writer.writerow([
                bauteil.artikel_nr,
                bauteil.name,
                bauteil.beschreibung,
                bauteil.get_kategorie_display(),
                ', '.join(bauteil.gewerke) if bauteil.gewerke else '',
                bauteil.get_einheit_display(),
                str(bauteil.einzelpreis).replace('.', ','),  # German decimal separator
                bauteil.lieferant,
                bauteil.lieferanten_artikel_nr,
                'Ja' if bauteil.ist_aktiv else 'Nein',
                bauteil.verfuegbar_ab.strftime('%d.%m.%Y') if bauteil.verfuegbar_ab else '',
                bauteil.verfuegbar_bis.strftime('%d.%m.%Y') if bauteil.verfuegbar_bis else ''
            ])

        return response

    @admin.action(description='Duplizieren für anderes Gewerk')
    def duplicate_for_new_gewerk(self, request, queryset):
        """Duplicate component for use in another trade."""
        # This would open a form to select target trade
        # For now, just show message
        self.message_user(
            request,
            f'Funktion "Duplizieren" wird in nächster Version implementiert.',
            level='warning'
        )


# =============================================================================
# BAUTEIL REGEL ADMIN
# =============================================================================

@admin.register(BauteilRegel)
class BauteilRegelAdmin(admin.ModelAdmin):
    """Admin for BauteilRegel with JSON editor."""

    list_display = (
        'name',
        'bauteil_link',
        'operation_badge',
        'prioritaet',
        'status_badge'
    )
    list_filter = ('ist_aktiv', 'bauteil__kategorie')
    search_fields = ('name', 'bauteil__name', 'bauteil__artikel_nr')
    readonly_fields = ('id', 'erstellt_am', 'aktualisiert_am', 'regel_preview')
    autocomplete_fields = ['bauteil']

    fieldsets = (
        ('Zuordnung', {
            'fields': ('id', 'bauteil', 'name')
        }),
        ('Regel-Definition', {
            'fields': ('regel_definition', 'regel_preview'),
            'description': '''
                <strong>Level 1 DSL Beispiele:</strong><br>
                <code>{"operation": "MULTIPLY", "faktor": 3, "komponente": "Tür", "attribut": "anzahl"}</code><br>
                <code>{"operation": "FIXED", "wert": 10}</code><br>
                <code>{"operation": "ADD", "terme": [...]}</code>
            '''
        }),
        ('Priorität & Status', {
            'fields': ('prioritaet', 'ist_aktiv')
        }),
        ('Metadaten', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def bauteil_link(self, obj):
        """Link to associated component."""
        url = reverse('admin:documents_standardbauteil_change', args=[obj.bauteil.id])
        return format_html('<a href="{}">{}</a>', url, obj.bauteil.name)
    bauteil_link.short_description = 'Bauteil'

    def operation_badge(self, obj):
        """Display operation type."""
        operation = obj.regel_definition.get('operation', 'UNKNOWN')
        colors = {
            'MULTIPLY': '#3498db',
            'ADD': '#2ecc71',
            'SUBTRACT': '#e74c3c',
            'FIXED': '#f39c12',
        }
        color = colors.get(operation, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px; font-family: monospace;">{}</span>',
            color,
            operation
        )
    operation_badge.short_description = 'Operation'

    def status_badge(self, obj):
        """Active/Inactive badge."""
        if obj.ist_aktiv:
            return format_html('<span style="color: green;">● Aktiv</span>')
        return format_html('<span style="color: red;">● Inaktiv</span>')
    status_badge.short_description = 'Status'

    def regel_preview(self, obj):
        """Human-readable preview of rule."""
        try:
            operation = obj.regel_definition.get('operation')
            if operation == 'MULTIPLY':
                faktor = obj.regel_definition.get('faktor')
                komponente = obj.regel_definition.get('komponente')
                attribut = obj.regel_definition.get('attribut')
                return format_html(
                    '<code>{} × {}.{}</code>',
                    faktor, komponente, attribut
                )
            elif operation == 'FIXED':
                wert = obj.regel_definition.get('wert')
                return format_html('<code>Fest: {}</code>', wert)
            elif operation == 'ADD':
                terme_count = len(obj.regel_definition.get('terme', []))
                return format_html('<code>Summe von {} Termen</code>', terme_count)
            else:
                return format_html('<code>{}</code>', json.dumps(obj.regel_definition))
        except Exception as e:
            return format_html('<span style="color: red;">Fehler: {}</span>', str(e))
    regel_preview.short_description = 'Regel-Vorschau'


# =============================================================================
# BAUTEIL KATALOG ADMIN
# =============================================================================

@admin.register(BauteilKatalog)
class BauteilKatalogAdmin(admin.ModelAdmin):
    """
    Admin for BauteilKatalog with version control.

    Features:
    - Version history navigation
    - Bulk import/export
    - Catalog cloning for new version
    """

    list_display = (
        'name',
        'version_badge',
        'firma_display',
        'gewerk_badge',
        'gueltig_ab',
        'gueltig_bis',
        'bauteile_count',
        'status_badges'
    )
    list_filter = (
        'gewerk',
        'ist_aktiv',
        'ist_standard',
        'gueltig_ab'
    )
    search_fields = ('name', 'version', 'beschreibung', 'firma__name')
    readonly_fields = ('id', 'erstellt_am', 'aktualisiert_am', 'version_history')
    autocomplete_fields = ['firma', 'erstellt_von', 'vorgaenger_version']
    inlines = [BauteilKatalogPositionInline]
    date_hierarchy = 'gueltig_ab'

    fieldsets = (
        ('Identifikation', {
            'fields': ('id', 'name', 'version', 'beschreibung')
        }),
        ('Zuordnung', {
            'fields': ('firma', 'gewerk')
        }),
        ('Gültigkeitszeitraum', {
            'fields': ('gueltig_ab', 'gueltig_bis')
        }),
        ('Status', {
            'fields': ('ist_aktiv', 'ist_standard')
        }),
        ('Versionierung', {
            'fields': ('vorgaenger_version', 'version_history'),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': ('erstellt_am', 'aktualisiert_am', 'erstellt_von'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'clone_catalog_new_version',
        'set_as_standard',
        'export_catalog_csv'
    ]

    def version_badge(self, obj):
        """Version badge with predecessor link."""
        badge = format_html(
            '<span style="background-color: #3498db; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-weight: bold;">v{}</span>',
            obj.version
        )
        if obj.vorgaenger_version:
            url = reverse('admin:documents_bauteilkatalog_change', args=[obj.vorgaenger_version.id])
            badge += format_html(' <a href="{}">← Vorgänger</a>', url)
        return badge
    version_badge.short_description = 'Version'

    def firma_display(self, obj):
        """Display company or 'Global'."""
        if obj.firma:
            return obj.firma.name
        return format_html('<em>Global</em>')
    firma_display.short_description = 'Firma'

    def gewerk_badge(self, obj):
        """Colored badge for trade."""
        colors = {
            'tischler': '#8B4513',
            'zimmerer': '#228B22',
            'polsterer': '#9370DB',
            'allgemein': '#708090',
        }
        color = colors.get(obj.gewerk, '#708090')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_gewerk_display()
        )
    gewerk_badge.short_description = 'Gewerk'

    def bauteile_count(self, obj):
        """Count of components in catalog."""
        count = obj.bauteile.count()
        return f"{count} Bauteile"
    bauteile_count.short_description = 'Umfang'

    def status_badges(self, obj):
        """Combined status badges."""
        badges = []
        if obj.ist_aktiv:
            badges.append('<span style="color: green;">● Aktiv</span>')
        else:
            badges.append('<span style="color: red;">● Inaktiv</span>')

        if obj.ist_standard:
            badges.append('<span style="color: blue;">★ Standard</span>')

        return format_html(' '.join(badges))
    status_badges.short_description = 'Status'

    def version_history(self, obj):
        """Display version history chain."""
        history = []
        current = obj
        while current.vorgaenger_version:
            current = current.vorgaenger_version
            url = reverse('admin:documents_bauteilkatalog_change', args=[current.id])
            history.append(
                f'<a href="{url}">v{current.version}</a> ({current.gueltig_ab.strftime("%d.%m.%Y")})'
            )

        if not history:
            return format_html('<em>Keine Vorgänger-Versionen</em>')

        return format_html('<br>'.join(['← ' + h for h in history]))
    version_history.short_description = 'Versions-Historie'

    @admin.action(description='Neue Version erstellen (Klon)')
    def clone_catalog_new_version(self, request, queryset):
        """Clone catalog as new version."""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Bitte genau einen Katalog auswählen.',
                level='error'
            )
            return

        # Implementation would open a form for new version details
        self.message_user(
            request,
            'Funktion "Neue Version" wird in nächster Version implementiert.',
            level='warning'
        )

    @admin.action(description='Als Standard-Katalog setzen')
    def set_as_standard(self, request, queryset):
        """Set catalog as standard."""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Bitte genau einen Katalog auswählen.',
                level='error'
            )
            return

        catalog = queryset.first()

        # Deactivate other standard catalogs for same firma + gewerk
        BauteilKatalog.objects.filter(
            firma=catalog.firma,
            gewerk=catalog.gewerk,
            ist_standard=True
        ).update(ist_standard=False)

        catalog.ist_standard = True
        catalog.save()

        self.message_user(
            request,
            f'Katalog "{catalog.name}" wurde als Standard gesetzt.'
        )

    @admin.action(description='Export Katalog als CSV')
    def export_catalog_csv(self, request, queryset):
        """Export catalog with prices to CSV."""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Bitte genau einen Katalog auswählen.',
                level='error'
            )
            return

        catalog = queryset.first()

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="katalog_{catalog.version}.csv"'

        writer = csv.writer(response, delimiter=';')

        # Header
        writer.writerow([
            'Artikel-Nr',
            'Name',
            'Kategorie',
            'Standard-Preis',
            'Katalog-Preis',
            'Einheit',
            'Position',
            'Aktiv'
        ])

        # Catalog positions
        for pos in catalog.bauteilkatalogposition_set.select_related('bauteil').order_by('position'):
            writer.writerow([
                pos.bauteil.artikel_nr,
                pos.bauteil.name,
                pos.bauteil.get_kategorie_display(),
                str(pos.bauteil.einzelpreis).replace('.', ','),
                str(pos.get_preis()).replace('.', ','),
                pos.bauteil.get_einheit_display(),
                pos.position,
                'Ja' if pos.ist_aktiv_in_katalog else 'Nein'
            ])

        return response


# =============================================================================
# GEOMETRIE BERECHNUNG ADMIN
# =============================================================================

@admin.register(GeometrieBerechnung)
class GeometrieBerechnungAdmin(admin.ModelAdmin):
    """Admin for GeometrieBerechnung with visual preview."""

    list_display = (
        'extraction_link',
        'bauteil_link',
        'kanten_typ_badge',
        'länge_display',
        'checkbox_status',
        'erstellt_am'
    )
    list_filter = (
        'kanten_typ',
        'ist_aktiviert',
        'manuell_ueberschrieben',
        'erstellt_am'
    )
    search_fields = (
        'extraction_result__document__original_filename',
        'bauteil__name'
    )
    readonly_fields = ('id', 'erstellt_am', 'aktualisiert_am', 'komponenten_preview')
    autocomplete_fields = ['extraction_result', 'bauteil']

    fieldsets = (
        ('Zuordnung', {
            'fields': ('id', 'extraction_result', 'bauteil')
        }),
        ('Kanten-Spezifikation', {
            'fields': ('kanten_typ', 'formel', 'berechnete_laenge')
        }),
        ('User-Editierung', {
            'fields': ('ist_aktiviert', 'manuell_ueberschrieben', 'manuelle_laenge'),
            'description': 'Checkbox für User-Freigabe und manuelle Überschreibung'
        }),
        ('Komponenten-Daten', {
            'fields': ('komponenten_daten', 'komponenten_preview'),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def extraction_link(self, obj):
        """Link to extraction result."""
        url = reverse('admin:documents_extractionresult_change', args=[obj.extraction_result.id])
        filename = obj.extraction_result.document.original_filename
        return format_html('<a href="{}">{}</a>', url, filename[:30])
    extraction_link.short_description = 'Dokument'

    def bauteil_link(self, obj):
        """Link to component."""
        url = reverse('admin:documents_standardbauteil_change', args=[obj.bauteil.id])
        return format_html('<a href="{}">{}</a>', url, obj.bauteil.name)
    bauteil_link.short_description = 'Bauteil'

    def kanten_typ_badge(self, obj):
        """Colored badge for edge type."""
        colors = {
            'korpus_außen': '#2ecc71',
            'korpus_innen': '#95a5a6',
            'tür_außen': '#3498db',
            'einlegeboden_vorder': '#e74c3c',
            'einlegeboden_seite': '#f39c12',
            'schublade_außen': '#9b59b6',
            'rueckseite': '#7f8c8d',
        }
        color = colors.get(obj.kanten_typ, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_kanten_typ_display()
        )
    kanten_typ_badge.short_description = 'Kanten-Typ'

    def länge_display(self, obj):
        """Display final length with unit."""
        länge = obj.get_final_laenge()
        if obj.manuell_ueberschrieben:
            return format_html(
                '<strong style="color: #e74c3c;">{:.2f} lfm</strong> (manuell)',
                länge
            )
        return format_html('<strong>{:.2f} lfm</strong>', länge)
    länge_display.short_description = 'Länge'

    def checkbox_status(self, obj):
        """Checkbox status display."""
        if obj.ist_aktiviert:
            return format_html('☑ <span style="color: green;">Aktiviert</span>')
        return format_html('☐ <span style="color: #95a5a6;">Deaktiviert</span>')
    checkbox_status.short_description = 'Status'

    def komponenten_preview(self, obj):
        """Pretty-print component data."""
        try:
            data_str = json.dumps(obj.komponenten_daten, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', data_str)
        except:
            return str(obj.komponenten_daten)
    komponenten_preview.short_description = 'Komponenten-Daten (JSON)'


# =============================================================================
# COMPANY PROFILE ADMIN
# =============================================================================

@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    """Admin for CompanyProfile."""

    list_display = ('name', 'gewerk_badge', 'users_count', 'erstellt_am')
    list_filter = ('gewerk', 'erstellt_am')
    search_fields = ('name',)
    filter_horizontal = ('users',)
    readonly_fields = ('id', 'erstellt_am')

    fieldsets = (
        ('Firma', {
            'fields': ('id', 'name', 'gewerk')
        }),
        ('Benutzer', {
            'fields': ('users',)
        }),
        ('Metadaten', {
            'fields': ('erstellt_am',),
            'classes': ('collapse',)
        }),
    )

    def gewerk_badge(self, obj):
        """Colored badge for trade."""
        colors = {
            'tischler': '#8B4513',
            'zimmerer': '#228B22',
            'polsterer': '#9370DB',
            'allgemein': '#708090',
        }
        color = colors.get(obj.gewerk, '#708090')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_gewerk_display()
        )
    gewerk_badge.short_description = 'Gewerk'

    def users_count(self, obj):
        """Count of users."""
        count = obj.users.count()
        return f"{count} Benutzer"
    users_count.short_description = 'Anzahl Benutzer'
