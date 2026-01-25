<template>
  <div class="drawing-container">
    <!-- Character Display -->
    <div class="character-display">
      <span class="current-char">{{ character }}</span>
      <button
        class="play-sound-btn"
        title="Play pronunciation"
        :aria-label="`Play pronunciation of ${character}`"
        @click="playAudio"
      >
        <span class="play-icon" aria-hidden="true">🔊</span>
      </button>
      <div class="char-info-container">
        <!-- Player Turn Indicator (Multiplayer) - replaces default prompt -->
        <template v-if="playerName">
          <span class="char-info player-turn">{{ playerName }}'s Turn</span>
          <span class="turn-progress">({{ playerNumber }} of {{ totalPlayers }})</span>
        </template>
        <template v-else>
          <span class="char-info">Draw this {{ charType }}!</span>
        </template>
        <!-- High Score Display (when logged in and has previous score) -->
        <span v-if="highScoreForMode !== null && !playerName" class="high-score-display">
          High Score: {{ highScoreForMode }}
        </span>
        <span v-if="bestOf3Mode" class="attempt-indicator">
          Attempt {{ currentAttempt }} of 3
          <span class="attempt-dots">
            <span
              v-for="i in 3"
              :key="i"
              class="attempt-dot"
              :class="{ filled: i <= attempts.length, current: i === currentAttempt }"
            />
          </span>
        </span>
      </div>
    </div>

    <!-- Canvas Area -->
    <div ref="canvasWrapper" class="canvas-wrapper">
      <!-- Trace Image Overlay (dashed lines from font skeleton) -->
      <img
        v-if="showTraceOverlay"
        :src="generatedGuide.trace_image"
        class="trace-overlay"
        alt="Trace guide"
      >

      <!-- Guided Mode Layer (step-by-step instruction) -->
      <svg
        v-if="guidedMode && guidedStrokes"
        class="guided-layer"
        :class="{ 'high-contrast': highContrastMode }"
        :viewBox="`0 0 ${canvasSize} ${canvasSize}`"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- Completed strokes (dimmed) -->
        <polyline
          v-for="(stroke, index) in completedGuidedStrokes"
          :key="'completed-' + index"
          :points="stroke.points.map(p => p.join(',')).join(' ')"
          fill="none"
          :stroke="guidedColors.pathColor || stroke.color"
          stroke-width="4"
          stroke-linecap="round"
          stroke-linejoin="round"
          opacity="0.3"
        />

        <!-- Current stroke guide (if not complete) -->
        <g v-if="currentGuidedStroke && !isGuidedComplete">
          <!-- Dashed path showing where to draw -->
          <polyline
            :points="currentGuidedStroke.points.map(p => p.join(',')).join(' ')"
            fill="none"
            :stroke="guidedColors.pathColor || currentGuidedStroke.color"
            stroke-width="4"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-dasharray="10,8"
            class="guided-path"
          />

          <!-- Start zone - stable circle with glowing ring -->
          <!-- Outer ring shows acceptable start area -->
          <circle
            :cx="currentGuidedStroke.start_zone.x"
            :cy="currentGuidedStroke.start_zone.y"
            :r="currentGuidedStroke.start_zone.radius * displayMultiplier"
            :fill="guidedColors.startFill"
            :stroke="guidedColors.startStroke"
            stroke-width="2"
            stroke-dasharray="8,4"
            class="start-zone-ring"
          />
          <!-- Color blind mode: concentric rings pattern for start zone -->
          <circle
            v-if="showShapeIndicators"
            :cx="currentGuidedStroke.start_zone.x"
            :cy="currentGuidedStroke.start_zone.y"
            :r="currentGuidedStroke.start_zone.radius * displayMultiplier * 0.7"
            fill="none"
            :stroke="guidedColors.startStroke"
            stroke-width="2"
            opacity="0.6"
          />
          <circle
            v-if="showShapeIndicators"
            :cx="currentGuidedStroke.start_zone.x"
            :cy="currentGuidedStroke.start_zone.y"
            :r="currentGuidedStroke.start_zone.radius * displayMultiplier * 0.4"
            fill="none"
            :stroke="guidedColors.startStroke"
            stroke-width="2"
            opacity="0.6"
          />
          <!-- Center dot - the target to aim for (stays perfectly still) -->
          <circle
            :cx="currentGuidedStroke.start_zone.x"
            :cy="currentGuidedStroke.start_zone.y"
            r="14"
            :fill="guidedColors.startDotFill"
            class="start-zone-dot"
          />
          <!-- Stroke number -->
          <text
            :x="currentGuidedStroke.start_zone.x"
            :y="currentGuidedStroke.start_zone.y + 5"
            text-anchor="middle"
            :fill="guidedColors.startTextFill"
            font-size="14"
            font-weight="bold"
          >
            {{ currentGuidedStroke.order }}
          </text>

          <!-- End zone - circle showing acceptable area + arrow -->
          <circle
            :cx="currentGuidedStroke.end_zone.x"
            :cy="currentGuidedStroke.end_zone.y"
            :r="currentGuidedStroke.end_zone.radius * displayMultiplier"
            :fill="guidedColors.endFill"
            :stroke="guidedColors.endStroke"
            stroke-width="2"
            stroke-dasharray="8,4"
            class="end-zone-ring"
          />
          <!-- Color blind mode: diamond shape overlay for end zone -->
          <rect
            v-if="showShapeIndicators"
            :x="currentGuidedStroke.end_zone.x - currentGuidedStroke.end_zone.radius * displayMultiplier * 0.5"
            :y="currentGuidedStroke.end_zone.y - currentGuidedStroke.end_zone.radius * displayMultiplier * 0.5"
            :width="currentGuidedStroke.end_zone.radius * displayMultiplier"
            :height="currentGuidedStroke.end_zone.radius * displayMultiplier"
            :transform="`rotate(45 ${currentGuidedStroke.end_zone.x} ${currentGuidedStroke.end_zone.y})`"
            fill="none"
            :stroke="guidedColors.endStroke"
            stroke-width="2"
            opacity="0.7"
          />
          <polygon
            :points="getGuidedArrowPoints(currentGuidedStroke.points)"
            :fill="guidedColors.pathColor || currentGuidedStroke.color"
            class="end-arrow"
          />
        </g>

        <!-- Instruction text at bottom (hidden while drawing) -->
        <g v-if="currentGuidedStroke && !isGuidedComplete && !isDrawing">
          <rect
            :x="10"
            :y="canvasSize - 45"
            :width="canvasSize - 20"
            height="35"
            rx="8"
            :fill="guidedColors.instructionBg"
            :stroke="guidedColors.instructionStroke"
            stroke-width="2"
          />
          <text
            :x="canvasSize / 2"
            :y="canvasSize - 22"
            text-anchor="middle"
            :fill="guidedColors.instructionText"
            font-size="14"
            font-weight="500"
          >
            {{ currentGuidedStroke.instruction }}
          </text>
        </g>

        <!-- Completion message -->
        <g v-if="isGuidedComplete">
          <rect
            :x="canvasSize / 4"
            :y="canvasSize / 2 - 30"
            :width="canvasSize / 2"
            height="60"
            rx="12"
            :fill="guidedColors.completionBg"
            :stroke="guidedColors.completionStroke"
            stroke-width="2"
          />
          <text
            :x="canvasSize / 2"
            :y="canvasSize / 2 + 8"
            text-anchor="middle"
            :fill="guidedColors.completionText"
            font-size="20"
            font-weight="bold"
          >
            Great job!
          </text>
        </g>

        <!-- Feedback message -->
        <g v-if="strokeFeedback">
          <rect
            :x="canvasSize / 4"
            :y="canvasSize / 2 - 25"
            :width="canvasSize / 2"
            height="50"
            rx="10"
            :fill="strokeFeedback.valid ? guidedColors.feedbackValidBg : guidedColors.feedbackInvalidBg"
            :stroke="strokeFeedback.valid ? guidedColors.feedbackValidStroke : guidedColors.feedbackInvalidStroke"
            stroke-width="2"
          />
          <text
            :x="canvasSize / 2"
            :y="canvasSize / 2 + 6"
            text-anchor="middle"
            :fill="strokeFeedback.valid ? guidedColors.feedbackValidText : guidedColors.feedbackInvalidText"
            font-size="16"
            font-weight="600"
          >
            {{ strokeFeedback.feedback }}
          </text>
        </g>
      </svg>

      <!-- Guided Mode Progress Indicator -->
      <div v-if="guidedMode && guidedStrokes" class="guided-progress">
        <span class="progress-text">Stroke {{ currentStrokeStep + 1 }} of {{ guidedStrokes.total_strokes }}</span>
        <div class="progress-dots">
          <span
            v-for="i in guidedStrokes.total_strokes"
            :key="i"
            class="progress-dot"
            :class="{
              completed: i <= currentStrokeStep,
              current: i === currentStrokeStep + 1
            }"
          />
        </div>
      </div>

      <!-- Drawing Canvas -->
      <canvas
        ref="canvas"
        class="drawing-canvas"
        role="img"
        :aria-label="`Drawing canvas for practicing the ${charType} ${character}`"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
        @touchstart.prevent="handleTouchStart"
        @touchmove.prevent="handleTouchMove"
        @touchend.prevent="stopDrawing"
      />
    </div>

    <!-- Controls -->
    <div class="controls">
      <button
        v-if="showStepByStepButton"
        class="control-btn step-btn"
        :class="{ active: guidedMode }"
        :aria-pressed="guidedMode"
        aria-label="Step-by-step mode"
        @click="$emit('toggle-guided')"
      >
        <span class="btn-icon" aria-hidden="true">👆</span>
        <span class="btn-text">{{ guidedMode ? 'Exit Steps' : 'Step-by-Step' }}</span>
      </button>

      <button
        v-if="showTraceButton"
        class="control-btn dash-btn"
        :class="{ active: dashTracingMode }"
        :aria-pressed="dashTracingMode"
        aria-label="Trace mode"
        @click="$emit('toggle-dash-tracing')"
      >
        <span class="btn-icon" aria-hidden="true">✂️</span>
        <span class="btn-text">{{ dashTracingMode ? 'Hide Trace' : 'Trace Mode' }}</span>
      </button>

      <button
        v-if="showBestOf3Button"
        class="control-btn best3-btn"
        :class="{ active: bestOf3Mode }"
        :aria-pressed="bestOf3Mode"
        aria-label="Best of 3 mode"
        @click="$emit('toggle-best-of-3')"
      >
        <span class="btn-icon" aria-hidden="true">🎯</span>
        <span class="btn-text">{{ bestOf3Mode ? 'Best of 3: ON' : 'Best of 3' }}</span>
      </button>

      <button
        v-if="showDebugButton"
        class="control-btn debug-btn"
        :class="{ active: showDebugMode }"
        :aria-pressed="showDebugMode"
        aria-label="Debug mode"
        @click="$emit('toggle-debug-mode')"
      >
        <span class="btn-icon" aria-hidden="true">🔍</span>
        <span class="btn-text">{{ showDebugMode ? 'Debug: ON' : 'Debug' }}</span>
      </button>

      <button class="control-btn clear-btn" aria-label="Clear drawing" @click="clearCanvas">
        <span class="btn-icon" aria-hidden="true">🗑️</span>
        <span class="btn-text">Clear</span>
      </button>

      <button
        class="control-btn submit-btn"
        :disabled="isSubmitting"
        aria-label="Submit drawing"
        @click="submitDrawing"
      >
        <span class="btn-icon" aria-hidden="true">{{ isSubmitting ? '⏳' : '✓' }}</span>
        <span class="btn-text">{{ isSubmitting ? 'Checking...' : 'Done!' }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, toRefs } from 'vue'
