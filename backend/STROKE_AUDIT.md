# Stroke Definition Audit

This file tracks the systematic verification of stroke definitions for all fonts and characters.
Each character should have strokes that match the actual font rendering and follow proper handwriting instruction.

## Legend
- [ ] = Not checked
- [x] = Verified correct
- [!] = Fixed

---

## FREDOKA (Rounded Playful)
Sans-serif, rounded style. Numbers have serifs and base lines.

### Uppercase (All Verified)
- [x] A (3 strokes: left diagonal, right diagonal, crossbar)
- [x] B (3 strokes: stem, upper bump, lower bump)
- [x] C (1 stroke: curve)
- [x] D (2 strokes: stem, curve)
- [x] E (4 strokes: stem, top bar, middle bar, bottom bar)
- [x] F (3 strokes: stem, top bar, middle bar)
- [x] G (1 stroke: continuous C-curve with bar)
- [x] H (3 strokes: left stem, right stem, crossbar)
- [!] I (1 stroke: vertical line - FIXED from 3, sans-serif has no serifs)
- [x] J (2 strokes: top bar, hook curve)
- [x] K (3 strokes: stem, upper diagonal, lower diagonal)
- [x] L (2 strokes: stem, base)
- [x] M (4 strokes: left stem, left diagonal, right diagonal, right stem)
- [x] N (3 strokes: left stem, diagonal, right stem)
- [x] O (1 stroke: oval)
- [x] P (2 strokes: stem, bump)
- [x] Q (2 strokes: oval, tail)
- [x] R (3 strokes: stem, bump, leg)
- [x] S (1 stroke: S-curve)
- [x] T (2 strokes: top bar, stem)
- [x] U (1 stroke: U-curve)
- [x] V (2 strokes: left diagonal, right diagonal)
- [x] W (4 strokes)
- [x] X (2 strokes: both diagonals)
- [x] Y (3 strokes: left diagonal, right diagonal, stem)
- [x] Z (3 strokes: top bar, diagonal, bottom bar)

### Lowercase (All Verified)
- [x] a (2 strokes: circle, stem)
- [x] b (2 strokes: stem, bump)
- [x] c (1 stroke: curve)
- [x] d (2 strokes: circle, stem)
- [x] e (2 strokes: horizontal, curve)
- [x] f (2 strokes: hook stem, crossbar)
- [x] g (2 strokes: circle, descender)
- [x] h (2 strokes: stem, hump)
- [x] i (2 strokes: stem, dot)
- [x] j (2 strokes: hook, dot)
- [x] k (3 strokes: stem, upper diagonal, lower diagonal)
- [x] l (1 stroke: stem)
- [x] m (3 strokes: stem, first hump, second hump)
- [x] n (2 strokes: stem, hump)
- [x] o (1 stroke: oval)
- [x] p (2 strokes: stem, bump)
- [x] q (2 strokes: circle, descender)
- [x] r (2 strokes: stem, shoulder)
- [x] s (1 stroke: S-curve)
- [x] t (2 strokes: stem, crossbar)
- [x] u (2 strokes: U-curve, stem)
- [x] v (2 strokes)
- [x] w (4 strokes)
- [x] x (2 strokes)
- [x] y (2 strokes: left diagonal, right diagonal with descender)
- [x] z (3 strokes)

### Numbers (All Verified)
- [x] 0 (1 stroke: oval)
- [!] 1 (3 strokes: serif, stem, base - FIXED from 2)
- [x] 2 (1 stroke: continuous)
- [x] 3 (2 strokes: top curve, bottom curve)
- [x] 4 (2 strokes: angle, vertical)
- [!] 5 (3 strokes: top bar, stem, curve - FIXED from 2)
- [x] 6 (1 stroke: loop)
- [x] 7 (2 strokes: top bar, diagonal)
- [x] 8 (1 stroke: figure-8)
- [x] 9 (1 stroke: loop)

---

## NUNITO (Clean Sans-serif)
Clean geometric style. Numbers have serifs and base lines similar to Fredoka.

### Uppercase (All Verified)
- [x] A-H (same as Fredoka)
- [x] I (1 stroke: simple vertical - sans-serif)
- [x] J (1 stroke: simple hook curve - NO top serif)
- [x] K-Z (same as Fredoka)

### Lowercase (All Verified)
- [x] a-z (same as Fredoka)

### Numbers (All Verified)
- [!] 1 (3 strokes: serif, stem, base - FIXED)
- [!] 5 (3 strokes: top bar, stem, curve - FIXED)
- [x] 0, 2-4, 6-9 (verified same as Fredoka)

---

## PLAYWRITE-US (Educational Manuscript)
Educational style with serifs. Lowercase 'f' has descender hook.

### Uppercase (All Verified)
- [x] A-H (same structure, with serifs)
- [x] I (3 strokes: top serif, stem, bottom serif - CORRECT for educational style)
- [x] J (2 strokes: top bar, hook)
- [x] K-Z (same structure)

### Lowercase (All Verified)
- [x] a-e (same as Fredoka)
- [x] f (2 strokes: hook with descender, crossbar - descender extends below baseline)
- [x] g-z (same as Fredoka)

### Numbers (All Verified)
- [!] 1 (3 strokes - FIXED)
- [!] 5 (3 strokes - FIXED)
- [x] Others (verified)

---

## PATRICK-HAND (Casual Handwriting)
Casual handwritten style. "7" has European cross-stroke. "1" has no base.

### Uppercase (All Verified)
- [x] A-H (same structure, handwritten style)
- [x] I (3 strokes: top serif, stem, bottom serif)
- [x] J (2 strokes: top bar, hook)
- [x] K-Z (same structure)

### Lowercase (All Verified)
- [x] a-z (same as Fredoka)

### Numbers (All Verified)
- [!] 1 (2 strokes: serif, stem - NO base - FIXED from 1)
- [!] 5 (3 strokes - FIXED)
- [!] 7 (3 strokes: top bar, diagonal, cross-stroke - FIXED, European style)
- [x] Others (verified)

---

## SCHOOLBELL (Playful Handwriting)
Playful kid-friendly style. Simple "1" with no decorations.

### Uppercase (All Verified)
- [x] A-H (same structure, playful style)
- [x] I (3 strokes: top serif, stem, bottom serif)
- [x] J (2 strokes: top bar, hook)
- [x] K-Z (same structure)

### Lowercase (All Verified)
- [x] a-z (same as Fredoka)

### Numbers (All Verified)
- [!] 1 (1 stroke: simple vertical - FIXED, playful/simple style)
- [!] 5 (3 strokes - FIXED)
- [x] Others (verified)

---

## Progress Summary
- Total combinations: 310 (5 fonts x 62 characters)
- **All 310 combinations verified**
- Fixed: ~15 characters across fonts
- Audit completed: 2026-01-24

## Key Font Differences Summary

| Character | Fredoka | Nunito | PlaywriteUS | PatrickHand | Schoolbell |
|-----------|---------|--------|-------------|-------------|------------|
| I (upper) | 1 str   | 1 str  | 3 str       | 3 str       | 3 str      |
| J (upper) | 2 str   | 1 str  | 2 str       | 2 str       | 2 str      |
| 1 (num)   | 3 str   | 3 str  | 3 str       | 2 str       | 1 str      |
| 7 (num)   | 2 str   | 2 str  | 2 str       | 3 str       | 2 str      |

Notes:
- Fredoka & Nunito: Sans-serif uppercase I (no serifs)
- Nunito: Uppercase J has no top bar
- PatrickHand: Number 1 has no base; Number 7 has European cross-stroke
- Schoolbell: Number 1 is simple vertical line
