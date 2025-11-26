# Archive - German Handwerk Document Analysis System

Dieses Verzeichnis enthält **archivierte Code-Artefakte** aus früheren Entwicklungsphasen.

## 📋 Zweck

Das Archive-System dient der **sauberen Repository-Hygiene** ohne Verlust der Git-History:

- ✅ Entfernt ungenutzten Code aus aktivem Development
- ✅ Bewahrt historischen Kontext für zukünftige Referenz
- ✅ Ermöglicht schnelles Rollback falls nötig
- ✅ Dokumentiert Entwicklungs-Entscheidungen

---

## 📁 Struktur

```
archive/
├── 2025-11/                    # Monats-Archiv (YYYY-MM)
│   ├── CHANGES.md             # Dokumentation aller Änderungen
│   ├── deprecated_code/       # Veralteter/ersetzter Code
│   ├── old_migrations/        # Superseded Migrations (>6 Monate)
│   ├── experimental/          # Verworfene Experimente
│   └── unused_files/          # Files ohne References
├── 2025-10/
│   └── ...
└── legacy/                     # Langzeit-Archiv (>12 Monate)
    ├── mvp_v1/                # MVP Version 1 (vor Refactoring)
    ├── proof_of_concepts/     # Frühe POCs
    └── abandoned_features/    # Features die nicht in Production gingen
```

---

## 🔄 Archivierungs-Prozess

### Wann archivieren?

**Automatische Trigger:**
- Code nicht verwendet seit 30+ Tagen (vulture detection)
- Migration-Files >6 Monate alt und superseded
- Test-Files für entfernte Features
- Experimental code ohne Tests

**Manuelle Review-Trigger:**
- Feature-Deprecation beschlossen
- Refactoring macht alten Code obsolet
- API-Version wird End-of-Life
- Design-Pattern wird durch besseren ersetzt

### Wie archivieren?

**1. Identifiziere Kandidaten:**
```bash
# Ungenutzte Python-Files finden
vulture . --min-confidence 80 > unused_code_report.txt

# Alte Migrations finden
find . -name "*.py" -path "*/migrations/*" -mtime +180

# Files ohne Git-Activity
git log --all --pretty=format: --name-only --since="30 days ago" | sort -u
```

**2. Verschiebe mit Git (behält History):**
```bash
# Aktueller Monat
ARCHIVE_DATE=$(date +%Y-%m)
mkdir -p archive/$ARCHIVE_DATE/{deprecated_code,old_migrations,experimental}

# Git move (behält History!)
git mv path/to/old_file.py archive/$ARCHIVE_DATE/deprecated_code/
```

**3. Dokumentiere in CHANGES.md:**
```bash
cat >> archive/$ARCHIVE_DATE/CHANGES.md << EOF
## Archiviert am $(date +%Y-%m-%d)

### Deprecated Code
- \`old_feature.py\`: Ersetzt durch new_feature.py
  - **Grund:** Performance-Verbesserung mit async processing
  - **Dependencies:** Keine
  - **Migration:** Siehe migration_guide.md
  - **Rollback:** \`git mv archive/$ARCHIVE_DATE/deprecated_code/old_feature.py path/to/\`

### Performance Impact
- Reduzierte Codebase-Größe: -15%
- Schnellere Tests: -8% Laufzeit
- Cleaner Dependencies Graph
EOF
```

**4. Commit mit aussagekräftiger Message:**
```bash
git add .
git commit -m "archive: Move deprecated features to archive/$ARCHIVE_DATE

- Moved unused OCR fallback to deprecated_code/
- Archived migrations 0001-0010 (superseded by 0025)
- Removed experimental async_v1 implementation

See archive/$ARCHIVE_DATE/CHANGES.md for details
Rollback: Instructions in CHANGES.md if needed"
```

---

## 📊 Archiv-Statistiken

### Aktueller Stand

| Kategorie | Anzahl Files | Größe | Ältestes |
|-----------|--------------|-------|----------|
| Deprecated Code | TBD | TBD | TBD |
| Old Migrations | TBD | TBD | TBD |
| Experimental | TBD | TBD | TBD |
| Legacy | TBD | TBD | TBD |

*Aktualisiert: Wird monatlich durch Cleanup-Action generiert*

---

## 🔍 Archive durchsuchen

### Nach Feature/Funktion suchen
```bash
# Suche in allen Archiv-Ordnern
grep -r "function_name" archive/

# Suche in spezifischem Monat
grep -r "OldService" archive/2025-11/
```

### Nach Datum suchen
```bash
# Zeige alle Archivierungen im November 2025
ls -la archive/2025-11/*/

# Zeige CHANGES.md für bestimmten Monat
cat archive/2025-11/CHANGES.md
```

