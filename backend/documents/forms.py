"""Custom Django admin forms with tooltips for better UX."""
from django import forms
from .models import Document, ExtractionResult, AuditLog
from .betriebskennzahl_models import (
    BetriebskennzahlTemplate,
    HolzartKennzahl,
    OberflächenbearbeitungKennzahl,
    KomplexitaetKennzahl,
    IndividuelleBetriebskennzahl,
    MateriallistePosition,
    SaisonaleMarge,
    AdminActionAudit,
)
from .pattern_models import (
    ExtractionFailurePattern,
    PatternReviewSession,
    PatternFixProposal,
)
from .transparency_models import (
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark,
)


# =============================================================================
# DOCUMENT FORMS
# =============================================================================


class DocumentAdminForm(forms.ModelForm):
    """Admin form for Document with helpful tooltips."""

    class Meta:
        model = Document
        fields = '__all__'
        help_texts = {
            'file': 'Upload PDF, GAEB XML, or image file (max size per Django settings)',
            'original_filename': 'Original name of uploaded file (auto-populated)',
            'document_type': 'Type of document: PDF for scanned documents, GAEB for construction standards',
            'status': 'Current processing status: uploaded → processing → completed/error',
            'retention_until': 'DSGVO compliance: Document will be auto-deleted after this date',
            'is_encrypted': 'Enable encryption for sensitive data (recommended for client documents)',
            'metadata': 'Additional JSON metadata (e.g., client info, project details)',
        }


# =============================================================================
# BETRIEBSKENNZAHL FORMS (TIER 1, 2, 3)
# =============================================================================


class BetriebskennzahlTemplateAdminForm(forms.ModelForm):
    """Admin form for Betriebskennzahl templates with tooltips."""

    class Meta:
        model = BetriebskennzahlTemplate
        fields = '__all__'
        help_texts = {
            'name': 'Template name (e.g., "Schreiner Standard 2024")',
            'version': 'Version number for tracking updates (e.g., "1.0", "2.1")',
            'description': 'Detailed description of this template and when to use it',
            'is_active': 'Only one template should be active at a time',
        }


class HolzartKennzahlAdminForm(forms.ModelForm):
    """Admin form for wood type factors with tooltips."""

    class Meta:
        model = HolzartKennzahl
        fields = '__all__'
        help_texts = {
            'holzart': 'Wood type name (e.g., "Eiche", "Buche", "Kiefer")',
            'kategorie': 'Category: Hartholz (hardwood) or Weichholz (softwood)',
            'preis_faktor': 'Price multiplier: 1.0 = base price, 1.3 = +30% premium (e.g., Eiche: 1.3)',
            'verfuegbarkeit': 'Availability: verfügbar (available), begrenzt (limited), auf_anfrage (on request)',
            'is_enabled': 'Uncheck to temporarily disable this wood type without deleting',
        }


class OberflächenbearbeitungKennzahlAdminForm(forms.ModelForm):
    """Admin form for surface finishing factors with tooltips."""

    class Meta:
        model = OberflächenbearbeitungKennzahl
        fields = '__all__'
        help_texts = {
            'bearbeitung': 'Surface treatment type (e.g., "geölt", "lackiert", "naturbelassen")',
            'preis_faktor': 'Price multiplier: 1.0 = no change, 1.15 = +15% (e.g., lackiert: 1.15)',
            'zeit_faktor': 'Time multiplier: Additional labor time for this finish (1.0 = no change)',
            'is_enabled': 'Uncheck to temporarily disable this finishing option',
        }


class KomplexitaetKennzahlAdminForm(forms.ModelForm):
    """Admin form for complexity/technique factors with tooltips."""

    class Meta:
        model = KomplexitaetKennzahl
        fields = '__all__'
        help_texts = {
            'technik': 'Technique name (e.g., "gefräst", "gedrechselt", "geschnitzt")',
            'schwierigkeitsgrad': 'Difficulty: niedrig (low), mittel (medium), hoch (high), sehr_hoch (very high)',
            'preis_faktor': 'Price multiplier for this technique (e.g., hand_geschnitzt: 2.0 = +100%)',
            'zeit_faktor': 'Labor time multiplier (e.g., gedrechselt: 1.25 = +25% time)',
            'is_enabled': 'Uncheck to temporarily disable this technique',
        }


