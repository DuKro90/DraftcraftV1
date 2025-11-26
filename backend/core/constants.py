"""
Core Constants for DraftCraft - Manufacturing & Pricing Data
Schicht 1: Fertigungsspezifische Kennzahlen (zentral)

Diese Daten sind nicht benutzerkonfigurierbar und bilden die Basis
für alle Preiskalkulationen.
"""

from decimal import Decimal

# ============================================================================
# MATERIAL SPECIFICATIONS
# Fertigungsspezifische Material-Daten
# ============================================================================

GERMAN_WOOD_TYPES = {
    'eiche': {
        'german_name': 'Eiche (Massivholz)',
        'english_name': 'Oak (solid wood)',
        'category': 'hardwood',
        'base_time_hours_per_sqm': Decimal('0.50'),
        'base_material_cost_per_sqm': Decimal('45.00'),  # Durchschnitt
        'density': Decimal('0.75'),  # g/cm³
        'workability': 'medium',
        'surface_quality': 'high',
        'notes': 'Deutsches Eichenholz, stabil und langlebig',
        'difficulty': 'medium',
    },
    'buche': {
        'german_name': 'Buche (Massivholz)',
        'english_name': 'Beech (solid wood)',
        'category': 'hardwood',
        'base_time_hours_per_sqm': Decimal('0.48'),
        'base_material_cost_per_sqm': Decimal('38.00'),
        'density': Decimal('0.70'),
        'workability': 'medium',
        'surface_quality': 'high',
        'notes': 'Feinporiges Holz, gute Oberflächenqualität',
        'difficulty': 'medium',
    },
    'kiefer': {
        'german_name': 'Kiefer (Nadelholz)',
        'english_name': 'Pine (softwood)',
        'category': 'softwood',
        'base_time_hours_per_sqm': Decimal('0.35'),
        'base_material_cost_per_sqm': Decimal('22.00'),
        'density': Decimal('0.51'),
        'workability': 'easy',
        'surface_quality': 'medium',
        'notes': 'Kostengünstiges Nadelholz, weich',
        'difficulty': 'easy',
    },
    'fichte': {
        'german_name': 'Fichte (Nadelholz)',
        'english_name': 'Spruce (softwood)',
        'category': 'softwood',
        'base_time_hours_per_sqm': Decimal('0.30'),
        'base_material_cost_per_sqm': Decimal('18.00'),
        'density': Decimal('0.47'),
        'workability': 'easy',
        'surface_quality': 'low',
        'notes': 'Sehr weiches, günstiges Holz',
        'difficulty': 'easy',
    },
    'ahorn': {
        'german_name': 'Ahorn (Massivholz)',
        'english_name': 'Maple (solid wood)',
        'category': 'hardwood',
        'base_time_hours_per_sqm': Decimal('0.55'),
        'base_material_cost_per_sqm': Decimal('65.00'),
        'density': Decimal('0.75'),
        'workability': 'hard',
        'surface_quality': 'very_high',
        'notes': 'Hartes, edles Holz mit schöner Maserung',
        'difficulty': 'hard',
    },
    'nussbaum': {
        'german_name': 'Nussbaum (Massivholz)',
        'english_name': 'Walnut (solid wood)',
        'category': 'hardwood',
        'base_time_hours_per_sqm': Decimal('0.60'),
        'base_material_cost_per_sqm': Decimal('95.00'),
        'density': Decimal('0.67'),
        'workability': 'medium',
        'surface_quality': 'very_high',
        'notes': 'Edles Holz mit dunkler Färbung',
        'difficulty': 'hard',
    },
    'erle': {
        'german_name': 'Erle',
        'english_name': 'Alder',
        'category': 'softwood',
        'base_time_hours_per_sqm': Decimal('0.32'),
        'base_material_cost_per_sqm': Decimal('20.00'),
        'density': Decimal('0.55'),
        'workability': 'easy',
        'surface_quality': 'low',
        'notes': 'Günstiges, weiches Nadelholz',
        'difficulty': 'easy',
    },
    'mdf': {
        'german_name': 'MDF-Platte',
        'english_name': 'MDF board',
        'category': 'engineered_wood',
        'base_time_hours_per_sqm': Decimal('0.25'),
        'base_material_cost_per_sqm': Decimal('12.00'),
        'density': Decimal('0.75'),
        'workability': 'very_easy',
        'surface_quality': 'medium',
        'notes': 'Mitteldichte Faserplatte, kostengünstig',
        'difficulty': 'very_easy',
    },
    'sperrholz': {
        'german_name': 'Sperrholz',
        'english_name': 'Plywood',
        'category': 'engineered_wood',
        'base_time_hours_per_sqm': Decimal('0.30'),
        'base_material_cost_per_sqm': Decimal('15.00'),
        'density': Decimal('0.70'),
        'workability': 'easy',
        'surface_quality': 'low',
        'notes': 'Sperrholz für stabile Konstruktionen',
        'difficulty': 'easy',
    },
}

# ============================================================================
# COMPLEXITY FACTORS
# Arbeitszeitfaktoren für verschiedene Bearbeitungstechniken
# ============================================================================

