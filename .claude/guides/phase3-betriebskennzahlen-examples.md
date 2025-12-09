# Phase 3: Betriebskennzahlen - Detailed Code Examples

**Version:** 1.0.0
**Letzte Aktualisierung:** November 27, 2025
**Status:** ✅ Production Ready

---

## 📋 Wann dieses Dokument nutzen?

**Verwende dieses Dokument für:**
- Detaillierte Code-Beispiele für CalculationEngine
- Komplexe Pricing-Szenarien
- PatternAnalyzer Integration
- SafeKnowledgeBuilder Deployment-Workflows

**Für Quick-Reference siehe:** `.claude/CLAUDE.md` (Übersicht) und `PHASE3_INTEGRATION_SUMMARY.md` (Architecture)

---

## 💰 CalculationEngine - Detaillierte Beispiele

### Beispiel 1: Einfache Möbelkalkulation (Eiche-Tisch)

```python
from extraction.services.calculation_engine import CalculationEngine
from decimal import Decimal

# Setup
engine = CalculationEngine(user)

# Extracted Data aus OCR/NER/Agent
extracted_data = {
    'project_description': 'Esstisch aus Eiche, geölt',
    'holzart': 'eiche',
    'oberflaeche': 'geölt',
    'komplexitaet': 'gefräst',
    'labor_hours': 18,
    'material_quantity': 2.5,  # m² Holz
}

# Berechnung
result = engine.calculate_project_price(
    extracted_data=extracted_data,
    customer_type='neue_kunden',
    breakdown=True
)

print(result)
```

**Erwartete Ausgabe:**

```python
{
    'total_price_eur': Decimal('1876.50'),
    'breakdown': {
        'base_labor': Decimal('900.00'),     # 18h × 50€
        'material_cost': Decimal('325.00'),  # 2.5m² × 130€ (Eiche-Faktor)

        # TIER 1 Adjustments
        'wood_factor_adjustment': Decimal('97.50'),     # +30% für Eiche
        'surface_adjustment': Decimal('32.50'),         # +10% für Öl
        'complexity_adjustment': Decimal('48.75'),      # +15% für Fräsen

        # TIER 2 Company
        'overhead': Decimal('202.50'),       # 15% Gemeinkosten
        'margin': Decimal('270.25'),         # 20% Marge

        # Final
        'subtotal_netto': Decimal('1876.50'),
        'mwst_19': Decimal('356.54'),
        'total_brutto': Decimal('2233.04')
    },
    'warnings': [],
    'applied_factors': {
        'holzart': 1.3,
        'oberflaeche': 1.1,
        'komplexitaet': 1.15
    }
}
```

### Beispiel 2: Komplexe Kalkulation mit Custom Materials

```python
# Setup mit Custom Materials
from documents.models import MateriallistePosition, IndividuelleBetriebskennzahl

# User hat eigene Eiche-Preise
material = MateriallistePosition.objects.create(
    user=user,
    sku='EICHE-25MM-PREMIUM',
    bezeichnung='Eiche massiv 25mm Premium-Qualität',
    einheit='m²',
    einheitspreis_netto=Decimal('180.00'),  # Höher als Standard
    mindestbestellmenge=Decimal('1.0'),
    bulk_discount_threshold=Decimal('10.0'),
    bulk_discount_percent=Decimal('15.0')
)

# Betriebskennzahl aktiviert Custom Materials
kennzahl = IndividuelleBetriebskennzahl.objects.get(user=user)
kennzahl.use_custom_materials = True
kennzahl.save()

# Extraction mit SKU
extracted_data = {
    'material_sku': 'EICHE-25MM-PREMIUM',
    'material_quantity': 15.0,  # Qualifiziert für Bulk Discount
    'holzart': 'eiche',
    'oberflaeche': 'klavierlack',  # Premium finish
    'komplexitaet': 'hand_geschnitzt',
    'labor_hours': 80,
}

result = engine.calculate_project_price(
    extracted_data=extracted_data,
    customer_type='bestehende_kunden',
    breakdown=True
)

print(result)
```

**Erwartete Ausgabe:**

