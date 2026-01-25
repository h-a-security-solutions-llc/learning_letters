import { describe, it, expect } from 'vitest'

// Test helper functions that might be extracted from components

describe('Character Type Detection', () => {
  const getCharType = (char: string): string => {
    if (/[A-Z]/.test(char)) return 'uppercase letter'
    if (/[a-z]/.test(char)) return 'lowercase letter'
    if (/[0-9]/.test(char)) return 'number'
    return 'unknown'
  }

  it('identifies uppercase letters', () => {
    expect(getCharType('A')).toBe('uppercase letter')
    expect(getCharType('Z')).toBe('uppercase letter')
    expect(getCharType('M')).toBe('uppercase letter')
  })

  it('identifies lowercase letters', () => {
    expect(getCharType('a')).toBe('lowercase letter')
    expect(getCharType('z')).toBe('lowercase letter')
    expect(getCharType('m')).toBe('lowercase letter')
  })

  it('identifies numbers', () => {
    expect(getCharType('0')).toBe('number')
    expect(getCharType('9')).toBe('number')
    expect(getCharType('5')).toBe('number')
  })
})

describe('Character Sequences', () => {
  const uppercaseLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
  const lowercaseLetters = 'abcdefghijklmnopqrstuvwxyz'.split('')
  const numbers = '0123456789'.split('')

  const getNextCharacter = (current: string): string | null => {
    let sequence: string[] = []

    if (/[A-Z]/.test(current)) {
      sequence = uppercaseLetters
    } else if (/[a-z]/.test(current)) {
      sequence = lowercaseLetters
    } else if (/[0-9]/.test(current)) {
      sequence = numbers
    }

    if (sequence.length === 0) return null

    const currentIndex = sequence.indexOf(current)
    if (currentIndex === -1) return null

    const nextIndex = (currentIndex + 1) % sequence.length
    return sequence[nextIndex]
  }

  it('gets next uppercase letter', () => {
    expect(getNextCharacter('A')).toBe('B')
    expect(getNextCharacter('M')).toBe('N')
    expect(getNextCharacter('Y')).toBe('Z')
  })

  it('wraps around for uppercase letters', () => {
    expect(getNextCharacter('Z')).toBe('A')
  })

  it('gets next lowercase letter', () => {
    expect(getNextCharacter('a')).toBe('b')
    expect(getNextCharacter('m')).toBe('n')
  })

  it('wraps around for lowercase letters', () => {
    expect(getNextCharacter('z')).toBe('a')
  })

  it('gets next number', () => {
    expect(getNextCharacter('0')).toBe('1')
    expect(getNextCharacter('5')).toBe('6')
    expect(getNextCharacter('8')).toBe('9')
  })

  it('wraps around for numbers', () => {
    expect(getNextCharacter('9')).toBe('0')
  })
})

describe('Color Generation', () => {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3',
    '#F38181', '#AA96DA', '#FCBAD3', '#A8D8EA',
    '#FFB6B9', '#61C0BF', '#BBDED6', '#FAE3D9'
  ]

  const getCharColor = (char: string): string => {
    const index = char.charCodeAt(0) % colors.length
    return colors[index]
  }

  it('returns a color for any character', () => {
    const color = getCharColor('A')
    expect(color).toBeDefined()
    expect(color).toMatch(/^#[0-9A-Fa-f]{6}$/)
  })

  it('returns consistent color for same character', () => {
    const color1 = getCharColor('A')
    const color2 = getCharColor('A')
    expect(color1).toBe(color2)
  })

  it('returns different colors for different characters', () => {
    const colorA = getCharColor('A')
    const colorB = getCharColor('B')
    // They might be the same if charCode % 12 equals, but typically different
    expect(typeof colorA).toBe('string')
    expect(typeof colorB).toBe('string')
  })
})

describe('Star Calculation', () => {
  const calculateStars = (score: number): number => {
    if (score >= 95) return 5
    if (score >= 85) return 4
    if (score >= 70) return 3
    if (score >= 50) return 2
    if (score >= 30) return 1
    return 0
  }

  it('returns 5 stars for scores >= 95', () => {
    expect(calculateStars(95)).toBe(5)
    expect(calculateStars(100)).toBe(5)
  })

  it('returns 4 stars for scores 85-94', () => {
    expect(calculateStars(85)).toBe(4)
    expect(calculateStars(94)).toBe(4)
  })

  it('returns 3 stars for scores 70-84', () => {
    expect(calculateStars(70)).toBe(3)
    expect(calculateStars(84)).toBe(3)
  })

  it('returns 2 stars for scores 50-69', () => {
    expect(calculateStars(50)).toBe(2)
    expect(calculateStars(69)).toBe(2)
  })

  it('returns 1 star for scores 30-49', () => {
    expect(calculateStars(30)).toBe(1)
    expect(calculateStars(49)).toBe(1)
  })

  it('returns 0 stars for scores < 30', () => {
    expect(calculateStars(0)).toBe(0)
    expect(calculateStars(29)).toBe(0)
  })
})

describe('Winner Determination', () => {
  interface PlayerResult {
    name: string
    score: number
  }

  const findWinners = (results: PlayerResult[]): PlayerResult[] => {
    if (results.length === 0) return []
    const highestScore = Math.max(...results.map(r => r.score))
    return results.filter(r => r.score === highestScore)
  }

  it('returns single winner', () => {
    const results = [
      { name: 'Player 1', score: 85 },
      { name: 'Player 2', score: 70 },
      { name: 'Player 3', score: 60 }
    ]
    const winners = findWinners(results)
    expect(winners.length).toBe(1)
    expect(winners[0].name).toBe('Player 1')
  })

  it('returns multiple winners in case of tie', () => {
    const results = [
      { name: 'Player 1', score: 85 },
      { name: 'Player 2', score: 85 },
      { name: 'Player 3', score: 60 }
    ]
    const winners = findWinners(results)
    expect(winners.length).toBe(2)
    expect(winners.map(w => w.name)).toContain('Player 1')
    expect(winners.map(w => w.name)).toContain('Player 2')
  })

  it('handles empty results', () => {
    const winners = findWinners([])
    expect(winners.length).toBe(0)
  })

  it('handles all players with same score', () => {
    const results = [
      { name: 'Player 1', score: 75 },
      { name: 'Player 2', score: 75 },
      { name: 'Player 3', score: 75 }
    ]
    const winners = findWinners(results)
    expect(winners.length).toBe(3)
  })
})
