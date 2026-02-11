/**
 * Stroke Extraction Service
 *
 * Provides dynamic stroke extraction from fonts using the WASM module.
 * Falls back to static JSON files when available.
 */

// @ts-ignore - WASM module types
import init, { extract_strokes } from '../wasm-pkg/learning_letters_scoring.js'
import { initScoring } from './scoring'

export interface StrokeZone {
  cx: number
  cy: number
  r: number
}

export interface Stroke {
  points: Array<[number, number]>
  start_zone: StrokeZone
  end_zone: StrokeZone
  direction: string
}

export interface StrokeData {
  character: string
  font: string
  char_type: string
  strokes: Stroke[]
}

// Legacy format used by DrawingCanvas
export interface LegacyStroke {
  points: Array<[number, number]>
  direction: string
}

export interface LegacyCharacterData {
  type: string
  phonetic?: string
  sound?: string
  strokes: LegacyStroke[]
}

// Cache for extracted strokes
const strokeCache = new Map<string, StrokeData>()

// Cache for loaded font data
const fontCache = new Map<string, Uint8Array>()

/**
 * Load a font file
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
 * Get cache key for stroke data
 */
function getCacheKey(character: string, fontName: string): string {
  return `${fontName}:${character}`
}

/**
 * Map font selection names to static stroke JSON file names
 */
function getStaticStrokeFileName(fontName: string): string | null {
  const strokeFileMap: Record<string, string> = {
    'Fredoka-Regular': 'fredoka',
    'Nunito-Regular': 'nunito',
    'PatrickHand-Regular': 'patrick-hand',
    'PlaywriteUS-Regular': 'playwrite-us',
    'Schoolbell-Regular': 'schoolbell'
  }
  return strokeFileMap[fontName] || null
}

/**
 * Try to load strokes from static JSON file
 */
async function loadStaticStrokes(
  character: string,
  fontName: string
): Promise<LegacyCharacterData | null> {
  const fileName = getStaticStrokeFileName(fontName)
  if (!fileName) {
    return null
  }

  try {
    const response = await fetch(`/strokes/${fileName}.json`)
    if (!response.ok) {
      return null
    }
    const data = await response.json()
    return data.characters?.[character] || null
  } catch {
    return null
  }
}

/**
 * Convert WASM StrokeData to legacy format used by DrawingCanvas
 */
function convertToLegacyFormat(strokeData: StrokeData): LegacyCharacterData {
  return {
    type: strokeData.char_type,
    strokes: strokeData.strokes.map(stroke => ({
      points: stroke.points.map(p => [p[0], p[1]] as [number, number]),
      direction: stroke.direction
    }))
  }
}

/**
 * Convert legacy format to new StrokeData format
 */
function convertFromLegacyFormat(
  legacy: LegacyCharacterData,
  character: string,
  fontName: string
): StrokeData {
  return {
    character,
    font: fontName,
    char_type: legacy.type,
    strokes: legacy.strokes.map(stroke => ({
      points: stroke.points.map(p => [p[0], p[1]] as [number, number]),
      start_zone: {
        cx: stroke.points[0][0],
        cy: stroke.points[0][1],
        r: 10
      },
      end_zone: {
        cx: stroke.points[stroke.points.length - 1][0],
        cy: stroke.points[stroke.points.length - 1][1],
        r: 10
      },
      direction: stroke.direction
    }))
  }
}

/**
 * Extract strokes from a font using WASM
 */
async function extractStrokesFromFont(
  character: string,
  fontName: string
): Promise<StrokeData> {
  // Initialize WASM module
  await initScoring()

  // Load font data
  const fontData = await loadFont(fontName)

  // Extract strokes using WASM (use 200 for good detail)
  const result = extract_strokes(fontData, character, 200) as StrokeData

  return result
}

/**
 * Get stroke data for a character
 *
 * Strategy:
 * 1. Check cache
 * 2. Try static JSON files (pre-generated, hand-tuned) - unless forceDynamic is true
 * 3. Fall back to dynamic WASM extraction
 *
 * @param character - The character to get strokes for
 * @param fontName - The font name (e.g., 'Fredoka-Regular')
 * @param forceDynamic - If true, skip static JSON and use WASM extraction
 * @returns StrokeData with strokes array
 */
export async function getStrokes(
  character: string,
  fontName: string,
  forceDynamic: boolean = false
): Promise<StrokeData> {
  const cacheKey = forceDynamic ? `dynamic:${fontName}:${character}` : getCacheKey(character, fontName)

  // Check cache first
  if (strokeCache.has(cacheKey)) {
    return strokeCache.get(cacheKey)!
  }

  // Try static JSON first (pre-generated, potentially hand-tuned) - unless forceDynamic
  if (!forceDynamic) {
    const staticData = await loadStaticStrokes(character, fontName)
    if (staticData) {
      const strokeData = convertFromLegacyFormat(staticData, character, fontName)
      strokeCache.set(cacheKey, strokeData)
      return strokeData
    }
  }

  // Use dynamic extraction
  try {
    const strokeData = await extractStrokesFromFont(character, fontName)
    strokeCache.set(cacheKey, strokeData)
    return strokeData
  } catch (error) {
    console.error(`Failed to extract strokes for '${character}' in ${fontName}:`, error)
    // Return empty stroke data as fallback
    return {
      character,
      font: fontName,
      char_type: 'unknown',
      strokes: []
    }
  }
}

/**
 * Get stroke data in legacy format (for DrawingCanvas compatibility)
 *
 * @param character - The character to get strokes for
 * @param fontName - The font name (e.g., 'Fredoka-Regular')
 * @param forceDynamic - If true, skip static JSON and use WASM extraction
 * @returns Legacy stroke format with strokes array
 */
export async function getStrokesLegacy(
  character: string,
  fontName: string,
  forceDynamic: boolean = false
): Promise<LegacyCharacterData | null> {
  try {
    const strokeData = await getStrokes(character, fontName, forceDynamic)
    if (strokeData.strokes.length === 0) {
      return null
    }
    return convertToLegacyFormat(strokeData)
  } catch {
    return null
  }
}

/**
 * Get strokes using dynamic WASM extraction only (for testing/debugging)
 * This bypasses all static JSON files and caching.
 *
 * @param character - The character to get strokes for
 * @param fontName - The font name (e.g., 'Fredoka-Regular')
 * @returns StrokeData with strokes array
 */
export async function getDynamicStrokes(
  character: string,
  fontName: string
): Promise<StrokeData> {
  return extractStrokesFromFont(character, fontName)
}

/**
 * Preload strokes for multiple characters
 */
export async function preloadStrokes(
  characters: string[],
  fontName: string
): Promise<void> {
  await Promise.all(
    characters.map(char => getStrokes(char, fontName))
  )
}

/**
 * Clear the stroke cache
 */
export function clearStrokeCache(): void {
  strokeCache.clear()
}

/**
 * Check if dynamic stroke extraction is available
 */
export async function isDynamicExtractionAvailable(): Promise<boolean> {
  try {
    await initScoring()
    return typeof extract_strokes === 'function'
  } catch {
    return false
  }
}
