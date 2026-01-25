# Learning Letters - iOS & Android Mobile Build Guide

This guide covers converting the Learning Letters Vue.js web application to native iOS and Android apps using Capacitor.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Developer Account Registration](#developer-account-registration)
3. [Capacitor Setup](#capacitor-setup)
4. [iOS Configuration](#ios-configuration)
5. [Android Configuration](#android-configuration)
6. [Environment Configuration](#environment-configuration)
7. [Building for Development](#building-for-development)
8. [Building for Production](#building-for-production)
9. [App Store Submission](#app-store-submission)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Hardware

| Platform | Requirement |
|----------|-------------|
| iOS | macOS computer (Mac Mini, MacBook, iMac, etc.) |
| Android | Any OS (macOS, Windows, Linux) |
| Both | macOS is the only OS that can build for both platforms |

### Required Software

#### macOS Setup

```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Node.js (if not installed)
brew install node

# 3. Install Xcode from Mac App Store
# Open App Store and search for "Xcode", then install

# 4. After Xcode installation, install command line tools
xcode-select --install

# 5. Accept Xcode license
sudo xcodebuild -license accept

# 6. Install CocoaPods (iOS dependency manager)
sudo gem install cocoapods

# 7. Install Android Studio
brew install --cask android-studio
```

#### Android Studio Configuration

After installing Android Studio:

1. Open Android Studio
2. Go to **Preferences** → **Appearance & Behavior** → **System Settings** → **Android SDK**
3. Install the following SDK components:
   - **SDK Platforms tab:**
     - Android 14.0 (API 34) - or latest stable
     - Android 13.0 (API 33)
   - **SDK Tools tab:**
     - Android SDK Build-Tools
     - Android SDK Command-line Tools
     - Android Emulator
     - Android SDK Platform-Tools

4. Set environment variables (add to `~/.zshrc` or `~/.bash_profile`):

```bash
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
```

5. Reload shell: `source ~/.zshrc`

#### Verify Installation

```bash
# Check Node.js
node --version  # Should be 18+ recommended

# Check npm
npm --version

# Check Xcode
xcodebuild -version

# Check Android SDK
echo $ANDROID_HOME
adb --version

# Check CocoaPods
pod --version
```

---

## Developer Account Registration

### Apple Developer Program

**Cost:** $99/year (individual) or $299/year (organization)

**Registration Steps:**

1. Go to [developer.apple.com/programs/enroll](https://developer.apple.com/programs/enroll/)
2. Sign in with your Apple ID (or create one)
3. Choose account type:
   - **Individual:** For personal apps, uses your name as publisher
   - **Organization:** For company apps, requires D-U-N-S number
4. Complete identity verification (may require government ID)
5. Pay annual fee
6. Wait for approval (usually 24-48 hours, organizations may take longer)

**Post-Registration Setup:**

1. Log into [App Store Connect](https://appstoreconnect.apple.com/)
2. Accept all agreements under **Agreements, Tax, and Banking**
3. Set up banking information for payments
4. Create an App ID in the [Developer Portal](https://developer.apple.com/account/):
   - Go to **Certificates, Identifiers & Profiles**
   - Click **Identifiers** → **+**
   - Select **App IDs** → **App**
   - Enter description: "Learning Letters"
   - Bundle ID: `io.tellaro.learningletters` (or your domain reversed)
   - Select capabilities: None required for this app

### Google Play Developer Account

**Cost:** $25 one-time fee

**Registration Steps:**

1. Go to [play.google.com/console/signup](https://play.google.com/console/signup)
2. Sign in with a Google account
3. Accept the Developer Distribution Agreement
4. Pay the $25 registration fee
5. Complete account details:
   - Developer name (shown on Play Store)
   - Contact email
   - Website (optional)
6. Verify identity (required since 2023):
   - Personal accounts: Government ID
   - Organization accounts: Business documents + D-U-N-S number

**Post-Registration Setup:**

1. Set up a Google Cloud project for any APIs needed
2. Configure payments in the Play Console
3. Create your app listing (can be done before app is ready)

---

## Capacitor Setup

### Install Capacitor

From the `frontend` directory:

```bash
cd /home/jhenderson/projects/learning_letters/frontend

# Install Capacitor core and CLI
npm install @capacitor/core @capacitor/cli

# Initialize Capacitor
npx cap init "Learning Letters" "io.tellaro.learningletters" --web-dir dist
```

This creates `capacitor.config.ts` in the project root.

### Configure Capacitor

Edit `capacitor.config.ts`:

```typescript
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'io.tellaro.learningletters',
  appName: 'Learning Letters',
  webDir: 'dist',
  server: {
    // For development, you can use live reload:
    // url: 'http://YOUR_DEV_MACHINE_IP:7001',
    // cleartext: true,

    // For production, leave these commented out
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#FFFFFF',
      showSpinner: false
    },
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true
    }
  },
  ios: {
    contentInset: 'automatic'
  },
  android: {
    allowMixedContent: false
  }
};

export default config;
```

### Add Platform Support

```bash
# Install platform packages
npm install @capacitor/ios @capacitor/android

# Add iOS platform (macOS only)
npx cap add ios

# Add Android platform
npx cap add android
```

This creates `ios/` and `android/` directories with native projects.

### Install Recommended Plugins

```bash
# Splash screen and status bar
npm install @capacitor/splash-screen @capacitor/status-bar

# Haptic feedback (optional, for touch interactions)
npm install @capacitor/haptics

# App info (version, etc.)
npm install @capacitor/app
```

---

## iOS Configuration

### Project Structure

After running `npx cap add ios`, you'll have:

```
ios/
├── App/
│   ├── App/
│   │   ├── Assets.xcassets/      # App icons, splash screens
│   │   ├── Info.plist            # App configuration
│   │   └── capacitor.config.json # Capacitor config copy
│   ├── App.xcodeproj/            # Xcode project
│   └── Podfile                   # CocoaPods dependencies
```

### App Icons

Create app icons in various sizes. Use a tool like [App Icon Generator](https://appicon.co/) with a 1024x1024 source image.

Required sizes for iOS:
- 20x20 (1x, 2x, 3x)
- 29x29 (1x, 2x, 3x)
- 40x40 (1x, 2x, 3x)
- 60x60 (2x, 3x)
- 76x76 (1x, 2x)
- 83.5x83.5 (2x)
- 1024x1024 (App Store)

Place in `ios/App/App/Assets.xcassets/AppIcon.appiconset/`

### Splash Screen

Create splash screen images or use a single adaptive image:

1. Create a 2732x2732 centered logo image
2. Place in `ios/App/App/Assets.xcassets/Splash.imageset/`
3. Configure background color in `capacitor.config.ts`

### Info.plist Configuration

Edit `ios/App/App/Info.plist` to add required permissions and settings:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- App Transport Security - Allow your API domain -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>learning.tellaro.io</key>
            <dict>
                <key>NSExceptionAllowsInsecureHTTPLoads</key>
                <false/>
                <key>NSIncludesSubdomains</key>
                <true/>
            </dict>
        </dict>
    </dict>

    <!-- Display name -->
    <key>CFBundleDisplayName</key>
    <string>Learning Letters</string>

    <!-- Supported orientations -->
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>

    <!-- Status bar style -->
    <key>UIStatusBarStyle</key>
    <string>UIStatusBarStyleDefault</string>
    <key>UIViewControllerBasedStatusBarAppearance</key>
    <true/>
</dict>
</plist>
```

### Signing Configuration

1. Open Xcode: `npx cap open ios`
2. Select the **App** target
3. Go to **Signing & Capabilities** tab
4. Select your Team (Apple Developer account)
5. Xcode will automatically manage signing

---

## Android Configuration

### Project Structure

After running `npx cap add android`, you'll have:

```
android/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── AndroidManifest.xml    # App configuration
│   │       ├── java/                   # Native code
│   │       └── res/                    # Resources (icons, etc.)
│   └── build.gradle                    # App-level build config
├── build.gradle                        # Project-level build config
└── gradle.properties                   # Gradle settings
```

### App Icons

Create adaptive icons for Android. Use [Android Asset Studio](https://romannurik.github.io/AndroidAssetStudio/icons-launcher.html).

Required resources:
- `mipmap-mdpi/` (48x48)
- `mipmap-hdpi/` (72x72)
- `mipmap-xhdpi/` (96x96)
- `mipmap-xxhdpi/` (144x144)
- `mipmap-xxxhdpi/` (192x192)

Place in `android/app/src/main/res/`

### AndroidManifest.xml Configuration

Edit `android/app/src/main/AndroidManifest.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Internet permission (required for API calls) -->
    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/AppTheme"
        android:usesCleartextTraffic="false">

        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|locale|smallestScreenSize|screenLayout|uiMode"
            android:exported="true"
            android:launchMode="singleTask"
            android:theme="@style/AppTheme.NoActionBarLaunch">

            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

### Network Security Configuration

Create `android/app/src/main/res/xml/network_security_config.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- Allow your production API domain -->
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">learning.tellaro.io</domain>
    </domain-config>

    <!-- For development only - allow localhost -->
    <!-- Remove this block for production builds -->
    <!--
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">localhost</domain>
    </domain-config>
    -->
</network-security-config>
```

Reference in AndroidManifest.xml:
```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

### Signing Configuration (Release Builds)

1. Generate a keystore:

```bash
keytool -genkey -v -keystore learning-letters-release.keystore \
  -alias learning-letters -keyalg RSA -keysize 2048 -validity 10000
```

2. Store keystore securely (DO NOT commit to git)

3. Create `android/keystore.properties` (add to .gitignore):

```properties
storePassword=your_keystore_password
keyPassword=your_key_password
keyAlias=learning-letters
storeFile=../learning-letters-release.keystore
```

4. Update `android/app/build.gradle`:

```groovy
def keystorePropertiesFile = rootProject.file("keystore.properties")
def keystoreProperties = new Properties()
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    signingConfigs {
        release {
            if (keystorePropertiesFile.exists()) {
                keyAlias keystoreProperties['keyAlias']
                keyPassword keystoreProperties['keyPassword']
                storeFile file(keystoreProperties['storeFile'])
                storePassword keystoreProperties['storePassword']
            }
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

---

## Environment Configuration

The app uses `VITE_LEARNING_API_BASE` environment variable for the backend URL.

### Environment Files

Environment files are **gitignored** to prevent committing secrets. Use `.env.example` as a template.

**Setup:**
```bash
# For production builds
cp .env.example .env

# For local development
cp .env.example .env.development
# Then edit to use: VITE_LEARNING_API_BASE=http://localhost:7000
```

**`.env.example` (template, committed to repo):**
```
VITE_LEARNING_API_BASE=https://learning.tellaro.io
```

**`.env` (production, gitignored):**
```
VITE_LEARNING_API_BASE=https://learning.tellaro.io
# Add any API keys or secrets here
```

**`.env.development` (local dev, gitignored):**
```
VITE_LEARNING_API_BASE=http://localhost:7000
```

**`.env.staging` (optional, gitignored):**
```
VITE_LEARNING_API_BASE=https://staging.learning.tellaro.io
```

### Building for Different Environments

```bash
# Development build (uses .env.development)
npm run dev

# Production build (uses .env)
npm run build

# Staging build (uses .env.staging)
npm run build -- --mode staging
```

### Mobile-Specific Considerations

For mobile development with live reload:

1. Find your machine's local IP: `ifconfig | grep inet`
2. Update `.env.development`:
   ```
   VITE_LEARNING_API_BASE=http://YOUR_IP:7000
   ```
3. Ensure your backend allows CORS from the Capacitor app origin

---

## Building for Development

### Workflow

```bash
# 1. Build the web app
npm run build

# 2. Sync with native projects
npx cap sync

# 3. Open in IDE
npx cap open ios      # Opens Xcode
npx cap open android  # Opens Android Studio
```

### Live Reload (Development)

For faster iteration during development:

1. Start the dev server:
   ```bash
   npm run dev -- --host
   ```

2. Update `capacitor.config.ts`:
   ```typescript
   server: {
     url: 'http://YOUR_MACHINE_IP:7001',
     cleartext: true  // Required for Android HTTP
   }
   ```

3. Run on device/simulator from IDE

4. **Remember to remove the `server.url` config before production builds!**

### Running on iOS Simulator

```bash
# List available simulators
xcrun simctl list devices

# Run on specific simulator
npx cap run ios --target "iPhone 15 Pro"
```

### Running on Android Emulator

```bash
# List available emulators
emulator -list-avds

# Run on specific emulator
npx cap run android --target "Pixel_7_API_34"
```

### Running on Physical Devices

**iOS:**
1. Connect device via USB
2. Trust the computer on the device
3. Select device in Xcode
4. Click Run

**Android:**
1. Enable Developer Options on device (tap Build Number 7 times)
2. Enable USB Debugging
3. Connect via USB
4. Accept debugging prompt on device
5. Select device in Android Studio
6. Click Run

---

## Building for Production

### iOS Production Build

1. **Update version numbers** in Xcode:
   - Select App target → General tab
   - Update Version (e.g., "1.0.0") and Build (e.g., "1")

2. **Build the web app:**
   ```bash
   npm run build
   npx cap sync ios
   ```

3. **Create archive in Xcode:**
   - Select **Product** → **Archive**
   - Wait for build to complete

4. **Upload to App Store Connect:**
   - In the Organizer window, select the archive
   - Click **Distribute App**
   - Select **App Store Connect**
   - Follow prompts to upload

### Android Production Build

1. **Update version numbers** in `android/app/build.gradle`:
   ```groovy
   android {
       defaultConfig {
           versionCode 1        // Increment for each release
           versionName "1.0.0"  // User-visible version
       }
   }
   ```

2. **Build the web app:**
   ```bash
   npm run build
   npx cap sync android
   ```

3. **Generate signed APK/AAB:**

   Via command line:
   ```bash
   cd android
   ./gradlew bundleRelease  # Creates .aab for Play Store
   # or
   ./gradlew assembleRelease  # Creates .apk
   ```

   Output location: `android/app/build/outputs/bundle/release/app-release.aab`

   Or via Android Studio:
   - **Build** → **Generate Signed Bundle / APK**
   - Select **Android App Bundle**
   - Select keystore and enter credentials
   - Select **release** build variant
   - Click **Finish**

---

## App Store Submission

### Apple App Store

1. **Prepare App Store Connect listing:**
   - Log into [App Store Connect](https://appstoreconnect.apple.com/)
   - Create new app with your Bundle ID
   - Fill in required information:
     - App name, subtitle, description
     - Keywords, categories
     - Screenshots (required sizes below)
     - App icon (1024x1024)
     - Privacy policy URL
     - Age rating questionnaire

2. **Required screenshots:**
   - 6.7" (iPhone 15 Pro Max): 1290 x 2796
   - 6.5" (iPhone 14 Plus): 1284 x 2778
   - 5.5" (iPhone 8 Plus): 1242 x 2208
   - 12.9" iPad Pro: 2048 x 2732

3. **Submit for review:**
   - Select build uploaded from Xcode
   - Answer export compliance questions
   - Submit for review

4. **Review timeline:** Usually 24-48 hours for initial review

### Google Play Store

1. **Prepare Play Console listing:**
   - Log into [Play Console](https://play.google.com/console/)
   - Create new app
   - Fill in required information:
     - App name, description (short & full)
     - Screenshots, feature graphic
     - App icon (512x512)
     - Privacy policy URL
     - Content rating questionnaire
     - Target audience declaration

2. **Required graphics:**
   - Screenshots: At least 2, up to 8 per device type
   - Feature graphic: 1024 x 500
   - App icon: 512 x 512

3. **Upload AAB:**
   - Go to **Production** → **Releases**
   - Create new release
   - Upload your `.aab` file
   - Add release notes
   - Review and roll out

4. **Review timeline:** Usually 1-3 days for new apps

---

## Troubleshooting

### Common iOS Issues

**"No signing certificate" error:**
```bash
# Reset Xcode signing
cd ios/App
rm -rf Pods Podfile.lock
pod install
```
Then re-select your team in Xcode.

**CocoaPods issues:**
```bash
sudo gem install cocoapods
cd ios/App
pod repo update
pod install
```

**Build fails after Xcode update:**
```bash
sudo xcode-select --reset
sudo xcodebuild -license accept
```

### Common Android Issues

**"SDK location not found" error:**
Create/edit `android/local.properties`:
```properties
sdk.dir=/Users/YOUR_USERNAME/Library/Android/sdk
```

**Gradle build fails:**
```bash
cd android
./gradlew clean
./gradlew build
```

**"INSTALL_FAILED_INSUFFICIENT_STORAGE" on emulator:**
- Wipe emulator data in AVD Manager
- Or increase emulator storage in AVD settings

### Common Capacitor Issues

**Changes not reflecting in app:**
```bash
npm run build
npx cap sync
# Then rebuild in IDE
```

**Plugin not working:**
```bash
npx cap sync
# For iOS, also run:
cd ios/App && pod install
```

**Web assets out of sync:**
```bash
npx cap copy  # Faster than sync, only copies web assets
```

### Debugging Tips

**iOS Safari Web Inspector:**
1. Enable on device: Settings → Safari → Advanced → Web Inspector
2. Connect device to Mac
3. Open Safari on Mac → Develop menu → Select device → Select app

**Android Chrome DevTools:**
1. Enable USB debugging on device
2. Connect device
3. Open Chrome on computer → `chrome://inspect`
4. Click "inspect" under your app's WebView

---

## Quick Reference Commands

```bash
# === Development ===
npm run dev                    # Start dev server
npm run build                  # Production build
npx cap sync                   # Sync web to native
npx cap copy                   # Copy web assets only (faster)

# === iOS ===
npx cap open ios              # Open in Xcode
npx cap run ios               # Build and run on simulator
npx cap run ios --target "iPhone 15"  # Specific simulator

# === Android ===
npx cap open android          # Open in Android Studio
npx cap run android           # Build and run on emulator
npx cap run android --target "Pixel_7_API_34"  # Specific emulator

# === Debugging ===
npx cap doctor                # Check for issues
adb logcat                    # Android logs
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-24 | 1.0 | Initial guide created |

---

## Resources

- [Capacitor Documentation](https://capacitorjs.com/docs)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [Android Developer Documentation](https://developer.android.com/docs)
- [Vue.js Documentation](https://vuejs.org/)
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play Policy Center](https://play.google.com/about/developer-content-policy/)
