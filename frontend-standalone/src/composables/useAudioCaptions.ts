import { ref } from 'vue'
import { getCharacterCaption } from '@/services/audio'

/**
 * Composable for managing audio captions for accessibility
 */
export function useAudioCaptions() {
  const currentCaption = ref<string | null>(null)
  const isVisible = ref(false)
  let hideTimeout: ReturnType<typeof setTimeout> | null = null

  /**
   * Show a caption for a character
   */
  function showCaption(character: string) {
    // Clear any pending hide
    if (hideTimeout) {
      clearTimeout(hideTimeout)
      hideTimeout = null
    }

    currentCaption.value = getCharacterCaption(character)
    isVisible.value = true
  }

  /**
   * Hide the caption after a delay
   */
  function hideCaptionAfterDelay(delayMs: number = 800) {
    hideTimeout = setTimeout(() => {
      isVisible.value = false
      // Clear caption text after fade out
      setTimeout(() => {
        if (!isVisible.value) {
          currentCaption.value = null
        }
      }, 300)
    }, delayMs)
  }

  /**
   * Immediately hide the caption
   */
  function hideCaption() {
    if (hideTimeout) {
      clearTimeout(hideTimeout)
      hideTimeout = null
    }
    isVisible.value = false
    currentCaption.value = null
  }

  return {
    currentCaption,
    isVisible,
    showCaption,
    hideCaptionAfterDelay,
    hideCaption,
  }
}