import axios from 'axios'
import api from '@/services/api'
import { apiUrl } from '@/config/api'

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
      default: true
    },
    showStepByStepButton: {
      type: Boolean,
      default: true
    },
    guidedMode: {
      type: Boolean,
      default: false
    },
    currentStrokeStep: {
      type: Number,
      default: 0
    },
    selectedFont: {
      type: String,
      default: null
    },
    voiceGender: {
      type: String,
      default: 'female'
    },
    playerName: {
      type: String,
      default: null
    },
    playerNumber: {
      type: Number,
      default: null
    },
    totalPlayers: {
      type: Number,
      default: null
    },
    highContrastMode: {
      type: Boolean,
      default: false
    },
    strokeTolerance: {
      type: Number,
      default: 0.5
    },
    colorBlindMode: {
      type: Boolean,
      default: false
    },
    audioSpeed: {
      type: Number,
      default: 1.0
    },
    enableCaptions: {
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
  emits: ['submit', 'toggle-dash-tracing', 'toggle-best-of-3', 'toggle-debug-mode', 'toggle-guided', 'stroke-completed', 'reset-guided-progress', 'guided-complete', 'play-audio'],
  setup(props, { emit }) {
    const { showDebugMode } = toRefs(props)
    const canvas = ref(null)
    const canvasWrapper = ref(null)
    const ctx = ref(null)
    const isDrawing = ref(false)
    const isSubmitting = ref(false)
    const lastX = ref(0)
    const lastY = ref(0)
    const canvasSize = ref(400)
    const generatedGuide = ref(null)

    // Guided mode state
    const guidedStrokes = ref(null)
    const userStrokePoints = ref([])
    const strokeFeedback = ref(null)
    const isValidating = ref(false)
    const canvasStateBeforeStroke = ref(null)  // Save state to restore on failed stroke

    const playAudio = () => {
      // Emit event for App.vue to handle (includes caption support)
      emit('play-audio', props.character)
    }

    // Computed for stroke tolerance display multiplier
    const displayMultiplier = computed(() => props.strokeTolerance || 0.5)

    // Computed for showing shape indicators (color blind support)
    const showShapeIndicators = computed(() =>
      props.colorBlindMode || props.highContrastMode
    )

    const charType = computed(() => {
      if (/[A-Z]/.test(props.character)) return 'uppercase letter'
      if (/[a-z]/.test(props.character)) return 'lowercase letter'
      return 'number'
    })

    // Computed property for showing trace overlay - ensures reactivity
    const showTraceOverlay = computed(() => {
      return props.dashTracingMode && generatedGuide.value?.trace_image
    })

    const fetchStrokeData = async () => {
      try {
        // Build guide URL with optional font parameter
        let guideUrl = apiUrl(`/api/characters/${encodeURIComponent(props.character)}/guides?size=${canvasSize.value}`)
        if (props.selectedFont) {
          guideUrl += `&font=${encodeURIComponent(props.selectedFont)}`
        }

        const guideResponse = await axios.get(guideUrl)
        generatedGuide.value = guideResponse.data
      } catch (error) {
        console.error('Failed to fetch guide data:', error)
      }
    }

    const fetchGuidedStrokes = async () => {
      try {
        let url = apiUrl(`/api/characters/${encodeURIComponent(props.character)}/guided-strokes?size=${canvasSize.value}`)
        if (props.selectedFont) {
          url += `&font=${encodeURIComponent(props.selectedFont)}`
        }
        const response = await axios.get(url)
        guidedStrokes.value = response.data
      } catch (error) {
        console.error('Failed to fetch guided strokes:', error)
      }
    }

    const validateCurrentStroke = async () => {
      if (!guidedStrokes.value || userStrokePoints.value.length < 3) {
        return { valid: false, feedback: 'Draw a longer line!' }
      }

      isValidating.value = true
      try {
        const response = await axios.post(
          apiUrl(`/api/characters/${encodeURIComponent(props.character)}/validate-stroke`),
          {
            stroke_index: props.currentStrokeStep,
            drawn_points: userStrokePoints.value,
            font: props.selectedFont || null,
            tolerance_multiplier: props.strokeTolerance * 2  // Convert 0.5/0.75/1.0 to 1.0/1.5/2.0
          }
        )
        return response.data
      } catch (error) {
        console.error('Failed to validate stroke:', error)
        return { valid: false, feedback: 'Something went wrong. Try again!' }
      } finally {
        isValidating.value = false
      }
    }

    const currentGuidedStroke = computed(() => {
      if (!guidedStrokes.value?.strokes) return null
      return guidedStrokes.value.strokes[props.currentStrokeStep] || null
    })

    const completedGuidedStrokes = computed(() => {
      if (!guidedStrokes.value?.strokes) return []
      return guidedStrokes.value.strokes.slice(0, props.currentStrokeStep)
    })

    const isGuidedComplete = computed(() => {
      if (!guidedStrokes.value?.strokes) return false
      return props.currentStrokeStep >= guidedStrokes.value.strokes.length
    })

    // High contrast mode colors for guided mode
    // Note: Canvas background is WHITE, so high contrast uses BLACK for visibility
    const guidedColors = computed(() => {
      if (props.highContrastMode) {
        return {
          // Start zone (high contrast: black on white canvas)
          startFill: 'rgba(0, 0, 0, 0.1)',
          startStroke: '#000000',
          startDotFill: '#000000',
          startTextFill: '#FFFFFF',
          // End zone (high contrast: black on white canvas)
          endFill: 'rgba(0, 0, 0, 0.1)',
          endStroke: '#000000',
          // Instruction text
          instructionBg: 'rgba(0, 0, 0, 0.9)',
          instructionText: '#FFFFFF',
          instructionStroke: '#000000',
          // Completion message
          completionBg: 'rgba(0, 0, 0, 0.95)',
          completionText: '#FFFFFF',
          completionStroke: '#000000',
          // Feedback colors (high contrast)
          feedbackValidBg: 'rgba(0, 0, 0, 0.95)',
          feedbackInvalidBg: 'rgba(128, 0, 0, 0.95)',
          feedbackValidText: '#FFFFFF',
          feedbackInvalidText: '#FFFFFF',
          feedbackValidStroke: '#000000',
          feedbackInvalidStroke: '#800000',
          // Path color override (for dashed guide) - BLACK on white canvas
          pathColor: '#000000'
        }
      }
      return {
        // Normal mode colors (green and orange)
        startFill: 'rgba(76, 175, 80, 0.1)',
        startStroke: '#4CAF50',
        startDotFill: '#4CAF50',
        startTextFill: 'white',
        endFill: 'rgba(255, 152, 0, 0.1)',
        endStroke: '#FF9800',
        instructionBg: 'rgba(0, 0, 0, 0.7)',
        instructionText: 'white',
        completionBg: 'rgba(76, 175, 80, 0.9)',
        completionText: 'white',
        completionStroke: 'none',
        // Feedback colors (normal)
        feedbackValidBg: 'rgba(76, 175, 80, 0.9)',
        feedbackInvalidBg: 'rgba(255, 152, 0, 0.9)',
        feedbackValidText: 'white',
        feedbackInvalidText: 'white',
        feedbackValidStroke: 'none',
        feedbackInvalidStroke: 'none',
        // Instruction box
        instructionStroke: 'none',
        pathColor: null  // Use stroke's own color
      }
    })

    const setupCanvas = () => {
      if (!canvas.value || !canvasWrapper.value) return

      const wrapper = canvasWrapper.value
      const size = Math.min(wrapper.clientWidth, wrapper.clientHeight, 500)
      canvasSize.value = size

      canvas.value.width = size
      canvas.value.height = size

      ctx.value = canvas.value.getContext('2d')
      ctx.value.lineCap = 'round'
      ctx.value.lineJoin = 'round'
      ctx.value.lineWidth = 12
      ctx.value.strokeStyle = '#333'

      // Fill with white background
      ctx.value.fillStyle = 'white'
      ctx.value.fillRect(0, 0, size, size)

      // Draw ruled paper lines
      drawRuledLines(size)
    }

    const drawRuledLines = (size) => {
      if (!ctx.value) return

      const lineSpacing = size / 8  // 8 lines across the canvas
      const lineColor = '#add8e6'   // Light blue like notebook paper

      ctx.value.save()
      ctx.value.strokeStyle = lineColor
      ctx.value.lineWidth = 1

      // Draw horizontal lines
      for (let y = lineSpacing; y < size; y += lineSpacing) {
        ctx.value.beginPath()
        ctx.value.moveTo(0, y)
        ctx.value.lineTo(size, y)
        ctx.value.stroke()
      }

      ctx.value.restore()
    }

    const getCanvasCoords = (clientX, clientY) => {
      const rect = canvas.value.getBoundingClientRect()
      const scaleX = canvas.value.width / rect.width
      const scaleY = canvas.value.height / rect.height
      return {
        x: (clientX - rect.left) * scaleX,
        y: (clientY - rect.top) * scaleY
      }
    }

    const startDrawing = (e) => {
      isDrawing.value = true
      const coords = getCanvasCoords(e.clientX, e.clientY)
      lastX.value = coords.x
      lastY.value = coords.y

      // Track points in guided mode
      if (props.guidedMode) {
        // Save canvas state before drawing so we can restore on failure
        canvasStateBeforeStroke.value = ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height)
        userStrokePoints.value = [[coords.x, coords.y]]
        strokeFeedback.value = null
      }
    }

    const draw = (e) => {
      if (!isDrawing.value) return

      const coords = getCanvasCoords(e.clientX, e.clientY)

      ctx.value.beginPath()
      ctx.value.moveTo(lastX.value, lastY.value)
      ctx.value.lineTo(coords.x, coords.y)
      ctx.value.stroke()

      lastX.value = coords.x
      lastY.value = coords.y

      // Track points in guided mode
      if (props.guidedMode) {
        userStrokePoints.value.push([coords.x, coords.y])
      }
    }

    const stopDrawing = async () => {
      if (!isDrawing.value) return
      isDrawing.value = false

      // Validate stroke in guided mode
      if (props.guidedMode && userStrokePoints.value.length > 2 && !isGuidedComplete.value) {
        const result = await validateCurrentStroke()
        strokeFeedback.value = result

        if (result.valid) {
          const isLastStroke = props.currentStrokeStep + 1 >= guidedStrokes.value.total_strokes

          setTimeout(() => {
            strokeFeedback.value = null
            canvasStateBeforeStroke.value = null  // Will be set fresh when next stroke starts

            if (isLastStroke) {
              // Last stroke - keep the drawing, signal completion
              emit('guided-complete')
            } else {
              // More strokes to go - keep the drawing visible, advance to next stroke
              emit('stroke-completed', props.currentStrokeStep)
            }
          }, 800) // Brief delay to show feedback
        } else {
          // Failed - restore canvas to before this stroke attempt
          setTimeout(() => {
            if (canvasStateBeforeStroke.value) {
              ctx.value.putImageData(canvasStateBeforeStroke.value, 0, 0)
            }
            strokeFeedback.value = null
          }, 1200) // Show feedback a bit longer before erasing
        }
        userStrokePoints.value = []
      }
    }

    const handleTouchStart = (e) => {
      const touch = e.touches[0]
      const coords = getCanvasCoords(touch.clientX, touch.clientY)
      isDrawing.value = true
      lastX.value = coords.x
      lastY.value = coords.y

      // Track points in guided mode
      if (props.guidedMode) {
        // Save canvas state before drawing so we can restore on failure
        canvasStateBeforeStroke.value = ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height)
        userStrokePoints.value = [[coords.x, coords.y]]
        strokeFeedback.value = null
      }
    }

    const handleTouchMove = (e) => {
      if (!isDrawing.value) return

      const touch = e.touches[0]
      const coords = getCanvasCoords(touch.clientX, touch.clientY)

      ctx.value.beginPath()
      ctx.value.moveTo(lastX.value, lastY.value)
      ctx.value.lineTo(coords.x, coords.y)
      ctx.value.stroke()

      lastX.value = coords.x
      lastY.value = coords.y

      // Track points in guided mode
      if (props.guidedMode) {
        userStrokePoints.value.push([coords.x, coords.y])
      }
    }

    const clearCanvas = (resetGuided = true) => {
      ctx.value.fillStyle = 'white'
      ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
      drawRuledLines(canvas.value.width)

      // Reset guided mode progress when manually clearing
      if (props.guidedMode && resetGuided) {
        userStrokePoints.value = []
        strokeFeedback.value = null
        emit('reset-guided-progress')
      }
    }

    const submitDrawing = async () => {
      if (isSubmitting.value) return

      isSubmitting.value = true

      try {
        const imageData = canvas.value.toDataURL('image/png')

        // Determine the drawing mode
        let mode = 'freestyle'
        if (props.guidedMode) {
          mode = 'step-by-step'
        } else if (props.dashTracingMode) {
          mode = 'tracing'
        }

        const response = await api.post('/api/score', {
          image_data: imageData,
          character: props.character,
          font: props.selectedFont || null,
          mode: mode,
          record_progress: !props.isMultiplayer  // Don't record progress in multiplayer
        })

        emit('submit', {
          imageData,
          scoreResult: response.data
        })
      } catch (error) {
        console.error('Failed to submit drawing:', error)
        alert('Oops! Something went wrong. Please try again.')
      } finally {
        isSubmitting.value = false
      }
    }

    // Helper functions for SVG tracing
    const getScaledPoint = (point) => {
      const scale = canvasSize.value / 100
      return [point[0] * scale, point[1] * scale]
    }

    const getScaledPoints = (points) => {
      return points.map(p => getScaledPoint(p).join(',')).join(' ')
    }

    const getArrowPoints = (points) => {
      if (points.length < 2) return ''

      const scale = canvasSize.value / 100
      const lastIdx = points.length - 1
      const endPoint = points[lastIdx]
      const prevPoint = points[Math.max(0, lastIdx - 1)]

      const endX = endPoint[0] * scale
      const endY = endPoint[1] * scale
      const prevX = prevPoint[0] * scale
      const prevY = prevPoint[1] * scale

      // Calculate direction
      const dx = endX - prevX
      const dy = endY - prevY
      const length = Math.sqrt(dx * dx + dy * dy)

      if (length === 0) return ''

      const unitX = dx / length
      const unitY = dy / length

      // Arrow dimensions
      const arrowLength = 15
      const arrowWidth = 10

      // Arrow tip at end point
      const tipX = endX
      const tipY = endY

      // Arrow base points
      const baseX = endX - unitX * arrowLength
      const baseY = endY - unitY * arrowLength

      const perpX = -unitY
      const perpY = unitX

      const leftX = baseX + perpX * arrowWidth
      const leftY = baseY + perpY * arrowWidth
      const rightX = baseX - perpX * arrowWidth
      const rightY = baseY - perpY * arrowWidth

      return `${tipX},${tipY} ${leftX},${leftY} ${rightX},${rightY}`
    }

    const getGeneratedArrowPoints = (points) => {
      if (points.length < 2) return ''

      const lastIdx = points.length - 1
      const endPoint = points[lastIdx]
      const prevPoint = points[Math.max(0, lastIdx - 1)]

      const endX = endPoint[0]
      const endY = endPoint[1]
      const prevX = prevPoint[0]
      const prevY = prevPoint[1]

      const dx = endX - prevX
      const dy = endY - prevY
      const length = Math.sqrt(dx * dx + dy * dy)

      if (length === 0) return ''

      const unitX = dx / length
      const unitY = dy / length

      // Small arrow for 0-100 coordinate space
      const arrowLength = 3
      const arrowWidth = 2

      const tipX = endX
      const tipY = endY
      const baseX = endX - unitX * arrowLength
      const baseY = endY - unitY * arrowLength

      const perpX = -unitY
      const perpY = unitX

      const leftX = baseX + perpX * arrowWidth
      const leftY = baseY + perpY * arrowWidth
      const rightX = baseX - perpX * arrowWidth
      const rightY = baseY - perpY * arrowWidth

      return `${tipX},${tipY} ${leftX},${leftY} ${rightX},${rightY}`
    }

    // Arrow for guided mode (canvas-sized coordinates)
    const getGuidedArrowPoints = (points) => {
      if (points.length < 2) return ''

      const lastIdx = points.length - 1
      const endPoint = points[lastIdx]
      const prevPoint = points[Math.max(0, lastIdx - 1)]

      const endX = endPoint[0]
      const endY = endPoint[1]
      const prevX = prevPoint[0]
      const prevY = prevPoint[1]

      const dx = endX - prevX
      const dy = endY - prevY
      const length = Math.sqrt(dx * dx + dy * dy)

      if (length === 0) return ''

      const unitX = dx / length
      const unitY = dy / length

      // Arrow for canvas-sized coordinates
      const arrowLength = 18
      const arrowWidth = 12

      const tipX = endX
      const tipY = endY
      const baseX = endX - unitX * arrowLength
      const baseY = endY - unitY * arrowLength

      const perpX = -unitY
      const perpY = unitX

      const leftX = baseX + perpX * arrowWidth
      const leftY = baseY + perpY * arrowWidth
      const rightX = baseX - perpX * arrowWidth
      const rightY = baseY - perpY * arrowWidth

      return `${tipX},${tipY} ${leftX},${leftY} ${rightX},${rightY}`
    }

    onMounted(() => {
      nextTick(async () => {
        setupCanvas()
        // Always fetch stroke/guide data on mount
        await fetchStrokeData()
        // If guided mode is already enabled on mount, fetch guided strokes
        if (props.guidedMode) {
          fetchGuidedStrokes()
        }
      })

      window.addEventListener('resize', setupCanvas)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', setupCanvas)
    })

    watch(() => props.character, () => {
      nextTick(() => {
        clearCanvas(false)
        fetchStrokeData()
        if (props.guidedMode) {
          fetchGuidedStrokes()
        }
      })
    })

    // Fetch guided strokes when guided mode is toggled on
    watch(() => props.guidedMode, (newVal) => {
      if (newVal) {
        fetchGuidedStrokes()
        userStrokePoints.value = []
        strokeFeedback.value = null
      }
    })

    watch(() => props.dashTracingMode, async (newVal) => {
      // Fetch guide data if trace mode is enabled and we don't have the trace image
      if (newVal && (!generatedGuide.value || !generatedGuide.value.trace_image)) {
        await fetchStrokeData()
      }
      nextTick(() => {
        clearCanvas()
      })
    })

    // Clear canvas when attempt changes (best of 3 mode)
    watch(() => props.currentAttempt, () => {
      nextTick(() => {
        clearCanvas()
      })
    })

    // Clear canvas when guided mode step resets to 0 (Try Again)
    watch(() => props.currentStrokeStep, (newVal, oldVal) => {
      if (props.guidedMode && newVal === 0 && oldVal !== 0) {
        nextTick(() => {
          // Clear canvas without emitting reset (already reset by parent)
          ctx.value.fillStyle = 'white'
          ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
          drawRuledLines(canvas.value.width)
          userStrokePoints.value = []
          strokeFeedback.value = null
          canvasStateBeforeStroke.value = null
        })
      }
    })

    // Refetch guides and guided strokes when font changes
    watch(() => props.selectedFont, () => {
      fetchStrokeData()
      if (props.guidedMode) {
        fetchGuidedStrokes()
        // Reset guided progress when font changes
        userStrokePoints.value = []
        strokeFeedback.value = null
        emit('reset-guided-progress')
      }
    })

    return {
      canvas,
      canvasWrapper,
      canvasSize,
      charType,
      generatedGuide,
      showTraceOverlay,
      isDrawing,
      isSubmitting,
      playAudio,
      startDrawing,
      draw,
      stopDrawing,
      handleTouchStart,
      handleTouchMove,
      clearCanvas,
      submitDrawing,
      getScaledPoint,
      getScaledPoints,
      getArrowPoints,
      getGeneratedArrowPoints,
      showDebugMode,
      // Guided mode
      guidedStrokes,
      userStrokePoints,
      strokeFeedback,
      isValidating,
      currentGuidedStroke,
      completedGuidedStrokes,
      isGuidedComplete,
      guidedColors,
      fetchGuidedStrokes,
      getGuidedArrowPoints,
      displayMultiplier,
      showShapeIndicators
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

.character-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 15px;
  padding: 15px;
}

