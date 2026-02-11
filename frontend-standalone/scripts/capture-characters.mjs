#!/usr/bin/env node
/**
 * Capture rendered characters as PNG images for visual analysis
 * Uses Puppeteer to render with actual browser font rendering
 */

import puppeteer from 'puppeteer';
import { mkdir, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const FONTS = [
  { name: 'Schoolbell-Regular', file: 'schoolbell', family: 'Schoolbell' },
  { name: 'Fredoka-Regular', file: 'fredoka', family: 'Fredoka' },
  { name: 'Nunito-Regular', file: 'nunito', family: 'Nunito' },
  { name: 'PatrickHand-Regular', file: 'patrick-hand', family: 'Patrick Hand' },
  { name: 'PlaywriteUS-Regular', file: 'playwrite-us', family: 'Playwrite US Modern' },
];

async function captureCharacter(page, char, fontFamily, size = 200) {
  // Create an HTML page that renders the character
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        @font-face {
          font-family: '${fontFamily}';
          src: url('file://${ROOT}/public/fonts/${fontFamily.replace(/ /g, '')}-Regular.ttf');
        }
        body {
          margin: 0;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          width: ${size}px;
          height: ${size}px;
          background: white;
        }
        .char {
          font-family: '${fontFamily}', sans-serif;
          font-size: ${size * 0.75}px;
          color: #333;
          text-align: center;
          line-height: ${size}px;
        }
        .grid {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        .grid line {
          stroke: rgba(0, 150, 255, 0.2);
          stroke-width: 1;
        }
      </style>
    </head>
    <body>
      <div class="char">${char === '<' ? '&lt;' : char === '>' ? '&gt;' : char === '&' ? '&amp;' : char}</div>
      <svg class="grid" viewBox="0 0 100 100">
        <line x1="25" y1="0" x2="25" y2="100"/>
        <line x1="50" y1="0" x2="50" y2="100"/>
        <line x1="75" y1="0" x2="75" y2="100"/>
        <line x1="0" y1="25" x2="100" y2="25"/>
        <line x1="0" y1="50" x2="100" y2="50"/>
        <line x1="0" y1="75" x2="100" y2="75"/>
      </svg>
    </body>
    </html>
  `;

  await page.setContent(html);
  await page.setViewport({ width: size, height: size });

  // Wait for fonts to load
  await page.evaluate(() => document.fonts.ready);

  return await page.screenshot({ type: 'png' });
}

async function main() {
  const args = process.argv.slice(2);
  const fontFilter = args.find(a => a.startsWith('--font='))?.split('=')[1];
  const charFilter = args.find(a => a.startsWith('--char='))?.split('=')[1];
  const typeFilter = args.find(a => a.startsWith('--type='))?.split('=')[1];

  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  let chars = [];
  if (charFilter) {
    chars = charFilter.split(',');
  } else if (typeFilter === 'upper') {
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  } else if (typeFilter === 'lower') {
    chars = 'abcdefghijklmnopqrstuvwxyz'.split('');
  } else if (typeFilter === 'numbers') {
    chars = '0123456789'.split('');
  } else {
    chars = [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ', ...'abcdefghijklmnopqrstuvwxyz', ...'0123456789'];
  }

  const fontsToProcess = fontFilter
    ? FONTS.filter(f => f.file.toLowerCase().includes(fontFilter.toLowerCase()))
    : FONTS;

  const outDir = join(ROOT, 'scripts/char-renders');
  await mkdir(outDir, { recursive: true });

  for (const font of fontsToProcess) {
    const fontDir = join(outDir, font.file);
    await mkdir(fontDir, { recursive: true });

    console.log(`\nCapturing ${font.family}...`);

    for (const char of chars) {
      const safeName = char.match(/[A-Z]/) ? `upper_${char}` :
                       char.match(/[a-z]/) ? `lower_${char}` :
                       `num_${char}`;

      try {
        const buffer = await captureCharacter(page, char, font.family);
        const outPath = join(fontDir, `${safeName}.png`);
        await writeFile(outPath, buffer);
        process.stdout.write(`  ${char}`);
      } catch (e) {
        console.error(`\n  Error capturing ${char}: ${e.message}`);
      }
    }
    console.log('\n  Done');
  }

  await browser.close();
  console.log(`\nImages saved to: ${outDir}`);
}

main().catch(console.error);
