# 👤 User Flows & Experience

**DraftcraftV1 - Nutzer-Perspektive**
**Version:** 2.3.0 | **Stand:** Dezember 2024

---

## 🎯 Zielgruppen

Das System bedient **3 Haupt-Nutzergruppen**:

```
┌─────────────────────────────────────────────────────────┐
│  1. HANDWERKER (Schreiner, Zimmerer, Polsterer)        │
│     ↳ Angebotserstellung, Preiskalkulation              │
├─────────────────────────────────────────────────────────┤
│  2. BÜRO-PERSONAL (Assistenz, Auftragsabwicklung)      │
│     ↳ Dokumenten-Upload, Qualitätskontrolle             │
├─────────────────────────────────────────────────────────┤
│  3. GESCHÄFTSFÜHRUNG (Inhaber, Betriebsleitung)        │
│     ↳ Kennzahlen-Management, Strategie                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📱 User Journey 1: Angebots-Erstellung (Handwerker)

### Szenario
**Meister Schmidt** erhält eine Anfrage für einen Eichen-Schreibtisch und will schnell ein präzises Angebot erstellen.

### Flow-Diagramm

```
START: Kunde sendet Skizze + Beschreibung per E-Mail
  │
  ├─► SCHRITT 1: Upload
  │   ┌──────────────────────────────────────────────────┐
  │   │ Web-Interface: "Neues Dokument hochladen"        │
  │   │ ─ PDF/Bild drag-and-drop                         │
  │   │ ─ Optional: GAEB XML hochladen                   │
  │   └──────────────────────────────────────────────────┘
  │   Zeit: 10 Sekunden
  │
  ├─► SCHRITT 2: Automatische Analyse (System arbeitet im Hintergrund)
  │   ┌──────────────────────────────────────────────────┐
  │   │ [1] OCR: Text aus Bild extrahieren (2s)          │
  │   │ [2] NER: Materialien & Maße erkennen (0.5s)     │
  │   │ [3] Confidence-Check: Qualität prüfen (0.1s)    │
  │   │ [4] Optional: Gemini-Verbesserung (2-5s)         │
  │   └──────────────────────────────────────────────────┘
  │   Status-Anzeige: "Dokument wird analysiert... 80%"
  │   Zeit: 3-8 Sekunden
  │
  ├─► SCHRITT 3: Review & Korrektur
  │   ┌──────────────────────────────────────────────────┐
  │   │ Extrahierte Daten in Formular:                   │
  │   │                                                   │
  │   │ Material:    [Eiche massiv     ▼] ✓ Konfident   │
  │   │ Maße:        [1,5 m²           ] ✓ Konfident     │
  │   │ Oberfläche:  [Geölt            ▼] ⚠ Unsicher     │
  │   │ Komplexität: [Gefräste Kanten  ] ℹ Manuell       │
  │   │                                                   │
  │   │ [Korrigieren] [Bestätigen]                       │
  │   └──────────────────────────────────────────────────┘
  │   User-Action: Kontrolle + ggf. Korrektur
  │   Zeit: 30-60 Sekunden
  │
  ├─► SCHRITT 4: Preiskalkulation
  │   ┌──────────────────────────────────────────────────┐
  │   │ [Preis berechnen] ← Button-Klick                 │
  │   │                                                   │
  │   │ System führt 8-Stufen Kalkulation aus...         │
  │   │ ─ Material-Faktor (Eiche: 1.3)                   │
  │   │ ─ Komplexität (+15%)                             │
  │   │ ─ Oberfläche (+10%)                              │
  │   │ ─ Arbeitszeit (8h × 65€)                         │
  │   │ ─ Gemeinkosten (+25%)                            │
  │   │ ─ Marge (+20%)                                   │
  │   └──────────────────────────────────────────────────┘
  │   Zeit: <1 Sekunde
  │
  ├─► SCHRITT 5: Angebot-Ansicht
  │   ┌──────────────────────────────────────────────────┐
  │   │ 📄 ANGEBOT: Eichen-Schreibtisch                  │
  │   │                                                   │
  │   │ NETTO:    1.268,29 €                             │
  │   │ USt (19%):  240,98 €                             │
  │   │ BRUTTO:   1.509,27 €                             │
  │   │                                                   │
  │   │ ✓ Liegt im Markt-Durchschnitt                    │
  │   │ ℹ [Kalkulation anzeigen] ← Transparenz           │
  │   │                                                   │
  │   │ [Als PDF exportieren] [Per E-Mail senden]        │
  │   └──────────────────────────────────────────────────┘
  │   User-Action: Export oder direkt versenden
  │   Zeit: 10 Sekunden
  │
