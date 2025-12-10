/**
 * Hooks barrel export with compatibility layer
 */

// Export main hooks
export { useAuth } from './useAuth'
export { useCalculation } from './useCalculation'
export { useConfig } from './useConfig'
export { useDocuments } from './useDocuments'
export { useProposals } from './useProposals'
export { useTransparency } from './useTransparency'

// Re-export types
export type {
  HolzartConfig,
  OberflächeConfig,
  KomplexitätConfig,
} from './useConfig'

export type {
  CalculationInput,
  CalculationResult,
} from './useCalculation'

export type {
  Document,
  ExtractionResult,
} from './useDocuments'

export type {
  Proposal,
  ProposalLineItem,
  CreateProposalData,
} from './useProposals'

export type {
  CalculationExplanation,
  CalculationFactor,
  UserProjectBenchmark,
  FeedbackData,
} from './useTransparency'

// Compatibility exports - delegating to main hooks
import { useAuth } from './useAuth'
import { useCalculation } from './useCalculation'
import { useConfig } from './useConfig'
import { useDocuments } from './useDocuments'
import { useProposals } from './useProposals'
import { useTransparency } from './useTransparency'

/**
 * Compatibility wrapper: useRegister -> useAuth
 */
export const useRegister = useAuth

/**
 * Compatibility wrapper: useCalculatePrice -> useCalculation
 */
export const useCalculatePrice = useCalculation

/**
 * Compatibility wrapper: useCalculateMultiMaterial -> useCalculation
 */
export const useCalculateMultiMaterial = useCalculation

/**
 * Compatibility wrapper: useHolzarten -> useConfig
 */
export const useHolzarten = useConfig

/**
 * Compatibility wrapper: useOberflaechen -> useConfig
 */
export const useOberflaechen = useConfig

/**
 * Compatibility wrapper: useKomplexitaeten -> useConfig
 */
export const useKomplexitaeten = useConfig

/**
 * Compatibility wrapper: useCreateHolzart -> useConfig
 */
export const useCreateHolzart = useConfig

/**
 * Compatibility wrapper: useUpdateHolzart -> useConfig
 */
export const useUpdateHolzart = useConfig

/**
 * Compatibility wrapper: useDeleteHolzart -> useConfig
 */
export const useDeleteHolzart = useConfig

/**
 * Compatibility wrapper: useUploadDocument -> useDocuments
 */
export const useUploadDocument = useDocuments

/**
 * Compatibility wrapper: useProcessDocument -> useDocuments
 */
export const useProcessDocument = useDocuments

/**
 * Compatibility wrapper: useAutoExtractionSummary -> useDocuments
 */
export const useAutoExtractionSummary = useDocuments

/**
 * Compatibility wrapper: useProposal -> useProposals (for single proposal)
 */
export function useProposal(id: number) {
  const { useProposal: getProposal } = useProposals()
  return getProposal(id)
}

/**
 * Compatibility wrapper: useGenerateProposal -> useProposals
 */
export const useGenerateProposal = useProposals

/**
 * Compatibility wrapper: useDownloadProposalPdf -> useProposals
 */
export const useDownloadProposalPdf = useProposals

/**
 * Compatibility wrapper: useSendProposal -> useProposals
 */
export const useSendProposal = useProposals

/**
 * Compatibility wrapper: useCalculationExplanation -> useTransparency
 */
export function useCalculationExplanation(calculationId: number) {
  const { useExplanation } = useTransparency()
  return useExplanation(calculationId)
}

/**
 * Compatibility wrapper: useCalculationExplanations -> useTransparency
 */
export const useCalculationExplanations = useTransparency

/**
 * Compatibility wrapper: useCalculationComparison -> useTransparency
 */
export const useCalculationComparison = useTransparency

/**
 * Compatibility wrapper: useUserBenchmarks -> useTransparency
 */
export const useUserBenchmarks = useTransparency

/**
 * Compatibility wrapper: useSubmitCalculationFeedback -> useTransparency
 */
export const useSubmitCalculationFeedback = useTransparency

/**
 * Compatibility wrapper: useConfidenceBadgeColor -> Simple utility function
 */
export function useConfidenceBadgeColor(level: string) {
  const colors = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-red-100 text-red-800',
  }
  return colors[level as keyof typeof colors] || colors.medium
}

/**
 * Compatibility wrapper: useDataSourceBadge -> Simple utility function
 */
export function useDataSourceBadge(source: string) {
  const badges = {
    tier1: 'Standard',
    tier2: 'Firma',
    tier3: 'Dynamisch',
    ai: 'KI-generiert',
  }
  return badges[source as keyof typeof badges] || 'Unbekannt'
}

/**
 * Compatibility wrapper: useDeviationFormatter -> Simple utility function
 */
export function useDeviationFormatter(deviation: number) {
  const sign = deviation > 0 ? '+' : ''
  return `${sign}${(deviation * 100).toFixed(1)}%`
}
