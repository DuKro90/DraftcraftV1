# 🧠 Machine Learning Pipeline

**DraftcraftV1 - ML Workflow & Model Details**
**Version:** 2.3.0 | **Stand:** Dezember 2024

---

## 🎯 ML-System Übersicht

Das System nutzt **3 ML-Komponenten** in einer sequenziellen Pipeline:

```
┌──────────────────────────────────────────────────────────────┐
│                    ML PIPELINE ARCHITECTURE                   │
└──────────────────────────────────────────────────────────────┘
                              │
                              ↓
         ┌────────────────────────────────────────┐
         │   INPUT: PDF/Image (German Document)    │
         └────────────────────────────────────────┘
                              │
                              ↓
    ┌─────────────────────────────────────────────────┐
    │  STAGE 1: OCR (Computer Vision)                 │
    │  ─────────────────────────────────────          │
    │  Model: PaddleOCR 2.7 (German)                  │
    │  Task:  Image → Text + Bounding Boxes           │
    │  Output: Raw text with confidence scores        │
    └─────────────────────────────────────────────────┘
                              │
                              ↓
    ┌─────────────────────────────────────────────────┐
    │  STAGE 2: NER (Natural Language Processing)     │
    │  ────────────────────────────────────────       │
    │  Model: spaCy 3.8 de_core_news_lg + Custom      │
    │  Task:  Text → Structured Entities              │
    │  Output: Entities (Material, Dimension, etc.)   │
    └─────────────────────────────────────────────────┘
                              │
                              ↓
    ┌─────────────────────────────────────────────────┐
    │  STAGE 3: LLM Enhancement (Optional)            │
    │  ──────────────────────────────────────         │
    │  Model: Google Gemini 1.5 Flash                 │
    │  Task:  Verify/Enhance low-confidence results   │
    │  Output: Enhanced entities + explanations       │
    └─────────────────────────────────────────────────┘
                              │
                              ↓
         ┌────────────────────────────────────────┐
         │   OUTPUT: Structured Business Data      │
         │   (Ready for Calculation Engine)        │
         └────────────────────────────────────────┘
```

---

## 📸 STAGE 1: OCR Pipeline (PaddleOCR)

### Model Details

```
┌─────────────────────────────────────────────────────────────┐
│                    PADDLEOCR CONFIGURATION                   │
├─────────────────────────────────────────────────────────────┤
│  Model:        PaddleOCR 2.7.0.3                            │
│  Language:     German ('de')                                │
│  Architecture: PP-OCRv3 (Detection + Recognition)           │
│  Weights:      Pre-trained on German text corpus            │
│  Input Size:   Dynamic (auto-scaled to 960px width)         │
│  GPU Support:  Optional (CPU fallback enabled)              │
└─────────────────────────────────────────────────────────────┘
```

### Two-Stage OCR Process

