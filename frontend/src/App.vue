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
      <button
        v-if="currentView !== 'selection'"
        class="back-button"
        aria-label="Go back"
        @click="handleBackClick"
      >
        <span class="back-arrow" aria-hidden="true">←</span> Back
      </button>
      <div class="header-buttons">
        <!-- Multiplayer Scoreboard -->
        <div v-if="isMultiplayerMode && players.length > 0" class="scoreboard">
          <span class="scoreboard-label">Rounds {{ roundsPlayed }}</span>
          <span class="scoreboard-divider">|</span>
          <span
            v-for="(player, index) in players"
            :key="index"
            class="player-score"
          >
            <span class="player-name-short">{{ player.name.substring(0, 8) }}</span>
            <span class="player-wins">{{ playerWins[index] || 0 }}</span>
          </span>
        </div>
        <div class="mode-toggle" role="group" aria-label="Game mode selection">
          <button
            class="mode-btn"
            :class="{ active: !isMultiplayerMode }"
            title="Single Player"
            :aria-pressed="!isMultiplayerMode"
            aria-label="Single player mode"
            @click="switchToSinglePlayer"
          >
            <span class="mode-icon" aria-hidden="true">👤</span>
          </button>
          <button
            class="mode-btn"
            :class="{ active: isMultiplayerMode }"
            title="Multiplayer"
            :aria-pressed="isMultiplayerMode"
            aria-label="Multiplayer mode"
            @click="showMultiplayerSetup = true"
          >
            <span class="mode-icon" aria-hidden="true">👥</span>
          </button>
        </div>
        <!-- User Menu (when logged in) or Settings Button -->
        <UserMenu v-if="isAuthenticated" @logout="() => {}" />
        <button class="settings-button" aria-label="Open settings" @click="showSettings = true">
          <span class="settings-icon" aria-hidden="true">⚙️</span>
        </button>
      </div>
    </header>

    <!-- Settings Panel -->
    <SettingsPanel
      v-if="showSettings"
      :settings="settings"
      @close="showSettings = false"
      @update:settings="settings = $event"
      @show-auth="openAuthModal"
    />

    <!-- Auth Modal -->
    <AuthModal
      v-if="showAuthModal"
      :initial-mode="authModalMode"
      @close="showAuthModal = false"
      @success="onAuthSuccess"
    />

    <!-- Multiplayer Setup Wizard -->
    <MultiplayerSetupWizard
      v-if="showMultiplayerSetup"
      :default-trace-mode-allowed="settings.enableTraceMode"
      :default-step-by-step-allowed="settings.enableStepByStep"
      :saved-players="settings.rememberMultiplayerPlayers ? savedMultiplayerPlayers : []"
      @close="showMultiplayerSetup = false"
      @start-game="onStartMultiplayerGame"
    />

    <!-- Back Confirmation Modal -->
    <div v-if="showBackConfirm" class="confirm-overlay" @click.self="showBackConfirm = false">
      <div class="confirm-modal">
        <h3>Leave Game?</h3>
        <p>This will end the multiplayer game and lose all progress.</p>
        <div class="confirm-buttons">
          <button class="confirm-btn cancel" @click="showBackConfirm = false">
            Cancel
          </button>
          <button class="confirm-btn leave" @click="confirmBack">
            Leave
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Character Selection View -->
      <CharacterSelection
        v-if="currentView === 'selection'"
        :selected-font="settings.selectedFont"
        :progress="userProgress"
        @select-character="onSelectCharacter"
      />

      <!-- Drawing View -->
      <DrawingCanvas
        v-else-if="currentView === 'drawing'"
        :character="selectedCharacter"
        :dash-tracing-mode="dashTracingMode"
        :current-attempt="currentAttempt"
        :best-of3-mode="bestOf3Mode"
        :attempts="attempts"
        :show-debug-mode="showDebugMode"
        :show-trace-button="effectiveShowTraceButton"
        :show-best-of3-button="!isMultiplayerMode && settings.enableBestOf3"
        :show-debug-button="settings.enableDebugMode"
        :show-step-by-step-button="effectiveShowStepByStepButton"
        :selected-font="settings.selectedFont"
        :voice-gender="settings.voiceGender"
        :guided-mode="guidedMode"
        :current-stroke-step="currentStrokeStep"
        :high-contrast-mode="settings.highContrastMode"
        :player-name="currentPlayer?.name"
        :player-number="currentPlayerIndex + 1"
        :total-players="players.length"
        :stroke-tolerance="settings.strokeTolerance"
        :color-blind-mode="settings.colorBlindMode"
        :audio-speed="settings.audioSpeed"
        :enable-captions="settings.enableCaptions"
        :high-score-for-mode="highScoreForMode"
        :is-multiplayer="isMultiplayerMode"
        @submit="onSubmitDrawing"
        @toggle-dash-tracing="toggleDashTracing"
        @toggle-best-of-3="toggleBestOf3"
        @toggle-debug-mode="toggleDebugMode"
        @toggle-guided="toggleGuidedMode"
        @stroke-completed="onStrokeCompleted"
        @reset-guided-progress="onResetGuidedProgress"
        @guided-complete="onGuidedComplete"
        @play-audio="playCharacterAudio"
      />

      <!-- Results View (Single Player) -->
      <ResultsDisplay
        v-else-if="currentView === 'results'"
        :character="selectedCharacter"
        :score-data="scoreData"
        :user-drawing="userDrawing"
        :attempts="attempts"
        :best-of3-mode="bestOf3Mode"
        :show-debug-mode="showDebugMode"
        :voice-gender="settings.voiceGender"
        :auto-play-sound="settings.autoPlaySound"
        :audio-speed="settings.audioSpeed"
        :enable-captions="settings.enableCaptions"
        @try-again="onTryAgain"
        @next="onNextCharacter"
        @play-audio="playCharacterAudio"
      />

      <!-- Multiplayer Results View -->
      <MultiplayerResultsDisplay
        v-else-if="currentView === 'multiplayer-results'"
        :player-results="playerResults"
        :character="selectedCharacter"
        :voice-gender="settings.voiceGender"
        :audio-speed="settings.audioSpeed"
        :enable-captions="settings.enableCaptions"
        @play-again="onMultiplayerPlayAgain"
        @next-letter="onMultiplayerNextLetter"
        @play-audio="playCharacterAudio"
      />
    </main>

    <!-- Audio Caption Toast -->
    <AudioCaption
      :caption="currentCaption"
      :is-visible="captionVisible"
    />
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { apiUrl } from '@/config/api'
import CharacterSelection from './components/CharacterSelection.vue'
import DrawingCanvas from './components/DrawingCanvas.vue'
import ResultsDisplay from './components/ResultsDisplay.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import MultiplayerSetupWizard from './components/MultiplayerSetupWizard.vue'
import MultiplayerResultsDisplay from './components/MultiplayerResultsDisplay.vue'
import AudioCaption from './components/AudioCaption.vue'
import AuthModal from './components/AuthModal.vue'
import UserMenu from './components/UserMenu.vue'
import { useAudioCaptions } from './composables/useAudioCaptions'
import { useAuth } from './composables/useAuth'
import { useSync } from './composables/useSync'
import { progressApi } from './services/api'

