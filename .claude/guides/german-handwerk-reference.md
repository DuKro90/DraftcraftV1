# German Handwerk Reference Guide

**Version:** 1.0.0
**Letzte Aktualisierung:** November 27, 2025

---

## 🇩🇪 Vollständige Handwerks-Terminologie & Faktoren

Dieses Dokument enthält vollständige Listen und Referenzen für deutsche Handwerks-spezifische Begriffe und Preisfaktoren.

**Verwende dieses Dokument wenn:**
- Du mit Holzarten-Preisfaktoren arbeitest
- Komplexitäts- oder Oberflächenfaktoren implementierst
- Deutsche Fachbegriffe für NER/OCR validierst
- Preisberechnungen mit Handwerks-Spezifika durchführst

---

## 🌳 Holzarten & Preisfaktoren

### Hartholz (Laubhölzer)

```python
HARTHOLZ_ARTEN = {
    'eiche': {
        'kategorie': 'hartholz',
        'faktor': 1.3,
        'dichte_kg_m3': 720,
        'eigenschaften': ['robust', 'langlebig', 'witterungsbeständig'],
        'typische_verwendung': ['Möbel', 'Parkett', 'Treppen', 'Außenbau']
    },
    'buche': {
        'kategorie': 'hartholz',
        'faktor': 1.2,
        'dichte_kg_m3': 720,
        'eigenschaften': ['hart', 'verschleißfest', 'elastisch'],
        'typische_verwendung': ['Möbel', 'Parkett', 'Treppen', 'Werkzeuggriffe']
    },
    'esche': {
        'kategorie': 'hartholz',
        'faktor': 1.25,
        'dichte_kg_m3': 690,
        'eigenschaften': ['zäh', 'elastisch', 'stoßfest'],
        'typische_verwendung': ['Sportgeräte', 'Werkzeugstiele', 'Möbel', 'Treppen']
    },
    'ahorn': {
        'kategorie': 'hartholz',
        'faktor': 1.2,
        'dichte_kg_m3': 630,
        'eigenschaften': ['hell', 'homogen', 'verschleißfest'],
        'typische_verwendung': ['Möbel', 'Parkett', 'Musikinstrumente', 'Küchenarbeitsplatten']
    },
    'nussbaum': {
        'kategorie': 'hartholz',
        'faktor': 1.5,
        'dichte_kg_m3': 640,
        'eigenschaften': ['edel', 'dekorativ', 'dunkel'],
        'typische_verwendung': ['Furniere', 'Möbel', 'Vertäfelungen', 'Drechselarbeiten']
    },
    'kirschbaum': {
        'kategorie': 'hartholz',
        'faktor': 1.35,
        'dichte_kg_m3': 600,
        'eigenschaften': ['rötlich', 'fein', 'dekorativ'],
        'typische_verwendung': ['Möbel', 'Vertäfelungen', 'Drechselarbeiten']
    },
    'birke': {
        'kategorie': 'hartholz',
        'faktor': 1.1,
        'dichte_kg_m3': 650,
        'eigenschaften': ['hell', 'zäh', 'elastisch'],
        'typische_verwendung': ['Sperrholz', 'Möbel', 'Parkett']
    }
}
```

### Weichholz (Nadelhölzer)

