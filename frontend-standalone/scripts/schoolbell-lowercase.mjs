#!/usr/bin/env node
/**
 * AI-analyzed lowercase stroke definitions for Schoolbell font
 * Based on visual analysis of rendered characters
 */

import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Phonetic data for lowercase (same as uppercase)
const PHONETICS = {
  'a': { phonetic: 'ay', sound: 'ah as in apple' },
  'b': { phonetic: 'bee', sound: 'buh as in ball' },
  'c': { phonetic: 'see', sound: 'kuh as in cat' },
  'd': { phonetic: 'dee', sound: 'duh as in dog' },
  'e': { phonetic: 'ee', sound: 'eh as in elephant' },
  'f': { phonetic: 'ef', sound: 'fuh as in fish' },
  'g': { phonetic: 'jee', sound: 'guh as in goat' },
  'h': { phonetic: 'aych', sound: 'huh as in hat' },
  'i': { phonetic: 'eye', sound: 'ih as in igloo' },
  'j': { phonetic: 'jay', sound: 'juh as in jump' },
  'k': { phonetic: 'kay', sound: 'kuh as in kite' },
  'l': { phonetic: 'el', sound: 'luh as in lion' },
  'm': { phonetic: 'em', sound: 'muh as in moon' },
  'n': { phonetic: 'en', sound: 'nuh as in nest' },
  'o': { phonetic: 'oh', sound: 'ah as in octopus' },
  'p': { phonetic: 'pee', sound: 'puh as in pig' },
  'q': { phonetic: 'kyoo', sound: 'kwuh as in queen' },
  'r': { phonetic: 'ar', sound: 'ruh as in rabbit' },
  's': { phonetic: 'ess', sound: 'sss as in snake' },
  't': { phonetic: 'tee', sound: 'tuh as in tiger' },
  'u': { phonetic: 'yoo', sound: 'uh as in umbrella' },
  'v': { phonetic: 'vee', sound: 'vuh as in van' },
  'w': { phonetic: 'double-yoo', sound: 'wuh as in water' },
  'x': { phonetic: 'eks', sound: 'ks as in box' },
  'y': { phonetic: 'why', sound: 'yuh as in yellow' },
  'z': { phonetic: 'zee', sound: 'zzz as in zebra' },
};

function stroke(points, direction) {
  return { points, direction };
}

function interpolate(start, end, steps = 10) {
  const points = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    points.push([
      Math.round(start[0] + (end[0] - start[0]) * t),
      Math.round(start[1] + (end[1] - start[1]) * t)
    ]);
  }
  return points;
}

function curve(start, control, end, steps = 15) {
  const points = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = (1-t)*(1-t)*start[0] + 2*(1-t)*t*control[0] + t*t*end[0];
    const y = (1-t)*(1-t)*start[1] + 2*(1-t)*t*control[1] + t*t*end[1];
    points.push([Math.round(x), Math.round(y)]);
  }
  return points;
}

// Lowercase letters sit in approximately y: 35-75 range (x-height)
// Letters with ascenders (b,d,f,h,k,l) go up to ~15
// Letters with descenders (g,j,p,q,y) go down to ~90

