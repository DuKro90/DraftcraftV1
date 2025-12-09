"""Bulk upload service for Betriebskennzahlen data.

This service handles Excel/CSV import for mass data entry, eliminating the need
for manual one-by-one data entry in the Django admin interface.

Supported models:
- HolzartKennzahl (Wood types)
- OberflächenbearbeitungKennzahl (Surface finishes)
- KomplexitaetKennzahl (Complexity factors)
- MateriallistePosition (Material catalog)
- SaisonaleMarge (Seasonal campaigns)

Features:
- Excel (.xlsx) and CSV (.csv) support
- Row-by-row validation with detailed error reporting
- Dry-run mode for preview before commit
- Duplicate detection and update support
- German number format parsing (1.234,56)
"""

import io
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from dataclasses import dataclass, field

import openpyxl
import csv
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from ..betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    MateriallistePosition,
    SaisonaleMarge,
)


@dataclass
class ValidationError:
    """Single validation error."""
    row: int
    field: str
    value: Any
    error: str


@dataclass
class BulkUploadResult:
    """Result of bulk upload operation."""
    success: bool
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """Total rows successfully processed."""
        return self.created_count + self.updated_count

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0

    def add_error(self, row: int, field: str, value: Any, error: str):
        """Add validation error."""
        self.errors.append(ValidationError(row=row, field=field, value=value, error=error))

    def get_summary(self) -> str:
        """Get human-readable summary."""
        summary = f"✓ Created: {self.created_count}, Updated: {self.updated_count}, Skipped: {self.skipped_count}"
        if self.has_errors:
            summary += f"\n✗ Errors: {len(self.errors)}"
        return summary


class GermanNumberParser:
    """Parse German number formats (1.234,56)."""

    @staticmethod
    def parse_decimal(value: str) -> Decimal:
        """
        Parse German decimal format to Decimal.

        Examples:
            1.234,56 → 1234.56
            1234,56  → 1234.56
            1234.56  → 1234.56 (also handle US format)
            1234     → 1234
        """
        if not value or value == '':
            raise ValueError("Empty value")

        # Remove whitespace
        value = str(value).strip()

        # Check if it's German format (comma as decimal separator)
        if ',' in value:
            # German format: 1.234,56
            value = value.replace('.', '')  # Remove thousands separator
            value = value.replace(',', '.')  # Convert decimal separator
        # else: assume US format or integer

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid number format: {value}") from e

    @staticmethod
    def parse_date(value: str) -> date:
        """
        Parse German date format (DD.MM.YYYY).

        Also accepts: YYYY-MM-DD, DD/MM/YYYY
        """
        if not value or value == '':
            raise ValueError("Empty date")

        value = str(value).strip()

        # Try German format first: DD.MM.YYYY
        for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Invalid date format (expected DD.MM.YYYY): {value}")


