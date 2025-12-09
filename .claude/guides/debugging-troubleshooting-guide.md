# Debugging & Troubleshooting - Advanced Guide

**Version:** 1.0.0
**Letzte Aktualisierung:** November 27, 2025

---

## 📋 Wann dieses Dokument nutzen?

**Verwende dieses Dokument für:**
- Komplexe Debugging-Szenarien
- Production Issues die nicht in Quick-Ref sind
- Performance Deep-Dives
- Memory/Database Issues

**Für häufige Probleme siehe:** `.claude/CLAUDE.md` (OCR Quality, GAEB Encoding, Performance)

---

## 🔍 Advanced OCR Issues

### Problem: Fraktur-Schrift in historischen Dokumenten

**Symptom:** OCR confidence <0.5 für alte Rechnungen/Dokumente

**Root Cause:** PaddleOCR deutsche Modelle sind für moderne Schriften optimiert

**Lösung:**

```python
from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

def preprocess_fraktur_document(image_path: str) -> np.ndarray:
    """
    Spezielles Preprocessing für Fraktur/alte Schriften.
    """
    img = Image.open(image_path).convert('L')  # Grayscale

    # 1. Contrast Enhancement (stärker als normal)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(3.0)  # Stark erhöhen

    # 2. Sharpening für verblasste Tinte
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)  # 2x

    # 3. Binarization mit adaptivem Threshold
    img_array = np.array(img)
    from skimage.filters import threshold_local
    block_size = 35
    binary = img_array > threshold_local(img_array, block_size, offset=10)
    img_array = (binary * 255).astype(np.uint8)

    # 4. Noise Removal
    from scipy.ndimage import median_filter
    img_array = median_filter(img_array, size=2)

    return img_array

# OCR mit speziellem Config
ocr = PaddleOCR(
    lang='german',
    use_gpu=False,
    det_algorithm='DB++',  # Besserer Detector
    rec_algorithm='SVTR_LCNet',  # Besserer Recognizer
    use_space_char=True,
    use_angle_cls=True,  # Rotation detection
    enable_mkldnn=True
)

# Processing
preprocessed = preprocess_fraktur_document('old_invoice.jpg')
result = ocr.ocr(preprocessed)
```

### Problem: Multi-Column Layout Confusion

**Symptom:** OCR liest Spalten durcheinander (z.B. Menge + Preis vertauscht)

**Lösung:**

```python
def extract_with_layout_analysis(image_path: str):
    """
    OCR mit Layout-Awareness für tabellarische Dokumente.
    """
    from paddleocr import PPStructure
    import cv2

    # Use PP-Structure für Layout Analysis
    table_engine = PPStructure(
        lang='german',
        layout=True,  # Layout-Detection aktiviert
        table=True,   # Tabellen-Erkennung
        ocr=True,
        show_log=False
    )

    img = cv2.imread(image_path)
    result = table_engine(img)

    # Parse Tabellen
    tables = [r for r in result if r['type'] == 'table']

    structured_data = []
    for table in tables:
        # Extrahiere Zeilen/Spalten
        cells = table['res']['cells']

        # Group by row
        rows = {}
        for cell in cells:
            row_idx = cell['row']
            if row_idx not in rows:
                rows[row_idx] = []
            rows[row_idx].append(cell)

        # Sort columns by x-coordinate
        for row_idx in rows:
            rows[row_idx].sort(key=lambda c: c['bbox'][0])  # Sort by x

        structured_data.append({
            'table_bbox': table['bbox'],
            'rows': rows
        })

    return structured_data
```

---

## 💾 Database Performance Issues

### Problem: Slow queries bei großen ExtractionResult Mengen

**Symptom:** `/api/extractions/` Endpoint >5 Sekunden

**Diagnosis:**

```python
# Check Query Performance
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    extractions = ExtractionResult.objects.filter(user=user).select_related('document')[:100]
    list(extractions)  # Force evaluation

    print(f"Queries executed: {len(connection.queries)}")
    for q in connection.queries[-10:]:
        print(f"Time: {q['time']}s - {q['sql'][:100]}")
```

**Lösung: Indexes & Query Optimization**

```python
# 1. Add Migration for Indexes
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('documents', '0005_pattern_analysis_support')]

    operations = [
        migrations.AddIndex(
            model_name='extractionresult',
            index=models.Index(
                fields=['user', '-created_at'],
                name='extract_user_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='extractionresult',
            index=models.Index(
                fields=['user', 'status', '-created_at'],
                name='extract_user_status_idx'
            ),
        ),
    ]

# 2. Optimize Queryset
def get_recent_extractions(user, limit=100):
    """Optimized query with prefetch."""
    return ExtractionResult.objects.filter(
        user=user
    ).select_related(
        'document'  # 1:1 join
    ).prefetch_related(
        'patterns__fix_proposals'  # M2M joins
    ).only(  # Nur benötigte Felder
        'id', 'created_at', 'status',
        'document__filename', 'document__upload_date'
    ).order_by('-created_at')[:limit]
```

### Problem: Memory Issues bei Batch Processing

**Symptom:** Docker Container OOM killed bei >50 Dokumente parallel

