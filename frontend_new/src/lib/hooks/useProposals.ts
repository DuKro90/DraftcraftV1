/**
 * Proposals hook for managing project proposals
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

export interface ProposalLineItem {
  id?: number
  description: string
  quantity: number
  unit: string
  unit_price: number
  total_price: number
}

export interface Proposal {
  id: number
  title: string
  customer_name: string
  customer_email?: string
  created_at: string
  updated_at: string
  status: 'draft' | 'sent' | 'accepted' | 'rejected'
  total_amount: number
  line_items: ProposalLineItem[]
  notes?: string
}

export interface CreateProposalData {
  title: string
  customer_name: string
  customer_email?: string
  line_items: ProposalLineItem[]
  notes?: string
}

/**
 * Hook for proposal management
 */
export function useProposals() {
  const queryClient = useQueryClient()

  // Fetch all proposals
  const proposalsQuery = useQuery<Proposal[]>({
    queryKey: ['proposals'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/proposals/')
      return response.data
    },
  })

  // Fetch single proposal
  const useProposal = (id: number) => {
    return useQuery<Proposal>({
      queryKey: ['proposals', id],
      queryFn: async () => {
        const response = await apiClient.get(`/api/v1/proposals/${id}/`)
        return response.data
      },
      enabled: !!id,
    })
  }

  // Create proposal
  const createMutation = useMutation({
    mutationFn: async (data: CreateProposalData) => {
      const response = await apiClient.post<Proposal>('/api/v1/proposals/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] })
    },
  })

  // Update proposal
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<CreateProposalData> }) => {
      const response = await apiClient.patch<Proposal>(`/api/v1/proposals/${id}/`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] })
    },
  })

  // Delete proposal
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/proposals/${id}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] })
    },
  })

  // Send proposal to customer
  const sendMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.post<Proposal>(`/api/v1/proposals/${id}/send/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] })
    },
  })

  return {
    proposals: proposalsQuery.data || [],
    isLoading: proposalsQuery.isLoading,
    useProposal,
    create: createMutation.mutate,
    createAsync: createMutation.mutateAsync,
    update: updateMutation.mutate,
    deleteProposal: deleteMutation.mutate,
    send: sendMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isSending: sendMutation.isPending,
    createError: createMutation.error,
  }
}

// Compatibility exports
export const useGenerateProposal = useProposals
export const useDownloadProposalPdf = useProposals
export const useSendProposal = useProposals

// Export useProposal as standalone function
export function useProposal(id: number) {
  const { useProposal: getProposal } = useProposals()
  return getProposal(id)
}

export default useProposals
