# 🏗️ System-Architektur & Logik

**DraftcraftV1 - Technical Architecture Overview**
**Version:** 2.3.0 | **Stand:** Dezember 2024

---

## 🎯 Architektur-Übersicht

Das System folgt einer **3-Layer Service-Architektur** mit klarer Trennung von Verantwortlichkeiten:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  Django Admin · REST API (planned) · Web Interface (planned)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────────┐
│                         BUSINESS LOGIC LAYER                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Extraction  │  │  Calculation │  │  Self-Learn  │         │
│  │   Services   │  │   Services   │  │   Services   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                              │
│  PostgreSQL (Supabase) · Redis (Memory) · File Storage (GCS)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Haupt-Datenfluss: Dokument → Angebot

### End-to-End Pipeline

```
INPUT: PDF/Image Upload
  │
  ├─► [1] DOCUMENT INGESTION
  │   ┌────────────────────────────────────────────────┐
  │   │ Django View: DocumentUploadView                │
  │   │ ├─► Validierung (Format, Größe, MIME-Type)    │
  │   │ ├─► Virus-Scan (optional)                      │
  │   │ ├─► Storage: Cloud Storage (GCS)               │
  │   │ └─► Model: Document.objects.create()           │
  │   └────────────────────────────────────────────────┘
  │   Output: Document ID + File Path
  │
  ├─► [2] INTEGRATED PIPELINE START
  │   ┌────────────────────────────────────────────────┐
  │   │ Service: IntegratedPipeline.process_document() │
  │   │ ├─► Orchestriert alle Sub-Services             │
  │   │ ├─► Error Handling & Retries                   │
  │   │ └─► Status Updates (via Django Signals)        │
  │   └────────────────────────────────────────────────┘
  │
  ├─► [3] OCR EXTRACTION
  │   ┌────────────────────────────────────────────────┐
  │   │ Service: GermanHandwerkOCRService              │
  │   │ ├─► PDF → Images (pdf2image)                   │
  │   │ ├─► Image Preprocessing                        │
  │   │ │   ├─► Contrast Enhancement                   │
  │   │ │   ├─► Noise Reduction                        │
  │   │ │   └─► Rotation Correction                    │
  │   │ ├─► PaddleOCR.ocr(lang='german')               │
  │   │ │   ├─► Text Detection (Bounding Boxes)        │
  │   │ │   ├─► Text Recognition (Character-Level)     │
  │   │ │   └─► Confidence Scores                      │
  │   │ └─► Output: Structured Text + Positions        │
  │   └────────────────────────────────────────────────┘
  │   Output: OCRResult(text, confidence, positions)
  │   Time: 2-3 seconds/page
  │
  ├─► [4] NER EXTRACTION
  │   ┌────────────────────────────────────────────────┐
  │   │ Service: GermanHandwerkNERService              │
  │   │ ├─► spaCy Pipeline: de_core_news_lg            │
  │   │ ├─► Custom Entity Recognition                  │
  │   │ │   ├─► MATERIAL (Holzarten, Metalle)          │
  │   │ │   ├─► DIMENSION (m², lfm, Stk)               │
  │   │ │   ├─► MONEY (Preise, Beträge)                │
  │   │ │   ├─► SURFACE (Öl, Lack, Wachs)              │
  │   │ │   └─► COMPLEXITY (Gefräst, Geschnitzt)       │
  │   │ ├─► Relation Extraction (Entity Linking)       │
  │   │ └─► Confidence Aggregation                     │
  │   └────────────────────────────────────────────────┘
  │   Output: List[Entity(text, label, confidence)]
  │   Time: 0.3-0.5 seconds
  │
  ├─► [5] CONFIDENCE ROUTING
  │   ┌────────────────────────────────────────────────┐
  │   │ Service: ConfidenceRouter                      │
  │   │ ├─► Calculate Overall Confidence               │
  │   │ │   └─► Weighted: OCR (40%) + NER (60%)        │
  │   │ ├─► Routing Decision:                          │
  │   │ │   ├─► ≥0.92: AUTO_ACCEPT                     │
  │   │ │   ├─► 0.80-0.92: AGENT_VERIFY                │
  │   │ │   ├─► 0.70-0.80: AGENT_EXTRACT               │
  │   │ │   └─► <0.70: HUMAN_REVIEW                    │
  │   │ └─► Cost Estimation                            │
  │   └────────────────────────────────────────────────┘
  │   Output: RoutingDecision(tier, estimated_cost)
  │
  ├─► [6a] GEMINI AGENT (if needed)
  │   ┌────────────────────────────────────────────────┐
  │   │ Service: GeminiAgentService                    │
  │   │ ├─► Memory Context Retrieval                   │
  │   │ │   ├─► Redis: Recent 100 docs (TTL 24h)       │
  │   │ │   └─► PostgreSQL: Similar projects           │
  │   │ ├─► Prompt Construction                        │
  │   │ │   ├─► System: "Du bist Experte für Handwerk" │
  │   │ │   ├─► Context: Memory + TIER data            │
  │   │ │   └─► Task: Verify/Extract entities          │
  │   │ ├─► Gemini 1.5 Flash API Call                  │
  │   │ │   └─► Temperature: 0.1 (low creativity)      │
  │   │ ├─► Response Parsing & Validation              │
  │   │ └─► Cost Tracking (per token)                  │
  │   └────────────────────────────────────────────────┘
  │   Output: EnhancedEntities + Explanation
  │   Time: 2-5 seconds
  │   Cost: ~$0.0001-0.00025
  │
  ├─► [6b] HUMAN REVIEW (if confidence < 0.70)
  │   ┌────────────────────────────────────────────────┐
  │   │ Django Admin: Review Interface                 │
  │   │ ├─► Side-by-side: Original + Extracted         │
  │   │ ├─► Confidence Highlights (Red/Yellow/Green)   │
  │   │ ├─► Correction Form with Context               │
  │   │ └─► Save → Becomes Training Data               │
  │   └────────────────────────────────────────────────┘
  │   Output: VerifiedEntities
  │   Time: 2-5 minutes (manual)
  │
  ├─► [7] CALCULATION ENGINE
  │   ┌────────────────────────────────────────────────┐
  │   │ Service: CalculationEngine.calculate_price()   │
  │   │                                                 │
  │   │ Step 1: Base Price                             │
  │   │   └─► Material Price × Dimension               │
  │   │                                                 │
  │   │ Step 2: Material Factor (TIER 1)               │
  │   │   └─► Query: MaterialList.get(name=entity)     │
  │   │                                                 │
  │   │ Step 3: Complexity Factor (TIER 1)             │
  │   │   └─► Query: ComplexityFactor.filter()         │
  │   │                                                 │
  │   │ Step 4: Surface Factor (TIER 1)                │
  │   │   └─► Query: SurfaceFinish.get()               │
  │   │                                                 │
  │   │ Step 5: Labor Cost (TIER 2)                    │
  │   │   └─► Hours × CompanyMetrics.labor_rate        │
  │   │                                                 │
  │   │ Step 6: Overhead (TIER 2)                      │
  │   │   └─► Subtotal × CompanyMetrics.overhead_rate  │
  │   │                                                 │
  │   │ Step 7: Margin (TIER 2)                        │
  │   │   └─► Subtotal × CompanyMetrics.margin_rate    │
  │   │                                                 │
  │   │ Step 8: Dynamic Adjustments (TIER 3)           │
  │   │   └─► Apply active PricingRules                │
  │   │                                                 │
  │   └─► Output: DetailedCalculation + Breakdown      │
  │   └────────────────────────────────────────────────┘
  │   Output: CalculationResult(price, breakdown, factors)
  │   Time: <0.5 seconds
  │
  ├─► [8] EXPLANATION GENERATION
  │   ┌────────────────────────────────────────────────┐
  │   │ Service: ExplanationService                    │
  │   │ ├─► Convert Calculation → Human-Readable       │
  │   │ ├─► Fetch Benchmarks (similar projects)        │
  │   │ ├─► Generate Markdown Report                   │
  │   │ └─► Store: CalculationExplanation.create()     │
  │   └────────────────────────────────────────────────┘
  │   Output: Explanation (Markdown) + Benchmarks
  │
  └─► [9] OUTPUT GENERATION
      ┌────────────────────────────────────────────────┐
      │ Django View: AngebotDetailView                 │
      │ ├─► Render Template (PDF/HTML)                 │
      │ ├─► Include: Price + Breakdown + Explanation   │
      │ └─► Export Options (Email, Download)           │
      └────────────────────────────────────────────────┘
      Output: PDF/HTML Angebot ready for customer

TOTAL TIME: 5-15 seconds (depending on routing)
```