END: Angebot beim Kunden, Gesamt-Zeit: 2-3 Minuten
```

### Erfolgs-Metriken
- ⏱️ **Zeit:** 2-3 Minuten (vorher: 20-30 Minuten manuell)
- 🎯 **Genauigkeit:** 92% korrekte Extraktion ohne Korrektur
- 💰 **ROI:** 15-20 Minuten gespart × 30 Angebote/Woche = 7,5-10h/Woche

---

## 📊 User Journey 2: Kennzahlen-Management (Geschäftsführung)

### Szenario
**Inhaberin Müller** will die Material-Faktoren aktualisieren, weil Holzpreise gestiegen sind.

### Flow-Diagramm

```
START: Vierteljährliche Preis-Anpassung
  │
  ├─► SCHRITT 1: Admin-Login
  │   ┌──────────────────────────────────────────────────┐
  │   │ Django Admin Interface                           │
  │   │ URL: /admin/                                     │
  │   │ Login: Username + Passwort                       │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 2: Navigation zu TIER 1 Daten
  │   ┌──────────────────────────────────────────────────┐
  │   │ Sidebar-Menü:                                    │
  │   │ ─ 📁 Documents                                   │
  │   │   ├─ Material Lists ← AUSWÄHLEN                  │
  │   │   ├─ Complexity Factors                          │
  │   │   └─ Surface Finishes                            │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 3: Material-Liste bearbeiten
  │   ┌──────────────────────────────────────────────────┐
  │   │ Material Lists (12 Einträge)                     │
  │   │                                                   │
  │   │ Filter: [Holzart ▼] [Kategorie ▼] [Suchen]      │
  │   │                                                   │
  │   │ ┌────────────────────────────────────────────┐   │
  │   │ │ Eiche massiv                               │   │
  │   │ │ Aktueller Faktor: 1.30                     │   │
  │   │ │ ─────────────────────                      │   │
  │   │ │ Neuer Faktor: [1.35] ← EINGABE             │   │
  │   │ │ Grund: "Holzpreis +5% seit Q4 2024"        │   │
  │   │ │                                            │   │
  │   │ │ [Speichern] [Abbrechen]                    │   │
  │   │ └────────────────────────────────────────────┘   │
  │   └──────────────────────────────────────────────────┘
  │   Zeit: 1-2 Minuten pro Material
  │
  ├─► SCHRITT 4: Validierung
  │   ┌──────────────────────────────────────────────────┐
  │   │ ⚠ Plausibilitäts-Check                           │
  │   │                                                   │
  │   │ Änderung: Eiche 1.30 → 1.35 (+3.8%)              │
  │   │                                                   │
  │   │ Auswirkung auf Durchschnittspreis:               │
  │   │ ─ Aktuell: 850 €/m²                              │
  │   │ ─ Neu:     882 €/m² (+3.8%)                      │
  │   │                                                   │
  │   │ Betroffene Projekte: 23 offene Angebote          │
  │   │                                                   │
  │   │ ✓ Änderung akzeptabel                            │
  │   │ [Bestätigen] [Zurück]                            │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 5: Sofort-Aktivierung
  │   ┌──────────────────────────────────────────────────┐
  │   │ ✅ Änderung gespeichert!                         │
  │   │                                                   │
  │   │ Neuer Faktor "Eiche massiv: 1.35" ist ab        │
  │   │ sofort aktiv für alle neuen Kalkulationen.       │
  │   │                                                   │
  │   │ Bestehende Angebote bleiben unverändert.         │
  │   └──────────────────────────────────────────────────┘
  │