```
INPUT: PDF Page / Image
  │
  ├─► STEP 1: TEXT DETECTION (Bounding Box Prediction)
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Model: DB (Differentiable Binarization)            │
  │   │  ───────────────────────────────────────            │
  │   │  Input:   Image (H×W×3, RGB)                        │
  │   │  Process: Convolutional Neural Network              │
  │   │  Output:  Bounding Boxes [(x1,y1), (x2,y2), ...]    │
  │   │                                                      │
  │   │  Algorithm Flow:                                     │
  │   │  1. Image Resizing: 960px width (preserve aspect)   │
  │   │  2. CNN Feature Extraction: ResNet-18 backbone       │
  │   │  3. Binary Segmentation: Text vs Background         │
  │   │  4. Contour Detection: Polygon approximation        │
  │   │  5. Box Filtering: Min area 10px², aspect ratio     │
  │   │                                                      │
  │   │  Performance:                                        │
  │   │  - Detection Rate: ~98% for printed text            │
  │   │  - Speed: ~0.5s per page (CPU)                      │
  │   │  - False Positives: <2% (logos, decorations)        │
  │   └─────────────────────────────────────────────────────┘
  │   Output: List of text regions with coordinates
  │
  ├─► STEP 2: TEXT RECOGNITION (Character-Level OCR)
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Model: CRNN (Convolutional RNN)                    │
  │   │  ────────────────────────────────────               │
  │   │  Input:   Cropped text regions (grayscale)          │
  │   │  Process: CNN (features) + RNN (sequence)           │
  │   │  Output:  Text string + confidence per character    │
  │   │                                                      │
  │   │  Algorithm Flow:                                     │
  │   │  FOR each bounding box:                              │
  │   │    1. Crop & Normalize: 32px height, grayscale      │
  │   │    2. CNN Encoding: VGG-like feature extraction     │
  │   │    3. RNN Decoding: LSTM layers (bidirectional)     │
  │   │    4. CTC Decoding: Sequence-to-text alignment      │
  │   │    5. Confidence: Softmax probabilities averaged    │
  │   │                                                      │
  │   │  German-Specific Optimizations:                     │
  │   │  ✓ Umlauts (ä, ö, ü, ß) in training data            │
  │   │  ✓ Number format: 1.234,56 (dot thousands)          │
  │   │  ✓ Special chars: €, °, ² (common in construction)  │
  │   │                                                      │
  │   │  Performance:                                        │
  │   │  - Character Accuracy: 96% (printed), 75% (hand)    │
  │   │  - Speed: ~1.5s per page (CPU)                      │
  │   │  - Confidence: 0.0-1.0 per word                     │
  │   └─────────────────────────────────────────────────────┘
  │   Output: Full text with word-level confidence scores
  │
  └─► AGGREGATION: Combine results
      ┌─────────────────────────────────────────────────────┐
      │  Combine Detection + Recognition                    │
      │  ────────────────────────────────                   │
      │  - Merge bounding boxes + text strings              │
      │  - Calculate overall page confidence                │
      │  - Spatial ordering (top-to-bottom, left-to-right)  │
      │  - Handle multi-column layouts                      │
      └─────────────────────────────────────────────────────┘
      Output: OCRResult(text, confidence, positions)
```

### Preprocessing Pipeline

```
Raw Image
  │
  ├─► [1] FORMAT DETECTION
  │   └─► PDF → Convert to images (pdf2image, DPI=300)
  │
  ├─► [2] IMAGE QUALITY ASSESSMENT
  │   ├─ Check resolution (min 200 DPI)
  │   ├─ Brightness histogram analysis
  │   └─ Blur detection (Laplacian variance)
  │   ↓ Low quality? → Apply preprocessing
  │
  ├─► [3] PREPROCESSING (Conditional)
  │   ┌─────────────────────────────────────────────────┐
  │   │  IF brightness < 100 OR > 200:                  │
  │   │    → Histogram equalization                     │
  │   │                                                  │
  │   │  IF blur_score < 100:                           │
  │   │    → Sharpening (Unsharp Mask)                  │
  │   │                                                  │
  │   │  IF noise detected:                             │
  │   │    → Gaussian blur (σ=0.5)                      │
  │   │                                                  │
  │   │  IF rotation != 0°:                             │
  │   │    → Deskew (Hough transform)                   │
  │   │                                                  │
  │   │  Special: Handwriting detection                 │
  │   │    → Increase contrast (+150%)                  │
  │   │    → Binarization (Otsu threshold)              │
  │   └─────────────────────────────────────────────────┘
  │
  └─► [4] FORMAT NORMALIZATION
      ├─ Resize to 960px width (preserve aspect)
      ├─ Convert to RGB (if grayscale)
      └─ Padding to 32px multiple (model requirement)
      ↓
      Ready for PaddleOCR
```

### Output Structure

```python
# ocr_service.py returns:
@dataclass
class OCRResult:
    full_text: str              # Complete extracted text
    confidence: float           # Average confidence (0.0-1.0)
    pages: List[PageResult]     # Per-page results
    processing_time: float      # Seconds

@dataclass
class PageResult:
    page_number: int
    text_boxes: List[TextBox]
    page_confidence: float

@dataclass
class TextBox:
    text: str                   # Extracted text snippet
    confidence: float           # Box-level confidence
    bbox: List[Tuple[int, int]] # [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    position: str               # "header" | "body" | "footer"
```

### Error Handling

