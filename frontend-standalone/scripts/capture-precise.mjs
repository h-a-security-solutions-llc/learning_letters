#!/usr/bin/env node
/**
 * Capture characters with precise 10-unit grid for accurate coordinate tracing
 * Matches the app's rendering: character centered in canvas with 0-100 coordinate space
 */

import puppeteer from 'puppeteer';
import { mkdir, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const FONTS = [
  { name: 'Schoolbell-Regular', file: 'schoolbell', family: 'Schoolbell' },
];

async function captureCharacter(page, char, fontFamily, size = 400) {
  // Render at 400px with 10-unit grid lines (every 40px = 10 units in 0-100 space)
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        @font-face {
          font-family: '${fontFamily}';
          src: url('file://${ROOT}/public/fonts/${fontFamily.replace(/ /g, '')}-Regular.ttf');
        }
        * { margin: 0; padding: 0; }
        body {
          width: ${size}px;
          height: ${size}px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          position: relative;
        }
        .char {
          font-family: '${fontFamily}', sans-serif;
          font-size: ${size * 0.7}px;
          color: #333;
          text-align: center;
          line-height: 1;
        }
        .grid {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        .grid line.major {
          stroke: rgba(255, 0, 0, 0.4);
          stroke-width: 1;
        }
        .grid line.minor {
          stroke: rgba(0, 0, 255, 0.2);
          stroke-width: 0.5;
        }
        .grid text {
          font-family: Arial, sans-serif;
          font-size: 10px;
          fill: red;
        }
      </style>
    </head>
    <body>
      <div class="char">${char === '<' ? '&lt;' : char === '>' ? '&gt;' : char === '&' ? '&amp;' : char}</div>
      <svg class="grid" viewBox="0 0 100 100">
        <!-- 10-unit grid lines -->
        ${[10,20,30,40,50,60,70,80,90].map(i => `
          <line class="minor" x1="${i}" y1="0" x2="${i}" y2="100"/>
          <line class="minor" x1="0" y1="${i}" x2="100" y2="${i}"/>
        `).join('')}
        <!-- 25-unit major grid lines -->
        ${[25,50,75].map(i => `
          <line class="major" x1="${i}" y1="0" x2="${i}" y2="100"/>
          <line class="major" x1="0" y1="${i}" x2="100" y2="${i}"/>
        `).join('')}
        <!-- Coordinate labels -->
        <text x="1" y="8">0</text>
        <text x="23" y="8">25</text>
        <text x="48" y="8">50</text>
        <text x="73" y="8">75</text>
        <text x="1" y="27">25</text>
        <text x="1" y="52">50</text>
        <text x="1" y="77">75</text>
      </svg>
    </body>
    </html>
  `;

  await page.setContent(html);
  await page.setViewport({ width: size, height: size });
  await page.evaluate(() => document.fonts.ready);

  return await page.screenshot({ type: 'png' });
}

async function main() {
  const args = process.argv.slice(2);
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1];

  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  const chars = charArg ? charArg.split(',') : ['P'];
  const font = FONTS[0]; // Schoolbell

  const outDir = join(ROOT, 'scripts/precise-renders');
  await mkdir(outDir, { recursive: true });

  for (const char of chars) {
    const safeName = char.match(/[A-Z]/) ? `upper_${char}` :
                     char.match(/[a-z]/) ? `lower_${char}` :
                     `num_${char}`;

    const buffer = await captureCharacter(page, char, font.family);
    const outPath = join(outDir, `${font.file}_${safeName}.png`);
    await writeFile(outPath, buffer);
    console.log(`Captured: ${char} -> ${outPath}`);
  }

  await browser.close();
  console.log('Done!');
}

main().catch(console.error);
