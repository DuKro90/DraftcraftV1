# ANALYSE: Transparenz & Benutzerfreundlichkeit für Handwerker

## 1. ANFORDERUNGSPROFIL: Deutsche Handwerker

### 1.1 Vertrauens-Faktoren (kritisch für Akzeptanz)

**Kulturelle Besonderheiten:**
- Hohes Bedürfnis nach Kontrolle und Nachvollziehbarkeit
- Skepsis gegenüber "Black Box"-Systemen
- Haftungsdenken: "Kann ich das gegenüber Kunden vertreten?"
- Meisterprinzip: Eigenverantwortung & Expertenstatus

**Konkrete Erwartungen:**
- Jeder Kalkulationsschritt muss einsehbar sein
- Manuelle Korrektur muss jederzeit möglich sein
- Ergebnisse müssen plausibel erklärbar sein
- Keine "Computer sagt nein"-Situationen

### 1.2 IT-Kompetenz-Profil

**Typische Charakteristika:**
- Pragmatisch, praxisorientiert
- Begrenzte Zeit für Einarbeitung
- Oft mobile Nutzung (Baustelle, Kundentermin)
- Wenig Geduld für komplexe Interfaces
- Hohe Akzeptanz für bewährte Workflows

---

## 2. BESTANDSAUFNAHME: Aktuelles System

### 2.1 Vorhandene Transparenz-Features ✅

| Feature | Status | Bewertung |
|---------|--------|-----------|
| **Detaillierte Kalkulation** anzeigen | ✅ Vorhanden | Gut strukturiert |
| **Schritt-für-Schritt** Berechnung | ✅ Vorhanden | Nachvollziehbar |
| **Einzelpositionen** aufgeschlüsselt | ✅ Vorhanden | Detailliert |
| **Materialkosten** transparent | ✅ Vorhanden | Gut |
| **Manuelle Override-Funktion** | ✅ Vorhanden | Kritisch wichtig |

### 2.2 Identifizierte Lücken ❌

| Bereich | Problem | Risiko |
|---------|---------|--------|
| **Warum-Fragen** | KI-Entscheidungen nicht erklärt | HOCH |
| **Vergleichbarkeit** | Keine Benchmark zu früheren Kalkulationen | MITTEL |
| **Lernprozess** | Training-Interface fehlt | HOCH |
| **Fehlersichtbarkeit** | Unsicherheiten nicht kommuniziert | MITTEL |
| **Visuelle Aufbereitung** | Zu textlastig für schnelle Erfassung | MITTEL |

---

## 3. BEST PRACTICES: Transparenz in KI-Systemen

### 3.1 Explainable AI (XAI) für Non-Tech-User

**Erfolgreiche Ansätze aus anderen Branchen:**

#### A) **Progressive Disclosure** (Stufenweise Informationstiefe)
```
Level 1: Endergebnis (für schnelle Entscheidung)
Level 2: Hauptfaktoren (3-5 wichtigste Einflussfaktoren)
Level 3: Detailkalkulation (vollständig)
Level 4: KI-Begründung (optional)
```

#### B) **Visual Confidence Indicators** (Ampelsystem)
- 🟢 Grün: Hohe Datenlage, sichere Kalkulation
- 🟡 Gelb: Teilweise Schätzung, Prüfung empfohlen
- 🔴 Rot: Unsichere Datenbasis, manuelle Kontrolle nötig

#### C) **Comparative Explanations** (Vergleichsbasierte Erklärungen)
- "Diese Kalkulation liegt 12% über Ihrem Durchschnitt für Badezimmer"
- "Ähnliche Projekte kosteten zwischen X und Y"

### 3.2 Non-Technical User Interface Design

**Bewährte Prinzipien:**

1. **Speak their Language**
   - Handwerker-Terminologie statt IT-Begriffe
   - "Kalkulation prüfen" statt "Validierung durchführen"

2. **Show, Don't Tell**
   - Visuelle Darstellung vor Text
   - Icons und Farben als Orientierung

3. **Undo über Error Prevention**
   - Jede Aktion rückgängig machbar
   - "Speichern" explizit, kein Autosave ohne Hinweis

4. **Mobile-First für Handwerker**
   - Große Touch-Targets
   - Spracherfassung für Notizen

---

## 4. OPTIMIERUNGSVORSCHLÄGE (Priorisiert)

### 🔴 PRIO 1: Vertrauenskritisch

#### 4.1 KI-Erklärungskomponente