```
OCR Failure Scenarios:
══════════════════════════════════════════════════════════════

1. EMPTY RESULT (confidence = 0.0)
   Causes: Blank page, image-only PDF
   Action: Skip page, log warning

2. LOW CONFIDENCE (< 0.70)
   Causes: Bad scan quality, handwriting, Fraktur script
   Action: Route to AGENT_EXTRACT (Gemini)

3. ENCODING ERROR
   Causes: Special characters, non-German text
   Action: Fallback encoding (UTF-8 → Windows-1252)

4. TIMEOUT (> 10s per page)
   Causes: Large image, CPU overload
   Action: Reduce resolution, retry with DPI=150

5. PADDLEOCR CRASH
   Causes: Out of memory, corrupted model
   Action: Service restart, alert admin
```

---

## 🔤 STAGE 2: NER Pipeline (spaCy)

### Model Details

```
┌─────────────────────────────────────────────────────────────┐
│                     SPACY CONFIGURATION                      │
├─────────────────────────────────────────────────────────────┤
│  Model:         de_core_news_lg (Large German)              │
│  Version:       spaCy 3.8.0                                 │
│  Training Data: German news + custom Handwerk corpus        │
│  Vocabulary:    500,000+ tokens                             │
│  Embeddings:    Word2Vec 300-dimensional                    │
│  Pipeline:      tok2vec → tagger → parser → ner             │
└─────────────────────────────────────────────────────────────┘
```

### NER Pipeline Architecture

```
INPUT: OCR Text (string)
  │
  ├─► STEP 1: TOKENIZATION
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Component: Tokenizer (German rules)                │
  │   │  ────────────────────────────────                   │
  │   │  Rules:                                              │
  │   │  - Split on whitespace + punctuation                │
  │   │  - Keep German compounds (e.g., "Eichen-Schreibtisch") │
  │   │  - Preserve units (e.g., "25 m²" → ["25", "m²"])    │
  │   │  - Handle currency (e.g., "1.234,56 €")             │
  │   │                                                      │
  │   │  Example:                                            │
  │   │  Input:  "Tisch aus Eiche, 1,5 m², geölt"           │
  │   │  Output: ["Tisch", "aus", "Eiche", ",",             │
  │   │           "1,5", "m²", ",", "geölt"]                │
  │   └─────────────────────────────────────────────────────┘
  │
  ├─► STEP 2: PART-OF-SPEECH TAGGING
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Component: Tagger (Morphology)                     │
  │   │  ───────────────────────────────                    │
  │   │  Tags: NOUN, VERB, ADJ, NUM, etc. (German tagset)   │
  │   │                                                      │
  │   │  Example:                                            │
  │   │  "Eiche" → NOUN (Nominativ, Feminin, Singular)      │
  │   │  "geölt" → ADJ (past participle)                    │
  │   │  "1,5"   → NUM (cardinal)                           │
  │   └─────────────────────────────────────────────────────┘
  │
  ├─► STEP 3: DEPENDENCY PARSING
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Component: Parser (Syntax tree)                    │
  │   │  ────────────────────────────────                   │
  │   │  Builds grammatical relationships:                  │
  │   │  - Subject → Verb → Object                          │
  │   │  - Adjective → Noun                                 │
  │   │  - Number → Unit                                    │
  │   │                                                      │
  │   │  Example Tree:                                       │
  │   │  Tisch ← ROOT                                       │
  │   │    ├── aus ← prep                                   │
  │   │    │   └── Eiche ← pobj (Material!)                 │
  │   │    └── geölt ← amod (Surface!)                      │
  │   └─────────────────────────────────────────────────────┘
  │
  ├─► STEP 4: NAMED ENTITY RECOGNITION
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Component: NER (Custom labels)                     │
  │   │  ──────────────────────────────                     │
  │   │  Base Model: Transformer-based (BERT-like)          │
  │   │  Training: Pre-trained + fine-tuned                 │
  │   │                                                      │
  │   │  Entity Labels (Custom for Handwerk):               │
  │   │  ────────────────────────────────────────           │
  │   │  MATERIAL      - Holzarten, Metalle, Stoffe         │
  │   │  DIMENSION     - Maße (m², lfm, Stk, kg)            │
  │   │  MONEY         - Preise (€, USD)                    │
  │   │  DATE          - Termine (DD.MM.YYYY)               │
  │   │  QUANTITY      - Mengen (Stückzahl)                 │
  │   │  SURFACE       - Oberflächenbehandlung              │
  │   │  COMPLEXITY    - Verarbeitungs-Indikatoren          │
  │   │                                                      │
  │   │  Recognition Algorithm:                             │
  │   │  1. Token embeddings (tok2vec)                      │
  │   │  2. BiLSTM encoding (context)                       │
  │   │  3. CRF decoding (BIO tagging)                      │
  │   │     B-MATERIAL (Begin), I-MATERIAL (Inside)         │
  │   │  4. Confidence: Softmax probabilities               │
  │   │                                                      │
  │   │  Example Output:                                     │
  │   │  "Eiche"    → MATERIAL (conf: 0.94)                 │
  │   │  "1,5 m²"   → DIMENSION (conf: 0.98)                │
  │   │  "geölt"    → SURFACE (conf: 0.89)                  │
  │   └─────────────────────────────────────────────────────┘
  │
  ├─► STEP 5: RELATION EXTRACTION
  │   ┌─────────────────────────────────────────────────────┐
  │   │  Custom Logic (Rule-based + ML)                     │
  │   │  ────────────────────────────────                   │
  │   │  Links entities via dependency tree:                │
  │   │                                                      │
  │   │  IF MATERIAL ← prep → QUANTITY:                     │
  │   │    → Link: "Eiche" + "1,5 m²"                       │
  │   │                                                      │
  │   │  IF SURFACE ← amod → MATERIAL:                      │
  │   │    → Link: "geölt" applies to "Eiche"               │
  │   │                                                      │
  │   │  Output: Entity Graph                               │
  │   │  {                                                   │
  │   │    "material": "Eiche",                             │
  │   │    "dimension": "1,5 m²",                           │
  │   │    "surface": "geölt"                               │
  │   │  }                                                   │
  │   └─────────────────────────────────────────────────────┘
  │
  └─► STEP 6: POST-PROCESSING
      ┌─────────────────────────────────────────────────────┐
      │  Normalization & Validation                         │
      │  ──────────────────────────────                     │
      │  - Number parsing: "1,5" → Decimal(1.5)             │
      │  - Unit standardization: "qm" → "m²"                │
      │  - Material lookup: "Eiche" → MaterialList check    │
      │  - Confidence aggregation: avg(entity_scores)       │
      │  - Duplicate removal                                │
      └─────────────────────────────────────────────────────┘
      Output: List[Entity] + overall_confidence
```

