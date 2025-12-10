/**
 * API barrel export
 */

export { default, apiClient } from './client'
export {
  getErrorMessage,
  isAuthenticated,
  getCurrentUser,
  setAuth,
  clearAuth,
} from './client'

export type { ApiError } from './client'

// Export apiClient as named export 'api' for compatibility
import { apiClient } from './client'
export const api = apiClient