const SETTINGS_KEY = 'learning_letters_settings'
const MULTIPLAYER_PLAYERS_KEY = 'learning_letters_multiplayer_players'

const defaultSettings = {
  enableBestOf3: true,
  enableTraceMode: true,
  traceModeDefault: false,
  enableDebugMode: false,
  enableStepByStep: true,
  stepByStepDefault: false,
  selectedFont: 'Fredoka-Regular',
  voiceGender: 'rachel',
  autoPlaySound: true,
  rememberMultiplayerPlayers: true,
  highContrastMode: false,
  // Accessibility settings
  uiScale: 100,
  reducedMotion: false,  // false = show animations (default), null = system preference, true = reduce motion
  audioSpeed: 1.0,
  strokeTolerance: 0.5,
  colorBlindMode: false,
  enableCaptions: false
}

export default {
  name: 'App',
  components: {
    CharacterSelection,
    DrawingCanvas,
    ResultsDisplay,
    SettingsPanel,
    MultiplayerSetupWizard,
    MultiplayerResultsDisplay,
    AudioCaption,
    AuthModal,
    UserMenu
  },
  setup() {
    const currentView = ref('selection')
    const selectedCharacter = ref(null)
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

    // Multiplayer state
    const isMultiplayerMode = ref(false)
    const showMultiplayerSetup = ref(false)
    const players = ref([])  // [{ name, traceModeAllowed, stepByStepAllowed }]
    const currentPlayerIndex = ref(0)
    const playerResults = ref([])  // [{ name, imageData, scoreResult }]
    const showBackConfirm = ref(false)
    const savedMultiplayerPlayers = ref([])  // Persisted player configurations
    const roundsPlayed = ref(0)  // Number of completed rounds
    const playerWins = ref([])  // Wins per player index [0, 1, 2, ...]

    // Auth state
    const { user, isAuthenticated, initAuth } = useAuth()
    const showAuthModal = ref(false)
    const authModalMode = ref('login')

    // Sync state
    const { mergeOnLogin, pushSettings, pushMultiplayerPlayers, syncMultiplayerPlayersOnLogin } = useSync()

    // Progress tracking
    const userProgress = ref([])

    // Computed properties for multiplayer
    const currentPlayer = computed(() =>
      isMultiplayerMode.value ? players.value[currentPlayerIndex.value] : null
    )

    const effectiveShowTraceButton = computed(() =>
      currentPlayer.value?.traceModeAllowed ?? settings.value.enableTraceMode
    )

    const effectiveShowStepByStepButton = computed(() =>
      currentPlayer.value?.stepByStepAllowed ?? settings.value.enableStepByStep
    )

    // Compute current drawing mode based on mode toggles
    const currentDrawingMode = computed(() => {
      if (guidedMode.value) return 'step-by-step'
      if (dashTracingMode.value) return 'tracing'
      return 'freestyle'
    })

    // Compute high score for the current character/font/mode
    const highScoreForMode = computed(() => {
      if (!isAuthenticated.value || !selectedCharacter.value) return null

      const progress = userProgress.value.find(p =>
        p.character === selectedCharacter.value &&
        p.font_name === settings.value.selectedFont &&
        p.mode === currentDrawingMode.value
      )

      return progress?.high_score ?? null
    })

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

    // Save settings to localStorage and sync to server if authenticated
    const saveSettings = async () => {
      try {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings.value))
        // Sync to server if authenticated
        if (isAuthenticated.value) {
          await pushSettings(settings.value)
        }
      } catch (e) {
        console.error('Failed to save settings:', e)
      }
    }

    // Watch settings for changes
    watch(settings, saveSettings, { deep: true })

    // Watch high contrast mode and apply to body
    watch(() => settings.value.highContrastMode, (enabled) => {
      if (enabled) {
        document.body.classList.add('high-contrast')
      } else {
        document.body.classList.remove('high-contrast')
      }
    }, { immediate: true })

    // Watch UI scale and apply to body
    watch(() => settings.value.uiScale, (scale) => {
      document.body.classList.remove('ui-scale-100', 'ui-scale-125', 'ui-scale-150')
      document.body.classList.add(`ui-scale-${scale}`)
    }, { immediate: true })

    // Watch reduced motion setting and apply to body
    watch(() => settings.value.reducedMotion, (value) => {
      // Remove both classes first
      document.body.classList.remove('reduced-motion', 'motion-enabled')
      // null = follow system preference (no class needed)
      // true = force reduced motion
      // false = force motion enabled
      if (value === true) {
        document.body.classList.add('reduced-motion')
      } else if (value === false) {
        document.body.classList.add('motion-enabled')
      }
    }, { immediate: true })

    // Load/save multiplayer players
    const loadMultiplayerPlayers = () => {
      try {
        const saved = localStorage.getItem(MULTIPLAYER_PLAYERS_KEY)
        if (saved) {
          savedMultiplayerPlayers.value = JSON.parse(saved)
        }
      } catch (e) {
        console.error('Failed to load multiplayer players:', e)
      }
    }

    const saveMultiplayerPlayers = async (playerList) => {
      if (!settings.value.rememberMultiplayerPlayers) return
      try {
        localStorage.setItem(MULTIPLAYER_PLAYERS_KEY, JSON.stringify(playerList))
        savedMultiplayerPlayers.value = playerList
        // Sync to server if authenticated
        if (isAuthenticated.value) {
          await pushMultiplayerPlayers(playerList)
        }
      } catch (e) {
        console.error('Failed to save multiplayer players:', e)
      }
    }

    // Load settings on mount
    onMounted(async () => {
      loadSettings()
      loadMultiplayerPlayers()
      // Apply high contrast mode if enabled
      if (settings.value.highContrastMode) {
        document.body.classList.add('high-contrast')
      }
      // Initialize auth (try to restore session)
      await initAuth()
      // Fetch progress if authenticated
      if (isAuthenticated.value) {
        await fetchProgress()
      }
    })

    // Show auth modal from settings panel
    const openAuthModal = (mode) => {
      authModalMode.value = mode
      showAuthModal.value = true
      showSettings.value = false  // Close settings when opening auth
    }

    // Fetch user progress from server
    const fetchProgress = async () => {
      if (!isAuthenticated.value) {
        userProgress.value = []
        return
      }
      try {
        const response = await progressApi.getAll()
        userProgress.value = response.progress || []
      } catch (e) {
        console.error('Failed to fetch progress:', e)
        userProgress.value = []
      }
    }

    const onAuthSuccess = async () => {
      showAuthModal.value = false
      // Sync settings and multiplayer players after login
      const mergedSettings = await mergeOnLogin()
      if (mergedSettings) {
        settings.value = mergedSettings
      }
      const syncedPlayers = await syncMultiplayerPlayersOnLogin()
      if (syncedPlayers && syncedPlayers.length > 0) {
        savedMultiplayerPlayers.value = syncedPlayers
      }
      // Fetch progress
      await fetchProgress()
    }

    // Audio captions
    const { currentCaption, isVisible: captionVisible, showCaption, hideCaptionAfterDelay } = useAudioCaptions()

    const playCharacterAudio = async (character) => {
      try {
        const audio = new Audio(apiUrl(`/api/audio/${encodeURIComponent(character)}?voice=${settings.value.voiceGender}`))
        audio.playbackRate = settings.value.audioSpeed

        // Show caption if enabled
        if (settings.value.enableCaptions) {
          showCaption(character)
          audio.onended = () => {
            hideCaptionAfterDelay(800)
          }
        }

        await audio.play()
      } catch (error) {
        console.error('Failed to play audio:', error)
      }
    }

    const onSelectCharacter = (character) => {
      selectedCharacter.value = character
      // Apply default modes from settings
      dashTracingMode.value = settings.value.enableTraceMode && settings.value.traceModeDefault
      guidedMode.value = settings.value.enableStepByStep && settings.value.stepByStepDefault
      attempts.value = []
      currentAttempt.value = 1
      currentStrokeStep.value = 0  // Reset guided mode
      currentView.value = 'drawing'

      // Auto-play pronunciation if enabled
      if (settings.value.autoPlaySound) {
        playCharacterAudio(character)
      }
    }

    // Update local progress cache when a new high score is achieved
    const updateLocalProgress = (scoreResult) => {
      if (!isAuthenticated.value || !scoreResult.is_new_high_score) return

      const mode = currentDrawingMode.value
      const existingIndex = userProgress.value.findIndex(p =>
        p.character === selectedCharacter.value &&
        p.font_name === settings.value.selectedFont &&
        p.mode === mode
      )

      if (existingIndex >= 0) {
        // Update existing entry
        userProgress.value[existingIndex].high_score = scoreResult.high_score_for_mode
        userProgress.value[existingIndex].stars = scoreResult.stars
      } else {
        // Add new entry (server will have created it)
        userProgress.value.push({
          id: '',  // Will be set on next fetch
          character: selectedCharacter.value,
          font_name: settings.value.selectedFont,
          mode: mode,
          high_score: scoreResult.high_score_for_mode,
          stars: scoreResult.stars,
          attempts_count: 1,
          best_attempt_at: new Date().toISOString()
        })
      }
    }

    const onSubmitDrawing = async (drawingData) => {
      // Update local progress cache if user achieved a new high score
      if (!isMultiplayerMode.value) {
        updateLocalProgress(drawingData.scoreResult)
      }

      if (isMultiplayerMode.value) {
        // Store result for current player
        playerResults.value.push({
          name: currentPlayer.value.name,
          imageData: drawingData.imageData,
          scoreResult: drawingData.scoreResult
        })

        if (currentPlayerIndex.value < players.value.length - 1) {
          // More players remaining
          currentPlayerIndex.value++
          currentAttempt.value++  // Triggers canvas clear via watcher
          // Reset guided mode for next player
          guidedMode.value = false
          currentStrokeStep.value = 0
          dashTracingMode.value = false
        } else {
          // All players done - record winner(s) and show results
          recordRoundWinners()
          currentView.value = 'multiplayer-results'
        }
      } else if (bestOf3Mode.value) {
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
      currentStrokeStep.value = 0  // Reset guided mode to step 1
      currentView.value = 'drawing'
    }

    // Character sequences for navigation
    const uppercaseLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
    const lowercaseLetters = 'abcdefghijklmnopqrstuvwxyz'.split('')
    const numbers = '0123456789'.split('')

    const onNextCharacter = () => {
      const current = selectedCharacter.value
      let sequence = []
      let nextChar = null

      // Determine which sequence we're in
      if (/[A-Z]/.test(current)) {
        sequence = uppercaseLetters
      } else if (/[a-z]/.test(current)) {
        sequence = lowercaseLetters
      } else if (/[0-9]/.test(current)) {
        sequence = numbers
      }

      if (sequence.length > 0) {
        const currentIndex = sequence.indexOf(current)
        const nextIndex = (currentIndex + 1) % sequence.length  // Wrap around
        nextChar = sequence[nextIndex]
      }

      if (nextChar) {
        // Go to the next character (reuse onSelectCharacter logic)
        scoreData.value = null
        userDrawing.value = null
        onSelectCharacter(nextChar)
      } else {
        // Fallback to selection screen
        currentView.value = 'selection'
        selectedCharacter.value = null
        scoreData.value = null
        userDrawing.value = null
        attempts.value = []
        currentAttempt.value = 1
      }
    }

    const goBack = async () => {
      // Always go back to character selection (Try Again handles returning to drawing)
      currentView.value = 'selection'
      selectedCharacter.value = null
      scoreData.value = null
      userDrawing.value = null
      attempts.value = []
      currentAttempt.value = 1
      // Refresh progress when returning to selection
      if (isAuthenticated.value) {
        await fetchProgress()
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

    const toggleDashTracing = () => {
      dashTracingMode.value = !dashTracingMode.value
      // Turn off guided mode when trace mode is enabled (mutually exclusive)
      if (dashTracingMode.value && guidedMode.value) {
        guidedMode.value = false
      }
    }

    const toggleGuidedMode = () => {
      guidedMode.value = !guidedMode.value
      if (guidedMode.value) {
        currentStrokeStep.value = 0
        // Turn off trace mode when guided mode is enabled (mutually exclusive)
        if (dashTracingMode.value) {
          dashTracingMode.value = false
        }
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
    }

    // Multiplayer functions
    const recordRoundWinners = () => {
      if (playerResults.value.length === 0) return

      // Find the highest score
      const highestScore = Math.max(...playerResults.value.map(r => r.scoreResult.score))

      // Award a win to all players who achieved the highest score (handles ties)
      playerResults.value.forEach((result, index) => {
        if (result.scoreResult.score === highestScore) {
          playerWins.value[index]++
        }
      })

      roundsPlayed.value++
    }

    const onStartMultiplayerGame = (playerList) => {
      players.value = playerList
      isMultiplayerMode.value = true
      showMultiplayerSetup.value = false
      currentPlayerIndex.value = 0
      playerResults.value = []
      // Reset win tracking for new game
      roundsPlayed.value = 0
      playerWins.value = playerList.map(() => 0)
      // Save players for next time
      saveMultiplayerPlayers(playerList)
      // Go to character selection
      currentView.value = 'selection'
    }

    const switchToSinglePlayer = () => {
      if (isMultiplayerMode.value) {
        isMultiplayerMode.value = false
        players.value = []
        currentPlayerIndex.value = 0
        playerResults.value = []
        // Reset win tracking
        roundsPlayed.value = 0
        playerWins.value = []
        // Reset to selection if in the middle of a game
        if (currentView.value === 'drawing' || currentView.value === 'multiplayer-results') {
          currentView.value = 'selection'
          selectedCharacter.value = null
        }
      }
    }

    const handleBackClick = () => {
      if (isMultiplayerMode.value && currentView.value === 'drawing' && playerResults.value.length > 0) {
        // Show confirmation if players have already drawn
        showBackConfirm.value = true
      } else {
        goBack()
      }
    }

    const confirmBack = () => {
      showBackConfirm.value = false
      // Reset multiplayer state
      playerResults.value = []
      currentPlayerIndex.value = 0
      goBack()
    }

    const onMultiplayerPlayAgain = () => {
      // Same letter, reset players
      playerResults.value = []
      currentPlayerIndex.value = 0
      currentAttempt.value = 1
      currentStrokeStep.value = 0
      guidedMode.value = false
      dashTracingMode.value = false
      currentView.value = 'drawing'
    }

    const onMultiplayerNextLetter = () => {
      // Go to next character (stays in multiplayer mode)
      playerResults.value = []
      currentPlayerIndex.value = 0
      currentAttempt.value = 1
      currentStrokeStep.value = 0
      guidedMode.value = false
      dashTracingMode.value = false
      onNextCharacter()
    }

    return {
      currentView,
      selectedCharacter,
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
      toggleDashTracing,
      guidedMode,
      currentStrokeStep,
      toggleGuidedMode,
      onStrokeCompleted,
      onResetGuidedProgress,
      onGuidedComplete,
      showSettings,
      settings,
      playCharacterAudio,
      // Multiplayer
      isMultiplayerMode,
      showMultiplayerSetup,
      players,
      currentPlayerIndex,
      playerResults,
      currentPlayer,
      effectiveShowTraceButton,
      effectiveShowStepByStepButton,
      onStartMultiplayerGame,
      switchToSinglePlayer,
      handleBackClick,
      showBackConfirm,
      confirmBack,
      onMultiplayerPlayAgain,
      onMultiplayerNextLetter,
      savedMultiplayerPlayers,
      roundsPlayed,
      playerWins,
      // Audio captions
      currentCaption,
      captionVisible,
      // Auth
      user,
      isAuthenticated,
      showAuthModal,
      authModalMode,
      openAuthModal,
      onAuthSuccess,
      // Progress
      userProgress,
      fetchProgress,
      currentDrawingMode,
      highScoreForMode
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

.header-buttons {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Multiplayer Scoreboard */
.scoreboard {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  padding: 8px 14px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  font-size: 0.85rem;
  font-weight: 600;
}

.scoreboard-label {
  color: #764ba2;
}

.scoreboard-divider {
  color: #ccc;
}

.player-score {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(118, 75, 162, 0.1);
  border-radius: 12px;
}

.player-name-short {
  color: #555;
  font-size: 0.8rem;
}

.player-wins {
  color: #764ba2;
  font-weight: 700;
  min-width: 16px;
  text-align: center;
}

.mode-toggle {
  display: flex;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 25px;
  padding: 4px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.mode-btn {
  background: transparent;
  border: none;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.mode-btn:hover:not(.active) {
  background: rgba(102, 126, 234, 0.1);
}

.mode-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.settings-button {
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

/* Back Confirmation Modal */
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 150;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.confirm-modal {
  background: white;
  border-radius: 20px;
  padding: 25px;
  max-width: 350px;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.confirm-modal h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1.4rem;
}

.confirm-modal p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 1rem;
}

.confirm-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.confirm-btn {
  padding: 12px 30px;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.confirm-btn.cancel {
  background: #f0f0f0;
  color: #666;
}

.confirm-btn.cancel:hover {
  background: #e0e0e0;
}

.confirm-btn.leave {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: white;
}

.confirm-btn.leave:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
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

  .header-buttons {
    gap: 6px;
  }

  .scoreboard {
    padding: 5px 8px;
    gap: 5px;
    font-size: 0.7rem;
  }

  .scoreboard-label {
    display: none;
  }

  .scoreboard-divider {
    display: none;
  }

  .player-score {
    padding: 2px 5px;
    gap: 2px;
  }

  .player-name-short {
    font-size: 0.65rem;
    max-width: 40px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .player-wins {
    font-size: 0.75rem;
  }

  .mode-toggle {
    padding: 3px;
  }

  .mode-btn {
    width: 32px;
    height: 32px;
  }

  .mode-icon {
    font-size: 1rem;
  }

  .settings-button {
    width: 38px;
    height: 38px;
    font-size: 1.2rem;
  }
}
</style>