### Custom Training Data

```
Training Corpus for German Handwerk:
════════════════════════════════════════════════════════════

Source 1: Annotated Real Documents (500+ samples)
  ├─ Collected from beta testers
  ├─ Manually labeled entities
  └─ Example annotations in IOB format:
      "Tisch O
       aus   O
       Eiche B-MATERIAL
       ,     O
       1,5   B-DIMENSION
       m²    I-DIMENSION"

Source 2: Synthetic Data Generation (10,000+ samples)
  ├─ Templates: "{MATERIAL} Tisch, {DIMENSION}, {SURFACE}"
  ├─ Variables from TIER 1 data
  └─ Augmentation: Synonyms, word order variations

Fine-Tuning Process:
  1. Load de_core_news_lg (base model)
  2. Add custom entity labels
  3. Train NER component (10 epochs)
  4. Validation split: 80% train / 20% test
  5. Metrics: F1 score > 0.90 (target)
```

### Performance Metrics

```
NER Evaluation (Test Set: 100 documents):
══════════════════════════════════════════════════════════════

Entity Type      Precision  Recall  F1-Score  Samples
────────────────────────────────────────────────────────────
MATERIAL         0.96       0.93    0.94      150
DIMENSION        0.98       0.97    0.97      200
MONEY            0.99       0.98    0.98      180
SURFACE          0.91       0.87    0.89      80
COMPLEXITY       0.88       0.83    0.85      60
DATE             0.95       0.94    0.94      120
QUANTITY         0.97       0.96    0.96      140
────────────────────────────────────────────────────────────
OVERALL          0.95       0.93    0.94      930
```

---

## 🤖 STAGE 3: LLM Enhancement (Gemini)

### When LLM is Used

