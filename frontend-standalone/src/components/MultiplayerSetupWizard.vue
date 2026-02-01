<template>
  <div class="wizard-overlay" @click.self="$emit('close')">
    <div class="wizard-panel">
      <div class="wizard-header">
        <h2>Multiplayer Setup</h2>
        <button class="close-button" @click="$emit('close')">
          ×
        </button>
      </div>

      <div class="wizard-content">
        <!-- Step 1: Player Count -->
        <div v-if="currentStep === 1" class="step-content">
          <h3>How many players?</h3>
          <div class="player-count-options">
            <button
              v-for="count in [2, 3, 4]"
              :key="count"
              class="count-btn"
              :class="{ selected: playerCount === count }"
              @click="selectPlayerCount(count)"
            >
              <span class="count-number">{{ count }}</span>
              <span class="count-label">Players</span>
            </button>
          </div>
        </div>

        <!-- Step 2: Player Settings -->
        <div v-if="currentStep === 2" class="step-content">
          <h3>Player Settings</h3>
          <div class="players-list">
            <div
              v-for="(player, index) in players"
              :key="index"
              class="player-card"
            >
              <div class="player-header">
                <span class="player-number">{{ index + 1 }}</span>
                <input
                  v-model="player.name"
                  type="text"
                  class="player-name-input"
                  :placeholder="`Player ${index + 1}`"
                  maxlength="15"
                >
              </div>
              <div class="player-options">
                <label class="option-toggle">
                  <input
                    v-model="player.traceModeAllowed"
                    type="checkbox"
                  >
                  <span class="toggle-slider" />
                  <span class="option-label">Trace Mode</span>
                </label>
                <label class="option-toggle">
                  <input
                    v-model="player.stepByStepAllowed"
                    type="checkbox"
                  >
                  <span class="toggle-slider" />
                  <span class="option-label">Step-by-Step</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step Indicator -->
      <div class="step-indicator">
        <span class="step-dot" :class="{ active: currentStep === 1 }" />
        <span class="step-dot" :class="{ active: currentStep === 2 }" />
      </div>

      <!-- Footer Buttons -->
      <div class="wizard-footer">
        <button
          v-if="currentStep > 1"
          class="footer-btn back-btn"
          @click="previousStep"
        >
          Back
        </button>
        <button
          v-if="currentStep === 1"
          class="footer-btn next-btn"
          :disabled="!playerCount"
          @click="nextStep"
        >
          Next
        </button>
        <button
          v-if="currentStep === 2"
          class="footer-btn start-btn"
          @click="startGame"
        >
          Start Game
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'MultiplayerSetupWizard',
  props: {
    defaultTraceModeAllowed: {
      type: Boolean,
      default: true
    },
    defaultStepByStepAllowed: {
      type: Boolean,
      default: true
    },
    savedPlayers: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'start-game'],
  setup(props, { emit }) {
    const currentStep = ref(1)
    const playerCount = ref(null)
    const players = ref([])

    onMounted(() => {
      if (props.savedPlayers.length >= 2) {
        playerCount.value = props.savedPlayers.length
      }
    })

    const selectPlayerCount = (count) => {
      playerCount.value = count
    }

    const initializePlayers = () => {
      players.value = Array.from({ length: playerCount.value }, (_, i) => {
        const savedPlayer = props.savedPlayers[i]
        if (savedPlayer) {
          return {
            name: savedPlayer.name || `Player ${i + 1}`,
            traceModeAllowed: savedPlayer.traceModeAllowed ?? props.defaultTraceModeAllowed,
            stepByStepAllowed: savedPlayer.stepByStepAllowed ?? props.defaultStepByStepAllowed
          }
        }
        return {
          name: `Player ${i + 1}`,
          traceModeAllowed: props.defaultTraceModeAllowed,
          stepByStepAllowed: props.defaultStepByStepAllowed
        }
      })
    }

    const nextStep = () => {
      if (currentStep.value === 1 && playerCount.value) {
        initializePlayers()
        currentStep.value = 2
      }
    }

    const previousStep = () => {
      if (currentStep.value > 1) {
        currentStep.value--
      }
    }

    const startGame = () => {
      const finalPlayers = players.value.map((player, index) => ({
        ...player,
        name: player.name.trim() || `Player ${index + 1}`
      }))
      emit('start-game', finalPlayers)
    }

    return {
      currentStep,
      playerCount,
      players,
      selectPlayerCount,
      nextStep,
      previousStep,
      startGame
    }
  }
}
</script>

<style scoped>
.wizard-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 100;
  display: flex;
  justify-content: flex-end;
}

.wizard-panel {
  width: 400px;
  max-width: 95vw;
  background: white;
  height: 100%;
  box-shadow: -5px 0 20px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.wizard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.wizard-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.wizard-content {
  flex: 1;
  overflow-y: auto;
  padding: 25px;
}

.step-content h3 {
  text-align: center;
  color: #333;
  margin-bottom: 25px;
  font-size: 1.3rem;
}

.player-count-options {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.count-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 90px;
  border: 3px solid #ddd;
  border-radius: 20px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.count-btn:hover {
  border-color: #4ECDC4;
  transform: scale(1.05);
}

.count-btn.selected {
  border-color: #4ECDC4;
  background: rgba(78, 205, 196, 0.1);
  box-shadow: 0 0 15px rgba(78, 205, 196, 0.3);
}

.count-number {
  font-size: 2rem;
  font-weight: 700;
  color: #764ba2;
}

.count-label {
  font-size: 0.85rem;
  color: #666;
}

.players-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.player-card {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 15px;
  border: 2px solid #eee;
}

.player-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.player-number {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
}

.player-name-input {
  flex: 1;
  padding: 10px 15px;
  border: 2px solid #ddd;
  border-radius: 10px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.player-name-input:focus {
  border-color: #4ECDC4;
  outline: none;
}

.player-options {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.option-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.option-toggle input {
  display: none;
}

.toggle-slider {
  width: 40px;
  height: 22px;
  background: #ccc;
  border-radius: 11px;
  position: relative;
  transition: background 0.3s;
  flex-shrink: 0;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.option-toggle input:checked + .toggle-slider {
  background: #4ECDC4;
}

.option-toggle input:checked + .toggle-slider::after {
  transform: translateX(18px);
}

.option-label {
  font-size: 0.9rem;
  color: #555;
}

.step-indicator {
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 15px;
}

.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ddd;
  transition: all 0.3s;
}

.step-dot.active {
  background: #4ECDC4;
  transform: scale(1.2);
}

.wizard-footer {
  display: flex;
  justify-content: space-between;
  gap: 15px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.footer-btn {
  flex: 1;
  padding: 15px 25px;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn {
  background: #f0f0f0;
  color: #666;
  border: none;
}

.back-btn:hover {
  background: #e0e0e0;
}

.next-btn,
.start-btn {
  background: linear-gradient(135deg, #4ECDC4 0%, #44B09E 100%);
  color: white;
  border: none;
}

.next-btn:hover:not(:disabled),
.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
}

.next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .wizard-panel {
    width: 100%;
    max-width: 100%;
  }

  .player-options {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