---

## 🧩 Service Layer Details

### 1. Extraction Services

```
┌─────────────────────────────────────────────────────────┐
│              extraction/services/                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ocr_service.py                                         │
│  ├─ Class: GermanHandwerkOCRService                     │
│  ├─ Dependencies: PaddleOCR, PIL, pdf2image             │
│  ├─ Key Methods:                                        │
│  │  ├─ process_pdf(file_path) → OCRResult              │
│  │  ├─ preprocess_image(img) → Image                   │
│  │  └─ extract_text_with_positions() → List[TextBox]   │
│  └─ State: Stateless (can be singleton)                │
│                                                          │
│  ner_service.py                                         │
│  ├─ Class: GermanHandwerkNERService                     │
│  ├─ Dependencies: spaCy (de_core_news_lg)               │
│  ├─ Key Methods:                                        │
│  │  ├─ extract_entities(text) → List[Entity]           │
│  │  ├─ link_relations(entities) → Graph                │
│  │  └─ calculate_confidence() → float                  │
│  └─ State: Model loaded once (singleton pattern)       │
│                                                          │
│  gemini_agent_service.py                                │
│  ├─ Class: GeminiAgentService                           │
│  ├─ Dependencies: google.generativeai, MemoryService    │
│  ├─ Key Methods:                                        │
│  │  ├─ verify_extraction() → VerificationResult        │
│  │  ├─ enhance_extraction() → EnhancedEntities         │
│  │  └─ track_cost(tokens) → None                       │
│  └─ State: API client + cost tracker                   │
│                                                          │
│  memory_service.py                                      │
│  ├─ Class: MemoryService                                │
│  ├─ Dependencies: Redis, Django ORM                     │
│  ├─ Key Methods:                                        │
│  │  ├─ store_short_term(doc) → None (Redis TTL 24h)    │
│  │  ├─ store_long_term(doc) → None (PostgreSQL)        │
│  │  ├─ retrieve_context(query) → List[Doc]             │
│  │  └─ cleanup_expired() → int                         │
│  └─ State: Redis connection pool                       │
│                                                          │
│  confidence_router.py                                   │
│  ├─ Class: ConfidenceRouter                             │
│  ├─ Dependencies: None (pure logic)                     │
│  ├─ Key Methods:                                        │
│  │  ├─ route(confidence) → RoutingDecision             │
│  │  ├─ estimate_cost(tier) → Decimal                   │
│  │  └─ check_budget() → bool                           │
│  └─ State: Stateless                                   │
│                                                          │
│  integrated_pipeline.py                                 │
│  ├─ Class: IntegratedPipeline                           │
│  ├─ Dependencies: All above services                    │
│  ├─ Key Methods:                                        │
│  │  ├─ process_document(doc_id) → PipelineResult       │
│  │  ├─ handle_error(exception) → ErrorResponse         │
│  │  └─ emit_status_update(status) → None               │
│  └─ State: Orchestrator (injects dependencies)         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2. Calculation Services

```
┌─────────────────────────────────────────────────────────┐
│         extraction/services/calculation_engine.py        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Class: CalculationEngine                               │
│  ├─ Dependencies: Django Models (TIER 1/2/3)            │
│  ├─ Key Methods:                                        │
│  │  ├─ calculate_price(entities) → Calculation         │
│  │  │   └─ 8-step process (see above)                  │
│  │  │                                                   │
│  │  ├─ _get_base_price(material, dim) → Decimal        │
│  │  │   └─ Query MaterialList                          │
│  │  │                                                   │
│  │  ├─ _apply_material_factor() → Decimal              │
│  │  ├─ _apply_complexity_factor() → Decimal            │
│  │  ├─ _apply_surface_factor() → Decimal               │
│  │  │   └─ All query TIER 1 models                     │
│  │  │                                                   │
│  │  ├─ _calculate_labor() → Decimal                    │
│  │  ├─ _calculate_overhead() → Decimal                 │
│  │  ├─ _calculate_margin() → Decimal                   │
│  │  │   └─ All query TIER 2: CompanyMetrics            │
│  │  │                                                   │
│  │  ├─ _apply_dynamic_rules() → Decimal                │
│  │  │   └─ Query TIER 3: PricingRule (active only)     │
│  │  │                                                   │
│  │  └─ get_breakdown() → Dict[str, Decimal]            │
│  │      └─ Detailed step-by-step prices                │
│  │                                                      │
│  └─ State: Caches TIER data (invalidated on update)    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3. Self-Learning Services