```python
WEICHHOLZ_ARTEN = {
    'fichte': {
        'kategorie': 'weichholz',
        'faktor': 0.8,
        'dichte_kg_m3': 470,
        'eigenschaften': ['leicht', 'harzreich', 'elastisch'],
        'typische_verwendung': ['Konstruktionsholz', 'Dachstühle', 'Möbel', 'Verpackungen']
    },
    'kiefer': {
        'kategorie': 'weichholz',
        'faktor': 0.9,
        'dichte_kg_m3': 520,
        'eigenschaften': ['harzreich', 'rustikal', 'dauerhaft'],
        'typische_verwendung': ['Möbel', 'Fußböden', 'Fenster', 'Türen']
    },
    'tanne': {
        'kategorie': 'weichholz',
        'faktor': 0.85,
        'dichte_kg_m3': 450,
        'eigenschaften': ['leicht', 'harzfrei', 'geruchlos'],
        'typische_verwendung': ['Konstruktionsholz', 'Innenausbau', 'Möbel']
    },
    'lärche': {
        'kategorie': 'weichholz',
        'faktor': 1.0,
        'dichte_kg_m3': 590,
        'eigenschaften': ['hart', 'witterungsbeständig', 'dauerhaft'],
        'typische_verwendung': ['Außenbau', 'Fenster', 'Fassaden', 'Gartenmöbel']
    },
    'douglasie': {
        'kategorie': 'weichholz',
        'faktor': 0.95,
        'dichte_kg_m3': 550,
        'eigenschaften': ['fest', 'elastisch', 'dauerhaft'],
        'typische_verwendung': ['Konstruktionsholz', 'Fenster', 'Türen', 'Terrassen']
    },
    'zirbelkiefer': {
        'kategorie': 'weichholz',
        'faktor': 1.15,
        'dichte_kg_m3': 400,
        'eigenschaften': ['duftend', 'leicht', 'beruhigend'],
        'typische_verwendung': ['Möbel', 'Wandverkleidungen', 'Schlafzimmermöbel']
    }
}
```

---

## 🔨 Komplexitätsfaktoren

### Bearbeitungstechniken

```python
KOMPLEXITÄTS_FAKTOREN = {
    # Basis-Bearbeitung
    'gesägt': {
        'faktor': 1.0,
        'arbeitszeit_std_pro_m': 0.5,
        'schwierigkeitsgrad': 'einfach',
        'werkzeug': ['Säge', 'Tischkreissäge', 'Formatkreissäge']
    },
    'gehobelt': {
        'faktor': 1.05,
        'arbeitszeit_std_pro_m': 0.8,
        'schwierigkeitsgrad': 'einfach',
        'werkzeug': ['Hobel', 'Abrichthobelmaschine', 'Dickenhobelmaschine']
    },
    'geschliffen': {
        'faktor': 1.1,
        'arbeitszeit_std_pro_m': 1.0,
        'schwierigkeitsgrad': 'einfach',
        'werkzeug': ['Schleifmaschine', 'Bandschleifer', 'Exzenterschleifer']
    },

    # Fortgeschrittene Bearbeitung
    'gefräst': {
        'faktor': 1.15,
        'arbeitszeit_std_pro_m': 1.5,
        'schwierigkeitsgrad': 'mittel',
        'werkzeug': ['Fräsmaschine', 'CNC-Fräse', 'Oberfräse']
    },
    'gedrechselt': {
        'faktor': 1.25,
        'arbeitszeit_std_pro_stuck': 2.0,
        'schwierigkeitsgrad': 'mittel',
        'werkzeug': ['Drechselbank', 'Drechseleisen']
    },
    'gestemmt': {
        'faktor': 1.2,
        'arbeitszeit_std_pro_verbindung': 1.0,
        'schwierigkeitsgrad': 'mittel',
        'werkzeug': ['Stechbeitel', 'Stemmeisen', 'Kettenstemmer']
    },
    'gebogen': {
        'faktor': 1.3,
        'arbeitszeit_std_pro_teil': 3.0,
        'schwierigkeitsgrad': 'hoch',
        'werkzeug': ['Biegepresse', 'Dampfkammer', 'Schablonen']
    },

    # Künstlerische Bearbeitung
    'geschnitzt': {
        'faktor': 1.5,
        'arbeitszeit_std_pro_dm2': 4.0,
        'schwierigkeitsgrad': 'hoch',
        'werkzeug': ['Schnitzeisen', 'Schnitzwerkzeug-Set']
    },
    'hand_geschnitzt': {
        'faktor': 2.0,
        'arbeitszeit_std_pro_dm2': 8.0,
        'schwierigkeitsgrad': 'sehr_hoch',
        'werkzeug': ['Handschnitzeisen', 'Spezialeisen'],
        'meisterarbeit': True
    },
    'intarsien': {
        'faktor': 2.5,
        'arbeitszeit_std_pro_dm2': 12.0,
        'schwierigkeitsgrad': 'sehr_hoch',
        'werkzeug': ['Furniersäge', 'Intarsienhobel', 'Präzisionswerkzeug'],
        'meisterarbeit': True
    },

    # Spezielle Verbindungen
    'zinken': {
        'faktor': 1.4,
        'arbeitszeit_std_pro_verbindung': 2.5,
        'schwierigkeitsgrad': 'hoch',
        'werkzeug': ['Schwalbenschwanzzinken-Lehre', 'Säge', 'Stechbeitel']
    },
    'schlitz_und_zapfen': {
        'faktor': 1.35,
        'arbeitszeit_std_pro_verbindung': 2.0,
        'schwierigkeitsgrad': 'mittel-hoch',
        'werkzeug': ['Zapfenschneidemaschine', 'Kettenstemmer']
    }
}
```

