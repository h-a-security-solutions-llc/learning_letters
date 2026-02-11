# Stroke Optimization TODO

**Goal:** All 62 characters across all 5 fonts must score >= 95% combined.

**Score formula:** `combined = coverage*0.40 + accuracy*0.30 + similarity*0.30`
**Bottleneck:** Similarity (IoU with 14px dilation) — straight-line stroke rendering can't fully match curved font glyphs.

## Current Status (2026-02-11)

| Font | Passing | Failing | % Done |
|------|---------|---------|--------|
| Fredoka | 60/62 | 1 (+1 error) | 97% |
| Patrick Hand | 60/62 | 2 | 97% |
| Playwrite US | 42/62 | 20 | 68% |
| Schoolbell | 35/62 | 27 | 56% |
| Nunito | 1/62 | 61 | 2% |
| **Total** | **198/310** | **111** | **64%** |

## Fredoka (60/62) — Nearly Done

- [ ] **j** — 94% (sim:85%). Stuck at 94% after enhanced optimizer. Needs ~1% sim boost.
- [ ] **x** — Scoring error (navigation timeout). Investigate and fix.

## Patrick Hand (60/62) — Nearly Done

- [ ] **l** — 93% (sim:81%). Enhanced optimizer stuck at 93%.
- [ ] **r** — 93% (sim:81%). Enhanced optimizer stuck at 93%.

## Playwrite US (42/62) — 20 Failing

Close to passing (92-94%, may respond to optimizer):
- [ ] **T** — 94% (sim:81%)
- [ ] **x** — 94% (sim:82%)
- [ ] **u** — 93% (sim:82%)
- [ ] **z** — 92% (sim:81%)
- [ ] **a** — 92% (sim:78%)
- [ ] **1** — 92% (sim:77%)

Need more work (91%):
- [ ] **s** — 91% (sim:77%)
- [ ] **o** — 91% (sim:76%)
- [ ] **l** — 91% (sim:75%)
- [ ] **c** — 91% (sim:78%)

Significantly below target (79-90%):
- [ ] **V** — 90% (sim:76%)
- [ ] **4** — 90% (sim:80%)
- [ ] **n** — 89% (sim:75%)
- [ ] **M** — 89% (sim:76%)
- [ ] **j** — 87% (sim:73%)
- [ ] **v** — 86% (sim:70%)
- [ ] **t** — 86% (sim:72%)
- [ ] **r** — 86% (sim:72%)
- [ ] **I** — 84% (sim:68%)
- [ ] **i** — 79% (sim:63%)

## Schoolbell (35/62) — 27 Failing

At 94% (need ~1-2% sim boost):
- [ ] **2** (sim:85%), **H** (sim:83%), **W** (sim:83%), **X** (sim:83%), **v** (sim:82%), **S** (sim:82%), **w** (sim:82%), **L** (sim:82%), **I** (sim:81%)

At 93%:
- [ ] **4** (sim:85%), **8** (sim:84%), **Q** (sim:83%), **u** (sim:83%), **c** (sim:82%), **z** (sim:82%), **9** (sim:82%), **5** (sim:81%)

At 89-92%:
- [ ] **n** (sim:79%), **g** (sim:81%), **E** (sim:77%), **7** (sim:78%), **Z** (sim:78%), **G** (sim:79%), **o** (sim:79%), **x** (sim:75%), **T** (sim:72%), **N** (sim:75%)

## Nunito (1/62) — 61 Failing (Needs Different Approach)

Best chars (94%): 6, g, w — enhanced optimizer tried and stuck.
Most chars at 89-93%. Worst: r (77%), l (78%), i (80%).

Nunito's rounded glyphs create a fundamental mismatch with straight-line stroke rendering. The greedy point-nudging optimizer cannot bridge the gap.

## Approach Options

### 1. Continue Greedy Optimization (Current)
- Run `optimize-enhanced.mjs` on remaining chars
- **Pro:** Can push some 93% chars to 95%
- **Con:** Hits ceiling at 94% for many chars; very slow with 500+ points

### 2. Increase Stroke Point Density
- Add more points to strokes to better approximate curves
- **Pro:** Better curve approximation -> higher sim scores
- **Con:** Larger JSON files, more points for kids to trace

### 3. Adjust Scoring Parameters
- Increase dilation radius (currently 14px) for more forgiving IoU
- Lower passing threshold from 95%
- Adjust weight formula to reduce sim weight
- **Pro:** Many chars at 93-94% would immediately pass
- **Con:** May make scoring too lenient for actual user drawings

### 4. Curve Rendering (Quadratic/Bezier)
- Render strokes as curves instead of straight line segments
- **Pro:** Better matches curved glyphs
- **Con:** Previous test showed no improvement (points optimized for linear rendering). Would need to re-optimize all points for curve rendering.

### 5. Font-Specific Line Width Tuning
- Different fonts may benefit from different lineWidth values
- Thicker lines increase overlap area, boosting sim scores

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `batch-score.mjs --font=<name>` | Score all 62 chars for a font |
| `optimize-stable.mjs --font=<name> --char=<c>` | Basic greedy point nudging |
| `optimize-enhanced.mjs --font=<name> --char=<c>` | Midpoints + offset midpoints + nudging |
| `save-optimized.mjs --font=<name> --mappings='c:taskid'` | Save stuck optimizer results from output files |
