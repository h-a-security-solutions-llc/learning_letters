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
          :style="{ '--char-color': getCharColor(char), fontFamily: fontFamily }"
          :aria-label="getCharacterLabel(char)"
          @click="$emit('select-character', char)"
        >
          {{ char }}
        </button>
      </div>
    </div>

    <!-- Instructions -->
    <div class="instructions">
      <p>Tap a letter or number to start learning!</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { apiUrl } from '@/config/api'

export default {
  name: 'CharacterSelection',
  props: {
    selectedFont: {
      type: String,
      default: 'Fredoka-Regular'
    }
  },
  emits: ['select-character'],
  setup(props) {
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

    // Font loading for character display
    const fontFamily = computed(() => {
      // Map font file names to CSS font family names
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
      // Create @font-face rule dynamically
      const fontMap = {
        'Fredoka-Regular': { family: 'Fredoka', file: 'Fredoka-Regular.ttf' },
        'Nunito-Regular': { family: 'Nunito', file: 'Nunito-Regular.ttf' },
        'PlaywriteUS-Regular': { family: 'PlaywriteUS', file: 'PlaywriteUS-Regular.ttf' },
        'PatrickHand-Regular': { family: 'PatrickHand', file: 'PatrickHand-Regular.ttf' },
        'Schoolbell-Regular': { family: 'Schoolbell', file: 'Schoolbell-Regular.ttf' }
      }

      const fontInfo = fontMap[fontName]
      if (!fontInfo) return

      // Check if font is already loaded
      const styleId = `font-${fontInfo.family}`
      if (document.getElementById(styleId)) return

      // Create style element with @font-face
      const style = document.createElement('style')
      style.id = styleId
      style.textContent = `
        @font-face {
          font-family: '${fontInfo.family}';
          src: url('${apiUrl(`/api/fonts/${fontInfo.file}`)}') format('truetype');
          font-weight: normal;
          font-style: normal;
          font-display: swap;
        }
      `
      document.head.appendChild(style)
    }

    // Load font on mount and when it changes
    onMounted(() => {
      loadFont(props.selectedFont)
    })

    watch(() => props.selectedFont, (newFont) => {
      loadFont(newFont)
    })

    return {
      categories,
      activeCategory,
      currentCharacters,
      getCharColor,
      getCharacterLabel,
      fontFamily
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