### Zusätzliche Komplexitäts-Multiplikatoren

```python
KOMPLEXITÄTS_MULTIPLIKATOREN = {
    'präzisionsarbeit': 1.15,       # Toleranzen < 0.1mm
    'restaurierung': 1.3,            # Historische Techniken
    'einzelanfertigung': 1.2,        # Keine Serienproduktion
    'sondermaße': 1.1,               # Abweichend von Standard
    'maßanfertigung': 1.25,          # Individuelle Maße
    'curved_surfaces': 1.4,          # Gekrümmte Oberflächen
    'mehrfarbig': 1.2,               # Verschiedene Holzarten kombiniert
}
```

---

## 🎨 Oberflächenbearbeitungs-Faktoren

### Standard-Oberflächen

```python
OBERFLÄCHEN_FAKTOREN = {
    'naturbelassen': {
        'faktor': 1.0,
        'arbeitszeit_std_pro_m2': 0.0,
        'materialkosten_eur_pro_m2': 0.0,
        'eigenschaften': ['natürlich', 'unbehandelt'],
        'schutz': 'minimal',
        'haltbarkeit_jahre': 2
    },
    'gewachst': {
        'faktor': 1.08,
        'arbeitszeit_std_pro_m2': 0.5,
        'materialkosten_eur_pro_m2': 3.50,
        'eigenschaften': ['natürlich', 'matt', 'offenporig'],
        'schutz': 'niedrig',
        'haltbarkeit_jahre': 3,
        'erneuerung_nötig': True
    },
    'geölt': {
        'faktor': 1.10,
        'arbeitszeit_std_pro_m2': 1.0,
        'materialkosten_eur_pro_m2': 5.00,
        'eigenschaften': ['natürlich', 'matt-seidig', 'offenporig'],
        'schutz': 'mittel',
        'haltbarkeit_jahre': 5,
        'erneuerung_nötig': True,
        'typische_produkte': ['Hartöl', 'Naturöl', 'Leinöl']
    },
    'gebeizt': {
        'faktor': 1.12,
        'arbeitszeit_std_pro_m2': 1.5,
        'materialkosten_eur_pro_m2': 6.00,
        'eigenschaften': ['farblich verändert', 'holzstruktur sichtbar'],
        'schutz': 'niedrig',
        'zusatzbehandlung_nötig': True,
        'typische_farben': ['nussbaum', 'eiche', 'mahagoni', 'weiß', 'grau']
    },
    'lackiert': {
        'faktor': 1.15,
        'arbeitszeit_std_pro_m2': 2.0,
        'materialkosten_eur_pro_m2': 8.00,
        'eigenschaften': ['geschlossen', 'glänzend oder matt', 'robust'],
        'schutz': 'hoch',
        'haltbarkeit_jahre': 10,
        'schichten': 2-3,
        'zwischenschliff': True
    },
    'lasiert': {
        'faktor': 1.13,
        'arbeitszeit_std_pro_m2': 1.5,
        'materialkosten_eur_pro_m2': 7.00,
        'eigenschaften': ['offenporig', 'holzstruktur sichtbar', 'farblich getönt'],
        'schutz': 'mittel-hoch',
        'haltbarkeit_jahre': 7,
        'typisch_für': ['Außenanwendungen', 'Gartenmöbel']
    },

    # Premium-Oberflächen
    'french_polish': {
        'faktor': 1.5,
        'arbeitszeit_std_pro_m2': 8.0,
        'materialkosten_eur_pro_m2': 15.00,
        'eigenschaften': ['hochglänzend', 'traditionell', 'handpoliert'],
        'schutz': 'mittel',
        'haltbarkeit_jahre': 15,
        'meisterarbeit': True,
        'typisch_für': ['Antiquitäten', 'Restaurierung', 'Musikinstrumente']
    },
    'klavierlack': {
        'faktor': 1.6,
        'arbeitszeit_std_pro_m2': 12.0,
        'materialkosten_eur_pro_m2': 25.00,
        'eigenschaften': ['hochglänzend', 'spiegelnd', 'mehrschichtig'],
        'schutz': 'sehr_hoch',
        'haltbarkeit_jahre': 20,
        'schichten': 8-12,
        'zwischenschliff': True,
        'endpolitur': True,
        'meisterarbeit': True
    },
    'pulverbeschichtet': {
        'faktor': 1.3,
        'arbeitszeit_std_pro_m2': 2.5,
        'materialkosten_eur_pro_m2': 18.00,
        'eigenschaften': ['extrem robust', 'gleichmäßig', 'farbbeständig'],
        'schutz': 'sehr_hoch',
        'haltbarkeit_jahre': 15,
        'typisch_für': ['Metallteile', 'Außenanwendungen']
    }
}
```

