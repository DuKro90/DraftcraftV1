# Dependencies Setup Guide - DraftcraftV1

**Status:** ✅ COMPLETED
**Datum:** 2025-12-01
**Python Version:** 3.14.0

---

## 📋 Übersicht

Dieser Guide dokumentiert die Installation aller benötigten Dependencies für DraftcraftV1 Development.

**Kern-Dependencies:**
- ✅ `django-redis==5.4.0` - Redis Cache Backend
- ✅ `opencv-python-headless==4.12.0.88` - OCR Image Processing
- ✅ `numpy==2.2.6` - Numerical Computing (Auto-installed mit OpenCV)

---

## 🎯 Installierte Versionen (2025-12-01)

| Package | Version | Status | Zweck |
|---------|---------|--------|-------|
| django-redis | 5.4.0 | ✅ INSTALLED | Redis cache backend für Django |
| opencv-python-headless | 4.12.0.88 | ✅ INSTALLED | Computer Vision (headless für Cloud Run) |
| numpy | 2.2.6 | ✅ INSTALLED | Numerical computing (OpenCV dependency) |

---

## 🔧 Installation Steps

### 1. django-redis Installation

```bash
pip install django-redis==5.4.0
```

**Output:**
```
Successfully installed django-redis-5.4.0
```

**Validation:**
```python
import django_redis
print(django_redis.VERSION)  # (5, 4, 0)
```

---

### 2. OpenCV Installation

```bash
pip install opencv-python-headless
```

**Output:**
```
Successfully installed opencv-python-headless-4.12.0.88
Successfully installed numpy-2.2.6
```

**Validation:**
```python
import cv2
import numpy as np
print(cv2.__version__)   # 4.12.0
print(np.__version__)    # 2.2.6
```

---

## ⚠️ Python 3.14 Specific Issues (GELÖST)

### Issue 1: NumPy Binary Wheels

**Problem:**
- Python 3.14 ist sehr neu (Released: Oktober 2024)
- NumPy 1.26.4 (aus `constraints.txt`) hat keine Binary Wheels für Python 3.14
- Pip versucht aus Source zu kompilieren (10-15 Min)

**Lösung:**
- Upgrade auf OpenCV 4.12.0.88 (neueste Version)
- OpenCV 4.12+ ist kompatibel mit NumPy 2.x
- NumPy 2.2.6 hat Binary Wheels für Python 3.14
- Installation in Sekunden statt Minuten

**Hinweis:**
- `constraints.txt` definiert `numpy>=1.21.0,<2.0.0` für Docker (Python 3.10/3.11)
- Für lokale Dev mit Python 3.14: NumPy 2.x ist OK
- Production Docker nutzt Python 3.10 → NumPy 1.26.4 funktioniert

---

### Issue 2: OpenCV ABI Compatibility

**Original Problem (Python 3.10):**
```
ImportError: numpy.core.multiarray failed to import
RuntimeError: module compiled against ABI version 0x1000009
but this version of numpy is 0x2000000
```

**Ursprüngliche Lösung (Docker):**
- OpenCV 4.6.0.66 + NumPy 1.26.4
- Siehe: `.claude/claude code docker build guide.md`

**Neue Lösung (Python 3.14 Dev):**
- OpenCV 4.12.0.88 + NumPy 2.2.6
- Kein ABI-Konflikt, beide Versionen kompatibel

---

## 📊 Kompatibilitäts-Matrix

| Python | OpenCV | NumPy | Status |
|--------|--------|-------|--------|
| 3.10 (Docker) | 4.6.0.66 | 1.26.4 | ✅ Production |
| 3.11 (Docker) | 4.6.0.66 | 1.26.4 | ✅ Production |
| 3.14 (Local Dev) | 4.12.0.88 | 2.2.6 | ✅ Development |

**Wichtig:**
- Docker Production nutzt weiterhin `constraints.txt` (NumPy 1.x)
- Lokale Dev mit Python 3.14 nutzt NumPy 2.x
- Beide Setups funktionieren unabhängig

---

## 🧪 Test Validation