**Aktuell:**
```typescript
// System gibt nur Ergebnis aus
const calculatedPrice = ai_service.calculatePrice(labor);
```

**Optimiert:**
```typescript
interface ExplainableCalculation {
  result: number;
  confidence: 'high' | 'medium' | 'low';
  factors: {
    factor: string;
    impact: number; // in %
    explanation: string;
  }[];
  similarProjects: number; // Anzahl vergleichbarer Projekte in DB
}

// Beispiel-Ausgabe:
{
  result: 2850,
  confidence: 'high',
  factors: [
    {
      factor: 'Raumgröße',
      impact: 35,
      explanation: '24m² entspricht Erfahrungswert für mittlere Bäder'
    },
    {
      factor: 'Materialkosten',
      impact: 45,
      explanation: 'Fliesen Preisklasse "mittel" laut Ihren letzten 5 Projekten'
    },
    {
      factor: 'Zeitaufwand',
      impact: 20,
      explanation: 'Ihre Verlegegeschwindigkeit: 8m²/Tag (Durchschnitt)'
    }
  ],
  similarProjects: 12
}
```

**UI-Konzept:**
```
┌─────────────────────────────────────┐
│ Kalkulation: Badezimmer Fliesen     │
│                                     │
│ Gesamt: 2.850 € ●●●●○ (hohe Sicher.)│
│                                     │
│ Worauf basiert diese Kalkulation?  │
│ ▼ Hauptfaktoren zeigen              │
└─────────────────────────────────────┘

[Ausgeklappt:]
┌─────────────────────────────────────┐
│ Materialkosten (45%): 1.282 €       │
│ → Ihre Preisklasse "mittel"         │
│ → [Anpassen]                        │
│                                     │
│ Raumgröße (35%): 997 €              │
│ → 24m² = Mittelgroßes Bad           │
│ → Vergleich mit 12 ähnl. Projekten  │
│                                     │
│ Zeitaufwand (20%): 571 €            │
│ → Ihre Verlegegeschw.: 8m²/Tag      │
│ → [Korrigieren]                     │
└─────────────────────────────────────┘
```

---

#### 4.2 Vergleichs-Dashboard

**Feature: "Wie kalkuliere ICH normalerweise?"**

```typescript
interface PersonalBenchmark {
  projectType: string;
  userAverage: number;
  suggestedPrice: number;
  deviation: number; // in %
  lastThreeProjects: {
    date: string;
    finalPrice: number;
    profitMargin: number;
  }[];
}
```

**UI-Konzept:**
```
┌─────────────────────────────────────┐
│ Ihre Badezimmer-Projekte            │
│                                     │
│ Vorgeschlagen: 2.850 €              │
│ Ihr Durchschnitt: 2.650 €           │
│                                     │
│ ↑ +7,5% über Ihrem Durchschnitt     │
│                                     │
│ Grund: Hochwertigere Fliesen als    │
│ sonst üblich                        │
│                                     │
│ Letzte 3 Projekte:                  │
│ • März 2024: 2.580 € (23% Marge)   │
│ • Jan 2024:  2.720 € (19% Marge)   │
│ • Nov 2023:  2.650 € (21% Marge)   │
│                                     │
│ [Details] [Übernehmen] [Anpassen]   │
└─────────────────────────────────────┘
```

---

### 🟡 PRIO 2: Training & Lernprozess

#### 4.3 Transparentes Trainings-Interface

**Problem:** Handwerker sollen System trainieren, ohne zu verstehen WAS passiert.

**Lösung: Guided Training mit Erklärung**

```typescript
interface TrainingFeedbackUI {
  originalCalculation: number;
  actualPrice: number;
  difference: number;
  whatSystemLearns: {
    parameter: string;
    oldValue: number;
    newValue: number;
    impact: string; // Laienverständliche Erklärung
  }[];
  affectedFutureCalculations: number; // Wie viele zukünftige Kalks betroffen
}
```