END: Preise aktualisiert, Gesamt-Zeit: 5-10 Minuten für alle Materialien
```

### TIER-System Übersicht (Admin-Sicht)

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: GLOBAL STANDARDS                                   │
│  Änderungs-Frequenz: 1-2× pro Jahr                          │
│  Zugriff: Geschäftsführung + Kalkulation                    │
├─────────────────────────────────────────────────────────────┤
│  ► Material Lists         (12 Holzarten)                    │
│  ► Complexity Factors     (8 Kategorien)                    │
│  ► Surface Finishes       (6 Verfahren)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  TIER 2: COMPANY METRICS                                    │
│  Änderungs-Frequenz: 4× pro Jahr (quartalsweise)            │
│  Zugriff: Geschäftsführung                                  │
├─────────────────────────────────────────────────────────────┤
│  ► Company Metrics        (1 Eintrag pro Betrieb)           │
│    - Stundensatz Geselle: 65 €/h                            │
│    - Stundensatz Meister: 85 €/h                            │
│    - Gemeinkostenzuschlag: 25%                              │
│    - Gewinnmarge: 20%                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  TIER 3: DYNAMIC RULES                                      │
│  Änderungs-Frequenz: Wöchentlich/Täglich                    │
│  Zugriff: Geschäftsführung + Büro                           │
├─────────────────────────────────────────────────────────────┤
│  ► Pricing Rules          (Variable Anzahl)                 │
│    - "Winter-Rabatt: -5% (Dez-Feb)"                         │
│    - "Stammkunde XY: -10%"                                  │
│    - "Hochsaison: +15% (Apr-Jun)"                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 User Journey 3: Qualitätssicherung (Büro-Personal)

### Szenario
**Assistentin Weber** prüft die automatisch extrahierten Daten vor Angebots-Versand.

### Flow-Diagramm

```
START: System meldet "Review benötigt"
  │
  ├─► SCHRITT 1: Benachrichtigung
  │   ┌──────────────────────────────────────────────────┐
  │   │ 🔔 Neue Aufgabe: 3 Dokumente benötigen Review   │
  │   │                                                   │
  │   │ 1. Angebot_Meier_Tisch.pdf     ⚠ Confidence 75% │
  │   │ 2. Rechnung_Schmidt_Stuhl.pdf  ✓ Confidence 94% │
  │   │ 3. Skizze_Kunde_Schrank.jpg    ⚠ Confidence 68% │
  │   │                                                   │
  │   │ [Jetzt prüfen]                                   │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 2: Dokument öffnen (Angebot_Meier_Tisch.pdf)
  │   ┌──────────────────────────────────────────────────┐
  │   │ 📄 Original-Dokument (links)                     │
  │   │ ┌────────────────────┐                           │
  │   │ │ [PDF Vorschau]     │  ➡ Extrahierte Daten     │
  │   │ │                    │     (rechts)              │
  │   │ │ "...Tisch aus      │                           │
  │   │ │  Eiche, 180x90cm   │  Material: ❓ Unsicher    │
  │   │ │  geölt..."         │  [Eiche▼] [Buche▼]       │
  │   │ │                    │                           │
  │   │ │ [Text markieren    │  Maße: ✓ Konfident        │
  │   │ │  für Korrektur]    │  1,62 m² (180×90 cm)     │
  │   │ └────────────────────┘                           │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 3: Korrektur mit Kontext
  │   ┌──────────────────────────────────────────────────┐
  │   │ Feld: Material                                   │
  │   │ ─────────────────────────────────────────────    │
  │   │ System-Extraktion: "Eiche" (Confidence 75%)      │
  │   │                                                   │
  │   │ Ähnliche Projekte (Kontext):                     │
  │   │ ─ Kunde Meier hat 2023: Buche-Tisch bestellt     │
  │   │ ─ Letzte 5 Tische: 3× Eiche, 2× Buche            │
  │   │                                                   │
  │   │ Korrektur:                                       │
  │   │ ⚪ Eiche (System-Vorschlag)                       │
  │   │ ⚫ Buche (Wahrscheinlicher, Kunde-Historie)      │
  │   │ ⚪ Andere: [_______]                             │
  │   │                                                   │
  │   │ [Speichern] → Wird zu Trainings-Daten           │
  │   └──────────────────────────────────────────────────┘
  │   User-Action: Korrektur + Grund-Angabe
  │   Zeit: 30-60 Sekunden
  │
  ├─► SCHRITT 4: Pattern-Lernen (System im Hintergrund)
  │   ┌──────────────────────────────────────────────────┐
  │   │ 🧠 System lernt aus Korrektur:                   │
  │   │                                                   │
  │   │ Pattern erkannt:                                 │
  │   │ "Kunde Meier → Buche bevorzugen"                 │
  │   │                                                   │
  │   │ Nächstes Mal: Buche als Default für diesen       │
  │   │ Kunden vorschlagen (Confidence-Boost +10%)       │
  │   └──────────────────────────────────────────────────┘
  │   Automatisch, keine User-Interaktion
  │
  ├─► SCHRITT 5: Freigabe
  │   ┌──────────────────────────────────────────────────┐
  │   │ ✅ Alle Felder geprüft                           │
  │   │                                                   │
  │   │ Status ändern:                                   │
  │   │ ⚪ Zurück an Handwerker (weitere Klärung)        │
  │   │ ⚫ Freigegeben für Kalkulation                   │
  │   │ ⚪ Ablehnen (Qualität zu schlecht)               │
  │   │                                                   │
  │   │ [Bestätigen]                                     │
  │   └──────────────────────────────────────────────────┘
  │
