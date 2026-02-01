<template>
  <div class="drawing-container">
    <!-- Player Turn Indicator (Multiplayer) -->
    <div v-if="playerName" class="player-turn-indicator">
      <span class="player-badge">Player {{ playerNumber }}/{{ totalPlayers }}</span>
      <span class="player-name-display">{{ playerName }}'s Turn</span>
    </div>

    <!-- Character Display -->
    <div class="character-display">
      <span
        class="character-letter"
        :style="{ fontFamily: fontFamily }"
      >
        {{ character }}
      </span>
      <button class="speak-btn" :aria-label="`Play pronunciation of ${character}`" @click="$emit('play-audio', character)">
        <span class="speaker-icon" aria-hidden="true">🔊</span>
      </button>
    </div>

    <!-- High Score Display -->
    <div v-if="highScoreForMode !== null && !isMultiplayer" class="high-score-badge">
      Best: {{ highScoreForMode }}%
    </div>

    <!-- Drawing Area -->
    <div class="canvas-wrapper">
      <canvas
        ref="canvas"
        class="drawing-canvas"
        :class="{ 'high-contrast': highContrastMode }"
        @touchstart.prevent="startDrawing"
        @touchmove.prevent="draw"
        @touchend.prevent="stopDrawing"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
      />

      <!-- Trace overlay -->
      <div
        v-if="dashTracingMode && traceImage"
        class="trace-overlay"
      >
        <img :src="traceImage" alt="Trace guide" />
      </div>

      <!-- Guided Mode Stroke Guide -->
      <svg
        v-if="guidedMode && currentStrokeData && !isCurrentStrokeComplete"
        class="stroke-guide-overlay"
        viewBox="0 0 400 400"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- Current stroke path (animated dash) -->
        <path
          v-if="currentStrokePath"
          :d="currentStrokePath"
          class="stroke-guide-path animated"
          fill="none"
          stroke-width="20"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <!-- Start zone circle -->
        <circle
          v-if="currentStrokeData.points && currentStrokeData.points.length > 0"
          :cx="currentStrokeData.points[0][0] * 4"
          :cy="currentStrokeData.points[0][1] * 4"
          :r="strokeTolerance * 40"
          class="stroke-zone start-zone"
          :class="{ 'active': strokeState === 'waiting', 'color-blind': colorBlindMode }"
        />

        <!-- End zone circle -->
        <circle
          v-if="currentStrokeData.points && currentStrokeData.points.length > 1"
          :cx="currentStrokeData.points[currentStrokeData.points.length - 1][0] * 4"
          :cy="currentStrokeData.points[currentStrokeData.points.length - 1][1] * 4"
          :r="strokeTolerance * 40"
          class="stroke-zone end-zone"
          :class="{ 'approaching': strokeState === 'drawing', 'color-blind': colorBlindMode }"
        />

        <!-- Color blind mode shapes -->
        <g v-if="colorBlindMode && currentStrokeData.points && currentStrokeData.points.length > 0">
          <!-- Triangle for start -->
          <polygon
            :points="getTrianglePoints(currentStrokeData.points[0][0] * 4, currentStrokeData.points[0][1] * 4, strokeTolerance * 25)"
            class="color-blind-shape start-shape"
          />
          <!-- Square for end -->
          <rect
            v-if="currentStrokeData.points.length > 1"
            :x="currentStrokeData.points[currentStrokeData.points.length - 1][0] * 4 - strokeTolerance * 18"
            :y="currentStrokeData.points[currentStrokeData.points.length - 1][1] * 4 - strokeTolerance * 18"
            :width="strokeTolerance * 36"
            :height="strokeTolerance * 36"
            class="color-blind-shape end-shape"
          />
        </g>
      </svg>
    </div>

    <!-- Attempt Counter for Best of 3 -->
    <div v-if="bestOf3Mode && !guidedMode" class="attempt-indicator">
      <span class="attempt-text">Attempt</span>
      <div class="attempt-dots">
        <span
          v-for="i in 3"
          :key="i"
          class="attempt-dot"
          :class="{ active: i <= currentAttempt, current: i === currentAttempt }"
        />
      </div>
    </div>

    <!-- Guided Mode Progress -->
    <div v-if="guidedMode && strokeData.length > 0" class="guided-progress">
      <div class="progress-label">Stroke {{ Math.min(currentStrokeStep + 1, strokeData.length) }} of {{ strokeData.length }}</div>
      <div class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: `${(currentStrokeStep / strokeData.length) * 100}%` }"
        />
      </div>
      <button
        v-if="currentStrokeStep > 0"
        class="reset-guided-btn"
        @click="$emit('reset-guided-progress')"
      >
        Start Over
      </button>
    </div>

    <!-- Control Buttons -->
    <div class="control-buttons">
      <button class="control-btn clear-btn" aria-label="Clear drawing" @click="clearCanvas">
        <span class="btn-icon" aria-hidden="true">🗑️</span>
        <span>Clear</span>
      </button>

      <button
        v-if="showTraceButton && !guidedMode"
        class="control-btn trace-btn"
        :class="{ active: dashTracingMode }"
        aria-label="Toggle trace mode"
        @click="$emit('toggle-dash-tracing')"
      >
        <span class="btn-icon" aria-hidden="true">✏️</span>
        <span>{{ dashTracingMode ? 'Trace On' : 'Trace Off' }}</span>
      </button>

      <button
        v-if="showStepByStepButton && !dashTracingMode"
        class="control-btn guided-btn"
        :class="{ active: guidedMode }"
        aria-label="Toggle step-by-step mode"
        @click="$emit('toggle-guided')"
      >
        <span class="btn-icon" aria-hidden="true">👆</span>
        <span>{{ guidedMode ? 'Guided On' : 'Step-by-Step' }}</span>
      </button>

      <button
        v-if="showBestOf3Button && !guidedMode"
        class="control-btn bestof3-btn"
        :class="{ active: bestOf3Mode }"
        aria-label="Toggle best of 3 mode"
        @click="$emit('toggle-best-of-3')"
      >
        <span class="btn-icon" aria-hidden="true">🎯</span>
        <span>{{ bestOf3Mode ? 'Best of 3 On' : 'Best of 3' }}</span>
      </button>

      <button
        v-if="showDebugButton && !guidedMode"
        class="control-btn debug-btn"
        :class="{ active: showDebugMode }"
        aria-label="Toggle debug mode"
        @click="$emit('toggle-debug-mode')"
      >
        <span class="btn-icon" aria-hidden="true">🔬</span>
        <span>Debug</span>
      </button>
    </div>

    <!-- Submit Button -->
    <button
      class="submit-btn"
      :disabled="isSubmitting"
      aria-label="Submit drawing"
      @click="submitDrawing"
    >
      <span v-if="isSubmitting">Checking...</span>
      <span v-else-if="guidedMode && currentStrokeStep < strokeData.length">Complete All Strokes First</span>
      <span v-else>
        <span class="btn-icon" aria-hidden="true">✅</span>
        Check My Work!
      </span>
    </button>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { scoreDrawing, getReferenceImage } from '@/services/scoring'