**UI-Konzept:**
```
┌─────────────────────────────────────┐
│ Projekt abschließen & KI trainieren │
│                                     │
│ Kalkulation war: 2.850 €            │
│ Tatsächlich:     3.100 €            │
│ Differenz:       +250 € (+8,7%)     │
│                                     │
│ Was lernt die KI daraus?            │
│                                     │
│ ✓ Zeitaufwand war höher             │
│   Alt: 3 Tage → Neu: 3,5 Tage      │
│   Grund: [Eingabefeld]              │
│   z.B. "Alte Fliesen schwer zu      │
│   entfernen"                        │
│                                     │
│ ✓ Materialkosten anpassen           │
│   Fliesen waren teurer wegen        │
│   [Dropdown: Lieferengpass/Qualität]│
│                                     │
│ ⚠️ Zukünftige Auswirkung:           │
│   Ca. 8 ähnliche Projekte werden    │
│   künftig 5-10% höher kalkuliert    │
│                                     │
│ [Nur Preis übernehmen]              │
│ [Mit Erklärung trainieren]          │
│ [Einmalig, nicht lernen]            │
└─────────────────────────────────────┘
```

**Kritischer Vorteil:**
- Handwerker versteht WARUM System anders kalkulieren wird
- Kann spezifische Faktoren (z.B. Altbau vs. Neubau) markieren
- Behält Kontrolle über "Was wird gelernt"

---

#### 4.4 "Trainings-Logbuch" (Nachvollziehbarkeit)

```
┌─────────────────────────────────────┐
│ Was die KI von Ihnen gelernt hat    │
│                                     │
│ Letzte 30 Tage: 5 Anpassungen       │
│                                     │
│ 15.03.2024: Badezimmer-Fliesen      │
│ → Zeitaufwand +15% bei Altbau       │
│ → Betrifft künftig: Altbau-Projekte │
│ [Rückgängig] [Details]              │
│                                     │
│ 10.03.2024: Küche-Elektrik          │
│ → Materialkosten -8%                │
│ → Sie haben günstigeren Lieferanten │
│ [Rückgängig] [Details]              │
│                                     │
│ [Alle Anpassungen anzeigen]         │
│ [Als Backup exportieren]            │
└─────────────────────────────────────┘
```

---

### 🟢 PRIO 3: Usability-Verbesserungen

#### 4.5 Vereinfachte Eingabe-Modi

**"Schnell-Modus" für routinierte Nutzer:**
```
┌─────────────────────────────────────┐
│ Neues Projekt                       │
│                                     │
│ [Spracheingabe aktiviert 🎤]        │
│                                     │
│ "Badezimmer, 20 Quadratmeter,       │
│  mittlere Fliesen, Altbau"          │
│                                     │
│ → System erkennt:                   │
│   • Projekttyp: Badezimmer          │
│   • Fläche: 20m²                    │
│   • Material: Mittelklasse          │
│   • Besonderheit: Altbau            │
│                                     │
│ [Kalkulation starten]               │
│ [Details anpassen]                  │
└─────────────────────────────────────┘
```

#### 4.6 Mobile-optimierte Ansicht

**Baustellen-Modus:**
```
┌───────────────────┐
│ 🏗️ Baustelle      │
├───────────────────┤
│ Projekt: Bad Müll.│
│                   │
│ Kalkulation:      │
│ 2.850 €           │
│                   │
│ [🎤 Notiz]        │
│ [📸 Foto]         │
│ [📝 Anpassen]     │
│                   │
│ Heute erledigt:   │
│ ▓▓▓▓▓▓░░░░ 60%   │
│                   │
│ [Zeit stempeln]   │
└───────────────────┘
```

---

## 5. IMPLEMENTIERUNGS-ROADMAP

### Phase 1: Vertrauen aufbauen (Wochen 1-4)
- [ ] KI-Erklärungskomponente implementieren
- [ ] Konfidenz-Anzeige (Ampelsystem)
- [ ] Vergleichs-Dashboard zu eigenen Projekten
- [ ] Faktor-basierte Aufschlüsselung

**Erfolgskriterium:** Handwerker kann jedem Kunden erklären, wie Preis zustande kam.

### Phase 2: Training transparent machen (Wochen 5-8)
- [ ] Guided Training Interface
- [ ] "Was lernt die KI"-Vorschau
- [ ] Trainings-Logbuch
- [ ] Rollback-Funktion für Anpassungen

**Erfolgskriterium:** Handwerker versteht, wie seine Eingaben System beeinflussen.

### Phase 3: Usability optimieren (Wochen 9-12)
- [ ] Spracheingabe
- [ ] Mobile-First-Redesign
- [ ] Schnell-Modi für Routineaufgaben
- [ ] Offline-Fähigkeit für Baustelle

**Erfolgskriterium:** System wird auch ohne WLAN auf Baustelle genutzt.

---

