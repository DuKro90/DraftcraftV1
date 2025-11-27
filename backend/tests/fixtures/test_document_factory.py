"""Factory for generating synthetic test documents for batch processing."""
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
import random
from io import BytesIO

from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from documents.models import Document


class SyntheticDocumentFactory:
    """Generate realistic synthetic German construction documents for testing."""

    # German construction vocabulary
    TRADE_TYPES = [
        'Tischler', 'Schreiner', 'Polsterer', 'Schreiner/Möbelbau',
        'Kunsthandwerk Möbel', 'Maßmöbelbau', 'Innenausstattung'
    ]

    MATERIALS = {
        'Holzarten': [
            'Eiche', 'Buche', 'Kiefer', 'Fichte', 'Ahorn',
            'Erle', 'Esche', 'Nussbaum', 'Teak', 'Mahagoni'
        ],
        'Oberflächen': [
            'lackiert', 'geölt', 'gewachst', 'natur', 'gebeizt',
            'hochglanz', 'matt', 'strukturiert', 'geflammte Eiche'
        ],
        'Polstermaterial': [
            'Stoff', 'Leder', 'Kunstleder', 'Mikrofaser', 'Wolle',
            'Baumwollmischung', 'Leinen', 'Seide'
        ]
    }

    PROJECT_TYPES = [
        'Stuhl', 'Tisch', 'Schrank', 'Bett', 'Bücherschrank',
        'Sideboard', 'Couchtisch', 'Esstisch', 'Wohnzimmereinrichtung',
        'Schlafzimmereinrichtung', 'Küchenmöbel', 'Maßanfertigung'
    ]

    GERMAN_NUMBERS = [
        '2.450,50', '1.234,75', '950,00', '3.500,99', '750,25',
        '5.000,00', '1.875,50', '2.999,99', '1.500,00', '4.200,75'
    ]

    INVOICE_NUMBERS = [
        'RE-2024-001', 'RE-2024-0234', 'RE-24-10234', 'RG-2024-234',
        'RECHNUNG-2024-100', 'RE/2024/001', 'A-2024-234'
    ]

    DATES = [
        '15.11.2024', '20.10.2024', '10.09.2024', '05.11.2024',
        '25.10.2024', '18.09.2024', '28.08.2024', '12.07.2024'
    ]

    @classmethod
    def create_text_document(
        cls,
        user: User,
        document_type: str = 'invoice',
        include_keywords: bool = True
    ) -> Document:
        """Create a synthetic text document.

        Args:
            user: User who owns the document
            document_type: 'invoice', 'estimate', 'offer', 'proposal'
            include_keywords: Include construction terminology

        Returns:
            Created Document instance
        """
        # Generate content
        content = cls._generate_document_content(document_type, include_keywords)

        # Create file content
        file_content = ContentFile(content.encode('utf-8'))
        filename = f"synthetic_{document_type}_{random.randint(1000, 9999)}.txt"

        # Create document
        doc = Document.objects.create(
            user=user,
            file=file_content,
            original_filename=filename,
            file_size_bytes=len(content.encode('utf-8')),
            status='uploaded',
            document_type='txt'
        )

        return doc

    @classmethod
    def create_batch_documents(
        cls,
        user: User,
        count: int = 10,
        document_type: str = 'invoice'
    ) -> List[Document]:
        """Create multiple synthetic documents for batch testing.

        Args:
            user: User who owns documents
            count: Number of documents to create
            document_type: Type of documents

        Returns:
            List of created Document instances
        """
        documents = []
        for i in range(count):
            doc = cls.create_text_document(
                user=user,
                document_type=document_type,
                include_keywords=True
            )
            documents.append(doc)

        return documents

    @classmethod
    def _generate_document_content(
        cls,
        document_type: str,
        include_keywords: bool = True
    ) -> str:
        """Generate synthetic document content.

        Args:
            document_type: Type of document
            include_keywords: Include construction terminology

        Returns:
            Document text content
        """
        if document_type == 'invoice':
            return cls._generate_invoice(include_keywords)
        elif document_type == 'estimate':
            return cls._generate_estimate(include_keywords)
        elif document_type == 'offer':
            return cls._generate_offer(include_keywords)
        else:
            return cls._generate_invoice(include_keywords)

    @classmethod
    def _generate_invoice(cls, include_keywords: bool) -> str:
        """Generate synthetic invoice."""
        trade = random.choice(cls.TRADE_TYPES)
        material = random.choice(cls.MATERIALS['Holzarten'])
        surface = random.choice(cls.MATERIALS['Oberflächen'])
        project = random.choice(cls.PROJECT_TYPES)
        invoice_num = random.choice(cls.INVOICE_NUMBERS)
        amount = random.choice(cls.GERMAN_NUMBERS)
        date = random.choice(cls.DATES)

        content = f"""
RECHNUNG / INVOICE

Rechnungsnummer: {invoice_num}
Datum: {date}

Von:
{trade} GmbH
Musterstraße 123
12345 Musterstadt
USt-IdNr.: DE123456789

Beschreibung der Leistungen:
Anfertigung {project} - hochwertiges Möbelstück

Material: {material}
Oberfläche: {surface}
Verarbeitung: handwerkliche Fertigung

Leistungsbeschreibung:
- Materialkosten: {amount} €
- Arbeitszeit: 40 Stunden
- Verpackung und Versand: 150,00 €

Summe netto: {amount} €
USt (19%): 750,00 €
Gesamtsumme: 3.000,00 €

Zahlungsbedingungen:
- Fällig in 14 Tagen nach Rechnungsdatum
- Banküberweisung bevorzugt

"""
        if include_keywords:
            content += f"\nMateriaal-Hinweis: Dieses Möbelstück wurde aus hochwertigem {material} gefertigt und mit einer {surface} Oberfläche versehen.\n"

        return content.strip()

    @classmethod
    def _generate_estimate(cls, include_keywords: bool) -> str:
        """Generate synthetic estimate."""
        trade = random.choice(cls.TRADE_TYPES)
        project = random.choice(cls.PROJECT_TYPES)
        material = random.choice(cls.MATERIALS['Holzarten'])
        date = random.choice(cls.DATES)

        content = f"""
KOSTENVORANSCHLAG / ESTIMATE

Angebot für: {project}
Datum: {date}
Gültig bis: {date}

Auftraggeber:
Musterstraße 123
12345 Musterstadt

Leistungsbeschreibung:
Maßanfertigung {project} aus {material}

Positionen:
1. Material und Zuschnitt: 2.000,00 €
2. Verarbeitung und Montage: 1.500,00 €
3. Oberflächenbehandlung: 500,00 €
4. Lieferung: 200,00 €

Summe: 4.200,00 €

Lieferfrist: 8-10 Wochen ab Auftragserteilung
Zahlungsbedingungen: 50% Anzahlung, 50% bei Lieferung

"""

        if include_keywords:
            content += f"\nAnmerkungen: Dieses Projekt erfordert spezialisierte Handwerkstechnik und hochwertiges {material}-Material.\n"

        return content.strip()

    @classmethod
    def _generate_offer(cls, include_keywords: bool) -> str:
        """Generate synthetic offer."""
        trade = random.choice(cls.TRADE_TYPES)
        materials = ', '.join(random.sample(cls.MATERIALS['Holzarten'], 2))
        surfaces = ', '.join(random.sample(cls.MATERIALS['Oberflächen'], 2))
        date = random.choice(cls.DATES)

        content = f"""
ANGEBOT / OFFER

Für: {trade} Möbel
Datum: {date}

Unsere Leistungen:
- Maßgefertigte Möbel
- Hochwertige Materialien: {materials}
- Oberflächenfinish: {surfaces}
- Fachgerechte Montage und Lieferung

Ausstattungsdetails:
- Handwerkliche Qualität
- Zertifizierte Materialien
- Nachhaltige Produktion
- Individuelle Anpassung möglich

Kontakt:
Tel.: +49 (0) 123 456789
Email: info@example.de

Wir freuen uns auf Ihre Anfrage!

"""

        if include_keywords:
            content += f"\nSpezialitäten: {trade} mit Fokus auf Qualität und Nachhaltigkeit.\n"

        return content.strip()

    @classmethod
    def create_documents_with_variations(
        cls,
        user: User,
        count: int = 5,
        with_errors: bool = False
    ) -> List[Document]:
        """Create documents with variations for testing.

        Args:
            user: User who owns documents
            count: Number of documents
            with_errors: Include documents with OCR-like errors

        Returns:
            List of Document instances
        """
        documents = []

        for i in range(count):
            doc_type = random.choice(['invoice', 'estimate', 'offer'])

            doc = cls.create_text_document(
                user=user,
                document_type=doc_type,
                include_keywords=True
            )
            documents.append(doc)

        return documents

    @classmethod
    def get_sample_gaeb_data(cls) -> Dict[str, Any]:
        """Get sample GAEB (German construction standard) data.

        Returns:
            Dictionary with GAEB-formatted construction data
        """
        return {
            'ordnungszahl': '01.001',
            'kurztext': 'Schreinerei - Maßmöbel Anfertigung',
            'langtext': 'Handwerkliche Anfertigung von hochwertigen Maßmöbeln aus massivem Holz',
            'material': random.choice(cls.MATERIALS['Holzarten']),
            'menge': round(random.uniform(1.0, 10.0), 2),
            'einheit': 'm²',
            'einheitspreis': f"{round(random.uniform(50.0, 200.0), 2)}",
            'gesamtpreis': f"{round(random.uniform(500.0, 2000.0), 2)}",
            'verarbeitung': random.choice(cls.MATERIALS['Oberflächen']),
            'lieferzeit': f"{random.randint(2, 8)} Wochen"
        }

    @classmethod
    def get_german_test_data_samples(cls) -> List[Dict[str, str]]:
        """Get collection of German construction terminology for testing.

        Returns:
            List of dictionaries with German terms and translations
        """
        return [
            {
                'german': 'Tischler',
                'english': 'Carpenter',
                'category': 'Handwerk'
            },
            {
                'german': 'Schreiner',
                'english': 'Cabinet Maker',
                'category': 'Handwerk'
            },
            {
                'german': 'Eiche',
                'english': 'Oak',
                'category': 'Material'
            },
            {
                'german': 'Buche',
                'english': 'Beech',
                'category': 'Material'
            },
            {
                'german': 'lackiert',
                'english': 'Lacquered',
                'category': 'Surface'
            },
            {
                'german': 'geölt',
                'english': 'Oiled',
                'category': 'Surface'
            },
            {
                'german': 'Maßmöbel',
                'english': 'Custom Furniture',
                'category': 'Project'
            },
            {
                'german': 'Oberfläche',
                'english': 'Surface',
                'category': 'General'
            },
        ]