```
┌─────────────────────────────────────────────────────────┐
│       extraction/services/pattern_analyzer.py            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Class: PatternAnalyzer                                 │
│  ├─ Dependencies: Django Models (ExtractionPattern)     │
│  ├─ Key Methods:                                        │
│  │  ├─ analyze_failures() → List[Pattern]              │
│  │  │   ├─ Query failed extractions (last 7 days)      │
│  │  │   ├─ Group by error signature                    │
│  │  │   ├─ Calculate frequency (>5 = pattern)          │
│  │  │   └─ Identify root cause                         │
│  │  │                                                   │
│  │  ├─ categorize_pattern() → PatternType              │
│  │  │   └─ OCR_FAILURE | NER_MISS | CALC_ERROR         │
│  │  │                                                   │
│  │  └─ suggest_fix() → FixSuggestion                   │
│  │      ├─ OCR → Preprocessing adjustment              │
│  │      ├─ NER → Training data addition                │
│  │      └─ CALC → TIER data missing                    │
│  │                                                      │
│  └─ Scheduled: Daily cron job                          │
│                                                          │
├─────────────────────────────────────────────────────────┤
│       extraction/services/knowledge_builder.py           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Class: SafeKnowledgeBuilder                            │
│  ├─ Dependencies: PatternAnalyzer, Django Models        │
│  ├─ Key Methods:                                        │
│  │  ├─ generate_fix(pattern) → KnowledgeFix            │
│  │  │   ├─ Analyze pattern details                     │
│  │  │   ├─ Generate code/config change                 │
│  │  │   ├─ Create test plan                            │
│  │  │   └─ Store as DRAFT                              │
│  │  │                                                   │
│  │  ├─ deploy_to_staging(fix_id) → FixDeployment       │
│  │  │   ├─ Apply fix to staging env                    │
│  │  │   ├─ Run test suite                              │
│  │  │   ├─ Monitor for 24h                             │
│  │  │   └─ Update status: STAGING_ACTIVE               │
│  │  │                                                   │
│  │  ├─ promote_to_production(fix_id) → bool            │
│  │  │   ├─ Check staging metrics (success rate >85%)   │
│  │  │   ├─ Admin approval required                     │
│  │  │   ├─ Deploy to production                        │
│  │  │   └─ Enable monitoring                           │
│  │  │                                                   │
│  │  └─ rollback(fix_id) → bool                         │
│  │      ├─ Triggered if error rate >20%                │
│  │      ├─ Revert code changes                         │
│  │      └─ Update status: ROLLED_BACK                  │
│  │                                                      │
│  └─ Safety: Automatic rollback + manual approval       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4. Transparency Services

```
┌─────────────────────────────────────────────────────────┐
│      extraction/services/explanation_service.py          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Class: ExplanationService                              │
│  ├─ Dependencies: CalculationEngine, Django Models      │
│  ├─ Key Methods:                                        │
│  │  ├─ generate_explanation(calc) → Explanation        │
│  │  │   ├─ Convert breakdown to Markdown               │
│  │  │   ├─ Add human-readable reasons                  │
│  │  │   ├─ Include TIER data sources                   │
│  │  │   └─ Store: CalculationExplanation               │
│  │  │                                                   │
│  │  ├─ fetch_benchmarks(project) → Benchmarks          │
│  │  │   ├─ Find similar projects (K-NN, k=5)           │
│  │  │   ├─ Calculate percentiles (P25, P50, P75)       │
│  │  │   ├─ Compare current price                       │
│  │  │   └─ Store: UserProjectBenchmark                 │
│  │  │                                                   │
│  │  └─ format_for_user(expl, benchmark) → Markdown     │
│  │      └─ Template: Material → Process → Cost → Result│
│  │                                                      │
│  └─ Output: Human-friendly, transparent explanations   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🗄️ Data Models & Relationships