## 6. TECHNISCHE OPTIMIERUNGEN (System-Prompt)

### 6.1 Erweiterte Kalkulations-Funktion

**Aktueller Prompt (vereinfacht):**
```
"Kalkuliere Preis basierend auf Projektdaten"
```

**Optimierter Prompt:**
```
Du bist ein erfahrener Handwerksmeister-Assistent. 

AUFGABE: Erstelle eine transparente, nachvollziehbare Kalkulation.

AUSGABEFORMAT:
1. Endergebnis mit Konfidenz-Level
2. Top 3-5 Hauptfaktoren (mit %-Anteil)
3. Vergleich zu ähnlichen Projekten dieses Nutzers
4. Unsicherheiten/Annahmen explizit benennen
5. Empfehlung für manuelle Prüfung (wenn nötig)

WICHTIG:
- Verwende Handwerker-Sprache, keine IT-Begriffe
- Bei Unsicherheit (Konfidenz <70%): Warnung ausgeben
- Erkläre WARUM ein Faktor wichtig ist
- Nenne konkrete Vergleichswerte

BEISPIEL GUTE ERKLÄRUNG:
"Zeitaufwand höher, weil Altbau (basierend auf Ihren letzten 
3 Altbau-Projekten: Ø 15% mehr Zeit als Neubau)"

BEISPIEL SCHLECHTE ERKLÄRUNG:
"Zeitaufwand-Koeffizient: 1.15"
```

### 6.2 Kontext-Anreicherung für bessere Erklärungen

```typescript
// Vor Kalkulation: Relevanten Kontext sammeln
interface CalculationContext {
  userHistory: {
    similarProjects: number;
    averagePrice: number;
    averageMargin: number;
  };
  industryBenchmark: {
    regionalAverage: number;
    priceRange: { min: number; max: number };
  };
  projectRiskFactors: string[]; // z.B. "Altbau", "Denkmalschutz"
}

// An KI übergeben für bessere Begründungen
const explanation = await ai_service.explainCalculation(
  calculation,
  context
);
```

---

## 7. MESSBARE ERFOLGSKRITERIEN

### Vertrauen (quantifizierbar)

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Manuelle Overrides** | <15% der Kalkulationen | System-Logs |
| **Trainings-Feedback** | >80% der abgeschlossenen Projekte | Nutzer-Aktivität |
| **Wiederverwendung** | >60% nutzen "Ähnliche Projekte" | Feature-Usage |
| **Support-Anfragen** | <5% "Verstehe Kalkulation nicht" | Ticket-Analyse |

### Usability (testbar)

| Test | Ziel | Methode |
|------|------|---------|
| **Onboarding-Zeit** | <15 Min bis erste Kalkulation | User-Testing |
| **Aufgaben-Erfolg** | >90% schaffen Testkalkulation ohne Hilfe | Beobachtung |
| **Mobile Nutzung** | >40% der Kalkulationen mobil | Analytics |
| **NPS** | >50 (Net Promoter Score) | Befragung |

---

## 8. RISIKO-MITIGATION

### Typische Stolpersteine

#### Risiko 1: "Zu kompliziert"
**Mitigation:**
- A/B-Test: Vereinfachte vs. detaillierte Ansicht
- Standard = Einfach-Modus
- Details nur auf Anforderung

#### Risiko 2: "Vertraue dem Computer nicht"
**Mitigation:**
- Erste 50 Kalkulationen: Immer Side-by-Side mit manueller Kalkulation zeigen
- Testimonials von anderen Handwerkern
- "Sicherheitsmodus": KI schlägt vor, Handwerker genehmigt

#### Risiko 3: "Zu viel Einarbeitung"
**Mitigation:**
- Video-Tutorials max. 2 Min
- Gamification: "5 Projekte → Bronze-Meister"
- Peer-Support (Handwerker helfen Handwerkern)

---

## 9. KONKRETE UI-MOCKUPS (Code-Basis)

### 9.1 Haupt-Kalkulations-Screen (Erweitert)

