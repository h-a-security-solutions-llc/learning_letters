#!/usr/bin/env node
/**
 * Debug WASM scoring - minimal test with verbose logging
 */

import puppeteer from 'puppeteer';
import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join, extname } from 'path';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

async function main() {
  const fontArg = 'schoolbell';
  const charArg = 'P';
  const size = 400;

  // Load stroke data
  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const charData = strokeFile.characters[charArg];
  const strokes = charData.strokes;

  const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.wasm': 'application/wasm',
    '.ttf': 'font/ttf',
    '.json': 'application/json'
  };

  const html = `<!DOCTYPE html>
<html>
<head><style>* { margin: 0; padding: 0; }</style></head>
<body>
  <div id="log"></div>
  <canvas id="canvas" width="${size}" height="${size}"></canvas>
  <script type="module">
    function log(msg) {
      console.log(msg);
      document.getElementById('log').innerHTML += msg + '<br>';
    }

    async function run() {
      try {
        log('1. Starting import...');
        const mod = await import('/src/wasm-pkg/learning_letters_scoring.js');
        log('2. Module imported: ' + Object.keys(mod).join(', '));

        log('3. Calling init()...');
        await mod.default();
        log('4. Init complete');

        log('5. Loading font...');
        const fontRes = await fetch('/fonts/Schoolbell-Regular.ttf');
        log('6. Font response: ' + fontRes.status);
        const fontBuf = await fontRes.arrayBuffer();
        log('7. Font loaded: ' + fontBuf.byteLength + ' bytes');
        const fontData = new Uint8Array(fontBuf);

        log('8. Generating reference image...');
        const refPng = mod.generate_reference_image('${charArg}', fontData, ${size});
        log('9. Reference generated: ' + refPng.length + ' bytes');

        log('10. Drawing user strokes...');
        const canvas = document.getElementById('canvas');
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
        log('11. Strokes drawn');

        log('12. Getting canvas as PNG...');
        const userBlob = await new Promise(r => canvas.toBlob(r, 'image/png'));
        const userBuf = await userBlob.arrayBuffer();
        const userPng = new Uint8Array(userBuf);
        log('13. User PNG: ' + userPng.length + ' bytes');

        log('14. Calculating similarity...');
        const result = mod.score_drawing(userPng, '${charArg}', fontData);
        log('15. SCORE: ' + (result.score * 100).toFixed(1) + '%');
        log('16. Coverage: ' + (result.coverage * 100).toFixed(1) + '%');
        log('17. Accuracy: ' + (result.accuracy * 100).toFixed(1) + '%');
        log('18. Similarity: ' + (result.similarity * 100).toFixed(1) + '%');

        window.testResult = { score: result.score, coverage: result.coverage, accuracy: result.accuracy, similarity: result.similarity, stars: result.stars, success: true };
      } catch (e) {
        log('ERROR: ' + e.message);
        console.error(e);
        window.testResult = { error: e.message, success: false };
      }
    }
    run();
  </script>
</body>
</html>`;

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
      console.log('404:', req.url);
      res.writeHead(404);
      res.end('Not found: ' + req.url);
    }
  });

  await new Promise(resolve => server.listen(3462, resolve));
  console.log('Server running on port 3462');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // Capture console output
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  console.log('Navigating to test page...');
  await page.goto('http://localhost:3462/test.html', { waitUntil: 'networkidle2', timeout: 30000 });

  console.log('Waiting for result...');
  try {
    await page.waitForFunction('window.testResult !== undefined', { timeout: 30000 });
    const result = await page.evaluate(() => window.testResult);
    console.log('\nResult:', result);
  } catch (e) {
    console.log('Timeout - checking page state...');
    const logContent = await page.evaluate(() => document.getElementById('log').innerHTML);
    console.log('Log content:', logContent);
  }

  await browser.close();
  server.close();
}

main().catch(console.error);
