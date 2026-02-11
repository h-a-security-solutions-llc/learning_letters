<template>
  <div class="drawing-container">
    <!-- Player Turn Indicator (Multiplayer) -->
    <div v-if="playerName" class="player-turn-indicator">
      <span class="player-badge">Player {{ playerNumber }}/{{ totalPlayers }}</span>
      <span class="player-name-display">{{ playerName }}'s Turn</span>
    </div>

    <!-- Character Display with High Score -->
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
      <!-- High Score Badge - inline with character -->
      <span v-if="highScoreForMode !== null && !isMultiplayer" class="high-score-badge">
        Best: {{ highScoreForMode }}%
      </span>
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

      <!-- Trace overlay - shown in trace mode only (guided mode uses stroke guides without trace to avoid misalignment) -->
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
        :viewBox="`0 0 ${canvasSize} ${canvasSize}`"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- Completed strokes (dimmed) -->
        <g class="completed-strokes">
          <path
            v-for="(stroke, index) in completedStrokePaths"
            :key="'completed-' + index"
            :d="stroke"
            class="stroke-completed"
            fill="none"
            :stroke="guidedColors.completedStroke"
            stroke-width="16"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-opacity="0.4"
          />
        </g>

        <!-- Current stroke path (animated dash with smooth curves) -->
        <path
          v-if="currentStrokePath"
          :d="currentStrokePath"
          class="stroke-guide-path animated"
          fill="none"
          :stroke="guidedColors.pathStroke"
          stroke-width="20"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <!-- Start zone with concentric rings for color blind accessibility -->
        <g v-if="currentStrokeData.points && currentStrokeData.points.length > 0" class="start-zone-group">
          <!-- Outer ring -->
          <circle
            :cx="scaleCoord(currentStrokeData.points[0][0])"
            :cy="scaleCoord(currentStrokeData.points[0][1])"
            :r="strokeTolerance * canvasSize * 0.4"
            :fill="guidedColors.startFill"
            :stroke="guidedColors.startStroke"
            stroke-width="2"
            class="stroke-zone start-zone"
            :class="{ 'active': strokeState === 'waiting' }"
          />
          <!-- Inner ring for color blind mode -->
          <circle
            v-if="colorBlindMode"
            :cx="scaleCoord(currentStrokeData.points[0][0])"
            :cy="scaleCoord(currentStrokeData.points[0][1])"
            :r="strokeTolerance * canvasSize * 0.25"
            fill="none"
            :stroke="guidedColors.startStroke"
            stroke-width="2"
            stroke-dasharray="4 2"
          />
          <!-- Stroke order number -->
          <text
            :x="scaleCoord(currentStrokeData.points[0][0])"
            :y="scaleCoord(currentStrokeData.points[0][1]) + 6"
            text-anchor="middle"
            :fill="guidedColors.startStroke"
            font-size="18"
            font-weight="bold"
            class="stroke-number"
          >
            {{ currentStrokeStep + 1 }}
          </text>
        </g>

        <!-- End zone with diamond shape for color blind accessibility -->
        <g v-if="currentStrokeData.points && currentStrokeData.points.length > 1" class="end-zone-group">
          <!-- End zone circle -->
          <circle
            :cx="scaleCoord(currentStrokeData.points[currentStrokeData.points.length - 1][0])"
            :cy="scaleCoord(currentStrokeData.points[currentStrokeData.points.length - 1][1])"
            :r="strokeTolerance * canvasSize * 0.4"
            :fill="guidedColors.endFill"
            :stroke="guidedColors.endStroke"
            stroke-width="2"
            class="stroke-zone end-zone"
            :class="{ 'approaching': strokeState === 'drawing' }"
          />
          <!-- Diamond shape for color blind mode -->
          <polygon
            v-if="colorBlindMode"
            :points="getDiamondPoints(
              scaleCoord(currentStrokeData.points[currentStrokeData.points.length - 1][0]),
              scaleCoord(currentStrokeData.points[currentStrokeData.points.length - 1][1]),
              strokeTolerance * canvasSize * 0.2
            )"
            fill="none"
            :stroke="guidedColors.endStroke"
            stroke-width="2"
          />
          <!-- Direction arrow pointing to end zone -->
          <path
            :d="getDirectionArrow()"
            fill="none"
            :stroke="guidedColors.endStroke"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="direction-arrow"
          />
        </g>
      </svg>

      <!-- Instruction text box -->
      <div v-if="guidedMode && !isCurrentStrokeComplete && currentStrokeData" class="instruction-box">
        <span class="instruction-text">{{ currentInstruction }}</span>
      </div>

      <!-- Feedback message overlay -->
      <div v-if="strokeFeedback" class="feedback-overlay" :class="{ 'valid': strokeFeedback.valid, 'invalid': !strokeFeedback.valid }">
        <span class="feedback-text">{{ strokeFeedback.feedback }}</span>
      </div>

      <!-- Completion message -->
      <div v-if="guidedMode && isCurrentStrokeComplete && strokeData.length > 0" class="completion-overlay">
        <span class="completion-text">Great job!</span>
        <span class="completion-subtext">All {{ strokeData.length }} strokes complete!</span>
      </div>
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
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { scoreDrawing, getReferenceImage } from '@/services/scoring'
import { getStrokesLegacy } from '@/services/strokeExtraction'

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
    showTraceButton: {
      type: Boolean,
      default: true
    },
    showBestOf3Button: {
      type: Boolean,
      default: true
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
    },
    debugMode: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'submit',
    'toggle-dash-tracing',
    'toggle-best-of-3',
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
    const canvasSize = 400
    const canvasStateBeforeStroke = ref(null)
    const strokeFeedback = ref(null)
    const userStrokePoints = ref([])
    let feedbackTimeout = null

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

    const guidedColors = computed(() => {
      if (props.highContrastMode) {
        return {
          startFill: 'rgba(0, 0, 0, 0.1)',
          startStroke: '#000000',
          endFill: 'rgba(0, 0, 0, 0.1)',
          endStroke: '#000000',
          pathStroke: 'rgba(0, 0, 0, 0.6)',
          completedStroke: '#666666'
        }
      }
      return {
        startFill: 'rgba(76, 175, 80, 0.15)',
        startStroke: '#4CAF50',
        endFill: 'rgba(255, 152, 0, 0.15)',
        endStroke: '#FF9800',
        pathStroke: 'rgba(78, 205, 196, 0.6)',
        completedStroke: '#4ECDC4'
      }
    })

    const currentStrokeData = computed(() => {
      if (!props.guidedMode || strokeData.value.length === 0) return null
      return strokeData.value[props.currentStrokeStep] || null
    })

    const scaleCoord = (val) => {
      return val * (canvasSize / 100)
    }

    const generateSmoothPath = (points) => {
      if (!points || points.length < 2) return ''

      // Scale points from 0-100 to canvas size
      const scaledPoints = points.map(p => [scaleCoord(p[0]), scaleCoord(p[1])])

      // For high-res points (>20), use polyline for performance
      if (scaledPoints.length > 20) {
        let d = `M ${scaledPoints[0][0]},${scaledPoints[0][1]}`
        for (let i = 1; i < scaledPoints.length; i++) {
          d += ` L ${scaledPoints[i][0]},${scaledPoints[i][1]}`
        }
        return d
      }

      // For fewer points, use Catmull-Rom spline interpolation for smooth curves
      const catmullRomSpline = (p0, p1, p2, p3, t) => {
        const t2 = t * t
        const t3 = t2 * t
        return [
          0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                 (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                 (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
          0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                 (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                 (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        ]
      }

      // Generate interpolated points using Catmull-Rom
      const interpolated = []
      const tension = 0.5
      const segments = 10 // Points per segment

      for (let i = 0; i < scaledPoints.length - 1; i++) {
        const p0 = scaledPoints[Math.max(0, i - 1)]
        const p1 = scaledPoints[i]
        const p2 = scaledPoints[Math.min(scaledPoints.length - 1, i + 1)]
        const p3 = scaledPoints[Math.min(scaledPoints.length - 1, i + 2)]

        for (let j = 0; j < segments; j++) {
          const t = j / segments
          interpolated.push(catmullRomSpline(p0, p1, p2, p3, t))
        }
      }
      // Add final point
      interpolated.push(scaledPoints[scaledPoints.length - 1])

      // Build SVG path
      if (interpolated.length === 0) return ''
      let d = `M ${interpolated[0][0]},${interpolated[0][1]}`
      for (let i = 1; i < interpolated.length; i++) {
        d += ` L ${interpolated[i][0]},${interpolated[i][1]}`
      }
      return d
    }

    const currentStrokePath = computed(() => {
      if (!currentStrokeData.value || !currentStrokeData.value.points) return ''
      return generateSmoothPath(currentStrokeData.value.points)
    })

    const completedStrokePaths = computed(() => {
      if (!props.guidedMode || strokeData.value.length === 0) return []
      const paths = []
      for (let i = 0; i < props.currentStrokeStep && i < strokeData.value.length; i++) {
        const stroke = strokeData.value[i]
        if (stroke && stroke.points) {
          paths.push(generateSmoothPath(stroke.points))
        }
      }
      return paths
    })

    const isCurrentStrokeComplete = computed(() => {
      return props.currentStrokeStep >= strokeData.value.length
    })

    const currentInstruction = computed(() => {
      if (!currentStrokeData.value) return ''
      const direction = currentStrokeData.value.direction || ''
      const directionMap = {
        'down': 'Draw down',
        'up': 'Draw up',
        'right': 'Draw right',
        'left': 'Draw left',
        'down-left': 'Draw down and to the left',
        'down-right': 'Draw down and to the right',
        'up-left': 'Draw up and to the left',
        'up-right': 'Draw up and to the right',
        'curve-left': 'Draw a curve to the left',
        'curve-right': 'Draw a curve to the right',
        'right-curve': 'Draw right then curve',
        'down-curve': 'Draw down then curve',
        'curve-in': 'Draw a curve inward'
      }
      return directionMap[direction] || `Draw stroke ${props.currentStrokeStep + 1}`
    })

    const initCanvas = (forceReinit = false) => {
      if (!canvas.value) return

      const rect = canvas.value.getBoundingClientRect()
      const newWidth = Math.round(rect.width * window.devicePixelRatio)
      const newHeight = Math.round(rect.height * window.devicePixelRatio)

      // Skip if size hasn't changed (unless forced)
      const sizeChanged = canvas.value.width !== newWidth || canvas.value.height !== newHeight

      if (!forceReinit && !sizeChanged && ctx.value) {
        return
      }

      // Save existing content if size is the same and we have drawings
      let savedContent = null
      const canPreserveContent = !sizeChanged && ctx.value && hasDrawnOnCanvas.value
      if (canPreserveContent && canvas.value.width > 0 && canvas.value.height > 0) {
        try {
          savedContent = ctx.value.getImageData(0, 0, canvas.value.width, canvas.value.height)
        } catch (e) {
          // Ignore if we can't save
        }
      }

      // Setting width/height clears the canvas
      canvas.value.width = newWidth
      canvas.value.height = newHeight

      ctx.value = canvas.value.getContext('2d')
      ctx.value.scale(window.devicePixelRatio, window.devicePixelRatio)

      ctx.value.lineCap = 'round'
      ctx.value.lineJoin = 'round'
      ctx.value.lineWidth = 8
      ctx.value.strokeStyle = props.highContrastMode ? '#000000' : '#333333'

      // Restore content if we saved it
      if (savedContent) {
        try {
          ctx.value.putImageData(savedContent, 0, 0)
        } catch (e) {
          // Ignore if we can't restore
        }
      }
    }

    const clearCanvas = () => {
      if (!ctx.value || !canvas.value) return

      const rect = canvas.value.getBoundingClientRect()
      ctx.value.clearRect(0, 0, rect.width, rect.height)
      hasDrawnOnCanvas.value = false
      strokeState.value = 'waiting'
      strokeFeedback.value = null
      userStrokePoints.value = []
    }

    const saveCanvasState = () => {
      if (!ctx.value || !canvas.value) return
      canvasStateBeforeStroke.value = ctx.value.getImageData(
        0, 0,
        canvas.value.width,
        canvas.value.height
      )
    }

    const restoreCanvasState = () => {
      if (!ctx.value || !canvas.value || !canvasStateBeforeStroke.value) return
      ctx.value.putImageData(canvasStateBeforeStroke.value, 0, 0)
      canvasStateBeforeStroke.value = null
    }

    const showFeedback = (valid, feedback) => {
      strokeFeedback.value = { valid, feedback }
      if (feedbackTimeout) clearTimeout(feedbackTimeout)
      feedbackTimeout = setTimeout(() => {
        strokeFeedback.value = null
      }, valid ? 1000 : 2000)
    }

    const loadStrokeData = async () => {
      try {
        // Use the stroke extraction service which handles static JSON files
        const data = await getStrokesLegacy(props.character, props.selectedFont)
        strokeData.value = data?.strokes || []
      } catch (error) {
        console.error('Failed to load stroke data:', error)
        strokeData.value = []
      }
    }

    const getDiamondPoints = (cx, cy, size) => {
      return `${cx},${cy - size} ${cx + size},${cy} ${cx},${cy + size} ${cx - size},${cy}`
    }

    const getDirectionArrow = () => {
      if (!currentStrokeData.value || !currentStrokeData.value.points || currentStrokeData.value.points.length < 2) {
        return ''
      }
      const points = currentStrokeData.value.points
      const lastIdx = points.length - 1
      const endX = scaleCoord(points[lastIdx][0])
      const endY = scaleCoord(points[lastIdx][1])
      const prevX = scaleCoord(points[lastIdx - 1][0])
      const prevY = scaleCoord(points[lastIdx - 1][1])

      // Calculate direction vector
      const dx = endX - prevX
      const dy = endY - prevY
      const len = Math.sqrt(dx * dx + dy * dy)
      if (len === 0) return ''

      // Normalize and create arrow
      const nx = dx / len
      const ny = dy / len
      const arrowLen = 15
      const arrowWidth = 8

      // Arrow tip at end zone edge
      const tipX = endX - nx * (props.strokeTolerance * canvasSize * 0.4 + 5)
      const tipY = endY - ny * (props.strokeTolerance * canvasSize * 0.4 + 5)
      const baseX = tipX - nx * arrowLen
      const baseY = tipY - ny * arrowLen

      // Perpendicular for arrow wings
      const px = -ny * arrowWidth
      const py = nx * arrowWidth

      return `M ${baseX + px},${baseY + py} L ${tipX},${tipY} L ${baseX - px},${baseY - py}`
    }

    const validateStrokeLocally = () => {
      const stroke = currentStrokeData.value
      const points = userStrokePoints.value
      if (!stroke || points.length < 3) {
        return { valid: false, feedback: 'Draw a longer line!' }
      }

      const startPoint = points[0]
      const endPoint = points[points.length - 1]
      const tolerance = getToleranceInPixels()

      // Check start zone
      const startZone = stroke.points[0]
      const startCenter = strokeToPixelCoords(startZone[0], startZone[1])
      const startDist = Math.sqrt(
        Math.pow(startPoint.x - startCenter.x, 2) +
        Math.pow(startPoint.y - startCenter.y, 2)
      )
      const startedCorrectly = startDist <= tolerance

      // Check end zone
      const endZone = stroke.points[stroke.points.length - 1]
      const endCenter = strokeToPixelCoords(endZone[0], endZone[1])
      const endDist = Math.sqrt(
        Math.pow(endPoint.x - endCenter.x, 2) +
        Math.pow(endPoint.y - endCenter.y, 2)
      )
      const endedCorrectly = endDist <= tolerance

      if (startedCorrectly && endedCorrectly) {
        return { valid: true, feedback: 'Great!' }
      } else if (!startedCorrectly) {
        return { valid: false, feedback: 'Start in the green circle!' }
      } else {
        return { valid: false, feedback: 'End in the orange circle!' }
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
      // For touchstart/touchmove, use e.touches
      if (e.touches && e.touches.length > 0) {
        return {
          x: e.touches[0].clientX - rect.left,
          y: e.touches[0].clientY - rect.top
        }
      }
      // For touchend, use e.changedTouches (e.touches is empty when finger is lifted)
      if (e.changedTouches && e.changedTouches.length > 0) {
        return {
          x: e.changedTouches[0].clientX - rect.left,
          y: e.changedTouches[0].clientY - rect.top
        }
      }
      // For mouse events
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
    }

    // Get the SVG scaling info for coordinate conversion
    // Accounts for preserveAspectRatio="xMidYMid meet"
    const getSvgTransform = () => {
      const rect = canvas.value.getBoundingClientRect()
      const containerWidth = rect.width
      const containerHeight = rect.height

      // SVG viewBox is canvasSize x canvasSize (400x400)
      // With "meet", it scales to fit the smaller dimension
      const svgScale = Math.min(containerWidth, containerHeight) / canvasSize

      // SVG content size after scaling
      const svgDisplaySize = canvasSize * svgScale

      // Centering offsets (xMidYMid)
      const offsetX = (containerWidth - svgDisplaySize) / 2
      const offsetY = (containerHeight - svgDisplaySize) / 2

      return { svgScale, offsetX, offsetY }
    }

    // Convert stroke coordinates (0-100) to pixel coordinates
    const strokeToPixelCoords = (strokeX, strokeY) => {
      const { svgScale, offsetX, offsetY } = getSvgTransform()

      // Convert from 0-100 stroke coords to SVG coords (0-400), then to pixels
      const svgX = strokeX * (canvasSize / 100)
      const svgY = strokeY * (canvasSize / 100)

      return {
        x: svgX * svgScale + offsetX,
        y: svgY * svgScale + offsetY
      }
    }

    // Get the tolerance radius in pixels (matches the SVG circle visual size)
    const getToleranceInPixels = () => {
      const { svgScale } = getSvgTransform()
      // SVG circle radius is: strokeTolerance * canvasSize * 0.4 (in viewBox units)
      // In pixels: multiply by svgScale
      return props.strokeTolerance * canvasSize * 0.4 * svgScale
    }

    const isInZone = (pos, zoneCenter) => {
      const center = strokeToPixelCoords(zoneCenter[0], zoneCenter[1])
      const radius = getToleranceInPixels()
      const dist = Math.sqrt(
        Math.pow(pos.x - center.x, 2) +
        Math.pow(pos.y - center.y, 2)
      )
      return dist <= radius
    }

    const startDrawing = (e) => {
      const pos = getEventPos(e)

      if (props.guidedMode && currentStrokeData.value) {
        const startPoint = currentStrokeData.value.points[0]
        if (!isInZone(pos, startPoint)) {
          return
        }
        // Save canvas state before starting stroke
        saveCanvasState()
        userStrokePoints.value = [pos]
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

      // Track stroke points in guided mode
      if (props.guidedMode && strokeState.value === 'drawing') {
        userStrokePoints.value.push(pos)
      }

      lastX.value = pos.x
      lastY.value = pos.y
    }

    const stopDrawing = (e) => {
      if (!isDrawing.value) return

      if (props.guidedMode && currentStrokeData.value && strokeState.value === 'drawing') {
        const pos = e ? getEventPos(e) : { x: lastX.value, y: lastY.value }
        userStrokePoints.value.push(pos)

        // Validate stroke locally
        const result = validateStrokeLocally()
        const currentStep = props.currentStrokeStep
        const isLastStroke = currentStep + 1 >= strokeData.value.length

        if (result.valid) {
          showFeedback(true, result.feedback)

          // Clear saved state - the stroke is valid and should be kept
          canvasStateBeforeStroke.value = null

          // Delay emit to allow feedback to display and prevent race conditions
          setTimeout(() => {
            if (isLastStroke) {
              emit('guided-complete')
            }
            emit('stroke-completed', currentStep)
          }, 300)
        } else {
          // Invalid stroke - show feedback and restore canvas
          showFeedback(false, result.feedback)
          setTimeout(() => {
            restoreCanvasState()
          }, 500)
        }

        strokeState.value = 'waiting'
        userStrokePoints.value = []
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
        const result = await scoreDrawing(canvas.value, props.character, props.selectedFont, props.debugMode)

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
            },
            debug: true  // Enable debug section display
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
        initCanvas(true)
        loadTraceImage()
        loadStrokeData()
      })
    })

    onUnmounted(() => {
      if (feedbackTimeout) {
        clearTimeout(feedbackTimeout)
      }
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
      completedStrokePaths,
      isCurrentStrokeComplete,
      strokeState,
      fontFamily,
      guidedColors,
      currentInstruction,
      strokeFeedback,
      canvasSize,
      startDrawing,
      draw,
      stopDrawing,
      clearCanvas,
      submitDrawing,
      getTrianglePoints,
      getDiamondPoints,
      getDirectionArrow,
      scaleCoord
    }
  }
}
</script>

<style scoped>
.drawing-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  padding: 15px;
  gap: 15px;
  overflow-y: auto;
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
  position: relative;
  background: white;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  /* Force square aspect ratio so canvas and SVG overlay align */
  width: min(100%, 70vh);
  height: min(100%, 70vh);
  aspect-ratio: 1 / 1;
  flex-shrink: 0;
  align-self: center;
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

.stroke-zone.start-zone.active {
  animation: pulse 1s ease-in-out infinite;
}

.stroke-zone.end-zone.approaching {
  opacity: 0.8;
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

.stroke-completed {
  opacity: 0.4;
}

.stroke-number {
  pointer-events: none;
  user-select: none;
}

.direction-arrow {
  opacity: 0.8;
}

.instruction-box {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.75);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  pointer-events: none;
  z-index: 10;
}

.instruction-text {
  white-space: nowrap;
}

.feedback-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: 700;
  pointer-events: none;
  z-index: 20;
  animation: feedbackPop 0.3s ease-out;
}

.feedback-overlay.valid {
  background: rgba(76, 175, 80, 0.9);
  color: white;
  box-shadow: 0 4px 20px rgba(76, 175, 80, 0.5);
}

.feedback-overlay.invalid {
  background: rgba(244, 67, 54, 0.9);
  color: white;
  box-shadow: 0 4px 20px rgba(244, 67, 54, 0.5);
}

@keyframes feedbackPop {
  0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; }
  50% { transform: translate(-50%, -50%) scale(1.1); }
  100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}

.completion-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(76, 175, 80, 0.95);
  color: white;
  padding: 20px 32px;
  border-radius: 16px;
  text-align: center;
  pointer-events: none;
  z-index: 20;
  box-shadow: 0 8px 30px rgba(76, 175, 80, 0.5);
  animation: completionBounce 0.5s ease-out;
}

.completion-text {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.completion-subtext {
  display: block;
  font-size: 0.9rem;
  opacity: 0.9;
}

@keyframes completionBounce {
  0% { transform: translate(-50%, -50%) scale(0); }
  50% { transform: translate(-50%, -50%) scale(1.1); }
  70% { transform: translate(-50%, -50%) scale(0.95); }
  100% { transform: translate(-50%, -50%) scale(1); }
}

.start-zone-group .start-zone.active {
  animation: startPulse 1.5s ease-in-out infinite;
}

@keyframes startPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
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