### Core Domain Models

```
┌─────────────────────────────────────────────────────────────┐
│                     documents/models.py                      │
└─────────────────────────────────────────────────────────────┘

Document (Core)
├─ id: UUID (primary key)
├─ uploaded_at: DateTime
├─ file_path: String (GCS URL)
├─ status: Enum (PENDING, PROCESSING, COMPLETED, FAILED)
├─ created_by: ForeignKey(User)
└─ Relations:
   ├─ extraction_results (1:Many) → ExtractionResult
   ├─ calculations (1:Many) → Calculation
   └─ explanations (1:Many) → CalculationExplanation

MaterialList (TIER 1)
├─ name: String (e.g., "Eiche massiv")
├─ category: String (e.g., "Hartholz")
├─ factor: Decimal (e.g., 1.3)
├─ base_price: Decimal (€/m²)
├─ properties: JSONField (Härte, Farbe, etc.)
└─ is_active: Boolean

ComplexityFactor (TIER 1)
├─ name: String (e.g., "Gefräst")
├─ description: Text
├─ factor: Decimal (e.g., 1.15)
├─ required_skill: String (e.g., "CNC-Fräse")
└─ is_active: Boolean

SurfaceFinish (TIER 1)
├─ name: String (e.g., "Geölt")
├─ process_steps: Text
├─ factor: Decimal (e.g., 1.1)
├─ durability_years: Integer
└─ is_active: Boolean

CompanyMetrics (TIER 2)
├─ company: ForeignKey(Company)
├─ labor_rate_journeyman: Decimal (€/h)
├─ labor_rate_master: Decimal (€/h)
├─ overhead_rate: Decimal (0.25 = 25%)
├─ margin_rate: Decimal (0.20 = 20%)
├─ valid_from: Date
└─ valid_until: Date (nullable)

PricingRule (TIER 3)
├─ name: String (e.g., "Winter-Rabatt")
├─ rule_type: Enum (DISCOUNT, SURCHARGE, CUSTOM)
├─ adjustment: Decimal (-0.05 = -5%)
├─ conditions: JSONField (date_range, customer, etc.)
├─ priority: Integer (higher = applied first)
├─ is_active: Boolean
└─ valid_until: Date

CalculationExplanation (Transparency)
├─ calculation: OneToOne(Calculation)
├─ explanation_markdown: Text
├─ factor_sources: JSONField (which TIER data was used)
├─ generated_at: DateTime
└─ version: Integer (for A/B testing)

UserProjectBenchmark (Transparency)
├─ user: ForeignKey(User)
├─ project_type: String
├─ avg_price_per_m2: Decimal
├─ percentile_25: Decimal
├─ percentile_50: Decimal
├─ percentile_75: Decimal
├─ sample_size: Integer
└─ calculated_at: DateTime
```

