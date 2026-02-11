#!/usr/bin/env node
/**
 * Generate stroke data for all characters in all fonts
 * Uses the WASM stroke extraction module
 */

import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Characters to process
const UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
const LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'.split('');
const NUMBERS = '0123456789'.split('');
const ALL_CHARS = [...UPPERCASE, ...LOWERCASE, ...NUMBERS];

// Font configurations
const FONTS = [
  { name: 'Schoolbell-Regular', file: 'schoolbell', display: 'Schoolbell' },
  { name: 'Fredoka-Regular', file: 'fredoka', display: 'Fredoka' },
  { name: 'Nunito-Regular', file: 'nunito', display: 'Nunito' },
  { name: 'PatrickHand-Regular', file: 'patrick-hand', display: 'Patrick Hand' },
  { name: 'PlaywriteUS-Regular', file: 'playwrite-us', display: 'Playwrite US' },
];

// Phonetic data for characters
const PHONETICS = {
  'A': { phonetic: 'ay', sound: 'ah as in apple' },
  'B': { phonetic: 'bee', sound: 'buh as in ball' },
  'C': { phonetic: 'see', sound: 'kuh as in cat' },
  'D': { phonetic: 'dee', sound: 'duh as in dog' },
  'E': { phonetic: 'ee', sound: 'eh as in elephant' },
  'F': { phonetic: 'ef', sound: 'fuh as in fish' },
  'G': { phonetic: 'jee', sound: 'guh as in goat' },
  'H': { phonetic: 'aych', sound: 'huh as in hat' },
  'I': { phonetic: 'eye', sound: 'ih as in igloo' },
  'J': { phonetic: 'jay', sound: 'juh as in jump' },
  'K': { phonetic: 'kay', sound: 'kuh as in kite' },
  'L': { phonetic: 'el', sound: 'luh as in lion' },
  'M': { phonetic: 'em', sound: 'muh as in moon' },
  'N': { phonetic: 'en', sound: 'nuh as in nest' },
  'O': { phonetic: 'oh', sound: 'ah as in octopus' },
  'P': { phonetic: 'pee', sound: 'puh as in pig' },
  'Q': { phonetic: 'kyoo', sound: 'kwuh as in queen' },
  'R': { phonetic: 'ar', sound: 'ruh as in rabbit' },
  'S': { phonetic: 'ess', sound: 'sss as in snake' },
  'T': { phonetic: 'tee', sound: 'tuh as in tiger' },
  'U': { phonetic: 'yoo', sound: 'uh as in umbrella' },
  'V': { phonetic: 'vee', sound: 'vuh as in van' },
  'W': { phonetic: 'double-yoo', sound: 'wuh as in water' },
  'X': { phonetic: 'eks', sound: 'ks as in box' },
  'Y': { phonetic: 'why', sound: 'yuh as in yellow' },
  'Z': { phonetic: 'zee', sound: 'zzz as in zebra' },
  '0': { phonetic: 'zero', sound: 'zero' },
  '1': { phonetic: 'one', sound: 'one' },
  '2': { phonetic: 'two', sound: 'two' },
  '3': { phonetic: 'three', sound: 'three' },
  '4': { phonetic: 'four', sound: 'four' },
  '5': { phonetic: 'five', sound: 'five' },
  '6': { phonetic: 'six', sound: 'six' },
  '7': { phonetic: 'seven', sound: 'seven' },
  '8': { phonetic: 'eight', sound: 'eight' },
  '9': { phonetic: 'nine', sound: 'nine' },
};

// Add lowercase phonetics (same as uppercase)
for (const char of LOWERCASE) {
  PHONETICS[char] = PHONETICS[char.toUpperCase()];
}

async function loadWasm() {
  // Dynamic import of the Node.js WASM module
  const wasmPath = join(ROOT, 'src/wasm-pkg-node/learning_letters_scoring.js');
  const wasm = await import(wasmPath);
  return wasm;
}