**Lösung: Chunk Processing + Garbage Collection**

```python
import gc
from django.db import transaction

def process_documents_chunked(document_ids, chunk_size=10):
    """
    Process documents in chunks to avoid memory overflow.
    """
    total = len(document_ids)
    processed = 0

    for i in range(0, total, chunk_size):
        chunk_ids = document_ids[i:i+chunk_size]

        # Process chunk in transaction
        with transaction.atomic():
            documents = Document.objects.filter(id__in=chunk_ids)

            for doc in documents:
                try:
                    result = process_single_document(doc)
                    result.save()
                except Exception as e:
                    logger.error(f"Failed {doc.id}: {e}")

        processed += len(chunk_ids)
        logger.info(f"Processed {processed}/{total}")

        # Explicit cleanup
        gc.collect()

        # Give system time to breathe
        import time
        time.sleep(0.5)

    return processed
```

---

## 🚀 Performance Profiling

### Profile OCR Service

```python
import cProfile
import pstats
from io import StringIO

def profile_ocr_service():
    """Profile OCR performance."""
    profiler = cProfile.Profile()

    profiler.enable()
    # Your OCR code
    result = ocr_service.process_pdf('test.pdf')
    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    print(s.getvalue())

# Identify bottlenecks
# Typical output:
#   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
#      1    0.050    0.050    2.450    2.450 ocr_service.py:45(process_pdf)
#      5    1.200    0.240    1.800    0.360 paddleocr.py:234(ocr)
#     50    0.500    0.010    0.600    0.012 image_processing.py:12(preprocess)
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def process_large_document(doc_id):
    """Memory profile dieser Funktion."""
    doc = Document.objects.get(id=doc_id)
    images = convert_pdf_to_images(doc.file.path)  # ← Potentieller Memory Hog
    results = [ocr.ocr(img) for img in images]
    return combine_results(results)

# Run with: python -m memory_profiler script.py
# Output zeigt Line-by-Line Memory Usage:
# Line #    Mem usage    Increment  Occurrences   Line Contents
# =============================================================
#     12     50.0 MiB     50.0 MiB           1   doc = Document.objects.get(id=doc_id)
#     13    250.5 MiB    200.5 MiB           1   images = convert_pdf_to_images(...)  ← Problem!
#     14    280.0 MiB     29.5 MiB          10   results = [ocr.ocr(img) for img in images]
```

---

## 🔐 Redis Connection Issues

### Problem: Redis timeout in production

**Symptom:** `ConnectionError: Error while reading from socket` in MemoryService

**Diagnosis:**

```bash
# Check Redis connection
redis-cli ping
# → PONG (OK)

# Check connection pool
redis-cli INFO clients
# → connected_clients:127
# → blocked_clients:0

# Check memory
redis-cli INFO memory
# → used_memory_human:512.50M
# → maxmemory_human:1.00G  ← Prüfen ob zu wenig!
```

**Lösung: Connection Pool & Timeouts**

```python
# config/settings/base.py

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,  # Seconds
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'health_check_interval': 30,
            },
            'REDIS_CLIENT_KWARGS': {
                'socket_keepalive': True,
                'socket_keepalive_options': {
                    1: 1,   # TCP_KEEPIDLE
                    2: 1,   # TCP_KEEPINTVL
                    3: 3,   # TCP_KEEPCNT
                }
            }
        },
        'KEY_PREFIX': 'handwerk',
        'VERSION': 1,
    }
}

# Graceful Fallback in MemoryService
def store_pattern(self, pattern_type, pattern_data, ttl_hours=1):
    """Store with fallback if Redis unavailable."""
    try:
        cache.set(key, value, timeout=ttl_hours * 3600)
        return True
    except RedisError as e:
        logger.warning(f"Redis unavailable: {e}. Falling back to DB.")
        # Fallback: Store in DocumentMemory model
        DocumentMemory.objects.create(
            user=self.user,
            pattern_type=pattern_type,
            pattern_data=pattern_data
        )
        return True
```

---

## 🧮 Calculation Engine Edge Cases

### Problem: Decimal precision errors in pricing

**Symptom:** Totals don't match breakdown (e.g. 1250.49 vs 1250.50)

**Root Cause:** Float arithmetic statt Decimal

**Lösung:**

```python
from decimal import Decimal, ROUND_HALF_UP

def safe_decimal_multiply(a, b, decimal_places=2):
    """Safe multiplication mit korrekte Rundung."""
    result = Decimal(str(a)) * Decimal(str(b))
    return result.quantize(
        Decimal('0.01') if decimal_places == 2 else Decimal(f'0.{"0" * decimal_places}'),
        rounding=ROUND_HALF_UP
    )

# Beispiel
labor = Decimal('18')
rate = Decimal('50.00')
factor = Decimal('1.15')  # Komplexität

# ❌ FALSCH
total_wrong = float(labor) * float(rate) * float(factor)
# → 1034.9999999999998

# ✅ RICHTIG
base = labor * rate
total_correct = safe_decimal_multiply(base, factor, decimal_places=2)
# → Decimal('1035.00')
```

### Problem: Division by Zero bei Custom Materials