```typescript
// src/components/TransparentCalculation.tsx

export function TransparentCalculationView({ 
  calculation, 
  project, 
  userHistory 
}: Props) {
  const [detailLevel, setDetailLevel] = useState<'simple' | 'detailed' | 'expert'>('simple');
  
  return (
    <div className="calculation-view">
      {/* Stufe 1: Schnellübersicht */}
      <Card>
        <ResultHeader 
          amount={calculation.total}
          confidence={calculation.confidence}
        />
        
        <ConfidenceIndicator level={calculation.confidence} />
        
        {calculation.confidence < 0.7 && (
          <WarningBanner>
            ⚠️ Wenig vergleichbare Projekte. Empfehlung: Manuell prüfen.
          </WarningBanner>
        )}
        
        <ComparisonBadge 
          userAverage={userHistory.average}
          current={calculation.total}
        />
      </Card>

      {/* Stufe 2: Hauptfaktoren (ausklappbar) */}
      <Collapsible title="Worauf basiert diese Kalkulation?" defaultOpen={false}>
        <FactorBreakdown factors={calculation.factors} />
        
        <PersonalBenchmark 
          userHistory={userHistory}
          currentProject={project}
        />
      </Collapsible>

      {/* Stufe 3: Volle Details (nur auf Anfrage) */}
      {detailLevel !== 'simple' && (
        <DetailedCalculation calculation={calculation} />
      )}

      {/* Aktionen */}
      <ActionBar>
        <Button onClick={() => acceptCalculation(calculation)}>
          Übernehmen
        </Button>
        <Button variant="secondary" onClick={() => showAdjustment()}>
          Anpassen
        </Button>
        <Button variant="ghost" onClick={() => setDetailLevel('expert')}>
          Alle Details
        </Button>
      </ActionBar>
    </div>
  );
}

// Konfidenz-Indikator Komponente
function ConfidenceIndicator({ level }: { level: number }) {
  const getColor = () => {
    if (level >= 0.8) return 'green';
    if (level >= 0.6) return 'yellow';
    return 'red';
  };
  
  const getText = () => {
    if (level >= 0.8) return 'Hohe Sicherheit';
    if (level >= 0.6) return 'Mittlere Sicherheit';
    return 'Niedrige Sicherheit - Prüfung empfohlen';
  };
  
  return (
    <div className={`confidence-badge ${getColor()}`}>
      <ConfidenceMeter value={level} />
      <span>{getText()}</span>
      <InfoTooltip>
        Basierend auf {Math.floor(level * 20)} ähnlichen Projekten
        in Ihrer Historie
      </InfoTooltip>
    </div>
  );
}

// Faktor-Aufschlüsselung
function FactorBreakdown({ factors }: { factors: Factor[] }) {
  return (
    <div className="factor-list">
      {factors.map(factor => (
        <FactorCard key={factor.name}>
          <FactorHeader>
            <span>{factor.name}</span>
            <span className="impact">{factor.impactPercent}%</span>
          </FactorHeader>
          
          <FactorAmount>{formatCurrency(factor.amount)}</FactorAmount>
          
          <FactorExplanation>{factor.explanation}</FactorExplanation>
          
          {factor.adjustable && (
            <Button size="sm" onClick={() => adjustFactor(factor)}>
              Anpassen
            </Button>
          )}
        </FactorCard>
      ))}
    </div>
  );
}
```

### 9.2 Training-Interface

