/**
 * Scoring Service - WASM wrapper for character scoring
 *
 * This service provides the interface to the Rust WASM scoring engine,
 * handling font loading, image processing, and score calculation.
 */

// @ts-ignore - WASM module types
import init, { score_drawing, generate_reference_image } from '../wasm-pkg/learning_letters_scoring.js'

let wasmInitialized = false
const fontCache = new Map<string, Uint8Array>()

export interface ScoringResult {
  score: number
  stars: number
  feedback: string
  coverage: number
  accuracy: number
  similarity: number
  referenceImage: string
}

/**
 * Initialize the WASM module
 */
export async function initScoring(): Promise<void> {
  if (!wasmInitialized) {
    await init()
    wasmInitialized = true
  }
}

/**
 * Load a font file and cache it
 */
async function loadFont(fontName: string): Promise<Uint8Array> {
  if (fontCache.has(fontName)) {
    return fontCache.get(fontName)!
  }

  const response = await fetch(`/fonts/${fontName}.ttf`)
  if (!response.ok) {
    throw new Error(`Failed to load font: ${fontName}`)
  }

  const buffer = await response.arrayBuffer()
  const bytes = new Uint8Array(buffer)
  fontCache.set(fontName, bytes)
  return bytes
}

/**
 * Convert canvas to PNG bytes
 */
async function canvasToPngBytes(canvas: HTMLCanvasElement): Promise<Uint8Array> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(async (blob) => {
      if (!blob) {
        reject(new Error('Failed to convert canvas to blob'))
        return
      }
      const buffer = await blob.arrayBuffer()
      resolve(new Uint8Array(buffer))
    }, 'image/png')
  })
}

/**
 * Score a user's drawing
 *
 * @param canvas - The canvas element with the user's drawing
 * @param character - The character that was drawn
 * @param fontName - The font to use for reference (default: Fredoka-Regular)
 * @param debugMode - Whether to auto-save debug images (default: false)
 * @returns ScoringResult with score, stars, and detailed metrics
 */
export async function scoreDrawing(
  canvas: HTMLCanvasElement,
  character: string,
  fontName: string = 'Fredoka-Regular',
  debugMode: boolean = false
): Promise<ScoringResult> {
  // Store debug info on window object for inspection
  const debugLog: string[] = []
  const log = (msg: string) => {
    debugLog.push(msg)
    // Try multiple console methods
    console.warn(msg)
    console.log(msg)
    console.info(msg)
  }

  log('========== SCORING DEBUG START ==========')
  log(`[Scoring] Character: ${character}, Font: ${fontName}`)
  log(`[Scoring] Canvas: ${canvas.width}x${canvas.height}`)

  try {
    await initScoring()
    log('[Scoring] WASM initialized')

    const pngBytes = await canvasToPngBytes(canvas)
    log(`[Scoring] PNG bytes: ${pngBytes.length}`)

    const fontData = await loadFont(fontName)
    log(`[Scoring] Font loaded: ${fontData.length} bytes`)

    const result = score_drawing(pngBytes, character, fontData)

    log('=== RESULTS ===')
    log(`Coverage: ${result.coverage}%`)
    log(`Accuracy: ${result.accuracy}%`)
    log(`Similarity: ${result.similarity}%`)
    log(`Final: ${result.score}% (${result.stars} stars)`)

    // Get debug images from WASM
    const debugUserBytes = result.debug_user_processed as Uint8Array
    const debugRefBytes = result.debug_reference_processed as Uint8Array

    // Create blob URLs for debug images
    const debugUserBlob = new Blob([new Uint8Array(debugUserBytes)], { type: 'image/png' })
    const debugRefBlob = new Blob([new Uint8Array(debugRefBytes)], { type: 'image/png' })
    const debugUserUrl = URL.createObjectURL(debugUserBlob)
    const debugRefUrl = URL.createObjectURL(debugRefBlob)

    log(`Debug images created: user=${debugUserBytes.length} bytes, ref=${debugRefBytes.length} bytes`)

    // Store on window for debugging
    ;(window as any).__SCORING_DEBUG__ = {
      timestamp: new Date().toISOString(),
      character,
      fontName,
      canvasSize: `${canvas.width}x${canvas.height}`,
      pngBytes: pngBytes.length,
      result: {
        score: result.score,
        stars: result.stars,
        coverage: result.coverage,
        accuracy: result.accuracy,
        similarity: result.similarity,
        feedback: result.feedback
      },
      logs: debugLog,
      debugImages: {
        userProcessed: debugUserUrl,
        referenceProcessed: debugRefUrl
      },
      // Function to download debug images
      saveDebugImages: () => {
        const a1 = document.createElement('a')
        a1.href = debugUserUrl
        a1.download = `debug_user_${character}_${Date.now()}.png`
        a1.click()

        const a2 = document.createElement('a')
        a2.href = debugRefUrl
        a2.download = `debug_ref_${character}_${Date.now()}.png`
        a2.click()

        // Also save original canvas
        const a3 = document.createElement('a')
        a3.href = canvas.toDataURL('image/png')
        a3.download = `debug_original_${character}_${Date.now()}.png`
        a3.click()
      }
    }
    log('Debug info stored in window.__SCORING_DEBUG__')

    // Auto-save debug images if debug mode is enabled
    if (debugMode) {
      log('Debug mode enabled - auto-saving debug images...')
      ;(window as any).__SCORING_DEBUG__.saveDebugImages()
    }

    // Convert reference image bytes to data URL
    const refBytes = result.reference_image as Uint8Array
    const refBlob = new Blob([new Uint8Array(refBytes)], { type: 'image/png' })
    const referenceImage = URL.createObjectURL(refBlob)

    return {
      score: result.score,
      stars: result.stars,
      feedback: result.feedback,
      coverage: result.coverage,
      accuracy: result.accuracy,
      similarity: result.similarity,
      referenceImage
    }
  } catch (error) {
    console.error('[Scoring] Error during scoring:', error)
    throw error
  }
}

/**
 * Generate a reference image for a character
 *
 * @param character - The character to render
 * @param fontName - The font to use
 * @param size - Output image size
 * @returns Data URL of the reference image
 */
export async function getReferenceImage(
  character: string,
  fontName: string = 'Fredoka-Regular',
  size: number = 200
): Promise<string> {
  await initScoring()

  const fontData = await loadFont(fontName)
  const pngBytes = generate_reference_image(character, fontData, size) as Uint8Array

  const blob = new Blob([new Uint8Array(pngBytes)], { type: 'image/png' })
  return URL.createObjectURL(blob)
}

/**
 * Preload fonts for faster scoring
 */
export async function preloadFonts(fontNames: string[]): Promise<void> {
  await Promise.all(fontNames.map(name => loadFont(name)))
}
