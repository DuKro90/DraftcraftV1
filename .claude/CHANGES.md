# Archive Changes - 2025-11

**Archivierungs-Datum:** 2025-11-20  
**Durchgeführt von:** Automated Cleanup + Manual Review  
**Phase:** Phase 2 Production Development  

---

## 📊 Übersicht

| Kategorie | Anzahl Files | Gesamt-Größe | Grund |
|-----------|--------------|--------------|-------|
| Deprecated Code | 0 | 0 KB | - |
| Old Migrations | 0 | 0 KB | - |
| Experimental | 0 | 0 KB | - |
| Unused Files | 0 | 0 KB | - |

**Total archiviert:** 0 Files, 0 KB

---

## 📦 Deprecated Code

> Code der durch bessere Implementierungen ersetzt wurde

### [Keine Einträge]

<!-- Template für zukünftige Einträge:

### `extraction/legacy/old_ocr_service.py`
**Ersetzt durch:** `extraction/services/ocr_service.py`  
**Grund:** Migration zu PaddleOCR von Tesseract  
**Archiviert am:** 2025-11-20  

**Dependencies:**
- Keine - komplett standalone

**Migration-Path:**
```python
# Alt
from extraction.legacy.old_ocr_service import TesseractOCR
ocr = TesseractOCR()

# Neu  
from extraction.services.ocr_service import get_ocr_service
ocr = get_ocr_service()
```

**Rollback-Instructions:**
```bash
git mv archive/2025-11/deprecated_code/old_ocr_service.py extraction/legacy/
pip install tesseract-ocr
# Update imports in affected files
```

**Performance Impact:**
- Alt: ~5s pro Seite (Tesseract)
- Neu: ~2s pro Seite (PaddleOCR)
- Improvement: 60% schneller

**DSGVO Impact:**
- Keine PII betroffen
- Gleiches Retention-Policy

-->

---

## 🗃️ Old Migrations

> Django Migrations >6 Monate alt und superseded

### [Keine Einträge]

<!-- Template für zukünftige Einträge:

### `documents/migrations/0001_initial.py` - `0010_add_gaeb_support.py`
**Superseded durch:** `0025_consolidated_schema.py`  
**Archiviert am:** 2025-11-20  
**Ursprüngliches Datum:** 2025-05-15 - 2025-07-20  

**Grund:**
- Alle 10 Migrations wurden in einer konsolidierten Migration zusammengefasst
- Alter: >6 Monate
- Keine aktiven Deployments mit diesen Migrations mehr

**Rollback-Instructions:**
```bash
# WICHTIG: Rollback nur in Entwicklung, NIEMALS in Production!

# 1. Migrations zurückholen
git mv archive/2025-11/old_migrations/0001_initial.py documents/migrations/
# ... für alle 10 Migrations

# 2. Consolidated Migration entfernen
git rm documents/migrations/0025_consolidated_schema.py

# 3. Database State prüfen
python manage.py showmigrations documents

# 4. Falls nötig, fake migrations
python manage.py migrate documents 0010 --fake
```

**Warnung:** ⚠️ Diese Migrations sind nur für historische Referenz. 
Neue Deployments sollten IMMER mit der consolidated migration starten.

-->

---

## 🧪 Experimental Code

> Proof-of-Concepts und verworfene Experimente

### [Keine Einträge]

<!-- Template für zukünftige Einträge:

### `experiments/async_ocr_v1/`
**Status:** Experiment verworfen  
**Archiviert am:** 2025-11-20  
**Entwicklungszeit:** 2025-10-01 - 2025-10-15  

**Original-Ziel:**
- Async OCR Processing mit Celery
- Goal: 50% Performance-Improvement

**Warum verworfen:**
- Cloud Tasks bietet bessere Integration
- Celery adds unnecessary infrastructure complexity
- Maintenance overhead nicht gerechtfertigt

**Gelernte Lektionen:**
- Serverless > Self-managed Workers für unser Scale
- Cloud-native Solutions bevorzugen
- Keep infrastructure simple

**Wiederverwendbare Teile:**
- Queue-Design-Patterns → Verwendet in Cloud Tasks Setup
- Performance-Benchmarks → Baseline für aktuelle Implementation

**Rollback:** Nicht empfohlen - Code war POC-Qualität

