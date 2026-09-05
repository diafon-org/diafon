#!/usr/bin/env python3
"""Build the Diaphone font — fonts/Diaphone-Regular.ttf — from Noto Serif (SIL OFL 1.1).

The starting point of the bespoke font: a derivative of Noto Serif (the most widely deployed
OFL family) subset to exactly the character set the engine can emit (every uni/ipa glyph, the
language orthographies incl. tone-marked Pinyin vowels, the tone signs, Latin + digits + basic
punctuation), renamed per the OFL (the reserved name "Noto" is dropped; the copyright notice
and license are retained — see fonts/OFL.txt). Glyph work (the stroke-family marks, bespoke
letterforms) edits THIS font in place via fontTools + the SVG round-trip (scripts/font_svg.py).

Usage:  python scripts/build_font.py        # writes fonts/Diaphone-Regular.ttf, prints coverage
Exits non-zero if any required codepoint is missing from the source font.
"""
import io
import os
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

SRC = os.path.join(ROOT, "fonts", "NotoSerif-Regular.ttf")
OUT = os.path.join(ROOT, "fonts", "Diaphone-Regular.ttf")

BASIC = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
         " .,;:!?()[]/-–—'\"·ʼ")


def charset():
    """Every character the engine can emit, in NFC and NFD (marks + precomposed forms)."""
    from diaphone.engine import export_data
    data = export_data(os.path.join(ROOT, "data"))
    chars = set(BASIC)
    pools = [g for m in data["maps"].values() for g in m.values()]
    pools += [g for o in data["orth"].values() for g in o.values()]
    pools += [g for o in data["lazy"].values() for g in o.values()]
    pools += list(data["toneSup"].values()) + list(data["toneSigns"].values())
    pools += [c for marks in data["toneMarks"].values() for c in marks]      # āáǎà…
    # tone signs composed onto every vowel glyph (the uni --tones output space)
    vowels = [g for lab, g in data["maps"]["uni"].items() if lab[0] in "aeiou"]
    pools += [unicodedata.normalize("NFC", v + s) for v in vowels for s in data["toneSigns"].values()]
    for g in pools:
        for form in ("NFC", "NFD"):
            chars.update(unicodedata.normalize(form, g))
    chars.update("̦͈̓̎")   # the full j-mark family (comma below/above + the doubled pair)
                                               #   engine today but completes the single/double pair)
    # capitals mirror lowercase for everything READABLE (uni glyphs + spellings; IPA ignores case)
    readable = list(data["maps"]["uni"].values()) \
        + [g for o in data["orth"].values() for g in o.values()] \
        + [g for o in data["lazy"].values() for g in o.values()]
    for g in readable:
        for form in ("NFC", "NFD"):
            chars.update(unicodedata.normalize(form, g.upper()))
    return chars


# ---- Glyph surgery: the stroke family — the palatal/soft marks drawn as acutes ----
# Codepoints: the comma pair below/above (U+0326/U+0313) plus the doubled vertical pair
# (U+0348/U+030E — Unicode has no double comma), and
# descender letters p g); OUR font draws the whole family as the base font's acute at its
# NATURAL SIZE (no stretching): rotated 180° below, growing down from the letter's midline;
# upright above, growing up from the letter-body top. These procedural shapes are SEEDS —
# the editing loop is SVG:
#   python scripts/font_svg.py export 0326 0348 0313 030E   -> fonts/svg/*.svg (edit anywhere)
# and any fonts/svg/<glyph>.svg present replaces the seed at build time (see font_svg.py).
SINGLE_TOP = 0.15    # top of the single below-stroke, fraction of x-height (mostly outside the letter)
SINGLE_TIP = -0.16   # its tip, fraction of the em (negative = below the baseline)
DOUBLE_TOP = 0.10    # the double pair embeds even less …
DOUBLE_TIP = -0.12   # … and still exits the letter clearly
DOUBLE_SEP = 0.15    # centre-to-centre distance of a double stroke, as a fraction of the em