### Git History für archiviertes File
```bash
# Volle History anzeigen (auch nach Move)
git log --follow -- archive/2025-11/deprecated_code/old_file.py

# File-Content zu bestimmtem Zeitpunkt
git show <commit-hash>:old/path/to/file.py
```

---

## ♻️ Rollback-Prozeduren

### File wiederherstellen

**Schneller Rollback:**
```bash
# File zurück ins aktive Project
git mv archive/2025-11/deprecated_code/needed_file.py extraction/services/

# Commit
git commit -m "unarchive: Restore needed_file.py from archive

Reason: Feature is needed for new requirement
Original archive: 2025-11 (deprecated_code/)
See issue #123 for context"
```

**Mit Anpassungen:**
```bash
# Copy statt move (für Referenz)
cp archive/2025-11/deprecated_code/old_feature.py extraction/services/new_feature.py

# Dann anpassen und committen
git add extraction/services/new_feature.py
git commit -m "feat: Reimplement feature based on archived code

Based on archive/2025-11/deprecated_code/old_feature.py
Adapted for new async architecture"
```

---

## 🗑️ Permanente Löschung

### Wann permanent löschen?

**NIEMALS löschen wenn:**
- ❌ Code <12 Monate alt
- ❌ Noch in Git-History von aktiven Branches
- ❌ Könnte rechtliche Relevanz haben (DSGVO, Audit)
- ❌ Teil von noch supporteten Features

**KÖNNTE gelöscht werden wenn:**
- ✅ Code >12 Monate archiviert
- ✅ Keine Dependencies mehr
- ✅ Feature komplett deprecated und EOL
- ✅ Backup in separatem Repository vorhanden

### Permanente Löschung (mit Vorsicht!)

```bash
# 1. Finale Sicherung außerhalb Repository
tar -czf legacy-backup-$(date +%Y-%m-%d).tar.gz archive/legacy/

# 2. Lösche aus Git (Vorsicht - nicht reversibel!)
git rm -r archive/legacy/old_project/

# 3. Commit
git commit -m "cleanup: Remove legacy code >12 months old

Files removed: archive/legacy/old_project/
Backup created: legacy-backup-2025-11-20.tar.gz
Reason: EOL, no dependencies, >12 months archived

CAUTION: This is permanent deletion from Git history"
```

---

## 🔒 DSGVO Compliance

### Archivierte Daten & DSGVO

**Wichtig:** Auch archivierter Code muss DSGVO-konform sein!

- ✅ **Keine PII in archivierten Test-Daten**
- ✅ **Keine echten API-Keys oder Credentials**
- ✅ **Pseudonymisierung von User-Daten in Examples**

### Audit vor Archivierung

```bash
# Prüfe auf sensitive Daten
grep -r "password\|api_key\|secret" archive/2025-11/

# Prüfe auf PII
grep -r "@.*\.de\|[0-9]\{10,\}" archive/2025-11/

# Prüfe auf hardcoded URLs
grep -r "https://.*\.de" archive/2025-11/
```

---

## 📋 Automatische Archivierung

### GitHub Actions Workflow

Siehe `.github/workflows/cleanup.yml` - Läuft monatlich:

**Was wird automatisch archiviert:**
1. Files ohne References (vulture detection)
2. Migrations >6 Monate (nach Manual Review)
3. Test-Files für entfernte Features
4. Experimental Branches merged >90 Tage

**Manual Review erforderlich für:**
- Core Services (extraction/, documents/)
- API Endpoints (api/)
- Models & Migrations
- Security-relevanter Code

---

## 📚 Best Practices

### DO ✅

- **Dokumentiere warum** archiviert wurde
- **Gib Rollback-Instructions** in CHANGES.md
- **Behalte Git-History** mit `git mv`
- **Archiviere regelmäßig** (monatlich)
- **Review vor Archivierung** (keine unbeabsichtigten Dependencies)

### DON'T ❌

- **Lösche nicht direkt** (erst archivieren, dann >12 Monate prüfen)
- **Keine Archive-Files ändern** (read-only nach Archivierung)
- **Keine neuen Files in Archive** (nur via Archivierungs-Prozess)
- **Keine unvollständige Dokumentation** (immer CHANGES.md pflegen)

---

## 🔗 Verwandte Dokumentation

- **CLAUDE.md** - Main Development Guide
- **.claude/CHANGELOG.md** - Alle Projekt-Änderungen
- **.github/workflows/cleanup.yml** - Automatisierungs-Workflow
- **archive/YYYY-MM/CHANGES.md** - Monatliche Archivierungs-Details

---

## 📞 Fragen?

**Bei Unklarheiten:**
- Prüfe relevante `CHANGES.md` im Archive-Ordner
- Suche in Git-History: `git log --follow -- <file>`
- Kontaktiere Team für Manual-Review
- Erstelle Issue für Archive-Policy-Fragen

---

**Archivierungs-Policy Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-20  
**Nächster Review:** Monatlich (1. des Monats)
