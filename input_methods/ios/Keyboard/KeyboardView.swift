// The keys: the 26 letters on the chosen base layout (Layouts.swift), digits
// for tones, a symbols page, and the few functional keys. Drawn in one view,
// not one view per key, so a touch between keys still lands on the nearest.
// Characters are emitted on touch down, as on Android: the layout has no
// slide corrections to wait for, and fast typists overlap their taps. The
// globe is a real UIButton, since the system's input-mode list needs one.
import UIKit

enum Key: Equatable {
    case char(Character), space, backspace, shift, enter, toggle, symbols, globe
}

final class KeyboardView: UIView {
    var onKey: ((Key) -> Void)?
    /// A long press on the toggle key: the settings panel.
    var onToggleHold: (() -> Void)?

    var layoutCode = "qwerty" { didSet { if layoutCode != oldValue { rebuild() } } }
    var showsGlobe = false { didSet { if showsGlobe != oldValue { rebuild() } } }
    var symbolsPage = false { didSet { if symbolsPage != oldValue { rebuild() } } }
    var shifted = false { didSet { setNeedsDisplay() } }
    var capsLock = false { didSet { setNeedsDisplay() } }
    var enabledMode = true { didSet { setNeedsDisplay() } }
    var returnLabel = "return" { didSet { setNeedsDisplay() } }

    let globeButton = UIButton(type: .system)

    /// The height of one row; the controller sizes the keyboard from it.
    static func rowHeight(for traits: UITraitCollection, landscape: Bool) -> CGFloat {
        if traits.userInterfaceIdiom == .pad { return landscape ? 62 : 54 }
        return landscape ? 34 : 46
    }
    var rowHeight: CGFloat = 46 { didSet { setNeedsLayout() } }
    static let rowCount = 5

    private struct Slot { let key: Key; var rect: CGRect }
    private var rows: [[(Key, CGFloat)]] = []
    private var slots: [Slot] = []
    private var down: [ObjectIdentifier: Int] = [:]          // touch → slot index
    private var repeatTimer: Timer?
    private var holdTimer: Timer?
    private var toggleHeld = false
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

    private func rebuild() {
        let letters = Layouts.get(layoutCode).rows
        let digits: [(Key, CGFloat)] = "1234567890".map { (.char($0), 1) }
        func keys(_ s: String) -> [(Key, CGFloat)] { s.map { (.char($0), 1) } }
        func sided(_ left: Key, _ s: String) -> [(Key, CGFloat)] {
            let side = max(1, (10 - CGFloat(s.count)) / 2)     // the side keys share what the row leaves
            return [(left, side)] + keys(s) + [(.backspace, side)]
        }
        var bottom: [(Key, CGFloat)] = [(.symbols, showsGlobe ? 1 : 1.25), (.toggle, 1.25)]
        if showsGlobe { bottom.append((.globe, 1)) }
        bottom += [(.char(","), 1), (.space, showsGlobe ? 3 : 3.75), (.char("."), 1), (.enter, 1.75)]
        rows = symbolsPage
            ? [digits, keys("-/:;()$&@\""), keys("[]{}#%^*+="), sided(.symbols, "?!'_~<>"), bottom]
            : [digits, keys(letters[0]), keys(letters[1]), sided(.shift, letters[2]), bottom]
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

    // MARK: accessibility: one element per key, for VoiceOver and for UI tests

    private func spoken(_ key: Key) -> String {
        switch key {
        case .char(let c): return label(key).isEmpty ? String(c) : label(key)
        case .space: return "space"
        case .backspace: return "delete"
        case .shift: return capsLock ? "caps lock" : "shift"
        case .enter: return returnLabel
        case .toggle: return enabledMode ? "Diafon on" : "Diafon off"
        case .symbols: return symbolsPage ? "letters" : "numbers and symbols"
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
            e.accessibilityLabel = spoken(s.key)
            if case .char(let c) = s.key { e.accessibilityIdentifier = "key:\(c)" } else { e.accessibilityIdentifier = "key:" + spoken(s.key) }
            e.accessibilityTraits = .keyboardKey
            e.accessibilityFrameInContainerSpace = s.rect
            e.activate = { [weak self] in self?.emit(s.key) }
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
        case .space: return enabledMode ? "" : "space"
        case .backspace: return "⌫"
        case .shift: return capsLock ? "⇪" : "⇧"
        case .enter: return returnLabel
        case .toggle: return enabledMode ? "Dia" : "abc"
        case .symbols: return symbolsPage ? "ABC" : "123"
        case .globe: return ""
        }
    }

    override func draw(_ rect: CGRect) {
        let pressed = Set(down.values)
        for (i, s) in slots.enumerated() where s.key != .globe {
            let functional: Bool
            if case .char = s.key { functional = false } else { functional = s.key != .space }
            let on = (s.key == .shift && (shifted || capsLock)) || (s.key == .toggle && enabledMode)
            let fill: UIColor = pressed.contains(i) ? Theme.pressed : on ? Theme.accent : functional ? Theme.functional : Theme.key
            Theme.shadow.setFill()
            UIBezierPath(roundedRect: s.rect.offsetBy(dx: 0, dy: 1), cornerRadius: 5).fill()
            fill.setFill()
            UIBezierPath(roundedRect: s.rect, cornerRadius: 5).fill()

            var color = on ? Theme.onAccent : Theme.ink
            var font = UIFont.systemFont(ofSize: functional ? 16 : 22)
            if case .char(let c) = s.key {
                if let op = Theme.operators[c], enabledMode, !symbolsPage { color = op; font = .systemFont(ofSize: 22, weight: .semibold) }
                if c.isNumber { font = .systemFont(ofSize: 18) }
            }
            if s.key == .enter || s.key == .symbols || (s.key == .space && !enabledMode) { font = .systemFont(ofSize: 15) }
            let text = label(s.key) as NSString
            let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: color]
            let size = text.size(withAttributes: attrs)
            text.draw(at: CGPoint(x: s.rect.midX - size.width / 2, y: s.rect.midY - size.height / 2), withAttributes: attrs)
        }
    }

    // MARK: touches

    /// The key under a point, or the nearest one in its row.
    private func slot(at p: CGPoint) -> Int? {
        if let i = slots.firstIndex(where: { $0.rect.insetBy(dx: -gap / 2, dy: -gap / 2).contains(p) }) { return i }
        let row = slots.indices.filter { abs(slots[$0].rect.midY - p.y) <= rowHeight / 2 }
        return row.min { abs(slots[$0].rect.midX - p.x) < abs(slots[$1].rect.midX - p.x) }
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        for t in touches {
            guard let i = slot(at: t.location(in: self)) else { continue }
            down[ObjectIdentifier(t)] = i
            let key = slots[i].key
            switch key {
            case .toggle:
                toggleHeld = false
                holdTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: false) { [weak self] _ in
                    self?.toggleHeld = true; self?.onToggleHold?()
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

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) { release(touches, fire: true) }
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) { release(touches, fire: false) }

    private func release(_ touches: Set<UITouch>, fire: Bool) {
        for t in touches {
            guard let i = down.removeValue(forKey: ObjectIdentifier(t)), i < slots.count else { continue }
            switch slots[i].key {
            case .toggle:
                holdTimer?.invalidate(); holdTimer = nil
                if fire, !toggleHeld { emit(.toggle) }
            case .backspace:
                repeatTimer?.invalidate(); repeatTimer = nil
            default: break
            }
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
