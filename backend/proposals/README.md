# Proposals Module

Proposal generation, editing, and PDF/email export.

## Status: ✅ COMPLETE

Fully implemented with:

- **Proposal** model - Main proposal document with status tracking
- **ProposalLine** model - Individual line items with pricing
- **ProposalTemplate** model - Pricing configuration (hourly rate, margins)
- **ProposalCalculationLog** model - Audit trail for pricing decisions
- **ProposalService** - 3-layer pricing engine with German formatting
- **ProposalPdfService** - Professional PDF generation (ReportLab)
- **ProposalEmailService** - Email delivery with attachments

## Architecture

Service layer pattern with models as data only:
- `ProposalService` - Business logic for proposal generation
- `ProposalPdfService` - PDF generation with German formatting
- `ProposalEmailService` - SMTP integration

## Features

✅ 3-layer pricing calculation (manufacturing + company + dynamic)
✅ German currency formatting (€ with comma decimals)
✅ PDF export with professional styling
✅ Email sending with attachments
✅ Calculation audit trail
✅ Customer information management
✅ Full REST API integration
✅ 10+ test cases

## Tests

```bash
pytest tests/test_pdf_service.py -v  # PDF generation
pytest tests/test_api_views.py::TestProposalAPI -v  # Proposal endpoints
```