class IndividuelleBetriebskennzahlAdminForm(forms.ModelForm):
    """Admin form for company-specific metrics with tooltips."""

    class Meta:
        model = IndividuelleBetriebskennzahl
        fields = '__all__'
        help_texts = {
            'stundensatz_arbeit': 'Labor rate per hour in EUR (e.g., 65.00 for skilled carpenter)',
            'betriebskosten_umlage': 'Overhead allocation percentage (typical: 15-25%)',
            'gewinnmarge_prozent': 'Target profit margin percentage (typical: 10-20%)',
            'handwerk_template': 'Select global template for wood types, finishes, and complexity factors',
            'use_handwerk_standard': 'Enable TIER 1: Use global standards from selected template',
            'use_custom_materials': 'Enable TIER 2: Use custom material catalog (overrides global)',
            'use_seasonal_adjustments': 'Enable TIER 3: Apply seasonal campaigns and special pricing',
            'use_customer_discounts': 'Enable TIER 3: Allow customer-specific discounts',
            'use_bulk_discounts': 'Enable TIER 3: Apply bulk purchase discounts',
            'is_active': 'Only one configuration per company should be active',
        }


class MateriallistePositionAdminForm(forms.ModelForm):
    """Admin form for material catalog with tooltips."""

    class Meta:
        model = MateriallistePosition
        fields = '__all__'
        help_texts = {
            'material_name': 'Material description (e.g., "Eiche Massivholz 40mm")',
            'sku': 'Stock Keeping Unit - unique identifier (e.g., "OAK-40-M2")',
            'lieferant': 'Supplier name (e.g., "Holzhandel München GmbH")',
            'standardkosten_eur': 'Base cost per unit in EUR (e.g., 45.50 per m²)',
            'verpackungseinheit': 'Packaging unit (e.g., "Paket à 10 Stück")',
            'verfuegbarkeit': 'Stock status: auf_lager (in stock), bestellt (ordered), abgekündigt (discontinued)',
            'rabatt_ab_100': 'Discount percentage when ordering 100+ units (e.g., 5 = 5% discount)',
            'rabatt_ab_500': 'Discount percentage when ordering 500+ units (e.g., 10 = 10% discount)',
            'is_enabled': 'Uncheck to temporarily hide this material without deleting',
        }


class SaisonaleMargeAdminForm(forms.ModelForm):
    """Admin form for seasonal pricing with tooltips."""

    class Meta:
        model = SaisonaleMarge
        fields = '__all__'
        help_texts = {
            'name': 'Campaign name (e.g., "Sommerschlussverkauf 2024", "Kundentreue-Rabatt")',
            'description': 'Detailed description of this campaign and eligibility criteria',
            'adjustment_type': 'prozent (percentage) or absolut (fixed EUR amount)',
            'value': 'Adjustment value: e.g., 10 for 10% discount OR 50 for 50 EUR discount',
            'start_date': 'Campaign start date (German format: DD.MM.YYYY)',
            'end_date': 'Campaign end date (German format: DD.MM.YYYY)',
            'applicable_to': 'Who qualifies: alle (all), stammkunden (regular), neukunden (new), grosskunden (bulk)',
            'is_active': 'Uncheck to pause campaign without deleting',
        }


# =============================================================================
# PATTERN ANALYSIS FORMS
# =============================================================================


class ExtractionFailurePatternAdminForm(forms.ModelForm):
    """Admin form for extraction failure patterns with tooltips."""

    class Meta:
        model = ExtractionFailurePattern
        fields = '__all__'
        help_texts = {
            'field_name': 'Field that failed extraction (e.g., "material_name", "price")',
            'pattern_type': 'Type: ocr_quality, ner_miss, gaeb_parse, gemini_hallucination, format_error',
            'root_cause': 'Technical explanation of why extraction failed',
            'severity': 'CRITICAL (system broken), HIGH (major impact), MEDIUM (noticeable), LOW (minor)',
            'confidence_threshold': 'Confidence level where this pattern was detected (0.0-1.0)',
            'affected_document_count': 'Number of documents affected by this pattern',
            'total_occurrences': 'Total times this pattern was observed',
            'example_documents': 'JSON array of document IDs showing this pattern',
            'suggested_fix': 'Proposed solution to resolve this pattern',
            'is_reviewed': 'Check after admin has reviewed this pattern',
            'admin_notes': 'Admin comments about review decision and next steps',
            'resolution_deadline': 'Target date to resolve (auto-calculated based on severity)',
        }


