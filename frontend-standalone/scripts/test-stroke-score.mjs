#!/usr/bin/env node
/**
 * Test stroke scoring - generates image from strokes and scores against WASM reference
 */

import puppeteer from 'puppeteer';
import { mkdir, writeFile, readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1] || 'P';

  // Load stroke data
  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const charData = strokeFile.characters[charArg];

  if (!charData) {
    console.error(`No stroke data for '${charArg}'`);
    process.exit(1);
  }

  const fontMap = {
    'schoolbell': 'Schoolbell-Regular',
    'fredoka': 'Fredoka-Regular',
    'nunito': 'Nunito-Regular',
    'patrick-hand': 'PatrickHand-Regular',
    'playwrite-us': 'PlaywriteUS-Regular'
  };

  const fontFileName = fontMap[fontArg];
  const size = 400;
  const strokes = charData.strokes;

  // Start server
  const { createServer } = await import('http');
  const { readFileSync, existsSync } = await import('fs');
  const { extname } = await import('path');

  const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.wasm': 'application/wasm',
    '.ttf': 'font/ttf',
    '.json': 'application/json',
    '.png': 'image/png'
  };

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        * { margin: 0; padding: 0; }
        body { display: flex; gap: 20px; padding: 20px; font-family: Arial; }
        .panel { text-align: center; }
        h3 { margin-bottom: 10px; }
      </style>
    </head>
    <body>
      <div class="panel">
        <h3>Reference</h3>
        <img id="ref" width="${size}" height="${size}" style="border:1px solid #ccc">
      </div>
      <div class="panel">
        <h3>Strokes</h3>
        <canvas id="user" width="${size}" height="${size}" style="border:1px solid #ccc"></canvas>
      </div>
      <div class="panel">
        <h3>Score</h3>
        <div id="score" style="font-size:48px;margin-top:150px">...</div>
      </div>
      <script type="module">
        import init, { generate_reference_image, calculate_similarity } from '/src/wasm-pkg/learning_letters_scoring.js';

        async function run() {
          await init();

          // Load font
          const fontRes = await fetch('/fonts/${fontFileName}.ttf');
          const fontBuf = await fontRes.arrayBuffer();
          const fontData = new Uint8Array(fontBuf);

          // Generate reference
          const refPng = generate_reference_image('${charArg}', fontData, ${size});
          const refBlob = new Blob([refPng], { type: 'image/png' });
          document.getElementById('ref').src = URL.createObjectURL(refBlob);

          // Draw strokes on canvas
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

          // Get user image
          const userBlob = await new Promise(r => canvas.toBlob(r, 'image/png'));
          const userBuf = await userBlob.arrayBuffer();
          const userPng = new Uint8Array(userBuf);

          // Score
          const score = calculate_similarity(userPng, refPng);
          const pct = (score * 100).toFixed(1);
          document.getElementById('score').textContent = pct + '%';
          document.getElementById('score').style.color = score >= 0.95 ? 'green' : score >= 0.8 ? 'orange' : 'red';

          window.testScore = score;
        }

        run().catch(e => {
          document.getElementById('score').textContent = 'Error: ' + e.message;
          window.testScore = -1;
        });
      </script>
    </body>
    </html>
  `;

  const server = createServer((req, res) => {
    if (req.url === '/test.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(html);
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
      res.end('Not found: ' + req.url);
    }
  });

  await new Promise(resolve => server.listen(3461, resolve));
  console.log('Server running on port 3461');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  await page.goto('http://localhost:3461/test.html');
  await page.waitForFunction('window.testScore !== undefined', { timeout: 15000 });

  const score = await page.evaluate(() => window.testScore);

  // Save screenshot
  const outDir = join(ROOT, 'scripts/stroke-scores');
  await mkdir(outDir, { recursive: true });
  const safeName = charArg.match(/[A-Z]/) ? `upper_${charArg}` :
                   charArg.match(/[a-z]/) ? `lower_${charArg}` : `num_${charArg}`;
  await page.screenshot({ path: join(outDir, `${fontArg}_${safeName}.png`) });

  await browser.close();
  server.close();

  console.log(`\nCharacter: ${charArg}`);
  console.log(`Font: ${fontArg}`);
  console.log(`Score: ${(score * 100).toFixed(1)}%`);
  console.log(`Status: ${score >= 0.95 ? 'PASS' : 'NEEDS WORK'}`);
  console.log(`\nScreenshot saved to scripts/stroke-scores/${fontArg}_${safeName}.png`);

  process.exit(score >= 0.95 ? 0 : 1);
}

main().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