### Extraction & Learning Models

```
┌─────────────────────────────────────────────────────────────┐
│                   extraction/models.py                       │
└─────────────────────────────────────────────────────────────┘

ExtractionResult
├─ document: ForeignKey(Document)
├─ ocr_text: Text
├─ ocr_confidence: Decimal
├─ entities: JSONField (List[Entity])
├─ overall_confidence: Decimal
├─ routing_decision: Enum (AUTO_ACCEPT, AGENT_VERIFY, etc.)
├─ gemini_enhanced: Boolean
├─ human_verified: Boolean
├─ corrections: JSONField (if manually corrected)
├─ processing_time: Decimal (seconds)
└─ created_at: DateTime

ExtractionPattern
├─ pattern_type: Enum (OCR_FAILURE, NER_MISS, CALC_ERROR)
├─ error_signature: String (unique identifier)
├─ frequency: Integer (count of occurrences)
├─ root_cause: Text (analysis result)
├─ sample_documents: ManyToMany(Document)
├─ detected_at: DateTime
├─ status: Enum (NEW, UNDER_REVIEW, FIX_CREATED)
└─ priority: Integer (based on frequency + impact)

KnowledgeFix
├─ pattern: ForeignKey(ExtractionPattern)
├─ fix_type: Enum (OCR_PREPROCESSING, NER_TRAINING, TIER_DATA, RULE)
├─ description: Text
├─ code_changes: Text (diff or JSON config)
├─ test_plan: Text
├─ status: Enum (DRAFT, STAGING, PRODUCTION, ROLLED_BACK)
├─ created_at: DateTime
├─ approved_by: ForeignKey(User, nullable)
└─ Relations:
   └─ deployments (1:Many) → FixDeployment

FixDeployment
├─ fix: ForeignKey(KnowledgeFix)
├─ environment: Enum (STAGING, PRODUCTION)
├─ deployed_at: DateTime
├─ metrics: JSONField (success_rate, error_rate, performance)
├─ status: Enum (ACTIVE, MONITORING, FAILED, ROLLED_BACK)
└─ rollback_at: DateTime (nullable)
```