.current-char {
  font-size: 4rem;
  font-weight: 700;
  color: white;
  text-shadow: 3px 3px 0 rgba(0, 0, 0, 0.2);
  min-width: 80px;
  text-align: center;
}

.play-sound-btn {
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s, background 0.2s;
}

.play-sound-btn:hover:not(:disabled) {
  transform: scale(1.1);
  background: white;
}

.play-sound-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.play-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.char-info-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
}

.char-info {
  color: white;
  font-size: 1.3rem;
  font-weight: 500;
}

.attempt-indicator {
  color: #FFE66D;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.attempt-dots {
  display: flex;
  gap: 4px;
}

.attempt-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.attempt-dot.filled {
  background: #4ECDC4;
}

.attempt-dot.current {
  background: #FFE66D;
  box-shadow: 0 0 8px #FFE66D;
}

/* Player Turn Indicator (inline in character display) */
.char-info.player-turn {
  color: #FFE66D;
  font-weight: 700;
}

.turn-progress {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* High Score Display */
.high-score-display {
  color: #FFE66D;
  font-size: 0.9rem;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.2);
  padding: 4px 12px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.canvas-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 200px;
}

.trace-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  max-width: 500px;
  max-height: 500px;
  pointer-events: none;
  z-index: 1;
  object-fit: contain;
}

