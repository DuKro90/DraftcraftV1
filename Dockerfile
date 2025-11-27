# =============================================================================
# DRAFTCRAFTV1 - PRODUCTION DOCKERFILE
# =============================================================================
# German Handwerk Document Analysis System
# Django 5.0 | Python 3.11 | Target: Google Cloud Run
# Phase 3: Betriebskennzahlen & Integration ✅ COMPLETED
# =============================================================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# =============================================================================
# SYSTEM DEPENDENCIES
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpq5 \
    postgresql-client \
    curl \
    swig \
    pkg-config \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# PYTHON DEPENDENCIES - OpenCV/NumPy 2.x Compatibility Fix
# =============================================================================
# Problem: OpenCV 4.6.x ist inkompatibel mit NumPy 2.x
# PaddleOCR 2.7.0.3 erfordert opencv<=4.6.0.66
# OpenCV 4.6.0.66 wurde mit NumPy 1.x kompiliert → binär inkompatibel mit NumPy 2.x
#
# Lösung: Staged installation mit constraints.txt + Verification Steps
# Dokumentation: .claude/claude code docker build guide.md
# =============================================================================

# Copy requirements files
COPY backend/requirements/ /app/requirements/

# -----------------------------------------------------------------------------
# Schritt 1: NumPy mit exakter Version ZUERST installieren
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir "numpy==1.26.4" && \
    python -c "import numpy; print(f'✅ NumPy {numpy.__version__} installiert')"

# -----------------------------------------------------------------------------
# Schritt 2: OpenCV headless OHNE Dependencies (nutzt vorhandenes NumPy)
# -----------------------------------------------------------------------------
# WICHTIG: --no-deps verhindert dass pip numpy upgradet
# WICHTIG: opencv-python-headless für Cloud Run (headless, kein GUI)
RUN pip install --no-cache-dir \
    "opencv-python-headless==4.6.0.66" \
    --no-deps && \
    python -c "import cv2; print(f'✅ OpenCV {cv2.__version__} installiert')"

# -----------------------------------------------------------------------------
# Schritt 3: Verification - FAIL FAST bei falscher NumPy-Version
# -----------------------------------------------------------------------------
RUN python -c "\
import numpy as np; \
import cv2; \
assert np.__version__.startswith('1.'), f'FEHLER: NumPy {np.__version__} ist 2.x!'; \
print(f'✅ Kompatibilitäts-Check: NumPy {np.__version__}, OpenCV {cv2.__version__}')"

# -----------------------------------------------------------------------------
# Schritt 4: Base Dependencies MIT Constraint
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    -c /app/requirements/constraints.txt \
    -r /app/requirements/base.txt

# -----------------------------------------------------------------------------
# Schritt 5: Development Dependencies MIT Constraint
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    -c /app/requirements/constraints.txt \
    -r /app/requirements/development.txt

# -----------------------------------------------------------------------------
# Schritt 6: ML Dependencies MIT Constraint
# -----------------------------------------------------------------------------
# PaddleOCR wird hier mit allen Dependencies installiert
# constraints.txt stellt sicher dass numpy<2.0 bleibt
RUN pip install --no-cache-dir \
    -c /app/requirements/constraints.txt \
    -r /app/requirements/ml.txt

# -----------------------------------------------------------------------------
# Schritt 6.5: OpenCV Cleanup - Enforce Headless Version
# -----------------------------------------------------------------------------
# Problem: PaddleOCR installiert opencv-python (mit GUI)
# Lösung: Alle OpenCV-Pakete entfernen und nur headless neu installieren
RUN pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python || true && \
    pip install --no-cache-dir \
    "opencv-python-headless==4.6.0.66" \
    --no-deps && \
    python -c "import cv2; print(f'✅ OpenCV Headless Re-installed: {cv2.__version__}')"

# -----------------------------------------------------------------------------
# Schritt 7: Finale Verification nach ALLEN Installationen
# -----------------------------------------------------------------------------
# KRITISCH: Prüft ob ein Paket numpy auf 2.x geupgradet hat
RUN python -c "\
import numpy as np; \
import cv2; \
assert np.__version__.startswith('1.'), f'KRITISCH: NumPy wurde auf {np.__version__} geupgradet!'; \
print(f'✅ FINAL CHECK: NumPy {np.__version__}, OpenCV {cv2.__version__}')"

# -----------------------------------------------------------------------------
# Schritt 8: spaCy German Model
# -----------------------------------------------------------------------------
RUN python -m spacy download de_core_news_sm || echo "⚠️ spaCy model download übersprungen"

# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Copy application code
COPY backend/ /app/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# =============================================================================
# HEALTH CHECK & STARTUP
# =============================================================================

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:$PORT/health/ || exit 1

# Expose port
EXPOSE $PORT

# Run Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "config.wsgi:application"]
