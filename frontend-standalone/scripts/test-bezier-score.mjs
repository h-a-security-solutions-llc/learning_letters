#!/usr/bin/env node
/**
 * Test scoring with bezier curve rendering instead of straight lines.
 * Usage: node scripts/test-bezier-score.mjs --font=schoolbell --char=H
 */
import puppeteer from 'puppeteer';
import { readFile } from 'fs/promises';
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

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charsArg = args.find(a => a.startsWith('--chars='))?.split('=')[1] || 'H,I,L,S,W,X,q,v,w,2';
  const lineWidth = 24;
  const size = 400;
  const fontFileName = FONT_MAP[fontArg];

  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const chars = charsArg.split(',');

  const mimeTypes = {
    '.html': 'text/html', '.js': 'application/javascript',
    '.wasm': 'application/wasm', '.ttf': 'font/ttf', '.json': 'application/json'
  };

  let currentChar = '';
  let currentStrokes = [];
  let renderMode = 'linear';

  function generateHtml() {
    const bezierRender = `
      // Catmull-Rom to Bezier conversion for smooth curves
      function drawSmoothStroke(ctx, points, scale) {
        if (points.length < 2) return;
        ctx.beginPath();
        ctx.moveTo(points[0][0] * scale, points[0][1] * scale);

        if (points.length === 2) {
          ctx.lineTo(points[1][0] * scale, points[1][1] * scale);
        } else {
          // Use quadratic curves through midpoints
          for (let i = 0; i < points.length - 1; i++) {
            const x0 = points[i][0] * scale;
            const y0 = points[i][1] * scale;
            const x1 = points[i+1][0] * scale;
            const y1 = points[i+1][1] * scale;

            if (i === 0) {
              // First segment: line to midpoint
              const mx = (x0 + x1) / 2;
              const my = (y0 + y1) / 2;
              ctx.lineTo(mx, my);
            } else if (i === points.length - 2) {
              // Last segment: curve to end
              ctx.quadraticCurveTo(x0, y0, x1, y1);
            } else {
              // Middle segments: curve through midpoints
              const mx = (x0 + x1) / 2;
              const my = (y0 + y1) / 2;
              ctx.quadraticCurveTo(x0, y0, mx, my);
            }
          }
        }
        ctx.stroke();
      }`;

    const linearRender = `
      function drawSmoothStroke(ctx, points, scale) {
        if (points.length < 2) return;
        ctx.beginPath();
        ctx.moveTo(points[0][0] * scale, points[0][1] * scale);
        for (let i = 1; i < points.length; i++) {
          ctx.lineTo(points[i][0] * scale, points[i][1] * scale);
        }
        ctx.stroke();
      }`;

    return `<!DOCTYPE html>
<html><head><style>* { margin: 0; padding: 0; }</style></head>
<body>
  <canvas id="canvas" width="${size}" height="${size}"></canvas>
  <script type="module">
    import init, { score_drawing } from '/src/wasm-pkg/learning_letters_scoring.js';

    ${renderMode === 'bezier' ? bezierRender : linearRender}

    async function run() {
      try {
        await init();
        const fontRes = await fetch('/fonts/${fontFileName}.ttf');
        const fontData = new Uint8Array(await fontRes.arrayBuffer());
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, ${size}, ${size});
        const strokes = ${JSON.stringify(currentStrokes)};
        ctx.strokeStyle = 'black';
        ctx.lineWidth = ${lineWidth};
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        const scale = ${size} / 100;
        for (const stroke of strokes) {
          if (!stroke.points || stroke.points.length < 2) continue;
          drawSmoothStroke(ctx, stroke.points, scale);
        }
        const userBlob = await new Promise(r => canvas.toBlob(r, 'image/png'));
        const userPng = new Uint8Array(await userBlob.arrayBuffer());
        const result = score_drawing(userPng, '${currentChar}', fontData);
        window.testResult = { score: result.score, coverage: result.coverage, accuracy: result.accuracy, similarity: result.similarity, success: true };
      } catch (e) {
        window.testResult = { error: e.message, success: false };
      }
    }
    run();
  </script>
</body></html>`;
  }

  const server = createServer((req, res) => {
    if (req.url === '/test.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(generateHtml());
      return;
    }
    let filePath = join(ROOT, req.url);
    if (!existsSync(filePath)) filePath = join(ROOT, 'public', req.url);
    if (existsSync(filePath)) {
      const ext = extname(filePath);
      res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
      res.end(readFileSync(filePath));
    } else {
      res.writeHead(404);
      res.end('Not found');
    }
  });

  await new Promise(resolve => server.listen(0, resolve));
  const port = server.address().port;

  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });

  console.log('Char | Linear | Bezier | Improvement');
  console.log('-----|--------|--------|------------');

  for (const char of chars) {
    const charData = strokeFile.characters[char];
    if (!charData) continue;
    currentChar = char;
    currentStrokes = charData.strokes;

    // Test linear
    renderMode = 'linear';
    const page1 = await browser.newPage();
    await page1.goto(`http://localhost:${port}/test.html`, { waitUntil: 'networkidle0', timeout: 30000 });
    await page1.waitForFunction('window.testResult !== undefined', { timeout: 15000 });
    const linearResult = await page1.evaluate(() => window.testResult);
    await page1.close();

    // Test bezier
    renderMode = 'bezier';
    const page2 = await browser.newPage();
    await page2.goto(`http://localhost:${port}/test.html`, { waitUntil: 'networkidle0', timeout: 30000 });
    await page2.waitForFunction('window.testResult !== undefined', { timeout: 15000 });
    const bezierResult = await page2.evaluate(() => window.testResult);
    await page2.close();

    const diff = bezierResult.score - linearResult.score;
    const arrow = diff > 0 ? '+' : diff < 0 ? '' : '=';
    console.log(`  ${char}  |  ${linearResult.score}%   |  ${bezierResult.score}%   | ${arrow}${diff}% (sim: ${linearResult.similarity}→${bezierResult.similarity})`);
  }

  await browser.close();
  server.close();
}

main().catch(console.error);
