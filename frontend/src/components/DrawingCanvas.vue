<template>
  <div class="drawing-container">
    <!-- Character Display -->
    <div class="character-display">
      <span class="current-char">{{ character }}</span>
      <button class="play-sound-btn" @click="playAudio" :disabled="isPlayingAudio" title="Play pronunciation">
        <span class="play-icon">{{ isPlayingAudio ? '...' : '🔊' }}</span>
      </button>
      <div class="char-info-container">
        <span class="char-info">Draw this {{ charType }}!</span>
        <span v-if="bestOf3Mode" class="attempt-indicator">
          Attempt {{ currentAttempt }} of 3
          <span class="attempt-dots">
            <span v-for="i in 3" :key="i" class="attempt-dot" :class="{ filled: i <= attempts.length, current: i === currentAttempt }"></span>
          </span>
        </span>
      </div>
    </div>

    <!-- Canvas Area -->
    <div class="canvas-wrapper" ref="canvasWrapper">
      <!-- Animated Guide Layer (from auto-generated font data) -->
      <svg
        v-if="tracingMode && generatedGuide?.animated_strokes"
        class="tracing-layer"
        :viewBox="`0 0 100 100`"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- Animated stroke paths - each stroke appears one at a time -->
        <g v-for="(stroke, index) in generatedGuide.animated_strokes" :key="index">
          <polyline
            v-if="index < animationStep"
            :points="stroke.points.map(p => p.join(',')).join(' ')"
            fill="none"
            :stroke="stroke.color"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="animated-stroke"
            :style="{ animationDelay: `${index * 0.1}s` }"
          />
          <!-- Start marker with number -->
          <g v-if="index < animationStep && stroke.points.length > 0">
            <!-- Outer ring for first stroke -->
            <circle
              v-if="index === 0"
              :cx="stroke.points[0][0]"
              :cy="stroke.points[0][1]"
              r="6"
              fill="none"
              :stroke="stroke.color"
              stroke-width="1"
              class="start-marker-ring"
            />
            <!-- Start marker circle -->
            <circle
              :cx="stroke.points[0][0]"
              :cy="stroke.points[0][1]"
              :r="index === 0 ? 4 : 3"
              :fill="stroke.color"
              :class="index === 0 ? 'start-marker-first' : 'start-marker'"
            />
            <!-- Number label -->
            <text
              :x="stroke.points[0][0]"
              :y="stroke.points[0][1] + 1.2"
              text-anchor="middle"
              fill="white"
              font-size="3"
              font-weight="bold"
            >
              {{ stroke.order }}
            </text>
            <!-- Direction arrow at end -->
            <polygon
              v-if="stroke.points.length >= 2"
              :points="getGeneratedArrowPoints(stroke.points)"
              :fill="stroke.color"
            />
          </g>
        </g>
        <!-- Replay button when animation complete -->
        <g v-if="!isAnimating && animationStep > 0" class="replay-hint">
          <text x="50" y="95" text-anchor="middle" fill="#666" font-size="3">
            Tap "Show Guide" to replay
          </text>
        </g>
      </svg>

      <!-- Trace Image Overlay (dashed lines from font skeleton) -->
      <img
        v-if="dashTracingMode && generatedGuide?.trace_image"
        :src="generatedGuide.trace_image"
        class="trace-overlay"
        alt="Trace guide"
      />

      <!-- Guided Mode Layer (step-by-step instruction) -->
      <svg
        v-if="guidedMode && guidedStrokes"
        class="guided-layer"
        :viewBox="`0 0 ${canvasSize} ${canvasSize}`"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- Completed strokes (dimmed) -->
        <polyline
          v-for="(stroke, index) in completedGuidedStrokes"
          :key="'completed-' + index"
          :points="stroke.points.map(p => p.join(',')).join(' ')"
          fill="none"
          :stroke="stroke.color"
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
            :stroke="currentGuidedStroke.color"
            stroke-width="4"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-dasharray="10,8"
            class="guided-path"
          />

          <!-- Start zone - stable green circle with glowing ring -->
          <!-- Outer ring shows acceptable start area -->
          <circle
            :cx="currentGuidedStroke.start_zone.x"
            :cy="currentGuidedStroke.start_zone.y"
            :r="currentGuidedStroke.start_zone.radius * 0.5"
            fill="rgba(76, 175, 80, 0.1)"
            stroke="#4CAF50"
            stroke-width="2"
            stroke-dasharray="8,4"
            class="start-zone-ring"
          />
          <!-- Center dot - the target to aim for (stays perfectly still) -->
          <circle
            :cx="currentGuidedStroke.start_zone.x"
            :cy="currentGuidedStroke.start_zone.y"
            r="14"
            fill="#4CAF50"
            class="start-zone-dot"
          />
          <!-- Stroke number -->
          <text
            :x="currentGuidedStroke.start_zone.x"
            :y="currentGuidedStroke.start_zone.y + 5"
            text-anchor="middle"
            fill="white"
            font-size="14"
            font-weight="bold"
          >
            {{ currentGuidedStroke.order }}
          </text>

          <!-- End zone - circle showing acceptable area + arrow -->
          <circle
            :cx="currentGuidedStroke.end_zone.x"
            :cy="currentGuidedStroke.end_zone.y"
            :r="currentGuidedStroke.end_zone.radius * 0.5"
            fill="rgba(255, 152, 0, 0.1)"
            stroke="#FF9800"
            stroke-width="2"
            stroke-dasharray="8,4"
            class="end-zone-ring"
          />
          <polygon
            :points="getGuidedArrowPoints(currentGuidedStroke.points)"
            :fill="currentGuidedStroke.color"
            class="end-arrow"
          />
        </g>

        <!-- Instruction text at bottom -->
        <g v-if="currentGuidedStroke && !isGuidedComplete">
          <rect
            :x="10"
            :y="canvasSize - 45"
            :width="canvasSize - 20"
            height="35"
            rx="8"
            fill="rgba(0,0,0,0.7)"
          />
          <text
            :x="canvasSize / 2"
            :y="canvasSize - 22"
            text-anchor="middle"
            fill="white"
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
            fill="rgba(76, 175, 80, 0.9)"
          />
          <text
            :x="canvasSize / 2"
            :y="canvasSize / 2 + 8"
            text-anchor="middle"
            fill="white"
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
            :fill="strokeFeedback.valid ? 'rgba(76, 175, 80, 0.9)' : 'rgba(255, 152, 0, 0.9)'"
          />
          <text
            :x="canvasSize / 2"
            :y="canvasSize / 2 + 6"
            text-anchor="middle"
            fill="white"
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
          ></span>
        </div>
      </div>

      <!-- Drawing Canvas -->
      <canvas
        ref="canvas"
        class="drawing-canvas"
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
      <button v-if="showGuideButton" class="control-btn trace-btn" :class="{ active: tracingMode }" @click="$emit('toggle-tracing')">
        <span class="btn-icon">✏️</span>
        <span class="btn-text">{{ tracingMode ? 'Hide Guide' : 'Show Guide' }}</span>
      </button>

      <button v-if="showTraceButton" class="control-btn dash-btn" :class="{ active: dashTracingMode }" @click="$emit('toggle-dash-tracing')">
        <span class="btn-icon">✂️</span>
        <span class="btn-text">{{ dashTracingMode ? 'Hide Trace' : 'Trace Mode' }}</span>
      </button>

      <button v-if="showBestOf3Button" class="control-btn best3-btn" :class="{ active: bestOf3Mode }" @click="$emit('toggle-best-of-3')">
        <span class="btn-icon">🎯</span>
        <span class="btn-text">{{ bestOf3Mode ? 'Best of 3: ON' : 'Best of 3' }}</span>
      </button>

      <button v-if="showDebugButton" class="control-btn debug-btn" :class="{ active: showDebugMode }" @click="$emit('toggle-debug-mode')">
        <span class="btn-icon">🔍</span>
        <span class="btn-text">{{ showDebugMode ? 'Debug: ON' : 'Debug' }}</span>
      </button>

      <button v-if="showStepByStepButton" class="control-btn step-btn" :class="{ active: guidedMode }" @click="$emit('toggle-guided')">
        <span class="btn-icon">👆</span>
        <span class="btn-text">{{ guidedMode ? 'Exit Steps' : 'Step-by-Step' }}</span>
      </button>

      <button class="control-btn clear-btn" @click="clearCanvas">
        <span class="btn-icon">🗑️</span>
        <span class="btn-text">Clear</span>
      </button>

      <button class="control-btn submit-btn" @click="submitDrawing" :disabled="isSubmitting">
        <span class="btn-icon">{{ isSubmitting ? '⏳' : '✓' }}</span>
        <span class="btn-text">{{ isSubmitting ? 'Checking...' : 'Done!' }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, toRefs } from 'vue'
