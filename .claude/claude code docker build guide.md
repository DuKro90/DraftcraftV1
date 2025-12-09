# Claude Code Implementierungsleitfaden
# Docker OpenCV/NumPy Dependency Fix

**Projekt:** DraftcraftV1 - German Handwerk Document Analysis  
**Django:** 5.0 | **Python:** 3.11 | **Target:** Google Cloud Run  
**Erstellt:** 2025-11-27

---

## ⚠️ KRITISCHE REGELN

```
1. NIEMALS Features deaktivieren oder optional machen um Probleme zu umgehen
2. NIEMALS OCR-Funktionalität entfernen - es ist Core-Feature
3. IMMER Root Cause fixen, keine Workarounds
4. VOR Änderungen an funktionierendem Code: User fragen und Trade-offs erklären
5. ALLE 169+ Tests müssen nach Fix weiterhin bestehen
6. Target-Umgebung ist Google Cloud Run (headless, kein GUI)
```

---

## 📋 Aufgabenübersicht

### Ziel
Docker Container soll starten mit:
- OpenCV 4.6.0.66 (headless)
- NumPy 1.x (NICHT 2.x)
- PaddleOCR 2.7.0.3 funktionsfähig
- Alle Tests grün

### Das Problem
```
PaddleOCR 2.7.0.3 → opencv<=4.6.0.66 → numpy<2.0
ABER: pip installiert numpy 2.x → ImportError: numpy.core.multiarray
```

---

## 🔧 IMPLEMENTIERUNG

### Phase 1: Constraints File erstellen

**Datei:** `requirements/constraints.txt`

```txt
# =============================================================================
# DEPENDENCY CONSTRAINTS
# =============================================================================
# Diese Datei limitiert Versionen für ALLE pip-Installationen
# Wird verwendet mit: pip install -c constraints.txt -r requirements.txt
# =============================================================================

# NumPy MUSS < 2.0 sein für OpenCV 4.6.x Kompatibilität
# OpenCV 4.6.0.66 wurde mit NumPy 1.x kompiliert und ist binär inkompatibel mit NumPy 2.x
# PaddleOCR 2.7.0.3 erfordert opencv<=4.6.0.66
numpy>=1.21.0,<2.0.0
```

**Befehl:**
```bash
cat > requirements/constraints.txt << 'EOF'
# NumPy Constraint für OpenCV 4.6.x Kompatibilität
# OpenCV 4.6.0.66 ist binär inkompatibel mit NumPy 2.x
numpy>=1.21.0,<2.0.0
EOF
```

---

### Phase 2: requirements/ml.txt prüfen und anpassen

**Prüfen:** Existiert eine explizite numpy-Zeile?

```bash
grep -n "numpy" requirements/ml.txt
```

**Falls numpy explizit gelistet:** ENTFERNEN (wird über constraints gesteuert)

**Gewünschter Inhalt von ml.txt:**
```txt
# =============================================================================
# ML/OCR Dependencies
# =============================================================================
# NumPy Version wird über constraints.txt gesteuert (muss <2.0 sein)
# =============================================================================

paddleocr==2.7.0.3
pdf2image==1.16.3
spacy==3.7.2
opencv-python-headless==4.6.0.66
scikit-image==0.22.0
```

**WICHTIG:** 
- `opencv-python-headless` NICHT `opencv-python` (Cloud Run ist headless)
- Keine numpy-Zeile hier (Constraint übernimmt)

---

### Phase 3: Dockerfile anpassen

**Suche den Abschnitt mit pip install und ersetze ihn durch:**

```dockerfile
# =============================================================================
# PYTHON DEPENDENCIES - OpenCV/NumPy Fix
# =============================================================================
# Problem: OpenCV 4.6.x ist inkompatibel mit NumPy 2.x
# Lösung: Constraints File + Installationsreihenfolge
# =============================================================================

# Kopiere Requirements (falls nicht bereits geschehen)
COPY requirements/ /app/requirements/

# -----------------------------------------------------------------------------
# Schritt 1: NumPy mit exakter Version ZUERST installieren
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir "numpy==1.26.4" && \
    python -c "import numpy; print(f'✅ NumPy {numpy.__version__} installiert')"

# -----------------------------------------------------------------------------
# Schritt 2: OpenCV headless OHNE Dependencies (nutzt vorhandenes NumPy)
# -----------------------------------------------------------------------------
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
RUN pip install --no-cache-dir \
    -c /app/requirements/constraints.txt \
    -r /app/requirements/ml.txt

# -----------------------------------------------------------------------------
# Schritt 7: Finale Verification nach ALLEN Installationen
# -----------------------------------------------------------------------------
RUN python -c "\
import numpy as np; \
import cv2; \
assert np.__version__.startswith('1.'), f'KRITISCH: NumPy wurde auf {np.__version__} geupgradet!'; \
print(f'✅ FINAL CHECK: NumPy {np.__version__}, OpenCV {cv2.__version__}')"

# -----------------------------------------------------------------------------
# Schritt 8: spaCy German Model
# -----------------------------------------------------------------------------
RUN python -m spacy download de_core_news_sm || echo "⚠️ spaCy model download übersprungen"
```

---

### Phase 4: docker-compose.yml prüfen

**Sicherstellen dass web-Service korrekt konfiguriert ist:**

```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    # ... weitere Config
```

---

### Phase 5: Build und Test

**Schritt 5.1: Cleanup**
```bash
# Alte Container und Images entfernen
docker-compose down
docker system prune -f
docker builder prune -f
```

**Schritt 5.2: Build mit frischem Cache**
```bash
docker-compose build --no-cache web
```

