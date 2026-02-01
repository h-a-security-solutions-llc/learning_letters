<template>
  <div class="selection-container">
    <!-- Category Tabs -->
    <div class="category-tabs" role="tablist" aria-label="Character category selection">
      <button
        v-for="category in categories"
        :key="category.id"
        role="tab"
        :class="['category-tab', { active: activeCategory === category.id }]"
        :style="{ '--tab-color': category.color }"
        :aria-selected="activeCategory === category.id"
        :aria-controls="`${category.id}-panel`"
        @click="activeCategory = category.id"
      >
        {{ category.label }}
      </button>
    </div>

    <!-- Character Grid -->
    <div
      :id="`${activeCategory}-panel`"
      class="character-grid-container"
      role="tabpanel"
      :aria-label="`${activeCategory} characters`"
    >
      <div class="character-grid" role="list">
        <button
          v-for="char in currentCharacters"
          :key="char"
          role="listitem"
          class="character-button"
          :class="{ 'has-progress': getCharProgress(char) }"
          :style="{ '--char-color': getCharColor(char), fontFamily: fontFamily }"
          :aria-label="getCharacterLabel(char)"
          @click="$emit('select-character', char)"
        >
          {{ char }}
          <span v-if="getCharProgress(char)" class="progress-stars" :aria-label="`${getCharProgress(char).stars} stars`">
            <span class="stars-filled">{{ '★'.repeat(getCharProgress(char).stars) }}</span><span class="stars-empty">{{ '★'.repeat(5 - getCharProgress(char).stars) }}</span>
          </span>
        </button>
      </div>
    </div>

    <!-- Instructions and Clear Scores -->
    <div class="instructions">
      <p>Tap a letter or number to start learning!</p>
      <button
        v-if="hasAnyProgress"
        class="clear-scores-btn"
        @click="showClearModal = true"
      >
        Clear Scores
      </button>
    </div>

    <!-- Clear Scores Confirmation Modal -->
    <div v-if="showClearModal" class="modal-overlay" @click.self="showClearModal = false">
      <div class="modal-content">
        <h3>Clear Scores?</h3>
        <p>Are you sure you want to clear scores for:</p>
        <div class="mode-checkboxes">
          <label class="mode-checkbox">
            <input type="checkbox" v-model="clearFreestyle" />
            <span>Freestyle</span>
          </label>
          <label class="mode-checkbox">
            <input type="checkbox" v-model="clearTracing" />
            <span>Tracing</span>
          </label>
          <label class="mode-checkbox">
            <input type="checkbox" v-model="clearStepByStep" />
            <span>Step-by-Step</span>
          </label>
        </div>
        <div class="modal-buttons">
          <button class="modal-btn cancel" @click="showClearModal = false">No</button>
          <button
            class="modal-btn confirm"
            :disabled="!hasSelectedModes"
            @click="confirmClearScores"
          >
            Yes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'

