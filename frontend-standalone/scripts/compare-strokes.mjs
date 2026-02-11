#!/usr/bin/env node
/**
 * Compare stroke coordinates against actual trace
 * Renders character + stroke guides overlaid to check alignment
 */

import puppeteer from 'puppeteer';
import { mkdir, writeFile, readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

async function compareCharacter(page, char, fontFamily, strokeData, size = 400) {
  // Convert stroke points to SVG path
  function pointsToPath(points) {
    if (!points || points.length < 2) return '';
    const scaled = points.map(p => [p[0] * size / 100, p[1] * size / 100]);
    let d = `M ${scaled[0][0]} ${scaled[0][1]}`;
    for (let i = 1; i < scaled.length; i++) {
      d += ` L ${scaled[i][0]} ${scaled[i][1]}`;
    }
    return d;
  }

  const strokes = strokeData?.strokes || [];
  const strokePaths = strokes.map((s, i) => {
    const path = pointsToPath(s.points);
    const start = s.points[0];
    const end = s.points[s.points.length - 1];
    return { path, start, end, index: i };
  });

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
          color: rgba(0, 0, 0, 0.3);
          text-align: center;
          line-height: 1;
        }
        .overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        .stroke-path {
          fill: none;
          stroke: #4ECDC4;
          stroke-width: 8;
          stroke-linecap: round;
          stroke-linejoin: round;
        }
        .start-zone {
          fill: rgba(76, 175, 80, 0.5);
          stroke: #4CAF50;
          stroke-width: 2;
        }
        .end-zone {
          fill: rgba(255, 152, 0, 0.5);
          stroke: #FF9800;
          stroke-width: 2;
        }
        .stroke-number {
          font-family: Arial;
          font-size: 14px;
          font-weight: bold;
          fill: white;
        }
        .grid line {
          stroke: rgba(0, 0, 255, 0.15);
          stroke-width: 0.5;
        }
        .grid text {
          font-family: Arial;
          font-size: 8px;
          fill: blue;
        }
      </style>
    </head>
    <body>
      <div class="char">${char === '<' ? '&lt;' : char === '>' ? '&gt;' : char === '&' ? '&amp;' : char}</div>
      <svg class="overlay" viewBox="0 0 ${size} ${size}">
        <!-- Grid every 10 units -->
        <g class="grid">
          ${[10,20,30,40,50,60,70,80,90].map(i => `
            <line x1="${i * size/100}" y1="0" x2="${i * size/100}" y2="${size}"/>
            <line x1="0" y1="${i * size/100}" x2="${size}" y2="${i * size/100}"/>
          `).join('')}
          ${[0,10,20,30,40,50,60,70,80,90,100].map(i => `
            <text x="${i * size/100 + 2}" y="10">${i}</text>
          `).join('')}
          ${[10,20,30,40,50,60,70,80,90,100].map(i => `
            <text x="2" y="${i * size/100 - 2}">${i}</text>
          `).join('')}
        </g>

        <!-- Stroke paths -->
        ${strokePaths.map(s => `<path class="stroke-path" d="${s.path}"/>`).join('')}

        <!-- Start zones (green) -->
        ${strokePaths.map(s => `
          <circle class="start-zone" cx="${s.start[0] * size/100}" cy="${s.start[1] * size/100}" r="20"/>
          <text class="stroke-number" x="${s.start[0] * size/100 - 4}" y="${s.start[1] * size/100 + 4}">${s.index + 1}</text>
        `).join('')}

        <!-- End zones (orange) -->
        ${strokePaths.map(s => `
          <circle class="end-zone" cx="${s.end[0] * size/100}" cy="${s.end[1] * size/100}" r="15"/>
        `).join('')}
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
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1] || 'P';

  // Load stroke data
  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));

  const fontMap = {
    'schoolbell': 'Schoolbell',
    'fredoka': 'Fredoka',
    'nunito': 'Nunito',
    'patrick-hand': 'Patrick Hand',
    'playwrite-us': 'Playwrite US Modern'
  };

  const fontFamily = fontMap[fontArg] || 'Schoolbell';

  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  const outDir = join(ROOT, 'scripts/comparison');
  await mkdir(outDir, { recursive: true });

  const chars = charArg.split(',');

  for (const char of chars) {
    const strokeData = strokeFile.characters[char];
    if (!strokeData) {
      console.log(`No stroke data for '${char}'`);
      continue;
    }

    const buffer = await compareCharacter(page, char, fontFamily, strokeData);
    const safeName = char.match(/[A-Z]/) ? `upper_${char}` :
                     char.match(/[a-z]/) ? `lower_${char}` :
                     `num_${char}`;
    const outPath = join(outDir, `${fontArg}_${safeName}.png`);
    await writeFile(outPath, buffer);
    console.log(`Comparison saved: ${outPath}`);
    console.log(`  Strokes: ${strokeData.strokes.length}`);
    strokeData.strokes.forEach((s, i) => {
      console.log(`    ${i+1}. ${s.direction}: [${s.points[0]}] -> [${s.points[s.points.length-1]}]`);
    });
  }

  await browser.close();
}

main().catch(console.error);
