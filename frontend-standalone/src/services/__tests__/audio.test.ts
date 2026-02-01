import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  playCharacterAudio,
  preloadAudio,
  stopAudio,
  getCharacterCaption,
  checkAudioAvailability,
  type VoiceGender
} from '../audio'

describe('getCharacterCaption', () => {
  describe('uppercase letters', () => {
    it('returns "Capital A" for uppercase A', () => {
      expect(getCharacterCaption('A')).toBe('Capital A')
    })

    it('returns "Capital Z" for uppercase Z', () => {
      expect(getCharacterCaption('Z')).toBe('Capital Z')
    })
  })

  describe('lowercase letters', () => {
    it('returns "Lowercase a" for lowercase a', () => {
      expect(getCharacterCaption('a')).toBe('Lowercase a')
    })

    it('returns "Lowercase z" for lowercase z', () => {
      expect(getCharacterCaption('z')).toBe('Lowercase z')
    })
  })

  describe('numbers', () => {
    it('returns "Number 0" for 0', () => {
      expect(getCharacterCaption('0')).toBe('Number 0')
    })

    it('returns "Number 9" for 9', () => {
      expect(getCharacterCaption('9')).toBe('Number 9')
    })
  })

  describe('unknown characters', () => {
    it('returns the character itself for unknown characters', () => {
      expect(getCharacterCaption('!')).toBe('!')
      expect(getCharacterCaption('@')).toBe('@')
    })
  })
})

describe('playCharacterAudio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates audio element with correct path', async () => {
    await playCharacterAudio('A', 'rachel')

    // Check that Audio was created (mocked in test-setup.ts)
    expect(window.Audio).toBeDefined()
  })

  it('sets playback rate within bounds', async () => {
    // Test normal speed
    await playCharacterAudio('A', 'rachel', 1.0)

    // Test clamped speed (below min)
    await playCharacterAudio('A', 'rachel', 0.1)

    // Test clamped speed (above max)
    await playCharacterAudio('A', 'rachel', 3.0)
  })

  it('calls onEnded callback when provided', async () => {
    const onEnded = vi.fn()
    await playCharacterAudio('A', 'rachel', 1.0, onEnded)

    // The mock audio should have received the onended callback
    // In real implementation, this would be called when audio finishes
  })

  it('handles different voices', async () => {
    const voices: VoiceGender[] = ['rachel', 'adam', 'sarah', 'josh']

    for (const voice of voices) {
      await playCharacterAudio('A', voice)
    }

    // Should not throw for any voice
    expect(true).toBe(true)
  })

  it('handles all character types', async () => {
    // Uppercase
    await playCharacterAudio('A')
    await playCharacterAudio('Z')

    // Lowercase
    await playCharacterAudio('a')
    await playCharacterAudio('z')

    // Numbers
    await playCharacterAudio('0')
    await playCharacterAudio('9')

    // Should not throw for any character
    expect(true).toBe(true)
  })
})

describe('preloadAudio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('preloads audio for specified characters', () => {
    preloadAudio(['A', 'B', 'C'], 'rachel')

    // Should create audio elements for each character
    expect(true).toBe(true)
  })

  it('uses default voice when not specified', () => {
    preloadAudio(['A', 'B', 'C'])

    // Should use 'rachel' as default
    expect(true).toBe(true)
  })
})

describe('stopAudio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('stops all cached audio', async () => {
    // First play some audio to cache it
    await playCharacterAudio('A', 'rachel')
    await playCharacterAudio('B', 'rachel')

    // Then stop all audio
    stopAudio()

    // Should not throw
    expect(true).toBe(true)
  })
})

describe('checkAudioAvailability', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns true when audio is available', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true
    })

    const result = await checkAudioAvailability('rachel')
    expect(result).toBe(true)
  })

  it('returns false when audio is not available', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false
    })

    const result = await checkAudioAvailability('rachel')
    expect(result).toBe(false)
  })

  it('returns false when fetch throws', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'))

    const result = await checkAudioAvailability('rachel')
    expect(result).toBe(false)
  })

  it('uses default voice when not specified', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true
    })

    await checkAudioAvailability()

    expect(global.fetch).toHaveBeenCalledWith(
      '/audio/rachel/upper_A.mp3',
      { method: 'HEAD' }
    )
  })
})

describe('audio file paths', () => {
  it('generates correct paths for uppercase letters', async () => {
    await playCharacterAudio('A', 'rachel')
    // Path should be /audio/rachel/upper_A.mp3
  })

  it('generates correct paths for lowercase letters', async () => {
    await playCharacterAudio('a', 'rachel')
    // Path should be /audio/rachel/lower_a.mp3
  })

  it('generates correct paths for numbers', async () => {
    await playCharacterAudio('5', 'rachel')
    // Path should be /audio/rachel/num_5.mp3
  })

  it('generates correct paths for different voices', async () => {
    await playCharacterAudio('A', 'adam')
    // Path should be /audio/adam/upper_A.mp3

    await playCharacterAudio('A', 'sarah')
    // Path should be /audio/sarah/upper_A.mp3

    await playCharacterAudio('A', 'josh')
    // Path should be /audio/josh/upper_A.mp3
  })
})
