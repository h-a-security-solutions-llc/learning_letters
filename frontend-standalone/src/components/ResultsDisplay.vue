<template>
  <div class="results-container">
    <!-- Score Display -->
    <div class="score-section">
      <div class="stars">
        <span
          v-for="i in 5"
          :key="i"
          class="star"
          :class="{ filled: i <= scoreData.stars }"
        >
          ★
        </span>
      </div>
      <div class="score-number">
        {{ scoreData.score }}%
      </div>
      <div class="feedback">
        {{ scoreData.feedback }}
      </div>
    </div>

    <!-- Comparison Display -->
    <div class="comparison-section">
      <div class="comparison-item">
        <h3>Your Drawing</h3>
        <div class="image-container">
          <img :src="userDrawing" alt="Your drawing">
        </div>
      </div>

      <div class="vs-divider">
        <span>VS</span>
      </div>

      <div class="comparison-item">
        <h3>Perfect Example</h3>
        <div class="image-container">
          <img :src="scoreData.reference_image" alt="Perfect example">
        </div>
      </div>
    </div>

    <!-- Best of 3 Attempts Display -->
    <div v-if="bestOf3Mode && attempts.length > 0" class="attempts-section">
      <h3>Your 3 Attempts</h3>
      <div class="attempts-grid">
        <div
          v-for="(attempt, index) in attempts"
          :key="index"
          class="attempt-card"
          :class="{ best: attempt.scoreResult.score === scoreData.score }"
        >
          <div class="attempt-label">
            <span>#{{ index + 1 }}</span>
            <span v-if="attempt.scoreResult.score === scoreData.score" class="best-badge">BEST</span>
          </div>
          <img :src="attempt.imageData" alt="Attempt drawing">
          <div class="attempt-score">
            {{ attempt.scoreResult.score }}%
          </div>
        </div>
      </div>
    </div>

    <!-- Debug Section -->
    <div v-if="scoreData.debug && showDebugMode" class="debug-section">
      <h3>Score Details</h3>
      <div class="debug-details">
        <div class="detail-item">
          <span class="detail-label">Coverage</span>
          <span class="detail-value">{{ scoreData.details?.coverage || 0 }}%</span>
          <small>How much of the letter you traced</small>
        </div>
        <div class="detail-item">
          <span class="detail-label">Accuracy</span>
          <span class="detail-value">{{ scoreData.details?.accuracy || 0 }}%</span>
          <small>How well you stayed on the lines</small>
        </div>
        <div class="detail-item">
          <span class="detail-label">Similarity</span>
          <span class="detail-value">{{ scoreData.details?.similarity || 0 }}%</span>
          <small>Overall shape match</small>
        </div>
      </div>
    </div>

    <!-- Character Info -->
    <div class="character-info-section">
      <div class="character-large">
        {{ character }}
      </div>
      <div class="pronunciation">
        <button class="speak-btn" :aria-label="`Play pronunciation of ${character}`" @click="speakCharacter">
          <span class="speaker-icon" aria-hidden="true">🔊</span>
          <span>Hear it!</span>
        </button>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons">
      <button class="action-btn try-again-btn" aria-label="Try again" @click="$emit('try-again')">
        <span class="btn-icon" aria-hidden="true">🔄</span>
        <span>Try Again</span>
      </button>

      <button class="action-btn next-btn" :aria-label="`Next ${charType === 'number' ? 'number' : 'letter'}`" @click="$emit('next')">
        <span class="btn-icon" aria-hidden="true">➡️</span>
        <span>Next {{ charType === 'number' ? 'Number' : 'Letter' }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { onMounted, computed } from 'vue'

export default {
  name: 'ResultsDisplay',
  props: {
    character: {
      type: String,
      required: true
    },
    scoreData: {
      type: Object,
      required: true
    },
    userDrawing: {
      type: String,
      required: true
    },
    attempts: {
      type: Array,
      default: () => []
    },
    bestOf3Mode: {
      type: Boolean,
      default: false
    },
    showDebugMode: {
      type: Boolean,
      default: false
    },
    autoPlaySound: {
      type: Boolean,
      default: true
    }
  },
  emits: ['try-again', 'next', 'play-audio'],
  setup(props, { emit }) {
    const charType = computed(() => {
      if (/[0-9]/.test(props.character)) return 'number'
      return 'letter'
    })

    const speakCharacter = () => {
      emit('play-audio', props.character)
    }

    onMounted(() => {
      if (props.autoPlaySound) {
        setTimeout(() => {
          speakCharacter()
        }, 500)
      }
    })

    return {
      speakCharacter,
      charType
    }
  }
}
</script>

<style scoped>
.results-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 20px;
  overflow-y: auto;
}