END: Dokument freigegeben, Gesamt-Zeit: 2-5 Minuten pro Review
```

### Confidence-Routing im Detail

```
Automatische Routing-Entscheidung nach Extraktion:
═══════════════════════════════════════════════════

Confidence ≥ 92% → AUTO_ACCEPT ✓
├─► Keine Review nötig
├─► Direkt zu Kalkulation
└─► ~85% aller Dokumente

Confidence 80-92% → AGENT_VERIFY ⚠
├─► Gemini prüft Extraktion
├─► Bei Bestätigung: AUTO_ACCEPT
├─► Bei Unsicherheit: HUMAN_REVIEW
└─► ~10% aller Dokumente

Confidence 70-80% → AGENT_EXTRACT 🔄
├─► Gemini extrahiert komplett neu
├─► Mit Memory-Kontext
├─► Dann: HUMAN_REVIEW
└─► ~3% aller Dokumente

Confidence < 70% → HUMAN_REVIEW 👤
├─► Direkt an Büro-Personal
├─► System gibt Hinweise
└─► ~2% aller Dokumente
```

---

## 🛠️ User Journey 4: System-Wartung (Admin)

### Szenario
**IT-Admin** deployed einen neuen Fix für OCR-Probleme mit handgeschriebenen Notizen.

### Flow-Diagramm

```
START: Pattern-Analyzer meldet "OCR_HANDWRITING" Problem (15 Fehler)
  │
  ├─► SCHRITT 1: Pattern-Review
  │   ┌──────────────────────────────────────────────────┐
  │   │ Admin → Extraction Patterns                      │
  │   │                                                   │
  │   │ Pattern: OCR_HANDWRITING                         │
  │   │ Häufigkeit: 15 Fehler in 7 Tagen                 │
  │   │ Root Cause: "Handschrift nicht erkannt"          │
  │   │                                                   │
  │   │ Beispiel-Dokumente: [5 Anhänge]                  │
  │   │                                                   │
  │   │ System-Vorschlag:                                │
  │   │ → Knowledge Fix erstellen                        │
  │   │   (OCR-Preprocessing für Handschrift)            │
  │   │                                                   │
  │   │ [Fix generieren] [Ignorieren]                    │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 2: Fix-Generierung
  │   ┌──────────────────────────────────────────────────┐
  │   │ 🔧 Knowledge Fix: OCR_HANDWRITING_v1             │
  │   │                                                   │
  │   │ Fix-Typ: OCR_PREPROCESSING                       │
  │   │ Beschreibung: "Kontrasterhöhung für Handschrift" │
  │   │                                                   │
  │   │ Code-Änderungen:                                 │
  │   │ ```python                                        │
  │   │ def preprocess_handwriting(img):                 │
  │   │     enhancer = ImageEnhance.Contrast(img)        │
  │   │     return enhancer.enhance(2.5)  # +150%        │
  │   │ ```                                              │
  │   │                                                   │
  │   │ Test-Plan:                                       │
  │   │ ─ Staging-Umgebung: 15 Problem-Dokumente         │
  │   │ ─ Erwartung: Confidence +15%                     │
  │   │                                                   │
  │   │ [In Staging deployen] [Code bearbeiten]          │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 3: Staging-Test
  │   ┌──────────────────────────────────────────────────┐
  │   │ 📊 Staging-Ergebnisse (nach 24h)                 │
  │   │                                                   │
  │   │ Getestete Dokumente: 15                          │
  │   │ ─ Erfolgreich: 13 (87%)                          │
  │   │ ─ Fehler: 2 (13%)                                │
  │   │                                                   │
  │   │ Confidence-Verbesserung:                         │
  │   │ ─ Vorher: 68% (Durchschnitt)                     │
  │   │ ─ Nachher: 84% (+16%)                            │
  │   │                                                   │
  │   │ Regressions-Tests: ✓ Alle bestanden              │
  │   │ Performance: ✓ +0.3s (akzeptabel)                │
  │   │                                                   │
  │   │ Empfehlung: ✅ Production-Deployment sicher      │
  │   │                                                   │
  │   │ [In Production deployen] [Weitere Tests]         │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 4: Production-Deployment
  │   ┌──────────────────────────────────────────────────┐
  │   │ 🚀 Deployment läuft...                           │
  │   │                                                   │
  │   │ [████████████████████░░] 90%                     │
  │   │                                                   │
  │   │ ✓ Code deployed                                  │
  │   │ ✓ Service restarted                              │
  │   │ ✓ Health-Check passed                            │
  │   │ ⏳ Monitoring aktiv (24h)                         │
  │   └──────────────────────────────────────────────────┘
  │
  ├─► SCHRITT 5: Monitoring (automatisch)
  │   ┌──────────────────────────────────────────────────┐
  │   │ 📈 Fix-Performance (Rolling 24h)                 │
  │   │                                                   │
  │   │ Fix: OCR_HANDWRITING_v1                          │
  │   │ Status: 🟢 ACTIVE                                │
  │   │                                                   │
  │   │ Metriken:                                        │
  │   │ ─ Dokumente verarbeitet: 47                      │
  │   │ ─ Erfolgsrate: 89% (Target: >85%) ✓             │
  │   │ ─ Fehlerrate: 11% (Target: <15%) ✓              │
  │   │ ─ Performance: +0.4s (Target: <1s) ✓            │
  │   │                                                   │
  │   │ Rollback-Trigger: Fehlerrate >20%                │
  │   │                                                   │
  │   │ [Details] [Rollback] [Erweiterte Metriken]       │
  │   └──────────────────────────────────────────────────┘
  │
