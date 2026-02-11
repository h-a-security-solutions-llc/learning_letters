#!/usr/bin/env node
/**
 * AI-analyzed stroke definitions for Schoolbell font
 * Based on visual analysis of rendered characters
 *
 * Coordinates are in 0-100 space where the character is roughly centered
 * Grid reference: 25%, 50%, 75% lines visible in captures
 */

import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Phonetic data
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
};

// Helper to create a stroke
function stroke(points, direction) {
  return { points, direction };
}

// Helper to interpolate points along a path for smoother strokes
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

// Helper for curved paths (quadratic bezier approximation)
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

// Schoolbell uppercase stroke definitions based on visual analysis
const SCHOOLBELL_UPPERCASE = {
  'A': {
    type: 'uppercase',
    strokes: [
      // Left diagonal: from apex down-left
      stroke(interpolate([50, 15], [22, 85]), 'down-left'),
      // Right diagonal: from apex down-right
      stroke(interpolate([50, 15], [78, 85]), 'down-right'),
      // Crossbar: horizontal in middle
      stroke(interpolate([30, 55], [70, 55]), 'right'),
    ]
  },
  'B': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([28, 15], [28, 85]), 'down'),
      // Upper bump (angular for Schoolbell)
      stroke([...interpolate([28, 15], [55, 25]), ...interpolate([55, 25], [28, 48])], 'right'),
      // Lower bump (angular for Schoolbell)
      stroke([...interpolate([28, 48], [58, 58]), ...interpolate([58, 58], [28, 85])], 'right'),
    ]
  },
  'C': {
    type: 'uppercase',
    strokes: [
      // Single curved stroke from top-right, around to bottom-right
      stroke(curve([62, 25], [25, 50], [62, 75], 20), 'down-curve'),
    ]
  },
  'D': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([28, 15], [28, 85]), 'down'),
      // Curved right side
      stroke(curve([28, 15], [70, 50], [28, 85], 20), 'down-curve'),
    ]
  },
  'E': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([28, 15], [28, 85]), 'down'),
      // Top horizontal
      stroke(interpolate([28, 15], [62, 15]), 'right'),
      // Middle horizontal
      stroke(interpolate([28, 48], [55, 48]), 'right'),
      // Bottom horizontal
      stroke(interpolate([28, 85], [62, 85]), 'right'),
    ]
  },
  'F': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([30, 15], [30, 85]), 'down'),
      // Top horizontal
      stroke(interpolate([30, 15], [65, 15]), 'right'),
      // Middle horizontal
      stroke(interpolate([30, 45], [58, 45]), 'right'),
    ]
  },
  'G': {
    type: 'uppercase',
    strokes: [
      // Curved C-shape
      stroke(curve([62, 22], [22, 50], [62, 78], 20), 'down-curve'),
      // Horizontal bar from right side inward
      stroke(interpolate([62, 50], [45, 50]), 'left'),
    ]
  },
  'H': {
    type: 'uppercase',
    strokes: [
      // Left vertical
      stroke(interpolate([28, 15], [28, 85]), 'down'),
      // Right vertical
      stroke(interpolate([72, 15], [72, 85]), 'down'),
      // Crossbar
      stroke(interpolate([28, 50], [72, 50]), 'right'),
    ]
  },
  'I': {
    type: 'uppercase',
    strokes: [
      // Single vertical line
      stroke(interpolate([50, 15], [50, 85]), 'down'),
    ]
  },
  'J': {
    type: 'uppercase',
    strokes: [
      // Vertical line with curved bottom hook
      stroke([
        ...interpolate([58, 15], [58, 65]),
        ...curve([58, 65], [58, 85], [35, 80], 10)
      ], 'down-curve'),
    ]
  },
  'K': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([28, 15], [28, 85]), 'down'),
      // Upper diagonal (from middle to upper right)
      stroke(interpolate([28, 50], [68, 15]), 'up-right'),
      // Lower diagonal (from middle to lower right)
      stroke(interpolate([28, 50], [68, 85]), 'down-right'),
    ]
  },
  'L': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([30, 15], [30, 85]), 'down'),
      // Bottom horizontal
      stroke(interpolate([30, 85], [65, 85]), 'right'),
    ]
  },
  'M': {
    type: 'uppercase',
    strokes: [
      // Left vertical
      stroke(interpolate([20, 85], [20, 15]), 'up'),
      // Left diagonal down to center
      stroke(interpolate([20, 15], [50, 55]), 'down-right'),
      // Right diagonal up from center
      stroke(interpolate([50, 55], [80, 15]), 'up-right'),
      // Right vertical
      stroke(interpolate([80, 15], [80, 85]), 'down'),
    ]
  },
  'N': {
    type: 'uppercase',
    strokes: [
      // Left vertical (bottom to top)
      stroke(interpolate([28, 85], [28, 15]), 'up'),
      // Diagonal (top-left to bottom-right)
      stroke(interpolate([28, 15], [72, 85]), 'down-right'),
      // Right vertical (bottom to top)
      stroke(interpolate([72, 85], [72, 15]), 'up'),
    ]
  },
  'O': {
    type: 'uppercase',
    strokes: [
      // Single oval stroke starting from top
      stroke([
        ...curve([50, 15], [20, 50], [50, 85], 15),
        ...curve([50, 85], [80, 50], [50, 15], 15)
      ], 'down-curve'),
    ]
  },
  'P': {
    type: 'uppercase',
    strokes: [
      // Vertical stem (slightly tilted for Schoolbell)
      stroke(interpolate([30, 15], [32, 85]), 'down'),
      // Angular bump - two strokes forming a ">" shape
      stroke(interpolate([30, 15], [62, 32]), 'down-right'),
      stroke(interpolate([62, 32], [32, 50]), 'down-left'),
    ]
  },
  'Q': {
    type: 'uppercase',
    strokes: [
      // Oval like O
      stroke([
        ...curve([50, 18], [22, 50], [50, 82], 15),
        ...curve([50, 82], [78, 50], [50, 18], 15)
      ], 'down-curve'),
      // Tail diagonal
      stroke(interpolate([55, 70], [72, 88]), 'down-right'),
    ]
  },
  'R': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(interpolate([28, 15], [28, 85]), 'down'),
      // Angular bump like P
      stroke(interpolate([28, 15], [60, 30]), 'down-right'),
      stroke(interpolate([60, 30], [28, 48]), 'down-left'),
      // Leg diagonal
      stroke(interpolate([40, 48], [70, 85]), 'down-right'),
    ]
  },
  'S': {
    type: 'uppercase',
    strokes: [
      // S-curve - single continuous stroke
      stroke([
        ...curve([62, 25], [30, 20], [30, 45], 10),
        ...curve([30, 45], [70, 55], [70, 75], 10),
        ...curve([70, 75], [70, 85], [38, 80], 10)
      ], 'down-curve'),
    ]
  },
  'T': {
    type: 'uppercase',
    strokes: [
      // Top horizontal
      stroke(interpolate([25, 15], [75, 15]), 'right'),
      // Vertical stem
      stroke(interpolate([50, 15], [50, 85]), 'down'),
    ]
  },
  'U': {
    type: 'uppercase',
    strokes: [
      // Left side down and curve
      stroke([
        ...interpolate([28, 15], [28, 65]),
        ...curve([28, 65], [50, 88], [72, 65], 12)
      ], 'down-curve'),
      // Right side up
      stroke(interpolate([72, 65], [72, 15]), 'up'),
    ]
  },
  'V': {
    type: 'uppercase',
    strokes: [
      // Left diagonal down
      stroke(interpolate([22, 15], [50, 85]), 'down-right'),
      // Right diagonal up
      stroke(interpolate([50, 85], [78, 15]), 'up-right'),
    ]
  },
  'W': {
    type: 'uppercase',
    strokes: [
      // First down stroke
      stroke(interpolate([15, 15], [30, 85]), 'down-right'),
      // First up stroke
      stroke(interpolate([30, 85], [50, 40]), 'up-right'),
      // Second down stroke
      stroke(interpolate([50, 40], [70, 85]), 'down-right'),
      // Second up stroke
      stroke(interpolate([70, 85], [85, 15]), 'up-right'),
    ]
  },
  'X': {
    type: 'uppercase',
    strokes: [
      // Diagonal from top-left to bottom-right
      stroke(interpolate([25, 15], [75, 85]), 'down-right'),
      // Diagonal from top-right to bottom-left
      stroke(interpolate([75, 15], [25, 85]), 'down-left'),
    ]
  },
  'Y': {
    type: 'uppercase',
    strokes: [
      // Left diagonal to center
      stroke(interpolate([22, 15], [50, 50]), 'down-right'),
      // Right diagonal to center
      stroke(interpolate([78, 15], [50, 50]), 'down-left'),
      // Vertical stem from center down
      stroke(interpolate([50, 50], [50, 85]), 'down'),
    ]
  },
  'Z': {
    type: 'uppercase',
    strokes: [
      // Top horizontal
      stroke(interpolate([25, 15], [75, 15]), 'right'),
      // Diagonal
      stroke(interpolate([75, 15], [25, 85]), 'down-left'),
      // Bottom horizontal
      stroke(interpolate([25, 85], [75, 85]), 'right'),
    ]
  },
};

