"""
Automatic translation helper script for DraftCraft i18n.

This script helps automate the translation process by:
1. Generating German and English .po files with pre-filled translations
2. Creating a base translation dictionary

Usage:
    python scripts/auto_translate.py
"""

import os
import sys

# Translation dictionary: English -> German
TRANSLATIONS = {
    # Common terms
    "Status": "Status",
    "Active": "Aktiv",
    "Inactive": "Inaktiv",
    "Created": "Erstellt",
    "Updated": "Aktualisiert",
    "Published": "Veröffentlicht",
    "Unpublished": "Unveröffentlicht",
    "Save": "Speichern",
    "Delete": "Löschen",
    "Cancel": "Abbrechen",
    "Edit": "Bearbeiten",
    "View": "Anzeigen",
    "Add": "Hinzufügen",
    "Search": "Suchen",
    "Filter": "Filtern",
    "Export": "Exportieren",
    "Import": "Importieren",

    # Wiki System
    "Wiki Category": "Wiki-Kategorie",
    "Wiki Categories": "Wiki-Kategorien",
    "Wiki Article": "Wiki-Artikel",
    "Wiki Articles": "Wiki-Artikel",
    "Search Log": "Suchprotokoll",
    "Feedback": "Rückmeldung",
    "How-To Wiki": "Anleitungs-Wiki",
    "Comprehensive guides and documentation": "Umfassende Anleitungen und Dokumentation",
    "Getting Started": "Erste Schritte",
    "Data Import & Export": "Datenimport & -export",
    "Configuration": "Konfiguration",
    "Troubleshooting": "Fehlerbehebung",
    "Advanced Features": "Erweiterte Funktionen",
    "Beginner": "Anfänger",
    "Intermediate": "Fortgeschritten",
    "Advanced": "Experte",
    "Featured": "Empfohlen",
    "Popular": "Beliebt",
    "Recent": "Aktuell",
    "Related Articles": "Verwandte Artikel",
    "Was this article helpful?": "War dieser Artikel hilfreich?",
    "Yes, helpful": "Ja, hilfreich",
    "Not helpful": "Nicht hilfreich",
    "views": "Aufrufe",
    "Updated": "Aktualisiert",

    # Bulk Upload
    "Bulk Upload": "Massen-Upload",
    "Download template": "Vorlage herunterladen",
    "Template herunterladen": "Vorlage herunterladen",
    "Excel/CSV File": "Excel/CSV-Datei",
    "Preview mode": "Vorschau-Modus",
    "Update existing entries": "Bestehende Einträge aktualisieren",
    "Upload file": "Datei hochladen",
    "Dry run": "Testlauf",

    # Betriebskennzahlen
    "Wood Type": "Holzart",
    "Wood Types": "Holzarten",
    "Surface Finish": "Oberflächenbearbeitung",
    "Surface Finishes": "Oberflächenbearbeitungen",
    "Complexity Factor": "Komplexitätsfaktor",
    "Complexity Factors": "Komplexitätsfaktoren",
    "Material": "Material",
    "Materials": "Materialien",
    "Seasonal Campaign": "Saisonale Kampagne",
    "Seasonal Campaigns": "Saisonale Kampagnen",
    "Price factor": "Preisfaktor",
    "Time factor": "Zeitfaktor",
    "Difficulty": "Schwierigkeitsgrad",
    "Easy": "Einfach",
    "Medium": "Mittel",
    "Hard": "Schwer",
    "Master": "Meister",

    # Admin Interface
    "Dashboard": "Übersicht",
    "Documents": "Dokumente",
    "Extraction": "Extraktion",
    "Proposals": "Angebote",
    "Analytics": "Analyse",
    "Settings": "Einstellungen",
    "Help": "Hilfe",
    "Logout": "Abmelden",
    "Welcome": "Willkommen",

    # Document Management
    "Document": "Dokument",
    "File": "Datei",
    "Upload": "Hochladen",
    "Download": "Herunterladen",
    "Process": "Verarbeiten",
    "Processing": "Verarbeitung",
    "Completed": "Abgeschlossen",
    "Error": "Fehler",
    "Pending": "Ausstehend",

    # Forms & Validation
    "Required field": "Pflichtfeld",
    "Invalid value": "Ungültiger Wert",
    "This field is required": "Dieses Feld ist erforderlich",
    "Please enter a valid": "Bitte geben Sie einen gültigen",
    "Select": "Auswählen",
    "Choose": "Wählen",
    "Browse": "Durchsuchen",

    # Time & Dates
    "Today": "Heute",
    "Yesterday": "Gestern",
    "Last week": "Letzte Woche",
    "Last month": "Letzter Monat",
    "Date": "Datum",
    "Time": "Zeit",
    "Created at": "Erstellt am",
    "Updated at": "Aktualisiert am",
}

def create_po_header(language_code, language_name):
    """Create .po file header."""
    return f'''# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: DraftCraft 1.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-12-03 12:00+0100\\n"
"PO-Revision-Date: 2025-12-03 12:00+0100\\n"
"Last-Translator: Auto-Generated\\n"
"Language-Team: {language_name}\\n"
"Language: {language_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

'''

def create_po_entry(msgid, msgstr, comment=None):
    """Create a single .po entry."""
    entry = ""
    if comment:
        entry += f"# {comment}\n"
    entry += f'msgid "{msgid}"\n'
    entry += f'msgstr "{msgstr}"\n\n'
    return entry

def generate_german_po():
    """Generate German translations."""
    content = create_po_header("de", "German")

    for english, german in sorted(TRANSLATIONS.items()):
        content += create_po_entry(english, german)

    return content

def generate_english_po():
    """Generate English translations (msgid == msgstr)."""
    content = create_po_header("en", "English")

    for english in sorted(TRANSLATIONS.keys()):
        content += create_po_entry(english, english)

    return content

def main():
    """Main execution."""
    print("=" * 60)
    print("DraftCraft Auto-Translation Generator")
    print("=" * 60)

    # Create locale directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_dir = os.path.join(base_dir, 'locale')

    os.makedirs(os.path.join(locale_dir, 'de', 'LC_MESSAGES'), exist_ok=True)
    os.makedirs(os.path.join(locale_dir, 'en', 'LC_MESSAGES'), exist_ok=True)

    # Generate German .po
    de_po_path = os.path.join(locale_dir, 'de', 'LC_MESSAGES', 'django.po')
    print(f"\nGenerating: {de_po_path}")
    with open(de_po_path, 'w', encoding='utf-8') as f:
        f.write(generate_german_po())
    print(f"  Written {len(TRANSLATIONS)} German translations")

    # Generate English .po
    en_po_path = os.path.join(locale_dir, 'en', 'LC_MESSAGES', 'django.po')
    print(f"\nGenerating: {en_po_path}")
    with open(en_po_path, 'w', encoding='utf-8') as f:
        f.write(generate_english_po())
    print(f"  Written {len(TRANSLATIONS)} English translations")

    print("\n" + "=" * 60)
    print("SUCCESS! Translation files created.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python manage.py compilemessages")
    print("2. Restart Django server")
    print("3. Test language switching in admin")
    print("\n")

if __name__ == '__main__':
    main()