```
Confidence-Based Routing:
══════════════════════════════════════════════════════════════

Confidence Score    Action              LLM Task
────────────────────────────────────────────────────────────
≥ 0.92              AUTO_ACCEPT         None (skip LLM)
0.80 - 0.92         AGENT_VERIFY        Verify entities
0.70 - 0.80         AGENT_EXTRACT       Re-extract entities
< 0.70              HUMAN_REVIEW        None (manual)
```

### Model Configuration

```
┌─────────────────────────────────────────────────────────────┐
│                    GEMINI CONFIGURATION                      │
├─────────────────────────────────────────────────────────────┤
│  Model:           gemini-1.5-flash                          │
│  Version:         Latest (API auto-updates)                 │
│  Context Window:  1M tokens (massive)                       │
│  Temperature:     0.1 (deterministic, low creativity)       │
│  Top-P:           0.95                                      │
│  Max Tokens:      2,048 (typical response: 200-500)         │
│  Safety Settings: BLOCK_MEDIUM_AND_ABOVE (German laws)      │
└─────────────────────────────────────────────────────────────┘
```

### Prompt Engineering

```
System Prompt Template:
══════════════════════════════════════════════════════════════

Du bist ein Experte für deutsches Handwerk, spezialisiert auf
Schreiner-, Zimmerer- und Polsterer-Arbeiten.

Deine Aufgabe: {TASK}

KONTEXT:
- Kunde: {CUSTOMER_NAME} (Historie: {PREVIOUS_PROJECTS})
- Aktuelles Projekt: {PROJECT_TYPE}
- Bisherige Extraktion (OCR+NER):
  {EXTRACTED_ENTITIES}

TIER-DATEN (Verfügbare Materialien/Oberflächen):
{TIER1_DATA}

BEISPIELE (Ähnliche Projekte):
{MEMORY_CONTEXT}

AUFGABE:
{SPECIFIC_INSTRUCTION}

AUSGABE-FORMAT (JSON):
{
  "entities": [
    {"type": "MATERIAL", "value": "...", "confidence": 0.0-1.0},
    ...
  ],
  "explanation": "Begründung für Entscheidung",
  "changes": ["Was wurde korrigiert"]
}
```

### Task-Specific Prompts

```
AGENT_VERIFY (Confidence 0.80-0.92):
════════════════════════════════════════════════════════════

AUFGABE:
Überprüfe die extrahierten Entitäten auf Plausibilität.

SPEZIFISCHE CHECKS:
1. Material: Ist "Eiche" eine valide Holzart? (Check TIER 1)
2. Dimension: Ist "150 m²" realistisch für einen Tisch? (Plausibilitäts-Check)
3. Oberfläche: Passt "geölt" zu "Eiche"? (Domain Knowledge)

OUTPUT:
- verified: true/false (pro Entity)
- explanation: Warum akzeptiert/abgelehnt
- suggested_corrections: Falls Fehler erkannt

───────────────────────────────────────────────────────────

AGENT_EXTRACT (Confidence 0.70-0.80):
════════════════════════════════════════════════════════════

AUFGABE:
Extrahiere alle relevanten Informationen NEU aus dem Originaltext.

ORIGINALTEXT (OCR):
{FULL_OCR_TEXT}

BISHERIGE EXTRAKTION (Unsicher):
{LOW_CONFIDENCE_ENTITIES}

OUTPUT:
- entities: Vollständige neue Extraktion
- comparison: Was unterscheidet sich zur OCR/NER-Extraktion?
- reasoning: Warum ist deine Extraktion besser?
```

### Memory Context Integration

```
Memory Retrieval Process:
══════════════════════════════════════════════════════════════

1. SHORT-TERM MEMORY (Redis)
   Query: Last 100 documents, same customer
   Purpose: Recent patterns, customer preferences
   Example: "Kunde Meier bestellt immer Buche statt Eiche"

2. LONG-TERM MEMORY (PostgreSQL)
   Query: Similar projects (K-NN, k=5)
   Similarity: Material + Dimension + Project Type
   Purpose: Historical pricing, common combinations
   Example: "Eichen-Tische 1-2 m² meist mit Öl-Finish"

3. CONTEXT ASSEMBLY
   Limit: 10,000 tokens (avoid overwhelming LLM)
   Format: Structured JSON with most relevant projects
   Sorting: By similarity score (cosine distance)

Example Context JSON:
{
  "recent_by_customer": [
    {"project": "Buche-Tisch", "date": "2024-11-15", "material": "Buche"}
  ],
  "similar_projects": [
    {"project": "Eichen-Schreibtisch", "dim": "1.8 m²", "surface": "geölt"},
    ...
  ],
  "tier1_materials": ["Eiche", "Buche", "Kiefer", ...]
}
```