COMPLEXITY_FACTORS = {
    'simple': {
        'time_factor': Decimal('1.0'),
        'german_name': 'Einfache Ausführung',
        'english_name': 'Simple execution',
        'description': 'Schlicht, ohne Verzierungen oder komplexe Bearbeitungen',
        'examples': ['Regale', 'einfache Schränke', 'Tische'],
    },
    'turned': {
        'time_factor': Decimal('1.25'),
        'german_name': 'Gedreht',
        'english_name': 'Turned/Lathe work',
        'description': 'Rund gedrehte Elemente (z.B. Säulen, Tischbeine)',
        'examples': ['Holzstühle', 'Säulen', 'Treppengeländer', 'Drehteile'],
    },
    'milled': {
        'time_factor': Decimal('1.15'),
        'german_name': 'Gefräst',
        'english_name': 'Milled/Routed',
        'description': 'Feinbearbeitung mit Fräsmaschine (Profile, Nuten, etc.)',
        'examples': ['Profilleisten', 'Verzierungen', 'Verbindungen'],
    },
    'carved': {
        'time_factor': Decimal('1.50'),
        'german_name': 'Geschnitzt',
        'english_name': 'Carved',
        'description': 'Von Hand geschnitzte Verzierungen',
        'examples': ['Ornamente', 'Relief-Arbeiten', 'Figuren'],
    },
    'hand_carved': {
        'time_factor': Decimal('2.00'),
        'german_name': 'Handgeschnitzt',
        'english_name': 'Hand carved (art)',
        'description': 'Kunsthandwerkliche, individuelle Schnitzarbeiten',
        'examples': ['Kunstobjekte', 'Unikate', 'Spezialanfertigungen'],
    },
    'inlaid': {
        'time_factor': Decimal('1.80'),
        'german_name': 'Intarsia/Einlegearbeit',
        'english_name': 'Inlaid/Marquetry',
        'description': 'Verschiedene Hölzer eingelegt (Marketerien, Dekorelemente)',
        'examples': ['Marketerien', 'Dekorelemete', 'farbliche Muster'],
    },
    'veneered': {
        'time_factor': Decimal('1.35'),
        'german_name': 'Furniert',
        'english_name': 'Veneered',
        'description': 'Mit Furnierholz veredelt (dünne Holzschichten)',
        'examples': ['Furnierte Möbel', 'hochwertige Oberflächen'],
    },
}

# ============================================================================
# SURFACE FINISH FACTORS
# Oberflächenbehandlungs-Faktoren und Materialzuschläge
# ============================================================================

SURFACE_FACTORS = {
    'natural': {
        'time_factor': Decimal('1.0'),
        'german_name': 'Naturbelassen',
        'english_name': 'Natural/Untreated',
        'description': 'Keine Oberflächenbehandlung, nur geschliffen',
        'material_surcharge': Decimal('0.0'),
    },
    'waxed': {
        'time_factor': Decimal('1.08'),
        'german_name': 'Gewachst',
        'english_name': 'Waxed',
        'description': 'Mit Hartwachs oder Naturwachs behandelt',
        'material_surcharge': Decimal('8.50'),  # € pro m²
    },
    'oiled': {
        'time_factor': Decimal('1.10'),
        'german_name': 'Geölt',
        'english_name': 'Oiled',
        'description': 'Mit Naturöl (Leinöl, Hartöl) behandelt',
        'material_surcharge': Decimal('12.00'),
    },
    'stained': {
        'time_factor': Decimal('1.12'),
        'german_name': 'Gebeizt',
        'english_name': 'Stained',
        'description': 'Mit Holzbeize gefärbt',
        'material_surcharge': Decimal('6.50'),
    },
    'varnished': {
        'time_factor': Decimal('1.08'),
        'german_name': 'Lackiert (Klarlack)',
        'english_name': 'Varnished (clear)',
        'description': 'Mit transparentem Klarlack versiegelt',
        'material_surcharge': Decimal('10.00'),
    },
    'painted': {
        'time_factor': Decimal('1.15'),
        'german_name': 'Lackiert (Farblack)',
        'english_name': 'Painted',
        'description': 'Mit farbigem Farblack bemalt',
        'material_surcharge': Decimal('15.00'),
    },
    'polished': {
        'time_factor': Decimal('1.20'),
        'german_name': 'Poliert',
        'english_name': 'Polished',
        'description': 'Hochglanz poliert (intensive Handarbeit)',
        'material_surcharge': Decimal('18.00'),
    },
    'lacquered_matte': {
        'time_factor': Decimal('1.10'),
        'german_name': 'Lackiert (matt)',
        'english_name': 'Lacquered (matte)',
        'description': 'Mit mattierendem Lack versiegelt',
        'material_surcharge': Decimal('12.00'),
    },
}

# ============================================================================
# ADDITIONAL WORK ITEMS
# Zusätzliche, oft benötigte Arbeitsschritte
# ============================================================================

