/**
 * Configuration hook for Holzarten, Oberflächen, Komplexität
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

interface ConfigItem {
  id: number
  name: string
  faktor?: number
  beschreibung?: string
  is_active?: boolean
}

export interface HolzartConfig extends ConfigItem {
  kategorie: string
  dichte?: number
  haerte?: string
}

export interface OberflächeConfig extends ConfigItem {
  kategorie: string
  arbeitsschritte?: string[]
}

export interface KomplexitätConfig extends ConfigItem {
  kategorie: string
  beispiele?: string[]
}

/**
 * Hook for managing configuration data
 */
export function useConfig() {
  const queryClient = useQueryClient()

  // Fetch Holzarten
  const holzartenQuery = useQuery<HolzartConfig[]>({
    queryKey: ['config', 'holzarten'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/config/holzarten/')
      return response.data
    },
  })

  // Fetch Oberflächen
  const oberflächenQuery = useQuery<OberflächeConfig[]>({
    queryKey: ['config', 'oberflächen'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/config/oberflächen/')
      return response.data
    },
  })

  // Fetch Komplexitäten
  const komplexitätenQuery = useQuery<KomplexitätConfig[]>({
    queryKey: ['config', 'komplexitäten'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/config/komplexitäten/')
      return response.data
    },
  })

  // Update Holzart
  const updateHolzartMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<HolzartConfig> }) => {
      const response = await apiClient.patch(`/api/v1/config/holzarten/${id}/`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config', 'holzarten'] })
    },
  })

  // Update Oberfläche
  const updateOberflächeMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<OberflächeConfig> }) => {
      const response = await apiClient.patch(`/api/v1/config/oberflächen/${id}/`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config', 'oberflächen'] })
    },
  })

  // Update Komplexität
  const updateKomplexitätMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<KomplexitätConfig> }) => {
      const response = await apiClient.patch(`/api/v1/config/komplexitäten/${id}/`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config', 'komplexitäten'] })
    },
  })

  return {
    // Data
    holzarten: holzartenQuery.data || [],
    oberflächen: oberflächenQuery.data || [],
    komplexitäten: komplexitätenQuery.data || [],

    // Loading states
    isLoadingHolzarten: holzartenQuery.isLoading,
    isLoadingOberflächen: oberflächenQuery.isLoading,
    isLoadingKomplexitäten: komplexitätenQuery.isLoading,

    // Mutations
    updateHolzart: updateHolzartMutation.mutate,
    updateOberfläche: updateOberflächeMutation.mutate,
    updateKomplexität: updateKomplexitätMutation.mutate,

    // Mutation states
    isUpdating: updateHolzartMutation.isPending || updateOberflächeMutation.isPending || updateKomplexitätMutation.isPending,
  }
}

// Compatibility exports
export const useHolzarten = useConfig
export const useOberflaechen = useConfig
export const useKomplexitaeten = useConfig
export const useCreateHolzart = useConfig
export const useUpdateHolzart = useConfig
export const useDeleteHolzart = useConfig
