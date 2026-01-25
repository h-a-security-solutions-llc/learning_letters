/**
 * API Configuration
 *
 * Uses VITE_LEARNING_API_BASE environment variable if set,
 * otherwise defaults to production URL.
 *
 * Setup:
 *   1. Copy .env.example to .env (for production) or .env.development (for local dev)
 *   2. Update VITE_LEARNING_API_BASE as needed
 *
 * Note: .env files are gitignored - never commit secrets!
 */

export const API_BASE = import.meta.env.VITE_LEARNING_API_BASE || 'https://learning.tellaro.io'

/**
 * Constructs a full API URL from a path
 * @param path - API path (e.g., '/api/fonts' or 'api/fonts')
 * @returns Full URL to the API endpoint
 */
export function apiUrl(path: string): string {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${normalizedPath}`
}
