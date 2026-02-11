#!/usr/bin/env node
/**
 * AI-analyzed number stroke definitions for Schoolbell font
 */

import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const PHONETICS = {
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

const SCHOOLBELL_NUMBERS = {
  '0': {
    type: 'number',
    strokes: [
      // Single oval starting from top
      stroke([
        ...curve([50, 18], [25, 50], [50, 82], 12),
        ...curve([50, 82], [75, 50], [50, 18], 12),
      ], 'down-curve'),
    ]
  },
  '1': {
    type: 'number',
    strokes: [
      // Small diagonal at top-left
      stroke(interpolate([40, 28], [52, 18]), 'up-right'),
      // Vertical line
      stroke(interpolate([52, 18], [52, 82]), 'down'),
    ]
  },
  '2': {
    type: 'number',
    strokes: [
      // Continuous stroke: curve at top, diagonal, horizontal at bottom
      stroke([
        ...curve([32, 32], [32, 18], [55, 18], 8),
        ...curve([55, 18], [72, 18], [72, 35], 8),
        ...curve([72, 35], [72, 50], [50, 60], 8),
        ...interpolate([50, 60], [28, 82]),
        ...interpolate([28, 82], [72, 82]),
      ], 'right'),
    ]
  },
  '3': {
    type: 'number',
    strokes: [
      // Continuous S-curve with two bumps
      stroke([
        ...curve([32, 22], [55, 15], [62, 32], 8),
        ...curve([62, 32], [68, 45], [50, 50], 8),
        ...curve([50, 50], [68, 55], [62, 68], 8),
        ...curve([62, 68], [55, 82], [32, 78], 8),
      ], 'down-curve'),
    ]
  },
  '4': {
    type: 'number',
    strokes: [
      // Diagonal from top to middle-left
      stroke(interpolate([58, 18], [28, 58]), 'down-left'),
      // Horizontal across
      stroke(interpolate([28, 58], [72, 58]), 'right'),
      // Vertical from top to bottom on right side
      stroke(interpolate([58, 18], [58, 82]), 'down'),
    ]
  },
  '5': {
    type: 'number',
    strokes: [
      // Top horizontal + vertical down
      stroke([
        ...interpolate([65, 18], [35, 18]),
        ...interpolate([35, 18], [35, 48]),
      ], 'left'),
      // Curved bottom portion
      stroke([
        ...curve([35, 48], [55, 42], [65, 55], 10),
        ...curve([65, 55], [72, 68], [50, 82], 10),
        ...curve([50, 82], [28, 82], [28, 70], 8),
      ], 'down-curve'),
    ]
  },
  '6': {
    type: 'number',
    strokes: [
      // Continuous curve from top with loop at bottom
      stroke([
        ...curve([62, 22], [50, 15], [35, 35], 10),
        ...interpolate([35, 35], [35, 60]),
        ...curve([35, 60], [35, 82], [55, 82], 10),
        ...curve([55, 82], [72, 82], [72, 65], 10),
        ...curve([72, 65], [72, 48], [50, 48], 10),
        ...curve([50, 48], [35, 48], [35, 60], 8),
      ], 'down-curve'),
    ]
  },
  '7': {
    type: 'number',
    strokes: [
      // Horizontal at top
      stroke(interpolate([28, 18], [72, 18]), 'right'),
      // Diagonal down
      stroke(interpolate([72, 18], [42, 82]), 'down-left'),
    ]
  },
  '8': {
    type: 'number',
    strokes: [
      // Figure-8: start at middle, go up and around top loop, then bottom loop
      stroke([
        // Top loop (counterclockwise)
        ...curve([50, 50], [30, 45], [30, 32], 8),
        ...curve([30, 32], [30, 18], [50, 18], 8),
        ...curve([50, 18], [70, 18], [70, 32], 8),
        ...curve([70, 32], [70, 45], [50, 50], 8),
        // Bottom loop (clockwise)
        ...curve([50, 50], [72, 55], [72, 68], 8),
        ...curve([72, 68], [72, 82], [50, 82], 8),
        ...curve([50, 82], [28, 82], [28, 68], 8),
        ...curve([28, 68], [28, 55], [50, 50], 8),
      ], 'down-curve'),
    ]
  },
  '9': {
    type: 'number',
    strokes: [
      // Loop at top + descender
      stroke([
        // Top loop
        ...curve([65, 40], [65, 18], [45, 18], 10),
        ...curve([45, 18], [28, 18], [28, 35], 10),
        ...curve([28, 35], [28, 52], [50, 52], 10),
        ...curve([50, 52], [65, 52], [65, 40], 8),
        // Descender
        ...interpolate([65, 40], [65, 70]),
        ...curve([65, 70], [65, 85], [45, 82], 8),
      ], 'down-curve'),
    ]
  },
};

async function main() {
  const existingPath = join(ROOT, 'public/strokes/schoolbell.json');
  const existingData = JSON.parse(await readFile(existingPath, 'utf8'));

  // Update number characters
  for (const [char, data] of Object.entries(SCHOOLBELL_NUMBERS)) {
    const phonetic = PHONETICS[char];
    existingData.characters[char] = {
      type: data.type,
      phonetic: phonetic.phonetic,
      sound: phonetic.sound,
      strokes: data.strokes
    };
  }

  existingData.version = '3.2';

  await writeFile(existingPath, JSON.stringify(existingData, null, 2));
  console.log('Saved AI-analyzed Schoolbell number strokes');

  // Verify
  for (const c of '0123456789'.split('')) {
    const info = existingData.characters[c];
    console.log(`${c}: ${info.strokes.length} strokes`);
  }
}

main().catch(console.error);