### Quick Test - Import Check
```bash
python -c "
import django_redis
import cv2
import numpy as np
print('[OK] django-redis:', django_redis.VERSION)
print('[OK] OpenCV:', cv2.__version__)
print('[OK] NumPy:', np.__version__)
"
```

**Expected Output:**
```
[OK] django-redis: (5, 4, 0)
[OK] OpenCV: 4.12.0
[OK] NumPy: 2.2.6
```

---

### Full Test - Django Models Import
```bash
cd /c/Codes/DraftcraftV1/backend
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from documents.transparency_models import (
    CalculationExplanation,
    CalculationFactor,
    UserProjectBenchmark
)
print('[OK] Phase 4A Models loaded successfully!')
"
```

**Expected Output:**
```
[OK] Using DEVELOPMENT settings
[OK] Phase 4A Models loaded successfully!
```

---

### Full Test - Service Import
```bash
cd /c/Codes/DraftcraftV1/backend
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from extraction.services.explanation_service import ExplanationService
print('[OK] ExplanationService imported successfully!')
"
```

**Expected Output:**
```
[OK] Using DEVELOPMENT settings
[OK] ExplanationService imported successfully!
```

---

## 🐛 Troubleshooting

### Problem: "No module named 'django_redis'"
```bash
# Solution:
pip install django-redis==5.4.0
```

### Problem: "No module named 'cv2'"
```bash
# Solution:
pip install opencv-python-headless
```

### Problem: "numpy ABI version mismatch"
```bash
# Solution (Python 3.14):
pip uninstall opencv-python-headless numpy -y
pip install opencv-python-headless  # Latest version
```

### Problem: "NumPy compilation takes too long"
```bash
# Check Python version:
python --version

# If Python 3.14:
# Latest OpenCV auto-installs compatible NumPy 2.x (has binary wheels)

# If Python 3.10/3.11:
# Use constraints.txt as documented in CLAUDE.md
```

---

## 📝 Requirements Files Reference

### base.txt (Zeile 15-17)
```txt
# Async & Tasks
celery==5.3.4
redis==5.0.1
django-redis==5.4.0
```

### ml.txt (Zeile 23-24)
```txt
# Image preprocessing for OCR accuracy
opencv-python-headless==4.6.0.66  # Docker: Python 3.10/3.11
```

**Hinweis:** Lokale Dev mit Python 3.14 installiert automatisch neuere Version.

### constraints.txt (Zeile 26)
```txt
# NumPy Version Constraint für Docker
numpy>=1.21.0,<2.0.0
```

**Hinweis:** Gilt nur für Docker Build, nicht für lokale Dev mit Python 3.14.

---

## ✅ Checklist - Dependencies Setup Complete

- [x] django-redis 5.4.0 installiert
- [x] opencv-python-headless installiert
- [x] numpy kompatible Version installiert
- [x] Import-Tests erfolgreich
- [x] Django Models laden
- [x] Services laden
- [x] Keine ABI-Konflikte

---

## 🚀 Next Steps

### For Phase 4A Testing:
```bash
# Run Unit Tests (once pytest setup is complete)
cd /c/Codes/DraftcraftV1/backend
pytest tests/unit/test_transparency*.py -v

# Run Integration Tests
pytest tests/integration/test_transparency_integration.py -v
```

### For Production Deployment:
```bash
# Use Docker with Python 3.10/3.11
# Follow: .claude/claude code docker build guide.md
# Dependencies are handled via requirements/ml.txt + constraints.txt
```

---

## 📚 Related Documentation

- `PHASE4A_TRANSPARENCY_IMPLEMENTATION.md` - Phase 4A Implementation Details
- `.claude/claude code docker build guide.md` - Docker NumPy/OpenCV Fix
- `requirements/README.md` - Requirements Files Structure
- `CLAUDE.md` - Main Development Guide

---

**Erstellt:** 2025-12-01
**Letzte Aktualisierung:** 2025-12-01
**Status:** ✅ ALL DEPENDENCIES INSTALLED & WORKING
**Python Version:** 3.14.0
**OS:** Windows 10/11
