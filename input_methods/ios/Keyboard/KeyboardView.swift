// The keys: the 26 letters on the chosen base layout (Layouts.swift), two
// pages of signs behind the Diafon logo key, and the few functional keys; the
// digits are on the strip above (StripView). Drawn in one view,
// not one view per key, so a touch between keys still lands on the nearest.
// Characters are emitted on touch down, as on Android: the layout has no
// slide corrections to wait for, and fast typists overlap their taps. The
// globe is a real UIButton, since the system's input-mode list needs one.
import UIKit

enum Key: Equatable {
    case char(Character), space, backspace, shift, enter, logo, more, globe
}

final class KeyboardView: UIView {
    var onKey: ((Key) -> Void)?
    /// A long press on the logo key: the menu, at the touch's point (in this view).
    var onLogoHold: ((CGPoint) -> Void)?
    /// A long press on the space bar: the modes alone.
    var onSpaceHold: (() -> Void)?
    /// The held logo or space touch moving over the open menu, and let go.
    var onMenuDrag: ((CGPoint) -> Void)?
    var onMenuRelease: ((CGPoint) -> Void)?

    var layoutCode = "qwerty" { didSet { if layoutCode != oldValue { rebuild() } } }
    var showsGlobe = false { didSet { if showsGlobe != oldValue { rebuild() } } }
    /// The signs instead of the letters (the logo key), and which of their two pages.
    var symbolsPage = false { didSet { if symbolsPage != oldValue { if !symbolsPage { morePage = false }; rebuild() } } }
    var morePage = false { didSet { if morePage != oldValue { rebuild() } } }
    var shifted = false { didSet { setNeedsDisplay() } }
    var capsLock = false { didSet { setNeedsDisplay() } }
    var enabledMode = true { didSet { setNeedsDisplay() } }
    var returnLabel = "return" { didSet { setNeedsDisplay() } }
    /// The mode in use, named on the space bar.
    var spaceLabel = "" { didSet { setNeedsDisplay() } }

    let globeButton = UIButton(type: .system)

    /// The height of one row; the controller sizes the keyboard from it.
    static func rowHeight(for traits: UITraitCollection, landscape: Bool) -> CGFloat {
        if traits.userInterfaceIdiom == .pad { return landscape ? 62 : 54 }
        return landscape ? 34 : 46
    }
    var rowHeight: CGFloat = 46 { didSet { setNeedsLayout() } }
    static let rowCount = 4

    private struct Slot { let key: Key; var rect: CGRect }
    private var rows: [[(Key, CGFloat)]] = []
    private var slots: [Slot] = []
    private var down: [ObjectIdentifier: Key] = [:]          // touch → the key it is on
    private var repeatTimer: Timer?
    private var holdTimer: Timer?
    /// The logo touch: where it started (letters or signs), whether it slid off the
    /// key, whether its hold opened the menu.
    private var logoTouch: ObjectIdentifier?
    private var logoFromLetters = false, logoSlid = false, logoHeld = false
    /// The space touch: space goes in on release, unless a hold opened the modes.
    private var spaceTouch: ObjectIdentifier?
    private var spaceHeld = false
    private let gap: CGFloat = 6

    override init(frame: CGRect) {
        super.init(frame: frame)
        isMultipleTouchEnabled = true
        backgroundColor = .clear
        contentMode = .redraw
        globeButton.setImage(UIImage(systemName: "globe"), for: .normal)
        globeButton.tintColor = Theme.ink
        globeButton.backgroundColor = Theme.functional
        globeButton.layer.cornerRadius = 5
        globeButton.isHidden = true
        globeButton.accessibilityLabel = "next keyboard"
        addSubview(globeButton)
        rebuild()
    }
    required init?(coder: NSCoder) { fatalError() }

    /// The signs, on two pages: the common ones first.
    static let signs = [[".,?!'\"-:;/", "()@&#%+=*_", "~<>$€^|"],
                        ["[]{}\\`…•§°", "¥£¢¿¡«»„“”", "‘’–—·×÷"]]

