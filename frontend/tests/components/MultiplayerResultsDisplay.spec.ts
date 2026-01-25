import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import MultiplayerResultsDisplay from '@/components/MultiplayerResultsDisplay.vue'
import type { PlayerResult } from '@/types'

// Mock Audio
global.Audio = vi.fn().mockImplementation(() => ({
  play: vi.fn().mockResolvedValue(undefined),
  onended: null,
  onerror: null
})) as unknown as typeof Audio

describe('MultiplayerResultsDisplay', () => {
  const mockPlayerResults: PlayerResult[] = [
    {
      name: 'Player 1',
      imageData: 'data:image/png;base64,p1',
      scoreResult: {
        score: 85,
        stars: 4,
        feedback: 'Great!',
        reference_image: 'ref',
        details: { coverage: 90, accuracy: 80, similarity: 85 }
      }
    },
    {
      name: 'Player 2',
      imageData: 'data:image/png;base64,p2',
      scoreResult: {
        score: 70,
        stars: 3,
        feedback: 'Good!',
        reference_image: 'ref',
        details: { coverage: 75, accuracy: 70, similarity: 65 }
      }
    },
    {
      name: 'Player 3',
      imageData: 'data:image/png;base64,p3',
      scoreResult: {
        score: 60,
        stars: 2,
        feedback: 'Nice try!',
        reference_image: 'ref',
        details: { coverage: 65, accuracy: 60, similarity: 55 }
      }
    }
  ]

  let wrapper: VueWrapper

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = mount(MultiplayerResultsDisplay, {
      props: {
        playerResults: mockPlayerResults,
        character: 'A',
        voiceGender: 'rachel'
      }
    })
  })

  it('renders correctly', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.multiplayer-results-container').exists()).toBe(true)
  })

  it('displays winner banner', () => {
    expect(wrapper.find('.winner-banner').exists()).toBe(true)
    expect(wrapper.find('.winner-text').text()).toContain('Player 1')
    expect(wrapper.find('.winner-text').text()).toContain('Wins!')
  })

  it('displays all player result cards', () => {
    const cards = wrapper.findAll('.player-result-card')
    expect(cards.length).toBe(3)
  })

  it('sorts players by score (highest first)', () => {
    const cards = wrapper.findAll('.player-result-card')
    const names = cards.map(c => c.find('.player-name').text())
    expect(names[0]).toBe('Player 1')
    expect(names[1]).toBe('Player 2')
    expect(names[2]).toBe('Player 3')
  })

  it('marks winner card with winner class', () => {
    const winnerCard = wrapper.find('.player-result-card.winner')
    expect(winnerCard.exists()).toBe(true)
    expect(winnerCard.find('.player-name').text()).toBe('Player 1')
  })

  it('displays rank badges', () => {
    const badges = wrapper.findAll('.rank-badge')
    expect(badges.length).toBe(3)
    expect(badges[0].classes()).toContain('gold')
    expect(badges[1].classes()).toContain('silver')
    expect(badges[2].classes()).toContain('bronze')
  })

  it('displays scores for each player', () => {
    const scores = wrapper.findAll('.score')
    expect(scores[0].text()).toBe('85%')
    expect(scores[1].text()).toBe('70%')
    expect(scores[2].text()).toBe('60%')
  })

  it('displays correct stars for each player', () => {
    const cards = wrapper.findAll('.player-result-card')
    const firstCardStars = cards[0].findAll('.star.filled')
    expect(firstCardStars.length).toBe(4)
  })

  it('displays the character', () => {
    expect(wrapper.find('.character-display').text()).toBe('A')
  })

  it('emits play-again event when button is clicked', async () => {
    await wrapper.find('.play-again-btn').trigger('click')
    expect(wrapper.emitted('play-again')).toBeTruthy()
  })

  it('emits next-letter event when button is clicked', async () => {
    await wrapper.find('.next-letter-btn').trigger('click')
    expect(wrapper.emitted('next-letter')).toBeTruthy()
  })

  it('shows "It\'s a Tie!" for tied scores', async () => {
    const tiedResults: PlayerResult[] = [
      { ...mockPlayerResults[0], scoreResult: { ...mockPlayerResults[0].scoreResult, score: 80 } },
      { ...mockPlayerResults[1], scoreResult: { ...mockPlayerResults[1].scoreResult, score: 80 } }
    ]

    await wrapper.setProps({ playerResults: tiedResults })

    expect(wrapper.find('.winner-text').text()).toContain("It's a Tie!")
  })

  it('shows tie names when multiple winners', async () => {
    const tiedResults: PlayerResult[] = [
      { ...mockPlayerResults[0], scoreResult: { ...mockPlayerResults[0].scoreResult, score: 80 } },
      { ...mockPlayerResults[1], scoreResult: { ...mockPlayerResults[1].scoreResult, score: 80 } }
    ]

    await wrapper.setProps({ playerResults: tiedResults })

    const tieNames = wrapper.find('.tie-names')
    expect(tieNames.exists()).toBe(true)
    expect(tieNames.text()).toContain('Player 1')
    expect(tieNames.text()).toContain('Player 2')
  })

  it('displays drawing thumbnails', () => {
    const thumbnails = wrapper.findAll('.drawing-thumbnail img')
    expect(thumbnails.length).toBe(3)
    expect(thumbnails[0].attributes('src')).toBe('data:image/png;base64,p1')
  })

  it('shows speak button', () => {
    const speakBtn = wrapper.find('.speak-btn')
    expect(speakBtn.exists()).toBe(true)
  })
})
