/**
 * API Client for DraftCraft Backend
 * Handles authentication, request/response formatting, and error handling
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

// API Base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Main API client instance
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request interceptor - Add auth token
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor - Handle errors globally
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * API Error type
 */
export interface ApiError {
  message: string
  status?: number
  details?: Record<string, unknown>
}

/**
 * Extract error message from API error
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    return error.response?.data?.message || error.message || 'Ein Fehler ist aufgetreten'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Ein unbekannter Fehler ist aufgetreten'
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('auth_token')
}

/**
 * Get current user from localStorage
 */
export function getCurrentUser(): Record<string, unknown> | null {
  const userStr = localStorage.getItem('user')
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

/**
 * Set authentication token and user data
 */
export function setAuth(token: string, user: Record<string, unknown>): void {
  localStorage.setItem('auth_token', token)
  localStorage.setItem('user', JSON.stringify(user))
}

/**
 * Clear authentication
 */
export function clearAuth(): void {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user')
}

// Export apiClient as both default and named 'api' for compatibility
export const api = apiClient
export default apiClient
