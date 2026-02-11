#!/usr/bin/env node
/**
 * Compare stroke coordinates against the ACTUAL WASM-generated reference image
 * This ensures we're comparing against exactly what the app shows
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

  const fontMap = {
    'schoolbell': 'Schoolbell-Regular',
    'fredoka': 'Fredoka-Regular',
    'nunito': 'Nunito-Regular',
    'patrick-hand': 'PatrickHand-Regular',
    'playwrite-us': 'PlaywriteUS-Regular'
  };

  const fontFileName = fontMap[fontArg];
  const size = 400;

  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  const outDir = join(ROOT, 'scripts/wasm-comparison');
  await mkdir(outDir, { recursive: true });

  // Create HTML that loads WASM and generates the reference
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        * { margin: 0; padding: 0; }
        body { background: white; }
        #container {
          position: relative;
          width: ${size}px;
          height: ${size}px;
        }
        #reference {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          opacity: 0.4;
        }
        #overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
        .stroke-path {
          fill: none;
          stroke: #FF0000;
          stroke-width: 6;
          stroke-linecap: round;
        }
        .start-zone {
          fill: rgba(0, 255, 0, 0.6);
          stroke: green;
          stroke-width: 2;
        }
        .end-zone {
          fill: rgba(255, 165, 0, 0.6);
          stroke: orange;
          stroke-width: 2;
        }
        .stroke-num {
          font: bold 16px Arial;
          fill: white;
        }
        .grid {
          stroke: rgba(0,0,255,0.2);
          stroke-width: 0.5;
        }
        .grid-label {
          font: 10px Arial;
          fill: blue;
        }
      </style>
    </head>
    <body>
      <div id="container">
        <img id="reference" />
        <svg id="overlay" viewBox="0 0 ${size} ${size}">
          <g id="grid"></g>
          <g id="strokes"></g>
        </svg>
      </div>
      <script type="module">
        import init, { generate_reference_image } from '/src/wasm-pkg/learning_letters_scoring.js';

        async function run() {
          await init();

          // Load font
          const fontResponse = await fetch('/fonts/${fontFileName}.ttf');
          const fontBuffer = await fontResponse.arrayBuffer();
          const fontData = new Uint8Array(fontBuffer);

          // Generate reference image using WASM (same as app)
          const pngBytes = generate_reference_image('${charArg}', fontData, ${size});
          const blob = new Blob([pngBytes], { type: 'image/png' });
          const url = URL.createObjectURL(blob);
          document.getElementById('reference').src = url;

          // Draw grid
          const gridG = document.getElementById('grid');
          for (let i = 10; i < 100; i += 10) {
            const x = i * ${size} / 100;
            gridG.innerHTML += \`<line class="grid" x1="\${x}" y1="0" x2="\${x}" y2="${size}"/>\`;
            gridG.innerHTML += \`<line class="grid" x1="0" y1="\${x}" x2="${size}" y2="\${x}"/>\`;
            gridG.innerHTML += \`<text class="grid-label" x="\${x+2}" y="12">\${i}</text>\`;
            if (i > 10) gridG.innerHTML += \`<text class="grid-label" x="2" y="\${x-2}">\${i}</text>\`;
          }

          // Draw stroke guides
          const strokeData = ${JSON.stringify(strokeFile.characters[charArg])};
          const strokesG = document.getElementById('strokes');

          if (strokeData && strokeData.strokes) {
            strokeData.strokes.forEach((stroke, i) => {
              const points = stroke.points;
              if (points.length < 2) return;

              // Scale points from 0-100 to canvas size
              const scaled = points.map(p => [p[0] * ${size}/100, p[1] * ${size}/100]);

              // Draw path
              let d = 'M ' + scaled[0].join(' ');
              for (let j = 1; j < scaled.length; j++) {
                d += ' L ' + scaled[j].join(' ');
              }
              strokesG.innerHTML += \`<path class="stroke-path" d="\${d}"/>\`;

              // Start zone
              const start = scaled[0];
              strokesG.innerHTML += \`<circle class="start-zone" cx="\${start[0]}" cy="\${start[1]}" r="18"/>\`;
              strokesG.innerHTML += \`<text class="stroke-num" x="\${start[0]-5}" y="\${start[1]+5}">\${i+1}</text>\`;

              // End zone
              const end = scaled[scaled.length-1];
              strokesG.innerHTML += \`<circle class="end-zone" cx="\${end[0]}" cy="\${end[1]}" r="12"/>\`;
            });
          }

          window.renderComplete = true;
        }

        run();
      </script>
    </body>
    </html>
  `;

  // Start local server to serve files
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

  const server = createServer((req, res) => {
    let filePath = join(ROOT, req.url === '/' ? 'index.html' : req.url);
    if (req.url === '/test.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(html);
      return;
    }

    if (!existsSync(filePath)) {
      // Try public folder
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

  await new Promise(resolve => server.listen(3456, resolve));
  console.log('Server running on http://localhost:3456');

  await page.goto('http://localhost:3456/test.html');

  // Wait for render to complete
  await page.waitForFunction('window.renderComplete === true', { timeout: 10000 });
  await new Promise(r => setTimeout(r, 500)); // Extra time for image load

  const safeName = charArg.match(/[A-Z]/) ? `upper_${charArg}` :
                   charArg.match(/[a-z]/) ? `lower_${charArg}` :
                   `num_${charArg}`;

  const screenshot = await page.screenshot({ type: 'png' });
  const outPath = join(outDir, `${fontArg}_${safeName}.png`);
  await writeFile(outPath, screenshot);

  console.log(`\nComparison saved: ${outPath}`);
  console.log(`Character: ${charArg}, Font: ${fontArg}`);

  const strokeData = strokeFile.characters[charArg];
  if (strokeData) {
    console.log(`Strokes: ${strokeData.strokes.length}`);
    strokeData.strokes.forEach((s, i) => {
      const start = s.points[0];
      const end = s.points[s.points.length - 1];
      console.log(`  ${i+1}. [${start[0]},${start[1]}] -> [${end[0]},${end[1]}] (${s.direction})`);
    });
  }

  await browser.close();
  server.close();
}

main().catch(console.error);
