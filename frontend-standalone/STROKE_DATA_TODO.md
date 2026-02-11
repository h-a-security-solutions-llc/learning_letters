# Stroke Data Review TODO

## Overview
All stroke JSON files need to be reviewed and updated to accurately match each font's visual appearance. Currently, the stroke data appears to be copied from a base template with minor adjustments, resulting in mismatches (e.g., Schoolbell P shows curved strokes when the font actually has angular strokes).

## Fonts (5 total)
1. **Fredoka-Regular** - Rounded, playful style
2. **Nunito-Regular** - Rounded sans-serif
3. **PatrickHand-Regular** - Handwritten style
4. **PlaywriteUS-Regular** - Cursive/script style
5. **Schoolbell-Regular** - Casual handwritten, angular strokes

## Characters per Font (62 total)
- Uppercase: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z (26)
- Lowercase: a b c d e f g h i j k l m n o p q r s t u v w x y z (26)
- Numbers: 0 1 2 3 4 5 6 7 8 9 (10)

## Total Combinations: 310

---

## Review Checklist

### Fredoka-Regular (fredoka.json)
#### Uppercase
- [ ] A - 3 strokes (left diagonal, right diagonal, crossbar)
- [ ] B - 3 strokes (vertical, upper bump, lower bump)
- [ ] C - 1 stroke (curve)
- [ ] D - 2 strokes (vertical, curve)
- [ ] E - 4 strokes (vertical, top, middle, bottom)
- [ ] F - 3 strokes (vertical, top, middle)
- [ ] G - 1-2 strokes (curve with crossbar)
- [ ] H - 3 strokes (left vertical, right vertical, crossbar)
- [ ] I - 1-3 strokes (vertical, optional serifs)
- [ ] J - 1-2 strokes (curve, optional top)
- [ ] K - 3 strokes (vertical, upper diagonal, lower diagonal)
- [ ] L - 2 strokes (vertical, bottom)
- [ ] M - 4 strokes (left vertical, left diagonal, right diagonal, right vertical)
- [ ] N - 3 strokes (left vertical, diagonal, right vertical)
- [ ] O - 1 stroke (oval)
- [ ] P - 2 strokes (vertical, bump)
- [ ] Q - 2 strokes (oval, tail)
- [ ] R - 3 strokes (vertical, bump, leg)
- [ ] S - 1 stroke (s-curve)
- [ ] T - 2 strokes (top, vertical)
- [ ] U - 1 stroke (u-shape)
- [ ] V - 2 strokes (left diagonal, right diagonal)
- [ ] W - 4 strokes
- [ ] X - 2 strokes (diagonals)
- [ ] Y - 3 strokes (left diagonal, right diagonal, vertical)
- [ ] Z - 3 strokes (top, diagonal, bottom)

#### Lowercase
- [ ] a - 2 strokes (circle, stem)
- [ ] b - 2 strokes (stem, bump)
- [ ] c - 1 stroke (curve)
- [ ] d - 2 strokes (circle, stem)
- [ ] e - 1 stroke (with crossbar built in)
- [ ] f - 2 strokes (curve down, crossbar)
- [ ] g - 2 strokes (circle, descender)
- [ ] h - 2 strokes (stem, hump)
- [ ] i - 2 strokes (stem, dot)
- [ ] j - 2 strokes (curve, dot)
- [ ] k - 3 strokes (stem, upper diagonal, lower diagonal)
- [ ] l - 1 stroke (vertical)
- [ ] m - 3 strokes (stem, first hump, second hump)
- [ ] n - 2 strokes (stem, hump)
- [ ] o - 1 stroke (circle)
- [ ] p - 2 strokes (stem, bump)
- [ ] q - 2 strokes (circle, stem)
- [ ] r - 2 strokes (stem, curve)
- [ ] s - 1 stroke (s-curve)
- [ ] t - 2 strokes (vertical, crossbar)
- [ ] u - 1-2 strokes
- [ ] v - 2 strokes
- [ ] w - 3-4 strokes
- [ ] x - 2 strokes
- [ ] y - 2 strokes
- [ ] z - 3 strokes