export default {
  name: 'DrawingCanvas',
  props: {
    character: {
      type: String,
      required: true
    },
    dashTracingMode: {
      type: Boolean,
      default: false
    },
    currentAttempt: {
      type: Number,
      default: 1
    },
    bestOf3Mode: {
      type: Boolean,
      default: false
    },
    attempts: {
      type: Array,
      default: () => []
    },
    showDebugMode: {
      type: Boolean,
      default: false
    },
    showTraceButton: {
      type: Boolean,
      default: true
    },
    showBestOf3Button: {
      type: Boolean,
      default: true
    },
    showDebugButton: {
      type: Boolean,
      default: false
    },
    showStepByStepButton: {
      type: Boolean,
      default: true
    },
    selectedFont: {
      type: String,
      default: 'Fredoka-Regular'
    },
    guidedMode: {
      type: Boolean,
      default: false
    },
    currentStrokeStep: {
      type: Number,
      default: 0
    },
    highContrastMode: {
      type: Boolean,
      default: false
    },
    playerName: {
      type: String,
      default: null
    },
    playerNumber: {
      type: Number,
      default: 1
    },
    totalPlayers: {
      type: Number,
      default: 1
    },
    strokeTolerance: {
      type: Number,
      default: 0.5
    },
    colorBlindMode: {
      type: Boolean,
      default: false
    },
    highScoreForMode: {
      type: Number,
      default: null
    },
    isMultiplayer: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'submit',
    'toggle-dash-tracing',
    'toggle-best-of-3',
    'toggle-debug-mode',
    'toggle-guided',
    'stroke-completed',
    'reset-guided-progress',
    'guided-complete',
    'play-audio'
  ],
  setup(props, { emit }) {
    const canvas = ref(null)
    const ctx = ref(null)
    const isDrawing = ref(false)
    const isSubmitting = ref(false)
    const lastX = ref(0)
    const lastY = ref(0)
    const traceImage = ref(null)
    const strokeData = ref([])
    const strokeState = ref('waiting')
    const hasDrawnOnCanvas = ref(false)

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

    const currentStrokeData = computed(() => {
      if (!props.guidedMode || strokeData.value.length === 0) return null
      return strokeData.value[props.currentStrokeStep] || null
    })

    const currentStrokePath = computed(() => {
      if (!currentStrokeData.value || !currentStrokeData.value.points) return ''
      const points = currentStrokeData.value.points
      if (points.length < 2) return ''

      let d = `M ${points[0][0] * 4} ${points[0][1] * 4}`
      for (let i = 1; i < points.length; i++) {
        d += ` L ${points[i][0] * 4} ${points[i][1] * 4}`
      }
      return d
    })

    const isCurrentStrokeComplete = computed(() => {
      return props.currentStrokeStep >= strokeData.value.length
    })

    const initCanvas = () => {
      if (!canvas.value) return

      const rect = canvas.value.getBoundingClientRect()
      canvas.value.width = rect.width * window.devicePixelRatio
      canvas.value.height = rect.height * window.devicePixelRatio

      ctx.value = canvas.value.getContext('2d')
      ctx.value.scale(window.devicePixelRatio, window.devicePixelRatio)

      ctx.value.lineCap = 'round'
      ctx.value.lineJoin = 'round'
      ctx.value.lineWidth = 8
      ctx.value.strokeStyle = props.highContrastMode ? '#000000' : '#333333'
    }

    const clearCanvas = () => {
      if (!ctx.value || !canvas.value) return

      const rect = canvas.value.getBoundingClientRect()
      ctx.value.clearRect(0, 0, rect.width, rect.height)
      hasDrawnOnCanvas.value = false
      strokeState.value = 'waiting'
    }

    const loadStrokeData = async () => {
      try {
        const response = await fetch(`/strokes/${props.selectedFont.toLowerCase().replace('-regular', '')}.json`)
        if (!response.ok) {
          // Fallback to fredoka
          const fallback = await fetch('/strokes/fredoka.json')
          if (fallback.ok) {
            const data = await fallback.json()
            strokeData.value = data[props.character]?.strokes || []
          }
          return
        }
        const data = await response.json()
        strokeData.value = data[props.character]?.strokes || []
      } catch (error) {
        console.error('Failed to load stroke data:', error)
        strokeData.value = []
      }
    }

    const loadTraceImage = async () => {
      try {
        traceImage.value = await getReferenceImage(props.character, props.selectedFont, 400)
      } catch (error) {
        console.error('Failed to load trace image:', error)
      }
    }

    const getEventPos = (e) => {
      const rect = canvas.value.getBoundingClientRect()
      if (e.touches && e.touches.length > 0) {
        return {
          x: e.touches[0].clientX - rect.left,
          y: e.touches[0].clientY - rect.top
        }
      }
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
    }

    const isInZone = (pos, zoneCenter, tolerance) => {
      const rect = canvas.value.getBoundingClientRect()
      const scale = rect.width / 100
      const zoneCenterScaled = {
        x: zoneCenter[0] * scale,
        y: zoneCenter[1] * scale
      }
      const radius = tolerance * scale
      const dist = Math.sqrt(
        Math.pow(pos.x - zoneCenterScaled.x, 2) +
        Math.pow(pos.y - zoneCenterScaled.y, 2)
      )
      return dist <= radius
    }

    const startDrawing = (e) => {
      const pos = getEventPos(e)

      if (props.guidedMode && currentStrokeData.value) {
        const startPoint = currentStrokeData.value.points[0]
        if (!isInZone(pos, startPoint, props.strokeTolerance * 40)) {
          return
        }
        strokeState.value = 'drawing'
      }

      isDrawing.value = true
      lastX.value = pos.x
      lastY.value = pos.y
      hasDrawnOnCanvas.value = true
    }

    const draw = (e) => {
      if (!isDrawing.value || !ctx.value) return

      const pos = getEventPos(e)

      ctx.value.beginPath()
      ctx.value.moveTo(lastX.value, lastY.value)
      ctx.value.lineTo(pos.x, pos.y)
      ctx.value.stroke()

      lastX.value = pos.x
      lastY.value = pos.y
    }

    const stopDrawing = (e) => {
      if (!isDrawing.value) return

      if (props.guidedMode && currentStrokeData.value && strokeState.value === 'drawing') {
        const pos = e ? getEventPos(e) : { x: lastX.value, y: lastY.value }
        const endPoint = currentStrokeData.value.points[currentStrokeData.value.points.length - 1]

        if (isInZone(pos, endPoint, props.strokeTolerance * 40)) {
          emit('stroke-completed', props.currentStrokeStep)

          if (props.currentStrokeStep + 1 >= strokeData.value.length) {
            emit('guided-complete')
          }
        }

        strokeState.value = 'waiting'
      }

      isDrawing.value = false
    }

    const getTrianglePoints = (cx, cy, size) => {
      const h = size * Math.sqrt(3) / 2
      return `${cx},${cy - h * 2/3} ${cx - size/2},${cy + h/3} ${cx + size/2},${cy + h/3}`
    }

    const submitDrawing = async () => {
      if (isSubmitting.value) return
      if (props.guidedMode && props.currentStrokeStep < strokeData.value.length) return
      if (!hasDrawnOnCanvas.value) {
        alert('Please draw something first!')
        return
      }

      isSubmitting.value = true

      try {
        const imageData = canvas.value.toDataURL('image/png')
        const result = await scoreDrawing(canvas.value, props.character, props.selectedFont)

        emit('submit', {
          imageData,
          scoreResult: {
            score: result.score,
            stars: result.stars,
            feedback: result.feedback,
            reference_image: result.referenceImage,
            details: {
              coverage: result.coverage,
              accuracy: result.accuracy,
              similarity: result.similarity
            }
          }
        })
      } catch (error) {
        console.error('Scoring failed:', error)
        alert('Scoring failed. Please try again.')
      } finally {
        isSubmitting.value = false
      }
    }

    onMounted(() => {
      nextTick(() => {
        initCanvas()
        loadTraceImage()
        loadStrokeData()
      })
    })

    watch(() => props.character, () => {
      nextTick(() => {
        clearCanvas()
        loadTraceImage()
        loadStrokeData()
      })
    })

    watch(() => props.currentAttempt, () => {
      nextTick(() => {
        clearCanvas()
      })
    })

    watch(() => props.selectedFont, () => {
      loadTraceImage()
      loadStrokeData()
    })

    watch(() => props.guidedMode, (newVal) => {
      if (newVal) {
        clearCanvas()
        strokeState.value = 'waiting'
      }
    })

    watch(() => props.currentStrokeStep, () => {
      strokeState.value = 'waiting'
    })

    watch(() => props.highContrastMode, () => {
      if (ctx.value) {
        ctx.value.strokeStyle = props.highContrastMode ? '#000000' : '#333333'
      }
    })

    return {
      canvas,
      isSubmitting,
      traceImage,
      strokeData,
      currentStrokeData,
      currentStrokePath,
      isCurrentStrokeComplete,
      strokeState,
      fontFamily,
      startDrawing,
      draw,
      stopDrawing,
      clearCanvas,
      submitDrawing,
      getTrianglePoints
    }
  }
}
</script>

