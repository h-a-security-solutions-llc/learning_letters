import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import ResultsDisplay from '@/components/ResultsDisplay.vue'
import type { ScoreResult, DrawingAttempt } from '@/types'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} })
  }
}))

// Mock Audio
const mockAudioPlay = vi.fn().mockResolvedValue(undefined)
global.Audio = vi.fn().mockImplementation(() => ({
  play: mockAudioPlay,
  onended: null,
  onerror: null
})) as unknown as typeof Audio

describe('ResultsDisplay', () => {
  const mockScoreData: ScoreResult = {
    score: 85,
    stars: 4,
    feedback: 'Great job!',
    reference_image: 'data:image/png;base64,reference',
    details: {
      coverage: 90,
      accuracy: 80,
      similarity: 85
    }
  }

  const mockUserDrawing = 'data:image/png;base64,userdrawing'

  let wrapper: VueWrapper

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(ResultsDisplay, {
      props: {
        character: 'A',
        scoreData: mockScoreData,
        userDrawing: mockUserDrawing,
        attempts: [],
        bestOf3Mode: false,
        showDebugMode: false,
        voiceGender: 'rachel',
        autoPlaySound: false
      }
    })
  })

  it('renders correctly', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.results-container').exists()).toBe(true)
  })

  it('displays the score', () => {
    expect(wrapper.find('.score-number').text()).toBe('85%')
  })

  it('displays the feedback message', () => {
    expect(wrapper.find('.feedback').text()).toBe('Great job!')
  })

  it('displays correct number of filled stars', () => {
    const filledStars = wrapper.findAll('.star.filled')
    expect(filledStars.length).toBe(4)
  })

  it('displays user drawing', () => {
    const userImg = wrapper.findAll('.image-container img')[0]
    expect(userImg.attributes('src')).toBe(mockUserDrawing)
  })

  it('displays reference image', () => {
    const refImg = wrapper.findAll('.image-container img')[1]
    expect(refImg.attributes('src')).toBe('data:image/png;base64,reference')
  })

  it('displays the character', () => {
    expect(wrapper.find('.character-large').text()).toBe('A')
  })

  it('emits try-again event when button is clicked', async () => {
    await wrapper.find('.try-again-btn').trigger('click')
    expect(wrapper.emitted('try-again')).toBeTruthy()
  })

  it('emits next event when next button is clicked', async () => {
    await wrapper.find('.next-btn').trigger('click')
    expect(wrapper.emitted('next')).toBeTruthy()
  })

  it('shows speak button', () => {
    const speakBtn = wrapper.find('.speak-btn')
    expect(speakBtn.exists()).toBe(true)
    expect(speakBtn.text()).toContain('Hear it!')
  })

  it('does not show attempts section when not in best of 3 mode', () => {
    expect(wrapper.find('.attempts-section').exists()).toBe(false)
  })

  it('shows attempts section in best of 3 mode with attempts', async () => {
    const attempts: DrawingAttempt[] = [
      { imageData: 'data:image/png;base64,1', scoreResult: { ...mockScoreData, score: 70 } },
      { imageData: 'data:image/png;base64,2', scoreResult: { ...mockScoreData, score: 85 } },
      { imageData: 'data:image/png;base64,3', scoreResult: { ...mockScoreData, score: 75 } }
    ]

    await wrapper.setProps({
      bestOf3Mode: true,
      attempts
    })

    expect(wrapper.find('.attempts-section').exists()).toBe(true)
    expect(wrapper.findAll('.attempt-card').length).toBe(3)
  })

  it('marks best attempt in best of 3 mode', async () => {
    const attempts: DrawingAttempt[] = [
      { imageData: 'data:image/png;base64,1', scoreResult: { ...mockScoreData, score: 70 } },
      { imageData: 'data:image/png;base64,2', scoreResult: { ...mockScoreData, score: 85 } },
      { imageData: 'data:image/png;base64,3', scoreResult: { ...mockScoreData, score: 75 } }
    ]

    await wrapper.setProps({
      bestOf3Mode: true,
      attempts
    })

    const bestCard = wrapper.find('.attempt-card.best')
    expect(bestCard.exists()).toBe(true)
    expect(bestCard.find('.best-badge').text()).toBe('BEST')
  })

  it('does not show debug section when showDebugMode is false', () => {
    expect(wrapper.find('.debug-section').exists()).toBe(false)
  })

  it('shows debug section when showDebugMode is true and debug data exists', async () => {
    await wrapper.setProps({
      showDebugMode: true,
      scoreData: {
        ...mockScoreData,
        debug: {
          drawn_centered: 'data:image/png;base64,centered',
          drawn_unsanded: 'data:image/png;base64,unsanded',
          drawn_sanded: 'data:image/png;base64,sanded',
          reference_normalized: 'data:image/png;base64,ref'
        }
      }
    })

    expect(wrapper.find('.debug-section').exists()).toBe(true)
  })

  it('auto-plays audio when autoPlaySound is true', async () => {
    const wrapper = mount(ResultsDisplay, {
      props: {
        character: 'B',
        scoreData: mockScoreData,
        userDrawing: mockUserDrawing,
        attempts: [],
        bestOf3Mode: false,
        showDebugMode: false,
        voiceGender: 'rachel',
        autoPlaySound: true
      }
    })

    // The auto-play happens in onMounted with a setTimeout delay
    // Wait for the setTimeout to execute
    await new Promise(resolve => setTimeout(resolve, 600))

    // Component should emit play-audio event for auto-play
    expect(wrapper.emitted('play-audio')).toBeTruthy()
    expect(wrapper.emitted('play-audio')![0]).toEqual(['B'])
  })
})