#### Numbers
- [ ] 0 - 1 stroke (oval)
- [ ] 1 - 1-2 strokes (vertical, optional serif)
- [ ] 2 - 1 stroke (continuous)
- [ ] 3 - 1-2 strokes
- [ ] 4 - 3 strokes (vertical, horizontal, diagonal)
- [ ] 5 - 2-3 strokes
- [ ] 6 - 1 stroke (curve with loop)
- [ ] 7 - 2 strokes (top, diagonal)
- [ ] 8 - 1 stroke (figure 8)
- [ ] 9 - 1 stroke (loop with stem)

---

### Nunito-Regular (nunito.json)
#### Uppercase
- [ ] A through Z (26 characters)

#### Lowercase
- [ ] a through z (26 characters)

#### Numbers
- [ ] 0 through 9 (10 characters)

---

### PatrickHand-Regular (patrick-hand.json)
#### Uppercase
- [ ] A through Z (26 characters)

#### Lowercase
- [ ] a through z (26 characters)

#### Numbers
- [ ] 0 through 9 (10 characters)

---

### PlaywriteUS-Regular (playwrite-us.json)
**Note: This is a cursive font - strokes may connect differently**

#### Uppercase
- [ ] A through Z (26 characters)

#### Lowercase
- [ ] a through z (26 characters)

#### Numbers
- [ ] 0 through 9 (10 characters)

---

### Schoolbell-Regular (schoolbell.json)
**Note: Angular/casual handwritten style - many letters use straight lines instead of curves**

#### Uppercase (PRIORITY - these differ most from standard)
- [ ] A - Check if angular or curved
- [ ] B - **NEEDS REVIEW** - bumps may be angular
- [ ] C - Likely curved
- [ ] D - Check bump shape
- [ ] E - Likely standard
- [ ] F - Likely standard
- [ ] G - Check curve
- [ ] H - Likely standard
- [ ] I - Likely standard
- [ ] J - Check hook
- [ ] K - Likely standard
- [ ] L - Likely standard
- [ ] M - Check if angular peaks
- [ ] N - Check diagonal
- [ ] O - Check if oval or angular
- [ ] P - **NEEDS FIX** - Bump is angular (">") not curved
- [ ] Q - Check oval and tail
- [ ] R - **NEEDS REVIEW** - bump may be angular
- [ ] S - Check curve vs angular
- [ ] T - Likely standard
- [ ] U - Check curve
- [ ] V - Likely standard
- [ ] W - Check if angular peaks
- [ ] X - Likely standard
- [ ] Y - Check angles
- [ ] Z - Likely standard

#### Lowercase
- [ ] a through z (26 characters) - Review for angular vs curved

#### Numbers
- [ ] 0 through 9 (10 characters)

---

## Process for Each Character

1. **Render Reference**: Generate a large (400px+) reference image of the character in the font
2. **Trace Visually**: Identify the natural stroke order and direction
3. **Define Strokes**: Create point arrays that follow the centerline of each stroke
4. **Set Direction**: Assign appropriate direction hint (down, right, curve-left, etc.)
5. **Test**: Enable step-by-step mode and verify guides align with the rendered character
6. **Iterate**: Adjust points until guides match perfectly

## Coordinate System
- Points are in 0-100 normalized coordinate space
- (0,0) is top-left, (100,100) is bottom-right
- Characters should generally fit within ~10-90 range with margins

## Stroke Direction Values
- `down` - Vertical, top to bottom
- `up` - Vertical, bottom to top
- `right` - Horizontal, left to right
- `left` - Horizontal, right to left
- `down-left` - Diagonal
- `down-right` - Diagonal
- `up-left` - Diagonal
- `up-right` - Diagonal
- `curve-left` - Curved stroke curving leftward
- `curve-right` - Curved stroke curving rightward
- `down-curve` - Vertical with curve at end
- `curve-in` - Inward curving (like G crossbar)
- `right-curve` - Horizontal with curve
- `oval` - Closed oval/circle shape
- `s-curve` - S-shaped curve
- `down-curve-up` - U-shape

---

## Priority Order
1. **Schoolbell** - Most different from template, user reported issues
2. **PlaywriteUS** - Cursive style needs special attention
3. **PatrickHand** - Handwritten style may have variations
4. **Nunito** - Rounded but standard proportions
5. **Fredoka** - Base template, likely closest to correct
