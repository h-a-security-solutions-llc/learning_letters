#!/usr/bin/env node
/**
 * Score stroke coordinates against font reference
 * Generates an image from strokes and compares to WASM reference
 */

import puppeteer from 'puppeteer';
import { readFile, writeFile, mkdir } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { extname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1] || 'P';

  const fontMap = {
    'schoolbell': 'Schoolbell-Regular',
    'fredoka': 'Fredoka-Regular',
    'nunito': 'Nunito-Regular',
    'patrick-hand': 'PatrickHand-Regular',
    'playwrite-us': 'PlaywriteUS-Regular'
  };

  const fontFileName = fontMap[fontArg];
  const size = 400;

  // Load stroke data
  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const charData = strokeFile.characters[charArg];

  if (!charData) {
    console.error(`No stroke data for '${charArg}'`);
    process.exit(1);
  }

  const strokes = charData.strokes;

  // Create server
  const mimeTypes = {
    '.html': 'text/html', '.js': 'application/javascript',
    '.wasm': 'application/wasm', '.ttf': 'font/ttf',
    '.json': 'application/json', '.png': 'image/png'
  };

  const server = createServer((req, res) => {
    let filePath = join(ROOT, req.url === '/' ? 'index.html' : req.url);
    if (!existsSync(filePath)) filePath = join(ROOT, 'public', req.url);

    if (req.url === '/test-score.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(createTestHtml(charArg, fontFileName, strokes, size));
      return;
    }

    if (existsSync(filePath)) {
      const ext = extname(filePath);
      res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
      res.end(readFileSync(filePath));
    } else {
      res.writeHead(404);
      res.end('Not found: ' + req.url);
    }
  });

  await new Promise(resolve => server.listen(3460, resolve));

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') console.error('Page error:', msg.text());
  });

  try {
    await page.goto('http://localhost:3460/test-score.html', { waitUntil: 'networkidle2', timeout: 30000 });
  } catch (e) {
    console.log('Navigation warning:', e.message);
  }

  // Wait for result with longer timeout
  try {
    await page.waitForFunction('window.testResult !== undefined', { timeout: 30000 });
    const result = await page.evaluate(() => window.testResult);

    console.log(`\nCharacter: ${charArg}`);
    console.log(`Font: ${fontArg}`);
    console.log(`Score: ${(result.score * 100).toFixed(1)}%`);
    console.log(`Target: 95%`);
    console.log(`Status: ${result.score >= 0.95 ? 'PASS' : 'FAIL'}`);

    // Save debug images
    const outDir = join(ROOT, 'scripts/score-test');
    await mkdir(outDir, { recursive: true });

    if (result.userImageUrl) {
      const safeName = charArg.match(/[A-Z]/) ? `upper_${charArg}` :
                       charArg.match(/[a-z]/) ? `lower_${charArg}` : `num_${charArg}`;

      // Take screenshot
      await page.screenshot({ path: join(outDir, `${fontArg}_${safeName}_test.png`) });
      console.log(`\nSaved test image to scripts/score-test/`);
    }

  } catch (e) {
    console.error('Error:', e.message);
    // Take screenshot for debugging
    await page.screenshot({ path: join(ROOT, 'scripts/debug-error.png') });
  }

  await browser.close();
  server.close();
}

function createTestHtml(char, fontFileName, strokes, size) {
  return `
<!DOCTYPE html>
<html>
<head>
  <style>
    * { margin: 0; padding: 0; }
    body { background: white; display: flex; gap: 20px; padding: 20px; }
    .panel { text-align: center; }
    canvas, img { border: 1px solid #ccc; }
    h3 { margin-bottom: 10px; font: 14px Arial; }
  </style>
</head>
<body>
  <div class="panel">
    <h3>Reference (WASM)</h3>
    <img id="ref" width="${size}" height="${size}">
  </div>
  <div class="panel">
    <h3>User Strokes</h3>
    <canvas id="user" width="${size}" height="${size}"></canvas>
  </div>
  <div class="panel">
    <h3>Score</h3>
    <div id="score" style="font: bold 48px Arial; margin-top: 150px;">-</div>
  </div>

  <script type="module">
    import init, { generate_reference_image, calculate_similarity } from '/src/wasm-pkg/learning_letters_scoring.js';

    async function run() {
      try {
        await init();

        // Load font
        const fontResponse = await fetch('/fonts/${fontFileName}.ttf');
        const fontBuffer = await fontResponse.arrayBuffer();
        const fontData = new Uint8Array(fontBuffer);

        // Generate reference
        const refPng = generate_reference_image('${char}', fontData, ${size});
        const refBlob = new Blob([refPng], { type: 'image/png' });
        const refUrl = URL.createObjectURL(refBlob);
        document.getElementById('ref').src = refUrl;

        // Draw user strokes
        const canvas = document.getElementById('user');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, ${size}, ${size});

        const strokes = ${JSON.stringify(strokes)};
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 12;
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

        // Get user image as PNG
        const userBlob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
        const userBuffer = await userBlob.arrayBuffer();
        const userPng = new Uint8Array(userBuffer);

        // Calculate score
        const score = calculate_similarity(userPng, refPng);
        document.getElementById('score').textContent = (score * 100).toFixed(1) + '%';
        document.getElementById('score').style.color = score >= 0.95 ? 'green' : 'red';

        window.testResult = {
          score: score,
          userImageUrl: canvas.toDataURL()
        };

      } catch (e) {
        console.error('Error:', e);
        document.getElementById('score').textContent = 'Error';
        window.testResult = { score: 0, error: e.message };
      }
    }

    run();
  </script>
</body>
</html>`;
}

main().catch(console.error);