-->

---

## 📄 Unused Files

> Files ohne aktive References im Code

### [Keine Einträge]

<!-- Template für zukünftige Einträge:

### `core/utils/legacy_formatter.py`
**Letzte Verwendung:** >90 Tage  
**Archiviert am:** 2025-11-20  
**Vulture Confidence:** 95%  

**Ursprünglicher Zweck:**
- String-Formatierung für alte API v1

**Warum unused:**
- API v1 deprecated seit 2025-08
- Alle Consumers auf v2 migriert
- Keine Imports in aktiver Codebase

**Dependencies:**
- Keine externen Dependencies
- Keine Datenbank-Abhängigkeiten

**Rollback:**
```bash
git mv archive/2025-11/unused_files/legacy_formatter.py core/utils/
# Update imports falls nötig
```

**Empfehlung:** Permanent deletion nach 12 Monaten OK

-->

---

## 📈 Performance Impact

### Code-Reduktion
- **Codebase-Größe:** -0% (keine Änderungen diesen Monat)
- **Test-Laufzeit:** ±0%
- **Build-Zeit:** ±0%

### Dependencies
- **Entfernte Dependencies:** Keine
- **Reduzierte Complexity:** Keine Änderungen

---

## 🔒 DSGVO & Compliance

### Audit-Ergebnis
- ✅ Keine PII in archivierten Files
- ✅ Keine Credentials oder API-Keys
- ✅ Alle Test-Daten pseudonymisiert
- ✅ CHANGES.md dokumentiert alle Änderungen

### Retention Policy
- **Minimum Archive Period:** 12 Monate
- **Review Trigger:** Monatlich (1. des Monats)
- **Permanent Deletion:** Nach Manual Review + Team Approval

---

## 📋 Review Checklist

**Vor Archivierung durchgeführt:**
- [x] Vulture scan für unused code
- [x] Grep für aktive imports/references
- [x] Git log für recent activity
- [x] Dependency check
- [x] DSGVO audit
- [x] Team review (für kritische Files)

**Nach Archivierung:**
- [x] Tests passing (keine broken imports)
- [x] CI/CD pipeline grün
- [x] CHANGES.md dokumentiert
- [x] CHANGELOG.md updated
- [x] Commit mit aussagekräftiger Message

---

## 🔄 Rollback-Anleitung

### Genereller Prozess

```bash
# 1. Identifiziere benötigtes File
ls -la archive/2025-11/<kategorie>/

# 2. Prüfe Dependencies
grep -r "from.*<filename>" .

# 3. Rollback via Git
git mv archive/2025-11/<kategorie>/<file> <original-path>/

# 4. Tests ausführen
pytest tests/ -v

# 5. Commit
git commit -m "unarchive: Restore <file> from archive/2025-11

Reason: <warum benötigt>
Original archive date: 2025-11-20
See archive/2025-11/CHANGES.md for context"
```

### Bei Problemen

**Import Errors:**
```bash
# Prüfe alle Imports
grep -r "import.*<module>" .
# Update imports in betroffenen Files
```

**Test Failures:**
```bash
# Identifiziere fehlende Dependencies
pytest --collect-only
# Restore related archived files
```

**Performance Regression:**
```bash
# Benchmark vor/nach Rollback
python manage.py benchmark_ocr
# Compare mit Performance-Notes oben
```

---

## 📞 Support & Questions

**Bei Fragen zu archivierten Files:**
1. Prüfe diese CHANGES.md
2. Suche in Git-History: `git log --follow -- <file>`
3. Kontaktiere Original-Author (via git blame)
4. Erstelle Issue mit Label `archive-question`

**Für Rollback-Requests:**
1. Erstelle Issue mit Label `archive-rollback`
2. Begründe warum File benötigt wird
3. Warte auf Team-Review
4. Follow Rollback-Anleitung oben

---

## 📝 Änderungs-Log

| Datum | Änderung | Durchgeführt von |
|-------|----------|------------------|
| 2025-11-20 | Initial archive structure created | Automated Setup |
| - | - | - |

---

**Nächste Review:** 2025-12-01  
**Archivierungs-Policy:** Siehe `archive/README.md`  
**Maintenance:** Automatisch via `.github/workflows/cleanup.yml`
