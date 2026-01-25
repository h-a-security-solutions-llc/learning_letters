// Application settings
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
  // Accessibility settings
  uiScale: number              // 100 | 125 | 150
  reducedMotion: boolean | null // null = follow system preference
  audioSpeed: number           // 1.0 | 0.75 | 0.5
  strokeTolerance: number      // 0.5 | 0.75 | 1.0 (multiplier for zone radius)
  colorBlindMode: boolean
  enableCaptions: boolean
}

// Player for multiplayer mode
export interface Player {
  name: string
  traceModeAllowed: boolean
  stepByStepAllowed: boolean
}

// Score result from API
export interface ScoreResult {
  score: number
  stars: number
  feedback: string
  reference_image: string
  details: {
    coverage: number
    accuracy: number
    similarity: number
  }
  debug?: {
    drawn_centered: string
    drawn_unsanded: string
    drawn_sanded: string
    reference_normalized: string
  }
  is_new_high_score?: boolean
  previous_high_score?: number
  high_score_for_mode?: number
}

// Drawing mode for progress tracking
export type DrawingMode = 'freestyle' | 'tracing' | 'step-by-step'

// Player result for multiplayer
export interface PlayerResult {
  name: string
  imageData: string
  scoreResult: ScoreResult
}

// Drawing attempt (for best of 3 mode)
export interface DrawingAttempt {
  imageData: string
  scoreResult: ScoreResult
}

// Guide data from API
export interface GuideData {
  trace_image: string
  animated_strokes?: AnimatedStroke[]
  stroke_count: number
}

// Animated stroke for step-by-step mode
export interface AnimatedStroke {
  points: [number, number][]
  color: string
  order: number
  start_zone: {
    x: number
    y: number
    radius: number
  }
  end_zone: {
    x: number
    y: number
    radius: number
  }
}

// Guided strokes data from API
export interface GuidedStrokesData {
  strokes: AnimatedStroke[]
  total_strokes: number
}

// Stroke validation result
export interface StrokeValidationResult {
  valid: boolean
  feedback: string
}

// Font metadata
export interface FontMetadata {
  name: string
  display_name: string
  style: string
  description: string
  characteristics: string[]
}

// View types
export type AppView = 'selection' | 'drawing' | 'results' | 'multiplayer-results'

// Character category
export type CharacterCategory = 'uppercase' | 'lowercase' | 'numbers'

// Authentication types
export interface User {
  id: string
  email: string
  display_name: string
  created_at: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  display_name: string
}

// Synced settings (with version for conflict resolution)
export interface SyncedSettings extends AppSettings {
  version?: number
}

// User progress for high scores
export interface UserProgress {
  id: string
  character: string
  font_name: string
  mode: DrawingMode
  high_score: number
  stars: number
  attempts_count: number
  best_attempt_at: string
}
