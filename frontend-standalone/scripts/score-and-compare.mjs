#!/usr/bin/env node
/**
 * Score strokes against WASM reference and output debug images
 * Usage: node scripts/score-and-compare.mjs --font=schoolbell --char=P
 */

import puppeteer from 'puppeteer';
import { readFile, writeFile, mkdir } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join, extname } from 'path';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1] || 'P';
  const lineWidthArg = args.find(a => a.startsWith('--linewidth='))?.split('=')[1] || '12';
  const lineWidth = parseInt(lineWidthArg);
  const size = 400;

  const fontMap = {
    'schoolbell': 'Schoolbell-Regular',
    'fredoka': 'Fredoka-Regular',
    'nunito': 'Nunito-Regular',
    'patrick-hand': 'PatrickHand-Regular',
    'playwrite-us': 'PlaywriteUS-Regular'
  };
  const fontFileName = fontMap[fontArg];

  // Load stroke data
  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const charData = strokeFile.characters[charArg];

  if (!charData) {
    console.error(`No stroke data for '${charArg}' in ${fontArg}`);
    process.exit(1);
  }

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
<head>
  <style>
    * { margin: 0; padding: 0; }
    body { background: white; font-family: Arial, sans-serif; padding: 10px; }
    .container { display: flex; gap: 10px; }
    .panel { text-align: center; }
    canvas, img { border: 1px solid #ccc; display: block; }
    h4 { margin: 5px 0; font-size: 12px; }
  </style>
</head>
<body>
  <h3>Stroke Score: ${fontArg} - "${charArg}"</h3>
  <div class="container">
    <div class="panel">
      <h4>Reference</h4>
      <img id="refImg" width="${size}" height="${size}">
    </div>
    <div class="panel">
      <h4>User Strokes</h4>
      <canvas id="userCanvas" width="${size}" height="${size}"></canvas>
    </div>
    <div class="panel">
      <h4>Debug: User Processed</h4>
      <img id="debugUser" width="200" height="200">
    </div>
    <div class="panel">
      <h4>Debug: Ref Processed</h4>
      <img id="debugRef" width="200" height="200">
    </div>
  </div>
  <div id="scores" style="margin-top:10px; font-size:14px;"></div>
  <script type="module">
    import init, { score_drawing, generate_reference_image } from '/src/wasm-pkg/learning_letters_scoring.js';

    async function run() {
      try {
        await init();

        // Load font
        const fontRes = await fetch('/fonts/${fontFileName}.ttf');
        const fontBuf = await fontRes.arrayBuffer();
        const fontData = new Uint8Array(fontBuf);

        // Generate reference image
        const refPng = generate_reference_image('${charArg}', fontData, ${size});
        const refBlob = new Blob([refPng], { type: 'image/png' });
        document.getElementById('refImg').src = URL.createObjectURL(refBlob);

        // Draw user strokes
        const canvas = document.getElementById('userCanvas');
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

        // Get user image as PNG
        const userBlob = await new Promise(r => canvas.toBlob(r, 'image/png'));
        const userBuf = await userBlob.arrayBuffer();
        const userPng = new Uint8Array(userBuf);

        // Score
        const result = score_drawing(userPng, '${charArg}', fontData);

        // Show debug images
        const debugUserBlob = new Blob([result.debug_user_processed], { type: 'image/png' });
        document.getElementById('debugUser').src = URL.createObjectURL(debugUserBlob);

        const debugRefBlob = new Blob([result.debug_reference_processed], { type: 'image/png' });
        document.getElementById('debugRef').src = URL.createObjectURL(debugRefBlob);

        // Show scores
        const scoresDiv = document.getElementById('scores');
        const status = result.score >= 95 ? '✓ PASS' : '✗ NEEDS WORK';
        const statusColor = result.score >= 95 ? 'green' : 'red';
        scoresDiv.innerHTML = \`
          <div style="font-size:24px;color:\${statusColor};font-weight:bold">\${status}</div>
          <div><b>Combined:</b> \${result.score}% (target: 95%)</div>
          <div><b>Coverage:</b> \${result.coverage}% (how much of reference is covered)</div>
          <div><b>Accuracy:</b> \${result.accuracy}% (strokes within reference zone)</div>
          <div><b>Similarity:</b> \${result.similarity}% (IoU overlap)</div>
          <div><b>Stars:</b> \${result.stars}/5</div>
          <div><b>Feedback:</b> \${result.feedback}</div>
        \`;

        window.testResult = {
          score: result.score,
          coverage: result.coverage,
          accuracy: result.accuracy,
          similarity: result.similarity,
          stars: result.stars,
          feedback: result.feedback,
          success: true
        };
      } catch (e) {
        console.error(e);
        document.getElementById('scores').innerHTML = 'Error: ' + e.message;
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
      res.writeHead(404);
      res.end('Not found');
    }
  });

  await new Promise(resolve => server.listen(3463, resolve));

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 500 });

  await page.goto('http://localhost:3463/test.html', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForFunction('window.testResult !== undefined', { timeout: 30000 });

  const result = await page.evaluate(() => window.testResult);

  // Save screenshot
  const outDir = join(ROOT, 'scripts/stroke-scores');
  await mkdir(outDir, { recursive: true });

  const safeName = charArg.match(/[A-Z]/) ? `upper_${charArg}` :
                   charArg.match(/[a-z]/) ? `lower_${charArg}` : `num_${charArg}`;
  const screenshotPath = join(outDir, `${fontArg}_${safeName}.png`);
  await page.screenshot({ path: screenshotPath });

  await browser.close();
  server.close();

  // Output results
  console.log(`\n=== ${fontArg} "${charArg}" ===`);
  console.log(`Combined: ${result.score}% ${result.score >= 95 ? '✓' : '✗'}`);
  console.log(`Coverage: ${result.coverage}%`);
  console.log(`Accuracy: ${result.accuracy}%`);
  console.log(`Similarity: ${result.similarity}%`);
  console.log(`Stars: ${result.stars}/5`);
  console.log(`\nScreenshot: ${screenshotPath}`);

  // Exit with appropriate code
  process.exit(result.score >= 95 ? 0 : 1);
}

main().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
