/**
 * API Service with authentication interceptors
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { API_BASE } from '@/config/api'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Send cookies for refresh token
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token storage (in memory for security)
let accessToken: string | null = null
let refreshPromise: Promise<string | null> | null = null

// Token management functions
export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getAccessToken(): string | null {
  return accessToken
}

export function clearAccessToken(): void {
  accessToken = null
}

// Request interceptor - add auth header
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // If 401 and not already retrying, attempt token refresh
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== '/api/auth/refresh' &&
      originalRequest.url !== '/api/auth/login'
    ) {
      originalRequest._retry = true

      try {
        // Avoid multiple refresh calls
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken()
        }

        const newToken = await refreshPromise
        refreshPromise = null

        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return api(originalRequest)
        }
      } catch {
        refreshPromise = null
        // Refresh failed - user needs to re-login
        clearAccessToken()
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

// Refresh access token using refresh token cookie
async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await axios.post(
      `${API_BASE}/api/auth/refresh`,
      {},
      { withCredentials: true }
    )
    const newToken = response.data.access_token
    setAccessToken(newToken)
    return newToken
  } catch {
    clearAccessToken()
    return null
  }
}

// Auth API functions
export const authApi = {
  async register(email: string, password: string, displayName: string) {
    const response = await api.post('/api/auth/register', {
      email,
      password,
      display_name: displayName,
    })
    setAccessToken(response.data.access_token)
    return response.data
  },

  async login(email: string, password: string) {
    const response = await api.post('/api/auth/login', {
      email,
      password,
    })
    setAccessToken(response.data.access_token)
    return response.data
  },

  async logout() {
    try {
      await api.post('/api/auth/logout')
    } finally {
      clearAccessToken()
    }
  },

  async refresh() {
    const response = await api.post('/api/auth/refresh')
    setAccessToken(response.data.access_token)
    return response.data
  },

  async getMe() {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  async deleteAccount() {
    await api.delete('/api/auth/account')
    clearAccessToken()
  },
}

// Settings API functions
export const settingsApi = {
  async getSettings() {
    const response = await api.get('/api/user/settings')
    return response.data
  },

  async updateSettings(settings: Record<string, unknown>, version?: number) {
    const response = await api.put('/api/user/settings', {
      settings,
      version,
    })
    return response.data
  },

  async mergeSettings(localSettings: Record<string, unknown>) {
    const response = await api.post('/api/user/settings/merge', {
      local_settings: localSettings,
    })
    return response.data
  },

  async getMultiplayerPlayers() {
    const response = await api.get('/api/user/multiplayer-players')
    return response.data
  },

  async updateMultiplayerPlayers(players: Record<string, unknown>[]) {
    const response = await api.put('/api/user/multiplayer-players', {
      players,
    })
    return response.data
  },
}

// Progress API functions
export const progressApi = {
  async getAll() {
    const response = await api.get('/api/progress/')
    return response.data
  },

  async getForCharacter(character: string) {
    const response = await api.get(`/api/progress/${encodeURIComponent(character)}`)
    return response.data
  },

  async recordAttempt(character: string, fontName: string, score: number, stars: number) {
    const response = await api.post(`/api/progress/${encodeURIComponent(character)}`, {
      font_name: fontName,
      score,
      stars,
    })
    return response.data
  },

  async clearProgress(modes: string[]) {
    const response = await api.delete('/api/progress/', {
      data: { modes },
    })
    return response.data
  },
}

export default api
