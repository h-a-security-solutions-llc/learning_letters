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
      <button class="settings-button" @click="showSettings = true">
        <span class="settings-icon">⚙️</span>
      </button>
    </header>

    <!-- Settings Panel -->
    <SettingsPanel
      v-if="showSettings"
      :settings="settings"
      @close="showSettings = false"
      @update:settings="settings = $event"
    />

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
        :dash-tracing-mode="dashTracingMode"
        :current-attempt="currentAttempt"
        :best-of3-mode="bestOf3Mode"
        :attempts="attempts"
        :show-debug-mode="showDebugMode"
        :show-trace-button="settings.enableTraceMode"
        :show-guide-button="settings.enableGuideMode"
        :show-best-of3-button="settings.enableBestOf3"
        :show-debug-button="settings.enableDebugMode"
        :show-step-by-step-button="settings.enableStepByStep"
        :selected-font="settings.selectedFont"
        :voice-gender="settings.voiceGender"
        :guided-mode="guidedMode"
        :current-stroke-step="currentStrokeStep"
        @submit="onSubmitDrawing"
        @toggle-tracing="tracingMode = !tracingMode"
        @toggle-dash-tracing="dashTracingMode = !dashTracingMode"
        @toggle-best-of-3="toggleBestOf3"
        @toggle-debug-mode="toggleDebugMode"
        @toggle-guided="toggleGuidedMode"
        @stroke-completed="onStrokeCompleted"
        @reset-guided-progress="onResetGuidedProgress"
        @guided-complete="onGuidedComplete"
      />

      <!-- Results View -->
      <ResultsDisplay
        v-else-if="currentView === 'results'"
        :character="selectedCharacter"
        :score-data="scoreData"
        :user-drawing="userDrawing"
        :attempts="attempts"
        :best-of3-mode="bestOf3Mode"
        :show-debug-mode="showDebugMode"
        @try-again="onTryAgain"
        @next="onNextCharacter"
      />
    </main>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import CharacterSelection from './components/CharacterSelection.vue'
import DrawingCanvas from './components/DrawingCanvas.vue'
import ResultsDisplay from './components/ResultsDisplay.vue'
import SettingsPanel from './components/SettingsPanel.vue'

const SETTINGS_KEY = 'learning_letters_settings'

const defaultSettings = {
  enableBestOf3: true,
  enableTraceMode: true,
  traceModeDefault: false,
  enableGuideMode: true,
  guideModeDefault: false,
  enableDebugMode: false,
  enableStepByStep: true,
  selectedFont: 'Fredoka-Regular',
  voiceGender: 'rachel',
  autoPlaySound: true
}