async function loadFont(fontName) {
  const fontPath = join(ROOT, 'public/fonts', `${fontName}.ttf`);
  const buffer = await readFile(fontPath);
  return new Uint8Array(buffer);
}

function getCharType(char) {
  if (char >= 'A' && char <= 'Z') return 'uppercase';
  if (char >= 'a' && char <= 'z') return 'lowercase';
  if (char >= '0' && char <= '9') return 'number';
  return 'symbol';
}

async function generateStrokesForFont(wasm, fontConfig) {
  console.log(`\n=== Processing ${fontConfig.display} ===`);

  const fontData = await loadFont(fontConfig.name);
  const characters = {};

  let successCount = 0;
  let errorCount = 0;

  for (const char of ALL_CHARS) {
    process.stdout.write(`  ${char}`);

    try {
      // Extract strokes using WASM (use 300px for good detail)
      const result = wasm.extract_strokes(fontData, char, 300);

      if (result && result.strokes && result.strokes.length > 0) {
        // Convert strokes to the expected format
        const strokes = result.strokes.map(stroke => ({
          points: stroke.points.map(p => [Math.round(p[0]), Math.round(p[1])]),
          direction: stroke.direction
        }));

        const phonetic = PHONETICS[char] || { phonetic: char, sound: char };

        characters[char] = {
          type: getCharType(char),
          phonetic: phonetic.phonetic,
          sound: phonetic.sound,
          strokes: strokes
        };

        successCount++;
        process.stdout.write(`✓ `);
      } else {
        console.warn(`\n  Warning: No strokes extracted for '${char}'`);
        errorCount++;
      }
    } catch (err) {
      console.error(`\n  Error extracting '${char}':`, err.message);
      errorCount++;
    }
  }

  console.log(`\n  Done: ${successCount} success, ${errorCount} errors`);

  return {
    font: fontConfig.display,
    version: '2.0',
    description: `Stroke definitions for ${fontConfig.display} font - auto-generated from glyph analysis`,
    characters
  };
}

async function main() {
  console.log('Stroke Data Generator');
  console.log('=====================\n');

  // Parse command line args
  const args = process.argv.slice(2);
  const fontFilter = args.find(a => a.startsWith('--font='))?.split('=')[1];
  const charFilter = args.find(a => a.startsWith('--char='))?.split('=')[1];
  const dryRun = args.includes('--dry-run');

  if (fontFilter) {
    console.log(`Filtering to font: ${fontFilter}`);
  }
  if (charFilter) {
    console.log(`Filtering to char: ${charFilter}`);
  }
  if (dryRun) {
    console.log('Dry run mode - will not save files');
  }

  try {
    console.log('Loading WASM module...');
    const wasm = await loadWasm();
    console.log('WASM loaded successfully');

    const fontsToProcess = fontFilter
      ? FONTS.filter(f => f.name.toLowerCase().includes(fontFilter.toLowerCase()) ||
                          f.file.toLowerCase().includes(fontFilter.toLowerCase()))
      : FONTS;

    for (const fontConfig of fontsToProcess) {
      const strokeData = await generateStrokesForFont(wasm, fontConfig);

      // Save to file
      const outputPath = join(ROOT, 'public/strokes', `${fontConfig.file}.json`);

      if (dryRun) {
        console.log(`  Would save to: ${outputPath}`);
        // Print sample output for first character
        const firstChar = Object.keys(strokeData.characters)[0];
        console.log(`  Sample (${firstChar}):`, JSON.stringify(strokeData.characters[firstChar], null, 2));
      } else {
        await writeFile(outputPath, JSON.stringify(strokeData, null, 2));
        console.log(`  Saved to: ${outputPath}`);
      }
    }

    console.log('\nDone!');
  } catch (err) {
    console.error('Fatal error:', err);
    process.exit(1);
  }
}

main();
