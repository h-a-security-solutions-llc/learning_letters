import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  progressStorage,
  settingsStorage,
  multiplayerStorage,
  defaultSettings,
  type AppSettings,
  type MultiplayerPlayer
} from '../storage'

describe('progressStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('getAll', () => {
    it('returns empty object when no progress saved', () => {
      const result = progressStorage.getAll()
      expect(result).toEqual({})
    })

    it('returns saved progress', () => {
      const progress = {
        'A_Fredoka-Regular_freestyle': {
          highScore: 85,
          stars: 4,
          attempts: 3,
          lastAttempt: Date.now()
        }
      }
      localStorage.setItem('ll_progress', JSON.stringify(progress))

      const result = progressStorage.getAll()
      expect(result).toEqual(progress)
    })

    it('handles invalid JSON gracefully', () => {
      localStorage.setItem('ll_progress', 'invalid json')

      const result = progressStorage.getAll()
      expect(result).toEqual({})
    })
  })

  describe('get', () => {
    it('returns null when no progress for character', () => {
      const result = progressStorage.get('A', 'Fredoka-Regular', 'freestyle')
      expect(result).toBeNull()
    })

    it('returns progress entry when exists', () => {
      const entry = {
        highScore: 85,
        stars: 4,
        attempts: 3,
        lastAttempt: Date.now()
      }
      localStorage.setItem('ll_progress', JSON.stringify({
        'A_Fredoka-Regular_freestyle': entry
      }))

      const result = progressStorage.get('A', 'Fredoka-Regular', 'freestyle')
      expect(result).toEqual(entry)
    })
  })

  describe('record', () => {
    it('creates new entry when none exists', () => {
      const result = progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 75, 4)

      expect(result.isNewHighScore).toBe(true)
      expect(result.previousHighScore).toBeNull()

      const saved = progressStorage.get('A', 'Fredoka-Regular', 'freestyle')
      expect(saved?.highScore).toBe(75)
      expect(saved?.stars).toBe(4)
      expect(saved?.attempts).toBe(1)
    })

    it('updates high score when new score is higher', () => {
      progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 75, 4)
      const result = progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 90, 5)

      expect(result.isNewHighScore).toBe(true)
      expect(result.previousHighScore).toBe(75)

      const saved = progressStorage.get('A', 'Fredoka-Regular', 'freestyle')
      expect(saved?.highScore).toBe(90)
      expect(saved?.stars).toBe(5)
      expect(saved?.attempts).toBe(2)
    })

    it('does not update high score when new score is lower', () => {
      progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 90, 5)
      const result = progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 75, 4)

      expect(result.isNewHighScore).toBe(false)
      expect(result.previousHighScore).toBe(90)

      const saved = progressStorage.get('A', 'Fredoka-Regular', 'freestyle')
      expect(saved?.highScore).toBe(90)
      expect(saved?.stars).toBe(5)
      expect(saved?.attempts).toBe(2)
    })
  })

  describe('getHighScore', () => {
    it('returns null when no progress exists', () => {
      const result = progressStorage.getHighScore('A', 'Fredoka-Regular', 'freestyle')
      expect(result).toBeNull()
    })

    it('returns high score when exists', () => {
      progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 85, 4)

      const result = progressStorage.getHighScore('A', 'Fredoka-Regular', 'freestyle')
      expect(result).toBe(85)
    })
  })

  describe('clear', () => {
    it('clears all progress when no modes specified', () => {
      progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 85, 4)
      progressStorage.record('B', 'Fredoka-Regular', 'tracing', 90, 5)

      progressStorage.clear()

      expect(progressStorage.getAll()).toEqual({})
    })

    it('clears only specified modes', () => {
      progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 85, 4)
      progressStorage.record('B', 'Fredoka-Regular', 'tracing', 90, 5)
      progressStorage.record('C', 'Fredoka-Regular', 'step-by-step', 80, 4)

      progressStorage.clear(['freestyle'])

      const all = progressStorage.getAll()
      expect(all['A_Fredoka-Regular_freestyle']).toBeUndefined()
      expect(all['B_Fredoka-Regular_tracing']).toBeDefined()
      expect(all['C_Fredoka-Regular_step-by-step']).toBeDefined()
    })
  })

  describe('getFormattedProgress', () => {
    it('returns empty array when no progress', () => {
      const result = progressStorage.getFormattedProgress('Fredoka-Regular')
      expect(result).toEqual([])
    })

    it('returns formatted progress for specific font', () => {
      progressStorage.record('A', 'Fredoka-Regular', 'freestyle', 85, 4)
      progressStorage.record('B', 'Fredoka-Regular', 'tracing', 90, 5)
      progressStorage.record('C', 'Nunito-Regular', 'freestyle', 80, 4)

      const result = progressStorage.getFormattedProgress('Fredoka-Regular')

      expect(result.length).toBe(2)
      expect(result).toContainEqual({
        character: 'A',
        font_name: 'Fredoka-Regular',
        mode: 'freestyle',
        high_score: 85,
        stars: 4
      })
      expect(result).toContainEqual({
        character: 'B',
        font_name: 'Fredoka-Regular',
        mode: 'tracing',
        high_score: 90,
        stars: 5
      })
    })
  })
})

