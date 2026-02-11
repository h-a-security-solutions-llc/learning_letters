#!/usr/bin/env node
/**
 * Accurate stroke definitions for Schoolbell font
 * Coordinates traced from actual glyph renders with grid reference
 * Grid lines at 25%, 50%, 75% - coordinates in 0-100 space
 *
 * Schoolbell characteristics:
 * - Slight rightward slant on vertical strokes (about 2-3 units over full height)
 * - Angular bumps on letters like P, B, R (not curved)
 * - Handwritten, slightly irregular feel
 */

import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Phonetics
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

// Linear interpolation with exact start/end points
function line(start, end, steps = 8) {
  const points = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    points.push([
      Math.round((start[0] + (end[0] - start[0]) * t) * 10) / 10,
      Math.round((start[1] + (end[1] - start[1]) * t) * 10) / 10
    ]);
  }
  return points;
}

// Quadratic bezier curve
function curve(start, control, end, steps = 12) {
  const points = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = (1-t)*(1-t)*start[0] + 2*(1-t)*t*control[0] + t*t*end[0];
    const y = (1-t)*(1-t)*start[1] + 2*(1-t)*t*control[1] + t*t*end[1];
    points.push([Math.round(x * 10) / 10, Math.round(y * 10) / 10]);
  }
  return points;
}

// Coordinates traced from actual Schoolbell glyph renders
// All coordinates account for Schoolbell's characteristic slant

