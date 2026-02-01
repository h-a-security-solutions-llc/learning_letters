/**
 * Test setup file for Vitest
 * Configures global mocks and test utilities
 */

import { vi } from 'vitest'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    get length() {
      return Object.keys(store).length
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null)
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock Audio API
class MockAudio {
  src = ''
  playbackRate = 1
  currentTime = 0
  onended: (() => void) | null = null

  play = vi.fn(() => Promise.resolve())
  pause = vi.fn()
  load = vi.fn()
}

window.Audio = MockAudio as unknown as typeof Audio

// Mock fetch
global.fetch = vi.fn()

// Mock speechSynthesis
Object.defineProperty(window, 'speechSynthesis', {
  value: {
    speak: vi.fn(),
    cancel: vi.fn(),
    getVoices: vi.fn(() => [])
  }
})

// Mock SpeechSynthesisUtterance
window.SpeechSynthesisUtterance = vi.fn().mockImplementation(() => ({
  text: '',
  rate: 1,
  pitch: 1,
  volume: 1,
  voice: null
})) as unknown as typeof SpeechSynthesisUtterance

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
  localStorageMock.clear()
})