async function main() {
  // Read existing file to preserve lowercase and numbers
  const existingPath = join(ROOT, 'public/strokes/schoolbell.json');
  let existingData;
  try {
    existingData = JSON.parse(await readFile(existingPath, 'utf8'));
  } catch (e) {
    existingData = { characters: {} };
  }

  // Build new data with AI-analyzed uppercase strokes
  const newData = {
    font: 'Schoolbell',
    version: '3.0',
    description: 'Stroke definitions for Schoolbell font - AI-analyzed for pedagogical accuracy',
    characters: {}
  };

  // Add AI-analyzed uppercase
  for (const [char, data] of Object.entries(SCHOOLBELL_UPPERCASE)) {
    const phonetic = PHONETICS[char] || { phonetic: char, sound: char };
    newData.characters[char] = {
      type: data.type,
      phonetic: phonetic.phonetic,
      sound: phonetic.sound,
      strokes: data.strokes
    };
  }

  // Keep existing lowercase and numbers for now
  for (const [char, data] of Object.entries(existingData.characters)) {
    if (!newData.characters[char]) {
      newData.characters[char] = data;
    }
  }

  // Save
  await writeFile(existingPath, JSON.stringify(newData, null, 2));
  console.log('Saved AI-analyzed Schoolbell uppercase strokes');
  console.log(`Total characters: ${Object.keys(newData.characters).length}`);
}

main().catch(console.error);