ADDITIONAL_FEATURES = {
    'assembly': {
        'time_cost_hours': Decimal('0.25'),
        'german_name': 'Montage',
        'english_name': 'Assembly',
        'description': 'Zusammenbau von Komponenten',
    },
    'delivery': {
        'time_cost_hours': Decimal('0.50'),
        'german_name': 'Transport & Aufstellung',
        'english_name': 'Delivery & Setup',
        'description': 'Lieferung und Aufbau vor Ort',
    },
    'installation': {
        'time_cost_hours': Decimal('1.0'),
        'german_name': 'Installation',
        'english_name': 'Installation',
        'description': 'Einbau an Ort und Stelle (z.B. Wandmontage)',
    },
    'consulting': {
        'time_cost_hours': Decimal('1.0'),
        'german_name': 'Beratung',
        'english_name': 'Consulting',
        'description': 'Persönliche Beratung vor/nach Auftragserteilung',
    },
    'design': {
        'time_cost_hours': Decimal('2.0'),
        'german_name': 'Design & Planung',
        'english_name': 'Design & Planning',
        'description': 'Individuelle Entwurf und Planung',
    },
}

# ============================================================================
# UNIT CONVERSION & MAPPING
# Unterstützte Mengeneinheiten
# ============================================================================

UNIT_MAPPING = {
    'sqm': {
        'symbol': 'm²',
        'german_name': 'Quadratmeter',
        'english_name': 'Square meter',
        'type': 'area',
    },
    'lfm': {
        'symbol': 'lfm',
        'german_name': 'Laufende Meter',
        'english_name': 'Linear meter',
        'type': 'length',
    },
    'pcs': {
        'symbol': 'Stk',
        'german_name': 'Stück',
        'english_name': 'Piece',
        'type': 'count',
    },
    'hour': {
        'symbol': 'h',
        'german_name': 'Stunden',
        'english_name': 'Hours',
        'type': 'time',
    },
    'pauschal': {
        'symbol': 'Pauschal',
        'german_name': 'Pauschalgebühr',
        'english_name': 'Flat rate',
        'type': 'flat',
    },
    'kg': {
        'symbol': 'kg',
        'german_name': 'Kilogramm',
        'english_name': 'Kilogram',
        'type': 'weight',
    },
}

# ============================================================================
# DEFAULT VALUES
# Voreinstellungen für neue Betriebe
# ============================================================================

DEFAULT_HOURLY_RATE = Decimal('75.00')  # € pro Stunde
DEFAULT_PROFIT_MARGIN = Decimal('0.10')  # 10%
DEFAULT_OVERHEAD_FACTOR = Decimal('1.10')  # 10% Gemeinkosten
DEFAULT_TAX_RATE = Decimal('0.19')  # Deutsche MwSt 19%
DEFAULT_DELIVERY_DAYS = 30
DEFAULT_DOCUMENT_RETENTION_DAYS = 365  # DSGVO

# ============================================================================
# QUALITY STANDARDS
# Qualitätsmerkmale und deren Bewertung
# ============================================================================

QUALITY_TIERS = {
    'economy': {
        'factor': Decimal('0.85'),
        'german_name': 'Wirtschaftlich',
        'description': 'Standardqualität, kostenoptimiert',
    },
    'standard': {
        'factor': Decimal('1.0'),
        'german_name': 'Standard',
        'description': 'Gutes Preis-Leistungs-Verhältnis',
    },
    'premium': {
        'factor': Decimal('1.25'),
        'german_name': 'Premium',
        'description': 'Hochwertig, mit Extras',
    },
    'luxury': {
        'factor': Decimal('1.50'),
        'german_name': 'Luxus',
        'description': 'Höchste Qualität, Maßanfertigung',
    },
}

# ============================================================================
# CERTIFICATION & COMPLIANCE
# Zertifizierungen und Standards
# ============================================================================

CERTIFICATIONS = {
    'fsc': {
        'name': 'FSC Zertifiziert',
        'description': 'Nachhaltiges Holz aus verantwortungsvollen Quellen',
        'price_factor': Decimal('1.05'),  # 5% Aufschlag
    },
    'pefc': {
        'name': 'PEFC Zertifiziert',
        'description': 'Europäisches Waldzertifikat',
        'price_factor': Decimal('1.03'),  # 3% Aufschlag
    },
    'deco': {
        'name': 'DIN EN 71 (Spielzeugrichtlinie)',
        'description': 'Sicherheit für Möbel für Kinder',
        'price_factor': Decimal('1.10'),  # 10% Aufschlag für zusätzliche Tests
    },
}

# ============================================================================
# STANDARD MARKUP FOR DIFFERENT TRADES
# Handwerks-spezifische Aufschläge
# ============================================================================

TRADE_MARKUP_FACTORS = {
    'carpentry': Decimal('1.15'),  # Schreinerei: 15%
    'masonry': Decimal('1.12'),    # Maurerei: 12%
    'upholstery': Decimal('1.18'), # Polsterei: 18%
    'metalwork': Decimal('1.20'),  # Schlosserei: 20%
    'restoration': Decimal('1.35'), # Restaurierung: 35%
    'restoration_art': Decimal('1.50'),  # Kunsthandwerk: 50%
}
