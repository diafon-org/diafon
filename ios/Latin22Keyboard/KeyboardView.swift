/// Full QWERTY keyboard view rendered programmatically.
///
/// Supports three modes (alpha / numeric / symbols) and shift (off / once / caps-lock).
/// Key layout adapts to any bounds set by the parent view controller.
/// Reports final character actions to the delegate — shift and mode switching are
/// handled internally and never leak to the outside.
import UIKit

// MARK: - Data model

struct KeyModel {
    let label: String
    let action: KeyActionType
    var widthWeight: CGFloat = 1.0
    var style: KeyStyleType = .character
}

enum KeyActionType: Equatable {
    case character(String)
    case space
    case returnKey
    case backspace
    case shift
    case switchToMode(KeyboardMode)
}

enum KeyStyleType { case character, function, spaceBar, returnStyle }

enum KeyboardMode: Equatable { case alpha, numeric, symbols }

enum ShiftState { case off, once, locked }

// MARK: - Delegate

protocol KeyboardViewDelegate: AnyObject {
    func keyboardView(_ view: KeyboardView, didProduceAction action: KeyActionType)
}

// MARK: - KeyboardView

final class KeyboardView: UIView {

    weak var delegate: KeyboardViewDelegate?

    private(set) var mode: KeyboardMode = .alpha
    private(set) var shiftState: ShiftState = .off

    private var keyButtons: [UIButton: KeyModel] = [:]
    private var deleteTimer: Timer?
    private var lastBuiltSize: CGSize = .zero

    // MARK: Layout constants (recalculated from actual bounds in layoutSubviews)

    private let rowCount     = 4
    private let topPad:    CGFloat = 8
    private let bottomPad: CGFloat = 4
    private let rowGap:    CGFloat = 11
    private let keyGap:    CGFloat = 6
    private let sidePad:   CGFloat = 3
    private let cornerR:   CGFloat = 10

    // MARK: - Init

    override init(frame: CGRect) { super.init(frame: frame); setup() }
    required init?(coder: NSCoder) { super.init(coder: coder); setup() }

    private func setup() {
        backgroundColor = kbBg
    }