import axios from 'axios'

export default {
  name: 'DrawingCanvas',
  props: {
    character: {
      type: String,
      required: true
    },
    tracingMode: {
      type: Boolean,
      default: false
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
    showGuideButton: {
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
    }
  },
  emits: ['submit', 'toggle-tracing', 'toggle-dash-tracing', 'toggle-best-of-3', 'toggle-debug-mode', 'toggle-guided', 'stroke-completed', 'reset-guided-progress', 'guided-complete'],
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
    const animationStep = ref(0)
    const isAnimating = ref(false)
    const isPlayingAudio = ref(false)

    // Guided mode state
    const guidedStrokes = ref(null)
    const userStrokePoints = ref([])
    const strokeFeedback = ref(null)
    const isValidating = ref(false)
    const canvasStateBeforeStroke = ref(null)  // Save state to restore on failed stroke

    const playAudio = async () => {
      if (isPlayingAudio.value) return

      isPlayingAudio.value = true
      try {
        const audio = new Audio(`/api/audio/${encodeURIComponent(props.character)}?voice=${props.voiceGender}`)
        audio.onended = () => {
          isPlayingAudio.value = false
        }
        audio.onerror = () => {
          isPlayingAudio.value = false
        }
        await audio.play()
      } catch (error) {
        console.error('Failed to play audio:', error)
        isPlayingAudio.value = false
      }
    }

    const charType = computed(() => {
      if (/[A-Z]/.test(props.character)) return 'uppercase letter'
      if (/[a-z]/.test(props.character)) return 'lowercase letter'
      return 'number'
    })

    const fetchStrokeData = async () => {
      try {
        // Build guide URL with optional font parameter
        let guideUrl = `/api/characters/${encodeURIComponent(props.character)}/guides?size=${canvasSize.value}`
        if (props.selectedFont) {
          guideUrl += `&font=${encodeURIComponent(props.selectedFont)}`
        }

        const guideResponse = await axios.get(guideUrl)
        generatedGuide.value = guideResponse.data

        // Start animation when guide is loaded
        if (props.tracingMode && generatedGuide.value?.animated_strokes) {
          startGuideAnimation()
        }
      } catch (error) {
        console.error('Failed to fetch guide data:', error)
      }
    }

    const fetchGuidedStrokes = async () => {
      try {
        const response = await axios.get(`/api/characters/${encodeURIComponent(props.character)}/guided-strokes?size=${canvasSize.value}`)
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
          `/api/characters/${encodeURIComponent(props.character)}/validate-stroke`,
          {
            stroke_index: props.currentStrokeStep,
            drawn_points: userStrokePoints.value
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

    const startGuideAnimation = () => {
      if (!generatedGuide.value?.animated_strokes?.length) return

      animationStep.value = 0
      isAnimating.value = true

      const animateNextStroke = () => {
        if (animationStep.value < generatedGuide.value.animated_strokes.length) {
          animationStep.value++
          setTimeout(animateNextStroke, 800) // 800ms between strokes
        } else {
          isAnimating.value = false
        }
      }

      animateNextStroke()
    }

    const resetAnimation = () => {
      animationStep.value = 0
      isAnimating.value = false
    }

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

        const response = await axios.post('/api/score', {
          image_data: imageData,
          character: props.character
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
      nextTick(() => {
        setupCanvas()
        fetchStrokeData()
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

    watch(() => props.dashTracingMode, async () => {
      // Fetch guide data if not yet loaded
      if (props.dashTracingMode && !generatedGuide.value) {
        await fetchStrokeData()
      }
      nextTick(() => {
        clearCanvas()
      })
    })

    // Restart animation when guide mode is toggled
    watch(() => props.tracingMode, async () => {
      if (props.tracingMode) {
        if (!generatedGuide.value) {
          await fetchStrokeData()
        }
        startGuideAnimation()
      } else {
        resetAnimation()
      }
    })

    // Clear canvas when attempt changes (best of 3 mode)
    watch(() => props.currentAttempt, () => {
      nextTick(() => {
        clearCanvas()
      })
    })

    // Refetch guides when font changes
    watch(() => props.selectedFont, () => {
      fetchStrokeData()
    })

    return {
      canvas,
      canvasWrapper,
      canvasSize,
      charType,
      generatedGuide,
      animationStep,
      isAnimating,
      isSubmitting,
      isPlayingAudio,
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
      startGuideAnimation,
      resetAnimation,
      showDebugMode,
      // Guided mode
      guidedStrokes,
      userStrokePoints,
      strokeFeedback,
      isValidating,
      currentGuidedStroke,
      completedGuidedStrokes,
      isGuidedComplete,
      fetchGuidedStrokes,
      getGuidedArrowPoints
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

.canvas-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 200px;
}

.tracing-layer {
  position: absolute;
  width: 100%;
  height: 100%;
  max-width: 500px;
  max-height: 500px;
  pointer-events: none;
  z-index: 1;
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

.animated-stroke {
  animation: strokeFadeIn 0.5s ease-out forwards;
}

@keyframes strokeFadeIn {
  from {
    opacity: 0;
    stroke-width: 1;
  }
  to {
    opacity: 1;
    stroke-width: 3;
  }
}

.stroke-path {
  animation: dash 2s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -50;
  }
}

.start-marker {
  animation: pulse 1s ease-in-out infinite;
}

.start-marker-first {
  animation: pulse-first 0.8s ease-in-out infinite;
}

.start-marker-ring {
  animation: ring-pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

@keyframes pulse-first {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes ring-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.5; }
}

.direction-arrow {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
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
}
</style>
