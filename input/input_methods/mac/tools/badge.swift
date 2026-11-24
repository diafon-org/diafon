// The Diafon keyboard's icon for the input menu, the menu bar and the cursor badge:
// docs/logo/DiafonBadge.pdf, the bare mark (two dots and the stroke below them,
// docs/logo/mark.svg in the weight of the system's icon letters). Only the mark:
// the system draws the frame around a custom icon itself and tints it for the
// highlight and the dark menu bar, as it does for its own (Ainu@2x.pdf, 28 x 36).
//
// Usage: swift tools/badge.swift <out.pdf>
import CoreGraphics
import Foundation

let out = URL(fileURLWithPath: CommandLine.arguments[1])
var box = CGRect(x: 0, y: 0, width: 28, height: 36)
guard let ctx = CGContext(out as CFURL, mediaBox: &box, nil) else { exit(1) }
ctx.beginPDFPage(nil)
// the mark's own bounds, y down; drawn 22 pt high, centred
let mark = CGRect(x: 222, y: 94, width: 476, height: 712)
let s = 22 / mark.height
ctx.translateBy(x: box.midX, y: box.midY)
ctx.scaleBy(x: s, y: -s)
ctx.translateBy(x: -mark.midX, y: -mark.midY)
ctx.setFillColor(CGColor(gray: 0, alpha: 1))
for cx in [322.0, 598.0] as [CGFloat] {
    ctx.addEllipse(in: CGRect(x: cx - 99.36, y: 193.2 - 99.36, width: 198.72, height: 198.72))
}
ctx.fillPath()
ctx.move(to: CGPoint(x: 528.6, y: 421.4))
ctx.addArc(center: CGPoint(x: 579.6, y: 450.8), radius: 58.88, startAngle: atan2(421.4 - 450.8, 528.6 - 579.6),
           endAngle: atan2(480.2 - 450.8, 630.6 - 579.6), clockwise: false)
ctx.addCurve(to: CGPoint(x: 338.0, y: 737.1), control1: CGPoint(x: 571.9, y: 588.0), control2: CGPoint(x: 452.2, y: 692.2))
ctx.addArc(center: CGPoint(x: 314.7, y: 673.1), radius: 68.08, startAngle: atan2(737.1 - 673.1, 338.0 - 314.7),
           endAngle: atan2(609.1 - 673.1, 291.4 - 314.7), clockwise: false)
ctx.addCurve(to: CGPoint(x: 528.6, y: 421.4), control1: CGPoint(x: 407.7, y: 570.0), control2: CGPoint(x: 464.6, y: 526.1))
ctx.closePath()
ctx.fillPath()
ctx.endPDFPage()
ctx.closePDF()
