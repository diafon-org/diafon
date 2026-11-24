// The strip above the keys, the keyboard's top row. Between words it is the
// digit row; inside a word, once the word names something (its emoji), the
// suggestions take the digits' place, and a tap puts one in the word's place.
// A key at the strip's end then switches between the two (123, or the first
// emoji), so a tone can always be typed; the side chosen last stays.
// With text selected in the app, a chip that converts the selection.
import UIKit

final class StripView: UIView {
    enum Content: Equatable {
        /// The digit row; with a word's first emoji, the key at the end that brings its emoji back.
        case digits(String?)
        /// A word's emoji, and the key at the end that brings the digits back.
        case emoji([String])
        case convert(String)
    }

    var onDigit: ((Character) -> Void)?
    var onEmoji: ((String) -> Void)?
    var onConvert: (() -> Void)?
    /// The key at the strip's end: the other side (digits, emoji).
    var onSwitch: (() -> Void)?

    private let digits = DigitRow()
    private let scroll = UIScrollView()
    private let row = UIStackView()
    private let other = UIButton(type: .system)
    private var digitsEnd: NSLayoutConstraint!, scrollEnd: NSLayoutConstraint!
    private var shown: Content?
    static let height: CGFloat = 44
    private static let otherWidth: CGFloat = 44

    override init(frame: CGRect) {
        super.init(frame: frame)
        digits.onDigit = { [weak self] d in UIDevice.current.playInputClick(); self?.onDigit?(d) }
        scroll.showsHorizontalScrollIndicator = false
        row.axis = .horizontal
        row.spacing = 6
        row.alignment = .center
        other.tintColor = Theme.ink
        other.accessibilityIdentifier = "strip:switch"
        other.addAction(UIAction { [weak self] _ in UIDevice.current.playInputClick(); self?.onSwitch?() }, for: .touchDown)
        for v in [digits, scroll, other] as [UIView] { v.translatesAutoresizingMaskIntoConstraints = false; addSubview(v) }
        digitsEnd = digits.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -3)
        scrollEnd = scroll.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -6)
        row.translatesAutoresizingMaskIntoConstraints = false
        scroll.addSubview(row)
        NSLayoutConstraint.activate([
            digits.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 3),
            digitsEnd,
            other.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -3),
            other.widthAnchor.constraint(equalToConstant: Self.otherWidth),
            other.topAnchor.constraint(equalTo: topAnchor),
            other.bottomAnchor.constraint(equalTo: bottomAnchor),
            digits.topAnchor.constraint(equalTo: topAnchor),
            digits.bottomAnchor.constraint(equalTo: bottomAnchor),
            scroll.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 6),
            scrollEnd,
            scroll.topAnchor.constraint(equalTo: topAnchor),
            scroll.bottomAnchor.constraint(equalTo: bottomAnchor),
            row.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor),
            row.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor),
            row.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor),
            row.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor),
            row.heightAnchor.constraint(equalTo: scroll.frameLayoutGuide.heightAnchor),
        ])
        show(.digits(nil))
    }
    required init?(coder: NSCoder) { fatalError() }

    func show(_ content: Content) {
        guard content != shown else { return }        // the digits keep their touch between keys
        shown = content
        var onDigits = false, switchTo: String? = nil
        if case .digits(let e) = content { onDigits = true; switchTo = e }
        if case .emoji = content { switchTo = "123" }
        digits.isHidden = !onDigits
        scroll.isHidden = onDigits
        other.isHidden = switchTo == nil
        if let switchTo {
            other.setTitle(switchTo, for: .normal)
            other.titleLabel?.font = .systemFont(ofSize: onDigits ? 24 : 15)
            other.accessibilityLabel = onDigits ? "emoji" : "digits"
        }
        digitsEnd.constant = switchTo == nil ? -3 : -(3 + Self.otherWidth)
        scrollEnd.constant = switchTo == nil ? -6 : -(3 + Self.otherWidth)
        row.arrangedSubviews.forEach { $0.removeFromSuperview() }
        switch content {
        case .digits: break
        case .emoji(let list):
            for e in list { row.addArrangedSubview(emojiChip(e) { [weak self] in self?.onEmoji?(e) }) }
        case .convert(let target):
            row.addArrangedSubview(chip("Convert selection", "to " + target) { [weak self] in self?.onConvert?() })
        }
        scroll.contentOffset = .zero
    }

    private func emojiChip(_ e: String, tap: @escaping () -> Void) -> UIView {
        var cfg = UIButton.Configuration.plain()
        cfg.attributedTitle = AttributedString(e, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 26)]))
        cfg.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 8, bottom: 2, trailing: 8)
        let b = UIButton(configuration: cfg)
        b.accessibilityLabel = e
        b.addAction(UIAction { _ in tap() }, for: .touchUpInside)
        return b
    }

    private func chip(_ big: String, _ small: String, tap: @escaping () -> Void) -> UIView {
        var cfg = UIButton.Configuration.plain()
        cfg.attributedTitle = AttributedString(big, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 16), .foregroundColor: Theme.accent]))
        cfg.attributedSubtitle = AttributedString(small, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 9), .foregroundColor: Theme.muted]))
        cfg.titleAlignment = .center
        cfg.titlePadding = 0
        cfg.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 10, bottom: 2, trailing: 10)
        cfg.background.backgroundColor = Theme.key
        cfg.background.cornerRadius = 8
        cfg.background.strokeColor = Theme.accent
        cfg.background.strokeWidth = 2
        let b = UIButton(configuration: cfg)
        b.accessibilityLabel = "\(big), \(small)"
        b.addAction(UIAction { _ in tap() }, for: .touchUpInside)
        return b
    }
}

