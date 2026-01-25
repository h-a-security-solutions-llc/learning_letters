<template>
  <div class="settings-overlay" @click.self="$emit('close')">
    <div class="settings-panel">
      <div class="settings-header">
        <h2>Settings</h2>
        <button class="close-button" @click="$emit('close')">×</button>
      </div>

      <div class="settings-content">
        <!-- Best of 3 Mode -->
        <div class="setting-item">
          <label class="setting-toggle">
            <input
              type="checkbox"
              :checked="localSettings.enableBestOf3"
              @change="updateSetting('enableBestOf3', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
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
            />
            <span class="toggle-slider"></span>
            <span class="setting-label">Enable Trace Mode</span>
          </label>
          <div v-if="localSettings.enableTraceMode" class="nested-setting">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.traceModeDefault"
                @change="updateSetting('traceModeDefault', $event.target.checked)"
              />
              <span class="toggle-slider"></span>
              <span class="setting-label">Trace on by default</span>
            </label>
          </div>
        </div>

        <!-- Guide Mode -->
        <div class="setting-item">
          <label class="setting-toggle">
            <input
              type="checkbox"
              :checked="localSettings.enableGuideMode"
              @change="updateSetting('enableGuideMode', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
            <span class="setting-label">Enable Guide Mode</span>
          </label>
          <div v-if="localSettings.enableGuideMode" class="nested-setting">
            <label class="setting-toggle">
              <input
                type="checkbox"
                :checked="localSettings.guideModeDefault"
                @change="updateSetting('guideModeDefault', $event.target.checked)"
              />
              <span class="toggle-slider"></span>
              <span class="setting-label">Guide on by default</span>
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
            />
            <span class="toggle-slider"></span>
            <span class="setting-label">Enable Debug Mode</span>
          </label>
        </div>

        <!-- Step-by-Step Mode -->
        <div class="setting-item">
          <label class="setting-toggle">
            <input
              type="checkbox"
              :checked="localSettings.enableStepByStep"
              @change="updateSetting('enableStepByStep', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
            <span class="setting-label">Enable Step-by-Step Mode</span>
          </label>
          <p class="setting-description">
            Practice drawing each stroke one at a time with visual guides
          </p>
        </div>

        <!-- Audio Settings -->
        <div class="setting-item">
          <label class="setting-toggle">
            <input
              type="checkbox"
              :checked="localSettings.autoPlaySound"
              @change="updateSetting('autoPlaySound', $event.target.checked)"
            />
            <span class="toggle-slider"></span>
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
              />
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
              />
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
              />
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
              />
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
          <label class="setting-label-standalone">Font</label>
          <select
            class="font-select"
            :value="localSettings.selectedFont"
            @change="updateSetting('selectedFont', $event.target.value)"
          >
            <option v-for="font in availableFonts" :key="font" :value="font">
              {{ font }}
            </option>
          </select>
          <button class="preview-button" @click="showFontPreview">
            Show Letters
          </button>
        </div>
      </div>
    </div>

    <!-- Font Preview Modal -->
    <div v-if="fontPreviewVisible" class="preview-modal" @click.self="fontPreviewVisible = false">
      <div class="preview-content">
        <div class="preview-header">
          <h3>{{ localSettings.selectedFont }}</h3>
          <button class="close-button" @click="fontPreviewVisible = false">×</button>
        </div>
        <div v-if="fontPreviewLoading" class="preview-loading">Loading preview...</div>
        <img
          v-else-if="fontPreviewImage"
          :src="fontPreviewImage"
          alt="Font preview"
          class="preview-image"
        />
        <div v-else class="preview-error">Failed to load preview</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

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
    const availableFonts = ref(['Fredoka-Regular'])
    const fontPreviewVisible = ref(false)
    const fontPreviewImage = ref(null)
    const fontPreviewLoading = ref(false)

    // Watch for external settings changes
    watch(() => props.settings, (newVal) => {
      localSettings.value = { ...newVal }
    }, { deep: true })

    const updateSetting = (key, value) => {
      localSettings.value[key] = value
      emit('update:settings', { ...localSettings.value })
    }

    const fetchFonts = async () => {
      try {
        const response = await axios.get('/api/fonts')
        if (response.data.fonts && response.data.fonts.length > 0) {
          availableFonts.value = response.data.fonts
        }
      } catch (error) {
        console.error('Failed to fetch fonts:', error)
      }
    }

    const showFontPreview = async () => {
      fontPreviewVisible.value = true
      fontPreviewLoading.value = true
      fontPreviewImage.value = null

      try {
        const response = await axios.get(`/api/fonts/${encodeURIComponent(localSettings.value.selectedFont)}/preview`)
        fontPreviewImage.value = response.data.preview
      } catch (error) {
        console.error('Failed to load font preview:', error)
      } finally {
        fontPreviewLoading.value = false
      }
    }

    const previewVoice = async () => {
      try {
        // Play a sample letter pronunciation with selected voice
        const audio = new Audio(`/api/audio/A?voice=${localSettings.value.voiceGender}`)
        await audio.play()
      } catch (error) {
        console.error('Failed to play voice preview:', error)
      }
    }

    onMounted(fetchFonts)

    return {
      localSettings,
      availableFonts,
      fontPreviewVisible,
      fontPreviewImage,
      fontPreviewLoading,
      updateSetting,
      showFontPreview,
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

.font-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.font-select {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
}

.font-select:focus {
  border-color: #4ECDC4;
  outline: none;
}

.preview-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.preview-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Voice Options */
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

/* Font Preview Modal */
.preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.preview-content {
  background: white;
  border-radius: 16px;
  max-width: 650px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.preview-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.preview-image {
  width: 100%;
  height: auto;
  display: block;
}

.preview-loading,
.preview-error {
  padding: 40px;
  text-align: center;
  color: #666;
  font-size: 1rem;
}

@media (max-width: 600px) {
  .settings-panel {
    width: 100%;
    max-width: 100%;
  }
}
</style>