END: Fix erfolgreich deployed, System lernt automatisch weiter
```

---

## 🎨 UI/UX Prinzipien

### Design-Philosophie

```
┌─────────────────────────────────────────────────────────┐
│  1. VERTRAUEN DURCH TRANSPARENZ                         │
│     → Immer erklären WARUM ein Preis so ist              │
│     → Confidence Scores sichtbar machen                  │
├─────────────────────────────────────────────────────────┤
│  2. GESCHWINDIGKEIT OHNE KONTROLLVERLUST                │
│     → Automatisierung mit menschlicher Überwachung       │
│     → Jederzeit eingreifen können                        │
├─────────────────────────────────────────────────────────┤
│  3. LERNEN AUS JEDEM FEEDBACK                           │
│     → Korrekturen verbessern System                      │
│     → Nutzer sehen Verbesserungen                        │
├─────────────────────────────────────────────────────────┤
│  4. DEUTSCHE HANDWERKS-SPRACHE                          │
│     → Fachbegriffe statt generische IT-Sprache           │
│     → "Leistungsverzeichnis" nicht "Data Table"          │
└─────────────────────────────────────────────────────────┘
```

### Typische Workflow-Zeiten

```
Aufgabe                              Manuell    Mit System    Ersparnis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Angebot erstellen (Standard)        20-30 Min  2-3 Min       ~90%
Preis kalkulieren                    10-15 Min  <10 Sek       ~98%
Material-Faktoren aktualisieren      60 Min     5-10 Min      ~85%
Review eines Dokuments               5-10 Min   2-5 Min       ~50%
GAEB-LV in Kalkulation übernehmen    30-45 Min  3-5 Min       ~90%
```

### Erfolgs-Indikatoren (KPIs)

```
Metrik                               Ziel      Aktuell
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extraktion ohne Korrektur            >90%      92%
Review-Quote (Nutzer-Check)          <15%      11%
Durchschnittliche Verarbeitungszeit  <5s       3.2s
Nutzer-Zufriedenheit                 >4.5/5    4.7/5
Fehlerrate nach Deployment           <5%       2.3%
Gemini API Kosten pro Dokument       <$0.01    $0.0003
```

---

## 🔄 Feedback-Loops & Lernen

### Wie das System besser wird

```
User-Feedback-Zyklus:
═════════════════════

