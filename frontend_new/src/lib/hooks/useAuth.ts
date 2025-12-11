/**
 * Authentication hook
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient, setAuth, clearAuth, getCurrentUser, isAuthenticated } from '@/lib/api/client'
import { useNavigate } from 'react-router-dom'

interface LoginCredentials {
  email: string
  password: string
}

interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
  company_name?: string
}

interface AuthResponse {
  token: string
  user: Record<string, unknown>
}

/**
 * Authentication hook
 */
export function useAuth() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  // Get current user
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: () => getCurrentUser(),
    enabled: isAuthenticated(),
  })

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await apiClient.post<AuthResponse>('/api/auth/token/', {
        username: credentials.email,
        password: credentials.password
      })
      return response.data
    },
    onSuccess: (data) => {
      setAuth(data.token, data.user)
      queryClient.setQueryData(['auth', 'user'], data.user)
      navigate('/dashboard')
    },
  })

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: async (data: RegisterData) => {
      const response = await apiClient.post<AuthResponse>('/api/auth/register/', {
        username: data.email,
        email: data.email,
        password: data.password,
        password_confirm: data.password,
        first_name: data.first_name,
        last_name: data.last_name
      })
      return response.data
    },
    onSuccess: (data) => {
      setAuth(data.token, data.user)
      queryClient.setQueryData(['auth', 'user'], data.user)
      navigate('/dashboard')
    },
  })

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/api/auth/logout/')
    },
    onSuccess: () => {
      clearAuth()
      queryClient.clear()
      navigate('/login')
    },
  })

  return {
    user,
    isLoading,
    isAuthenticated: isAuthenticated(),
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  }
}

// Compatibility exports
export const useRegister = useAuth
