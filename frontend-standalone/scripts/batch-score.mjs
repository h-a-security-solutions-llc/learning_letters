#!/usr/bin/env node
/**
 * Batch score all characters for a font
 * Usage: node scripts/batch-score.mjs --font=schoolbell [--linewidth=24]
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
  const lineWidthArg = args.find(a => a.startsWith('--linewidth='))?.split('=')[1] || '24';
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
  const characters = Object.keys(strokeFile.characters);

  console.log(`Testing ${fontArg} font (${characters.length} characters) with lineWidth=${lineWidth}\n`);

  const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.wasm': 'application/wasm',
    '.ttf': 'font/ttf',
    '.json': 'application/json'
  };

  // Track current test parameters
  let currentChar = 'A';
  let currentStrokes = [];

  function getTestHtml() {
    return `<!DOCTYPE html>
<html>
<head><style>* { margin: 0; padding: 0; } body { background: white; }</style></head>
<body>
  <canvas id="canvas" width="${size}" height="${size}"></canvas>
  <script type="module">
    import init, { score_drawing } from '/src/wasm-pkg/learning_letters_scoring.js';

    const testChar = ${JSON.stringify(currentChar)};
    const testStrokes = ${JSON.stringify(currentStrokes)};

    async function run() {
      try {
        await init();
        const fontRes = await fetch('/fonts/${fontFileName}.ttf');
        const fontData = new Uint8Array(await fontRes.arrayBuffer());

        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, ${size}, ${size});

        ctx.strokeStyle = 'black';
        ctx.lineWidth = ${lineWidth};
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        const scale = ${size} / 100;
        for (const stroke of testStrokes) {
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
        const result = score_drawing(userPng, testChar, fontData);

        window.testResult = {
          score: result.score,
          coverage: result.coverage,
          accuracy: result.accuracy,
          similarity: result.similarity,
          success: true
        };
      } catch (e) {
        console.error(e);
        window.testResult = { error: e.message, success: false };
      }
    }
    run();
  </script>
</body>
</html>`;
  }

  const server = createServer((req, res) => {
    if (req.url === '/test.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(getTestHtml());
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

  await new Promise(resolve => server.listen(0, resolve));
  const assignedPort = server.address().port;

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  const results = { pass: [], fail: [], error: [] };

  for (const char of characters) {
    const charData = strokeFile.characters[char];
    if (!charData || !charData.strokes) {
      results.error.push({ char, error: 'No stroke data' });
      process.stdout.write('E');
      continue;
    }

    // Update current test parameters (used by getTestHtml)
    currentChar = char;
    currentStrokes = charData.strokes;

    try {
      await page.goto(`http://localhost:${assignedPort}/test.html`, { waitUntil: 'networkidle2', timeout: 30000 });
      await page.waitForFunction('window.testResult !== undefined', { timeout: 15000 });
      const result = await page.evaluate(() => window.testResult);

      if (result.success) {
        const entry = { char, score: result.score, coverage: result.coverage, accuracy: result.accuracy, similarity: result.similarity };

        if (result.score >= 95) {
          results.pass.push(entry);
          process.stdout.write('.');
        } else {
          results.fail.push(entry);
          process.stdout.write('X');
        }
      } else {
        results.error.push({ char, error: result.error });
        process.stdout.write('E');
      }
    } catch (e) {
      results.error.push({ char, error: e.message });
      process.stdout.write('E');
    }
  }

  await browser.close();
  server.close();

  // Print summary
  console.log('\n\n=== SUMMARY ===');
  console.log(`Font: ${fontArg}, LineWidth: ${lineWidth}`);
  console.log(`Passed: ${results.pass.length}/${characters.length}`);
  console.log(`Failed: ${results.fail.length}/${characters.length}`);
  console.log(`Errors: ${results.error.length}/${characters.length}`);

  if (results.fail.length > 0) {
    console.log('\n=== FAILED CHARACTERS (sorted by score) ===');
    results.fail.sort((a, b) => a.score - b.score);
    for (const f of results.fail) {
      console.log(`  ${f.char}: ${f.score}% (cov:${f.coverage}%, acc:${f.accuracy}%, sim:${f.similarity}%)`);
    }
  }

  if (results.error.length > 0) {
    console.log('\n=== ERRORS ===');
    for (const e of results.error) {
      console.log(`  ${e.char}: ${e.error}`);
    }
  }

  if (results.pass.length > 0) {
    console.log('\n=== PASSING CHARACTERS ===');
    const passed = results.pass.map(p => p.char).join(', ');
    console.log(`  ${passed}`);
  }

  // Exit with error code if any failed
  process.exit(results.fail.length > 0 || results.error.length > 0 ? 1 : 0);
}

main().catch(console.error);
