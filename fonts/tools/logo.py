#!/usr/bin/env python3
"""The Diafon mark -> docs/logo/: the system's two iconic marks, the double
dot above and the anchor below; the letter between them is implied. One
geometry (VARIANTS['mark']), the finals only: the two-tone mark light and
dark, the inline mark for the pages, the app icon square and rounded, the
Android adaptive layers, the browser extension's tile in its two states, PNGs at every icon size and the macOS icns.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'docs', 'logo')
INK, PAPER, ACCENT = '#1a1d24', '#f5f6f8', '#0e7c86'
S = 1024

# per 1000 of the tile: dot radius, dot spacing, dot centre y; the anchor's
# top y, spine length, head and foot widths, and its angles off vertical at
# the head (a0) and at the foot (a1): it leaves at x = hx and bends leftward
# only, from a0 to a1; the ink is centred in the tile, both ways
VARIANTS = {
    # the mark: dots r 90, 280 apart, at 210; the anchor leaves x 600 at y 450,
    # 400 long, 100 -> 120 wide, bending leftward from 30 to 70 degrees
    'mark': dict(r=90, apart=280, dy=210, top=490, length=400, head=100, foot=120, a0=30, a1=70, hx=630),
}


def hook(cx, top, length, head_w, tip_w, a0, a1, fill):
    """The anchor: from a rounded head at (cx, top) the stroke runs down and to
    the left only, leaving at a0 degrees off vertical and arriving at the foot
    at a1 degrees off vertical (30 -> 60: a gentle, one-way bend); `length`
    is the spine's length. The width eases from head_w to tip_w. y grows down.
    Returns (svg, (foot_x, foot_y))."""
    import math
    hw, tw = head_w / 2, tip_w / 2
    d0 = (-math.sin(math.radians(a0)), math.cos(math.radians(a0)))
    d1 = (-math.sin(math.radians(a1)), math.cos(math.radians(a1)))
    avg = ((d0[0] + d1[0]) / 2, (d0[1] + d1[1]) / 2)
    fx, fy = cx + avg[0] * length, top + avg[1] * length
    c1 = (cx + d0[0] * length / 3, top + d0[1] * length / 3)
    c2 = (fx - d1[0] * length / 3, fy - d1[1] * length / 3)
    # offsets perpendicular to the local direction, eased in width
    def side(pt, d, w, sgn):
        return (pt[0] + sgn * w * d[1], pt[1] - sgn * w * d[0])
    w1 = hw + (tw - hw) / 3
    w2 = hw + (tw - hw) * 2 / 3
    hl, hr = side((cx, top), d0, hw, -1), side((cx, top), d0, hw, 1)
    fl, fr = side((fx, fy), d1, tw, -1), side((fx, fy), d1, tw, 1)
    c1l, c1r = side(c1, d0, w1, -1), side(c1, d0, w1, 1)
    c2l, c2r = side(c2, d1, w2, -1), side(c2, d1, w2, 1)
    f = lambda p: f'{p[0]:.1f} {p[1]:.1f}'
    svg = (f'<path fill="{fill}" d="M{f(hl)} A{hw} {hw} 0 0 1 {f(hr)} '
           f'C{f(c1r)} {f(c2r)} {f(fr)} A{tw} {tw} 0 0 1 {f(fl)} '
           f'C{f(c2l)} {f(c1l)} {f(hl)} Z"/>')
    return svg, (fx, fy)


def dots(cx, cy, r, apart, fill):
    return ''.join(f'<circle cx="{cx + sgn * apart / 2}" cy="{cy}" r="{r}" fill="{fill}"/>' for sgn in (-1, 1))


def mark(v, fill, k=S / 1000):
    """The mark's body at scale k (tile units per 1000), its ink centred."""
    anchor, (fx, fy) = hook(v.get('hx', 500) * k, v['top'] * k, v['length'] * k, v['head'] * k, v['foot'] * k, v['a0'], v['a1'], fill)
    # centre the ink: the dots span 500 ± (apart/2 + r); the anchor's foot lies left
    left = min((500 - v['apart'] / 2 - v['r']) * k, fx - v['foot'] * k / 2)
    right = max((500 + v['apart'] / 2 + v['r']) * k, v.get('hx', 500) * k + v['head'] * k / 2)
    shift = 500 * k - (left + right) / 2
    top_ink = (v['dy'] - v['r']) * k
    bottom_ink = fy + v['foot'] * k / 2
    vshift = 500 * k - (top_ink + bottom_ink) / 2
    return (f'<g transform="translate({shift:.1f} {vshift:.1f})">'
            + dots(500 * k, v['dy'] * k, v['r'] * k, v['apart'] * k, fill) + anchor + '</g>')