---

## 📏 Deutsche Mengeneinheiten

### Standardeinheiten im Handwerk

```python
DEUTSCHE_EINHEITEN = {
    # Längenmaße
    'mm': {
        'name': 'Millimeter',
        'typ': 'länge',
        'faktor_zu_meter': 0.001,
        'verwendung': ['Präzisionsmaße', 'Materialstärke']
    },
    'cm': {
        'name': 'Zentimeter',
        'typ': 'länge',
        'faktor_zu_meter': 0.01,
        'verwendung': ['Kleinteile', 'Möbelmaße']
    },
    'm': {
        'name': 'Meter',
        'typ': 'länge',
        'faktor_zu_meter': 1.0,
        'verwendung': ['Standard-Längenmaß']
    },
    'lfm': {
        'name': 'Laufende Meter',
        'typ': 'länge',
        'faktor_zu_meter': 1.0,
        'verwendung': ['Profile', 'Leisten', 'Kabel', 'Rohre'],
        'besonderheit': 'Kontinuierliche Länge ohne Bruch'
    },

    # Flächenmaße
    'm²': {
        'name': 'Quadratmeter',
        'typ': 'fläche',
        'verwendung': ['Flächen', 'Wände', 'Böden', 'Platten']
    },
    'dm²': {
        'name': 'Quadratdezimeter',
        'typ': 'fläche',
        'faktor_zu_m2': 0.01,
        'verwendung': ['Kleine Flächen', 'Schnitzereien']
    },

    # Volumen
    'm³': {
        'name': 'Kubikmeter',
        'typ': 'volumen',
        'verwendung': ['Schnittholz', 'Beton', 'Schüttgut']
    },
    'fm': {
        'name': 'Festmeter',
        'typ': 'volumen',
        'entspricht': '1 m³',
        'verwendung': ['Holzhandel', 'Rundholz']
    },
    'rm': {
        'name': 'Raummeter',
        'typ': 'volumen',
        'faktor_zu_fm': 0.7,
        'verwendung': ['Brennholz gestapelt']
    },
    'srm': {
        'name': 'Schüttraummeter',
        'typ': 'volumen',
        'faktor_zu_fm': 0.5,
        'verwendung': ['Brennholz geschüttet']
    },

    # Gewicht
    'kg': {
        'name': 'Kilogramm',
        'typ': 'gewicht',
        'verwendung': ['Materialgewicht', 'Bauteile']
    },
    't': {
        'name': 'Tonne',
        'typ': 'gewicht',
        'faktor_zu_kg': 1000,
        'verwendung': ['Schüttgut', 'große Mengen']
    },

    # Stückzahlen
    'Stk': {
        'name': 'Stück',
        'typ': 'anzahl',
        'verwendung': ['Einzelteile', 'Schrauben', 'Beschläge']
    },
    'Paar': {
        'name': 'Paar',
        'typ': 'anzahl',
        'faktor_zu_stuck': 2,
        'verwendung': ['Scharniere', 'Türgriffe']
    },
    'Satz': {
        'name': 'Satz',
        'typ': 'anzahl',
        'verwendung': ['Zusammengehörige Teile'],
        'besonderheit': 'Anzahl im Satz variabel'
    },

    # Arbeitszeit
    'h': {
        'name': 'Stunden',
        'typ': 'arbeitszeit',
        'verwendung': ['Arbeitsstunden', 'Projektdauer']
    },
    'PT': {
        'name': 'Personentage',
        'typ': 'arbeitszeit',
        'faktor_zu_h': 8,
        'verwendung': ['Projektplanung']
    }
}
```