class PatternReviewSessionAdminForm(forms.ModelForm):
    """Admin form for pattern review sessions with tooltips."""

    class Meta:
        model = PatternReviewSession
        fields = '__all__'
        help_texts = {
            'title': 'Review session title (e.g., "OCR Quality Review - Week 47")',
            'description': 'Detailed notes about review scope and findings',
            'status': 'draft → in_progress → approved/rejected → applied',
            'reviewed_cases_count': 'Total number of cases reviewed in this session',
            'approved_cases': 'Number of cases approved for fix deployment',
            'estimated_impact': 'Expected improvement: low (<10 docs), medium (10-50), high (>50)',
            'estimated_documents_improved': 'Number of documents expected to improve after fix',
            'scheduled_deployment': 'When approved fix will be deployed (German format: DD.MM.YYYY HH:MM)',
            'rejection_reason': 'If rejected: explain why fix was not approved',
        }


class PatternFixProposalAdminForm(forms.ModelForm):
    """Admin form for pattern fix proposals with tooltips."""

    class Meta:
        model = PatternFixProposal
        fields = '__all__'
        help_texts = {
            'title': 'Fix title (e.g., "Improve OCR preprocessing for handwritten text")',
            'description': 'Detailed explanation of proposed fix and expected outcome',
            'fix_type': 'Type: ocr_config, ner_model_update, gaeb_parser_fix, gemini_prompt, regex_update',
            'affected_field': 'Which field this fix targets (e.g., "material_name")',
            'change_details': 'JSON with before/after configuration or code changes',
            'test_sample_size': 'Number of documents used for testing this fix',
            'test_success_rate': 'Success rate in testing (0.0-1.0). Must be ≥0.85 to deploy',
            'confidence_score': 'Confidence that this fix won\'t break other extractions (0.0-1.0)',
            'validation_notes': 'Notes from testing: what worked, what didn\'t, edge cases',
            'status': 'proposed → testing → validated → deployed/rolled_back',
        }


# =============================================================================
# TRANSPARENCY FORMS
# =============================================================================


class CalculationExplanationAdminForm(forms.ModelForm):
    """Admin form for calculation explanations with tooltips."""

    class Meta:
        model = CalculationExplanation
        fields = '__all__'
        help_texts = {
            'total_price_eur': 'Final calculated price in EUR',
            'confidence_level': 'high (>92%), medium (80-92%), low (<80%) - based on extraction quality',
            'confidence_score': 'Numeric confidence score (0.0-1.0)',
            'similar_projects_count': 'Number of similar past projects used for benchmark comparison',
            'user_average_for_type': 'Average price for this project type from user\'s history',
            'deviation_from_average_percent': 'How much this price differs from user\'s typical pricing (+/- %)',
        }


class CalculationFactorAdminForm(forms.ModelForm):
    """Admin form for calculation factors with tooltips."""

    class Meta:
        model = CalculationFactor
        fields = '__all__'
        help_texts = {
            'display_order': 'Order in which factors are displayed (1, 2, 3...)',
            'factor_name': 'Factor name (e.g., "Holzart: Eiche", "Oberflächenbearbeitung: Geölt")',
            'amount_eur': 'Amount contributed by this factor in EUR',
            'impact_percent': 'Percentage impact on total price (auto-calculated)',
            'explanation_text': 'Human-readable explanation for customer (e.g., "Eiche ist ein Hartholz...")',
            'data_source': 'Where this factor came from: tier1_global, tier2_company, tier3_dynamic, ocr_extraction',
            'is_adjustable': 'True if customer can negotiate this factor',
        }


class UserProjectBenchmarkAdminForm(forms.ModelForm):
    """Admin form for user project benchmarks with tooltips."""

    class Meta:
        model = UserProjectBenchmark
        fields = '__all__'
        help_texts = {
            'project_type': 'Project category (e.g., "Küchenbau", "Treppenbau", "Möbelbau")',
            'total_projects': 'Number of completed projects of this type',
            'average_price_eur': 'Average price across all projects of this type',
            'min_price_eur': 'Lowest price for this project type',
            'max_price_eur': 'Highest price for this project type',
            'average_margin_percent': 'Average profit margin for this project type',
            'last_calculated': 'When these statistics were last updated',
        }