### Cost Tracking

```
Cost Calculation per Request:
══════════════════════════════════════════════════════════════

Gemini 1.5 Flash Pricing (as of Dec 2024):
  Input:  $0.000075 per 1K tokens
  Output: $0.000300 per 1K tokens

Typical Request:
  Prompt:   ~1,500 tokens (system + context + task)
  Response: ~400 tokens (entities + explanation)

  Cost = (1.5 × $0.000075) + (0.4 × $0.000300)
       = $0.0001125 + $0.00012
       = $0.0002325 (~$0.00023)

Daily Budget: $10
Max Requests: $10 / $0.00023 ≈ 43,000 requests/day

Actual Usage (Phase 3 stats):
  Average: 50-80 requests/day
  Cost: $0.012-0.018/day
  Budget headroom: 99.8%
```

### Error Handling

```
LLM Failure Scenarios:
══════════════════════════════════════════════════════════════

1. API TIMEOUT (> 10s)
   Fallback: Retry once with shorter context
   Ultimate: Route to HUMAN_REVIEW

2. INVALID JSON RESPONSE
   Action: Parse with error recovery (extract partial JSON)
   Fallback: Use OCR/NER result as-is

3. SAFETY FILTER TRIGGERED
   Cause: Document contains sensitive content
   Action: Log warning, route to HUMAN_REVIEW

4. QUOTA EXCEEDED
   Daily budget spent → Disable Gemini for 24h
   All requests routed to HUMAN_REVIEW
   Email alert to admin

5. HALLUCINATION DETECTION
   Check: Are entities in TIER 1 data?
   If new material appears → Flag for review
   Confidence penalty: -20%
```

---

## 🔄 Pipeline Integration & Data Flow

### Full ML Pipeline Execution

```python
# Simplified code showing data flow
# File: extraction/services/integrated_pipeline.py

class IntegratedPipeline:
    def process_document(self, document_id: str) -> PipelineResult:
        doc = Document.objects.get(id=document_id)

        # STAGE 1: OCR
        ocr_service = GermanHandwerkOCRService()
        ocr_result = ocr_service.process_pdf(doc.file_path)
        # → OCRResult(text, confidence=0.85, processing_time=2.3s)

        # STAGE 2: NER
        ner_service = GermanHandwerkNERService()
        entities = ner_service.extract_entities(ocr_result.full_text)
        # → [Entity(text="Eiche", label="MATERIAL", conf=0.92), ...]

        # Calculate overall confidence
        overall_conf = (ocr_result.confidence * 0.4 +
                        avg(entities.confidence) * 0.6)
        # → 0.88 (OCR 85% × 0.4 + NER 90% × 0.6)

        # STAGE 3: Confidence-based routing
        router = ConfidenceRouter()
        decision = router.route(overall_conf)
        # → RoutingDecision(tier=AGENT_VERIFY, cost=0.00023)

        if decision.tier in [AGENT_VERIFY, AGENT_EXTRACT]:
            # Retrieve memory context
            memory_service = MemoryService()
            context = memory_service.retrieve_context(doc)
            # → List of similar projects + TIER 1 data

            # Call Gemini
            gemini_service = GeminiAgentService()
            enhanced = gemini_service.enhance_extraction(
                entities=entities,
                context=context,
                task=decision.tier
            )
            # → EnhancedEntities + explanation

            # Update entities with LLM results
            entities = enhanced.entities
            overall_conf = enhanced.confidence

        # Store results
        extraction_result = ExtractionResult.objects.create(
            document=doc,
            ocr_text=ocr_result.full_text,
            ocr_confidence=ocr_result.confidence,
            entities=entities,
            overall_confidence=overall_conf,
            routing_decision=decision.tier,
            gemini_enhanced=(decision.tier != AUTO_ACCEPT)
        )

        # Proceed to calculation if confidence high enough
        if overall_conf >= 0.80:
            calc_engine = CalculationEngine()
            price_result = calc_engine.calculate_price(entities)
            # → CalculationResult(price=1268.29, breakdown={...})

        return PipelineResult(
            extraction=extraction_result,
            calculation=price_result
        )
```