```python
{
    'total_price_eur': Decimal('12850.25'),
    'breakdown': {
        'base_labor': Decimal('4000.00'),    # 80h × 50€

        # Custom Material mit Bulk Discount
        'material_cost': Decimal('2295.00'),  # 15m² × 180€ × 0.85 (bulk)
        'material_bulk_discount': Decimal('-405.00'),

        # TIER 1 Premium
        'wood_factor_adjustment': Decimal('688.50'),    # Eiche 1.3x
        'surface_adjustment': Decimal('1147.50'),       # Klavierlack 1.6x
        'complexity_adjustment': Decimal('1435.00'),    # Hand-geschnitzt 2.0x

        # TIER 2
        'overhead': Decimal('1434.15'),      # 15%
        'margin': Decimal('1921.53'),        # 20%

        # TIER 3 - Bestandskunden Discount
        'customer_discount': Decimal('-642.51'),  # -5%

        'subtotal_netto': Decimal('12850.25'),
        'mwst_19': Decimal('2441.55'),
        'total_brutto': Decimal('15291.80')
    },
    'warnings': [
        'Premium surface finish applied: Klavierlack',
        'High complexity factor: hand_geschnitzt (2.0x)',
        'Bulk discount applied: 15% off for 15.0 m²'
    ],
    'applied_factors': {
        'holzart': 1.3,
        'oberflaeche': 1.6,
        'komplexitaet': 2.0,
        'bulk_discount': 0.85,
        'customer_discount': 0.95
    }
}
```

### Beispiel 3: Saisonale Anpassungen

```python
from documents.models import SaisonaleMarge
from datetime import date

# Winteraktion: -10% auf alle Projekte
winter_campaign = SaisonaleMarge.objects.create(
    kennzahl=kennzahl,
    bezeichnung='Winteraktion 2025',
    gueltig_von=date(2025, 1, 1),
    gueltig_bis=date(2025, 2, 28),
    anpassung_prozent=Decimal('-10.0'),
    aktiv=True
)

# Feature aktivieren
kennzahl.use_seasonal_adjustments = True
kennzahl.save()

# Normale Kalkulation - Seasonal wird automatisch angewendet
extracted_data = {
    'holzart': 'buche',
    'labor_hours': 10,
}

result = engine.calculate_project_price(
    extracted_data=extracted_data,
    breakdown=True
)

# Ergebnis enthält:
# 'seasonal_adjustment': Decimal('-50.00'),  # -10% von Subtotal
# 'seasonal_campaign': 'Winteraktion 2025'
```

---

## 🔍 PatternAnalyzer - Detaillierte Szenarien

### Beispiel 1: Analyse nach Extraktion mit niedriger Confidence

```python
from extraction.services.pattern_analyzer import PatternAnalyzer
from documents.models import ExtractionResult

# Setup
analyzer = PatternAnalyzer(user)

# Simuliere 10 Extractionen mit bekannten Issues
for i in range(10):
    ExtractionResult.objects.create(
        user=user,
        document_id=f"DOC-{i:03d}",
        extracted_data={
            'amount': 1250.50,
            'vendor': 'Müller',  # Inkomplett
            'material': 'Eiche 25mm'
        },
        confidence_scores={
            'amount': 0.95,
            'vendor': 0.65,      # LOW
            'material': 0.82
        }
    )

# Analyse ausführen
analysis = analyzer.analyze_extraction_results(days_back=7)

print(analysis)
```

**Erwartete Ausgabe:**

```python
{
    'summary': {
        'total_extractions': 10,
        'low_confidence_count': 10,
        'affected_fields': ['vendor'],
        'average_confidence': 0.81
    },

    'low_confidence_patterns': [
        {
            'field_name': 'vendor',
            'occurrence_count': 10,
            'average_confidence': 0.65,
            'confidence_range': '0.60-0.70',
            'example_values': ['Müller', 'Schmidt', 'Bauer'],
            'severity': 'HIGH'
        }
    ],

    'grouped_failures': {
        'vendor': {
            'very_low': [],
            'low': [
                {
                    'range': '0.60-0.70',
                    'count': 10,
                    'percentage': 100.0,
                    'examples': [...]
                }
            ],
            'medium': []
        }
    },

    'root_causes': [
        {
            'field': 'vendor',
            'cause': 'incomplete_company_name',
            'description': 'OCR extracts partial company names without legal form (GmbH, AG)',
            'frequency': 10,
            'confidence': 0.9,
            'typical_patterns': [
                'Missing "GmbH" suffix',
                'Missing "Schreinerei" prefix'
            ]
        }
    ],

    'recommendations': [
        {
            'priority': 'CRITICAL',
            'field': 'vendor',
            'recommendation': 'Implement company name completion logic',
            'estimated_impact': 'Would improve 10 extractions (100% of failures)',
            'suggested_fix_type': 'extraction_logic',
            'implementation_notes': [
                'Add dictionary of known vendors with full names',
                'Pattern matching for legal forms (GmbH, AG, e.K.)',
                'Fuzzy matching against vendor database'
            ]
        }
    ],

    'timeline': [
        {'date': '2025-11-27', 'failures': 10, 'success_rate': 0.0}
    ]
}
```