export default {
  name: 'CharacterSelection',
  props: {
    selectedFont: {
      type: String,
      default: 'Fredoka-Regular'
    },
    progress: {
      type: Array,
      default: () => []
    }
  },
  emits: ['select-character', 'clear-scores'],
  setup(props, { emit }) {
    const categories = [
      { id: 'uppercase', label: 'A B C', color: '#FF6B6B' },
      { id: 'lowercase', label: 'a b c', color: '#4ECDC4' },
      { id: 'numbers', label: '1 2 3', color: '#FFE66D' }
    ]

    const activeCategory = ref('uppercase')

    const uppercaseLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
    const lowercaseLetters = 'abcdefghijklmnopqrstuvwxyz'.split('')
    const numbers = '0123456789'.split('')

    const currentCharacters = computed(() => {
      switch (activeCategory.value) {
        case 'uppercase':
          return uppercaseLetters
        case 'lowercase':
          return lowercaseLetters
        case 'numbers':
          return numbers
        default:
          return uppercaseLetters
      }
    })

    const colors = [
      '#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3',
      '#F38181', '#AA96DA', '#FCBAD3', '#A8D8EA',
      '#FFB6B9', '#61C0BF', '#BBDED6', '#FAE3D9'
    ]

    const getCharColor = (char) => {
      const index = char.charCodeAt(0) % colors.length
      return colors[index]
    }

    const getCharacterLabel = (char) => {
      if (/[A-Z]/.test(char)) {
        return `Uppercase letter ${char}`
      } else if (/[a-z]/.test(char)) {
        return `Lowercase letter ${char}`
      } else {
        return `Number ${char}`
      }
    }

    // Get progress for a specific character (freeform mode only, highest stars)
    const getCharProgress = (char) => {
      const freestyleProgress = props.progress.filter(
        p => p.character === char && p.mode === 'freestyle'
      )
      if (freestyleProgress.length === 0) return null
      const result = freestyleProgress.reduce((best, current) =>
        current.stars > best.stars ? current : best
      )
      return result
    }

    // Font loading for character display
    const fontFamily = computed(() => {
      const fontMap = {
        'Fredoka-Regular': 'Fredoka',
        'Nunito-Regular': 'Nunito',
        'PlaywriteUS-Regular': 'PlaywriteUS',
        'PatrickHand-Regular': 'PatrickHand',
        'Schoolbell-Regular': 'Schoolbell'
      }
      return fontMap[props.selectedFont] || 'Fredoka'
    })

    const loadFont = (fontName) => {
      const fontMap = {
        'Fredoka-Regular': { family: 'Fredoka', file: 'Fredoka-Regular.ttf' },
        'Nunito-Regular': { family: 'Nunito', file: 'Nunito-Regular.ttf' },
        'PlaywriteUS-Regular': { family: 'PlaywriteUS', file: 'PlaywriteUS-Regular.ttf' },
        'PatrickHand-Regular': { family: 'PatrickHand', file: 'PatrickHand-Regular.ttf' },
        'Schoolbell-Regular': { family: 'Schoolbell', file: 'Schoolbell-Regular.ttf' }
      }

      const fontInfo = fontMap[fontName]
      if (!fontInfo) return

      const styleId = `font-${fontInfo.family}`
      if (document.getElementById(styleId)) return

      const style = document.createElement('style')
      style.id = styleId
      style.textContent = `
        @font-face {
          font-family: '${fontInfo.family}';
          src: url('/fonts/${fontInfo.file}') format('truetype');
          font-weight: normal;
          font-style: normal;
          font-display: swap;
        }
      `
      document.head.appendChild(style)
    }

    onMounted(() => {
      loadFont(props.selectedFont)
    })

    watch(() => props.selectedFont, (newFont) => {
      loadFont(newFont)
    })

    // Clear scores modal state
    const showClearModal = ref(false)
    const clearFreestyle = ref(true)
    const clearTracing = ref(true)
    const clearStepByStep = ref(true)

    const hasAnyProgress = computed(() => props.progress.length > 0)

    const hasSelectedModes = computed(() =>
      clearFreestyle.value || clearTracing.value || clearStepByStep.value
    )

    const confirmClearScores = () => {
      const modes = []
      if (clearFreestyle.value) modes.push('freestyle')
      if (clearTracing.value) modes.push('tracing')
      if (clearStepByStep.value) modes.push('step-by-step')

      emit('clear-scores', modes)
      showClearModal.value = false

      clearFreestyle.value = true
      clearTracing.value = true
      clearStepByStep.value = true
    }

    return {
      categories,
      activeCategory,
      currentCharacters,
      getCharColor,
      getCharacterLabel,
      fontFamily,
      getCharProgress,
      showClearModal,
      clearFreestyle,
      clearTracing,
      clearStepByStep,
      hasAnyProgress,
      hasSelectedModes,
      confirmClearScores
    }
  }
}
</script>

<style scoped>
.selection-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 20px;
}

.category-tabs {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.category-tab {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 15px 30px;
  border-radius: 30px;
  font-size: 1.3rem;
  font-weight: 600;
  transition: all 0.3s ease;
  border: 3px solid transparent;
}

.category-tab.active {
  background: white;
  color: var(--tab-color);
  border-color: var(--tab-color);
  transform: scale(1.05);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.category-tab:hover:not(.active) {
  background: rgba(255, 255, 255, 0.4);
}

.character-grid-container {
  flex: 1;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 20px;
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  gap: 15px;
  justify-items: center;
}

.character-button {
  width: 70px;
  height: 70px;
  background: white;
  color: var(--char-color);
  border-radius: 15px;
  font-size: 2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;
}

.character-button:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
}

.character-button:active {
  transform: scale(0.95);
}

.character-button.has-progress {
  position: relative;
}

.progress-stars {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.7rem;
  line-height: 1;
  white-space: nowrap;
}

.stars-filled {
  color: #FFD700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.stars-empty {
  color: rgba(0, 0, 0, 0.2);
}

.instructions {
  text-align: center;
  padding: 15px;
}

.instructions p {
  color: white;
  font-size: 1.2rem;
  font-weight: 500;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.clear-scores-btn {
  margin-top: 10px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  border: 2px solid rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-scores-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 20px;
  padding: 25px;
  max-width: 350px;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1.4rem;
}

.modal-content p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 1rem;
}

.mode-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 25px;
  text-align: left;
  padding: 0 20px;
}

.mode-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 1rem;
  color: #444;
}

.mode-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #764ba2;
}

.modal-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.modal-btn {
  padding: 12px 30px;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.modal-btn.cancel {
  background: #f0f0f0;
  color: #666;
}

.modal-btn.cancel:hover {
  background: #e0e0e0;
}

.modal-btn.confirm {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: white;
}

.modal-btn.confirm:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
}

.modal-btn.confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .selection-container {
    padding: 10px;
    gap: 10px;
  }

  .category-tabs {
    gap: 10px;
  }

  .category-tab {
    padding: 12px 20px;
    font-size: 1.1rem;
  }

  .character-grid {
    grid-template-columns: repeat(auto-fill, minmax(55px, 1fr));
    gap: 10px;
  }

  .character-button {
    width: 55px;
    height: 55px;
    font-size: 1.5rem;
  }

  .instructions p {
    font-size: 1rem;
  }
}

@media (min-width: 1024px) {
  .character-grid {
    grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
    gap: 20px;
  }

  .character-button {
    width: 90px;
    height: 90px;
    font-size: 2.5rem;
  }
}
</style>
