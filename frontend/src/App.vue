<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <h1>
        <span class="title-letter" style="color: #FF6B6B;">A</span>
        <span class="title-letter" style="color: #4ECDC4;">B</span>
        <span class="title-letter" style="color: #FFE66D;">C</span>
        <span class="title-text"> & </span>
        <span class="title-letter" style="color: #FF6B6B;">1</span>
        <span class="title-letter" style="color: #4ECDC4;">2</span>
        <span class="title-letter" style="color: #FFE66D;">3</span>
      </h1>
      <button v-if="currentView !== 'selection'" class="back-button" @click="goBack">
        <span class="back-arrow">←</span> Back
      </button>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Character Selection View -->
      <CharacterSelection
        v-if="currentView === 'selection'"
        @select-character="onSelectCharacter"
      />

      <!-- Drawing View -->
      <DrawingCanvas
        v-else-if="currentView === 'drawing'"
        :character="selectedCharacter"
        :tracing-mode="tracingMode"
        @submit="onSubmitDrawing"
        @toggle-tracing="tracingMode = !tracingMode"
      />

      <!-- Results View -->
      <ResultsDisplay
        v-else-if="currentView === 'results'"
        :character="selectedCharacter"
        :score-data="scoreData"
        :user-drawing="userDrawing"
        @try-again="onTryAgain"
        @next="onNextCharacter"
      />
    </main>
  </div>
</template>

<script>
import { ref } from 'vue'
import CharacterSelection from './components/CharacterSelection.vue'
import DrawingCanvas from './components/DrawingCanvas.vue'
import ResultsDisplay from './components/ResultsDisplay.vue'

export default {
  name: 'App',
  components: {
    CharacterSelection,
    DrawingCanvas,
    ResultsDisplay
  },
  setup() {
    const currentView = ref('selection')
    const selectedCharacter = ref(null)
    const tracingMode = ref(false)
    const scoreData = ref(null)
    const userDrawing = ref(null)

    const onSelectCharacter = (character) => {
      selectedCharacter.value = character
      tracingMode.value = false
      currentView.value = 'drawing'
    }

    const onSubmitDrawing = async (drawingData) => {
      userDrawing.value = drawingData.imageData
      scoreData.value = drawingData.scoreResult
      currentView.value = 'results'
    }

    const onTryAgain = () => {
      currentView.value = 'drawing'
    }

    const onNextCharacter = () => {
      currentView.value = 'selection'
      selectedCharacter.value = null
      scoreData.value = null
      userDrawing.value = null
    }

    const goBack = () => {
      if (currentView.value === 'results') {
        currentView.value = 'drawing'
      } else {
        currentView.value = 'selection'
        selectedCharacter.value = null
      }
    }

    return {
      currentView,
      selectedCharacter,
      tracingMode,
      scoreData,
      userDrawing,
      onSelectCharacter,
      onSubmitDrawing,
      onTryAgain,
      onNextCharacter,
      goBack
    }
  }
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.app-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  position: relative;
}

.app-header h1 {
  font-size: 2rem;
  font-weight: 700;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.title-letter {
  display: inline-block;
  animation: bounce 0.6s ease-in-out infinite alternate;
  text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.2);
}

.title-letter:nth-child(2) { animation-delay: 0.1s; }
.title-letter:nth-child(3) { animation-delay: 0.2s; }
.title-letter:nth-child(5) { animation-delay: 0.3s; }
.title-letter:nth-child(6) { animation-delay: 0.4s; }
.title-letter:nth-child(7) { animation-delay: 0.5s; }

.title-text {
  color: white;
  margin: 0 5px;
}

@keyframes bounce {
  from { transform: translateY(0); }
  to { transform: translateY(-5px); }
}

.back-button {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  color: #764ba2;
  padding: 10px 20px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.back-button:hover {
  background: white;
}

.back-arrow {
  font-size: 1.2rem;
}

.main-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

@media (max-width: 600px) {
  .app-header h1 {
    font-size: 1.5rem;
  }

  .back-button {
    padding: 8px 15px;
    font-size: 0.9rem;
  }
}
</style>