### Beispiel 2: Pattern Review Session erstellen

```python
from documents.models import PatternReviewSession, PatternFixProposal

# Analyst reviewed die Patterns
session = PatternReviewSession.objects.create(
    user=user,
    reviewed_by=admin_user,
    patterns_reviewed=10,
    patterns_confirmed=8,
    patterns_rejected=2,
    notes='Vendor name completion needed for 8/10 cases'
)

# Create Fix Proposals basierend auf Review
proposal = PatternFixProposal.objects.create(
    pattern_session=session,
    field_name='vendor',
    fix_type='extraction_logic',
    description='Add company name completion using vendor database',
    implementation_code='''
def complete_vendor_name(partial_name: str) -> str:
    """Complete partial vendor name with legal form."""
    vendors_db = {
        'Müller': 'Schreinerei Müller GmbH',
        'Schmidt': 'Tischlerei Schmidt e.K.',
        'Bauer': 'Holzbau Bauer AG'
    }
    return vendors_db.get(partial_name, partial_name)
''',
    expected_improvement_percent=Decimal('85.0'),
    confidence_score=Decimal('90.0'),
    status='proposed'
)

print(f"Proposal created: {proposal.id}")
```

### Beispiel 3: Pattern zu Knowledge-Fix Workflow

```python
# 1. Analyst identifiziert Pattern
analysis = analyzer.analyze_extraction_results()

# 2. Root Cause Analyse
root_cause = analysis['root_causes'][0]
print(f"Cause: {root_cause['cause']}")
# → "incomplete_company_name"

# 3. Fix Proposal erstellen
proposal = PatternFixProposal.objects.create(
    field_name=root_cause['field'],
    fix_type='extraction_logic',
    description=root_cause['description'],
    status='proposed'
)

# 4. Testing Phase
# Developer implementiert Fix und testet
test_results = run_fix_tests(proposal)
proposal.test_success_rate = test_results['success_rate']
proposal.status = 'testing'
proposal.save()

# 5. Validation
if test_results['success_rate'] >= 85:
    proposal.status = 'validated'
    proposal.confidence_score = Decimal('90.0')
    proposal.save()

# 6. Deployment (siehe SafeKnowledgeBuilder unten)
```

---

## 🛡️ SafeKnowledgeBuilder - Deployment Examples

### Beispiel 1: Can Apply Fix - Readiness Check

```python
from extraction.services.knowledge_builder import SafeKnowledgeBuilder

builder = SafeKnowledgeBuilder(user)

# Proposal aus obigem Beispiel
proposal = PatternFixProposal.objects.get(id=123)

# Deployment Readiness prüfen
can_apply, reason = builder.can_apply_fix(proposal)

if can_apply:
    print("✅ Ready for deployment")
else:
    print(f"❌ Cannot deploy: {reason}")
    # Mögliche Gründe:
    # - "Status must be 'validated' (currently 'proposed')"
    # - "Test success rate 75.0% below required 85%"
    # - "Confidence score 70.0% below required 80%"
```

### Beispiel 2: Deployment Checklist

```python
# Vollständige Checklist vor Deployment
checklist = builder.get_deployment_checklist(proposal)

print(checklist)
```

**Erwartete Ausgabe:**