---

## 💰 Mehrwertsteuer & Preisstrukturen

### MwSt-Sätze Deutschland

```python
MWST_SÄTZE = {
    'standard': {
        'prozent': 19,
        'gilt_für': ['Handwerksleistungen', 'Möbel', 'Bauteile', 'Dienstleistungen']
    },
    'ermäßigt': {
        'prozent': 7,
        'gilt_für': ['Bücher', 'Lebensmittel', 'ÖPNV'],
        'gilt_NICHT_für': ['Handwerk', 'Bau']
    }
}

# Beispiel Preisberechnung
def berechne_brutto_preis(netto: Decimal, mwst_satz: int = 19) -> Decimal:
    """
    Berechnet Bruttopreis aus Nettopreis.

    Args:
        netto: Nettopreis in EUR
        mwst_satz: MwSt-Satz in Prozent (default: 19)

    Returns:
        Bruttopreis in EUR

    Example:
        >>> berechne_brutto_preis(Decimal('100.00'))
        Decimal('119.00')
    """
    return netto * (1 + Decimal(mwst_satz) / 100)
```

---

## 🏗️ GAEB-Spezifische Begriffe

### GAEB Leistungsverzeichnis Struktur

```python
GAEB_BEGRIFFE = {
    'ordnungszahl': {
        'format': 'XX.XXX',
        'beispiel': '01.001',
        'bedeutung': 'Eindeutige Position im LV'
    },
    'kurztext': {
        'max_zeichen': 50,
        'bedeutung': 'Kurzbeschreibung der Leistung'
    },
    'langtext': {
        'bedeutung': 'Detaillierte Leistungsbeschreibung',
        'kann_enthalten': ['Materialangaben', 'Ausführungshinweise', 'Normen']
    },
    'menge': {
        'typ': 'Decimal',
        'nachkommastellen': 3,
        'beispiel': Decimal('25.500')
    },
    'einheitspreis': {
        'typ': 'Decimal',
        'nachkommastellen': 2,
        'währung': 'EUR'
    },
    'gesamtpreis': {
        'berechnung': 'menge × einheitspreis',
        'rundung': 2
    }
}
```

### VOB-Vergabearten

