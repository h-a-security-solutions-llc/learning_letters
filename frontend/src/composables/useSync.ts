/**
 * Settings sync composable
 * Handles syncing settings between localStorage and server for authenticated users
 */

import { ref, readonly } from 'vue'
import type { AppSettings, Player } from '@/types'
import { settingsApi } from '@/services/api'
import { useAuth } from './useAuth'

const SETTINGS_KEY = 'learning_letters_settings'
const MULTIPLAYER_PLAYERS_KEY = 'learning_letters_multiplayer_players'

// Singleton state
const isSyncing = ref(false)
const syncError = ref<string | null>(null)
const serverVersion = ref<number>(0)
const lastSyncedAt = ref<Date | null>(null)

// Default settings
const defaultSettings: AppSettings = {
  enableBestOf3: true,
  enableTraceMode: true,
  traceModeDefault: false,
  enableDebugMode: false,
  enableStepByStep: true,
  stepByStepDefault: false,
  selectedFont: 'Fredoka-Regular',
  voiceGender: 'rachel',
  autoPlaySound: true,
  rememberMultiplayerPlayers: true,
  highContrastMode: false,
  uiScale: 100,
  reducedMotion: false,
  audioSpeed: 1.0,
  strokeTolerance: 0.5,
  colorBlindMode: false,
  enableCaptions: false,
}

/**
 * Load settings from localStorage
 */
function loadLocalSettings(): AppSettings {
  try {
    const saved = localStorage.getItem(SETTINGS_KEY)
    if (saved) {
      return { ...defaultSettings, ...JSON.parse(saved) }
    }
  } catch (e) {
    console.error('Failed to load settings from localStorage:', e)
  }
  return { ...defaultSettings }
}

/**
 * Save settings to localStorage
 */
function saveLocalSettings(settings: AppSettings): void {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  } catch (e) {
    console.error('Failed to save settings to localStorage:', e)
  }
}

/**
 * Load multiplayer players from localStorage
 */
function loadLocalPlayers(): Player[] {
  try {
    const saved = localStorage.getItem(MULTIPLAYER_PLAYERS_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load multiplayer players from localStorage:', e)
  }
  return []
}

/**
 * Save multiplayer players to localStorage
 */
function saveLocalPlayers(players: Player[]): void {
  try {
    localStorage.setItem(MULTIPLAYER_PLAYERS_KEY, JSON.stringify(players))
  } catch (e) {
    console.error('Failed to save multiplayer players to localStorage:', e)
  }
}

// Composable export
export function useSync() {
  const { isAuthenticated } = useAuth()

  /**
   * Fetch settings from server and update local state
   * Returns the server settings or null if not authenticated
   */
  async function fetchSettings(): Promise<AppSettings | null> {
    if (!isAuthenticated.value) {
      return null
    }

    isSyncing.value = true
    syncError.value = null

    try {
      const response = await settingsApi.getSettings()
      serverVersion.value = response.version
      lastSyncedAt.value = new Date(response.updated_at)

      // Merge server settings with defaults (server overrides defaults)
      const mergedSettings = { ...defaultSettings, ...response.settings }
      return mergedSettings
    } catch (e) {
      console.error('Failed to fetch settings from server:', e)
      syncError.value = 'Failed to sync settings'
      return null
    } finally {
      isSyncing.value = false
    }
  }

  /**
   * Push local settings to server
   * Called after any setting change when authenticated
   */
  async function pushSettings(settings: AppSettings, retryCount = 0): Promise<boolean> {
    if (!isAuthenticated.value) {
      return false
    }

    isSyncing.value = true
    syncError.value = null

    try {
      const response = await settingsApi.updateSettings(settings, serverVersion.value)
      serverVersion.value = response.version
      lastSyncedAt.value = new Date(response.updated_at)
      return true
    } catch (e: unknown) {
      const error = e as { response?: { status?: number } }
      if (error.response?.status === 409 && retryCount < 3) {
        // Conflict - refetch latest version and retry
        syncError.value = 'Settings conflict - retrying'
        await fetchSettings()
        isSyncing.value = false
        return pushSettings(settings, retryCount + 1)
      } else {
        console.error('Failed to push settings to server:', e)
        syncError.value = 'Failed to save settings'
      }
      return false
    } finally {
      isSyncing.value = false
    }
  }

  /**
   * Merge local settings with server on first login
   * Called after successful login/register
   */
  async function mergeOnLogin(): Promise<AppSettings | null> {
    if (!isAuthenticated.value) {
      return null
    }

    isSyncing.value = true
    syncError.value = null

    try {
      const localSettings = loadLocalSettings()
      const response = await settingsApi.mergeSettings(localSettings)
      serverVersion.value = response.version
      lastSyncedAt.value = new Date(response.updated_at)

      // Update local storage with merged settings
      const mergedSettings = { ...defaultSettings, ...response.settings }
      saveLocalSettings(mergedSettings)

      return mergedSettings
    } catch (e) {
      console.error('Failed to merge settings on login:', e)
      syncError.value = 'Failed to sync settings'
      return null
    } finally {
      isSyncing.value = false
    }
  }

  /**
   * Fetch multiplayer players from server
   */
  async function fetchMultiplayerPlayers(): Promise<Player[] | null> {
    if (!isAuthenticated.value) {
      return null
    }

    try {
      const response = await settingsApi.getMultiplayerPlayers()
      return response.players
    } catch (e) {
      console.error('Failed to fetch multiplayer players from server:', e)
      return null
    }
  }

  /**
   * Push multiplayer players to server
   */
  async function pushMultiplayerPlayers(players: Player[]): Promise<boolean> {
    if (!isAuthenticated.value) {
      return false
    }

    try {
      await settingsApi.updateMultiplayerPlayers(players)
      return true
    } catch (e) {
      console.error('Failed to push multiplayer players to server:', e)
      return false
    }
  }

  /**
   * Sync multiplayer players on login
   */
  async function syncMultiplayerPlayersOnLogin(): Promise<Player[]> {
    if (!isAuthenticated.value) {
      return loadLocalPlayers()
    }

    try {
      // Push local players to server (merge strategy: local wins)
      const localPlayers = loadLocalPlayers()
      if (localPlayers.length > 0) {
        await pushMultiplayerPlayers(localPlayers)
      }

      // Fetch merged result
      const serverPlayers = await fetchMultiplayerPlayers()
      if (serverPlayers && serverPlayers.length > 0) {
        saveLocalPlayers(serverPlayers)
        return serverPlayers
      }

      return localPlayers
    } catch (e) {
      console.error('Failed to sync multiplayer players on login:', e)
      return loadLocalPlayers()
    }
  }

  return {
    // State
    isSyncing: readonly(isSyncing),
    syncError: readonly(syncError),
    serverVersion: readonly(serverVersion),
    lastSyncedAt: readonly(lastSyncedAt),

    // Settings sync
    fetchSettings,
    pushSettings,
    mergeOnLogin,

    // Multiplayer players sync
    fetchMultiplayerPlayers,
    pushMultiplayerPlayers,
    syncMultiplayerPlayersOnLogin,

    // Local storage helpers (for guest mode)
    loadLocalSettings,
    saveLocalSettings,
    loadLocalPlayers,
    saveLocalPlayers,
    defaultSettings,
  }
}
