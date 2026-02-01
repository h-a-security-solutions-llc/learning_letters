/**
 * Audio Service - Bundled audio playback
 *
 * Provides audio playback for character pronunciations using bundled MP3 files.
 * Supports multiple voices (rachel, adam, sarah, josh) and playback speed control.
 */

export type VoiceGender = 'rachel' | 'adam' | 'sarah' | 'josh'

// Character data with pronunciations
const CHARACTER_DATA: Record<string, { name: string; type: string }> = {
  // Uppercase letters
  'A': { name: 'upper_A', type: 'uppercase' },
  'B': { name: 'upper_B', type: 'uppercase' },
  'C': { name: 'upper_C', type: 'uppercase' },
  'D': { name: 'upper_D', type: 'uppercase' },
  'E': { name: 'upper_E', type: 'uppercase' },
  'F': { name: 'upper_F', type: 'uppercase' },
  'G': { name: 'upper_G', type: 'uppercase' },
  'H': { name: 'upper_H', type: 'uppercase' },
  'I': { name: 'upper_I', type: 'uppercase' },
  'J': { name: 'upper_J', type: 'uppercase' },
  'K': { name: 'upper_K', type: 'uppercase' },
  'L': { name: 'upper_L', type: 'uppercase' },
  'M': { name: 'upper_M', type: 'uppercase' },
  'N': { name: 'upper_N', type: 'uppercase' },
  'O': { name: 'upper_O', type: 'uppercase' },
  'P': { name: 'upper_P', type: 'uppercase' },
  'Q': { name: 'upper_Q', type: 'uppercase' },
  'R': { name: 'upper_R', type: 'uppercase' },
  'S': { name: 'upper_S', type: 'uppercase' },
  'T': { name: 'upper_T', type: 'uppercase' },
  'U': { name: 'upper_U', type: 'uppercase' },
  'V': { name: 'upper_V', type: 'uppercase' },
  'W': { name: 'upper_W', type: 'uppercase' },
  'X': { name: 'upper_X', type: 'uppercase' },
  'Y': { name: 'upper_Y', type: 'uppercase' },
  'Z': { name: 'upper_Z', type: 'uppercase' },
  // Lowercase letters
  'a': { name: 'lower_a', type: 'lowercase' },
  'b': { name: 'lower_b', type: 'lowercase' },
  'c': { name: 'lower_c', type: 'lowercase' },
  'd': { name: 'lower_d', type: 'lowercase' },
  'e': { name: 'lower_e', type: 'lowercase' },
  'f': { name: 'lower_f', type: 'lowercase' },
  'g': { name: 'lower_g', type: 'lowercase' },
  'h': { name: 'lower_h', type: 'lowercase' },
  'i': { name: 'lower_i', type: 'lowercase' },
  'j': { name: 'lower_j', type: 'lowercase' },
  'k': { name: 'lower_k', type: 'lowercase' },
  'l': { name: 'lower_l', type: 'lowercase' },
  'm': { name: 'lower_m', type: 'lowercase' },
  'n': { name: 'lower_n', type: 'lowercase' },
  'o': { name: 'lower_o', type: 'lowercase' },
  'p': { name: 'lower_p', type: 'lowercase' },
  'q': { name: 'lower_q', type: 'lowercase' },
  'r': { name: 'lower_r', type: 'lowercase' },
  's': { name: 'lower_s', type: 'lowercase' },
  't': { name: 'lower_t', type: 'lowercase' },
  'u': { name: 'lower_u', type: 'lowercase' },
  'v': { name: 'lower_v', type: 'lowercase' },
  'w': { name: 'lower_w', type: 'lowercase' },
  'x': { name: 'lower_x', type: 'lowercase' },
  'y': { name: 'lower_y', type: 'lowercase' },
  'z': { name: 'lower_z', type: 'lowercase' },
  // Numbers
  '0': { name: 'num_0', type: 'number' },
  '1': { name: 'num_1', type: 'number' },
  '2': { name: 'num_2', type: 'number' },
  '3': { name: 'num_3', type: 'number' },
  '4': { name: 'num_4', type: 'number' },
  '5': { name: 'num_5', type: 'number' },
  '6': { name: 'num_6', type: 'number' },
  '7': { name: 'num_7', type: 'number' },
  '8': { name: 'num_8', type: 'number' },
  '9': { name: 'num_9', type: 'number' },
}

// Audio element cache
const audioCache = new Map<string, HTMLAudioElement>()

/**
 * Get the audio file path for a character
 */
function getAudioPath(character: string, voice: VoiceGender): string {
  const charData = CHARACTER_DATA[character]
  if (!charData) {
    throw new Error(`Unknown character: ${character}`)
  }
  return `/audio/${voice}/${charData.name}.mp3`
}

/**
 * Get or create a cached audio element
 */
function getAudioElement(character: string, voice: VoiceGender): HTMLAudioElement {
  const cacheKey = `${voice}_${character}`

  if (audioCache.has(cacheKey)) {
    return audioCache.get(cacheKey)!
  }

  const audio = new Audio(getAudioPath(character, voice))
  audioCache.set(cacheKey, audio)
  return audio
}

/**
 * Play the pronunciation of a character
 *
 * @param character - The character to pronounce
 * @param voice - The voice to use (rachel, adam, sarah, josh)
 * @param speed - Playback speed (0.5 to 2.0)
 * @param onEnded - Optional callback when playback finishes
 */
export async function playCharacterAudio(
  character: string,
  voice: VoiceGender = 'rachel',
  speed: number = 1.0,
  onEnded?: () => void
): Promise<void> {
  try {
    const audio = getAudioElement(character, voice)
    audio.playbackRate = Math.max(0.5, Math.min(2.0, speed))
    audio.currentTime = 0

    if (onEnded) {
      audio.onended = onEnded
    }

    await audio.play()
  } catch (error) {
    console.error('Failed to play audio:', error)
    // Fall back to Web Speech API if bundled audio fails
    fallbackToSpeechSynthesis(character, speed)
  }
}

/**
 * Fallback to Web Speech API if bundled audio is unavailable
 */
function fallbackToSpeechSynthesis(character: string, speed: number): void {
  if (!('speechSynthesis' in window)) {
    console.warn('Speech synthesis not available')
    return
  }

  const charData = CHARACTER_DATA[character]
  let text = character

  if (charData?.type === 'uppercase') {
    text = `Capital ${character}`
  } else if (charData?.type === 'number') {
    text = character
  }

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = speed * 0.8 // Slightly slower for clarity
  speechSynthesis.speak(utterance)
}

/**
 * Preload audio files for faster playback
 */
export function preloadAudio(characters: string[], voice: VoiceGender = 'rachel'): void {
  for (const character of characters) {
    const audio = getAudioElement(character, voice)
    audio.load()
  }
}

/**
 * Stop any currently playing audio
 */
export function stopAudio(): void {
  for (const audio of audioCache.values()) {
    audio.pause()
    audio.currentTime = 0
  }
}

/**
 * Get character caption for accessibility
 */
export function getCharacterCaption(character: string): string {
  const charData = CHARACTER_DATA[character]
  if (!charData) {
    return character
  }

  switch (charData.type) {
    case 'uppercase':
      return `Capital ${character}`
    case 'lowercase':
      return `Lowercase ${character}`
    case 'number':
      return `Number ${character}`
    default:
      return character
  }
}

/**
 * Check if audio files are available
 */
export async function checkAudioAvailability(voice: VoiceGender = 'rachel'): Promise<boolean> {
  try {
    const response = await fetch(getAudioPath('A', voice), { method: 'HEAD' })
    return response.ok
  } catch {
    return false
  }
}