<style scoped>
.drawing-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 15px;
  gap: 15px;
}

.player-turn-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(255, 215, 0, 0.2);
  border: 2px solid #FFD700;
  border-radius: 15px;
  padding: 10px 20px;
}

.player-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.player-name-display {
  color: white;
  font-size: 1.2rem;
  font-weight: 700;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

.character-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.character-letter {
  font-size: 4rem;
  font-weight: 700;
  color: white;
  text-shadow: 3px 3px 0 rgba(0, 0, 0, 0.2);
}

.speak-btn {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: white;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
  transition: transform 0.2s;
}

.speak-btn:hover {
  transform: scale(1.1);
}

.high-score-badge {
  background: rgba(78, 205, 196, 0.2);
  border: 2px solid #4ECDC4;
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  text-align: center;
  align-self: center;
}

.canvas-wrapper {
  flex: 1;
  position: relative;
  background: white;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  min-height: 200px;
}

.drawing-canvas {
  width: 100%;
  height: 100%;
  touch-action: none;
  cursor: crosshair;
}

.drawing-canvas.high-contrast {
  background: #ffffff;
  border: 3px solid #000000;
}

.trace-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0.3;
}

.trace-overlay img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.stroke-guide-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.stroke-guide-path {
  stroke: rgba(78, 205, 196, 0.6);
}