const SCHOOLBELL_LOWERCASE = {
  'a': {
    type: 'lowercase',
    strokes: [
      // Bowl (oval on the left)
      stroke([
        ...curve([58, 42], [30, 42], [30, 58], 10),
        ...curve([30, 58], [30, 75], [58, 75], 10),
      ], 'down-curve'),
      // Vertical stem on right
      stroke(interpolate([58, 38], [58, 75]), 'down'),
    ]
  },
  'b': {
    type: 'lowercase',
    strokes: [
      // Tall vertical stem
      stroke(interpolate([35, 15], [35, 75]), 'down'),
      // Bowl on right
      stroke([
        ...curve([35, 45], [65, 45], [65, 60], 10),
        ...curve([65, 60], [65, 75], [35, 75], 10),
      ], 'down-curve'),
    ]
  },
  'c': {
    type: 'lowercase',
    strokes: [
      // Single C curve
      stroke(curve([62, 42], [28, 55], [62, 72], 20), 'down-curve'),
    ]
  },
  'd': {
    type: 'lowercase',
    strokes: [
      // Bowl on left (counterclockwise from stem)
      stroke([
        ...curve([65, 45], [35, 45], [35, 60], 10),
        ...curve([35, 60], [35, 75], [65, 75], 10),
      ], 'down-curve'),
      // Tall vertical stem on right
      stroke(interpolate([65, 15], [65, 75]), 'down'),
    ]
  },
  'e': {
    type: 'lowercase',
    strokes: [
      // Single stroke: horizontal line then curve around
      stroke([
        ...interpolate([32, 55], [65, 55]),
        ...curve([65, 55], [65, 38], [48, 38], 8),
        ...curve([48, 38], [28, 38], [28, 58], 8),
        ...curve([28, 58], [28, 75], [62, 72], 8),
      ], 'right'),
    ]
  },
  'f': {
    type: 'lowercase',
    strokes: [
      // Curved top + vertical stem
      stroke([
        ...curve([62, 20], [45, 15], [45, 35], 10),
        ...interpolate([45, 35], [45, 75]),
      ], 'down-curve'),
      // Crossbar
      stroke(interpolate([32, 45], [58, 45]), 'right'),
    ]
  },
  'g': {
    type: 'lowercase',
    strokes: [
      // Bowl at top
      stroke([
        ...curve([62, 42], [32, 42], [32, 58], 10),
        ...curve([32, 58], [32, 72], [62, 72], 10),
      ], 'down-curve'),
      // Descender with hook
      stroke([
        ...interpolate([62, 42], [62, 82]),
        ...curve([62, 82], [62, 92], [38, 88], 8),
      ], 'down-curve'),
    ]
  },
  'h': {
    type: 'lowercase',
    strokes: [
      // Tall vertical stem
      stroke(interpolate([35, 15], [35, 75]), 'down'),
      // Hump to right stem
      stroke([
        ...curve([35, 48], [55, 38], [55, 55], 10),
        ...interpolate([55, 55], [55, 75]),
      ], 'down-curve'),
    ]
  },
  'i': {
    type: 'lowercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([50, 38], [50, 75]), 'down'),
      // Dot
      stroke([[50, 25], [50, 28]], 'down'),
    ]
  },
  'j': {
    type: 'lowercase',
    strokes: [
      // Vertical with hook descender
      stroke([
        ...interpolate([52, 38], [52, 82]),
        ...curve([52, 82], [52, 92], [35, 88], 8),
      ], 'down-curve'),
      // Dot
      stroke([[52, 25], [52, 28]], 'down'),
    ]
  },
  'k': {
    type: 'lowercase',
    strokes: [
      // Tall vertical stem
      stroke(interpolate([35, 15], [35, 75]), 'down'),
      // Upper diagonal
      stroke(interpolate([35, 55], [60, 38]), 'up-right'),
      // Lower diagonal
      stroke(interpolate([35, 55], [60, 75]), 'down-right'),
    ]
  },
  'l': {
    type: 'lowercase',
    strokes: [
      // Simple tall vertical
      stroke(interpolate([50, 15], [50, 75]), 'down'),
    ]
  },
  'm': {
    type: 'lowercase',
    strokes: [
      // Left stem
      stroke(interpolate([22, 38], [22, 75]), 'down'),
      // First hump
      stroke([
        ...curve([22, 45], [38, 35], [38, 55], 10),
        ...interpolate([38, 55], [38, 75]),
      ], 'down-curve'),
      // Second hump
      stroke([
        ...curve([38, 45], [55, 35], [55, 55], 10),
        ...interpolate([55, 55], [55, 75]),
      ], 'down-curve'),
    ]
  },
  'n': {
    type: 'lowercase',
    strokes: [
      // Left stem
      stroke(interpolate([35, 38], [35, 75]), 'down'),
      // Hump to right stem
      stroke([
        ...curve([35, 45], [55, 35], [55, 55], 10),
        ...interpolate([55, 55], [55, 75]),
      ], 'down-curve'),
    ]
  },
  'o': {
    type: 'lowercase',
    strokes: [
      // Single oval
      stroke([
        ...curve([50, 38], [28, 55], [50, 72], 12),
        ...curve([50, 72], [72, 55], [50, 38], 12),
      ], 'down-curve'),
    ]
  },
  'p': {
    type: 'lowercase',
    strokes: [
      // Descender stem
      stroke(interpolate([35, 38], [35, 92]), 'down'),
      // Bowl on right
      stroke([
        ...curve([35, 42], [65, 42], [65, 58], 10),
        ...curve([65, 58], [65, 72], [35, 72], 10),
      ], 'down-curve'),
    ]
  },
  'q': {
    type: 'lowercase',
    strokes: [
      // Bowl on left
      stroke([
        ...curve([65, 42], [35, 42], [35, 58], 10),
        ...curve([35, 58], [35, 72], [65, 72], 10),
      ], 'down-curve'),
      // Descender stem on right
      stroke(interpolate([65, 38], [65, 92]), 'down'),
    ]
  },
  'r': {
    type: 'lowercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([38, 38], [38, 75]), 'down'),
      // Shoulder curve
      stroke(curve([38, 45], [52, 35], [58, 45], 10), 'right'),
    ]
  },
  's': {
    type: 'lowercase',
    strokes: [
      // S-curve
      stroke([
        ...curve([58, 42], [35, 38], [35, 52], 8),
        ...curve([35, 52], [65, 60], [65, 68], 8),
        ...curve([65, 68], [65, 75], [42, 72], 8),
      ], 'down-curve'),
    ]
  },
  't': {
    type: 'lowercase',
    strokes: [
      // Vertical stem (slightly above x-height)
      stroke(interpolate([50, 22], [50, 75]), 'down'),
      // Crossbar
      stroke(interpolate([35, 42], [65, 42]), 'right'),
    ]
  },
  'u': {
    type: 'lowercase',
    strokes: [
      // Left side down and curve
      stroke([
        ...interpolate([35, 38], [35, 62]),
        ...curve([35, 62], [50, 75], [65, 62], 10),
      ], 'down-curve'),
      // Right side
      stroke(interpolate([65, 38], [65, 75]), 'down'),
    ]
  },
  'v': {
    type: 'lowercase',
    strokes: [
      // Left diagonal down
      stroke(interpolate([30, 38], [50, 75]), 'down-right'),
      // Right diagonal up
      stroke(interpolate([50, 75], [70, 38]), 'up-right'),
    ]
  },
  'w': {
    type: 'lowercase',
    strokes: [
      // First down
      stroke(interpolate([18, 38], [30, 75]), 'down-right'),
      // First up
      stroke(interpolate([30, 75], [42, 50]), 'up-right'),
      // Second down
      stroke(interpolate([42, 50], [54, 75]), 'down-right'),
      // Second up
      stroke(interpolate([54, 75], [68, 38]), 'up-right'),
    ]
  },
  'x': {
    type: 'lowercase',
    strokes: [
      // Diagonal top-left to bottom-right
      stroke(interpolate([32, 38], [68, 75]), 'down-right'),
      // Diagonal top-right to bottom-left
      stroke(interpolate([68, 38], [32, 75]), 'down-left'),
    ]
  },
  'y': {
    type: 'lowercase',
    strokes: [
      // Left diagonal to center
      stroke(interpolate([30, 38], [50, 68]), 'down-right'),
      // Right diagonal with descender
      stroke([
        ...interpolate([70, 38], [50, 68]),
        ...interpolate([50, 68], [35, 92]),
      ], 'down-left'),
    ]
  },
  'z': {
    type: 'lowercase',
    strokes: [
      // Top horizontal
      stroke(interpolate([32, 38], [68, 38]), 'right'),
      // Diagonal
      stroke(interpolate([68, 38], [32, 75]), 'down-left'),
      // Bottom horizontal
      stroke(interpolate([32, 75], [68, 75]), 'right'),
    ]
  },
};

async function main() {
  const existingPath = join(ROOT, 'public/strokes/schoolbell.json');
  const existingData = JSON.parse(await readFile(existingPath, 'utf8'));

  // Update lowercase characters
  for (const [char, data] of Object.entries(SCHOOLBELL_LOWERCASE)) {
    const phonetic = PHONETICS[char] || { phonetic: char, sound: char };
    existingData.characters[char] = {
      type: data.type,
      phonetic: phonetic.phonetic,
      sound: phonetic.sound,
      strokes: data.strokes
    };
  }

  existingData.version = '3.1';
  existingData.description = 'Stroke definitions for Schoolbell font - AI-analyzed for pedagogical accuracy';

  await writeFile(existingPath, JSON.stringify(existingData, null, 2));
  console.log('Saved AI-analyzed Schoolbell lowercase strokes');

  // Verify
  const lower = 'abcdefghijklmnopqrstuvwxyz'.split('');
  for (const c of lower) {
    const info = existingData.characters[c];
    console.log(`${c}: ${info.strokes.length} strokes`);
  }
}

main().catch(console.error);