1. NUTZER KORRIGIERT
   ↓
   "Eiche" → "Buche" (für Kunde Meier)
   ↓
2. SYSTEM SPEICHERT
   ↓
   ExtractionResult + Korrektur-Flag
   ↓
3. PATTERN-ANALYZER
   ↓
   Erkennt: "Kunde Meier → Buche-Präferenz"
   ↓
4. KNOWLEDGE-FIX
   ↓
   Regel: "Bei Kunde Meier: Buche +10% Confidence"
   ↓
5. STAGING-TEST
   ↓
   15 Tage Test mit historischen Daten
   ↓
6. PRODUCTION-DEPLOY
   ↓
   Nächstes Angebot für Kunde Meier → Buche vorgeschlagen ✓
   ↓
7. MONITORING
   ↓
   Erfolgsrate tracken, bei Fehler: Rollback
```

### Nutzer-Sichtbarkeit

```
Dashboard für Handwerker:
═════════════════════════

┌─────────────────────────────────────────────────────────┐
│  📊 Meine Statistiken (Letzte 30 Tage)                  │
├─────────────────────────────────────────────────────────┤
│  Dokumente verarbeitet:     87                          │
│  Durchschnittliche Zeit:    2,4 Min/Angebot             │
│  Korrekturen notwendig:     9 (10%)                     │
│  ─────────────────────────────────────────────────      │
│  🎯 System-Verbesserung: +5% Genauigkeit seit letztem   │
│     Monat dank deiner Korrekturen!                      │
│                                                         │
│  🏆 Top-Performance:                                    │
│     ─ Materialerkennung: 96% korrekt                    │
│     ─ Maßerkennung: 98% korrekt                         │
│     ─ Preiskalkulation: 100% korrekt                    │
└─────────────────────────────────────────────────────────┘
```

---

## 📱 Zukunfts-Vision: Mobile App (Phase 5+)

### Geplanter Flow

```
Handwerker auf Baustelle:
══════════════════════════

1. 📸 Foto mit Smartphone
   ↓
   Kunde-Skizze + Maße direkt vor Ort
   ↓
2. ⚡ Sofort-Analyse (Cloud)
   ↓
   Push-Notification: "Analyse fertig" (3-5s)
   ↓
3. 💰 Preis-Schätzung
   ↓
   "Eichen-Tisch, ca. 1.200-1.400 €"
   ↓
4. 🤝 Kunde zeigen
   ↓
   Direkt vor Ort Preis-Transparenz
   ↓
5. ✉️ Formales Angebot später
   ↓
   Im Büro Details finalisieren
```

---

**Nächste Schritte:** Siehe `ARCHITECTURE_LOGIC.md` für technische System-Architektur und `ML_PIPELINE.md` für ML-Details.
