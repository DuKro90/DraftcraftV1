# Bulk Upload Guide - Betriebskennzahlen

**Problem:** Manually entering 50+ wood types, materials, or pricing factors one-by-one in Django admin is tedious and time-consuming.

**Solution:** Bulk upload from Excel/CSV templates with automatic validation.

---

## Quick Start (3 Steps)

### 1. Download Template

Navigate to the Django admin page for your desired model:
- Wood Types: `/admin/documents/holzartkennzahl/`
- Surface Finishes: `/admin/documents/oberflächenbearbeitungkennzahl/`
- Complexity Factors: `/admin/documents/komplexitaetkennzahl/`
- Materials: `/admin/documents/materiallisteposition/`
- Seasonal Campaigns: `/admin/documents/saisonalemarge/`

Click: **📥 Template herunterladen (Excel)** or **📥 Template herunterladen (CSV)**

### 2. Fill Template with Your Data

Open the downloaded template in Excel or any spreadsheet software.

**Important:**
- ✅ Keep the header row unchanged
- ✅ Fill data rows starting from row 2
- ✅ Use German number format: `1.234,56` (or `1234.56` also works)
- ✅ Use German date format: `DD.MM.YYYY`
- ✅ Follow example rows for formatting guidance
- ❌ Don't delete or rename columns

**Example - Wood Types Template:**
```
holzart     | kategorie  | preis_faktor | verfuegbarkeit | is_enabled
Eiche       | hartholz   | 1,3          | Verfügbar      | true
Buche       | hartholz   | 1,2          | Standard       | true
Kiefer      | nadelholz  | 0,9          | Standard       | true
```

### 3. Upload to Django Admin

1. Click: **📤 Bulk Upload** button
2. Select your filled template file
3. ✅ **Enable "Vorschau-Modus"** first (dry-run for validation)
4. Click **🚀 Upload starten**
5. Review validation results
6. If no errors: Disable "Vorschau-Modus" and upload again to save

---

## Supported Models

### 1. HolzartKennzahl (Wood Types)

**Required Fields:**
- `holzart` - Wood type name (e.g., "Eiche", "Buche")
- `kategorie` - Category: `hartholz`, `weichholz`, `nadelholz`
- `preis_faktor` - Price multiplier (e.g., 1,3 for +30%)

**Optional Fields:**
- `verfuegbarkeit` - Availability: `Standard`, `Verfügbar`, `Knapp`, `Nicht verfügbar`
- `is_enabled` - Enable/disable: `true`/`false`

**Notes:**
- Requires selecting a `BetriebskennzahlTemplate` during upload
- Duplicates detected by `holzart` name (case-insensitive)

---

### 2. OberflächenbearbeitungKennzahl (Surface Finishes)

**Required Fields:**
- `bearbeitung` - Finish type (e.g., "Geölt", "Lackiert")
- `preis_faktor` - Price multiplier
- `zeit_faktor` - Time multiplier

**Optional Fields:**
- `is_enabled` - Enable/disable: `true`/`false`

**Notes:**
- Requires selecting a `BetriebskennzahlTemplate`
- Both price and time factors must be positive

---

### 3. KomplexitaetKennzahl (Complexity Factors)

**Required Fields:**
- `technik` - Technique name (e.g., "Gefräst", "Gedrechselt")
- `schwierigkeitsgrad` - Difficulty: `einfach`, `mittel`, `schwer`, `meister`
- `preis_faktor` - Price multiplier
- `zeit_faktor` - Time multiplier

**Optional Fields:**
- `is_enabled` - Enable/disable: `true`/`false`

**Notes:**
- Requires selecting a `BetriebskennzahlTemplate`
- Difficulty levels translate to different pricing tiers

---

### 4. MateriallistePosition (Material Catalog)

**Required Fields:**
- `material_name` - Material name
- `sku` - Stock keeping unit (unique per user)
- `lieferant` - Supplier name
- `standardkosten_eur` - Standard cost per unit

**Optional Fields:**
- `verpackungseinheit` - Packaging unit (default: "Stück")
- `verfuegbarkeit` - Availability: `Auf Lager`, `Bestellbar`, `Nicht verfügbar`
- `rabatt_ab_100` - Discount % at 100+ quantity (default: 0)
- `rabatt_ab_500` - Discount % at 500+ quantity (default: 0)
- `is_enabled` - Enable/disable: `true`/`false`

**Notes:**
- Requires selecting a `User/Company` during upload
- SKU must be unique per user
- Use `update_existing` to modify prices/discounts

**Example:**
```
material_name       | sku        | lieferant | standardkosten_eur | verpackungseinheit | rabatt_ab_100 | rabatt_ab_500
Schrauben 4x40mm    | SCH-4x40   | Würth     | 12,50              | Box zu 100         | 5             | 10
Leim PU D4 5L       | LEIM-D4-5L | Titebond  | 45,80              | 5 Liter Flasche    | 0             | 15
```

---

### 5. SaisonaleMarge (Seasonal Campaigns)

**Required Fields:**
- `name` - Campaign name
- `adjustment_type` - Type: `prozent` or `absolut`
- `value` - Adjustment value
- `start_date` - Start date (DD.MM.YYYY)
- `end_date` - End date (DD.MM.YYYY)

**Optional Fields:**
- `description` - Campaign description
- `applicable_to` - Target: `Alle`, `Neukunden`, `Stammkunden`, `VIP`
- `is_active` - Enable/disable: `true`/`false`

**Notes:**
- Requires selecting a `User/Company`
- Start date must be before end date
- No duplicate detection (allows multiple overlapping campaigns)

