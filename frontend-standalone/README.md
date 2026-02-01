# Learning Letters - Standalone Frontend

A fully offline-capable learning application for teaching children to write letters and numbers. This version runs entirely in the browser with no backend required.

## Features

- **Offline Support**: Works completely offline as a PWA
- **WASM Scoring**: Fast, accurate character recognition using Rust/WebAssembly
- **Multiple Drawing Modes**: Freestyle, Tracing, and Step-by-Step guided modes
- **Multiplayer**: Up to 4 players can compete locally
- **Accessibility**: High contrast mode, color blind support, adjustable text size, audio captions
- **Mobile Ready**: iOS and Android via Capacitor

## Technology Stack

- **Frontend**: Vue.js 3 + TypeScript + Vite
- **Scoring Engine**: Rust compiled to WebAssembly
- **Mobile**: Capacitor for iOS/Android
- **Offline**: PWA with Service Worker

## Prerequisites

### For Development
- Node.js 18+
- npm 9+

### For WASM Development
- Rust toolchain (install via [rustup](https://rustup.rs/))
- `wasm-pack` tool

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install wasm-pack
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
```

### For iOS Development
- macOS with Xcode 14+
- Xcode Command Line Tools
- CocoaPods (`sudo gem install cocoapods`)
- Apple Developer account (for device testing)

### For Android Development
- Android Studio (Arctic Fox or later)
- Android SDK 33+
- JDK 17+
- For device testing: USB debugging enabled on device

## Installation

```bash
cd frontend-standalone

# Install Node.js dependencies
npm install

# Build WASM module (required before first run)
npm run wasm:build
```

## Development

### Running Locally

```bash
# Start development server (requires WASM to be built first)
npm run dev
```

Open http://localhost:7002 in your browser.

### Build Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Full production build (WASM + Vue) |
| `npm run build:quick` | Vue build only (skip WASM) |
| `npm run preview` | Preview production build locally |
| `npm run wasm:build` | Build WASM module (release) |
| `npm run wasm:build:dev` | Build WASM module (debug) |
| `npm run wasm:clean` | Remove built WASM files |
| `npm run test` | Run unit tests in watch mode |
| `npm run test:run` | Run unit tests once |
| `npm run lint` | Check for linting errors |
| `npm run type-check` | TypeScript type checking |

## Testing

### Running Tests

```bash
# Run all tests in watch mode
npm run test

# Run tests once (CI mode)
npm run test:run

# Run tests with coverage
npm run test -- --coverage
```

### Test Structure

```
src/
├── services/__tests__/       # Service unit tests
│   ├── storage.test.ts
│   └── audio.test.ts
├── components/__tests__/     # Component tests
│   └── AudioCaption.test.ts
└── wasm-scoring/src/         # Rust tests (run via cargo test)
```

### Running Rust Tests

```bash
cd src/wasm-scoring
cargo test
```

## Building for Production

```bash
# Full build (WASM + Vue + PWA)
npm run build

# Preview production build locally
npm run preview
```

The production build is output to the `dist/` directory.

## Mobile Deployment

### iOS Deployment

#### Initial Setup (First Time Only)

```bash
# Build the web assets first
npm run build

# Add iOS platform
npm run cap:add:ios

# Open in Xcode to configure signing
npm run cap:open:ios
```

#### Configure Signing in Xcode

1. In Xcode, select the project in the navigator
2. Select the "App" target
3. Go to "Signing & Capabilities" tab
4. Select your Team from the dropdown
5. Xcode will automatically manage signing

#### Building and Running

```bash
# Build and sync to iOS
npm run build:ios

# Open in Xcode
npm run cap:open:ios
```

**To run on a physical device:**
1. Connect your iOS device via USB
2. In Xcode, select your device from the device dropdown (top of window)
3. Click the Run button (play icon) or press Cmd+R
4. First time: Trust the developer certificate on your device (Settings > General > VPN & Device Management)

**To run on Simulator:**
1. In Xcode, select a simulator from the device dropdown
2. Click Run or press Cmd+R

#### Creating an IPA for Distribution

1. In Xcode, select "Any iOS Device" as the target
2. Go to Product > Archive
3. Once archived, click "Distribute App" in the Organizer
4. Follow the prompts for App Store, Ad Hoc, or Enterprise distribution

### Android Deployment

#### Initial Setup (First Time Only)

```bash
# Build the web assets first
npm run build

# Add Android platform
npm run cap:add:android

# Open in Android Studio
npm run cap:open:android
```

#### Building and Running

```bash
# Build and sync to Android
npm run build:android

# Open in Android Studio
npm run cap:open:android
```

**To run on a physical device:**
1. Enable Developer Options on your Android device:
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times
2. Enable USB Debugging:
   - Go to Settings > Developer Options
   - Enable "USB Debugging"
3. Connect device via USB
4. In Android Studio, select your device from the dropdown
5. Click Run or press Shift+F10

**To run on Emulator:**
1. In Android Studio, open AVD Manager (Tools > Device Manager)
2. Create a virtual device if none exists
3. Select the emulator from the device dropdown
4. Click Run

#### Creating an APK/AAB for Distribution

**Debug APK (for testing):**
1. In Android Studio: Build > Build Bundle(s) / APK(s) > Build APK(s)
2. Find APK at: `android/app/build/outputs/apk/debug/app-debug.apk`

**Release APK (for distribution):**
1. Generate a signing key (first time):
   ```bash
   keytool -genkey -v -keystore learning-letters.keystore -alias learning-letters -keyalg RSA -keysize 2048 -validity 10000
   ```
2. In Android Studio: Build > Generate Signed Bundle / APK
3. Choose APK or Android App Bundle
4. Enter keystore details
5. Select "release" build variant

**For Google Play Store:**
- Use Android App Bundle (AAB) format
- Configure `android/app/build.gradle` with your signing config

### Capacitor Commands Reference

| Command | Description |
|---------|-------------|
| `npm run cap:add:ios` | Add iOS platform |
| `npm run cap:add:android` | Add Android platform |
| `npm run cap:sync` | Sync web assets to native projects |
| `npm run cap:open:ios` | Open iOS project in Xcode |
| `npm run cap:open:android` | Open Android project in Android Studio |
| `npm run build:ios` | Build & sync for iOS |
| `npm run build:android` | Build & sync for Android |

### Troubleshooting Mobile Builds

#### iOS Issues

**"No signing certificate" error:**
- Ensure you're logged into Xcode with your Apple ID
- Go to Xcode > Preferences > Accounts and add your Apple ID

**"Untrusted Developer" on device:**
- On device: Settings > General > VPN & Device Management > Trust your developer certificate

**Pod install fails:**
```bash
cd ios/App
pod install --repo-update
```

#### Android Issues

**"SDK location not found" error:**
- Create `android/local.properties` with:
  ```
  sdk.dir=/path/to/your/Android/sdk
  ```

**Gradle sync fails:**
- In Android Studio: File > Sync Project with Gradle Files
- Try: File > Invalidate Caches and Restart

**Device not showing:**
- Ensure USB debugging is enabled
- Try different USB cable/port
- Run `adb devices` to check connection

## Project Structure

```
frontend-standalone/
├── src/
│   ├── wasm-scoring/           # Rust WASM scoring engine
│   │   ├── Cargo.toml          # Rust dependencies
│   │   └── src/
│   │       ├── lib.rs          # WASM bindings
│   │       ├── scoring.rs      # Scoring algorithm
│   │       └── image_ops.rs    # Image processing
│   ├── components/             # Vue components
│   │   ├── __tests__/          # Component tests
│   │   ├── DrawingCanvas.vue   # Main drawing canvas
│   │   ├── CharacterSelection.vue
│   │   ├── ResultsDisplay.vue
│   │   ├── SettingsPanel.vue
│   │   ├── MultiplayerSetupWizard.vue
│   │   ├── MultiplayerResultsDisplay.vue
│   │   └── AudioCaption.vue
│   ├── composables/            # Vue composables
│   │   └── useAudioCaptions.ts
│   ├── services/               # TypeScript services
│   │   ├── __tests__/          # Service tests
│   │   ├── scoring.ts          # WASM wrapper
│   │   ├── storage.ts          # localStorage service
│   │   └── audio.ts            # Audio playback
│   ├── App.vue                 # Main application
│   └── main.ts                 # Entry point
├── public/
│   ├── fonts/                  # TTF font files
│   ├── strokes/                # Stroke data JSON
│   └── audio/                  # Audio files by voice
│       ├── rachel/
│       ├── adam/
│       ├── sarah/
│       └── josh/
├── capacitor.config.ts         # Mobile config
├── vite.config.ts              # Build config
├── vitest.config.ts            # Test config
└── package.json
```

## Scoring Algorithm

The scoring system compares user drawings against reference characters using three metrics:

1. **Coverage (35%)**: How much of the reference character is covered by the drawing
2. **Accuracy (35%)**: How accurately the drawing stays within the reference bounds
3. **Similarity (30%)**: Overall shape similarity using IoU and Chamfer distance

### Image Processing Pipeline

1. **Preprocessing**: Extract drawn character, center, and normalize to 128x128
2. **Skeletonization**: Zhang-Suen thinning algorithm extracts stroke skeleton
3. **Line normalization**: Reconstruct strokes with consistent thickness
4. **Distance transform**: Euclidean distance transform for proximity calculations
5. **Score calculation**: Combine coverage, accuracy, and similarity metrics

### Star Ratings

| Score | Stars | Feedback |
|-------|-------|----------|
| 80-100 | 5 | Amazing! Perfect! |
| 65-79 | 4 | Great job! |
| 50-64 | 3 | Good work! |
| 30-49 | 2 | Nice try! |
| 0-29 | 1 | Keep practicing! |

## Storage

All data is stored locally using `localStorage`:

- **Progress**: High scores per character/font/mode
- **Settings**: User preferences (font, voice, modes)
- **Multiplayer**: Saved player configurations

Data persists across sessions and works offline.

## Bundle Size

| Component | Size (gzipped) |
|-----------|----------------|
| Vue + Vite bundle | ~50KB |
| WASM scoring | ~150KB |
| Fonts (5 TTF) | ~300KB |
| Stroke data | ~30KB |
| Audio (4 voices) | ~9MB |
| **Total** | **~10MB** |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm run test:run`
5. Run linting: `npm run lint`
6. Submit a pull request

## License

MIT
