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
      <div class="score-number">{{ scoreData.score }}%</div>
      <div class="feedback">{{ scoreData.feedback }}</div>
    </div>

    <!-- Comparison Display -->
    <div class="comparison-section">
      <div class="comparison-item">
        <h3>Your Drawing</h3>
        <div class="image-container">
          <img :src="userDrawing" alt="Your drawing" />
        </div>
      </div>

      <div class="vs-divider">
        <span>VS</span>
      </div>

      <div class="comparison-item">
        <h3>Perfect Example</h3>
        <div class="image-container">
          <img :src="scoreData.reference_image" alt="Perfect example" />
        </div>
      </div>
    </div>

    <!-- Character Info -->
    <div class="character-info-section">
      <div class="character-large">{{ character }}</div>
      <div class="pronunciation">
        <button class="speak-btn" @click="speakCharacter">
          <span class="speaker-icon">🔊</span>
          <span>Hear it!</span>
        </button>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons">
      <button class="action-btn try-again-btn" @click="$emit('try-again')">
        <span class="btn-icon">🔄</span>
        <span>Try Again</span>
      </button>

      <button class="action-btn next-btn" @click="$emit('next')">
        <span class="btn-icon">➡️</span>
        <span>Next Letter</span>
      </button>
    </div>
  </div>
</template>

<script>
import { onMounted, ref } from 'vue'
import axios from 'axios'

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
    }
  },
  emits: ['try-again', 'next'],
  setup(props) {
    const characterData = ref(null)

    const fetchCharacterData = async () => {
      try {
        const response = await axios.get(`/api/characters/${encodeURIComponent(props.character)}`)
        characterData.value = response.data
      } catch (error) {
        console.error('Failed to fetch character data:', error)
      }
    }

    const speakCharacter = () => {
      if (!('speechSynthesis' in window)) {
        alert('Sorry, your browser does not support speech!')
        return
      }

      // Cancel any ongoing speech
      window.speechSynthesis.cancel()

      // Determine what to say
      let textToSpeak = ''

      if (/[A-Za-z]/.test(props.character)) {
        // It's a letter
        const letterName = props.character.toUpperCase()
        const isUppercase = props.character === props.character.toUpperCase()

        // Say the letter name
        const nameUtterance = new SpeechSynthesisUtterance(
          `${isUppercase ? 'Capital' : 'Lowercase'} ${letterName}`
        )
        nameUtterance.rate = 0.8
        nameUtterance.pitch = 1.1

        // Say the phonetic sound
        if (characterData.value?.sound) {
          textToSpeak = `${isUppercase ? 'Capital' : 'Lowercase'} ${letterName}. ${characterData.value.sound}`
        } else {
          textToSpeak = `${isUppercase ? 'Capital' : 'Lowercase'} ${letterName}`
        }
      } else {
        // It's a number
        textToSpeak = props.character
      }

      const utterance = new SpeechSynthesisUtterance(textToSpeak)
      utterance.rate = 0.8
      utterance.pitch = 1.1

      // Try to use a child-friendly voice if available
      const voices = window.speechSynthesis.getVoices()
      const preferredVoice = voices.find(v =>
        v.name.includes('Female') ||
        v.name.includes('Samantha') ||
        v.name.includes('Karen') ||
        v.lang.startsWith('en')
      )

      if (preferredVoice) {
        utterance.voice = preferredVoice
      }

      window.speechSynthesis.speak(utterance)
    }

    onMounted(() => {
      fetchCharacterData()

      // Auto-play speech when results are shown
      // Small delay to ensure voices are loaded
      setTimeout(() => {
        if (window.speechSynthesis.getVoices().length === 0) {
          window.speechSynthesis.onvoiceschanged = () => {
            speakCharacter()
          }
        } else {
          speakCharacter()
        }
      }, 500)
    })

    return {
      characterData,
      speakCharacter
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
