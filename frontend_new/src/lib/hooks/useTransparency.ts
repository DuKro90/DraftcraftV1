/**
 * Transparency hook for calculation explanations and benchmarks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

export interface CalculationFactor {
  name: string
  category: string
  base_value: number
  applied_factor: number
  result_value: number
  explanation: string
}

export interface CalculationExplanation {
  id: number
  calculation_id: number
  created_at: string
  factors: CalculationFactor[]
  step_by_step: string[]
  confidence_level: 'high' | 'medium' | 'low'
  total_breakdown: {
    materials: number
    labor: number
    overhead: number
    margin: number
    total: number
  }
}

export interface UserProjectBenchmark {
  id: number
  project_type: string
  avg_price: number
  avg_duration: number
  success_rate: number
  total_projects: number
  last_updated: string
}

export interface FeedbackData {
  explanation_id: number
  rating: number
  comment?: string
  was_helpful: boolean
}

/**
 * Hook for transparency features
 */
export function useTransparency() {
  const queryClient = useQueryClient()

  // Fetch calculation explanation
  const useExplanation = (calculationId: number) => {
    return useQuery<CalculationExplanation>({
      queryKey: ['transparency', 'explanation', calculationId],
      queryFn: async () => {
        const response = await apiClient.get(
          `/api/v1/transparency/explanations/${calculationId}/`
        )
        return response.data
      },
      enabled: !!calculationId,
    })
  }

  // Fetch user benchmarks
  const benchmarksQuery = useQuery<UserProjectBenchmark[]>({
    queryKey: ['transparency', 'benchmarks'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/transparency/benchmarks/')
      return response.data
    },
  })

  // Submit feedback
  const feedbackMutation = useMutation({
    mutationFn: async (data: FeedbackData) => {
      const response = await apiClient.post('/api/v1/transparency/feedback/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transparency'] })
    },
  })

  // Get similar projects
  const useSimilarProjects = (projectType: string) => {
    return useQuery({
      queryKey: ['transparency', 'similar', projectType],
      queryFn: async () => {
        const response = await apiClient.get(
          `/api/v1/transparency/similar-projects/?type=${projectType}`
        )
        return response.data
      },
      enabled: !!projectType,
    })
  }

  return {
    useExplanation,
    benchmarks: benchmarksQuery.data || [],
    isLoadingBenchmarks: benchmarksQuery.isLoading,
    submitFeedback: feedbackMutation.mutate,
    isSubmittingFeedback: feedbackMutation.isPending,
    useSimilarProjects,
  }
}

// Compatibility exports
export const useUserBenchmarks = useTransparency
export const useCalculationExplanations = useTransparency
export const useCalculationComparison = useTransparency
export const useSubmitCalculationFeedback = useTransparency

export function useCalculationExplanation(calculationId: number) {
  const { useExplanation } = useTransparency()
  return useExplanation(calculationId)
}

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

export default useTransparency