**Example:**
```
name              | adjustment_type | value | start_date | end_date   | applicable_to
Sommeraktion 2025 | prozent         | 10    | 01.06.2025 | 31.08.2025 | Neukunden
Winterkampagne    | prozent         | 5     | 01.11.2025 | 31.01.2026 | Alle
```

---

## Features

### ✅ Dry-Run Mode (Vorschau)

Always use dry-run first to validate your data without saving:

1. Enable **"Vorschau-Modus (keine Änderungen speichern)"** checkbox
2. Upload file
3. Review validation results:
   - ✓ **Success:** Shows how many rows would be created/updated
   - ✗ **Errors:** Shows row number, field, and error message
4. Fix errors in your Excel file
5. Disable "Vorschau-Modus" and upload again to save

### ♻️ Update Existing Entries

Enable **"Bestehende Einträge aktualisieren"** to update instead of skip:

- **Wood Types, Surfaces, Complexity:** Matches by name (case-insensitive)
- **Materials:** Matches by SKU
- **Campaigns:** Always creates new (no matching)

**Use Cases:**
- Update prices after supplier changes
- Adjust multipliers based on market conditions
- Modify availability status
- Update discounts for bulk orders

### 🇩🇪 German Format Support

**Numbers:**
- ✅ German: `1.234,56` → 1234.56
- ✅ US: `1234.56` → 1234.56
- ✅ Simple: `1234` → 1234

**Dates:**
- ✅ German: `31.12.2025` → 2025-12-31
- ✅ ISO: `2025-12-31` → 2025-12-31
- ✅ Slash: `31/12/2025` → 2025-12-31

**Booleans:**
- ✅ English: `true`, `false`, `yes`, `no`, `y`, `n`
- ✅ German: `ja`, `nein`, `j`
- ✅ Numeric: `1`, `0`

### ⚠️ Error Handling

Errors are reported per row with:
- **Row Number:** Exact row in your Excel file
- **Field Name:** Which column has the issue
- **Value:** What you entered
- **Error Message:** What's wrong

**Example Error:**
```
Zeile 5, Feld "preis_faktor": Must be positive (Wert: "-1.2")
```

**Common Errors:**
- Missing required fields
- Invalid enum values (e.g., wrong kategorie)
- Negative numbers where positive required
- Invalid date formats
- Duplicate SKUs/names

---

## Best Practices

### 1. Always Use Dry-Run First
Never upload directly to production without validation.

### 2. Start Small
Test with 5-10 rows first, then scale to hundreds.

### 3. Keep Templates
Save your filled templates for future updates.

### 4. Document Changes
Use descriptive campaign names and material descriptions.

### 5. Version Control
Keep old templates before major updates (e.g., `materials_2025_Q1.xlsx`).

### 6. Check Encoding
Use UTF-8 encoding for CSV files to support umlauts (ä, ö, ü, ß).

### 7. Validate Formulas
Don't use Excel formulas in data cells—only plain values.

---

## Troubleshooting

### Problem: "Missing required columns" error
**Solution:** Make sure you didn't delete or rename header columns.

### Problem: "Invalid number format" error
**Solution:** Use German format `1.234,56` or `1234.56` (no spaces, letters, or extra symbols).

### Problem: "Invalid date format" error
**Solution:** Use `DD.MM.YYYY` format (e.g., `31.12.2025`).

### Problem: Duplicate SKU/Name warning
**Solution:** Either:
- Use different SKU/name
- Enable "Bestehende Einträge aktualisieren" to update instead

### Problem: Excel dropdowns not working in CSV
**Solution:** Dropdowns only work in `.xlsx` format. Use Excel templates for validation.

### Problem: Umlauts (ä, ö, ü) not displaying correctly
**Solution:**
- Save CSV with UTF-8 encoding
- Or use Excel `.xlsx` format (handles encoding automatically)

---

## Performance

| Rows | Excel Upload Time | CSV Upload Time |
|------|-------------------|-----------------|
| 10   | <1 second         | <1 second       |
| 100  | ~2 seconds        | ~1 second       |
| 500  | ~8 seconds        | ~5 seconds      |
| 1000 | ~15 seconds       | ~10 seconds     |

**Tips for Large Uploads:**
- Split into batches of 200-500 rows
- Use CSV for faster processing
- Disable validation dropdowns if not needed

---

## API Usage (Programmatic)

For integration with external systems:

```python
from documents.services.bulk_upload_service import BulkUploadService

# Initialize service
service = BulkUploadService(user=request.user)

# Read file
with open('holzarten.xlsx', 'rb') as f:
    file_content = f.read()

# Upload with dry-run
result = service.upload_holzart_kennzahlen(
    file_content=file_content,
    template_id=1,
    file_format='xlsx',
    dry_run=True,  # Set to False to save
    update_existing=False
)

# Check results
if result.success:
    print(f"✓ Created: {result.created_count}")
    print(f"✓ Updated: {result.updated_count}")
    print(f"⊘ Skipped: {result.skipped_count}")
else:
    print(f"✗ Errors: {len(result.errors)}")
    for error in result.errors:
        print(f"  Row {error.row}, {error.field}: {error.error}")
```

---

## Template Generation (Programmatic)

```python
from documents.services.template_generator import TemplateGenerator

generator = TemplateGenerator()

# Generate Excel template
excel_bytes = generator.generate_holzart_template(file_format='xlsx')

# Save to file
with open('holzarten_template.xlsx', 'wb') as f:
    f.write(excel_bytes)

# Generate CSV template
csv_bytes = generator.generate_materialliste_template(file_format='csv')
```

---

## Support

For issues or questions:
1. Check this guide first
2. Review error messages carefully (they're specific!)
3. Test with example data from downloaded templates
4. Check CHANGELOG.md for recent changes
5. Contact system administrator

**Version:** 1.5.0
**Last Updated:** December 03, 2025