**Schritt 5.3: Container starten**
```bash
docker-compose up -d
```

**Schritt 5.4: Logs prüfen**
```bash
docker-compose logs web --tail=100
```

**Schritt 5.5: Version-Check im Container**
```bash
docker-compose exec web pip list | grep -E "numpy|opencv|paddle"
```

**Erwartete Ausgabe:**
```
numpy                    1.26.4
opencv-python-headless   4.6.0.66
paddleocr                2.7.0.3
```

**Schritt 5.6: Import-Test**
```bash
docker-compose exec web python -c "
import numpy as np
import cv2
from paddleocr import PaddleOCR

print(f'NumPy: {np.__version__}')
print(f'OpenCV: {cv2.__version__}')
print('PaddleOCR: Import erfolgreich')
"
```

**Schritt 5.7: Test Suite**
```bash
docker-compose exec web pytest tests/ -v
```

---

## 📁 DATEIEN DIE GEÄNDERT WERDEN

| Datei | Aktion | Beschreibung |
|-------|--------|--------------|
| `requirements/constraints.txt` | NEU | NumPy Version Constraint |
| `requirements/ml.txt` | ÄNDERN | numpy-Zeile entfernen falls vorhanden |
| `Dockerfile` | ÄNDERN | pip install Abschnitt ersetzen |

---

## ✅ VALIDIERUNGS-CHECKLISTE

Nach Implementation diese Punkte prüfen:

```
[ ] constraints.txt existiert mit numpy<2.0.0
[ ] ml.txt hat KEINE explizite numpy-Zeile
[ ] Dockerfile nutzt -c constraints.txt bei ALLEN pip install
[ ] Dockerfile hat Verification-Steps
[ ] docker-compose build --no-cache erfolgreich
[ ] Container startet ohne Fehler
[ ] pip list zeigt numpy 1.26.x
[ ] pip list zeigt opencv-python-headless 4.6.0.66
[ ] python -c "import cv2, numpy" funktioniert
[ ] pytest tests/ -v alle Tests grün
[ ] OCR-Service Test funktioniert
```

---

## 🚨 FEHLERBEHEBUNG

### Fehler: "numpy.core.multiarray failed to import"
**Ursache:** NumPy 2.x installiert
**Lösung:** 
1. Prüfen ob constraints.txt bei pip install verwendet wird
2. Prüfen ob ein Paket numpy ohne Constraint installiert

```bash
# Debug:
docker-compose exec web pipdeptree --reverse --packages numpy
```

### Fehler: "libGL.so.1 not found"
**Ursache:** opencv-python statt opencv-python-headless
**Lösung:** In ml.txt `opencv-python-headless` verwenden

### Fehler: Build hängt bei PyMuPDF
**Info:** Normal, dauert 10-15 Minuten
**Aktion:** Warten

### Fehler: Tests schlagen fehl nach Fix
**Aktion:** 
1. NICHT den Fix rückgängig machen
2. Fehler analysieren
3. Tests einzeln debuggen
4. User konsultieren

---

## 📝 GIT COMMIT MESSAGE

Nach erfolgreichem Fix:

```
fix(docker): resolve OpenCV/NumPy 2.x incompatibility

- Add constraints.txt to pin numpy<2.0.0 for all installations
- Use opencv-python-headless for Cloud Run compatibility  
- Add verification steps in Dockerfile to fail fast
- Remove explicit numpy from ml.txt (controlled via constraints)

Problem: OpenCV 4.6.0.66 is binary-incompatible with NumPy 2.x
PaddleOCR 2.7.0.3 requires opencv<=4.6.0.66

Tested:
- Docker build successful
- All 169+ tests passing
- OCR service functional
```

---

## 📊 ERWARTETES ERGEBNIS

### Erfolgreicher Build Output (letzte Zeilen):
```
✅ NumPy 1.26.4 installiert
✅ OpenCV 4.6.0.66 installiert
✅ Kompatibilitäts-Check: NumPy 1.26.4, OpenCV 4.6.0.66
✅ FINAL CHECK: NumPy 1.26.4, OpenCV 4.6.0.66
```

### Erfolgreicher Container Start:
```
web_1  | [INFO] Starting Gunicorn
web_1  | [INFO] Workers: 4
web_1  | [INFO] Listening at: http://0.0.0.0:8000
```

### Erfolgreiche Tests:
```
========================= test session starts ==========================
collected 169 items
...
========================= 169 passed in X.XXs ==========================
```

---

## 🔄 FALLS CONSTRAINTS NICHT FUNKTIONIEREN

### Alternative A: pip-tools Lockfile

```bash
# Lokal:
pip install pip-tools
pip-compile requirements/ml.txt -o requirements/ml.locked.txt

# Dann in Dockerfile:
RUN pip install -r requirements/ml.locked.txt
```

### Alternative B: Exaktes Version Pinning in ml.txt

```txt
numpy==1.26.4
opencv-python-headless==4.6.0.66
paddleocr==2.7.0.3
# ... alle anderen mit ==
```

### Alternative C: Virtual Environment im Container

```dockerfile
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install numpy==1.26.4
# ... rest
```

---

## 📚 REFERENZEN

- [pip Constraints Files](https://pip.pypa.io/en/stable/user_guide/#constraints-files)
- [NumPy 2.0 Migration Guide](https://numpy.org/devdocs/numpy_2_0_migration_guide.html)
- [PaddleOCR Requirements](https://github.com/PaddlePaddle/PaddleOCR)
- [Cloud Run Container Contract](https://cloud.google.com/run/docs/container-contract)

---

**Ende des Leitfadens**