/// The digits, as keys: every touch is a key on touch down, any number of
/// fingers at once and the same digit as fast as it comes (a UIButton turns a
/// quick second tap into a repeat event and takes one finger at a time).
final class DigitRow: UIView {
    var onDigit: ((Character) -> Void)?
    private let digits = Array("1234567890")
    private var down: [ObjectIdentifier: Int] = [:]

    override init(frame: CGRect) {
        super.init(frame: frame)
        isMultipleTouchEnabled = true
        backgroundColor = .clear
        contentMode = .redraw
    }
    required init?(coder: NSCoder) { fatalError() }

    private func cell(_ i: Int) -> CGRect {
        let w = bounds.width / CGFloat(digits.count)
        return CGRect(x: CGFloat(i) * w, y: 0, width: w, height: bounds.height)
    }

    override func draw(_ rect: CGRect) {
        let pressed = Set(down.values)
        let attrs: [NSAttributedString.Key: Any] = [.font: UIFont.systemFont(ofSize: 20), .foregroundColor: Theme.ink]
        for (i, d) in digits.enumerated() {
            let r = cell(i)
            if pressed.contains(i) {
                Theme.pressed.setFill()
                UIBezierPath(roundedRect: r.insetBy(dx: 3, dy: 4), cornerRadius: 6).fill()
            }
            let text = String(d) as NSString
            let size = text.size(withAttributes: attrs)
            text.draw(at: CGPoint(x: r.midX - size.width / 2, y: r.midY - size.height / 2), withAttributes: attrs)
        }
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        for t in touches {
            let x = t.location(in: self).x
            let i = max(0, min(digits.count - 1, Int(x / max(1, bounds.width) * CGFloat(digits.count))))
            down[ObjectIdentifier(t)] = i
            onDigit?(digits[i])
        }
        setNeedsDisplay()
    }
    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) { lift(touches) }
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) { lift(touches) }
    private func lift(_ touches: Set<UITouch>) {
        for t in touches { down.removeValue(forKey: ObjectIdentifier(t)) }
        setNeedsDisplay()
    }

    // one element per digit, for VoiceOver and the UI tests (key:1 …)
    private final class DigitElement: UIAccessibilityElement {
        var activate: (() -> Void)?
        override func accessibilityActivate() -> Bool { activate?(); return true }
    }
    // kept between calls and rebuilt only when the row is laid out anew: a list made afresh on
    // every call is freed before the system reads it (the UI test then finds only the last digit)
    private var axCache: [Any] = [], axWidth: CGFloat = -1
    override var accessibilityElements: [Any]? {
        get {
            if axWidth != bounds.width || axCache.isEmpty {
                axWidth = bounds.width
                axCache = digits.enumerated().map { i, d in
                    let e = DigitElement(accessibilityContainer: self)
                    e.accessibilityLabel = String(d)
                    e.accessibilityIdentifier = "key:\(d)"
                    e.accessibilityTraits = .keyboardKey
                    e.accessibilityFrameInContainerSpace = cell(i)
                    e.activate = { [weak self] in self?.onDigit?(d) }
                    return e
                }
            }
            return axCache
        }
        set {}
    }
}