class BulkUploadService:
    """Service for bulk uploading Betriebskennzahlen data."""

    def __init__(self, user: Optional[User] = None):
        """
        Initialize bulk upload service.

        Args:
            user: User performing the upload (for user-specific data like materials)
        """
        self.user = user
        self.parser = GermanNumberParser()

    # =========================================================================
    # HOLZART (WOOD TYPES)
    # =========================================================================

    def upload_holzart_kennzahlen(
        self,
        file_content: bytes,
        template_id: int,
        file_format: str = 'xlsx',
        dry_run: bool = False,
        update_existing: bool = False
    ) -> BulkUploadResult:
        """
        Upload wood type factors from Excel/CSV.

        Expected columns:
        - holzart (str): Wood type name (e.g., "Eiche")
        - kategorie (str): hartholz/weichholz/nadelholz
        - preis_faktor (decimal): Price multiplier (e.g., 1.3)
        - verfuegbarkeit (str): Standard/Verfügbar/Knapp/Nicht verfügbar
        - is_enabled (bool): true/false, ja/nein, 1/0

        Args:
            file_content: File bytes
            template_id: BetriebskennzahlTemplate ID
            file_format: 'xlsx' or 'csv'
            dry_run: If True, validate but don't save
            update_existing: If True, update existing entries (match by holzart)

        Returns:
            BulkUploadResult with success/error details
        """
        result = BulkUploadResult(success=False)

        try:
            # Get template
            template = BetriebskennzahlTemplate.objects.get(id=template_id)
        except BetriebskennzahlTemplate.DoesNotExist:
            result.add_error(0, 'template_id', template_id, 'Template not found')
            return result

        # Parse file
        rows = self._parse_file(file_content, file_format)
        if not rows:
            result.add_error(0, 'file', '', 'No data rows found')
            return result

        # Validate headers
        required_headers = ['holzart', 'kategorie', 'preis_faktor']
        headers = rows[0]
        missing = [h for h in required_headers if h not in headers]
        if missing:
            result.add_error(0, 'headers', headers, f'Missing required columns: {missing}')
            return result

        # Process rows
        with transaction.atomic():
            for row_num, row_data in enumerate(rows[1:], start=2):
                try:
                    # Parse row
                    holzart = row_data.get('holzart', '').strip()
                    kategorie = row_data.get('kategorie', '').strip().lower()
                    preis_faktor = self.parser.parse_decimal(row_data.get('preis_faktor', ''))
                    verfuegbarkeit = row_data.get('verfuegbarkeit', 'Standard').strip()
                    is_enabled = self._parse_bool(row_data.get('is_enabled', 'true'))

                    # Validate
                    if not holzart:
                        result.add_error(row_num, 'holzart', holzart, 'Required field')
                        continue

                    if kategorie not in ['hartholz', 'weichholz', 'nadelholz']:
                        result.add_error(row_num, 'kategorie', kategorie,
                                       'Must be: hartholz, weichholz, or nadelholz')
                        continue

                    if preis_faktor <= 0:
                        result.add_error(row_num, 'preis_faktor', preis_faktor,
                                       'Must be positive')
                        continue

                    # Check for duplicates
                    existing = HolzartKennzahl.objects.filter(
                        template=template,
                        holzart__iexact=holzart
                    ).first()

                    if existing and not update_existing:
                        result.skipped_count += 1
                        continue

                    # Create or update
                    if not dry_run:
                        if existing and update_existing:
                            existing.kategorie = kategorie
                            existing.preis_faktor = preis_faktor
                            existing.verfuegbarkeit = verfuegbarkeit
                            existing.is_enabled = is_enabled
                            existing.save()
                            result.updated_count += 1
                        else:
                            HolzartKennzahl.objects.create(
                                template=template,
                                holzart=holzart,
                                kategorie=kategorie,
                                preis_faktor=preis_faktor,
                                verfuegbarkeit=verfuegbarkeit,
                                is_enabled=is_enabled
                            )
                            result.created_count += 1
                    else:
                        result.created_count += 1

                except Exception as e:
                    result.add_error(row_num, 'row', row_data, str(e))

            if dry_run:
                # Rollback transaction in dry-run mode
                transaction.set_rollback(True)

        result.success = not result.has_errors or result.total_processed > 0
        return result

    # =========================================================================
    # OBERFLÄCHENBEARBEITUNG (SURFACE FINISHES)
    # =========================================================================

    def upload_oberflaechenbearbeitung_kennzahlen(
        self,
        file_content: bytes,
        template_id: int,
        file_format: str = 'xlsx',
        dry_run: bool = False,
        update_existing: bool = False
    ) -> BulkUploadResult:
        """
        Upload surface finishing factors from Excel/CSV.

        Expected columns:
        - bearbeitung (str): Finish type (e.g., "Geölt")
        - preis_faktor (decimal): Price multiplier
        - zeit_faktor (decimal): Time multiplier
        - is_enabled (bool): true/false
        """
        result = BulkUploadResult(success=False)

        try:
            template = BetriebskennzahlTemplate.objects.get(id=template_id)
        except BetriebskennzahlTemplate.DoesNotExist:
            result.add_error(0, 'template_id', template_id, 'Template not found')
            return result

        rows = self._parse_file(file_content, file_format)
        if not rows:
            result.add_error(0, 'file', '', 'No data rows found')
            return result

        required_headers = ['bearbeitung', 'preis_faktor', 'zeit_faktor']
        headers = rows[0]
        missing = [h for h in required_headers if h not in headers]
        if missing:
            result.add_error(0, 'headers', headers, f'Missing columns: {missing}')
            return result

        with transaction.atomic():
            for row_num, row_data in enumerate(rows[1:], start=2):
                try:
                    bearbeitung = row_data.get('bearbeitung', '').strip()
                    preis_faktor = self.parser.parse_decimal(row_data.get('preis_faktor', ''))
                    zeit_faktor = self.parser.parse_decimal(row_data.get('zeit_faktor', ''))
                    is_enabled = self._parse_bool(row_data.get('is_enabled', 'true'))

                    if not bearbeitung:
                        result.add_error(row_num, 'bearbeitung', bearbeitung, 'Required')
                        continue

                    if preis_faktor <= 0 or zeit_faktor <= 0:
                        result.add_error(row_num, 'faktoren', f'{preis_faktor}/{zeit_faktor}',
                                       'Must be positive')
                        continue

                    existing = OberflächenbearbeitungKennzahl.objects.filter(
                        template=template,
                        bearbeitung__iexact=bearbeitung
                    ).first()

                    if existing and not update_existing:
                        result.skipped_count += 1
                        continue

                    if not dry_run:
                        if existing and update_existing:
                            existing.preis_faktor = preis_faktor
                            existing.zeit_faktor = zeit_faktor
                            existing.is_enabled = is_enabled
                            existing.save()
                            result.updated_count += 1
                        else:
                            OberflächenbearbeitungKennzahl.objects.create(
                                template=template,
                                bearbeitung=bearbeitung,
                                preis_faktor=preis_faktor,
                                zeit_faktor=zeit_faktor,
                                is_enabled=is_enabled
                            )
                            result.created_count += 1
                    else:
                        result.created_count += 1

                except Exception as e:
                    result.add_error(row_num, 'row', row_data, str(e))

            if dry_run:
                transaction.set_rollback(True)

        result.success = not result.has_errors or result.total_processed > 0
        return result

    # =========================================================================
    # KOMPLEXITÄT (COMPLEXITY FACTORS)
    # =========================================================================

    def upload_komplexitaet_kennzahlen(
        self,
        file_content: bytes,
        template_id: int,
        file_format: str = 'xlsx',
        dry_run: bool = False,
        update_existing: bool = False
    ) -> BulkUploadResult:
        """
        Upload complexity/technique factors from Excel/CSV.

        Expected columns:
        - technik (str): Technique name (e.g., "Gefräst")
        - schwierigkeitsgrad (str): einfach/mittel/schwer/meister
        - preis_faktor (decimal): Price multiplier
        - zeit_faktor (decimal): Time multiplier
        - is_enabled (bool): true/false
        """
        result = BulkUploadResult(success=False)

        try:
            template = BetriebskennzahlTemplate.objects.get(id=template_id)
        except BetriebskennzahlTemplate.DoesNotExist:
            result.add_error(0, 'template_id', template_id, 'Template not found')
            return result

        rows = self._parse_file(file_content, file_format)
        if not rows:
            result.add_error(0, 'file', '', 'No data rows found')
            return result

        required_headers = ['technik', 'schwierigkeitsgrad', 'preis_faktor', 'zeit_faktor']
        headers = rows[0]
        missing = [h for h in required_headers if h not in headers]
        if missing:
            result.add_error(0, 'headers', headers, f'Missing columns: {missing}')
            return result

        with transaction.atomic():
            for row_num, row_data in enumerate(rows[1:], start=2):
                try:
                    technik = row_data.get('technik', '').strip()
                    schwierigkeitsgrad = row_data.get('schwierigkeitsgrad', '').strip().lower()
                    preis_faktor = self.parser.parse_decimal(row_data.get('preis_faktor', ''))
                    zeit_faktor = self.parser.parse_decimal(row_data.get('zeit_faktor', ''))
                    is_enabled = self._parse_bool(row_data.get('is_enabled', 'true'))

                    if not technik:
                        result.add_error(row_num, 'technik', technik, 'Required')
                        continue

                    if schwierigkeitsgrad not in ['einfach', 'mittel', 'schwer', 'meister']:
                        result.add_error(row_num, 'schwierigkeitsgrad', schwierigkeitsgrad,
                                       'Must be: einfach, mittel, schwer, or meister')
                        continue

                    if preis_faktor <= 0 or zeit_faktor <= 0:
                        result.add_error(row_num, 'faktoren', f'{preis_faktor}/{zeit_faktor}',
                                       'Must be positive')
                        continue

                    existing = KomplexitaetKennzahl.objects.filter(
                        template=template,
                        technik__iexact=technik
                    ).first()

                    if existing and not update_existing:
                        result.skipped_count += 1
                        continue

                    if not dry_run:
                        if existing and update_existing:
                            existing.schwierigkeitsgrad = schwierigkeitsgrad
                            existing.preis_faktor = preis_faktor
                            existing.zeit_faktor = zeit_faktor
                            existing.is_enabled = is_enabled
                            existing.save()
                            result.updated_count += 1
                        else:
                            KomplexitaetKennzahl.objects.create(
                                template=template,
                                technik=technik,
                                schwierigkeitsgrad=schwierigkeitsgrad,
                                preis_faktor=preis_faktor,
                                zeit_faktor=zeit_faktor,
                                is_enabled=is_enabled
                            )
                            result.created_count += 1
                    else:
                        result.created_count += 1

                except Exception as e:
                    result.add_error(row_num, 'row', row_data, str(e))

            if dry_run:
                transaction.set_rollback(True)

        result.success = not result.has_errors or result.total_processed > 0
        return result

    # =========================================================================
    # MATERIALLISTE (MATERIAL CATALOG)
    # =========================================================================

    def upload_materialliste(
        self,
        file_content: bytes,
        user: User,
        file_format: str = 'xlsx',
        dry_run: bool = False,
        update_existing: bool = False
    ) -> BulkUploadResult:
        """
        Upload material catalog from Excel/CSV.

        Expected columns:
        - material_name (str): Material name
        - sku (str): Stock keeping unit (unique)
        - lieferant (str): Supplier name
        - standardkosten_eur (decimal): Standard cost per unit
        - verpackungseinheit (str): Packaging unit (e.g., "Box of 100")
        - verfuegbarkeit (str): Auf Lager/Bestellbar/Nicht verfügbar
        - rabatt_ab_100 (decimal, optional): Discount % at 100+ qty
        - rabatt_ab_500 (decimal, optional): Discount % at 500+ qty
        - is_enabled (bool): true/false
        """
        result = BulkUploadResult(success=False)

        rows = self._parse_file(file_content, file_format)
        if not rows:
            result.add_error(0, 'file', '', 'No data rows found')
            return result

        required_headers = ['material_name', 'sku', 'lieferant', 'standardkosten_eur']
        headers = rows[0]
        missing = [h for h in required_headers if h not in headers]
        if missing:
            result.add_error(0, 'headers', headers, f'Missing columns: {missing}')
            return result

        with transaction.atomic():
            for row_num, row_data in enumerate(rows[1:], start=2):
                try:
                    material_name = row_data.get('material_name', '').strip()
                    sku = row_data.get('sku', '').strip()
                    lieferant = row_data.get('lieferant', '').strip()
                    standardkosten = self.parser.parse_decimal(row_data.get('standardkosten_eur', ''))
                    verpackungseinheit = row_data.get('verpackungseinheit', 'Stück').strip()
                    verfuegbarkeit = row_data.get('verfuegbarkeit', 'Auf Lager').strip()

                    # Optional fields
                    rabatt_100 = row_data.get('rabatt_ab_100', '')
                    rabatt_ab_100 = self.parser.parse_decimal(rabatt_100) if rabatt_100 else Decimal('0')

                    rabatt_500 = row_data.get('rabatt_ab_500', '')
                    rabatt_ab_500 = self.parser.parse_decimal(rabatt_500) if rabatt_500 else Decimal('0')

                    is_enabled = self._parse_bool(row_data.get('is_enabled', 'true'))

                    # Validate
                    if not material_name or not sku or not lieferant:
                        result.add_error(row_num, 'required_fields', row_data,
                                       'material_name, sku, and lieferant are required')
                        continue

                    if standardkosten <= 0:
                        result.add_error(row_num, 'standardkosten_eur', standardkosten,
                                       'Must be positive')
                        continue

                    # Check for duplicate SKU
                    existing = MateriallistePosition.objects.filter(
                        user=user,
                        sku=sku
                    ).first()

                    if existing and not update_existing:
                        result.skipped_count += 1
                        continue

                    if not dry_run:
                        if existing and update_existing:
                            existing.material_name = material_name
                            existing.lieferant = lieferant
                            existing.standardkosten_eur = standardkosten
                            existing.verpackungseinheit = verpackungseinheit
                            existing.verfuegbarkeit = verfuegbarkeit
                            existing.rabatt_ab_100 = rabatt_ab_100
                            existing.rabatt_ab_500 = rabatt_ab_500
                            existing.is_enabled = is_enabled
                            existing.save()
                            result.updated_count += 1
                        else:
                            MateriallistePosition.objects.create(
                                user=user,
                                material_name=material_name,
                                sku=sku,
                                lieferant=lieferant,
                                standardkosten_eur=standardkosten,
                                verpackungseinheit=verpackungseinheit,
                                verfuegbarkeit=verfuegbarkeit,
                                rabatt_ab_100=rabatt_ab_100,
                                rabatt_ab_500=rabatt_ab_500,
                                is_enabled=is_enabled
                            )
                            result.created_count += 1
                    else:
                        result.created_count += 1

                except Exception as e:
                    result.add_error(row_num, 'row', row_data, str(e))

            if dry_run:
                transaction.set_rollback(True)

        result.success = not result.has_errors or result.total_processed > 0
        return result

    # =========================================================================
    # SAISONALE MARGE (SEASONAL CAMPAIGNS)
    # =========================================================================

    def upload_saisonale_marge(
        self,
        file_content: bytes,
        user: User,
        file_format: str = 'xlsx',
        dry_run: bool = False
    ) -> BulkUploadResult:
        """
        Upload seasonal pricing campaigns from Excel/CSV.

        Expected columns:
        - name (str): Campaign name
        - description (str): Description
        - adjustment_type (str): prozent/absolut
        - value (decimal): Adjustment value
        - start_date (date): DD.MM.YYYY
        - end_date (date): DD.MM.YYYY
        - applicable_to (str): Alle/Neukunden/Stammkunden/VIP
        - is_active (bool): true/false
        """
        result = BulkUploadResult(success=False)

        rows = self._parse_file(file_content, file_format)
        if not rows:
            result.add_error(0, 'file', '', 'No data rows found')
            return result

        required_headers = ['name', 'adjustment_type', 'value', 'start_date', 'end_date']
        headers = rows[0]
        missing = [h for h in required_headers if h not in headers]
        if missing:
            result.add_error(0, 'headers', headers, f'Missing columns: {missing}')
            return result

        with transaction.atomic():
            for row_num, row_data in enumerate(rows[1:], start=2):
                try:
                    name = row_data.get('name', '').strip()
                    description = row_data.get('description', '').strip()
                    adjustment_type = row_data.get('adjustment_type', '').strip().lower()
                    value = self.parser.parse_decimal(row_data.get('value', ''))
                    start_date = self.parser.parse_date(row_data.get('start_date', ''))
                    end_date = self.parser.parse_date(row_data.get('end_date', ''))
                    applicable_to = row_data.get('applicable_to', 'Alle').strip()
                    is_active = self._parse_bool(row_data.get('is_active', 'true'))

                    # Validate
                    if not name:
                        result.add_error(row_num, 'name', name, 'Required')
                        continue

                    if adjustment_type not in ['prozent', 'absolut']:
                        result.add_error(row_num, 'adjustment_type', adjustment_type,
                                       'Must be: prozent or absolut')
                        continue

                    if start_date >= end_date:
                        result.add_error(row_num, 'dates', f'{start_date} - {end_date}',
                                       'start_date must be before end_date')
                        continue

                    if not dry_run:
                        SaisonaleMarge.objects.create(
                            user=user,
                            name=name,
                            description=description,
                            adjustment_type=adjustment_type,
                            value=value,
                            start_date=start_date,
                            end_date=end_date,
                            applicable_to=applicable_to,
                            is_active=is_active
                        )
                        result.created_count += 1
                    else:
                        result.created_count += 1

                except Exception as e:
                    result.add_error(row_num, 'row', row_data, str(e))

            if dry_run:
                transaction.set_rollback(True)

        result.success = not result.has_errors or result.total_processed > 0
        return result

    # =========================================================================
    # FILE PARSING UTILITIES
    # =========================================================================

    def _parse_file(self, file_content: bytes, file_format: str) -> List[Dict[str, str]]:
        """
        Parse Excel or CSV file into list of dicts.

        Returns:
            List where first element is headers dict, rest are data rows
        """
        if file_format == 'xlsx':
            return self._parse_excel(file_content)
        elif file_format == 'csv':
            return self._parse_csv(file_content)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def _parse_excel(self, file_content: bytes) -> List[Dict[str, str]]:
        """Parse Excel file using openpyxl."""
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active

        rows = []
        headers = None

        for row in ws.iter_rows(values_only=True):
            # Skip empty rows
            if not any(row):
                continue

            if headers is None:
                # First non-empty row = headers
                headers = [str(cell).strip().lower() if cell else '' for cell in row]
                rows.append({h: h for h in headers})  # Header dict
            else:
                # Data row
                row_dict = {}
                for i, header in enumerate(headers):
                    value = row[i] if i < len(row) else ''
                    row_dict[header] = str(value) if value is not None else ''
                rows.append(row_dict)

        return rows

    def _parse_csv(self, file_content: bytes) -> List[Dict[str, str]]:
        """Parse CSV file."""
        content = file_content.decode('utf-8-sig')  # Handle BOM
        reader = csv.DictReader(io.StringIO(content))

        rows = []

        # Normalize headers to lowercase
        if reader.fieldnames:
            headers = [h.strip().lower() for h in reader.fieldnames]
            rows.append({h: h for h in headers})

            # Read data rows
            for row in reader:
                normalized_row = {k.strip().lower(): v.strip() for k, v in row.items()}
                rows.append(normalized_row)

        return rows

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean from various formats."""
        if isinstance(value, bool):
            return value

        value = str(value).strip().lower()
        return value in ['true', 'yes', 'ja', '1', 'y', 'j']
