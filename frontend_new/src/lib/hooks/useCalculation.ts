/**
 * Calculation hook for price calculations
 */

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

export interface CalculationInput {
  holzart_id?: number
  oberfläche_id?: number
  komplexität_id?: number
  dimensions?: {
    length?: number
    width?: number
    height?: number
  }
  labor_hours?: number
  materials?: Array<{
    name: string
    quantity: number
    unit_price: number
  }>
}

export interface CalculationResult {
  base_price: number
  holzart_faktor: number
  oberfläche_faktor: number
  komplexität_faktor: number
  material_cost: number
  labor_cost: number
  total_price: number
  margin: number
  final_price: number
  factors: {
    holzart: { name: string; faktor: number }
    oberfläche: { name: string; faktor: number }
    komplexität: { name: string; faktor: number }
  }
}

/**
 * Hook for price calculations
 */
export function useCalculation() {
  // Calculate price mutation
  const calculateMutation = useMutation({
    mutationFn: async (input: CalculationInput) => {
      const response = await apiClient.post<CalculationResult>(
        '/api/v1/calculate/price/',
        input
      )
      return response.data
    },
  })

  return {
    calculate: calculateMutation.mutate,
    calculateAsync: calculateMutation.mutateAsync,
    result: calculateMutation.data,
    isCalculating: calculateMutation.isPending,
    error: calculateMutation.error,
    reset: calculateMutation.reset,
  }
}

// Compatibility exports
export const useCalculatePrice = useCalculation
export const useCalculateMultiMaterial = useCalculation
