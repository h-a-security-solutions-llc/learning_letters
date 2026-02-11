#!/usr/bin/env node
import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

async function main() {
  const data = JSON.parse(await readFile(join(ROOT, 'public/strokes/schoolbell.json'), 'utf8'));

  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

  for (const c of chars) {
    const info = data.characters[c];
    if (info && info.strokes.length > 0) {
      let minX = 100, maxX = 0, minY = 100, maxY = 0;
      info.strokes.forEach(s => {
        s.points.forEach(p => {
          minX = Math.min(minX, p[0]);
          maxX = Math.max(maxX, p[0]);
          minY = Math.min(minY, p[1]);
          maxY = Math.max(maxY, p[1]);
        });
      });
      console.log(`${c}: bbox=[${minX.toFixed(0)},${minY.toFixed(0)} to ${maxX.toFixed(0)},${maxY.toFixed(0)}], strokes=${info.strokes.length}, directions=[${info.strokes.map(s => s.direction).join(', ')}]`);
    }
  }
}

main();