.stroke-guide-path.animated {
  stroke-dasharray: 20 10;
  animation: dash 1s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -30;
  }
}

.stroke-zone {
  fill: rgba(255, 255, 255, 0.8);
  stroke-width: 3;
  transition: all 0.3s ease;
}

.stroke-zone.start-zone {
  stroke: #4ECDC4;
  fill: rgba(78, 205, 196, 0.3);
}

.stroke-zone.start-zone.active {
  fill: rgba(78, 205, 196, 0.5);
  animation: pulse 1s ease-in-out infinite;
}

.stroke-zone.end-zone {
  stroke: #FF6B6B;
  fill: rgba(255, 107, 107, 0.2);
}

.stroke-zone.end-zone.approaching {
  fill: rgba(255, 107, 107, 0.4);
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.color-blind-shape {
  fill: none;
  stroke-width: 3;
  opacity: 0.8;
}

.color-blind-shape.start-shape {
  stroke: #4ECDC4;
}

.color-blind-shape.end-shape {
  stroke: #FF6B6B;
}

.attempt-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.attempt-text {
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
}

.attempt-dots {
  display: flex;
  gap: 8px;
}

.attempt-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: all 0.3s;
}

.attempt-dot.active {
  background: #4ECDC4;
}

.attempt-dot.current {
  box-shadow: 0 0 10px #4ECDC4;
  animation: dotPulse 1s ease-in-out infinite;
}