### Database Relationships Diagram

```
┌─────────────┐         ┌──────────────────┐
│  Document   │────1:N──│ ExtractionResult │
└─────────────┘         └──────────────────┘
      │                          │
      │                          ├── References: MaterialList (TIER 1)
      │                          ├── References: ComplexityFactor (TIER 1)
      │                          └── References: SurfaceFinish (TIER 1)
      │
      ├────1:N──► Calculation
      │              │
      │              ├── Uses: CompanyMetrics (TIER 2)
      │              ├── Applies: PricingRule (TIER 3)
      │              │
      │              └────1:1──► CalculationExplanation
      │
      └────M:N──► ExtractionPattern
                     │
                     └────1:N──► KnowledgeFix
                                    │
                                    └────1:N──► FixDeployment
```

---

## 🔒 Security & Compliance Architecture

### DSGVO-konformes Design

```
┌─────────────────────────────────────────────────────────────┐
│                    DSGVO COMPLIANCE LAYER                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DATA ENCRYPTION                                         │
│     ├─ At Rest: PostgreSQL column-level (sensitive fields)  │
│     ├─ In Transit: TLS 1.3 for all connections              │
│     └─ Storage: GCS with Customer-Managed Encryption Keys   │
│                                                              │
│  2. ACCESS CONTROL                                          │
│     ├─ Row-Level Security (RLS) in Supabase                 │
│     ├─ Django Permissions (per-model, per-object)           │
│     └─ Audit Logging (who accessed what, when)              │
│                                                              │
│  3. DATA RETENTION                                          │
│     ├─ Documents: Auto-delete after retention_until date    │
│     ├─ ExtractionResults: Anonymize PII after 90 days       │
│     └─ Audit Logs: Keep 2 years (legal requirement)         │
│                                                              │
│  4. DATA PORTABILITY (Art. 20 DSGVO)                        │
│     ├─ Export API: All user data as JSON                    │
│     └─ Format: Machine-readable, structured                 │
│                                                              │
│  5. RIGHT TO BE FORGOTTEN (Art. 17 DSGVO)                   │
│     ├─ Hard Delete: Cascade to all related records          │
│     ├─ Anonymization: For statistical data                  │
│     └─ Verification: Checksum to ensure complete deletion   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Authentication & Authorization Flow

```
User Request
  │
  ├─► [1] AUTHENTICATION
  │   ├─ Django Session (Web)
  │   ├─ JWT Token (API) - planned
  │   └─ Fail → 401 Unauthorized
  │
  ├─► [2] AUTHORIZATION
  │   ├─ Check Django Permissions
  │   │   ├─ Model-level: can_view_document
  │   │   └─ Object-level: owns_document
  │   ├─ Check RLS Policies (Supabase)
  │   │   └─ user_id matches row owner
  │   └─ Fail → 403 Forbidden
  │
  ├─► [3] RATE LIMITING
  │   ├─ Redis-based throttle
  │   ├─ Limits: 100 req/min per user
  │   └─ Fail → 429 Too Many Requests
  │
  └─► [4] AUDIT LOG
      ├─ Log: user, action, timestamp, IP
      └─ Store: Separate audit table