```python
VOB_VERGABEARTEN = {
    'VOB/A': {
        'titel': 'Allgemeine Bestimmungen für die Vergabe von Bauleistungen',
        'gilt_für': 'öffentliche Auftraggeber',
        'schwellenwerte': {
            'national': 215000,  # EUR
            'eu_weit': 5382000   # EUR
        }
    },
    'VOB/B': {
        'titel': 'Allgemeine Vertragsbedingungen für die Ausführung von Bauleistungen',
        'gilt_für': 'Vertragsbeziehung zwischen Auftraggeber und Auftragnehmer'
    },
    'VOB/C': {
        'titel': 'Allgemeine Technische Vertragsbedingungen für Bauleistungen',
        'enthält': 'DIN-Normen für Gewerke'
    }
}
```

---

## 📚 Compliance & Normen

### DSGVO-relevante Datenfelder

```python
DSGVO_KATEGORIEN = {
    'personenbezogene_daten': [
        'kunde_name',
        'kunde_adresse',
        'kunde_telefon',
        'kunde_email',
        'ansprechpartner_name'
    ],
    'nicht_personenbezogen': [
        'projekt_beschreibung',
        'material_liste',
        'preise',
        'mengen',
        'holzarten'
    ],
    'aufbewahrungsfristen': {
        'geschäftliche_korrespondenz': 6,  # Jahre (HGB §257)
        'buchungsbelege': 10,              # Jahre (AO §147)
        'lohn_gehalt': 6,                  # Jahre
        'bau_dokumente': 5                 # Jahre (VOB/B)
    }
}
```

---

## 🔧 NER Entity Labels für deutsche Handwerks-Dokumente

### Empfohlene spaCy Entity Labels

```python
HANDWERK_NER_LABELS = {
    'HOLZART': {
        'beispiele': ['Eiche', 'Buche', 'Fichte', 'Kiefer'],
        'training_priorität': 'hoch'
    },
    'OBERFLÄCHE': {
        'beispiele': ['lackiert', 'geölt', 'gewachst', 'naturbelassen'],
        'training_priorität': 'hoch'
    },
    'KOMPLEXITÄT': {
        'beispiele': ['gedrechselt', 'geschnitzt', 'gefräst'],
        'training_priorität': 'mittel'
    },
    'MASSE': {
        'beispiele': ['1,5 m', '25 cm', '10 mm'],
        'pattern': r'\d+[,.]?\d*\s*(mm|cm|m|lfm)',
        'training_priorität': 'hoch'
    },
    'MENGE': {
        'beispiele': ['5 Stk', '10 m²', '2,5 m³'],
        'pattern': r'\d+[,.]?\d*\s*(Stk|m²|m³|kg)',
        'training_priorität': 'hoch'
    },
    'PREIS': {
        'beispiele': ['1.250,50 €', '€ 2.450,00'],
        'pattern': r'(?:€\s*)?\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€?',
        'training_priorität': 'kritisch'
    },
    'FIRMA': {
        'beispiele': ['Schreinerei Müller GmbH', 'Tischlerei Schmidt'],
        'training_priorität': 'hoch'
    },
    'GAEB_POSITION': {
        'beispiele': ['01.001', '02.150'],
        'pattern': r'\d{2}\.\d{3}',
        'training_priorität': 'mittel'
    }
}
```

---

## 🌍 Regionale Unterschiede

### Norddeutschland vs. Süddeutschland

```python
REGIONALE_BEGRIFFE = {
    'tischler': {
        'region': 'Norddeutschland',
        'synonym': 'schreiner',
        'region_synonym': 'Süddeutschland & Österreich'
    },
    'leisten': {
        'süddeutsch': 'Leiste',
        'norddeutsch': 'Profil',
        'österreichisch': 'Staffel'
    },
    'fußleiste': {
        'synonym': ['Sockelleiste', 'Scheuerleiste'],
        'österreichisch': 'Fußbodenprofil'
    }
}
```

---

**Dieses Dokument wird bei Bedarf erweitert. Letzte Aktualisierung: 2025-11-27**