@keyframes dotPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.guided-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.progress-label {
  color: white;
  font-size: 0.9rem;
  font-weight: 500;
}

.progress-bar {
  width: 200px;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ECDC4, #44B09E);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.reset-guided-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 6px 16px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 500;
  transition: background 0.2s;
}

.reset-guided-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.control-buttons {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.control-btn.active {
  background: white;
  color: #764ba2;
}

.btn-icon {
  font-size: 1.1rem;
}

.submit-btn {
  background: linear-gradient(135deg, #4ECDC4 0%, #44B09E 100%);
  color: white;
  padding: 18px 40px;
  border-radius: 30px;
  font-size: 1.3rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 6px 25px rgba(78, 205, 196, 0.4);
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: scale(1.02);
  box-shadow: 0 8px 30px rgba(78, 205, 196, 0.5);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .drawing-container {
    padding: 10px;
    gap: 10px;
  }

  .character-letter {
    font-size: 3rem;
  }

  .speak-btn {
    width: 40px;
    height: 40px;
    font-size: 1.2rem;
  }

  .control-buttons {
    gap: 6px;
  }

  .control-btn {
    padding: 8px 12px;
    font-size: 0.8rem;
  }

  .submit-btn {
    padding: 15px 30px;
    font-size: 1.1rem;
  }
}
</style>
