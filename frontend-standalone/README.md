# Learning Letters - Standalone Frontend

A fully offline-capable learning application for teaching children to write letters and numbers. This version runs entirely in the browser with no backend required.

## Features

- **Offline Support**: Works completely offline as a PWA
- **WASM Scoring**: Fast, accurate character recognition using Rust/WebAssembly
- **Multiple Drawing Modes**: Freestyle, Tracing, and Step-by-Step guided modes
- **Multiplayer**: Up to 4 players can compete locally
- **Accessibility**: High contrast mode, color blind support, adjustable text size
- **Mobile Ready**: iOS and Android via Capacitor

## Technology Stack

- **Frontend**: Vue.js 3 + TypeScript + Vite
- **Scoring Engine**: Rust compiled to WebAssembly
- **Mobile**: Capacitor for iOS/Android
- **Offline**: PWA with Service Worker

## Prerequisites

- Node.js 18+
- Rust toolchain with `wasm-pack` (for building WASM)
- Xcode (for iOS builds)
- Android Studio (for Android builds)

## Installation

```bash
# Install dependencies
npm install

# Install wasm-pack (if not already installed)
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
```

## Development

```bash
# Build WASM module (first time or after Rust changes)
npm run wasm:build

# Start development server
npm run dev
```

Open http://localhost:7002 in your browser.

## Building for Production

```bash
# Full build (WASM + Vue)
npm run build

# Preview production build
npm run preview
```

## Mobile Development

### iOS

```bash
# Add iOS platform (first time only)
npm run cap:add:ios

# Build and sync
npm run build:ios

# Open in Xcode
npm run cap:open:ios
```

### Android

```bash
# Add Android platform (first time only)
npm run cap:add:android

# Build and sync
npm run build:android

# Open in Android Studio
npm run cap:open:android
```

## Project Structure

```
frontend-standalone/
├── src/
│   ├── wasm-scoring/      # Rust WASM scoring engine
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── scoring.rs
│   │       └── image_ops.rs
│   ├── components/        # Vue components
│   ├── composables/       # Vue composables
│   ├── services/          # TypeScript services
│   │   ├── scoring.ts     # WASM wrapper
│   │   ├── storage.ts     # localStorage service
│   │   └── audio.ts       # Audio playback
│   ├── App.vue
│   └── main.ts
├── public/
│   ├── fonts/            # TTF font files
│   ├── strokes/          # Stroke data JSON
│   └── audio/            # Audio files by voice
├── capacitor.config.ts   # Mobile config
├── vite.config.ts
└── package.json
```

## Storage

All data is stored locally:
- **Progress**: High scores per character/font/mode
- **Settings**: User preferences (font, voice, modes)
- **Multiplayer**: Saved player configurations

Data is stored in `localStorage` and persists across sessions.

## Bundle Size

| Component | Size (gzipped) |
|-----------|----------------|
| Vue + Vite bundle | ~50KB |
| WASM scoring | ~150KB |
| Fonts (5 TTF) | ~300KB |
| Stroke data | ~30KB |
| Audio (4 voices) | ~9MB |
| **Total** | **~10MB** |

## License

MIT