.drawing-canvas {
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  cursor: crosshair;
  touch-action: none;
  max-width: 500px;
  max-height: 500px;
  width: 100%;
  aspect-ratio: 1;
}

.controls {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 25px;
  border-radius: 30px;
  font-size: 1.1rem;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.control-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 1.3rem;
}

.trace-btn {
  background: white;
  color: #764ba2;
}

.trace-btn.active {
  background: #4ECDC4;
  color: white;
}

.dash-btn {
  background: white;
  color: #FF9800;
}

.dash-btn.active {
  background: #FF9800;
  color: white;
}

.best3-btn {
  background: white;
  color: #9C27B0;
}

.best3-btn.active {
  background: #9C27B0;
  color: white;
}

.debug-btn {
  background: white;
  color: #607D8B;
}

.debug-btn.active {
  background: #607D8B;
  color: white;
}

.clear-btn {
  background: white;
  color: #FF6B6B;
}

.submit-btn {
  background: linear-gradient(135deg, #4ECDC4 0%, #44B09E 100%);
  color: white;
}

.submit-btn:not(:disabled):hover {
  transform: scale(1.05);
}

.step-btn {
  background: white;
  color: #2196F3;
}

.step-btn.active {
  background: #2196F3;
  color: white;
}

/* Guided Mode Styles */
.guided-layer {
  position: absolute;
  width: 100%;
  height: 100%;
  max-width: 500px;
  max-height: 500px;
  pointer-events: none;
  z-index: 2;
}

.guided-path {
  animation: dash-move 1s linear infinite;
}

@keyframes dash-move {
  to {
    stroke-dashoffset: -18;
  }
}

.start-zone-ring {
  animation: glow-ring 1.2s ease-in-out infinite;
}

.start-zone-dot {
  /* No animation on the dot - keep it stable as the target */
  filter: drop-shadow(0 0 4px #4CAF50);
}

.guided-layer.high-contrast .start-zone-dot {
  filter: drop-shadow(0 0 6px #000000);
}

.guided-layer.high-contrast .guided-path {
  stroke-width: 6;
}

.guided-layer.high-contrast .start-zone-ring,
.guided-layer.high-contrast .end-zone-ring {
  stroke-width: 3;
}

@keyframes glow-ring {
  0%, 100% {
    opacity: 1;
    stroke-width: 2;
  }
  50% {
    opacity: 0.4;
    stroke-width: 3;
  }
}

.end-zone-ring {
  animation: glow-ring-orange 1.2s ease-in-out infinite;
}

@keyframes glow-ring-orange {
  0%, 100% {
    opacity: 1;
    stroke-width: 2;
  }
  50% {
    opacity: 0.4;
    stroke-width: 3;
  }
}

.end-arrow {
  animation: arrow-pulse 0.8s ease-in-out infinite alternate;
}

@keyframes arrow-pulse {
  from {
    opacity: 0.7;
  }
  to {
    opacity: 1;
  }
}

.guided-progress {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 3;
}

.progress-text {
  font-size: 0.85rem;
  font-weight: 500;
}

.progress-dots {
  display: flex;
  gap: 5px;
}

.progress-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.progress-dot.completed {
  background: #4CAF50;
}

.progress-dot.current {
  background: #FFE66D;
  box-shadow: 0 0 6px #FFE66D;
}

@media (max-width: 600px) {
  .drawing-container {
    padding: 10px;
    gap: 10px;
  }

  .character-display {
    padding: 10px;
    gap: 15px;
  }

  .current-char {
    font-size: 3rem;
    min-width: 60px;
  }

  .char-info {
    font-size: 1.1rem;
  }

  .control-btn {
    padding: 12px 18px;
    font-size: 1rem;
  }

  .btn-text {
    display: none;
  }

  .btn-icon {
    font-size: 1.5rem;
  }

  .turn-progress {
    font-size: 0.8rem;
  }
}
</style>