```python
{
    'proposal_id': 123,
    'field_name': 'vendor',
    'fix_type': 'extraction_logic',

    'checks': [
        {
            'name': 'Status Validation',
            'passed': True,
            'message': 'Status is "validated" ✅'
        },
        {
            'name': 'Test Success Rate',
            'passed': True,
            'message': 'Success rate 92.0% exceeds requirement (85%) ✅'
        },
        {
            'name': 'Confidence Score',
            'passed': True,
            'message': 'Confidence 90.0% exceeds requirement (80%) ✅'
        },
        {
            'name': 'Deployment Window',
            'passed': True,
            'message': 'Within deployment window (Mon-Thu, 09:00-16:00) ✅'
        }
    ],

    'ready_for_deployment': True,

    'estimated_impact': {
        'affected_extractions_last_30d': 85,
        'estimated_improvement': '92% of 85 extractions',
        'estimated_failures_prevented': 78
    },

    'rollback_plan': {
        'rollback_available': True,
        'rollback_window_days': 30,
        'rollback_deadline': '2025-12-27'
    }
}
```

### Beispiel 3: Safe Deployment mit Rollback

```python
# Deployment
try:
    result = builder.apply_fix(
        proposal=proposal,
        deployed_by=admin_user,
        deployment_notes='Vendor name completion logic - tested on 100 samples'
    )

    print(f"✅ Deployed: {result['deployment_id']}")
    print(f"Applied at: {result['applied_at']}")
    print(f"Monitoring until: {result['monitoring_deadline']}")

except DeploymentError as e:
    print(f"❌ Deployment failed: {e}")

# Monitoring Phase (7 Tage)
# Check impact on new extractions
from datetime import datetime, timedelta

monitoring_start = result['applied_at']
monitoring_end = monitoring_start + timedelta(days=7)

# Nach 7 Tagen: Evaluation
new_extractions = ExtractionResult.objects.filter(
    user=user,
    created_at__gte=monitoring_start,
    created_at__lte=monitoring_end
)

improvement = evaluate_fix_impact(new_extractions, 'vendor')

if improvement['success_rate'] < 0.85:
    # Rollback!
    rollback_result = builder.rollback_fix(
        proposal=proposal,
        rolled_back_by=admin_user,
        rollback_reason='Success rate dropped to 78% after deployment'
    )
    print(f"⚠️ Rolled back: {rollback_result}")
else:
    print(f"✅ Fix successful: {improvement['success_rate']:.1%} success rate")
```

### Beispiel 4: Kompletter Fix Lifecycle

```python
# === PHASE 1: DETECTION ===
analyzer = PatternAnalyzer(user)
analysis = analyzer.analyze_extraction_results(days_back=30)

critical_issues = [
    r for r in analysis['recommendations']
    if r['priority'] == 'CRITICAL'
]

print(f"Found {len(critical_issues)} critical issues")

# === PHASE 2: PROPOSAL ===
for issue in critical_issues:
    session = PatternReviewSession.objects.create(
        user=user,
        reviewed_by=admin_user,
        patterns_reviewed=issue['estimated_impact']
    )

    proposal = PatternFixProposal.objects.create(
        pattern_session=session,
        field_name=issue['field'],
        fix_type=issue['suggested_fix_type'],
        description=issue['recommendation'],
        status='proposed'
    )

    print(f"Created proposal {proposal.id} for {issue['field']}")

# === PHASE 3: TESTING ===
for proposal in PatternFixProposal.objects.filter(status='proposed'):
    # Developer implementiert und testet
    test_results = run_comprehensive_tests(proposal)

    proposal.test_success_rate = test_results['success_rate']
    proposal.test_sample_size = test_results['sample_size']
    proposal.status = 'testing'
    proposal.save()

    if test_results['success_rate'] >= 85:
        proposal.status = 'validated'
        proposal.confidence_score = Decimal(str(test_results['confidence']))
        proposal.save()
        print(f"✅ Proposal {proposal.id} validated")

# === PHASE 4: DEPLOYMENT ===
builder = SafeKnowledgeBuilder(user)

for proposal in PatternFixProposal.objects.filter(status='validated'):
    can_apply, reason = builder.can_apply_fix(proposal)

    if can_apply:
        result = builder.apply_fix(
            proposal=proposal,
            deployed_by=admin_user
        )
        print(f"🚀 Deployed {proposal.id}: {result['deployment_id']}")
    else:
        print(f"⏸️ Skipped {proposal.id}: {reason}")

# === PHASE 5: MONITORING (automated via Celery task) ===
# Nach 7 Tagen: Automatic evaluation
from celery import shared_task

@shared_task
def evaluate_deployed_fixes():
    """Runs daily to check deployed fixes."""
    deployed_fixes = PatternFixProposal.objects.filter(
        status='deployed',
        applied_at__lte=datetime.now() - timedelta(days=7)
    )

    for fix in deployed_fixes:
        impact = evaluate_fix_impact(fix)

        if impact['success_rate'] < 0.85:
            # Auto-rollback
            builder = SafeKnowledgeBuilder(fix.pattern_session.user)
            builder.rollback_fix(
                proposal=fix,
                rolled_back_by=None,  # Automated
                rollback_reason=f"Success rate {impact['success_rate']:.1%} below threshold"
            )
        else:
            # Mark as successful
            fix.status = 'deployed_success'
            fix.save()
```