def _customize_stroke_marks(font):
    """Replace the four stroke marks with acute copies. Below = 180°-rotated, stretched from
    TOP down to TIP so the stroke grows out of the letter; above = upright at natural size,
    bottom at the x-height. Marks' GPOS anchors untouched; x-centres kept, so attachment
    geometry survives."""
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform

    glyf, cmap = font["glyf"], font.getBestCmap()
    upm = font["head"].unitsPerEm
    glyphset = font.getGlyphSet()          # handles composite glyphs (decomposed on draw)

    def outline(cp):
        rec = DecomposingRecordingPen(glyphset)
        glyphset[cmap[cp]].draw(rec)
        pts = [pt for op, args in rec.value for pt in args if isinstance(pt, tuple)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return rec, (min(xs) + max(xs)) / 2, min(ys), max(ys)

    acute, a_cx, a_ymin, a_ymax = outline(0x0301)
    _, _, _, x_height = outline(ord("x"))
    sep = DOUBLE_SEP * upm

    def stroke_copies(target_cp, centers, span=None, mirror=False):
        _, cx, _, _ = outline(target_cp)
        pen = TTGlyphPen(None)
        for off in centers:
            if span:   # below: rotate 180° ("/" lean), stretch to span (top, tip); mirror
                top, tip = span               # (vertical flip only) gives the retroflex "\" lean
                sy = (top - tip) / (a_ymax - a_ymin)
                sx = 1 if mirror else -1
                t = Transform(sx, 0, 0, -sy, (cx + off) - sx * a_cx, top + a_ymin * sy)
            else:      # above: upright, natural size; bottom lands at the letter-body top
                t = Transform(1, 0, 0, 1, (cx + off) - a_cx, x_height - a_ymin)
            acute.replay(TransformPen(pen, t))
        glyf[cmap[target_cp]] = pen.glyph()

    single = (SINGLE_TOP * x_height, SINGLE_TIP * upm)
    double = (DOUBLE_TOP * x_height, DOUBLE_TIP * upm)
    stroke_copies(0x0326, [0], span=single)
    stroke_copies(0x0348, [-sep / 2, sep / 2], span=double)
    stroke_copies(0x0316, [0], span=single, mirror=True)   # the retroflex "\" tail
    stroke_copies(0x0313, [0])
    stroke_copies(0x030E, [-sep / 2, sep / 2])
    print(f"  stroke marks: below \"/\" {single[0]:.0f}→{single[1]:.0f} (single) / "
          f"{double[0]:.0f}→{double[1]:.0f} (double ×2, sep {sep:.0f}) / \"\\\" retroflex; "
          f"above upright natural from {x_height:.0f}")


def build():
    from fontTools.ttLib import TTFont
    from fontTools.subset import Subsetter, Options

    chars = charset()
    font = TTFont(SRC)
    cmap = font.getBestCmap()
    missing = sorted(c for c in chars if ord(c) not in cmap and not unicodedata.category(c).startswith("C"))
    if missing:
        print("MISSING from source font:", [f"U+{ord(c):04X} {unicodedata.name(c, '?')}" for c in missing])
        return 1

    opts = Options()
    opts.layout_features = ["*"]            # keep GPOS/GSUB — mark anchoring is the point
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.glyph_names = True                 # keep real glyph names — the SVG round-trip keys on them
    ss = Subsetter(opts)
    ss.populate(unicodes=[ord(c) for c in chars])
    ss.subset(font)

    _customize_stroke_marks(font)         # procedural SEED shapes for the stroke marks …
    import importlib.util
    spec = importlib.util.spec_from_file_location("font_svg", os.path.join(ROOT, "scripts", "font_svg.py"))
    font_svg = importlib.util.module_from_spec(spec); spec.loader.exec_module(font_svg)
    overridden = font_svg.import_overrides(font)      # … which any fonts/svg/*.svg edits REPLACE

    # OFL-compliant rename: drop the reserved name ("Noto"), keep attribution + license.
    name = font["name"]
    renames = {1: "Diaphone", 4: "Diaphone Regular", 6: "Diaphone-Regular", 16: "Diaphone"}
    for nid, val in renames.items():
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    cp = name.getDebugName(0) or ""
    note = " Diaphone is a derivative work (SIL OFL 1.1); reserved font names removed."
    name.setName(cp + note, 0, 3, 1, 0x409)
    name.setName("SIL Open Font License 1.1 — see fonts/OFL.txt", 13, 3, 1, 0x409)

    font.save(OUT)
    gpos = "GPOS" in font
    print(f"wrote {os.path.relpath(OUT, ROOT)} · {len(chars)} chars · "
          f"{font['maxp'].numGlyphs} glyphs · mark positioning {'kept' if gpos else 'MISSING'}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
