<template>
  <div
    class="settings-overlay"
    role="dialog"
    aria-labelledby="settings-title"
    @click.self="$emit('close')"
  >
    <div class="settings-panel" role="document">
      <div class="settings-header">
        <h2 id="settings-title">
          Settings
        </h2>
        <button class="close-button" aria-label="Close settings" @click="$emit('close')">
          <span aria-hidden="true">×</span>
        </button>
      </div>

      <div class="settings-content">
        <!-- Storage Info -->
        <div class="setting-section">
          <h3 class="setting-section-title">
            Data Storage
          </h3>
          <p class="storage-info">
            Your progress and settings are saved locally on this device. No account needed!
          </p>
        </div>

        <!-- Accessibility Section -->
        <div class="setting-section">
          <h3 class="setting-section-title">
            Accessibility
          </h3>

          <!-- High Contrast Mode -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.highContrastMode"
                @change="updateSetting('highContrastMode', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">High Contrast Mode</span>
            </label>
            <p class="setting-description">
              Black and white theme for improved visibility
            </p>
          </div>

          <!-- Text & Button Size -->
          <div class="setting-item">
            <label class="setting-label-standalone">Text &amp; Button Size</label>
            <div class="radio-group">
              <label
                class="radio-option"
                :class="{ active: localSettings.uiScale === 100 }"
              >
                <input
                  type="radio"
                  name="uiScale"
                  :checked="localSettings.uiScale === 100"
                  @change="updateSetting('uiScale', 100)"
                >
                <span class="radio-label">Normal</span>
              </label>
              <label
                class="radio-option"
                :class="{ active: localSettings.uiScale === 125 }"
              >
                <input
                  type="radio"
                  name="uiScale"
                  :checked="localSettings.uiScale === 125"
                  @change="updateSetting('uiScale', 125)"
                >
                <span class="radio-label">Large</span>
              </label>
              <label
                class="radio-option"
                :class="{ active: localSettings.uiScale === 150 }"
              >
                <input
                  type="radio"
                  name="uiScale"
                  :checked="localSettings.uiScale === 150"
                  @change="updateSetting('uiScale', 150)"
                >
                <span class="radio-label">Extra Large</span>
              </label>
            </div>
          </div>

          <!-- Pronunciation Speed -->
          <div class="setting-item">
            <label class="setting-label-standalone">Pronunciation Speed</label>
            <div class="radio-group speed-options">
              <label
                class="radio-option"
                :class="{ active: localSettings.audioSpeed === 1.0 }"
              >
                <input
                  type="radio"
                  name="audioSpeed"
                  :checked="localSettings.audioSpeed === 1.0"
                  @change="updateSetting('audioSpeed', 1.0)"
                >
                <span class="speed-icon">🐇</span>
                <span class="radio-label">Normal</span>
              </label>
              <label
                class="radio-option"
                :class="{ active: localSettings.audioSpeed === 0.75 }"
              >
                <input
                  type="radio"
                  name="audioSpeed"
                  :checked="localSettings.audioSpeed === 0.75"
                  @change="updateSetting('audioSpeed', 0.75)"
                >
                <span class="speed-icon">🐢</span>
                <span class="radio-label">Slow</span>
              </label>
              <label
                class="radio-option"
                :class="{ active: localSettings.audioSpeed === 0.5 }"
              >
                <input
                  type="radio"
                  name="audioSpeed"
                  :checked="localSettings.audioSpeed === 0.5"
                  @change="updateSetting('audioSpeed', 0.5)"
                >
                <span class="speed-icon">🐌</span>
                <span class="radio-label">Very Slow</span>
              </label>
            </div>
          </div>

          <!-- Color Blind Mode -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.colorBlindMode"
                @change="updateSetting('colorBlindMode', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">Color Blind Mode</span>
            </label>
            <p class="setting-description">
              Add shapes to start/end zones in addition to colors
            </p>
          </div>

          <!-- Show Audio Captions -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.enableCaptions"
                @change="updateSetting('enableCaptions', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">Show Audio Captions</span>
            </label>
            <p class="setting-description">
              Display text when pronunciation plays
            </p>
          </div>
        </div>

        <div class="setting-section">
          <h3 class="setting-section-title">
            Game Options
          </h3>

          <!-- Best of 3 Mode -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.enableBestOf3"
                @change="updateSetting('enableBestOf3', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">Enable Best of 3 Mode</span>
            </label>
          </div>

          <!-- Trace Mode -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.enableTraceMode"
                @change="updateSetting('enableTraceMode', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">Enable Trace Mode</span>
            </label>
            <div v-if="localSettings.enableTraceMode" class="nested-setting">
              <label class="setting-toggle">
                <input
                  type="checkbox"
                  :checked="localSettings.traceModeDefault"
                  @change="updateSetting('traceModeDefault', $event.target.checked)"
                >
                <span class="toggle-slider" />
                <span class="setting-label">Trace on by default</span>
              </label>
            </div>
          </div>

          <!-- Step-by-Step Mode -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.enableStepByStep"
                @change="updateSetting('enableStepByStep', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">Enable Step-by-Step Mode</span>
            </label>
            <p class="setting-description">
              Practice drawing each stroke one at a time with visual guides
            </p>
            <div v-if="localSettings.enableStepByStep" class="nested-setting">
              <label class="setting-toggle">
                <input
                  type="checkbox"
                  :checked="localSettings.stepByStepDefault"
                  @change="updateSetting('stepByStepDefault', $event.target.checked)"
                >
                <span class="toggle-slider" />
                <span class="setting-label">Step-by-Step on by default</span>
              </label>
            </div>
          </div>

          <!-- Audio Settings -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.autoPlaySound"
                @change="updateSetting('autoPlaySound', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">Auto-play pronunciation</span>
            </label>
          </div>

          <!-- Voice Selection -->
          <div class="setting-item">
            <label class="setting-label-standalone">Voice</label>
            <div class="voice-options">
              <label class="voice-option" :class="{ active: localSettings.voiceGender === 'rachel' }">
                <input
                  type="radio"
                  name="voiceGender"
                  value="rachel"
                  :checked="localSettings.voiceGender === 'rachel'"
                  @change="updateSetting('voiceGender', 'rachel')"
                >
                <span class="voice-icon">👩</span>
                <span class="voice-name">Rachel</span>
                <span class="voice-desc">Calm</span>
              </label>
              <label class="voice-option" :class="{ active: localSettings.voiceGender === 'sarah' }">
                <input
                  type="radio"
                  name="voiceGender"
                  value="sarah"
                  :checked="localSettings.voiceGender === 'sarah'"
                  @change="updateSetting('voiceGender', 'sarah')"
                >
                <span class="voice-icon">👩</span>
                <span class="voice-name">Sarah</span>
                <span class="voice-desc">Friendly</span>
              </label>
              <label class="voice-option" :class="{ active: localSettings.voiceGender === 'adam' }">
                <input
                  type="radio"
                  name="voiceGender"
                  value="adam"
                  :checked="localSettings.voiceGender === 'adam'"
                  @change="updateSetting('voiceGender', 'adam')"
                >
                <span class="voice-icon">👨</span>
                <span class="voice-name">Adam</span>
                <span class="voice-desc">Deep</span>
              </label>
              <label class="voice-option" :class="{ active: localSettings.voiceGender === 'josh' }">
                <input
                  type="radio"
                  name="voiceGender"
                  value="josh"
                  :checked="localSettings.voiceGender === 'josh'"
                  @change="updateSetting('voiceGender', 'josh')"
                >
                <span class="voice-icon">👨</span>
                <span class="voice-name">Josh</span>
                <span class="voice-desc">Young</span>
              </label>
            </div>
            <button class="preview-voice-button" @click="previewVoice">
              Preview Voice
            </button>
          </div>

          <!-- Font Selection -->
          <div class="setting-item font-section">
            <label class="setting-label-standalone">Font Style</label>
            <p class="font-section-description">
              Choose a handwriting style that matches your classroom curriculum
            </p>

            <div class="font-options">
              <label
                v-for="font in fontsDetailed"
                :key="font.name"
                class="font-option"
                :class="{ active: localSettings.selectedFont === font.name }"
              >
                <input
                  type="radio"
                  name="selectedFont"
                  :value="font.name"
                  :checked="localSettings.selectedFont === font.name"
                  @change="updateSetting('selectedFont', font.name)"
                >
                <div class="font-option-content">
                  <div class="font-option-header">
                    <span class="font-display-name">{{ font.display_name }}</span>
                    <span class="font-style-tag">{{ font.style }}</span>
                  </div>
                  <p class="font-option-description">{{ font.description }}</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Debug Mode -->
          <div class="setting-item">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.enableDebugMode"
                @change="updateSetting('enableDebugMode', $event.target.checked)"
              >
              <span class="toggle-slider" />
              <span class="setting-label">Enable Debug Mode</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { playCharacterAudio } from '@/services/audio'

