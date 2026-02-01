import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useAudioCaptions } from '../useAudioCaptions'

// Mock the audio service
vi.mock('@/services/audio', () => ({
  getCharacterCaption: vi.fn((char: string) => {
    if (char >= 'A' && char <= 'Z') return `Capital ${char}`
    if (char >= 'a' && char <= 'z') return `Lowercase ${char}`
    if (char >= '0' && char <= '9') return `Number ${char}`
    return char
  })
}))

describe('useAudioCaptions', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('initial state', () => {
    it('has null currentCaption initially', () => {
      const { currentCaption } = useAudioCaptions()
      expect(currentCaption.value).toBeNull()
    })

    it('has isVisible as false initially', () => {
      const { isVisible } = useAudioCaptions()
      expect(isVisible.value).toBe(false)
    })
  })

  describe('showCaption', () => {
    it('sets currentCaption for uppercase letter', () => {
      const { currentCaption, showCaption } = useAudioCaptions()

      showCaption('A')

      expect(currentCaption.value).toBe('Capital A')
    })

    it('sets currentCaption for lowercase letter', () => {
      const { currentCaption, showCaption } = useAudioCaptions()

      showCaption('a')

      expect(currentCaption.value).toBe('Lowercase a')
    })

    it('sets currentCaption for number', () => {
      const { currentCaption, showCaption } = useAudioCaptions()

      showCaption('5')

      expect(currentCaption.value).toBe('Number 5')
    })

    it('sets isVisible to true', () => {
      const { isVisible, showCaption } = useAudioCaptions()

      showCaption('A')

      expect(isVisible.value).toBe(true)
    })

    it('clears pending hide timeout when showing new caption', () => {
      const { showCaption, hideCaptionAfterDelay, isVisible } = useAudioCaptions()

      showCaption('A')
      hideCaptionAfterDelay(500)

      // Show new caption before timeout completes
      showCaption('B')

      // Advance past the original timeout
      vi.advanceTimersByTime(600)

      // Caption should still be visible because we showed a new one
      expect(isVisible.value).toBe(true)
    })
  })

  describe('hideCaptionAfterDelay', () => {
    it('hides caption after specified delay', () => {
      const { showCaption, hideCaptionAfterDelay, isVisible } = useAudioCaptions()

      showCaption('A')
      hideCaptionAfterDelay(500)

      expect(isVisible.value).toBe(true)

      vi.advanceTimersByTime(500)

      expect(isVisible.value).toBe(false)
    })

    it('uses default delay of 800ms', () => {
      const { showCaption, hideCaptionAfterDelay, isVisible } = useAudioCaptions()

      showCaption('A')
      hideCaptionAfterDelay()

      expect(isVisible.value).toBe(true)

      vi.advanceTimersByTime(799)
      expect(isVisible.value).toBe(true)

      vi.advanceTimersByTime(1)
      expect(isVisible.value).toBe(false)
    })

    it('clears caption text after fade out', () => {
      const { showCaption, hideCaptionAfterDelay, currentCaption, isVisible } = useAudioCaptions()

      showCaption('A')
      hideCaptionAfterDelay(500)

      // First the visibility goes false
      vi.advanceTimersByTime(500)
      expect(isVisible.value).toBe(false)

      // Then after 300ms fade out, caption text is cleared
      vi.advanceTimersByTime(300)
      expect(currentCaption.value).toBeNull()
    })

    it('does not clear caption if new caption is shown during fade out', () => {
      const { showCaption, hideCaptionAfterDelay, currentCaption, isVisible } = useAudioCaptions()

      showCaption('A')
      hideCaptionAfterDelay(500)

      // Wait for visibility to go false
      vi.advanceTimersByTime(500)
      expect(isVisible.value).toBe(false)

      // Show new caption during the fade out period
      showCaption('B')

      // Wait for the original fade out clear
      vi.advanceTimersByTime(300)

      // Caption should be the new one, not null
      expect(currentCaption.value).toBe('Capital B')
      expect(isVisible.value).toBe(true)
    })
  })

  describe('hideCaption', () => {
    it('immediately hides the caption', () => {
      const { showCaption, hideCaption, isVisible, currentCaption } = useAudioCaptions()

      showCaption('A')
      expect(isVisible.value).toBe(true)

      hideCaption()

      expect(isVisible.value).toBe(false)
      expect(currentCaption.value).toBeNull()
    })

    it('clears any pending hide timeout', () => {
      const { showCaption, hideCaptionAfterDelay, hideCaption, isVisible } = useAudioCaptions()

      showCaption('A')
      hideCaptionAfterDelay(500)

      // Hide immediately
      hideCaption()

      expect(isVisible.value).toBe(false)

      // Show again
      showCaption('B')

      // Advance past the original timeout
      vi.advanceTimersByTime(600)

      // Should still be visible because we cleared the timeout
      expect(isVisible.value).toBe(true)
    })
  })

  describe('multiple captions in sequence', () => {
    it('handles rapid caption changes', () => {
      const { showCaption, hideCaptionAfterDelay, currentCaption, isVisible } = useAudioCaptions()

      showCaption('A')
      hideCaptionAfterDelay(500)

      vi.advanceTimersByTime(200)

      showCaption('B')
      hideCaptionAfterDelay(500)

      vi.advanceTimersByTime(200)

      showCaption('C')
      hideCaptionAfterDelay(500)

      expect(currentCaption.value).toBe('Capital C')
      expect(isVisible.value).toBe(true)

      vi.advanceTimersByTime(500)

      expect(isVisible.value).toBe(false)
    })
  })
})
