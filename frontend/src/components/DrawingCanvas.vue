<template>
  <div class="drawing-container">
    <!-- Character Display -->
    <div class="character-display">
      <span class="current-char">{{ character }}</span>
      <span class="char-info">Draw this {{ charType }}!</span>
    </div>

    <!-- Canvas Area -->
    <div class="canvas-wrapper" ref="canvasWrapper">
      <!-- Tracing Guide Layer -->
      <svg
        v-if="tracingMode && strokeData"
        class="tracing-layer"
        :viewBox="`0 0 ${canvasSize} ${canvasSize}`"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- Character outline -->
        <text
          :x="canvasSize / 2"
          :y="canvasSize * 0.75"
          text-anchor="middle"
          :font-size="canvasSize * 0.7"
          fill="none"
          stroke="#ddd"
          stroke-width="2"
          stroke-dasharray="10,5"
          font-family="'Fredoka', sans-serif"
        >
          {{ character }}
        </text>

        <!-- Stroke paths with arrows -->
        <g v-for="(stroke, index) in strokeData.strokes" :key="index">
          <polyline
            :points="getScaledPoints(stroke.points)"
            fill="none"
            stroke="#4ECDC4"
            stroke-width="4"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-dasharray="15,10"
            class="stroke-path"
          />
          <!-- Arrow at start -->
          <circle
            :cx="getScaledPoint(stroke.points[0])[0]"
            :cy="getScaledPoint(stroke.points[0])[1]"
            r="12"
            fill="#FF6B6B"
            class="start-marker"
          />
          <text
            :x="getScaledPoint(stroke.points[0])[0]"
            :y="getScaledPoint(stroke.points[0])[1] + 5"
            text-anchor="middle"
            fill="white"
            font-size="14"
            font-weight="bold"
          >
            {{ index + 1 }}
          </text>
          <!-- Arrow showing direction -->
          <polygon
            :points="getArrowPoints(stroke.points)"
            fill="#4ECDC4"
            class="direction-arrow"
          />
        </g>
      </svg>

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
      <button class="control-btn trace-btn" :class="{ active: tracingMode }" @click="$emit('toggle-tracing')">
        <span class="btn-icon">✏️</span>
        <span class="btn-text">{{ tracingMode ? 'Hide Guide' : 'Show Guide' }}</span>
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
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
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
    }
  },
  emits: ['submit', 'toggle-tracing'],
  setup(props, { emit }) {
    const canvas = ref(null)
    const canvasWrapper = ref(null)
    const ctx = ref(null)
    const isDrawing = ref(false)
    const isSubmitting = ref(false)
    const lastX = ref(0)
    const lastY = ref(0)
    const canvasSize = ref(400)
    const strokeData = ref(null)

    const charType = computed(() => {
      if (/[A-Z]/.test(props.character)) return 'uppercase letter'
      if (/[a-z]/.test(props.character)) return 'lowercase letter'
      return 'number'
    })

    const fetchStrokeData = async () => {
      try {
        const response = await axios.get(`/api/characters/${encodeURIComponent(props.character)}`)
        strokeData.value = response.data
      } catch (error) {
        console.error('Failed to fetch stroke data:', error)
      }
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
    }

    const stopDrawing = () => {
      isDrawing.value = false
    }

    const handleTouchStart = (e) => {
      const touch = e.touches[0]
      const coords = getCanvasCoords(touch.clientX, touch.clientY)
      isDrawing.value = true
      lastX.value = coords.x
      lastY.value = coords.y
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
    }

    const clearCanvas = () => {
      ctx.value.fillStyle = 'white'
      ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
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
        clearCanvas()
        fetchStrokeData()
      })
    })

    return {
      canvas,
      canvasWrapper,
      canvasSize,
      charType,
      strokeData,
      isSubmitting,
      startDrawing,
      draw,
      stopDrawing,
      handleTouchStart,
      handleTouchMove,
      clearCanvas,
      submitDrawing,
      getScaledPoint,
      getScaledPoints,
      getArrowPoints
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

.char-info {
  color: white;
  font-size: 1.3rem;
  font-weight: 500;
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

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.8; }
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