```typescript
// src/components/TrainingInterface.tsx

export function ProjectCompletionTraining({ 
  project, 
  originalCalculation 
}: Props) {
  const [actualCosts, setActualCosts] = useState<CostBreakdown>(null);
  const [learningImpact, setLearningImpact] = useState<LearningImpact>(null);
  
  useEffect(() => {
    // Automatisch berechnen, was System lernen würde
    if (actualCosts) {
      const impact = calculateLearningImpact(
        originalCalculation,
        actualCosts,
        project
      );
      setLearningImpact(impact);
    }
  }, [actualCosts]);
  
  return (
    <Dialog title="Projekt abschließen & System trainieren">
      {/* Schritt 1: Tatsächliche Kosten eingeben */}
      <Section>
        <h3>Was hat das Projekt tatsächlich gekostet?</h3>
        
        <ComparisonTable>
          <thead>
            <tr>
              <th>Position</th>
              <th>Kalkuliert</th>
              <th>Tatsächlich</th>
              <th>Differenz</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Material</td>
              <td>{originalCalculation.material}</td>
              <td>
                <Input 
                  type="number"
                  value={actualCosts?.material}
                  onChange={(e) => updateActualCosts('material', e.target.value)}
                />
              </td>
              <td className={getDiffClass(...)}>
                {calculateDiff(...)}
              </td>
            </tr>
            {/* Weitere Positionen */}
          </tbody>
        </ComparisonTable>
      </Section>

      {/* Schritt 2: Erklärung erfragen */}
      {actualCosts && (
        <Section>
          <h3>Was war anders als erwartet?</h3>
          
          {learningImpact.significantDifferences.map(diff => (
            <DifferenceExplanation key={diff.category}>
              <DiffHeader>
                <strong>{diff.category}</strong>: {diff.percent}% {diff.direction}
              </DiffHeader>
              
              <RadioGroup
                label="Warum war das so?"
                options={[
                  { value: 'oneTime', label: 'Einmalig (nicht üblich)' },
                  { value: 'projectType', label: 'Typisch für diese Projektart' },
                  { value: 'myWorkStyle', label: 'So arbeite ich generell' }
                ]}
                onChange={(v) => setDifferenceReason(diff.category, v)}
              />
              
              <TextArea
                placeholder="Optionale Notiz für später..."
                onChange={(v) => setDifferenceNote(diff.category, v)}
              />
            </DifferenceExplanation>
          ))}
        </Section>
      )}

      {/* Schritt 3: Lernauswirkung zeigen */}
      {learningImpact && (
        <Section className="impact-preview">
          <h3>Was lernt die KI daraus?</h3>
          
          <ImpactList>
            {learningImpact.changes.map(change => (
              <ImpactItem key={change.parameter}>
                <ChangeIcon type={change.type} />
                <ChangeDescription>
                  <strong>{change.parameterLabel}</strong>
                  <br />
                  {change.oldValue} → {change.newValue}
                  <br />
                  <small>{change.explanation}</small>
                </ChangeDescription>
                
                <Toggle
                  label="Übernehmen?"
                  defaultChecked={true}
                  onChange={(checked) => toggleLearning(change, checked)}
                />
              </ImpactItem>
            ))}
          </ImpactList>
          
          <FutureImpactWarning>
            ⚠️ Diese Änderungen betreffen ca. {learningImpact.affectedFutureProjects} 
            zukünftige Kalkulationen vom Typ "{project.type}".
          </FutureImpactWarning>
        </Section>
      )}

      {/* Aktionen */}
      <DialogActions>
        <Button variant="secondary" onClick={saveWithoutLearning}>
          Nur Kosten speichern
        </Button>
        <Button variant="primary" onClick={saveAndTrain}>
          Speichern & KI trainieren
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

---

## 10. ZUSAMMENFASSUNG & NÄCHSTE SCHRITTE

### ✅ Bestehendes System hat solide Basis
- Grundstruktur ist vorhanden
- Manuelle Overrides möglich
- Detaillierte Berechnungen verfügbar

### ❌ Kritische Lücken identifiziert
1. **Keine Erklärung WARUM** KI zu Ergebnis kam
2. **Keine Vergleichbarkeit** zu eigenen Projekten
3. **Training ist Black Box**
4. **UI zu technisch** für Handwerker

### 🎯 Priorisierte Lösungen

**Quick Wins (1-2 Wochen):**
- Konfidenz-Indikator (Ampelsystem)
- Faktor-Aufschlüsselung mit %-Anteilen
- Vergleich zu Nutzer-Durchschnitt

**Vertrauensbildend (4 Wochen):**
- Vollständige Erklärungskomponente
- Trainings-Interface mit Vorschau
- Trainings-Logbuch

**Usability-Optimierung (8 Wochen):**
- Mobile-First Redesign
- Spracheingabe
- Offline-Modus

### 📋 Empfohlene nächste Schritte

1. **User Research** (1 Woche)
   - 5-10 Handwerker interviewen
   - Prototyp des Erklärungs-Interfaces testen
   - Kritische Akzeptanzkriterien validieren

2. **MVP Implementation** (2 Wochen)
   - Konfidenz-System
   - Basis-Erklärungskomponente
   - Vergleichs-Dashboard

3. **Alpha-Test** (2 Wochen)
   - 3-5 freundliche Handwerker
   - Intensive Begleitung
   - Iteratives Feedback

4. **Beta-Rollout** (4 Wochen)
   - Erweiterte Nutzergruppe
   - Monitoring der Akzeptanz-Metriken
   - Support-Kanal mit schneller Reaktion

---

**Kritischer Erfolgsfaktor:**  
Handwerker müssen das Gefühl haben, dass **sie die KI trainieren** (und nicht umgekehrt). Das System ist ein Assistent, der von ihrer Expertise lernt – nicht ein Besserwisser, der vorgibt, wie kalkuliert werden muss.