/**
 * Documents hook for file upload and extraction
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

export interface Document {
  id: number
  file_name: string
  file_type: string
  file_size: number
  uploaded_at: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  extraction_data?: Record<string, unknown>
  confidence_score?: number
}

export interface ExtractionResult {
  document_id: number
  extracted_data: Record<string, unknown>
  confidence_scores: Record<string, number>
  processing_time: number
}

/**
 * Hook for document management
 */
export function useDocuments() {
  const queryClient = useQueryClient()

  // Fetch all documents
  const documentsQuery = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/documents/')
      return response.data
    },
  })

  // Upload document
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post<Document>('/api/v1/documents/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  // Extract document data
  const extractMutation = useMutation({
    mutationFn: async (documentId: number) => {
      const response = await apiClient.post<ExtractionResult>(
        `/api/v1/documents/${documentId}/extract/`
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  // Delete document
  const deleteMutation = useMutation({
    mutationFn: async (documentId: number) => {
      await apiClient.delete(`/api/v1/documents/${documentId}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  return {
    documents: documentsQuery.data || [],
    isLoading: documentsQuery.isLoading,
    upload: uploadMutation.mutate,
    uploadAsync: uploadMutation.mutateAsync,
    extract: extractMutation.mutate,
    extractAsync: extractMutation.mutateAsync,
    deleteDocument: deleteMutation.mutate,
    isUploading: uploadMutation.isPending,
    isExtracting: extractMutation.isPending,
    isDeleting: deleteMutation.isPending,
    uploadError: uploadMutation.error,
    extractError: extractMutation.error,
    extractionResult: extractMutation.data,
  }
}

// Compatibility exports
export const useUploadDocument = useDocuments
export const useProcessDocument = useDocuments
export const useAutoExtractionSummary = useDocuments

export default useDocuments
