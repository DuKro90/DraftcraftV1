/**
 * Compatibility layer for older imports
 * This file provides backwards-compatible exports for components that use the old API
 */

// Re-export everything from the main modules
export * from './api/client'
export * from './utils/formatters'
export * from './utils/cn'
export * from './hooks/useAuth'
export * from './hooks/useCalculation'
export * from './hooks/useConfig'
export * from './hooks/useDocuments'
export * from './hooks/useProposals'
export * from './hooks/useTransparency'

// Import for creating compatibility wrappers
import { useAuth } from './hooks/useAuth'
import { useCalculation } from './hooks/useCalculation'
import { useConfig } from './hooks/useConfig'
import { useDocuments } from './hooks/useDocuments'
import { useProposals } from './hooks/useProposals'
import { useTransparency } from './hooks/useTransparency'

// Compatibility exports - Auth
export const useRegister = useAuth

// Compatibility exports - Calculation
export const useCalculatePrice = useCalculation
export const useCalculateMultiMaterial = useCalculation

// Compatibility exports - Config
export const useHolzarten = useConfig
export const useOberflaechen = useConfig
export const useKomplexitaeten = useConfig
export const useCreateHolzart = useConfig
export const useUpdateHolzart = useConfig
export const useDeleteHolzart = useConfig

// Compatibility exports - Documents
export const useUploadDocument = useDocuments
export const useProcessDocument = useDocuments
export const useAutoExtractionSummary = useDocuments

// Compatibility exports - Proposals
export function useProposal(id: number) {
  const { useProposal: getProposal } = useProposals()
  return getProposal(id)
}
export const useGenerateProposal = useProposals
export const useDownloadProposalPdf = useProposals
export const useSendProposal = useProposals

// Compatibility exports - Transparency
export function useCalculationExplanation(calculationId: number) {
  const { useExplanation } = useTransparency()
  return useExplanation(calculationId)
}
export const useCalculationExplanations = useTransparency
export const useCalculationComparison = useTransparency
export const useUserBenchmarks = useTransparency
export const useSubmitCalculationFeedback = useTransparency

// Utility functions
export function useConfidenceBadgeColor(level: string) {
  const colors = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-red-100 text-red-800',
  }
  return colors[level as keyof typeof colors] || colors.medium
}

export function useDataSourceBadge(source: string) {
  const badges = {
    tier1: 'Standard',
    tier2: 'Firma',
    tier3: 'Dynamisch',
    ai: 'KI-generiert',
  }
  return badges[source as keyof typeof badges] || 'Unbekannt'
}

export function useDeviationFormatter(deviation: number) {
  const sign = deviation > 0 ? '+' : ''
  return `${sign}${(deviation * 100).toFixed(1)}%`
}