const SCHOOLBELL_CHARS = {
  // === UPPERCASE ===
  'A': {
    type: 'uppercase',
    strokes: [
      // Left leg: apex to bottom-left (slight inward slant)
      stroke(line([50, 12], [22, 87]), 'down-left'),
      // Right leg: apex to bottom-right
      stroke(line([50, 12], [78, 87]), 'down-right'),
      // Crossbar
      stroke(line([30, 58], [70, 58]), 'right'),
    ]
  },
  'B': {
    type: 'uppercase',
    strokes: [
      // Vertical stem (slight rightward slant)
      stroke(line([27, 15], [29, 87]), 'down'),
      // Upper bump - angular for Schoolbell
      stroke([...line([27, 15], [55, 15]), ...line([55, 15], [55, 32]), ...line([55, 32], [28, 48])], 'right'),
      // Lower bump - angular
      stroke([...line([28, 48], [58, 48]), ...line([58, 48], [58, 70]), ...line([58, 70], [29, 87])], 'right'),
    ]
  },
  'C': {
    type: 'uppercase',
    strokes: [
      // Single curved stroke opening right
      stroke([...curve([60, 22], [22, 22], [22, 50]), ...curve([22, 50], [22, 78], [60, 78])], 'down-curve'),
    ]
  },
  'D': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(line([27, 15], [29, 87]), 'down'),
      // Curved right side
      stroke([...curve([27, 15], [70, 15], [70, 50]), ...curve([70, 50], [70, 87], [29, 87])], 'down-curve'),
    ]
  },
  'E': {
    type: 'uppercase',
    strokes: [
      // Vertical stem (slight slant)
      stroke(line([28, 17], [30, 85]), 'down'),
      // Top horizontal
      stroke(line([28, 17], [60, 17]), 'right'),
      // Middle horizontal
      stroke(line([29, 50], [55, 50]), 'right'),
      // Bottom horizontal
      stroke(line([30, 85], [60, 85]), 'right'),
    ]
  },
  'F': {
    type: 'uppercase',
    strokes: [
      // Vertical stem (slight rightward slant)
      stroke(line([30, 15], [32, 85]), 'down'),
      // Top horizontal
      stroke(line([30, 15], [63, 15]), 'right'),
      // Middle horizontal
      stroke(line([31, 47], [57, 47]), 'right'),
    ]
  },
  'G': {
    type: 'uppercase',
    strokes: [
      // C-curve opening right
      stroke([...curve([62, 22], [22, 22], [22, 50]), ...curve([22, 50], [22, 78], [62, 78])], 'down-curve'),
      // Horizontal bar inward
      stroke(line([62, 52], [45, 52]), 'left'),
    ]
  },
  'H': {
    type: 'uppercase',
    strokes: [
      // Left stem (slight slant)
      stroke(line([28, 17], [30, 85]), 'down'),
      // Right stem (slight slant)
      stroke(line([70, 17], [72, 85]), 'down'),
      // Crossbar
      stroke(line([29, 50], [71, 50]), 'right'),
    ]
  },
  'I': {
    type: 'uppercase',
    strokes: [
      // Single vertical (slight slant)
      stroke(line([49, 17], [51, 85]), 'down'),
    ]
  },
  'J': {
    type: 'uppercase',
    strokes: [
      // Vertical with curved hook at bottom
      stroke([...line([58, 15], [59, 65]), ...curve([59, 65], [59, 85], [38, 82])], 'down-curve'),
    ]
  },
  'K': {
    type: 'uppercase',
    strokes: [
      // Vertical stem
      stroke(line([28, 17], [30, 85]), 'down'),
      // Upper diagonal to right
      stroke(line([29, 52], [65, 17]), 'up-right'),
      // Lower diagonal to right
      stroke(line([29, 52], [65, 85]), 'down-right'),
    ]
  },
  'L': {
    type: 'uppercase',
    strokes: [
      // Vertical stem (slight slant)
      stroke(line([30, 17], [32, 85]), 'down'),
      // Bottom horizontal
      stroke(line([32, 85], [62, 85]), 'right'),
    ]
  },
  'M': {
    type: 'uppercase',
    strokes: [
      // Left vertical up
      stroke(line([22, 87], [20, 17]), 'up'),
      // Left diagonal down to center
      stroke(line([20, 17], [50, 55]), 'down-right'),
      // Right diagonal up from center
      stroke(line([50, 55], [80, 17]), 'up-right'),
      // Right vertical down
      stroke(line([80, 17], [82, 87]), 'down'),
    ]
  },
  'N': {
    type: 'uppercase',
    strokes: [
      // Left vertical up
      stroke(line([28, 87], [26, 17]), 'up'),
      // Diagonal down to right
      stroke(line([26, 17], [72, 87]), 'down-right'),
      // Right vertical up
      stroke(line([72, 87], [70, 17]), 'up'),
    ]
  },
  'O': {
    type: 'uppercase',
    strokes: [
      // Oval - single continuous stroke
      stroke([
        ...curve([50, 17], [22, 17], [22, 50]),
        ...curve([22, 50], [22, 83], [50, 83]),
        ...curve([50, 83], [78, 83], [78, 50]),
        ...curve([78, 50], [78, 17], [50, 17])
      ], 'down-curve'),
    ]
  },
  'P': {
    type: 'uppercase',
    strokes: [
      // Vertical stem with Schoolbell's rightward slant
      // Top at ~24,12 bottom at ~27,88
      stroke(line([24, 12], [27, 88]), 'down'),
      // Angular bump - diagonal out to upper right
      stroke(line([24, 12], [57, 23]), 'down-right'),
      // Angular bump - diagonal back to stem
      stroke(line([57, 23], [26, 48]), 'down-left'),
    ]
  },
  'Q': {
    type: 'uppercase',
    strokes: [
      // Oval like O
      stroke([
        ...curve([50, 18], [22, 18], [22, 50]),
        ...curve([22, 50], [22, 82], [50, 82]),
        ...curve([50, 82], [78, 82], [78, 50]),
        ...curve([78, 50], [78, 18], [50, 18])
      ], 'down-curve'),
      // Tail
      stroke(line([55, 70], [70, 88]), 'down-right'),
    ]
  },
  'R': {
    type: 'uppercase',
    strokes: [
      // Vertical stem (slanted)
      stroke(line([28, 15], [30, 87]), 'down'),
      // Angular bump out
      stroke(line([28, 15], [58, 28]), 'down-right'),
      // Angular bump back
      stroke(line([58, 28], [29, 48]), 'down-left'),
      // Leg diagonal
      stroke(line([40, 48], [68, 87]), 'down-right'),
    ]
  },
  'S': {
    type: 'uppercase',
    strokes: [
      // S-curve - single continuous
      stroke([
        ...curve([60, 25], [60, 15], [45, 15]),
        ...curve([45, 15], [25, 15], [25, 32]),
        ...curve([25, 32], [25, 45], [50, 50]),
        ...curve([50, 50], [75, 55], [75, 68]),
        ...curve([75, 68], [75, 85], [55, 85]),
        ...curve([55, 85], [35, 85], [35, 78])
      ], 'down-curve'),
    ]
  },
  'T': {
    type: 'uppercase',
    strokes: [
      // Top horizontal
      stroke(line([25, 17], [75, 17]), 'right'),
      // Vertical stem (slight slant)
      stroke(line([49, 17], [51, 85]), 'down'),
    ]
  },
  'U': {
    type: 'uppercase',
    strokes: [
      // Left side down with curve
      stroke([...line([28, 17], [29, 65]), ...curve([29, 65], [50, 87], [71, 65])], 'down-curve'),
      // Right side up
      stroke(line([71, 65], [72, 17]), 'up'),
    ]
  },
  'V': {
    type: 'uppercase',
    strokes: [
      // Left diagonal down
      stroke(line([22, 17], [50, 85]), 'down-right'),
      // Right diagonal up
      stroke(line([50, 85], [78, 17]), 'up-right'),
    ]
  },
  'W': {
    type: 'uppercase',
    strokes: [
      // First down
      stroke(line([15, 17], [30, 85]), 'down-right'),
      // First up
      stroke(line([30, 85], [50, 40]), 'up-right'),
      // Second down
      stroke(line([50, 40], [70, 85]), 'down-right'),
      // Second up
      stroke(line([70, 85], [85, 17]), 'up-right'),
    ]
  },
  'X': {
    type: 'uppercase',
    strokes: [
      // Diagonal top-left to bottom-right
      stroke(line([25, 17], [75, 85]), 'down-right'),
      // Diagonal top-right to bottom-left
      stroke(line([75, 17], [25, 85]), 'down-left'),
    ]
  },
  'Y': {
    type: 'uppercase',
    strokes: [
      // Left diagonal to center
      stroke(line([22, 17], [50, 50]), 'down-right'),
      // Right diagonal to center
      stroke(line([78, 17], [50, 50]), 'down-left'),
      // Vertical from center down
      stroke(line([50, 50], [51, 85]), 'down'),
    ]
  },
  'Z': {
    type: 'uppercase',
    strokes: [
      // Top horizontal
      stroke(line([25, 17], [75, 17]), 'right'),
      // Diagonal
      stroke(line([75, 17], [25, 85]), 'down-left'),
      // Bottom horizontal
      stroke(line([25, 85], [75, 85]), 'right'),
    ]
  },

  // === LOWERCASE ===
  'a': {
    type: 'lowercase',
    strokes: [
      // Bowl (counter-clockwise from right)
      stroke([
        ...curve([60, 45], [60, 35], [45, 35]),
        ...curve([45, 35], [28, 35], [28, 55]),
        ...curve([28, 55], [28, 75], [45, 75]),
        ...curve([45, 75], [60, 75], [60, 55])
      ], 'down-curve'),
      // Vertical stem on right (with slant)
      stroke(line([60, 38], [62, 75]), 'down'),
    ]
  },
  'b': {
    type: 'lowercase',
    strokes: [
      // Tall stem (slanted)
      stroke(line([35, 15], [37, 75]), 'down'),
      // Bowl on right
      stroke([
        ...curve([37, 45], [37, 35], [52, 35]),
        ...curve([52, 35], [68, 35], [68, 55]),
        ...curve([68, 55], [68, 75], [52, 75]),
        ...curve([52, 75], [37, 75], [37, 55])
      ], 'down-curve'),
    ]
  },
  'c': {
    type: 'lowercase',
    strokes: [
      // C curve
      stroke([...curve([62, 40], [30, 40], [30, 55]), ...curve([30, 55], [30, 72], [62, 72])], 'down-curve'),
    ]
  },
  'd': {
    type: 'lowercase',
    strokes: [
      // Bowl on left
      stroke([
        ...curve([63, 45], [63, 35], [48, 35]),
        ...curve([48, 35], [32, 35], [32, 55]),
        ...curve([32, 55], [32, 75], [48, 75]),
        ...curve([48, 75], [63, 75], [63, 55])
      ], 'down-curve'),
      // Tall stem on right (slanted)
      stroke(line([63, 15], [65, 75]), 'down'),
    ]
  },
  'e': {
    type: 'lowercase',
    strokes: [
      // Start with crossbar, then curve around
      stroke([
        ...line([30, 52], [65, 52]),
        ...curve([65, 52], [65, 38], [48, 38]),
        ...curve([48, 38], [28, 38], [28, 55]),
        ...curve([28, 55], [28, 72], [60, 72])
      ], 'right'),
    ]
  },
  'f': {
    type: 'lowercase',
    strokes: [
      // Curved top + stem
      stroke([...curve([62, 20], [48, 12], [48, 35]), ...line([48, 35], [50, 75])], 'down-curve'),
      // Crossbar
      stroke(line([35, 42], [62, 42]), 'right'),
    ]
  },
  'g': {
    type: 'lowercase',
    strokes: [
      // Bowl at top
      stroke([
        ...curve([62, 42], [62, 35], [48, 35]),
        ...curve([48, 35], [32, 35], [32, 52]),
        ...curve([32, 52], [32, 70], [48, 70]),
        ...curve([48, 70], [62, 70], [62, 52])
      ], 'down-curve'),
      // Descender with hook
      stroke([...line([62, 42], [63, 82]), ...curve([63, 82], [63, 92], [40, 88])], 'down-curve'),
    ]
  },
  'h': {
    type: 'lowercase',
    strokes: [
      // Tall stem (slanted)
      stroke(line([35, 15], [37, 75]), 'down'),
      // Hump to right stem
      stroke([...curve([37, 48], [50, 35], [55, 50]), ...line([55, 50], [57, 75])], 'down-curve'),
    ]
  },
  'i': {
    type: 'lowercase',
    strokes: [
      // Stem
      stroke(line([50, 38], [52, 75]), 'down'),
      // Dot
      stroke([[50, 25], [50, 28]], 'down'),
    ]
  },
  'j': {
    type: 'lowercase',
    strokes: [
      // Stem with descender hook
      stroke([...line([52, 38], [53, 82]), ...curve([53, 82], [53, 92], [38, 88])], 'down-curve'),
      // Dot
      stroke([[52, 25], [52, 28]], 'down'),
    ]
  },
  'k': {
    type: 'lowercase',
    strokes: [
      // Tall stem
      stroke(line([35, 15], [37, 75]), 'down'),
      // Upper diagonal
      stroke(line([36, 55], [58, 38]), 'up-right'),
      // Lower diagonal
      stroke(line([36, 55], [60, 75]), 'down-right'),
    ]
  },
  'l': {
    type: 'lowercase',
    strokes: [
      // Simple tall vertical (slanted)
      stroke(line([50, 15], [52, 75]), 'down'),
    ]
  },
  'm': {
    type: 'lowercase',
    strokes: [
      // Left stem
      stroke(line([22, 38], [24, 75]), 'down'),
      // First hump
      stroke([...curve([24, 45], [35, 35], [38, 50]), ...line([38, 50], [40, 75])], 'down-curve'),
      // Second hump
      stroke([...curve([40, 45], [52, 35], [55, 50]), ...line([55, 50], [57, 75])], 'down-curve'),
    ]
  },
  'n': {
    type: 'lowercase',
    strokes: [
      // Left stem
      stroke(line([35, 38], [37, 75]), 'down'),
      // Hump
      stroke([...curve([37, 45], [50, 35], [55, 50]), ...line([55, 50], [57, 75])], 'down-curve'),
    ]
  },
  'o': {
    type: 'lowercase',
    strokes: [
      // Oval
      stroke([
        ...curve([50, 38], [28, 38], [28, 55]),
        ...curve([28, 55], [28, 72], [50, 72]),
        ...curve([50, 72], [72, 72], [72, 55]),
        ...curve([72, 55], [72, 38], [50, 38])
      ], 'down-curve'),
    ]
  },
  'p': {
    type: 'lowercase',
    strokes: [
      // Descender stem (slanted)
      stroke(line([35, 38], [38, 92]), 'down'),
      // Bowl on right
      stroke([
        ...curve([36, 42], [36, 35], [52, 35]),
        ...curve([52, 35], [68, 35], [68, 52]),
        ...curve([68, 52], [68, 70], [52, 70]),
        ...curve([52, 70], [36, 70], [36, 55])
      ], 'down-curve'),
    ]
  },
  'q': {
    type: 'lowercase',
    strokes: [
      // Bowl on left
      stroke([
        ...curve([64, 42], [64, 35], [48, 35]),
        ...curve([48, 35], [32, 35], [32, 52]),
        ...curve([32, 52], [32, 70], [48, 70]),
        ...curve([48, 70], [64, 70], [64, 55])
      ], 'down-curve'),
      // Descender stem (slanted)
      stroke(line([64, 38], [67, 92]), 'down'),
    ]
  },
  'r': {
    type: 'lowercase',
    strokes: [
      // Stem
      stroke(line([38, 38], [40, 75]), 'down'),
      // Shoulder
      stroke(curve([39, 45], [50, 35], [58, 42]), 'right'),
    ]
  },
  's': {
    type: 'lowercase',
    strokes: [
      // S curve
      stroke([
        ...curve([58, 42], [58, 35], [45, 35]),
        ...curve([45, 35], [32, 35], [32, 48]),
        ...curve([32, 48], [32, 55], [50, 55]),
        ...curve([50, 55], [68, 55], [68, 65]),
        ...curve([68, 65], [68, 72], [55, 72]),
        ...curve([55, 72], [42, 72], [42, 68])
      ], 'down-curve'),
    ]
  },
  't': {
    type: 'lowercase',
    strokes: [
      // Stem (slightly above x-height, slanted)
      stroke(line([50, 22], [52, 75]), 'down'),
      // Crossbar
      stroke(line([38, 42], [62, 42]), 'right'),
    ]
  },
  'u': {
    type: 'lowercase',
    strokes: [
      // Left side down + curve
      stroke([...line([35, 38], [36, 60]), ...curve([36, 60], [50, 75], [64, 60])], 'down-curve'),
      // Right side (slanted)
      stroke(line([64, 38], [66, 75]), 'down'),
    ]
  },
  'v': {
    type: 'lowercase',
    strokes: [
      // Left diagonal
      stroke(line([30, 38], [50, 75]), 'down-right'),
      // Right diagonal
      stroke(line([50, 75], [70, 38]), 'up-right'),
    ]
  },
  'w': {
    type: 'lowercase',
    strokes: [
      // First down
      stroke(line([18, 38], [30, 75]), 'down-right'),
      // First up
      stroke(line([30, 75], [42, 50]), 'up-right'),
      // Second down
      stroke(line([42, 50], [54, 75]), 'down-right'),
      // Second up
      stroke(line([54, 75], [68, 38]), 'up-right'),
    ]
  },
  'x': {
    type: 'lowercase',
    strokes: [
      // Diagonal down-right
      stroke(line([32, 38], [68, 75]), 'down-right'),
      // Diagonal down-left
      stroke(line([68, 38], [32, 75]), 'down-left'),
    ]
  },
  'y': {
    type: 'lowercase',
    strokes: [
      // Left diagonal to center
      stroke(line([30, 38], [50, 68]), 'down-right'),
      // Right diagonal with descender
      stroke([...line([70, 38], [50, 68]), ...line([50, 68], [38, 92])], 'down-left'),
    ]
  },
  'z': {
    type: 'lowercase',
    strokes: [
      // Top horizontal
      stroke(line([32, 38], [68, 38]), 'right'),
      // Diagonal
      stroke(line([68, 38], [32, 75]), 'down-left'),
      // Bottom horizontal
      stroke(line([32, 75], [68, 75]), 'right'),
    ]
  },

  // === NUMBERS ===
  '0': {
    type: 'number',
    strokes: [
      // Oval
      stroke([
        ...curve([50, 18], [25, 18], [25, 50]),
        ...curve([25, 50], [25, 82], [50, 82]),
        ...curve([50, 82], [75, 82], [75, 50]),
        ...curve([75, 50], [75, 18], [50, 18])
      ], 'down-curve'),
    ]
  },
  '1': {
    type: 'number',
    strokes: [
      // Small serif at top
      stroke(line([42, 28], [52, 18]), 'up-right'),
      // Vertical (slanted)
      stroke(line([52, 18], [54, 82]), 'down'),
    ]
  },
  '2': {
    type: 'number',
    strokes: [
      // Continuous: curve at top -> diagonal -> horizontal
      stroke([
        ...curve([30, 30], [30, 18], [50, 18]),
        ...curve([50, 18], [72, 18], [72, 32]),
        ...curve([72, 32], [72, 48], [50, 58]),
        ...line([50, 58], [28, 82]),
        ...line([28, 82], [72, 82])
      ], 'right'),
    ]
  },
  '3': {
    type: 'number',
    strokes: [
      // Two bumps
      stroke([
        ...curve([32, 22], [50, 15], [62, 28]),
        ...curve([62, 28], [70, 38], [50, 50]),
        ...curve([50, 50], [70, 62], [62, 72]),
        ...curve([62, 72], [50, 85], [32, 78])
      ], 'down-curve'),
    ]
  },
  '4': {
    type: 'number',
    strokes: [
      // Diagonal from top to middle-left
      stroke(line([58, 18], [28, 58]), 'down-left'),
      // Horizontal
      stroke(line([28, 58], [72, 58]), 'right'),
      // Vertical (slanted)
      stroke(line([58, 18], [60, 82]), 'down'),
    ]
  },
  '5': {
    type: 'number',
    strokes: [
      // Top horizontal + vertical
      stroke([...line([65, 18], [35, 18]), ...line([35, 18], [35, 48])], 'left'),
      // Curved bottom
      stroke([
        ...curve([35, 48], [55, 42], [65, 55]),
        ...curve([65, 55], [72, 68], [50, 82]),
        ...curve([50, 82], [30, 82], [30, 72])
      ], 'down-curve'),
    ]
  },
  '6': {
    type: 'number',
    strokes: [
      // Curve from top + loop
      stroke([
        ...curve([62, 22], [50, 15], [35, 35]),
        ...line([35, 35], [35, 58]),
        ...curve([35, 58], [35, 82], [55, 82]),
        ...curve([55, 82], [72, 82], [72, 65]),
        ...curve([72, 65], [72, 48], [50, 48]),
        ...curve([50, 48], [35, 48], [35, 58])
      ], 'down-curve'),
    ]
  },
  '7': {
    type: 'number',
    strokes: [
      // Top horizontal
      stroke(line([28, 18], [72, 18]), 'right'),
      // Diagonal (slanted)
      stroke(line([72, 18], [45, 82]), 'down-left'),
    ]
  },
  '8': {
    type: 'number',
    strokes: [
      // Figure 8
      stroke([
        // Top loop
        ...curve([50, 50], [30, 45], [30, 32]),
        ...curve([30, 32], [30, 18], [50, 18]),
        ...curve([50, 18], [70, 18], [70, 32]),
        ...curve([70, 32], [70, 45], [50, 50]),
        // Bottom loop
        ...curve([50, 50], [72, 55], [72, 68]),
        ...curve([72, 68], [72, 82], [50, 82]),
        ...curve([50, 82], [28, 82], [28, 68]),
        ...curve([28, 68], [28, 55], [50, 50])
      ], 'down-curve'),
    ]
  },
  '9': {
    type: 'number',
    strokes: [
      // Loop at top + descender
      stroke([
        ...curve([65, 42], [65, 18], [45, 18]),
        ...curve([45, 18], [28, 18], [28, 35]),
        ...curve([28, 35], [28, 52], [50, 52]),
        ...curve([50, 52], [65, 52], [65, 42]),
        ...line([65, 42], [66, 70]),
        ...curve([66, 70], [66, 85], [48, 82])
      ], 'down-curve'),
    ]
  },
};

async function main() {
  const outputPath = join(ROOT, 'public/strokes/schoolbell.json');

  const data = {
    font: 'Schoolbell',
    version: '4.0',
    description: 'Stroke definitions for Schoolbell font - accurately traced from glyph renders',
    characters: {}
  };

  for (const [char, charData] of Object.entries(SCHOOLBELL_CHARS)) {
    const phonetic = PHONETICS[char] || { phonetic: char, sound: char };
    data.characters[char] = {
      type: charData.type,
      phonetic: phonetic.phonetic,
      sound: phonetic.sound,
      strokes: charData.strokes
    };
  }

  await writeFile(outputPath, JSON.stringify(data, null, 2));
  console.log('Saved accurate Schoolbell stroke data');
  console.log(`Total characters: ${Object.keys(data.characters).length}`);

  // Show P specifically
  const p = data.characters['P'];
  console.log('\nP strokes:');
  p.strokes.forEach((s, i) => {
    console.log(`  Stroke ${i + 1}: ${s.direction}`);
    console.log(`    Start: [${s.points[0]}]`);
    console.log(`    End: [${s.points[s.points.length - 1]}]`);
  });
}

main().catch(console.error);