```

---

## 🚀 Performance & Scalability

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                      CACHE LAYERS                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LAYER 1: Application Memory (Process-Local)                │
│  ├─ What: spaCy NER model, TIER 1 data                      │
│  ├─ Invalidation: On TIER data update (Django signals)      │
│  └─ Benefit: <1ms access time                               │
│                                                              │
│  LAYER 2: Redis (Shared Cache)                              │
│  ├─ What: Short-term memory, session data                   │
│  ├─ TTL: 24 hours (memory), 1 hour (sessions)               │
│  └─ Benefit: Fast cross-process sharing                     │
│                                                              │
│  LAYER 3: PostgreSQL (Persistent)                           │
│  ├─ What: All TIER data, extraction results                 │
│  ├─ Indexing: B-tree on frequently queried fields           │
│  └─ Benefit: Reliable, ACID-compliant                       │
│                                                              │
│  LAYER 4: CDN (Static Assets) - planned                     │
│  ├─ What: PDF exports, images                               │
│  └─ Benefit: Global low-latency delivery                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Async Processing Architecture

```
Synchronous Request (< 5s response time)
  │
  ├─► Document Upload
  ├─► TIER Data CRUD
  └─► Calculation (if entities already extracted)

Asynchronous Processing (background jobs)
  │
  ├─► [1] Document Analysis (OCR + NER)
  │   ├─ Trigger: On Document.status = PENDING
  │   ├─ Queue: Cloud Tasks (GCP) / Celery (local)
  │   └─ Notification: Django Signals → WebSocket (planned)
  │
  ├─► [2] Pattern Analysis (daily)
  │   ├─ Trigger: Cron (00:00 UTC)
  │   ├─ Duration: 5-10 minutes
  │   └─ Output: New patterns detected → email to admins
  │
  ├─► [3] Knowledge Fix Deployment
  │   ├─ Trigger: Admin approval
  │   ├─ Stages: Staging (24h) → Production
  │   └─ Monitoring: Auto-rollback on failure
  │
  └─► [4] Data Retention Cleanup
      ├─ Trigger: Daily cron
      └─ Action: Delete expired documents, anonymize PII