export default {
  name: 'App',
  components: {
    CharacterSelection,
    DrawingCanvas,
    ResultsDisplay,
    SettingsPanel
  },
  setup() {
    const currentView = ref('selection')
    const selectedCharacter = ref(null)
    const tracingMode = ref(false)
    const dashTracingMode = ref(false)
    const scoreData = ref(null)
    const userDrawing = ref(null)

    // Best of 3 mode
    const bestOf3Mode = ref(false)  // Default to disabled
    const attempts = ref([])  // Array of { imageData, scoreResult }
    const currentAttempt = ref(1)

    // Debug mode - show processing details
    const showDebugMode = ref(false)

    // Step-by-step guided mode
    const guidedMode = ref(false)
    const currentStrokeStep = ref(0)  // 0-indexed

    // Settings
    const showSettings = ref(false)
    const settings = ref({ ...defaultSettings })

    // Load settings from localStorage
    const loadSettings = () => {
      try {
        const saved = localStorage.getItem(SETTINGS_KEY)
        if (saved) {
          const parsed = JSON.parse(saved)
          settings.value = { ...defaultSettings, ...parsed }
        }
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }

    // Save settings to localStorage
    const saveSettings = () => {
      try {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings.value))
      } catch (e) {
        console.error('Failed to save settings:', e)
      }
    }

    // Watch settings for changes
    watch(settings, saveSettings, { deep: true })

    // Load settings on mount
    onMounted(loadSettings)

    const playCharacterAudio = async (character) => {
      try {
        const audio = new Audio(`/api/audio/${encodeURIComponent(character)}?voice=${settings.value.voiceGender}`)
        await audio.play()
      } catch (error) {
        console.error('Failed to play audio:', error)
      }
    }

    const onSelectCharacter = (character) => {
      selectedCharacter.value = character
      // Apply default modes from settings
      tracingMode.value = settings.value.enableGuideMode && settings.value.guideModeDefault
      dashTracingMode.value = settings.value.enableTraceMode && settings.value.traceModeDefault
      attempts.value = []
      currentAttempt.value = 1
      currentView.value = 'drawing'

      // Auto-play pronunciation if enabled
      if (settings.value.autoPlaySound) {
        playCharacterAudio(character)
      }
    }

    const onSubmitDrawing = async (drawingData) => {
      if (bestOf3Mode.value) {
        // Add to attempts
        attempts.value.push({
          imageData: drawingData.imageData,
          scoreResult: drawingData.scoreResult
        })

        if (currentAttempt.value < 3) {
          // More attempts remaining
          currentAttempt.value++
          // Stay on drawing view but canvas will be cleared
        } else {
          // All 3 attempts done - find best score
          const bestAttempt = attempts.value.reduce((best, current) =>
            current.scoreResult.score > best.scoreResult.score ? current : best
          )
          userDrawing.value = bestAttempt.imageData
          scoreData.value = bestAttempt.scoreResult
          currentView.value = 'results'
        }
      } else {
        // Single attempt mode
        userDrawing.value = drawingData.imageData
        scoreData.value = drawingData.scoreResult
        currentView.value = 'results'
      }
    }

    const onTryAgain = () => {
      attempts.value = []
      currentAttempt.value = 1
      currentView.value = 'drawing'
    }

    const onNextCharacter = () => {
      currentView.value = 'selection'
      selectedCharacter.value = null
      scoreData.value = null
      userDrawing.value = null
      attempts.value = []
      currentAttempt.value = 1
    }

    const goBack = () => {
      if (currentView.value === 'results') {
        currentView.value = 'drawing'
        attempts.value = []
        currentAttempt.value = 1
      } else {
        currentView.value = 'selection'
        selectedCharacter.value = null
      }
    }

    const toggleBestOf3 = () => {
      bestOf3Mode.value = !bestOf3Mode.value
      // Reset attempts when toggling mode
      attempts.value = []
      currentAttempt.value = 1
    }

    const toggleDebugMode = () => {
      showDebugMode.value = !showDebugMode.value
    }

    const toggleGuidedMode = () => {
      guidedMode.value = !guidedMode.value
      if (guidedMode.value) {
        currentStrokeStep.value = 0
      }
    }

    const onStrokeCompleted = (stepIndex) => {
      // Advance to next stroke
      currentStrokeStep.value = stepIndex + 1
    }

    const onResetGuidedProgress = () => {
      // Reset to first stroke but stay in guided mode
      currentStrokeStep.value = 0
    }

    const onGuidedComplete = () => {
      // All strokes completed in guided mode
      // Could show a celebration or auto-submit
      console.log('Guided mode complete!')
    }

    return {
      currentView,
      selectedCharacter,
      tracingMode,
      dashTracingMode,
      scoreData,
      userDrawing,
      bestOf3Mode,
      attempts,
      currentAttempt,
      onSelectCharacter,
      onSubmitDrawing,
      onTryAgain,
      onNextCharacter,
      goBack,
      toggleBestOf3,
      showDebugMode,
      toggleDebugMode,
      guidedMode,
      currentStrokeStep,
      toggleGuidedMode,
      onStrokeCompleted,
      onResetGuidedProgress,
      onGuidedComplete,
      showSettings,
      settings,
      playCharacterAudio
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

.settings-button {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  color: #764ba2;
  padding: 10px;
  border-radius: 50%;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  width: 45px;
  height: 45px;
}

.settings-button:hover {
  background: white;
}

.settings-icon {
  line-height: 1;
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
