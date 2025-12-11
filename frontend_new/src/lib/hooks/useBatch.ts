/**
 * Batch processing hook for multiple document uploads
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

export interface Batch {
  id: number
  name: string
  description?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_documents: number
  processed_documents: number
  failed_documents: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface BatchDocument {
  id: number
  batch_id: number
  document_id: number
  file_name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  confidence_score?: number
  error_message?: string
}

export interface CreateBatchInput {
  name: string
  description?: string
  files: File[]
}

/**
 * Hook for batch processing management
 */
export function useBatch() {
  const queryClient = useQueryClient()

  // Fetch all batches
  const batchesQuery = useQuery<Batch[]>({
    queryKey: ['batches'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/batches/')
      return response.data
    },
  })

  // Fetch single batch details
  const useBatchDetails = (batchId: number) => {
    return useQuery<Batch>({
      queryKey: ['batches', batchId],
      queryFn: async () => {
        const response = await apiClient.get(`/api/v1/batches/${batchId}/`)
        return response.data
      },
      enabled: !!batchId,
    })
  }

  // Fetch batch documents
  const useBatchDocuments = (batchId: number) => {
    return useQuery<BatchDocument[]>({
      queryKey: ['batches', batchId, 'documents'],
      queryFn: async () => {
        const response = await apiClient.get(`/api/v1/batches/${batchId}/documents/`)
        return response.data
      },
      enabled: !!batchId,
    })
  }

  // Create batch
  const createBatchMutation = useMutation({
    mutationFn: async (input: CreateBatchInput) => {
      const formData = new FormData()
      formData.append('name', input.name)
      if (input.description) {
        formData.append('description', input.description)
      }
      input.files.forEach((file) => {
        formData.append('files', file)
      })

      const response = await apiClient.post<Batch>('/api/v1/batches/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
  })

  // Process all documents in batch
  const processBatchMutation = useMutation({
    mutationFn: async (batchId: number) => {
      const response = await apiClient.post(`/api/v1/batches/${batchId}/process_all/`)
      return response.data
    },
    onSuccess: (_, batchId) => {
      queryClient.invalidateQueries({ queryKey: ['batches', batchId] })
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
  })

  // Delete batch
  const deleteBatchMutation = useMutation({
    mutationFn: async (batchId: number) => {
      await apiClient.delete(`/api/v1/batches/${batchId}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] })
    },
  })

  return {
    // Data
    batches: batchesQuery.data || [],
    isLoading: batchesQuery.isLoading,

    // Queries for single batch
    useBatchDetails,
    useBatchDocuments,

    // Mutations
    createBatch: createBatchMutation.mutate,
    createBatchAsync: createBatchMutation.mutateAsync,
    processBatch: processBatchMutation.mutate,
    processBatchAsync: processBatchMutation.mutateAsync,
    deleteBatch: deleteBatchMutation.mutate,

    // Mutation states
    isCreating: createBatchMutation.isPending,
    isProcessing: processBatchMutation.isPending,
    isDeleting: deleteBatchMutation.isPending,

    // Errors
    createError: createBatchMutation.error,
    processError: processBatchMutation.error,
    deleteError: deleteBatchMutation.error,
  }
}

// Compatibility exports
export const useCreateBatch = useBatch
export const useProcessBatch = useBatch
export const useBatchStatus = useBatch

export default useBatch
