/**
 * TypeScript types for DraftCraft API
 * Generated from Django REST Framework models
 */

// ========================================
// Authentication
// ========================================

export interface AuthResponse {
  token: string
  user: {
    id: number
    username: string
    email: string
  }
}

export interface ApiError {
  detail?: string
  message?: string
  errors?: Record<string, string[]>
}

// ========================================
// Documents
// ========================================

export type DocumentStatus =
  | 'uploaded'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'archived'

export interface Document {
  id: string
  original_filename: string
  file_path: string
  file_size: number
  document_type: 'pdf' | 'image' | 'gaeb_xml' | 'unknown'
  status: DocumentStatus
  uploaded_at: string
  processed_at: string | null
  created_at: string
  updated_at: string
}

// ========================================
// Extraction
// ========================================

export type EntityType =
  | 'CUSTOMER_NAME'
  | 'EMAIL'
  | 'ADDRESS'
  | 'PHONE'
  | 'DATE'
  | 'AMOUNT'
  | 'MATERIAL'
  | 'MEASUREMENT'
  | 'HOLZART'
  | 'OBERFLAECHE'
  | 'KOMPLEXITAET'

export interface ExtractedEntity {
  id: string
  entity_type: EntityType
  value: string
  confidence: number
  source_text: string
  position: {
    page: number
    bbox: [number, number, number, number]
  }
}

export interface ExtractionSummary {
  document_id: string
  status: DocumentStatus
  ocr_confidence: number
  entity_count: number
  entity_types: Record<EntityType, number>
  materials_found: number
  processing_time_ms: number
  extracted_at: string
  entities: ExtractedEntity[]
  routing_tier?: 'AUTO_ACCEPT' | 'AGENT_VERIFY' | 'AGENT_EXTRACT' | 'HUMAN_REVIEW'
}

// ========================================
// Proposals
// ========================================

export type ProposalStatus = 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired'

export interface ProposalLine {
  id: string
  position: number
  description: string
  quantity: number
  unit: string
  unit_price: number
  total_price: number
}

export interface Proposal {
  id: string
  proposal_number: string
  document_id: string
  status: ProposalStatus
  customer_name: string
  customer_email: string
  customer_address: string
  lines: ProposalLine[]
  subtotal: number
  vat_rate: number
  vat_amount: number
  total: number
  valid_until: string
  created_at: string
  updated_at: string
}

export interface ProposalRequest {
  document_id: string
  customer_name: string
  customer_email: string
  customer_address?: string
  valid_days?: number
  template_id?: string | null
}

// ========================================
// Betriebskennzahlen (Business Metrics)
// ========================================

export type HolzartKategorie = 'hartholz' | 'weichholz'
export type Verfuegbarkeit = 'verfuegbar' | 'begrenzt' | 'auf_anfrage'

export interface HolzartKennzahl {
  id: string
  holzart: string
  kategorie: HolzartKategorie
  preis_faktor: number
  verfuegbarkeit: Verfuegbarkeit
  is_enabled: boolean
}

export interface OberflächenbearbeitungKennzahl {
  id: string
  typ: string
  beschreibung: string
  preis_faktor: number
  zusatzkosten_pro_qm: number
  zeitaufwand_faktor: number
  is_enabled: boolean
}

export interface KomplexitaetKennzahl {
  id: string
  komplexitaet_typ: string
  beschreibung: string
  zeit_faktor: number
  preis_faktor: number
  is_enabled: boolean
}

// ========================================
// Pattern Analysis
// ========================================

export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface ExtractionFailurePattern {
  id: string
  pattern_type: string
  description: string
  severity: SeverityLevel
  occurrence_count: number
  first_seen: string
  last_seen: string
  example_documents: string[]
  suggested_fix: string
  is_resolved: boolean
}

export interface PatternFixProposal {
  id: string
  pattern_id: string
  fix_description: string
  code_changes: string
  test_success_rate: number
  estimated_impact: string
  approved: boolean
  deployed: boolean
  created_at: string
}

// ========================================
// Transparency (Phase 4A)
// ========================================

export type ConfidenceLevel = 'high' | 'medium' | 'low'
export type DataSource = 'tier1_global' | 'tier2_company' | 'tier3_dynamic' | 'user_history'

export interface CalculationFactor {
  id: string
  factor_name: string
  factor_category: string
  amount_eur: number
  impact_percent: number
  explanation_text: string
  data_source: DataSource
  is_adjustable: boolean
  display_order: number
}

export interface TierBreakdown {
  tier1_contribution: number
  tier2_contribution: number
  tier3_contribution: number
  user_history_contribution: number
}

export interface CalculationExplanation {
  id: string
  confidence_level: ConfidenceLevel
  confidence_score: number
  total_price_eur: number
  similar_projects_count: number
  user_average_for_type: number | null
  deviation_from_average_percent: number | null
  faktoren: CalculationFactor[]
  tier_breakdown: TierBreakdown
  created_at: string
}

export interface UserProjectBenchmark {
  id: string
  projekttyp: string
  durchschnittspreis_eur: number
  median_preis_eur: number
  min_preis_eur: number
  max_preis_eur: number
  anzahl_projekte: number
  letztes_projekt_datum: string
  durchschnitt_abweichung_prozent: number
  created_at: string
  updated_at: string
}

export type FeedbackType =
  | 'zu_hoch'
  | 'zu_niedrig'
  | 'genau_richtig'
  | 'faktor_fehlt'
  | 'faktor_falsch'
  | 'sonstiges'

export interface CalculationFeedback {
  extraction_result_id: string
  calculation_id?: string
  feedback_type: FeedbackType
  erwarteter_preis_eur?: number
  kommentare?: string
  faktoren_bewertung?: Record<string, number>
}

export interface CalculationComparison {
  current_price_eur: number
  benchmark_avg_eur: number
  difference_eur: number
  difference_percent: number
  is_above_average: boolean
  explanation: string
  factors_causing_difference: Array<{
    factor: string
    value: string
    impact: string
  }>
  sample_size: number
}

// ========================================
// Admin Dashboard (Phase 4D)
// ========================================

export interface DashboardStats {
  total_documents: number
  processed_today: number
  active_patterns: number
  critical_patterns: number
  avg_confidence: number
  total_users: number
  documents_last_7_days: Array<{
    date: string
    day: string
    count: number
  }>
  pattern_severity_breakdown: {
    CRITICAL: number
    HIGH: number
    MEDIUM: number
    LOW: number
  }
  timestamp: string
}

export type ActivityType = 'document_processed' | 'pattern_detected' | 'document_error'
export type ActivitySeverity = 'success' | 'info' | 'warning' | 'error' | 'high' | 'medium' | 'low'

export interface DashboardActivity {
  type: ActivityType
  title: string
  description: string
  timestamp: string
  severity: ActivitySeverity
  icon: string
}

export interface DashboardActivityResponse {
  activities: DashboardActivity[]
  total_count: number
}

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown'

export interface HealthComponent {
  status: HealthStatus
  message: string
  error_rate?: string
  recent_errors?: number
  recent_total?: number
}

export interface SystemHealth {
  overall: HealthStatus
  components: {
    database: HealthComponent
    cache: HealthComponent
    processing: HealthComponent
  }
  timestamp: string
}