def tile(fn, body, bg):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">'
           f'<rect width="{S}" height="{S}" rx="{S * 0.22:.0f}" fill="{bg}"/>{body}</svg>')
    open(os.path.join(OUT, fn), 'w').write(svg)


def main():
    import shutil
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        path = os.path.join(OUT, f)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    finals(VARIANTS['mark'])
    rasterise()
    android_resources(VARIANTS['mark'])
    print('\n'.join(sorted(os.listdir(OUT))))


def finals(v):
    """The deliverables: the primary two-tone mark on nothing (light and dark),
    the same coloured by the pages' CSS variables for inline use, the app icon
    (two-tone on ink, square and rounded; a light one on paper), and the
    Android adaptive icon layers (foreground within the 66/108 safe zone,
    two-tone on transparent; background ink)."""
    fin = OUT
    bare = lambda body: f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">{body}</svg>'
    open(os.path.join(fin, 'mark.svg'), 'w').write(bare(mark_two(v, ACCENT, INK)))
    open(os.path.join(fin, 'mark-dark.svg'), 'w').write(bare(mark_two(v, '#3ec8cf', PAPER)))
    # for inline use in the pages: the site's CSS variables colour it in either theme
    open(os.path.join(fin, 'mark-inline.svg'), 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="1em" height="1em" aria-hidden="true">'
        + mark_two(v, 'var(--accent, #0e7c86)', 'currentColor') + '</svg>')
    # the icon: the two-tone mark on an ink tile, bright teal dots and a paper
    # anchor, so both accents read on any launcher; a light one on paper too
    tile_svg = lambda body, bg, rx: (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">'
                                     f'<rect width="{S}" height="{S}" rx="{rx}" fill="{bg}"/>{body}</svg>')
    TEAL_BRIGHT = '#3ec8cf'
    open(os.path.join(fin, 'icon.svg'), 'w').write(tile_svg(mark_two(v, TEAL_BRIGHT, PAPER), INK, 0))     # square: platforms round it
    open(os.path.join(fin, 'icon-rounded.svg'), 'w').write(tile_svg(mark_two(v, TEAL_BRIGHT, PAPER), INK, f'{S * 0.22:.0f}'))
    open(os.path.join(fin, 'icon-light.svg'), 'w').write(tile_svg(mark_two(v, ACCENT, INK), PAPER, 0))
    # macOS: the system's icon grid, a rounded tile of 824 on the 1024 canvas
    # (the mark scaled with it); the small sizes of the icns take the bare
    # menu-bar mark above instead
    # the menu-bar sizes of the icns: the bare mark, large, no tile; teal dots
    # and a mid-grey anchor so it reads on a light and on a dark menu bar
    mk = 0.92
    open(os.path.join(fin, 'icon-menubar.svg'), 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">'
        f'<g transform="translate({S * (1 - mk) / 2:.0f} {S * (1 - mk) / 2:.0f})">{mark_two(v, TEAL_BRIGHT, "#8a93a3", S / 1000 * mk)}</g></svg>')
    # the input-source icon macOS shows in the input menu and in Input Sources,
    # in the system's own style: the wide rounded tile of the keyboard-layout
    # icons (22 x 15 pt), black, with a bold mark cut out of it (only alpha
    # counts: the system tints it for light and dark menus); a 15 px + 30 px
    # TIFF (DiafonMenu.tiff, in rasterise)
    TW, TH = 1466, 1000                                            # 22 : 15
    bold = dict(v, r=108, apart=300, head=128, foot=148)           # the weight of the tile's letters
    tk = 0.92                                                      # the mark's box against the tile's height
    open(os.path.join(fin, 'icon-template.svg'), 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TW} {TH}" width="{TW}" height="{TH}">'
        f'<mask id="cut"><rect width="{TW}" height="{TH}" fill="#fff"/>'
        f'<g transform="translate({(TW - TH * tk) / 2:.0f} {TH * (1 - tk) / 2:.0f})">{mark_two(bold, "#000", "#000", TH / 1000 * tk)}</g></mask>'
        f'<rect width="{TW}" height="{TH}" rx="{TH * 0.2:.0f}" fill="#000" mask="url(#cut)"/></svg>')
    mac = S * 824 / 1024
    off = (S - mac) / 2
    open(os.path.join(fin, 'icon-mac.svg'), 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">'
        f'<rect x="{off:.0f}" y="{off:.0f}" width="{mac:.0f}" height="{mac:.0f}" rx="{mac * 0.225:.0f}" fill="{INK}"/>'
        f'<g transform="translate({off:.0f} {off:.0f})">{mark_two(v, TEAL_BRIGHT, PAPER, S / 1000 * mac / S)}</g></svg>')
    k = S / 1000 * 0.58                                            # the adaptive icon's safe zone
    sh = S * (1 - 0.58) / 2
    open(os.path.join(fin, 'android-foreground.svg'), 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">'
        f'<g transform="translate({sh:.0f} {sh:.0f})">{mark_two(v, TEAL_BRIGHT, PAPER, k)}</g></svg>')
    open(os.path.join(fin, 'android-background.svg'), 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}"><rect width="{S}" height="{S}" fill="{INK}"/></svg>')
    # the browser extension's toolbar icon: the app icon's rounded tile, full
    # bleed (the toolbar pads it), the mark at 78% of it; two states, the
    # two-tone mark on ink when the conversion is on, all grey when it is off
    mk = 0.78
    mo = S * (1 - mk) / 2
    tile_state = lambda dots, anchor, bg: (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">'
        f'<rect width="{S}" height="{S}" rx="{S * 0.22:.0f}" fill="{bg}"/>'
        f'<g transform="translate({mo:.0f} {mo:.0f})">{mark_two(v, dots, anchor, S / 1000 * mk)}</g></svg>')
    open(os.path.join(fin, 'icon-tile-on.svg'), 'w').write(tile_state(TEAL_BRIGHT, PAPER, INK))
    open(os.path.join(fin, 'icon-tile-off.svg'), 'w').write(tile_state('#e9ecf1', PAPER, '#b9bfc9'))


