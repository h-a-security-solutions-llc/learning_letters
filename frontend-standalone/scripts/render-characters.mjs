#!/usr/bin/env node
/**
 * Render characters to PNG images for visual analysis
 * Uses the WASM module to render glyphs
 */

import { writeFile, mkdir } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createCanvas } from 'canvas';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Characters to process
const UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
const LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'.split('');
const NUMBERS = '0123456789'.split('');

// Font configurations
const FONTS = [
  { name: 'Schoolbell-Regular', file: 'schoolbell', display: 'Schoolbell' },
  { name: 'Fredoka-Regular', file: 'fredoka', display: 'Fredoka' },
  { name: 'Nunito-Regular', file: 'nunito', display: 'Nunito' },
  { name: 'PatrickHand-Regular', file: 'patrick-hand', display: 'Patrick Hand' },
  { name: 'PlaywriteUS-Regular', file: 'playwrite-us', display: 'Playwrite US' },
];

async function renderCharacter(char, fontPath, fontFamily, size = 200) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // White background
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, size, size);

  // Draw character
  ctx.fillStyle = '#333';
  ctx.font = `${size * 0.75}px "${fontFamily}"`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(char, size / 2, size / 2);

  // Draw grid lines for reference (every 25%)
  ctx.strokeStyle = 'rgba(0, 150, 255, 0.3)';
  ctx.lineWidth = 1;
  for (let i = 0.25; i <= 0.75; i += 0.25) {
    ctx.beginPath();
    ctx.moveTo(size * i, 0);
    ctx.lineTo(size * i, size);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, size * i);
    ctx.lineTo(size, size * i);
    ctx.stroke();
  }

  return canvas.toBuffer('image/png');
}

async function main() {
  const args = process.argv.slice(2);
  const fontFilter = args.find(a => a.startsWith('--font='))?.split('=')[1];
  const charFilter = args.find(a => a.startsWith('--char='))?.split('=')[1];
  const typeFilter = args.find(a => a.startsWith('--type='))?.split('=')[1];

  // Create output directory
  const outDir = join(ROOT, 'scripts/char-renders');
  await mkdir(outDir, { recursive: true });

  // Register fonts
  const { registerFont } = await import('canvas');
  for (const font of FONTS) {
    const fontPath = join(ROOT, 'public/fonts', `${font.name}.ttf`);
    try {
      registerFont(fontPath, { family: font.display });
      console.log(`Registered font: ${font.display}`);
    } catch (e) {
      console.error(`Failed to register ${font.name}:`, e.message);
    }
  }

  let chars = [];
  if (charFilter) {
    chars = [charFilter];
  } else if (typeFilter === 'upper') {
    chars = UPPERCASE;
  } else if (typeFilter === 'lower') {
    chars = LOWERCASE;
  } else if (typeFilter === 'numbers') {
    chars = NUMBERS;
  } else {
    chars = [...UPPERCASE, ...LOWERCASE, ...NUMBERS];
  }

  const fontsToProcess = fontFilter
    ? FONTS.filter(f => f.file.toLowerCase().includes(fontFilter.toLowerCase()))
    : FONTS;

  for (const font of fontsToProcess) {
    const fontDir = join(outDir, font.file);
    await mkdir(fontDir, { recursive: true });

    console.log(`\nRendering ${font.display}...`);

    for (const char of chars) {
      const safeName = char.match(/[A-Z]/) ? `upper_${char}` :
                       char.match(/[a-z]/) ? `lower_${char}` :
                       `num_${char}`;

      const buffer = await renderCharacter(char, null, font.display);
      const outPath = join(fontDir, `${safeName}.png`);
      await writeFile(outPath, buffer);
      process.stdout.write(`  ${char}`);
    }
    console.log('\n  Done');
  }

  console.log(`\nImages saved to: ${outDir}`);
}

main().catch(console.error);
