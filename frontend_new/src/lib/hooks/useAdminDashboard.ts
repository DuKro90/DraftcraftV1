/**
 * Admin Dashboard hook for statistics and monitoring
 */

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'

export interface DashboardStats {
  total_documents: number
  documents_today: number
  total_extractions: number
  extractions_today: number
  avg_confidence_score: number
  active_patterns: number
  pending_approvals: number
  system_health: 'healthy' | 'warning' | 'critical'
}

export interface RecentActivity {
  id: number
  type: 'document' | 'extraction' | 'pattern' | 'approval'
  description: string
  timestamp: string
  user: string
  status: 'success' | 'pending' | 'failed'
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  database: {
    connected: boolean
    response_time_ms: number
  }
  redis: {
    connected: boolean
    response_time_ms: number
  }
  storage: {
    available_mb: number
    used_percent: number
  }
  services: {
    ocr: boolean
    ner: boolean
    calculation: boolean
  }
}

/**
 * Hook for admin dashboard data
 */
export function useAdminDashboard() {
  // Fetch dashboard statistics
  const statsQuery = useQuery<DashboardStats>({
    queryKey: ['admin', 'dashboard', 'stats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/dashboard/stats/')
      return response.data
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  // Fetch recent activity
  const activityQuery = useQuery<RecentActivity[]>({
    queryKey: ['admin', 'dashboard', 'activity'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/dashboard/activity/')
      return response.data
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  })

  // Fetch system health
  const healthQuery = useQuery<SystemHealth>({
    queryKey: ['admin', 'dashboard', 'health'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/dashboard/health/')
      return response.data
    },
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  return {
    // Data
    stats: statsQuery.data,
    activity: activityQuery.data || [],
    health: healthQuery.data,

    // Loading states
    isLoadingStats: statsQuery.isLoading,
    isLoadingActivity: activityQuery.isLoading,
    isLoadingHealth: healthQuery.isLoading,

    // Error states
    statsError: statsQuery.error,
    activityError: activityQuery.error,
    healthError: healthQuery.error,

    // Refetch functions
    refetchStats: statsQuery.refetch,
    refetchActivity: activityQuery.refetch,
    refetchHealth: healthQuery.refetch,
  }
}

// Compatibility exports
export const useDashboardStats = useAdminDashboard
export const useRecentActivity = useAdminDashboard
export const useSystemHealth = useAdminDashboard

export default useAdminDashboard
