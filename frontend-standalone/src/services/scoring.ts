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
 * @returns ScoringResult with score, stars, and detailed metrics
 */
export async function scoreDrawing(
  canvas: HTMLCanvasElement,
  character: string,
  fontName: string = 'Fredoka-Regular'
): Promise<ScoringResult> {
  await initScoring()

  const pngBytes = await canvasToPngBytes(canvas)
  const fontData = await loadFont(fontName)

  const result = score_drawing(pngBytes, character, fontData)

  // Convert reference image bytes to data URL
  const refBytes = result.reference_image
  const refBlob = new Blob([refBytes], { type: 'image/png' })
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
  const pngBytes = generate_reference_image(character, fontData, size)

  const blob = new Blob([pngBytes], { type: 'image/png' })
  return URL.createObjectURL(blob)
}

/**
 * Preload fonts for faster scoring
 */
export async function preloadFonts(fontNames: string[]): Promise<void> {
  await Promise.all(fontNames.map(name => loadFont(name)))
}
