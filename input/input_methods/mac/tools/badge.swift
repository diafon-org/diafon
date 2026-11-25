// The keyboards' icons for the input menu, the menu bar and the keyboard switcher:
// one PDF per input mode, 22 x 16 pt as the system's own (US, HU). All of the icon
// is drawn here, the frame included: a filled rounded frame with the content cut
// out of it, in one colour, so the system tints it for the highlight and the dark
// menu bar (TISIconIsTemplate). Diafon itself is the mark (two dots and the stroke
// below them, docs/logo/mark.svg); a language keeps the two dots where they are and
// has its code in the stroke's place (HU, CS, PY), which also tells Diafon – Magyar
// from the system's Hungarian.
//
// Usage: swift tools/badge.swift <out directory> <name>=<code> …   (an empty code: the mark)
import CoreGraphics
import CoreText
import Foundation

let dir = URL(fileURLWithPath: CommandLine.arguments[1])
let W: CGFloat = 22, H: CGFloat = 16, markHeight: CGFloat = 11, codeSize: CGFloat = 7.6
// the mark's drawing is y down, 712 high, centred on 460, 450
let s = markHeight / 712
let place = CGAffineTransform(translationX: W / 2, y: H / 2).scaledBy(x: s, y: -s).translatedBy(x: -460, y: -450)

for arg in CommandLine.arguments.dropFirst(2) {
    let parts = arg.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false)
    let name = String(parts[0]), code = parts.count > 1 ? String(parts[1]) : ""
    var box = CGRect(x: 0, y: 0, width: W, height: H)
    guard let ctx = CGContext(dir.appendingPathComponent(name + ".pdf") as CFURL, mediaBox: &box, nil) else { exit(1) }
    ctx.beginPDFPage(nil)
    let path = CGMutablePath()       // what is cut out of the frame
    for cx in [322.0, 598.0] as [CGFloat] {
        path.addEllipse(in: CGRect(x: cx - 99.36, y: 193.2 - 99.36, width: 198.72, height: 198.72), transform: place)
    }
    if code.isEmpty {
        let stroke = CGMutablePath()
        stroke.move(to: CGPoint(x: 528.6, y: 421.4))
        stroke.addArc(center: CGPoint(x: 579.6, y: 450.8), radius: 58.88, startAngle: atan2(421.4 - 450.8, 528.6 - 579.6),
                      endAngle: atan2(480.2 - 450.8, 630.6 - 579.6), clockwise: false)
        stroke.addCurve(to: CGPoint(x: 338.0, y: 737.1), control1: CGPoint(x: 571.9, y: 588.0), control2: CGPoint(x: 452.2, y: 692.2))
        stroke.addArc(center: CGPoint(x: 314.7, y: 673.1), radius: 68.08, startAngle: atan2(737.1 - 673.1, 338.0 - 314.7),
                      endAngle: atan2(609.1 - 673.1, 291.4 - 314.7), clockwise: false)
        stroke.addCurve(to: CGPoint(x: 528.6, y: 421.4), control1: CGPoint(x: 407.7, y: 570.0), control2: CGPoint(x: 464.6, y: 526.1))
        stroke.closeSubpath()
        path.addPath(stroke, transform: place)
    } else {
        // the code in the system's bold letters, centred where the stroke sits
        let font = CTFontCreateUIFontForLanguage(.emphasizedSystem, codeSize, nil)!
        let line = CTLineCreateWithAttributedString(NSAttributedString(string: code, attributes: [kCTFontAttributeName as NSAttributedString.Key: font]))
        let width = CGFloat(CTLineGetTypographicBounds(line, nil, nil, nil))
        let origin = CGPoint(x: (W - width) / 2, y: 5.5 - CTFontGetCapHeight(font) / 2)
        for run in CTLineGetGlyphRuns(line) as! [CTRun] {
            let n = CTRunGetGlyphCount(run)
            var glyphs = [CGGlyph](repeating: 0, count: n), at = [CGPoint](repeating: .zero, count: n)
            CTRunGetGlyphs(run, CFRange(location: 0, length: n), &glyphs)
            CTRunGetPositions(run, CFRange(location: 0, length: n), &at)
            let attrs = CTRunGetAttributes(run) as NSDictionary
            let used = attrs[kCTFontAttributeName as String] as! CTFont
            for i in 0..<n {
                var t = CGAffineTransform(translationX: origin.x + at[i].x, y: origin.y + at[i].y)
                if let g = CTFontCreatePathForGlyph(used, glyphs[i], &t) { path.addPath(g) }
            }
        }
    }
    // a letter's outlines may overlap (P): subtract by winding, not by even-odd
    ctx.addPath(CGPath(roundedRect: box, cornerWidth: 3.6, cornerHeight: 3.6, transform: nil).subtracting(path, using: .winding))
    ctx.setFillColor(CGColor(gray: 0, alpha: 1))
    ctx.fillPath()
    ctx.endPDFPage()
    ctx.closePDF()
}
