#!/usr/bin/env node
/**
 * Enhanced stroke optimizer that can also add intermediate points for curves.
 * Usage: node scripts/optimize-enhanced.mjs --font=schoolbell --char=o --target=95
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

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const charArg = args.find(a => a.startsWith('--char='))?.split('=')[1] || 'o';
  const targetArg = args.find(a => a.startsWith('--target='))?.split('=')[1] || '95';
  const lineWidthArg = args.find(a => a.startsWith('--linewidth='))?.split('=')[1] || '24';
  const target = parseInt(targetArg);
  const lineWidth = parseInt(lineWidthArg);
  const size = 400;
  const fontFileName = FONT_MAP[fontArg];

  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));
  const charData = strokeFile.characters[charArg];

  if (!charData || !charData.strokes) {
    console.error(`No stroke data for '${charArg}'`);
    process.exit(1);
  }

  console.log(`Enhanced optimizing ${fontArg} "${charArg}" (target: ${target}%, lineWidth: ${lineWidth})`);

  const mimeTypes = {
    '.html': 'text/html', '.js': 'application/javascript',
    '.wasm': 'application/wasm', '.ttf': 'font/ttf', '.json': 'application/json'
  };

  let currentStrokes = JSON.parse(JSON.stringify(charData.strokes));
  let currentHtml = '';

  function generateHtml(strokes) {
    return `<!DOCTYPE html>
<html><head><style>* { margin: 0; padding: 0; }</style></head>
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
        window.testResult = { score: result.score, coverage: result.coverage, accuracy: result.accuracy, similarity: result.similarity, success: true };
      } catch (e) {
        window.testResult = { error: e.message, success: false };
      }
    }
    run();
  </script>
</body></html>`;
  }

  currentHtml = generateHtml(currentStrokes);

  const server = createServer((req, res) => {
    if (req.url === '/test.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(currentHtml);
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
  const assignedPort = server.address().port;

  async function score(strokes) {
    currentHtml = generateHtml(strokes);
    const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    try {
      const page = await browser.newPage();
      await page.goto(`http://localhost:${assignedPort}/test.html`, { waitUntil: 'networkidle0', timeout: 30000 });
      await page.waitForFunction('window.testResult !== undefined', { timeout: 15000 });
      const result = await page.evaluate(() => window.testResult);
      await browser.close();
      return result;
    } catch (e) {
      await browser.close();
      throw e;
    }
  }

  let result = await score(currentStrokes);
  if (!result.success) {
    console.error('Initial scoring failed:', result.error);
    server.close();
    process.exit(1);
  }
  let currentScore = result.score;
  console.log(`Initial: ${currentScore}% (cov:${result.coverage}%, acc:${result.accuracy}%, sim:${result.similarity}%)`);

  if (currentScore >= target) {
    console.log('Already meets target!');
    server.close();
    process.exit(0);
  }

  // Phase 1: Try adding midpoints to each segment
  console.log('\n=== Phase 1: Adding midpoints ===');
  for (let s = 0; s < currentStrokes.length && currentScore < target; s++) {
    const pts = currentStrokes[s].points;
    if (pts.length < 2) continue;

    // Try adding a midpoint between each pair of consecutive points
    for (let p = pts.length - 2; p >= 0 && currentScore < target; p--) {
      const mid = [
        Math.round((pts[p][0] + pts[p+1][0]) / 2),
        Math.round((pts[p][1] + pts[p+1][1]) / 2)
      ];
      const testStrokes = JSON.parse(JSON.stringify(currentStrokes));
      testStrokes[s].points.splice(p + 1, 0, mid);

      try {
        const testResult = await score(testStrokes);
        if (testResult.success && testResult.score > currentScore) {
          currentStrokes = testStrokes;
          currentScore = testResult.score;
          console.log(`  Added midpoint at stroke ${s+1}, after point ${p+1}: [${mid}] -> ${currentScore}%`);
        }
      } catch (e) { /* skip */ }
    }
  }

  console.log(`After midpoints: ${currentScore}%`);

  // Phase 2: Try offset midpoints (perpendicular to the segment)
  if (currentScore < target) {
    console.log('\n=== Phase 2: Offset midpoints ===');
    for (let s = 0; s < currentStrokes.length && currentScore < target; s++) {
      const pts = currentStrokes[s].points;
      if (pts.length < 2) continue;

      for (let p = pts.length - 2; p >= 0 && currentScore < target; p--) {
        const dx = pts[p+1][0] - pts[p][0];
        const dy = pts[p+1][1] - pts[p][1];
        const len = Math.sqrt(dx*dx + dy*dy);
        if (len < 3) continue;

        const nx = -dy / len; // perpendicular
        const ny = dx / len;

        const midX = (pts[p][0] + pts[p+1][0]) / 2;
        const midY = (pts[p][1] + pts[p+1][1]) / 2;

        let bestScore = currentScore;
        let bestOffset = null;

        for (const offset of [5, -5, 10, -10, 3, -3, 7, -7]) {
          const testPt = [
            Math.round(midX + nx * offset),
            Math.round(midY + ny * offset)
          ];
          if (testPt[0] < 0 || testPt[0] > 100 || testPt[1] < 0 || testPt[1] > 100) continue;

          const testStrokes = JSON.parse(JSON.stringify(currentStrokes));
          testStrokes[s].points.splice(p + 1, 0, testPt);

          try {
            const testResult = await score(testStrokes);
            if (testResult.success && testResult.score > bestScore) {
              bestScore = testResult.score;
              bestOffset = { pt: testPt, strokes: testStrokes };
            }
          } catch (e) { /* skip */ }
        }

        if (bestOffset) {
          currentStrokes = bestOffset.strokes;
          currentScore = bestScore;
          console.log(`  Offset midpoint at stroke ${s+1}: [${bestOffset.pt}] -> ${currentScore}%`);
        }
      }
    }
    console.log(`After offset midpoints: ${currentScore}%`);
  }

  // Phase 3: Standard point optimization (nudging)
  if (currentScore < target) {
    console.log('\n=== Phase 3: Point nudging ===');
    const deltaSets = [
      [[5, 0], [-5, 0], [0, 5], [0, -5]],
      [[3, 0], [-3, 0], [0, 3], [0, -3], [3, 3], [3, -3], [-3, 3], [-3, -3]],
      [[2, 0], [-2, 0], [0, 2], [0, -2], [2, 2], [2, -2], [-2, 2], [-2, -2]],
      [[1, 0], [-1, 0], [0, 1], [0, -1]]
    ];

    let iteration = 0;
    const maxIterations = 15;

    while (currentScore < target && iteration < maxIterations) {
      iteration++;
      let improved = false;
      console.log(`  Iteration ${iteration} (current: ${currentScore}%)`);

      for (const deltas of deltaSets) {
        if (currentScore >= target) break;
        for (let s = 0; s < currentStrokes.length && currentScore < target; s++) {
          for (let p = 0; p < currentStrokes[s].points.length && currentScore < target; p++) {
            let bestDelta = null;
            let bestScore = currentScore;

            for (const delta of deltas) {
              const testStrokes = JSON.parse(JSON.stringify(currentStrokes));
              testStrokes[s].points[p] = [
                currentStrokes[s].points[p][0] + delta[0],
                currentStrokes[s].points[p][1] + delta[1]
              ];
              try {
                const testResult = await score(testStrokes);
                if (testResult.success && testResult.score > bestScore) {
                  bestScore = testResult.score;
                  bestDelta = delta;
                }
              } catch (e) { /* skip */ }
            }

            if (bestDelta) {
              currentStrokes[s].points[p] = [
                currentStrokes[s].points[p][0] + bestDelta[0],
                currentStrokes[s].points[p][1] + bestDelta[1]
              ];
              currentScore = bestScore;
              improved = true;
              console.log(`    S${s+1}P${p+1}: +[${bestDelta}] -> ${currentScore}%`);
            }
          }
        }
      }
      if (!improved) break;
    }
  }

  server.close();
  console.log(`\nFinal score: ${currentScore}%`);

  if (currentScore >= target) {
    console.log('Target achieved! Saving...');
    const freshFile = JSON.parse(await readFile(strokePath, 'utf8'));
    freshFile.characters[charArg].strokes = currentStrokes;
    await writeFile(strokePath, JSON.stringify(freshFile, null, 2));
    console.log('Saved updated strokes.');
    process.exit(0);
  } else {
    console.log(`Could not reach target. Best: ${currentScore}%`);
    console.log('Optimized strokes (not saved):');
    console.log(JSON.stringify(currentStrokes, null, 2));
    process.exit(1);
  }
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