export default {
  name: 'SettingsPanel',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'update:settings'],
  setup(props, { emit }) {
    const localSettings = ref({ ...props.settings })

    const fontsDetailed = ref([
      {
        name: 'Fredoka-Regular',
        display_name: 'Fredoka',
        style: 'Rounded Playful',
        description: 'Bubbly round letters with a playful feel.'
      },
      {
        name: 'Nunito-Regular',
        display_name: 'Nunito',
        style: 'Clean Sans-serif',
        description: 'Modern clean letters, easy to read.'
      },
      {
        name: 'PlaywriteUS-Regular',
        display_name: 'Playwrite US',
        style: 'Educational',
        description: 'Traditional manuscript style used in schools.'
      },
      {
        name: 'PatrickHand-Regular',
        display_name: 'Patrick Hand',
        style: 'Casual Handwriting',
        description: 'Natural handwritten appearance.'
      },
      {
        name: 'Schoolbell-Regular',
        display_name: 'Schoolbell',
        style: 'Playful Handwriting',
        description: 'Fun childlike handwriting style.'
      }
    ])

    watch(() => props.settings, (newVal) => {
      localSettings.value = { ...newVal }
    }, { deep: true })

    const updateSetting = (key, value) => {
      localSettings.value[key] = value

      if (key === 'traceModeDefault' && value === true) {
        localSettings.value.stepByStepDefault = false
      } else if (key === 'stepByStepDefault' && value === true) {
        localSettings.value.traceModeDefault = false
      }

      emit('update:settings', { ...localSettings.value })
    }

    const previewVoice = async () => {
      try {
        await playCharacterAudio('A', localSettings.value.voiceGender, localSettings.value.audioSpeed)
      } catch (error) {
        console.error('Failed to play voice preview:', error)
      }
    }

    return {
      localSettings,
      fontsDetailed,
      updateSetting,
      previewVoice
    }
  }
}
</script>

