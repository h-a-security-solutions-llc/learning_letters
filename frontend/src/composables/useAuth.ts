/**
 * Authentication composable
 * Manages user authentication state, login, register, and logout
 */

import { ref, computed, readonly } from 'vue'
import type { User, AuthState, TokenResponse } from '@/types'
import { authApi, clearAccessToken } from '@/services/api'

// Singleton state (shared across all components)
const user = ref<User | null>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)
const isInitialized = ref(false)

// Computed properties
const isAuthenticated = computed(() => user.value !== null)
const authState = computed<AuthState>(() => ({
  user: user.value,
  isAuthenticated: isAuthenticated.value,
  isLoading: isLoading.value,
}))

// Initialize auth state (try to restore session from refresh token)
async function initAuth(): Promise<void> {
  if (isInitialized.value) return

  isLoading.value = true
  error.value = null

  try {
    // Try to refresh the access token using the refresh token cookie
    const response = await authApi.refresh()
    user.value = response.user
  } catch {
    // No valid session - user is not logged in
    user.value = null
    clearAccessToken()
  } finally {
    isLoading.value = false
    isInitialized.value = true
  }
}

// Register a new user
async function register(
  email: string,
  password: string,
  displayName: string
): Promise<TokenResponse> {
  isLoading.value = true
  error.value = null

  try {
    const response = await authApi.register(email, password, displayName)
    user.value = response.user
    return response
  } catch (err: unknown) {
    const message = extractErrorMessage(err)
    error.value = message
    throw new Error(message)
  } finally {
    isLoading.value = false
  }
}

// Login with email and password
async function login(email: string, password: string): Promise<TokenResponse> {
  isLoading.value = true
  error.value = null

  try {
    const response = await authApi.login(email, password)
    user.value = response.user
    return response
  } catch (err: unknown) {
    const message = extractErrorMessage(err)
    error.value = message
    throw new Error(message)
  } finally {
    isLoading.value = false
  }
}

// Logout
async function logout(): Promise<void> {
  isLoading.value = true
  error.value = null

  try {
    await authApi.logout()
  } finally {
    user.value = null
    clearAccessToken()
    isLoading.value = false
  }
}

// Delete account
async function deleteAccount(): Promise<void> {
  isLoading.value = true
  error.value = null

  try {
    await authApi.deleteAccount()
    user.value = null
  } catch (err: unknown) {
    const message = extractErrorMessage(err)
    error.value = message
    throw new Error(message)
  } finally {
    isLoading.value = false
  }
}

// Update user data (for display name changes etc)
function updateUser(updates: Partial<User>): void {
  if (user.value) {
    user.value = { ...user.value, ...updates }
  }
}

// Clear error
function clearError(): void {
  error.value = null
}

// Helper to extract error message from axios error
function extractErrorMessage(err: unknown): string {
  if (err && typeof err === 'object') {
    const axiosError = err as { response?: { data?: { detail?: string } }; message?: string }
    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail
    }
    if (axiosError.message) {
      return axiosError.message
    }
  }
  return 'An unexpected error occurred'
}

// Composable export
export function useAuth() {
  return {
    // State (readonly)
    user: readonly(user),
    isAuthenticated,
    isLoading: readonly(isLoading),
    error: readonly(error),
    authState,
    isInitialized: readonly(isInitialized),

    // Actions
    initAuth,
    register,
    login,
    logout,
    deleteAccount,
    updateUser,
    clearError,
  }
}
