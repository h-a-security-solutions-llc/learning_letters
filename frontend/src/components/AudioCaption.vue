<template>
  <Transition name="caption-fade">
    <div v-if="isVisible && caption" class="audio-caption-toast" role="status" aria-live="polite">
      <span class="caption-icon">🔊</span>
      <span class="caption-character">{{ caption.text }}</span>
      <span class="caption-phonetic">"{{ caption.phonetic }}"</span>
    </div>
  </Transition>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'
import type { CharacterCaption } from '@/composables/useAudioCaptions'

export default defineComponent({
  name: 'AudioCaption',
  props: {
    caption: {
      type: Object as PropType<CharacterCaption | null>,
      default: null
    },
    isVisible: {
      type: Boolean,
      default: false
    }
  }
})
</script>

<style scoped>
.audio-caption-toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.85);
  color: white;
  border-radius: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  font-family: 'Fredoka', sans-serif;
}

.caption-icon {
  font-size: 1.5rem;
}

.caption-character {
  font-size: 2rem;
  font-weight: 700;
}

.caption-phonetic {
  font-size: 1rem;
  color: #aaa;
  font-style: italic;
}

/* Fade transition */
.caption-fade-enter-active,
.caption-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.caption-fade-enter-from,
.caption-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

.caption-fade-enter-to,
.caption-fade-leave-from {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

@media (max-width: 600px) {
  .audio-caption-toast {
    bottom: 15px;
    padding: 10px 20px;
    gap: 10px;
  }

  .caption-icon {
    font-size: 1.2rem;
  }

  .caption-character {
    font-size: 1.5rem;
  }

  .caption-phonetic {
    font-size: 0.85rem;
  }
}
</style>