<style scoped>
.settings-overlay {
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

.settings-panel {
  width: 350px;
  max-width: 90vw;
  background: white;
  height: 100%;
  box-shadow: -5px 0 20px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.settings-header h2 {
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

.close-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.storage-info {
  margin: 0;
  padding: 12px;
  background: rgba(78, 205, 196, 0.1);
  border-radius: 10px;
  color: #4ECDC4;
  font-size: 0.9rem;
  line-height: 1.4;
}

.setting-item {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.setting-toggle input {
  display: none;
}

.toggle-slider {
  width: 48px;
  height: 26px;
  background: #ccc;
  border-radius: 13px;
  position: relative;
  transition: background 0.3s;
  flex-shrink: 0;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.setting-toggle input:checked + .toggle-slider {
  background: #4ECDC4;
}

.setting-toggle input:checked + .toggle-slider::after {
  transform: translateX(22px);
}

.setting-label {
  font-size: 1rem;
  color: #333;
}

.setting-label-standalone {
  display: block;
  font-size: 1rem;
  color: #333;
  margin-bottom: 10px;
  font-weight: 600;
}

.nested-setting {
  margin-top: 15px;
  margin-left: 20px;
  padding-left: 20px;
  border-left: 2px solid #eee;
}

.setting-description {
  margin: 8px 0 0 0;
  padding-left: 60px;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.4;
}

.setting-section {
  margin-bottom: 25px;
}

.setting-section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #764ba2;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(118, 75, 162, 0.2);
}

.radio-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.radio-option {
  flex: 1;
  min-width: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  border: 2px solid #ddd;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.radio-option input {
  display: none;
}

.radio-option:hover {
  border-color: #4ECDC4;
  background: rgba(78, 205, 196, 0.05);
}

.radio-option.active {
  border-color: #4ECDC4;
  background: rgba(78, 205, 196, 0.15);
}

.radio-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #333;
}

.speed-options .radio-option {
  padding: 12px 8px;
}

.speed-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.voice-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}

.voice-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 2px solid #ddd;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.voice-option input {
  display: none;
}

.voice-option:hover {
  border-color: #4ECDC4;
}

.voice-option.active {
  border-color: #4ECDC4;
  background: rgba(78, 205, 196, 0.1);
}

.voice-icon {
  font-size: 1.5rem;
  margin-bottom: 3px;
}

.voice-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #333;
}

.voice-desc {
  font-size: 0.7rem;
  color: #888;
  margin-top: 2px;
}

.preview-voice-button {
  width: 100%;
  background: #4ECDC4;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.preview-voice-button:hover {
  background: #3dbdb5;
}

.font-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.font-section-description {
  margin: 0 0 8px 0;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.4;
}

.font-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.font-option {
  display: block;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.font-option input {
  display: none;
}

.font-option:hover {
  border-color: #4ECDC4;
  background: rgba(78, 205, 196, 0.05);
}

.font-option.active {
  border-color: #4ECDC4;
  background: rgba(78, 205, 196, 0.1);
}

.font-option-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.font-option-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.font-display-name {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.font-style-tag {
  font-size: 0.7rem;
  font-weight: 500;
  color: #764ba2;
  background: rgba(118, 75, 162, 0.1);
  padding: 3px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.font-option-description {
  margin: 0;
  font-size: 0.8rem;
  color: #666;
  line-height: 1.3;
}

@media (max-width: 600px) {
  .settings-panel {
    width: 100%;
    max-width: 100%;
  }

  .radio-group {
    gap: 6px;
  }

  .radio-option {
    min-width: 70px;
    padding: 8px 6px;
  }

  .radio-label {
    font-size: 0.75rem;
  }
}
</style>