**Symptom:** `ZeroDivisionError` wenn material_quantity = 0

**Lösung: Validation Layer**

```python
class CalculationEngine:
    def _validate_input_data(self, extracted_data: Dict) -> List[str]:
        """Validate input vor Berechnung."""
        errors = []

        # Required fields
        if 'labor_hours' not in extracted_data:
            errors.append("Missing required field: labor_hours")

        # Positive values
        if extracted_data.get('labor_hours', 0) <= 0:
            errors.append("labor_hours must be > 0")

        if extracted_data.get('material_quantity', 0) <= 0:
            errors.append("material_quantity must be > 0")

        # Valid enums
        valid_holzarten = ['eiche', 'buche', 'kiefer', 'fichte', ...]
        if extracted_data.get('holzart') not in valid_holzarten:
            errors.append(f"Invalid holzart: {extracted_data.get('holzart')}")

        return errors

    def calculate_project_price(self, extracted_data, **kwargs):
        """Entry point mit Validation."""
        errors = self._validate_input_data(extracted_data)

        if errors:
            raise ValidationError(f"Invalid input: {', '.join(errors)}")

        # Proceed with calculation
        return self._calculate_internal(extracted_data, **kwargs)
```

---

## 🧪 Test Debugging

### Problem: Tests pass lokal, fail in CI/CD

**Diagnosis:**

```python
# Check Environment differences
import sys
import platform

def print_test_environment():
    """Debug environment info."""
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Django: {django.get_version()}")

    # Check installed packages
    import pkg_resources
    installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    critical_packages = ['paddleocr', 'opencv-python-headless', 'numpy', 'spacy']

    for pkg in critical_packages:
        print(f"{pkg}: {installed.get(pkg, 'NOT INSTALLED')}")

    # Check database
    from django.db import connection
    print(f"Database: {connection.settings_dict['ENGINE']}")

# Add to test setup
@pytest.fixture(scope='session', autouse=True)
def log_test_environment():
    print_test_environment()
```

**Common Fixes:**

```python
# 1. Timezone Issues
from django.utils import timezone
import pytz

# ❌ FALSCH (timezone-naive)
now = datetime.now()

# ✅ RICHTIG (timezone-aware)
now = timezone.now()

# 2. Ordering Issues (non-deterministic)
# ❌ FALSCH
results = Model.objects.all()[:10]

# ✅ RICHTIG
results = Model.objects.all().order_by('id')[:10]

# 3. Mock leaks zwischen Tests
@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    from unittest.mock import patch
    patch.stopall()
```

---

## 📡 API Rate Limiting Issues

### Problem: Gemini API "429 Too Many Requests"

**Lösung: Exponential Backoff**

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    """Decorator für API calls mit exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt == max_retries - 1:
                        raise

                    delay = base_delay * (2 ** attempt)  # Exponential
                    logger.warning(f"Rate limited. Retrying in {delay}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)

            raise Exception(f"Failed after {max_retries} retries")
        return wrapper
    return decorator

# Usage
class GeminiAgentService:
    @retry_with_backoff(max_retries=3, base_delay=2)
    def _call_gemini_api(self, prompt: str):
        """API call mit automatic retry."""
        response = self.model.generate_content(prompt)
        return response.text
```

---

## 🔧 Django Admin Performance

### Problem: Admin list view langsam bei 10k+ Objekten

**Lösung: Optimized Admin**

```python
from django.contrib import admin

class OptimizedExtractionResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'document_filename', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('document__filename', 'user__username')
    date_hierarchy = 'created_at'

    # Performance Optimizations
    list_select_related = ('user', 'document')  # Reduce queries
    list_per_page = 50  # Pagination
    show_full_result_count = False  # Don't COUNT(*)

    def document_filename(self, obj):
        """Avoid N+1 query durch select_related."""
        return obj.document.filename if obj.document else '-'

    def get_queryset(self, request):
        """Optimize base queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'document').only(
            'id', 'user__username', 'document__filename',
            'created_at', 'status'
        )
```

---

## 🔍 Logging Best Practices

### Structured Logging für Production Debugging

```python
import logging
import json

class StructuredLogger:
    """Structured logging für besseres Debugging."""

    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def log_extraction(self, document_id, duration, success, **kwargs):
        """Log extraction mit context."""
        log_data = {
            'event': 'extraction',
            'document_id': document_id,
            'duration_ms': duration,
            'success': success,
            **kwargs
        }
        self.logger.info(json.dumps(log_data))

    def log_error(self, error, context=None):
        """Log error mit full context."""
        log_data = {
            'event': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        self.logger.error(json.dumps(log_data), exc_info=True)

# Usage
logger = StructuredLogger(__name__)

try:
    start = time.time()
    result = process_document(doc)
    duration = (time.time() - start) * 1000
    logger.log_extraction(
        document_id=doc.id,
        duration=duration,
        success=True,
        confidence=result.confidence
    )
except Exception as e:
    logger.log_error(e, context={'document_id': doc.id})
```

---

**Für Quick-Reference siehe:** `.claude/CLAUDE.md`
**Letzte Aktualisierung:** 2025-11-27