### Performance Breakdown

```
Pipeline Stage Performance (Average):
══════════════════════════════════════════════════════════════

Stage                Time      Bottleneck           Optimization
──────────────────────────────────────────────────────────────
PDF → Images         0.5s      IO + ImageMagick     Cache converted images
OCR (PaddleOCR)      2.0s      CPU (CNN inference)  Use GPU / batch processing
NER (spaCy)          0.3s      CPU (transformer)    Model quantization
Confidence Routing   0.05s     None                 -
Gemini API           2-4s      Network latency      Async batch requests
Calculation          0.1s      DB queries (TIER)    Cache TIER data
──────────────────────────────────────────────────────────────
TOTAL (no Gemini)    3.0s      OCR dominates
TOTAL (with Gemini)  5.5s      OCR + Gemini
```

### ML Model Updates & Versioning

```
Model Lifecycle:
══════════════════════════════════════════════════════════════

PaddleOCR:
  Current: 2.7.0.3 (German models)
  Update frequency: 6-12 months (manual)
  Trigger: New PaddlePaddle release with German improvements
  Process: Test on validation set → Compare accuracy → Deploy

spaCy NER:
  Current: de_core_news_lg 3.8 + custom fine-tuning
  Update frequency: 3 months (custom) / 6 months (base model)
  Trigger:
    - Custom: Accumulated 500+ new training samples
    - Base: New spaCy major version
  Process:
    1. Collect corrections from HUMAN_REVIEW
    2. Re-annotate in IOB format
    3. Fine-tune NER component
    4. Validate on test set (F1 > 0.90 required)
    5. A/B test in staging (1 week)
    6. Deploy to production

Gemini:
  Current: gemini-1.5-flash (API, auto-updated by Google)
  Update frequency: Continuous (Google manages)
  Version control: None (API abstraction)
  Monitoring: Track response quality, cost per request
```

---

## 📊 ML Evaluation & Monitoring

### Key Metrics

```
Metrics Dashboard (Real-time):
══════════════════════════════════════════════════════════════

OCR Metrics:
  - Avg Confidence: 0.87 (Target: >0.85)
  - Processing Time: 2.1s/page (Target: <3s)
  - Error Rate: 1.2% (blank results, crashes)

NER Metrics:
  - Entity Recall: 0.93 (found 93% of entities)
  - Entity Precision: 0.95 (95% of found entities correct)
  - F1 Score: 0.94 (harmonic mean)
  - Confidence Distribution:
      0.9-1.0: 78% (high confidence)
      0.8-0.9: 15% (medium)
      <0.8:    7%  (low, routed to Gemini)

Gemini Metrics:
  - Usage Rate: 12% of documents (0.80-0.92 confidence)
  - Improvement: +8% average confidence boost
  - Cost per Enhanced Doc: $0.00023
  - Daily Cost: $0.015 (Budget: $10)

End-to-End Metrics:
  - Documents without correction: 89% (Target: >85%)
  - Avg processing time: 3.2s (Target: <5s)
  - User satisfaction: 4.7/5.0
```

### A/B Testing Framework

```
Testing New Models:
══════════════════════════════════════════════════════════════

Scenario: New spaCy NER model with improved SURFACE detection

1. BASELINE (7 days)
   Model: Current production model
   Traffic: 100%
   Collect: Entity accuracy, confidence scores

2. CANARY DEPLOYMENT (7 days)
   Model A (control): Current (90% traffic)
   Model B (test): New model (10% traffic)
   Compare: F1 score, processing time, user corrections

3. RAMP-UP (7 days)
   If Model B better: 50/50 split
   Monitor: No regressions in other entity types

4. FULL ROLLOUT
   If all metrics improved: 100% Model B
   Rollback trigger: F1 drops >2% OR processing time >1.5×
```

---

**Nächste Datei:** `KNOWLEDGE_INTEGRATION.md` - Detaillierte Erklärung des TIER 1/2/3 Systems.