    private func rebuild() {
        let letters = Layouts.get(layoutCode).rows
        func keys(_ s: String) -> [(Key, CGFloat)] { s.map { (.char($0), 1) } }
        func sided(_ left: Key, _ s: String) -> [(Key, CGFloat)] {
            let side = max(1, (10 - CGFloat(s.count)) / 2)     // the side keys share what the row leaves
            return [(left, side)] + keys(s) + [(.backspace, side)]
        }
        var bottom: [(Key, CGFloat)] = [(.logo, 1.75)]
        if showsGlobe { bottom.append((.globe, 1.25)) }
        bottom += [(.space, showsGlobe ? 5 : 6.25), (.enter, 2)]
        let page = Self.signs[morePage ? 1 : 0]
        rows = symbolsPage
            ? [keys(page[0]), keys(page[1]), sided(.more, page[2]), bottom]
            : [keys(letters[0]), keys(letters[1]), sided(.shift, letters[2]), bottom]
        globeButton.isHidden = !showsGlobe
        setNeedsLayout(); setNeedsDisplay()
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        slots.removeAll()
        let unit = bounds.width / 10
        for (r, row) in rows.enumerated() {
            let total = row.reduce(0) { $0 + $1.1 }
            var x = (bounds.width - total * unit) / 2
            let top = CGFloat(r) * rowHeight
            for (key, w) in row {
                slots.append(Slot(key: key, rect: CGRect(x: x + gap / 2, y: top + gap, width: w * unit - gap, height: rowHeight - gap)))
                x += w * unit
            }
        }
        if let g = slots.first(where: { $0.key == .globe }) { globeButton.frame = g.rect }
        rebuildAccessibility()
        setNeedsDisplay()
    }

    /// The logo key's frame, for the menu that opens from it.
    var logoFrame: CGRect { slots.first { $0.key == .logo }?.rect ?? .zero }
    var spaceFrame: CGRect { slots.first { $0.key == .space }?.rect ?? .zero }

    // MARK: accessibility: one element per key, for VoiceOver and for UI tests

    private func spoken(_ key: Key) -> String {
        switch key {
        case .char(let c): return label(key).isEmpty ? String(c) : label(key)
        case .space: return "space"
        case .backspace: return "delete"
        case .shift: return capsLock ? "caps lock" : "shift"
        case .enter: return returnLabel
        case .logo: return "diafon"
        case .more: return morePage ? "first signs" : "more signs"
        case .globe: return "next keyboard"
        }
    }

    private final class KeyElement: UIAccessibilityElement {
        var activate: (() -> Void)?
        override func accessibilityActivate() -> Bool { activate?(); return true }
    }

    private func rebuildAccessibility() {
        accessibilityElements = slots.map { s -> Any in
            if s.key == .globe { return globeButton }
            let e = KeyElement(accessibilityContainer: self)
            e.accessibilityLabel = s.key == .logo ? (symbolsPage ? "letters" : "signs; hold for the Diafon menu") : spoken(s.key)
            if case .char(let c) = s.key { e.accessibilityIdentifier = "key:\(c)" } else { e.accessibilityIdentifier = "key:" + spoken(s.key) }
            e.accessibilityTraits = .keyboardKey
            e.accessibilityFrameInContainerSpace = s.rect
            e.activate = { [weak self] in
                if s.key == .logo { self?.symbolsPage.toggle(); self?.onKey?(.logo) } else { self?.emit(s.key) }
            }
            return e
        }
    }

    override func setNeedsDisplay() {
        super.setNeedsDisplay()
        if !slots.isEmpty { rebuildAccessibility() }     // labels follow shift and mode
    }

    override var intrinsicContentSize: CGSize { CGSize(width: UIView.noIntrinsicMetric, height: rowHeight * CGFloat(Self.rowCount) + gap) }

    // MARK: drawing

    private func label(_ key: Key) -> String {
        switch key {
        case .char(let c): return shifted || capsLock ? String(c).uppercased() : String(c)
        case .space: return spaceLabel
        case .backspace: return "⌫"
        case .shift: return capsLock ? "⇪" : "⇧"
        case .enter: return returnLabel
        case .logo: return symbolsPage ? "abc" : ""
        case .more: return morePage ? "1/2" : "2/2"
        case .globe: return ""
        }
    }

