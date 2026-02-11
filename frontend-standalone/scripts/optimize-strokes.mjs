#!/usr/bin/env node
/**
 * Optimize stroke coordinates for a character by iteratively adjusting points
 * Usage: node scripts/optimize-strokes.mjs --font=schoolbell --char=C [--target=95]
 */

import puppeteer from 'puppeteer';
import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join, extname } from 'path';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const FONT_MAP = {
  'schoolbell': 'Schoolbell-Regular',
  'fredoka': 'Fredoka-Regular',
  'nunito': 'Nunito-Regular',
  'patrick-hand': 'PatrickHand-Regular',
  'playwrite-us': 'PlaywriteUS-Regular'
};

async function scoreStrokes(page, char, fontName, strokes, lineWidth = 24, size = 400) {
  const fontFileName = FONT_MAP[fontName];

  const html = `<!DOCTYPE html>
<html>
<head><style>* { margin: 0; padding: 0; }</style></head>
<body>
  <canvas id="canvas" width="${size}" height="${size}"></canvas>
  <script type="module">
    import init, { score_drawing } from '/src/wasm-pkg/learning_letters_scoring.js';

    async function run() {
      try {
        await init();
        const fontRes = await fetch('/fonts/${fontFileName}.ttf');
        const fontData = new Uint8Array(await fontRes.arrayBuffer());

        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, ${size}, ${size});

        const strokes = ${JSON.stringify(strokes)};
        ctx.strokeStyle = 'black';
        ctx.lineWidth = ${lineWidth};
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        const scale = ${size} / 100;
        for (const stroke of strokes) {
          if (!stroke.points || stroke.points.length < 2) continue;
          ctx.beginPath();
          ctx.moveTo(stroke.points[0][0] * scale, stroke.points[0][1] * scale);
          for (let i = 1; i < stroke.points.length; i++) {
            ctx.lineTo(stroke.points[i][0] * scale, stroke.points[i][1] * scale);
          }
          ctx.stroke();
        }

        const userBlob = await new Promise(r => canvas.toBlob(r, 'image/png'));
        const userPng = new Uint8Array(await userBlob.arrayBuffer());
        const result = score_drawing(userPng, '${char}', fontData);

        window.testResult = {
          score: result.score,
          coverage: result.coverage,
          accuracy: result.accuracy,
          similarity: result.similarity,
          success: true
        };
      } catch (e) {
        window.testResult = { error: e.message, success: false };
      }
    }
    run();
  </script>
</body>
</html>`;

  // Use page.setContent would have CORS issues, so we'll embed in server
  return { html, char };
}

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1] || 'C';
  const targetArg = args.find(a => a.startsWith('--target='))?.split('=')[1] || '95';
  const lineWidthArg = args.find(a => a.startsWith('--linewidth='))?.split('=')[1] || '24';
  const target = parseInt(targetArg);
  const lineWidth = parseInt(lineWidthArg);
  const size = 400;

  // Load stroke data
  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const charData = strokeFile.characters[charArg];

  if (!charData || !charData.strokes) {
    console.error(`No stroke data for '${charArg}'`);
    process.exit(1);
  }

  console.log(`Optimizing ${fontArg} "${charArg}" (target: ${target}%, lineWidth: ${lineWidth})`);

  const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.wasm': 'application/wasm',
    '.ttf': 'font/ttf',
    '.json': 'application/json'
  };

  let currentStrokes = JSON.parse(JSON.stringify(charData.strokes));
  let currentHtml = '';

  function generateHtml(strokes) {
    const fontFileName = FONT_MAP[fontArg];
    return `<!DOCTYPE html>
<html>
<head><style>* { margin: 0; padding: 0; }</style></head>
<body>
  <canvas id="canvas" width="${size}" height="${size}"></canvas>
  <script type="module">
    import init, { score_drawing } from '/src/wasm-pkg/learning_letters_scoring.js';

    async function run() {
      try {
        await init();
        const fontRes = await fetch('/fonts/${fontFileName}.ttf');
        const fontData = new Uint8Array(await fontRes.arrayBuffer());

        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, ${size}, ${size});

        const strokes = ${JSON.stringify(strokes)};
        ctx.strokeStyle = 'black';
        ctx.lineWidth = ${lineWidth};
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        const scale = ${size} / 100;
        for (const stroke of strokes) {
          if (!stroke.points || stroke.points.length < 2) continue;
          ctx.beginPath();
          ctx.moveTo(stroke.points[0][0] * scale, stroke.points[0][1] * scale);
          for (let i = 1; i < stroke.points.length; i++) {
            ctx.lineTo(stroke.points[i][0] * scale, stroke.points[i][1] * scale);
          }
          ctx.stroke();
        }

        const userBlob = await new Promise(r => canvas.toBlob(r, 'image/png'));
        const userPng = new Uint8Array(await userBlob.arrayBuffer());
        const result = score_drawing(userPng, '${charArg}', fontData);

        window.testResult = {
          score: result.score,
          coverage: result.coverage,
          accuracy: result.accuracy,
          similarity: result.similarity,
          success: true
        };
      } catch (e) {
        window.testResult = { error: e.message, success: false };
      }
    }
    run();
  </script>
</body>
</html>`;
  }

  currentHtml = generateHtml(currentStrokes);

  const server = createServer((req, res) => {
    if (req.url === '/test.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(currentHtml);
      return;
    }

    let filePath = join(ROOT, req.url);
    if (!existsSync(filePath)) {
      filePath = join(ROOT, 'public', req.url);
    }

    if (existsSync(filePath)) {
      const ext = extname(filePath);
      res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
      res.end(readFileSync(filePath));
    } else {
      res.writeHead(404);
      res.end('Not found');
    }
  });

  await new Promise(resolve => server.listen(3465, resolve));

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // Score function with retry logic and page recreation
  let activePage = page;
  async function score(strokes, retries = 3) {
    currentHtml = generateHtml(strokes);
    for (let i = 0; i < retries; i++) {
      try {
        await new Promise(r => setTimeout(r, 100));
        await activePage.goto('http://localhost:3465/test.html', { waitUntil: 'networkidle0', timeout: 30000 });
        await activePage.waitForFunction('window.testResult !== undefined', { timeout: 15000 });
        return await activePage.evaluate(() => window.testResult);
      } catch (e) {
        if (e.message.includes('detached') || e.message.includes('Target closed')) {
          // Create new page on frame detachment
          try { await activePage.close(); } catch {}
          activePage = await browser.newPage();
        }
        if (i === retries - 1) throw e;
        await new Promise(r => setTimeout(r, 300));
      }
    }
  }

  // Get initial score
  let result = await score(currentStrokes);
  if (!result.success) {
    console.error('Initial scoring failed:', result.error);
    await browser.close();
    server.close();
    process.exit(1);
  }

  let currentScore = result.score;
  console.log(`Initial score: ${currentScore}%`);

  if (currentScore >= target) {
    console.log('Already meets target!');
    await browser.close();
    server.close();
    process.exit(0);
  }

  // Optimization loop
  const deltas = [
    [3, 0], [-3, 0], [0, 3], [0, -3],
    [2, 2], [2, -2], [-2, 2], [-2, -2],
    [5, 0], [-5, 0], [0, 5], [0, -5]
  ];

  let iteration = 0;
  const maxIterations = 50;
  let improved = true;

  while (currentScore < target && iteration < maxIterations && improved) {
    improved = false;
    iteration++;
    console.log(`\nIteration ${iteration} (current: ${currentScore}%)`);

    // Try adjusting each point
    for (let s = 0; s < currentStrokes.length; s++) {
      for (let p = 0; p < currentStrokes[s].points.length; p++) {
        let bestDelta = null;
        let bestScore = currentScore;

        for (const delta of deltas) {
          const testStrokes = JSON.parse(JSON.stringify(currentStrokes));
          testStrokes[s].points[p] = [
            currentStrokes[s].points[p][0] + delta[0],
            currentStrokes[s].points[p][1] + delta[1]
          ];

          const testResult = await score(testStrokes);
          if (testResult.success && testResult.score > bestScore) {
            bestScore = testResult.score;
            bestDelta = delta;
          }
        }

        if (bestDelta) {
          currentStrokes[s].points[p] = [
            currentStrokes[s].points[p][0] + bestDelta[0],
            currentStrokes[s].points[p][1] + bestDelta[1]
          ];
          currentScore = bestScore;
          improved = true;
          console.log(`  Stroke ${s+1}, point ${p+1}: +${bestDelta} -> ${currentScore}%`);

          if (currentScore >= target) break;
        }
      }
      if (currentScore >= target) break;
    }
  }

  await browser.close();
  server.close();

  console.log(`\nFinal score: ${currentScore}%`);

  if (currentScore >= target) {
    console.log('Target achieved! Saving...');
    strokeFile.characters[charArg].strokes = currentStrokes;
    await writeFile(strokePath, JSON.stringify(strokeFile, null, 2));
    console.log('Saved updated strokes.');
  } else {
    console.log(`Could not reach target. Best: ${currentScore}%`);
    console.log('Optimized strokes (not saved):');
    console.log(JSON.stringify(currentStrokes, null, 2));
  }
}

main().catch(console.error);
