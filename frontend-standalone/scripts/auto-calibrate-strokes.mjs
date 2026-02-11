#!/usr/bin/env node
/**
 * Auto-calibrate stroke coordinates by scoring against WASM reference
 * Iterates until score > 95%
 */

import puppeteer from 'puppeteer';
import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { extname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.wasm': 'application/wasm',
  '.ttf': 'font/ttf',
  '.json': 'application/json',
  '.png': 'image/png'
};

async function createTestServer() {
  const server = createServer((req, res) => {
    let filePath = join(ROOT, req.url === '/' ? 'index.html' : req.url);

    if (!existsSync(filePath)) {
      filePath = join(ROOT, 'public', req.url);
    }

    if (existsSync(filePath)) {
      const ext = extname(filePath);
      const contentType = mimeTypes[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(readFileSync(filePath));
    } else {
      res.writeHead(404);
      res.end('Not found: ' + req.url);
    }
  });

  await new Promise(resolve => server.listen(3457, resolve));
  return server;
}

async function scoreStrokes(page, character, fontName, strokes, size = 400) {
  const fontMap = {
    'schoolbell': 'Schoolbell-Regular',
    'fredoka': 'Fredoka-Regular',
    'nunito': 'Nunito-Regular',
    'patrick-hand': 'PatrickHand-Regular',
    'playwrite-us': 'PlaywriteUS-Regular'
  };

  const fontFileName = fontMap[fontName];

  // Create test page that loads WASM and scores the strokes
  const html = `
    <!DOCTYPE html>
    <html>
    <head><style>* { margin: 0; padding: 0; }</style></head>
    <body>
      <canvas id="canvas" width="${size}" height="${size}"></canvas>
      <script type="module">
        import init, { generate_reference_image, calculate_similarity } from '/src/wasm-pkg/learning_letters_scoring.js';

        async function run() {
          await init();

          // Load font
          const fontResponse = await fetch('/fonts/${fontFileName}.ttf');
          const fontBuffer = await fontResponse.arrayBuffer();
          const fontData = new Uint8Array(fontBuffer);

          // Generate reference image
          const refPng = generate_reference_image('${character}', fontData, ${size});

          // Create user canvas with strokes
          const canvas = document.getElementById('canvas');
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = 'white';
          ctx.fillRect(0, 0, ${size}, ${size});

          // Draw strokes
          const strokes = ${JSON.stringify(strokes)};
          ctx.strokeStyle = 'black';
          ctx.lineWidth = 12;
          ctx.lineCap = 'round';
          ctx.lineJoin = 'round';

          for (const stroke of strokes) {
            if (stroke.points.length < 2) continue;
            ctx.beginPath();
            const scale = ${size} / 100;
            ctx.moveTo(stroke.points[0][0] * scale, stroke.points[0][1] * scale);
            for (let i = 1; i < stroke.points.length; i++) {
              ctx.lineTo(stroke.points[i][0] * scale, stroke.points[i][1] * scale);
            }
            ctx.stroke();
          }

          // Get user image as PNG
          const userBlob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
          const userBuffer = await userBlob.arrayBuffer();
          const userPng = new Uint8Array(userBuffer);

          // Calculate similarity
          const score = calculate_similarity(userPng, refPng);
          window.strokeScore = score;
        }

        run().catch(e => { window.strokeError = e.message; });
      </script>
    </body>
    </html>
  `;

  await page.setContent(html);

  // Wait for score calculation
  await page.waitForFunction('window.strokeScore !== undefined || window.strokeError !== undefined', { timeout: 15000 });

  const result = await page.evaluate(() => ({
    score: window.strokeScore,
    error: window.strokeError
  }));

  if (result.error) {
    throw new Error(result.error);
  }

  return result.score;
}

// Adjust a single coordinate slightly
function perturbCoord(coord, delta) {
  return [coord[0] + delta[0], coord[1] + delta[1]];
}

// Try small adjustments to improve score
async function optimizeStroke(page, character, fontName, strokes, strokeIdx, pointIdx, currentScore) {
  const deltas = [
    [2, 0], [-2, 0], [0, 2], [0, -2],
    [1, 1], [1, -1], [-1, 1], [-1, -1]
  ];

  let bestScore = currentScore;
  let bestDelta = null;

  for (const delta of deltas) {
    const testStrokes = JSON.parse(JSON.stringify(strokes));
    testStrokes[strokeIdx].points[pointIdx] = perturbCoord(
      strokes[strokeIdx].points[pointIdx],
      delta
    );

    try {
      const score = await scoreStrokes(page, character, fontName, testStrokes);
      if (score > bestScore) {
        bestScore = score;
        bestDelta = delta;
      }
    } catch (e) {
      // Skip failed attempts
    }
  }

  return { bestScore, bestDelta };
}

async function calibrateCharacter(page, character, fontName, initialStrokes, targetScore = 0.95) {
  let strokes = JSON.parse(JSON.stringify(initialStrokes));
  let currentScore = await scoreStrokes(page, character, fontName, strokes);

  console.log(`Initial score for ${character}: ${(currentScore * 100).toFixed(1)}%`);

  let iterations = 0;
  const maxIterations = 100;

  while (currentScore < targetScore && iterations < maxIterations) {
    let improved = false;

    // Try optimizing each point
    for (let s = 0; s < strokes.length; s++) {
      for (let p = 0; p < strokes[s].points.length; p++) {
        const { bestScore, bestDelta } = await optimizeStroke(
          page, character, fontName, strokes, s, p, currentScore
        );

        if (bestDelta && bestScore > currentScore) {
          strokes[s].points[p] = perturbCoord(strokes[s].points[p], bestDelta);
          currentScore = bestScore;
          improved = true;
          console.log(`  Adjusted stroke ${s+1} point ${p+1}: ${(currentScore * 100).toFixed(1)}%`);
        }
      }
    }

    if (!improved) {
      console.log('  No improvement found, stopping');
      break;
    }

    iterations++;
  }

  console.log(`Final score for ${character}: ${(currentScore * 100).toFixed(1)}% after ${iterations} iterations`);
  return { strokes, score: currentScore };
}

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1] || 'P';
  const targetArg = args.find(a => a.startsWith('--target='))?.split('=')[1] || '95';
  const targetScore = parseInt(targetArg) / 100;

  console.log(`Calibrating ${charArg} for ${fontArg} font (target: ${targetArg}%)`);

  // Load current stroke data
  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const charData = strokeFile.characters[charArg];

  if (!charData) {
    console.error(`No stroke data for '${charArg}'`);
    process.exit(1);
  }

  console.log('Starting server...');
  const server = await createTestServer();

  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.goto('http://localhost:3457/');

  try {
    const { strokes, score } = await calibrateCharacter(
      page, charArg, fontArg, charData.strokes, targetScore
    );

    if (score >= targetScore) {
      console.log('\nTarget score achieved! Saving...');
      strokeFile.characters[charArg].strokes = strokes;
      await writeFile(strokePath, JSON.stringify(strokeFile, null, 2));
      console.log('Saved updated strokes');
    } else {
      console.log(`\nCould not reach target score. Best: ${(score * 100).toFixed(1)}%`);
      console.log('Optimized strokes (not saved):');
      console.log(JSON.stringify(strokes, null, 2));
    }
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch(console.error);
