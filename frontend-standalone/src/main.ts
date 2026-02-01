import { createApp } from 'vue'
import App from './App.vue'
import { initScoring, preloadFonts } from './services/scoring'

// Initialize WASM and preload resources
async function init() {
  try {
    // Initialize WASM scoring engine
    await initScoring()

    // Preload default font
    await preloadFonts(['Fredoka-Regular'])
  } catch (error) {
    console.error('Failed to initialize:', error)
  }

  // Mount Vue app
  const app = createApp(App)
  app.mount('#app')
}

init()

// Register service worker for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((error) => {
      console.log('ServiceWorker registration failed:', error)
    })
  })
}