    /// The Diafon mark (docs/logo/mark.svg): two dots and the stroke below them.
    private func drawMark(in r: CGRect, color: UIColor) {
        let box = CGRect(x: 222, y: 94, width: 476, height: 712)   // the mark's own bounds
        let s = min(r.width / box.width, r.height / box.height)
        let ox = r.midX - box.midX * s, oy = r.midY - box.midY * s
        func p(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: ox + x * s, y: oy + y * s) }
        color.setFill()
        for cx in [322.0, 598.0] as [CGFloat] {
            UIBezierPath(arcCenter: p(cx, 193.2), radius: 99.36 * s, startAngle: 0, endAngle: .pi * 2, clockwise: true).fill()
        }
        let path = UIBezierPath()
        path.move(to: p(528.6, 421.4))
        path.addArc(withCenter: p(579.6, 450.8), radius: 58.88 * s, startAngle: atan2(421.4 - 450.8, 528.6 - 579.6),
                    endAngle: atan2(480.2 - 450.8, 630.6 - 579.6), clockwise: true)
        path.addCurve(to: p(338.0, 737.1), controlPoint1: p(571.9, 588.0), controlPoint2: p(452.2, 692.2))
        path.addArc(withCenter: p(314.7, 673.1), radius: 68.08 * s, startAngle: atan2(737.1 - 673.1, 338.0 - 314.7),
                    endAngle: atan2(609.1 - 673.1, 291.4 - 314.7), clockwise: true)
        path.addCurve(to: p(528.6, 421.4), controlPoint1: p(407.7, 570.0), controlPoint2: p(464.6, 526.1))
        path.close()
        path.fill()
    }

    override func draw(_ rect: CGRect) {
        let pressed = Set(down.values.map { "\($0)" })
        for s in slots where s.key != .globe {
            let functional: Bool
            if case .char = s.key { functional = false } else { functional = s.key != .space }
            let on = s.key == .shift && (shifted || capsLock)
            let fill: UIColor = pressed.contains("\(s.key)") ? Theme.pressed : on ? Theme.accent : functional ? Theme.functional : Theme.key
            Theme.shadow.setFill()
            UIBezierPath(roundedRect: s.rect.offsetBy(dx: 0, dy: 1), cornerRadius: 5).fill()
            fill.setFill()
            UIBezierPath(roundedRect: s.rect, cornerRadius: 5).fill()

            if s.key == .logo && !symbolsPage {
                drawMark(in: s.rect.insetBy(dx: 8, dy: 9), color: enabledMode ? Theme.accent : Theme.muted)
                continue
            }
            var color = on ? Theme.onAccent : Theme.ink
            var font = UIFont.systemFont(ofSize: functional ? 16 : 22)
            if case .char(let c) = s.key {
                if let op = Theme.operators[c], enabledMode, !symbolsPage { color = op; font = .systemFont(ofSize: 22, weight: .semibold) }
            }
            if [.enter, .logo, .more].contains(s.key) { font = .systemFont(ofSize: 15) }
            if s.key == .space { font = .systemFont(ofSize: 13); color = Theme.muted }
            let text = label(s.key) as NSString
            let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: color]
            let size = text.size(withAttributes: attrs)
            text.draw(at: CGPoint(x: s.rect.midX - size.width / 2, y: s.rect.midY - size.height / 2), withAttributes: attrs)
        }
    }

    // MARK: touches

    /// The key under a point, or the nearest one in its row.
    private func slot(at p: CGPoint) -> Int? {
        layoutIfNeeded()
        if let i = slots.firstIndex(where: { $0.rect.insetBy(dx: -gap / 2, dy: -gap / 2).contains(p) }) { return i }
        let row = slots.indices.filter { abs(slots[$0].rect.midY - p.y) <= rowHeight / 2 }
        return row.min { abs(slots[$0].rect.midX - p.x) < abs(slots[$1].rect.midX - p.x) }
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        for t in touches {
            guard let i = slot(at: t.location(in: self)) else { continue }
            let key = slots[i].key
            down[ObjectIdentifier(t)] = key
            switch key {
            case .logo:
                // as the system's 123 key: the signs come up at once, so a slide can
                // pick one; a hold that stays on the key opens the menu instead
                logoTouch = ObjectIdentifier(t)
                logoFromLetters = !symbolsPage
                logoSlid = false; logoHeld = false
                if logoFromLetters { symbolsPage = true }
                let at = t.location(in: self)
                holdTimer = Timer.scheduledTimer(withTimeInterval: 0.45, repeats: false) { [weak self] _ in
                    guard let self, !self.logoSlid else { return }
                    self.logoHeld = true
                    if self.logoFromLetters { self.symbolsPage = false }
                    self.onLogoHold?(at)
                }
            case .space:
                spaceTouch = ObjectIdentifier(t)
                spaceHeld = false
                holdTimer?.invalidate()
                holdTimer = Timer.scheduledTimer(withTimeInterval: 0.45, repeats: false) { [weak self] _ in
                    guard let self, self.spaceTouch != nil else { return }
                    self.spaceHeld = true
                    self.onSpaceHold?()
                }
            case .backspace:
                emit(key)
                repeatTimer = Timer.scheduledTimer(withTimeInterval: 0.45, repeats: false) { [weak self] _ in
                    self?.repeatTimer = Timer.scheduledTimer(withTimeInterval: 0.08, repeats: true) { _ in self?.emit(.backspace) }
                }
            case .globe: break
            default: emit(key)
            }
        }
        setNeedsDisplay()
    }

    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        if let t = touches.first(where: { ObjectIdentifier($0) == spaceTouch }), spaceHeld {
            onMenuDrag?(t.location(in: self)); return
        }
        guard let t = touches.first(where: { ObjectIdentifier($0) == logoTouch }) else { return }
        let p = t.location(in: self)
        if logoHeld { onMenuDrag?(p); return }
        guard let i = slot(at: p) else { return }
        let key = slots[i].key
        if key != .logo { logoSlid = true; holdTimer?.invalidate(); holdTimer = nil }
        if down[ObjectIdentifier(t)] != key { down[ObjectIdentifier(t)] = key; setNeedsDisplay() }
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) { release(touches, fire: true) }
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) { release(touches, fire: false) }

    private func release(_ touches: Set<UITouch>, fire: Bool) {
        for t in touches {
            let id = ObjectIdentifier(t)
            guard let key = down.removeValue(forKey: id) else { continue }
            if id == logoTouch {
                logoTouch = nil
                holdTimer?.invalidate(); holdTimer = nil
                if logoHeld { if fire { onMenuRelease?(t.location(in: self)) }; continue }
                if logoSlid {
                    // a slide from the logo: the key let go on, once, then back where it started
                    if logoFromLetters { symbolsPage = false }
                    if fire, case .char = key { emit(key) }
                    if fire, key == .space || key == .enter || key == .backspace { emit(key) }
                } else if !logoFromLetters {
                    symbolsPage = false                   // a tap on abc: the letters back
                    onKey?(.logo)
                } else {
                    onKey?(.logo)                         // a tap: the signs stay up
                }
                continue
            }
            if id == spaceTouch {
                spaceTouch = nil
                holdTimer?.invalidate(); holdTimer = nil
                if spaceHeld { if fire { onMenuRelease?(t.location(in: self)) } } else if fire { emit(.space) }
                continue
            }
            if key == .backspace { repeatTimer?.invalidate(); repeatTimer = nil }
        }
        setNeedsDisplay()
    }

    private func emit(_ key: Key) {
        UIDevice.current.playInputClick()
        onKey?(key)
    }
}

/// Input clicks play only from a view that says it wants them.
final class KeyboardInputView: UIInputView, UIInputViewAudioFeedback {
    var enableInputClicksWhenVisible: Bool { true }
}