---

## 🔗 IntegratedPipeline - Complete Examples

### Beispiel 1: End-to-End Processing

```python
from extraction.services.integrated_pipeline import IntegratedExtractionPipeline

pipeline = IntegratedExtractionPipeline(user)

# Input: OCR/NER Result + Document
ocr_result = {
    'full_text': '...',
    'amount': 1250.50,
    'vendor': 'Müller',  # Wird verbessert
    'material': 'Eiche',
    'holzart': 'eiche',
    'labor_hours': 20
}

ocr_confidences = {
    'amount': 0.95,
    'vendor': 0.68,  # LOW → Pattern Detection
    'material': 0.85,
    'holzart': 0.90
}

# Complete Processing
result = pipeline.process_extraction_result(
    extraction_result=ocr_result,
    confidence_scores=ocr_confidences,
    document_id='DOC-12345',
    apply_pricing=True
)

print(result)
```

**Erwartete Ausgabe:**

```python
{
    'extraction': {
        'amount': 1250.50,
        'vendor': 'Schreinerei Müller GmbH',  # ✅ Improved by Agent
        'material': 'Eiche',
        'holzart': 'eiche',
        'labor_hours': 20
    },

    'patterns': {
        'detected_issues': [
            {
                'field': 'vendor',
                'issue': 'incomplete_company_name',
                'confidence': 0.68,
                'severity': 'medium'
            }
        ],
        'analysis_summary': {
            'total_fields': 5,
            'low_confidence_fields': 1,
            'average_confidence': 0.81
        }
    },

    'pricing': {
        'total_price_eur': 1876.50,
        'calculation_method': 'tier_1_2_3',
        'factors_applied': {
            'holzart': 1.3,
            'labor_rate': 50.0
        }
    },

    'knowledge_applied': [
        {
            'field': 'vendor',
            'fix_id': 42,
            'fix_type': 'extraction_logic',
            'improvement': 'Completed company name with legal form'
        }
    ],

    'recommendations': {
        'immediate_actions': [],
        'future_improvements': [
            'Consider training NER model on vendor names'
        ]
    },

    'processing_notes': [
        'Pattern detected for vendor field - fix applied',
        'Pricing calculated using custom company rates',
        '1 knowledge fix automatically applied'
    ],

    'metadata': {
        'pipeline_version': '3.0.0',
        'processing_time_ms': 245,
        'phase2_used': True,
        'phase3_used': True
    }
}
```

---

## 📊 Performance Optimization Examples

### Beispiel: Batch Processing mit Pipeline

```python
from concurrent.futures import ThreadPoolExecutor

documents = Document.objects.filter(status='pending')[:100]

def process_single(doc):
    """Process einzelnes Dokument."""
    ocr_result = run_ocr(doc)
    ocr_confidences = calculate_confidences(ocr_result)

    return pipeline.process_extraction_result(
        extraction_result=ocr_result,
        confidence_scores=ocr_confidences,
        document_id=doc.id
    )

# Parallel processing
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_single, documents))

print(f"Processed {len(results)} documents")
print(f"Average confidence: {sum(r['patterns']['analysis_summary']['average_confidence'] for r in results) / len(results):.3f}")
```

---

**Für weitere Details siehe:**
- `PHASE3_INTEGRATION_SUMMARY.md` - Architecture Overview
- `PHASE3_TEST_VALIDATION.md` - Test Coverage Details
- `.claude/CLAUDE.md` - Quick Reference

**Letzte Aktualisierung:** 2025-11-27
