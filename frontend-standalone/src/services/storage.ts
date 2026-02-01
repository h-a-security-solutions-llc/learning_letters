/**
 * Storage Service - localStorage-based persistence
 *
 * Provides persistent storage for user progress, settings, and preferences
 * without requiring a backend server.
 */

const STORAGE_KEYS = {
  PROGRESS: 'll_progress',
  SETTINGS: 'll_settings',
  MULTIPLAYER_PLAYERS: 'll_multiplayer_players',
} as const

// ============================================================================
// Progress Storage
// ============================================================================

export interface ProgressEntry {
  highScore: number
  stars: number
  attempts: number
  lastAttempt: number
}

export type ProgressStore = Record<string, ProgressEntry>

function getProgressKey(character: string, font: string, mode: string): string {
  return `${character}_${font}_${mode}`
}

export const progressStorage = {
  /**
   * Get all progress entries
   */
  getAll(): ProgressStore {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.PROGRESS)
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  },

  /**
   * Get progress for a specific character/font/mode combination
   */
  get(character: string, font: string, mode: string): ProgressEntry | null {
    const store = this.getAll()
    const key = getProgressKey(character, font, mode)
    return store[key] || null
  },

  /**
   * Record a new attempt and update high score if necessary
   */
  record(
    character: string,
    font: string,
    mode: string,
    score: number,
    stars: number
  ): { isNewHighScore: boolean; previousHighScore: number | null } {
    const key = getProgressKey(character, font, mode)
    const store = this.getAll()
    const existing = store[key]

    const previousHighScore = existing?.highScore ?? null
    const isNewHighScore = !existing || score > existing.highScore

    store[key] = {
      highScore: isNewHighScore ? score : existing.highScore,
      stars: isNewHighScore ? stars : existing.stars,
      attempts: (existing?.attempts || 0) + 1,
      lastAttempt: Date.now(),
    }

    localStorage.setItem(STORAGE_KEYS.PROGRESS, JSON.stringify(store))
    return { isNewHighScore, previousHighScore }
  },

  /**
   * Get high score for a specific combination
   */
  getHighScore(character: string, font: string, mode: string): number | null {
    const entry = this.get(character, font, mode)
    return entry?.highScore ?? null
  },

  /**
   * Clear progress for specific modes, or all progress if no modes specified
   */
  clear(modes?: string[]): void {
    if (!modes || modes.length === 0) {
      localStorage.removeItem(STORAGE_KEYS.PROGRESS)
      return
    }

    const store = this.getAll()
    for (const key of Object.keys(store)) {
      if (modes.some(m => key.endsWith(`_${m}`))) {
        delete store[key]
      }
    }
    localStorage.setItem(STORAGE_KEYS.PROGRESS, JSON.stringify(store))
  },

  /**
   * Get progress formatted for CharacterSelection component
   */
  getFormattedProgress(font: string): Array<{
    character: string
    font_name: string
    mode: string
    high_score: number
    stars: number
  }> {
    const store = this.getAll()
    const result: Array<{
      character: string
      font_name: string
      mode: string
      high_score: number
      stars: number
    }> = []

    for (const [key, entry] of Object.entries(store)) {
      const parts = key.split('_')
      if (parts.length >= 3) {
        const mode = parts.pop()!
        const fontName = parts.pop()!
        const character = parts.join('_') // Handle edge cases

        if (fontName === font) {
          result.push({
            character,
            font_name: fontName,
            mode,
            high_score: entry.highScore,
            stars: entry.stars,
          })
        }
      }
    }

    return result
  },
}

// ============================================================================
// Settings Storage
// ============================================================================

export interface AppSettings {
  enableBestOf3: boolean
  enableTraceMode: boolean
  traceModeDefault: boolean
  enableDebugMode: boolean
  enableStepByStep: boolean
  stepByStepDefault: boolean
  selectedFont: string
  voiceGender: string
  autoPlaySound: boolean
  rememberMultiplayerPlayers: boolean
  highContrastMode: boolean
  uiScale: number
  reducedMotion: boolean | null
  audioSpeed: number
  strokeTolerance: number
  colorBlindMode: boolean
  enableCaptions: boolean
}

export const defaultSettings: AppSettings = {
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

export const settingsStorage = {
  /**
   * Load settings from localStorage
   */
  load(): AppSettings {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.SETTINGS)
      if (saved) {
        return { ...defaultSettings, ...JSON.parse(saved) }
      }
    } catch {
      // Ignore parse errors
    }
    return { ...defaultSettings }
  },

  /**
   * Save settings to localStorage
   */
  save(settings: AppSettings): void {
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings))
    } catch {
      console.error('Failed to save settings')
    }
  },
}

// ============================================================================
// Multiplayer Players Storage
// ============================================================================

export interface MultiplayerPlayer {
  name: string
  traceModeAllowed: boolean
  stepByStepAllowed: boolean
}

export const multiplayerStorage = {
  /**
   * Load saved multiplayer player configurations
   */
  load(): MultiplayerPlayer[] {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.MULTIPLAYER_PLAYERS)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  },

  /**
   * Save multiplayer player configurations
   */
  save(players: MultiplayerPlayer[]): void {
    try {
      localStorage.setItem(STORAGE_KEYS.MULTIPLAYER_PLAYERS, JSON.stringify(players))
    } catch {
      console.error('Failed to save multiplayer players')
    }
  },
}
