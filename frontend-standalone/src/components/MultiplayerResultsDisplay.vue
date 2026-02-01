<template>
  <div class="multiplayer-results-container">
    <!-- Winner Banner -->
    <div class="winner-banner">
      <div class="trophy-icon">🏆</div>
      <div class="winner-text">
        <template v-if="winners.length === 1">
          {{ winners[0].name }} Wins!
        </template>
        <template v-else>
          It's a Tie!
        </template>
      </div>
      <div v-if="winners.length > 1" class="tie-names">
        {{ winners.map(w => w.name).join(' & ') }}
      </div>
    </div>

    <!-- Player Results Grid -->
    <div class="results-grid">
      <div
        v-for="(result, index) in sortedResults"
        :key="index"
        class="player-result-card"
        :class="{ winner: isWinner(result) }"
      >
        <div class="rank-badge" :class="getRankClass(index)">
          <template v-if="index === 0">🥇</template>
          <template v-else-if="index === 1">🥈</template>
          <template v-else-if="index === 2">🥉</template>
          <template v-else>{{ index + 1 }}</template>
        </div>

        <div class="player-name">{{ result.name }}</div>

        <div class="drawing-thumbnail">
          <img :src="result.imageData" :alt="`${result.name}'s drawing`">
        </div>

        <div class="stars">
          <span
            v-for="i in 5"
            :key="i"
            class="star"
            :class="{ filled: i <= result.scoreResult.stars }"
          >★</span>
        </div>

        <div class="score">{{ result.scoreResult.score }}%</div>
      </div>
    </div>

    <!-- Character Section -->
    <div class="character-section">
      <span class="character-display">{{ character }}</span>
      <button class="speak-btn" :aria-label="`Play pronunciation of ${character}`" @click="speakCharacter">
        <span class="speaker-icon" aria-hidden="true">🔊</span>
      </button>
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons">
      <button class="action-btn play-again-btn" aria-label="Play again with same character" @click="$emit('play-again')">
        <span class="btn-icon" aria-hidden="true">🔄</span>
        <span>Play Again</span>
      </button>

      <button class="action-btn next-letter-btn" :aria-label="`Go to next ${charType.toLowerCase()}`" @click="$emit('next-letter')">
        <span class="btn-icon" aria-hidden="true">➡️</span>
        <span>Next {{ charType }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'MultiplayerResultsDisplay',
  props: {
    playerResults: {
      type: Array,
      required: true
    },
    character: {
      type: String,
      required: true
    }
  },
  emits: ['play-again', 'next-letter', 'play-audio'],
  setup(props, { emit }) {
    const charType = computed(() => {
      if (/[0-9]/.test(props.character)) return 'Number'
      return 'Letter'
    })

    const sortedResults = computed(() => {
      return [...props.playerResults].sort(
        (a, b) => b.scoreResult.score - a.scoreResult.score
      )
    })

    const highestScore = computed(() => {
      if (props.playerResults.length === 0) return 0
      return Math.max(...props.playerResults.map(r => r.scoreResult.score))
    })

    const winners = computed(() => {
      return sortedResults.value.filter(
        r => r.scoreResult.score === highestScore.value
      )
    })

    const isWinner = (result) => {
      return result.scoreResult.score === highestScore.value
    }

    const getRankClass = (index) => {
      if (index === 0) return 'gold'
      if (index === 1) return 'silver'
      if (index === 2) return 'bronze'
      return ''
    }

    const speakCharacter = () => {
      emit('play-audio', props.character)
    }

    return {
      charType,
      sortedResults,
      winners,
      isWinner,
      getRankClass,
      speakCharacter
    }
  }
}
</script>

<style scoped>
.multiplayer-results-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 20px;
  overflow-y: auto;
}

.winner-banner {
  text-align: center;
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
  animation: celebratePulse 1s ease-in-out infinite alternate;
}

@keyframes celebratePulse {
  from { transform: scale(1); }
  to { transform: scale(1.02); }
}

.trophy-icon {
  font-size: 3rem;
  margin-bottom: 5px;
  animation: trophyBounce 0.6s ease-in-out infinite alternate;
}

@keyframes trophyBounce {
  from { transform: translateY(0) rotate(-5deg); }
  to { transform: translateY(-10px) rotate(5deg); }
}

.winner-text {
  font-size: 1.8rem;
  font-weight: 700;
  color: #333;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
}

.tie-names {
  font-size: 1.1rem;
  color: #555;
  margin-top: 5px;
  font-weight: 600;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 15px;
  justify-items: center;
}

.player-result-card {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 15px;
  padding: 15px;
  text-align: center;
  width: 100%;
  max-width: 160px;
  transition: all 0.3s ease;
  position: relative;
}

.player-result-card.winner {
  background: rgba(255, 215, 0, 0.2);
  border: 2px solid #FFD700;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
}

.rank-badge {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
}

.rank-badge.gold {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
}

.rank-badge.silver {
  background: linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%);
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%);
  color: white;
}

.rank-badge:not(.gold):not(.silver):not(.bronze) {
  background: rgba(255, 255, 255, 0.9);
  color: #666;
  font-size: 0.9rem;
}

.player-name {
  color: white;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 10px;
  margin-top: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawing-thumbnail {
  background: white;
  border-radius: 10px;
  padding: 5px;
  margin-bottom: 10px;
}

.drawing-thumbnail img {
  width: 80px;
  height: 80px;
  object-fit: contain;
}

.stars {
  margin-bottom: 5px;
}

.star {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.3);
  margin: 0 1px;
}

.star.filled {
  color: #FFE66D;
  text-shadow: 0 0 10px #FFE66D;
}

.score {
  font-size: 1.3rem;
  font-weight: 700;
  color: #4ECDC4;
}

.character-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 15px;
}

.character-display {
  font-size: 3.5rem;
  font-weight: 700;
  color: white;
  text-shadow: 3px 3px 0 rgba(0, 0, 0, 0.2);
}

.speak-btn {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: white;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: none;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
  transition: transform 0.2s;
}

.speak-btn:hover {
  transform: scale(1.1);
}

.speaker-icon {
  font-size: 1.5rem;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-top: auto;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 35px;
  border-radius: 30px;
  font-size: 1.2rem;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}

.action-btn:hover {
  transform: scale(1.05);
}

.btn-icon {
  font-size: 1.4rem;
}

.play-again-btn {
  background: white;
  color: #764ba2;
}

.next-letter-btn {
  background: linear-gradient(135deg, #4ECDC4 0%, #44B09E 100%);
  color: white;
}

@media (max-width: 600px) {
  .multiplayer-results-container {
    padding: 15px;
    gap: 15px;
  }

  .winner-banner {
    padding: 15px;
  }

  .trophy-icon {
    font-size: 2.5rem;
  }

  .winner-text {
    font-size: 1.4rem;
  }

  .results-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .player-result-card {
    max-width: none;
  }

  .drawing-thumbnail img {
    width: 60px;
    height: 60px;
  }

  .action-btn {
    padding: 15px 25px;
    font-size: 1rem;
  }
}
</style>