    // MARK: - Layout

    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.size != lastBuiltSize else { return }
        lastBuiltSize = bounds.size
        buildKeys()
    }

    override func traitCollectionDidChange(_ prev: UITraitCollection?) {
        super.traitCollectionDidChange(prev)
        backgroundColor = kbBg
        lastBuiltSize = .zero   // force rebuild with new colours
        setNeedsLayout()
    }

    // MARK: - Build

    private func buildKeys() {
        subviews.forEach { $0.removeFromSuperview() }
        keyButtons.removeAll()
        lastBuiltSize = bounds.size

        let rows = currentRows
        let rowH = (bounds.height - topPad - bottomPad
                    - CGFloat(rowCount - 1) * rowGap) / CGFloat(rowCount)
        var y = topPad

        for row in rows {
            let totalW = row.reduce(0) { $0 + $1.widthWeight }
            let gapsW  = CGFloat(row.count - 1) * keyGap
            let usable = bounds.width - 2 * sidePad - gapsW
            var x = sidePad

            for key in row {
                let w = usable * key.widthWeight / totalW
                let btn = makeButton(key, frame: CGRect(x: x, y: y, width: w, height: rowH))
                addSubview(btn)
                keyButtons[btn] = key
                x += w + keyGap
            }
            y += rowH + rowGap
        }
    }

    private func makeButton(_ key: KeyModel, frame: CGRect) -> UIButton {
        let btn = UIButton(type: .custom)
        btn.frame = frame
        btn.layer.cornerRadius = cornerR
        btn.layer.shadowColor   = UIColor.black.cgColor
        btn.layer.shadowOffset  = CGSize(width: 0, height: 1)
        btn.layer.shadowOpacity = 0.35
        btn.layer.shadowRadius  = 0.5
        btn.layer.shadowPath    = UIBezierPath(roundedRect: CGRect(origin: .zero, size: frame.size),
                                              cornerRadius: cornerR).cgPath
        btn.clipsToBounds = false

        btn.setTitle(key.label, for: .normal)
        btn.titleLabel?.font = font(for: key.style)
        btn.setTitleColor(keyText, for: .normal)
        btn.backgroundColor = bgColor(for: key.style)

        btn.addTarget(self, action: #selector(down(_:)),  for: .touchDown)
        btn.addTarget(self, action: #selector(up(_:)),    for: [.touchUpInside, .touchUpOutside, .touchCancel])
        btn.addTarget(self, action: #selector(tapped(_:)), for: .touchUpInside)

        if key.action == .backspace {
            let lp = UILongPressGestureRecognizer(target: self, action: #selector(deleteLong(_:)))
            lp.minimumPressDuration = 0.4
            btn.addGestureRecognizer(lp)
        }

        // Highlight shift/mode key when active
        if key.action == .shift, shiftState != .off {
            btn.backgroundColor = shiftActiveColor
        }

        return btn
    }

    // MARK: - Key data

    private var currentRows: [[KeyModel]] {
        switch mode {
        case .alpha:   return alphaRows()
        case .numeric: return numericRows()
        case .symbols: return symbolRows()
        }
    }

    private func alphaRows() -> [[KeyModel]] {
        func letter(_ s: String) -> KeyModel {
            let out = shiftState != .off ? s.uppercased() : s
            return KeyModel(label: out, action: .character(out))
        }
        let row1 = "qwertyuiop".map { letter(String($0)) }
        let row2 = "asdfghjkl".map  { letter(String($0)) }

        let shiftLabel = shiftState == .locked ? "⇪" : "⇧"
        var row3: [KeyModel] = [
            KeyModel(label: shiftLabel,  action: .shift,     widthWeight: 1.5, style: .function)
        ]
        "zxcvbnm".forEach { row3.append(letter(String($0))) }
        row3.append(KeyModel(label: "⌫", action: .backspace, widthWeight: 1.5, style: .function))

        var row4: [KeyModel] = [
            KeyModel(label: "123",    action: .switchToMode(.numeric), widthWeight: 1.5, style: .function),
        ]
        row4.append(contentsOf: [
            KeyModel(label: "space", action: .space,                   widthWeight: 4.5, style: .spaceBar),
            KeyModel(label: "return",action: .returnKey,               widthWeight: 2.0, style: .returnStyle),
        ])

        return [row1, row2, row3, row4]
    }

    private func numericRows() -> [[KeyModel]] {
        let row1 = "1234567890".map { KeyModel(label: String($0), action: .character(String($0))) }
        let row2 = ["-","/",":",";","(",")",  "$","&","@","\""].map { KeyModel(label: $0, action: .character($0)) }
        return [row1, row2, punctuationRow(modeKey: KeyModel(label: "#+=", action: .switchToMode(.symbols), widthWeight: 1.5, style: .function)), bottomRow(modeLabel: "ABC", modeTarget: .alpha)]
    }

    private func symbolRows() -> [[KeyModel]] {
        let row1 = ["[","]","{","}","#","%","^","*","+","="].map { KeyModel(label: $0, action: .character($0)) }
        let row2 = ["_","\\","|","~","<",">","€","£","¥","•"].map { KeyModel(label: $0, action: .character($0)) }
        return [row1, row2, punctuationRow(modeKey: KeyModel(label: "123", action: .switchToMode(.numeric), widthWeight: 1.5, style: .function)), bottomRow(modeLabel: "ABC", modeTarget: .alpha)]
    }

    /// Builds the shared punctuation row used in numeric and symbol modes.
    private func punctuationRow(modeKey: KeyModel) -> [KeyModel] {
        var row = [modeKey]
        [".", ",", "?", "!", "'"].forEach { row.append(KeyModel(label: $0, action: .character($0))) }
        row.append(KeyModel(label: "⌫", action: .backspace, widthWeight: 1.5, style: .function))
        return row
    }

    private func bottomRow(modeLabel: String, modeTarget: KeyboardMode) -> [KeyModel] {
        var items: [KeyModel] = [
            KeyModel(label: modeLabel, action: .switchToMode(modeTarget), widthWeight: 1.5, style: .function),
        ]
        items.append(contentsOf: [
            KeyModel(label: "space",  action: .space,                    widthWeight: 4.5, style: .spaceBar),
            KeyModel(label: "return", action: .returnKey,                widthWeight: 2.0, style: .returnStyle),
        ])
        return items
    }

    // MARK: - Actions

    @objc private func down(_ sender: UIButton) {
        guard let m = keyButtons[sender] else { return }
        sender.backgroundColor = highlight(for: m.style)
    }

    @objc private func up(_ sender: UIButton) {
        guard let m = keyButtons[sender] else { return }
        sender.backgroundColor = bgColor(for: m.style)
        if m.action == .shift, shiftState != .off {
            sender.backgroundColor = shiftActiveColor
        }
    }

    @objc private func tapped(_ sender: UIButton) {
        guard let m = keyButtons[sender] else { return }
        handleAction(m.action)
    }

    @objc private func deleteLong(_ g: UILongPressGestureRecognizer) {
        switch g.state {
        case .began:
            deleteTimer = Timer.scheduledTimer(withTimeInterval: 0.08, repeats: true) { [weak self] _ in
                guard let self else { return }
                self.delegate?.keyboardView(self, didProduceAction: .backspace)
            }
        case .ended, .cancelled, .failed:
            deleteTimer?.invalidate()
            deleteTimer = nil
        default: break
        }
    }

    private func handleAction(_ action: KeyActionType) {
        switch action {
        case .shift:
            switch shiftState {
            case .off:    shiftState = .once
            case .once:   shiftState = .locked
            case .locked: shiftState = .off
            }
            buildKeys()

        case .switchToMode(let m):
            mode = m
            if m == .alpha { shiftState = .off }
            buildKeys()

        case .character:
            // Auto-cancel one-shot shift after a character is typed
            if shiftState == .once {
                shiftState = .off
                buildKeys()
            }
            delegate?.keyboardView(self, didProduceAction: action)

        default:
            delegate?.keyboardView(self, didProduceAction: action)
        }
    }

    // MARK: - Appearance

    private var isDark: Bool { traitCollection.userInterfaceStyle == .dark }

    private var kbBg: UIColor {
        isDark ? UIColor(white: 0.13, alpha: 1)
               : UIColor(red: 0.659, green: 0.690, blue: 0.722, alpha: 1)
    }
    private var keyText: UIColor { isDark ? .white : .black }
    private var shiftActiveColor: UIColor { UIColor.systemBlue.withAlphaComponent(0.85) }

    private func bgColor(for style: KeyStyleType) -> UIColor {
        switch style {
        case .character:   return isDark ? UIColor(white: 0.40, alpha: 1) : .white
        case .function,
             .spaceBar,
             .returnStyle: return isDark ? UIColor(white: 0.24, alpha: 1) : UIColor(white: 0.66, alpha: 1)
        }
    }

    private func highlight(for style: KeyStyleType) -> UIColor {
        switch style {
        case .character:   return isDark ? UIColor(white: 0.56, alpha: 1) : UIColor(white: 0.85, alpha: 1)
        default:           return isDark ? UIColor(white: 0.34, alpha: 1) : UIColor(white: 0.55, alpha: 1)
        }
    }

    private func font(for style: KeyStyleType) -> UIFont {
        switch style {
        case .character:  return .systemFont(ofSize: 22, weight: .regular)
        default:          return .systemFont(ofSize: 15, weight: .regular)
        }
    }
}