def android_resources(v):
    """The adaptive launcher icon for the Android input method, as vector
    drawables: the two-tone mark within the safe zone over an ink background."""
    import re
    res = os.path.join(ROOT, 'input_methods', 'android', 'app', 'src', 'main', 'res')
    if not os.path.isdir(res):
        return
    k = S / 1000 * 0.58
    sh = S * (1 - 0.58) / 2
    body = mark_two(v, '#3ec8cf', PAPER, k)
    # the mark body is <g transform="translate(x y)">circles + path</g>: vector drawables
    # take a <group> with translateX/Y and <path>s; circles become arc paths
    m = re.match(r'<g transform="translate\(([-\d.]+) ([-\d.]+)\)">(.*)</g>$', body)
    tx, ty, inner = float(m.group(1)) + sh, float(m.group(2)) + sh, m.group(3)
    paths = []
    for cx, cy, r, fill in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)" fill="(#[0-9a-fA-F]+)"/>', inner):
        cx, cy, r = float(cx), float(cy), float(r)
        paths.append((fill, f'M{cx - r:.1f} {cy:.1f} A{r:.1f} {r:.1f} 0 1 0 {cx + r:.1f} {cy:.1f} A{r:.1f} {r:.1f} 0 1 0 {cx - r:.1f} {cy:.1f} Z'))
    for fill, d in re.findall(r'<path fill="(#[0-9a-fA-F]+)" d="([^"]+)"/>', inner):
        paths.append((fill, d))
    xml = ['<?xml version="1.0" encoding="utf-8"?>',
           '<!-- generated by fonts/tools/logo.py; do not edit -->',
           f'<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="{S}" android:viewportHeight="{S}">',
           f'    <group android:translateX="{tx:.1f}" android:translateY="{ty:.1f}">']
    xml += [f'        <path android:fillColor="{fill}" android:pathData="{d}"/>' for fill, d in paths]
    xml += ['    </group>', '</vector>', '']
    os.makedirs(os.path.join(res, 'drawable'), exist_ok=True)
    os.makedirs(os.path.join(res, 'mipmap-anydpi-v26'), exist_ok=True)
    open(os.path.join(res, 'drawable', 'ic_launcher_foreground.xml'), 'w').write('\n'.join(xml))
    open(os.path.join(res, 'values', 'ic_launcher_background.xml'), 'w').write(
        '<?xml version="1.0" encoding="utf-8"?>\n<!-- generated by fonts/tools/logo.py; do not edit -->\n'
        f'<resources><color name="ic_launcher_background">{INK}</color></resources>\n')
    adaptive = ('<?xml version="1.0" encoding="utf-8"?>\n<!-- generated by fonts/tools/logo.py; do not edit -->\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@color/ic_launcher_background"/>\n'
                '    <foreground android:drawable="@drawable/ic_launcher_foreground"/>\n'
                '</adaptive-icon>\n')
    for fn in ('ic_launcher.xml', 'ic_launcher_round.xml'):
        open(os.path.join(res, 'mipmap-anydpi-v26', fn), 'w').write(adaptive)
    print('  android launcher icon written')


def rasterise():
    """PNGs of the finals (icon 16..1024, mark, Android foreground) and the
    macOS .icns, with headless Chrome and iconutil where present; the SVG
    must carry width/height equal to the target size for Chrome to scale."""
    import re
    import shutil
    import subprocess
    import tempfile
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    if not os.path.exists(chrome):
        print('  (no Chrome: PNGs and icns not rasterised)')
        return
    fin = OUT
    png = os.path.join(fin, 'png')
    os.makedirs(png, exist_ok=True)
    tmp = tempfile.mkdtemp()
    jobs = ([('icon', sz) for sz in (1024, 512, 256, 128, 64, 32, 16)]
            + [('icon-mac', sz) for sz in (1024, 512, 256, 128)] + [('icon-rounded', 1024)] + [('icon-menubar', sz) for sz in (64, 32, 16)] + [('icon-template', sz) for sz in (30, 15)]
            + [('mark', 1024), ('android-foreground', 1024), ('icon-light', 1024)]
            + [(f'icon-tile-{st}', sz) for st in ('on', 'off') for sz in (128, 64, 48, 32, 16)])
    for name, sz in jobs:
        src = open(os.path.join(fin, name + '.svg')).read()
        vw, vh = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', src).groups())
        w = round(sz * vw / vh)                                    # sz is the height
        sized = os.path.join(tmp, f'{name}-{sz}.svg')
        open(sized, 'w').write(re.sub(r'width="[\d.]+" height="[\d.]+"', f'width="{w}" height="{sz}"', src, count=1))
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--default-background-color=00000000',
                        f'--window-size={w},{sz}', f'--screenshot={os.path.join(png, f"{name}-{sz}.png")}', 'file://' + sized],
                       capture_output=True)
    if shutil.which('iconutil'):
        iconset = os.path.join(tmp, 'Diafon.iconset')
        os.makedirs(iconset)
        for s_ in (16, 32, 128, 256, 512):
            src = 'icon-tile-on' if s_ <= 32 else 'icon-mac'       # menu-bar sizes: the full-bleed tile, as the extension's
            shutil.copy(os.path.join(png, f'{src}-{s_}.png'), os.path.join(iconset, f'icon_{s_}x{s_}.png'))
            shutil.copy(os.path.join(png, f'{src}-{s_ * 2}.png'), os.path.join(iconset, f'icon_{s_}x{s_}@2x.png'))
        subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', os.path.join(fin, 'Diafon.icns')], capture_output=True)
    if shutil.which('tiffutil'):       # the input-source icon: 16 px and its @2x in one TIFF
        subprocess.run(['tiffutil', '-cathidpicheck', os.path.join(png, 'icon-template-15.png'),
                        os.path.join(png, 'icon-template-30.png'), '-out', os.path.join(fin, 'DiafonMenu.tiff')],
                       capture_output=True)
    shutil.rmtree(tmp)
    ext = os.path.join(ROOT, 'extensions', 'browser', 'icons')       # the extension's two states
    if os.path.isdir(os.path.dirname(ext)):
        os.makedirs(ext, exist_ok=True)
        for st in ('on', 'off'):
            for sz in (128, 48, 32, 16):
                shutil.copy(os.path.join(png, f'icon-tile-{st}-{sz}.png'), os.path.join(ext, f'{st}-{sz}.png'))
        print('  extension icons written')


def mark_two(v, dot_fill, anchor_fill, k=S / 1000):
    anchor, (fx, fy) = hook(v['hx'] * k, v['top'] * k, v['length'] * k, v['head'] * k, v['foot'] * k, v['a0'], v['a1'], anchor_fill)
    left = min((500 - v['apart'] / 2 - v['r']) * k, fx - v['foot'] * k / 2)
    right = max((500 + v['apart'] / 2 + v['r']) * k, v['hx'] * k + v['head'] * k / 2)
    shift = 500 * k - (left + right) / 2
    top_ink = (v['dy'] - v['r']) * k
    bottom_ink = fy + v['foot'] * k / 2
    vshift = 500 * k - (top_ink + bottom_ink) / 2
    return (f'<g transform="translate({shift:.1f} {vshift:.1f})">' + dots(500 * k, v['dy'] * k, v['r'] * k, v['apart'] * k, dot_fill) + anchor + '</g>')


if __name__ == '__main__':
    main()