describe('settingsStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('load', () => {
    it('returns default settings when none saved', () => {
      const result = settingsStorage.load()
      expect(result).toEqual(defaultSettings)
    })

    it('returns saved settings merged with defaults', () => {
      const partialSettings = {
        selectedFont: 'Nunito-Regular',
        voiceGender: 'adam'
      }
      localStorage.setItem('ll_settings', JSON.stringify(partialSettings))

      const result = settingsStorage.load()

      expect(result.selectedFont).toBe('Nunito-Regular')
      expect(result.voiceGender).toBe('adam')
      expect(result.enableBestOf3).toBe(defaultSettings.enableBestOf3)
    })

    it('handles invalid JSON gracefully', () => {
      localStorage.setItem('ll_settings', 'invalid json')

      const result = settingsStorage.load()
      expect(result).toEqual(defaultSettings)
    })
  })

  describe('save', () => {
    it('saves settings to localStorage', () => {
      const settings: AppSettings = {
        ...defaultSettings,
        selectedFont: 'Nunito-Regular',
        voiceGender: 'adam'
      }

      settingsStorage.save(settings)

      const saved = JSON.parse(localStorage.getItem('ll_settings') || '{}')
      expect(saved.selectedFont).toBe('Nunito-Regular')
      expect(saved.voiceGender).toBe('adam')
    })
  })
})

describe('multiplayerStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('load', () => {
    it('returns empty array when no players saved', () => {
      const result = multiplayerStorage.load()
      expect(result).toEqual([])
    })

    it('returns saved players', () => {
      const players: MultiplayerPlayer[] = [
        { name: 'Player 1', traceModeAllowed: true, stepByStepAllowed: false },
        { name: 'Player 2', traceModeAllowed: false, stepByStepAllowed: true }
      ]
      localStorage.setItem('ll_multiplayer_players', JSON.stringify(players))

      const result = multiplayerStorage.load()
      expect(result).toEqual(players)
    })

    it('handles invalid JSON gracefully', () => {
      localStorage.setItem('ll_multiplayer_players', 'invalid json')

      const result = multiplayerStorage.load()
      expect(result).toEqual([])
    })
  })

  describe('save', () => {
    it('saves players to localStorage', () => {
      const players: MultiplayerPlayer[] = [
        { name: 'Alice', traceModeAllowed: true, stepByStepAllowed: true }
      ]

      multiplayerStorage.save(players)

      const saved = JSON.parse(localStorage.getItem('ll_multiplayer_players') || '[]')
      expect(saved).toEqual(players)
    })
  })
})

describe('defaultSettings', () => {
  it('has expected default values', () => {
    expect(defaultSettings.enableBestOf3).toBe(true)
    expect(defaultSettings.enableTraceMode).toBe(true)
    expect(defaultSettings.traceModeDefault).toBe(false)
    expect(defaultSettings.enableDebugMode).toBe(false)
    expect(defaultSettings.enableStepByStep).toBe(true)
    expect(defaultSettings.stepByStepDefault).toBe(false)
    expect(defaultSettings.selectedFont).toBe('Fredoka-Regular')
    expect(defaultSettings.voiceGender).toBe('rachel')
    expect(defaultSettings.autoPlaySound).toBe(true)
    expect(defaultSettings.highContrastMode).toBe(false)
    expect(defaultSettings.uiScale).toBe(100)
    expect(defaultSettings.audioSpeed).toBe(1.0)
    expect(defaultSettings.strokeTolerance).toBe(0.5)
    expect(defaultSettings.colorBlindMode).toBe(false)
    expect(defaultSettings.enableCaptions).toBe(false)
  })
})