.score-section {
  text-align: center;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 20px;
}

.stars {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.star {
  color: rgba(255, 255, 255, 0.3);
  margin: 0 3px;
  transition: all 0.3s ease;
}

.star.filled {
  color: #FFE66D;
  text-shadow: 0 0 20px #FFE66D;
  animation: starPop 0.5s ease-out forwards;
}

.star.filled:nth-child(1) { animation-delay: 0.1s; }
.star.filled:nth-child(2) { animation-delay: 0.2s; }
.star.filled:nth-child(3) { animation-delay: 0.3s; }
.star.filled:nth-child(4) { animation-delay: 0.4s; }
.star.filled:nth-child(5) { animation-delay: 0.5s; }

@keyframes starPop {
  0% { transform: scale(0); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

.score-number {
  font-size: 3rem;
  font-weight: 700;
  color: white;
  text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.2);
}

.feedback {
  font-size: 1.5rem;
  color: #FFE66D;
  font-weight: 600;
  margin-top: 5px;
}

.comparison-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.comparison-item {
  text-align: center;
}

.comparison-item h3 {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 10px;
  font-weight: 500;
}

.image-container {
  background: white;
  border-radius: 15px;
  padding: 10px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.image-container img {
  width: 120px;
  height: 120px;
  object-fit: contain;
}

.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
}

.vs-divider span {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 10px 15px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 1rem;
}

.character-info-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 20px;
}

.character-large {
  font-size: 5rem;
  font-weight: 700;
  color: white;
  text-shadow: 4px 4px 0 rgba(0, 0, 0, 0.2);
}

.speak-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: white;
  padding: 15px 25px;
  border-radius: 20px;
  font-size: 1rem;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
  transition: all 0.2s ease;
}

.speak-btn:hover {
  transform: scale(1.05);
}

.speaker-icon {
  font-size: 2rem;
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
}

.action-btn:hover {
  transform: scale(1.05);
}

.btn-icon {
  font-size: 1.4rem;
}

.try-again-btn {
  background: white;
  color: #764ba2;
}

.next-btn {
  background: linear-gradient(135deg, #4ECDC4 0%, #44B09E 100%);
  color: white;
}

.attempts-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 15px;
}

.attempts-section h3 {
  color: white;
  font-size: 1rem;
  text-align: center;
  margin-bottom: 10px;
}

.attempts-grid {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.attempt-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 10px;
  text-align: center;
  transition: all 0.3s ease;
}

.attempt-card.best {
  background: rgba(78, 205, 196, 0.3);
  box-shadow: 0 0 15px rgba(78, 205, 196, 0.5);
}

.attempt-label {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: white;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.best-badge {
  background: #4ECDC4;
  color: white;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 700;
}

.attempt-card img {
  width: 80px;
  height: 80px;
  object-fit: contain;
  background: white;
  border-radius: 8px;
}

.attempt-score {
  color: #FFE66D;
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 5px;
}

.debug-section {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 15px;
  padding: 15px;
}

.debug-section h3 {
  color: #FFE66D;
  font-size: 1rem;
  margin-bottom: 15px;
  text-align: center;
}

.debug-details {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.detail-label {
  color: #aaa;
  font-size: 0.75rem;
}

.detail-value {
  color: #4ECDC4;
  font-size: 1.2rem;
  font-weight: 700;
}

.detail-item small {
  color: #666;
  font-size: 0.65rem;
  text-align: center;
}

@media (max-width: 600px) {
  .results-container {
    padding: 15px;
    gap: 15px;
  }

  .stars {
    font-size: 2rem;
  }

  .score-number {
    font-size: 2.5rem;
  }

  .feedback {
    font-size: 1.2rem;
  }

  .image-container img {
    width: 100px;
    height: 100px;
  }

  .character-large {
    font-size: 4rem;
  }

  .action-btn {
    padding: 15px 25px;
    font-size: 1rem;
  }
}

@media (min-width: 768px) {
  .image-container img {
    width: 150px;
    height: 150px;
  }
}
</style>