```

### Scalability Targets

```
Current (Development):        Target (Production):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Users: 1-5                   Users: 100-500 concurrent
Docs/day: 10-50              Docs/day: 3,000-5,000
Response time: <5s           Response time: <3s (P95)
Database: 500MB              Database: 50GB-100GB
Storage: 1GB                 Storage: 500GB-1TB
Uptime: 95%                  Uptime: 99.5% SLA
```

---

## 🔧 Configuration Management

### Environment-Specific Settings

```
settings/
├─ base.py          (Shared across all environments)
├─ development.py   (Local development)
├─ staging.py       (Pre-production testing)
└─ production.py    (Live system)

Key Differences:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Setting              Development    Staging      Production
────────────────────────────────────────────────────────────
DEBUG                True           False        False
DATABASE             SQLite/Local   Supabase     Cloud SQL
ALLOWED_HOSTS        localhost      staging.*    draftcraft.*
GEMINI_API_ENABLED   Optional       True         True
COST_LIMIT           $1/day         $5/day       $50/day
CACHE_BACKEND        Dummy          Redis        Redis
STORAGE              Local FS       GCS (test)   GCS (prod)
LOGGING_LEVEL        DEBUG          INFO         WARNING
```

### Secrets Management

```
Local Development:
  └─ .env file (gitignored)

Production (GCP):
  └─ Secret Manager
     ├─ DATABASE_URL
     ├─ GEMINI_API_KEY
     ├─ REDIS_URL
     └─ DJANGO_SECRET_KEY

Access Pattern:
  settings.py → os.getenv() → Secret Manager API
  ├─ Cached for 1 hour (reduce API calls)
  └─ Auto-rotated every 90 days
```

---

## 📊 Monitoring & Observability

### Key Metrics

```
Application Metrics (tracked in real-time):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Metric                          Alert Threshold    Action
────────────────────────────────────────────────────────────
OCR Confidence (avg)            < 0.80             Investigate
NER Success Rate                < 0.90             Retrain model
Gemini API Cost (daily)         > $45              Throttle
Document Processing Time        > 10s (P95)        Scale up
Error Rate                      > 5%               Page on-call
Pattern Detection Frequency     > 10/day           Review fixes
Fix Deployment Success          < 85%              Rollback
```

### Logging Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                      LOG LEVELS                              │
├─────────────────────────────────────────────────────────────┤
│  DEBUG:   Development only (verbose service calls)           │
│  INFO:    Normal operations (document processed)             │
│  WARNING: Degraded performance (Gemini fallback used)        │
│  ERROR:   Failed operations (OCR crashed)                    │
│  CRITICAL: System-wide failure (database down)               │
└─────────────────────────────────────────────────────────────┘

Log Destinations:
  Development → Console (colorized)
  Production  → Cloud Logging (GCP) + Sentry (errors)

Retention:
  INFO logs: 30 days
  ERROR logs: 90 days
  CRITICAL logs: 1 year
```

---

## 🔄 Deployment Pipeline

### CI/CD Flow

```
Git Push (main branch)
  │
  ├─► [1] AUTOMATED TESTS
  │   ├─ Linting: Black, Flake8, mypy
  │   ├─ Unit Tests: pytest (169+ tests)
  │   ├─ Integration Tests: Database + Services
  │   └─ Coverage Check: >80% required
  │   ↓ PASS → Continue
  │   ↓ FAIL → Block deployment
  │
  ├─► [2] BUILD
  │   ├─ Docker Build (multi-stage)
  │   ├─ Run Security Scan (Trivy)
  │   └─ Push to Container Registry
  │
  ├─► [3] DEPLOY TO STAGING
  │   ├─ Cloud Run (Staging)
  │   ├─ Smoke Tests (health check)
  │   └─ Manual approval required
  │
  └─► [4] DEPLOY TO PRODUCTION
      ├─ Cloud Run (Production)
      ├─ Blue-Green Deployment
      ├─ Gradual Traffic Shift (10% → 50% → 100%)
      ├─ Monitor for 30 minutes
      └─ Auto-rollback on errors
```

---

**Nächste Schritte:** Siehe `ML_PIPELINE.md` für detaillierte ML-Workflow-Beschreibung.
