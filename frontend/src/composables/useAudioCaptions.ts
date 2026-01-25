import { ref } from 'vue'

// Caption data for each character
export interface CharacterCaption {
  text: string
  phonetic: string
  fullText: string
}

export const characterCaptions: Record<string, CharacterCaption> = {
  // Uppercase letters
  'A': { text: 'A', phonetic: 'ay', fullText: 'The letter A' },
  'B': { text: 'B', phonetic: 'bee', fullText: 'The letter B' },
  'C': { text: 'C', phonetic: 'see', fullText: 'The letter C' },
  'D': { text: 'D', phonetic: 'dee', fullText: 'The letter D' },
  'E': { text: 'E', phonetic: 'ee', fullText: 'The letter E' },
  'F': { text: 'F', phonetic: 'ef', fullText: 'The letter F' },
  'G': { text: 'G', phonetic: 'jee', fullText: 'The letter G' },
  'H': { text: 'H', phonetic: 'aych', fullText: 'The letter H' },
  'I': { text: 'I', phonetic: 'eye', fullText: 'The letter I' },
  'J': { text: 'J', phonetic: 'jay', fullText: 'The letter J' },
  'K': { text: 'K', phonetic: 'kay', fullText: 'The letter K' },
  'L': { text: 'L', phonetic: 'el', fullText: 'The letter L' },
  'M': { text: 'M', phonetic: 'em', fullText: 'The letter M' },
  'N': { text: 'N', phonetic: 'en', fullText: 'The letter N' },
  'O': { text: 'O', phonetic: 'oh', fullText: 'The letter O' },
  'P': { text: 'P', phonetic: 'pee', fullText: 'The letter P' },
  'Q': { text: 'Q', phonetic: 'kyoo', fullText: 'The letter Q' },
  'R': { text: 'R', phonetic: 'ar', fullText: 'The letter R' },
  'S': { text: 'S', phonetic: 'ess', fullText: 'The letter S' },
  'T': { text: 'T', phonetic: 'tee', fullText: 'The letter T' },
  'U': { text: 'U', phonetic: 'yoo', fullText: 'The letter U' },
  'V': { text: 'V', phonetic: 'vee', fullText: 'The letter V' },
  'W': { text: 'W', phonetic: 'double-yoo', fullText: 'The letter W' },
  'X': { text: 'X', phonetic: 'eks', fullText: 'The letter X' },
  'Y': { text: 'Y', phonetic: 'why', fullText: 'The letter Y' },
  'Z': { text: 'Z', phonetic: 'zee', fullText: 'The letter Z' },
  // Lowercase letters
  'a': { text: 'a', phonetic: 'ay', fullText: 'Lowercase a' },
  'b': { text: 'b', phonetic: 'bee', fullText: 'Lowercase b' },
  'c': { text: 'c', phonetic: 'see', fullText: 'Lowercase c' },
  'd': { text: 'd', phonetic: 'dee', fullText: 'Lowercase d' },
  'e': { text: 'e', phonetic: 'ee', fullText: 'Lowercase e' },
  'f': { text: 'f', phonetic: 'ef', fullText: 'Lowercase f' },
  'g': { text: 'g', phonetic: 'jee', fullText: 'Lowercase g' },
  'h': { text: 'h', phonetic: 'aych', fullText: 'Lowercase h' },
  'i': { text: 'i', phonetic: 'eye', fullText: 'Lowercase i' },
  'j': { text: 'j', phonetic: 'jay', fullText: 'Lowercase j' },
  'k': { text: 'k', phonetic: 'kay', fullText: 'Lowercase k' },
  'l': { text: 'l', phonetic: 'el', fullText: 'Lowercase l' },
  'm': { text: 'm', phonetic: 'em', fullText: 'Lowercase m' },
  'n': { text: 'n', phonetic: 'en', fullText: 'Lowercase n' },
  'o': { text: 'o', phonetic: 'oh', fullText: 'Lowercase o' },
  'p': { text: 'p', phonetic: 'pee', fullText: 'Lowercase p' },
  'q': { text: 'q', phonetic: 'kyoo', fullText: 'Lowercase q' },
  'r': { text: 'r', phonetic: 'ar', fullText: 'Lowercase r' },
  's': { text: 's', phonetic: 'ess', fullText: 'Lowercase s' },
  't': { text: 't', phonetic: 'tee', fullText: 'Lowercase t' },
  'u': { text: 'u', phonetic: 'yoo', fullText: 'Lowercase u' },
  'v': { text: 'v', phonetic: 'vee', fullText: 'Lowercase v' },
  'w': { text: 'w', phonetic: 'double-yoo', fullText: 'Lowercase w' },
  'x': { text: 'x', phonetic: 'eks', fullText: 'Lowercase x' },
  'y': { text: 'y', phonetic: 'why', fullText: 'Lowercase y' },
  'z': { text: 'z', phonetic: 'zee', fullText: 'Lowercase z' },
  // Numbers
  '0': { text: '0', phonetic: 'zero', fullText: 'The number 0' },
  '1': { text: '1', phonetic: 'one', fullText: 'The number 1' },
  '2': { text: '2', phonetic: 'two', fullText: 'The number 2' },
  '3': { text: '3', phonetic: 'three', fullText: 'The number 3' },
  '4': { text: '4', phonetic: 'four', fullText: 'The number 4' },
  '5': { text: '5', phonetic: 'five', fullText: 'The number 5' },
  '6': { text: '6', phonetic: 'six', fullText: 'The number 6' },
  '7': { text: '7', phonetic: 'seven', fullText: 'The number 7' },
  '8': { text: '8', phonetic: 'eight', fullText: 'The number 8' },
  '9': { text: '9', phonetic: 'nine', fullText: 'The number 9' }
}

// Composable for managing audio caption visibility
export function useAudioCaptions() {
  const currentCaption = ref<CharacterCaption | null>(null)
  const isVisible = ref(false)
  let hideTimeout: ReturnType<typeof setTimeout> | null = null

  const showCaption = (character: string) => {
    const caption = characterCaptions[character]
    if (caption) {
      currentCaption.value = caption
      isVisible.value = true

      // Clear any existing timeout
      if (hideTimeout) {
        clearTimeout(hideTimeout)
      }
    }
  }

  const hideCaption = () => {
    isVisible.value = false
    // Delay clearing the caption to allow fade out animation
    hideTimeout = setTimeout(() => {
      currentCaption.value = null
    }, 300)
  }

  const hideCaptionAfterDelay = (delayMs: number = 800) => {
    if (hideTimeout) {
      clearTimeout(hideTimeout)
    }
    hideTimeout = setTimeout(() => {
      hideCaption()
    }, delayMs)
  }

  return {
    currentCaption,
    isVisible,
    showCaption,
    hideCaption,
    hideCaptionAfterDelay
  }
}

export function getCaption(character: string): CharacterCaption | null {
  return characterCaptions[character] || null
}
