#!/usr/bin/env node
/**
 * Extract optimized strokes from optimizer output files and save to stroke JSON.
 * Usage: node scripts/save-optimized.mjs --font=schoolbell --mappings='Z:b32ce96,q:b7483be,...'
 */
import { readFile, writeFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const TASK_DIR = '/tmp/claude-1000/-home-jhenderson-projects-learning-letters/tasks';

async function main() {
  const args = process.argv.slice(2);
  const fontArg = args.find(a => a.startsWith('--font='))?.split('=')[1] || 'schoolbell';
  const mappingsArg = args.find(a => a.startsWith('--mappings='))?.split('=').slice(1).join('=') || '';

  const strokePath = join(ROOT, `public/strokes/${fontArg}.json`);
  const strokeFile = JSON.parse(await readFile(strokePath, 'utf8'));

  const mappings = mappingsArg.split(',').map(m => {
    const [char, taskId] = m.split(':');
    return { char, taskId };
  });

  let savedCount = 0;

  for (const { char, taskId } of mappings) {
    try {
      const outputPath = join(TASK_DIR, `${taskId}.output`);
      const output = await readFile(outputPath, 'utf8');

      // Check if it was stuck (not already saved)
      if (output.includes('Target achieved')) {
        console.log(`${char}: Already saved by optimizer, skipping`);
        continue;
      }

      if (!output.includes('Optimized strokes (not saved):')) {
        console.log(`${char}: No optimized strokes found, skipping`);
        continue;
      }

      // Extract JSON after "Optimized strokes (not saved):"
      const marker = 'Optimized strokes (not saved):';
      const jsonStart = output.indexOf(marker) + marker.length;
      const jsonStr = output.substring(jsonStart).trim();
      const strokes = JSON.parse(jsonStr);

      strokeFile.characters[char].strokes = strokes;
      savedCount++;

      // Get the best score
      const scoreMatch = output.match(/Best: (\d+)%/);
      const bestScore = scoreMatch ? scoreMatch[1] : '?';
      console.log(`${char}: Saved optimized strokes (best: ${bestScore}%)`);
    } catch (e) {
      console.error(`${char}: Error - ${e.message}`);
    }
  }

  if (savedCount > 0) {
    await writeFile(strokePath, JSON.stringify(strokeFile, null, 2));
    console.log(`\nSaved ${savedCount} characters to ${strokePath}`);
  } else {
    console.log('\nNo characters to save');
  }
}

main().catch(console.error);
