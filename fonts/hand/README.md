# The handwriting capture

Three styles grow from one set of samples: the faithful hand, and a serif
and a sans regularised from the same skeletons and proportions.

1. Open `template.html` in a browser, print at 100% on A4 (no fit-to-page).
2. Fill the three sheets with a black 0.5-0.8 mm pen, per the sheet notes.
3. Scan at 300 dpi (best) or photograph flat, straight-on, all four corner
   squares visible; good even light, no shadows.
4. Drop the images here as `samples/page1.jpg`, `samples/page2.jpg`,
   `samples/page3.jpg` (png works too).
5. `fonts/tools/hand_trace.py` (built when samples exist) dewarps by the
   corner squares, cuts the cells, and traces each glyph to
   `svg/<name>.svg` for review before any font is built.
