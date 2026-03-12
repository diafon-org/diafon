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
    var symbolName: String? = nil
}

enum KeyActionType: Equatable {
    case character(String)
    case nextKeyboard
    case emojiKeyboard
    case space
    case returnKey
    case backspace
    case shift
    case switchToMode(KeyboardMode)
    case switchLanguage(String)
}

enum KeyStyleType { case character, function, spaceBar, returnStyle }

enum KeyboardMode: Equatable { case alpha, numeric, symbols, emoji }

enum ShiftState { case off, once, locked }

// MARK: - Delegate

protocol KeyboardViewDelegate: AnyObject {
    func keyboardView(_ view: KeyboardView, didProduceAction action: KeyActionType)
}

// MARK: - KeyboardView

final class KeyboardView: UIView {

    weak var delegate: KeyboardViewDelegate?

    /// Set to true when the system emoji keyboard is installed.
    /// Triggers a layout rebuild so the 😊 button appears/disappears automatically.
    var showsEmojiKey: Bool = false {
        didSet { guard oldValue != showsEmojiKey else { return }; lastBuiltSize = .zero; setNeedsLayout() }
    }

    /// All languages to offer in the picker. KVC keeps this up to date.
    var availableLanguages: [(id: String, name: String)] = []

    /// ID of the currently active language. Updates the space bar label and triggers rebuild.
    var currentLanguageID: String = "" {
        didSet { guard oldValue != currentLanguageID else { return }; lastBuiltSize = .zero; setNeedsLayout() }
    }

    /// When false the long-press language picker on the space bar is suppressed.
    var spacebarLangSwitchEnabled: Bool = true {
        didSet { guard oldValue != spacebarLangSwitchEnabled else { return }; lastBuiltSize = .zero; setNeedsLayout() }
    }

    private(set) var mode: KeyboardMode = .alpha
    private(set) var shiftState: ShiftState = .off

    private var keyButtons: [UIButton: KeyModel] = [:]
    private var deleteTimer: Timer?
    private var lastBuiltSize: CGSize = .zero
    private var calloutView: UIView?
    private var langPickerView: UIView?
    private var emojiPicker: EmojiPickerView!


    // MARK: Layout constants (recalculated from actual bounds in layoutSubviews)

    private let rowCount     = 4
    private let topPad:    CGFloat = 8
    private let bottomPad: CGFloat = 4
    private let rowGap:    CGFloat = 11
    private let keyGap:    CGFloat = 6
    private let sidePad:   CGFloat = 3
    private let cornerR:   CGFloat = 5

    // MARK: - Init

    override init(frame: CGRect) { super.init(frame: frame); setup() }
    required init?(coder: NSCoder) { super.init(coder: coder); setup() }

    private func setup() {
        backgroundColor = .clear
        // Add the emoji picker once and keep it in the hierarchy permanently.
        // Showing/hiding via isHidden avoids addSubview + NSLayoutConstraint.activate
        // being called from inside layoutSubviews, which corrupts UIKit's internal
        // layout tables and causes the *** key cannot be nil crash.
        let picker = EmojiPickerView()
        picker.delegate = self
        picker.translatesAutoresizingMaskIntoConstraints = false
        picker.isHidden = true
        addSubview(picker)
        NSLayoutConstraint.activate([
            picker.leadingAnchor.constraint(equalTo: leadingAnchor),
            picker.trailingAnchor.constraint(equalTo: trailingAnchor),
            picker.topAnchor.constraint(equalTo: topAnchor),
            picker.bottomAnchor.constraint(equalTo: bottomAnchor),
        ])
        emojiPicker = picker
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
        lastBuiltSize = .zero   // force rebuild with new colours
        setNeedsLayout()
    }

    // MARK: - Build

    private func buildKeys() {
        hideLangPicker()
        lastBuiltSize = bounds.size
        // Remove key button subviews (emoji picker stays in hierarchy, just hidden).
        subviews.filter { $0 !== emojiPicker }.forEach { $0.removeFromSuperview() }
        keyButtons.removeAll()
        calloutView = nil

        if mode == .emoji {
            showEmojiView()
            return
        }
        hideEmojiView()

        let rows = currentRows
        let rowH = (bounds.height - topPad - bottomPad
                    - CGFloat(rowCount - 1) * rowGap) / CGFloat(rowCount)
        var y = topPad

        // Pre-compute row-0 key width so row 1 ("asdfghjkl") can match it.
        let isAlpha = (mode == .alpha)
        let row0KeyW: CGFloat = {
            guard isAlpha, let row0 = rows.first else { return 0 }
            let totalW = row0.reduce(0) { $0 + $1.widthWeight }
            let gapsW  = CGFloat(row0.count - 1) * keyGap
            let usable = bounds.width - 2 * sidePad - gapsW
            return usable / totalW
        }()

        for (rowIndex, row) in rows.enumerated() {
            // Alpha row 1: same key width as row 0, centred with equal side padding.
            if isAlpha && rowIndex == 1 && row0KeyW > 0 {
                let rowContentW = CGFloat(row.count) * row0KeyW
                                + CGFloat(row.count - 1) * keyGap
                var x = (bounds.width - rowContentW) / 2
                for key in row {
                    let btn = makeButton(key, frame: CGRect(x: x, y: y, width: row0KeyW, height: rowH))
                    addSubview(btn)
                    keyButtons[btn] = key
                    x += row0KeyW + keyGap
                }
            } else {
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
            }
            y += rowH + rowGap
        }
    }

    private func makeButton(_ key: KeyModel, frame: CGRect) -> UIButton {
        let btn = UIButton(type: .custom)
        btn.frame = frame
        btn.layer.cornerRadius = cornerR
        btn.layer.shadowColor      = UIColor.black.cgColor
        btn.layer.shadowOffset     = CGSize(width: 0, height: 1)
        btn.layer.shadowOpacity    = 0.35
        btn.layer.shadowRadius     = 0.5
        btn.layer.shadowPath       = UIBezierPath(roundedRect: CGRect(origin: .zero, size: frame.size),
                                                 cornerRadius: cornerR).cgPath
        btn.clipsToBounds          = false
        // Cache the composited button+shadow as a bitmap so it isn't
        // recomposited on every frame — critical in the memory-limited
        // keyboard extension process.
        btn.layer.shouldRasterize       = true
        btn.layer.rasterizationScale    = UIScreen.main.scale

        let symConf = UIImage.SymbolConfiguration(pointSize: 17, weight: .light)
        if let sym = key.symbolName,
           let img = UIImage(systemName: sym)?
                       .withConfiguration(symConf)
                       .withRenderingMode(.alwaysTemplate) {
            btn.setImage(img, for: .normal)
            btn.tintColor = keyText
        } else {
            btn.setTitle(key.label, for: .normal)
            btn.titleLabel?.font = font(for: key.style)
            btn.setTitleColor(keyText, for: .normal)
        }
        btn.backgroundColor = bgColor(for: key.style)

        btn.addTarget(self, action: #selector(down(_:)),  for: .touchDown)
        btn.addTarget(self, action: #selector(up(_:)),    for: [.touchUpInside, .touchUpOutside, .touchCancel])
        btn.addTarget(self, action: #selector(tapped(_:)), for: .touchUpInside)

        if key.action == .backspace {
            let lp = UILongPressGestureRecognizer(target: self, action: #selector(deleteLong(_:)))
            lp.minimumPressDuration = 0.4
            btn.addGestureRecognizer(lp)
        }

        if key.action == .space, availableLanguages.count > 1, spacebarLangSwitchEnabled {
            let lp = UILongPressGestureRecognizer(target: self, action: #selector(spaceLong(_:)))
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
        case .emoji:   return []   // handled by EmojiPickerView overlay
        }
    }

    private func alphaRows() -> [[KeyModel]] {
        func letter(_ s: String) -> KeyModel {
            let out = shiftState != .off ? s.uppercased() : s
            return KeyModel(label: out, action: .character(out))
        }
        let row1 = "qwertyuiop".map { letter(String($0)) }
        let row2 = "asdfghjkl".map  { letter(String($0)) }

        let shiftSym: String = {
            switch shiftState {
            case .off:    return "shift"
            case .once:   return "shift.fill"
            case .locked: return "capslock.fill"
            }
        }()
        var row3: [KeyModel] = [
            KeyModel(label: "", action: .shift,     widthWeight: 1.5, style: .function, symbolName: shiftSym)
        ]
        "zxcvbnm".forEach { row3.append(letter(String($0))) }
        row3.append(KeyModel(label: "", action: .backspace, widthWeight: 1.5, style: .function, symbolName: "delete.backward"))

        let numKey   = KeyModel(label: "123", action: .switchToMode(.numeric), widthWeight: 1.5, style: .function)
        let spaceLbl = availableLanguages.count > 1 ? currentLanguageID.uppercased() : "space"
        var row4: [KeyModel] = [numKey]
        if showsEmojiKey {
            row4.append(KeyModel(label: "😊", action: .switchToMode(.emoji), widthWeight: 1.5, style: .function))
        }
        row4.append(KeyModel(label: spaceLbl, action: .space,     widthWeight: showsEmojiKey ? 4.5 : 6.0, style: .spaceBar))
        row4.append(KeyModel(label: "return", action: .returnKey, widthWeight: 2.0, style: .returnStyle))

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
        return [
            KeyModel(label: modeLabel, action: .switchToMode(modeTarget), widthWeight: 1.5, style: .function),
            KeyModel(label: "space",   action: .space,                    widthWeight: 5.5, style: .spaceBar),
            KeyModel(label: "return",  action: .returnKey,                widthWeight: 2.0, style: .returnStyle),
        ]
    }

    // MARK: - Actions

    @objc private func down(_ sender: UIButton) {
        guard let m = keyButtons[sender] else { return }
        sender.backgroundColor = highlight(for: m.style)
        if case .character(let s) = m.action { showCallout(for: sender, character: s) }
    }

    @objc private func up(_ sender: UIButton) {
        guard let m = keyButtons[sender] else { return }
        sender.backgroundColor = bgColor(for: m.style)
        if m.action == .shift, shiftState != .off {
            sender.backgroundColor = shiftActiveColor
        }
        hideCallout()
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
            cancelDeleteTimer()
        default: break
        }
    }

    /// Cancel the repeat-delete timer — call from KVC's viewWillDisappear.
    func cancelDeleteTimer() {
        deleteTimer?.invalidate()
        deleteTimer = nil
    }

    @objc private func spaceLong(_ g: UILongPressGestureRecognizer) {
        guard g.state == .began, let btn = g.view as? UIButton else { return }
        if langPickerView != nil { hideLangPicker() } else { showLangPicker(above: btn) }
    }

    // MARK: - Language picker

    private func showLangPicker(above spaceBtn: UIButton) {
        guard availableLanguages.count > 1 else { return }
        let btnW: CGFloat = 48
        let btnH: CGFloat = 36
        let gap:  CGFloat = 12
        let totalW = CGFloat(availableLanguages.count) * btnW
                   + CGFloat(availableLanguages.count - 1) * gap
        let x = max(4, min(spaceBtn.frame.midX - totalW / 2, bounds.width - totalW - 4))
        let y = spaceBtn.frame.minY - btnH - 8

        let container = UIView(frame: CGRect(x: x, y: y, width: totalW, height: btnH))
        container.backgroundColor = bgColor(for: .character)
        container.layer.cornerRadius = 10
        container.layer.shadowColor   = UIColor.black.cgColor
        container.layer.shadowOpacity = 0.25
        container.layer.shadowRadius  = 6
        container.layer.shadowOffset  = CGSize(width: 0, height: -2)
        container.isUserInteractionEnabled = true

        for (i, lang) in availableLanguages.enumerated() {
            let isCurrent = lang.id == currentLanguageID
            let code = String(lang.id.prefix(2)).uppercased()
            let btn = UIButton(type: .custom)
            btn.frame = CGRect(x: CGFloat(i) * (btnW + gap), y: 0, width: btnW, height: btnH)
            btn.setTitle(code, for: .normal)
            btn.titleLabel?.font      = .systemFont(ofSize: 15, weight: isCurrent ? .bold : .regular)
            btn.setTitleColor(isCurrent ? .white : keyText, for: .normal)
            btn.backgroundColor = isCurrent ? UIColor.systemBlue : .clear
            btn.layer.cornerRadius  = 6
            btn.tag = i
            btn.addTarget(self, action: #selector(langPickerTapped(_:)), for: .touchUpInside)
            container.addSubview(btn)
        }
        addSubview(container)
        langPickerView = container
    }

    private func hideLangPicker() {
        langPickerView?.removeFromSuperview()
        langPickerView = nil
    }

    @objc private func langPickerTapped(_ sender: UIButton) {
        let lang = availableLanguages[sender.tag]
        hideLangPicker()
        handleAction(.switchLanguage(lang.id))
    }

    // MARK: - Key callout

    private func showCallout(for btn: UIButton, character: String) {
        hideCallout()
        guard btn.frame.minY > topPad + 4 else { return }  // skip top row
        let calloutH: CGFloat = 48
        let calloutW = max(btn.frame.width + 8, CGFloat(44))
        let x = max(4, min(btn.frame.midX - calloutW / 2, bounds.width - calloutW - 4))
        let y = btn.frame.minY - calloutH - 2
        let v = UIView(frame: CGRect(x: x, y: y, width: calloutW, height: calloutH))
        v.isUserInteractionEnabled = false
        v.backgroundColor = bgColor(for: .character)
        v.layer.cornerRadius = 10
        v.layer.shadowColor   = UIColor.black.cgColor
        v.layer.shadowOpacity = 0.20
        v.layer.shadowRadius  = 4
        v.layer.shadowOffset  = CGSize(width: 0, height: -1)
        let lbl = UILabel(frame: v.bounds)
        lbl.text = character
        lbl.font = .systemFont(ofSize: 26, weight: .light)
        lbl.textColor = keyText
        lbl.textAlignment = .center
        v.addSubview(lbl)
        addSubview(v)
        calloutView = v
    }

    private func hideCallout() {
        calloutView?.removeFromSuperview()
        calloutView = nil
    }

    private func handleAction(_ action: KeyActionType) {
        hideLangPicker()
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
            if m == .alpha || m == .emoji { shiftState = .off }
            buildKeys()

        case .character:
            // Auto-cancel one-shot shift after a character is typed.
            // Relabel buttons in-place instead of calling buildKeys() —
            // avoids allocating/deallocating 35+ UIButton objects per keypress.
            if shiftState == .once {
                shiftState = .off
                // Collect mutations first — mutating keyButtons while iterating
                // over it is undefined behaviour and causes the nil-key crash.
                var updates: [(UIButton, KeyModel)] = []
                for (btn, model) in keyButtons {
                    if case .character(let s) = model.action, s.count == 1, s == s.uppercased(), s != s.lowercased() {
                        let lower = s.lowercased()
                        btn.setTitle(lower, for: .normal)
                        updates.append((btn, KeyModel(label: lower, action: .character(lower),
                                                      widthWeight: model.widthWeight, style: model.style)))
                    }
                    if model.action == .shift {
                        btn.backgroundColor = bgColor(for: .function)
                        let symConf = UIImage.SymbolConfiguration(pointSize: 17, weight: .light)
                        if let img = UIImage(systemName: "shift")?
                                         .withConfiguration(symConf)
                                         .withRenderingMode(.alwaysTemplate) {
                            btn.setImage(img, for: .normal)
                            btn.tintColor = keyText
                        }
                    }
                }
                for (btn, model) in updates { keyButtons[btn] = model }
            }
            delegate?.keyboardView(self, didProduceAction: action)

        default:
            delegate?.keyboardView(self, didProduceAction: action)
        }
    }

    // MARK: - Appearance

    private var isDark: Bool { traitCollection.userInterfaceStyle == .dark }

    // System keyboard colours (measured from iOS 26 on iPhone 14).

    private var keyText: UIColor { isDark ? .white : .black }
    private var shiftActiveColor: UIColor { UIColor.systemBlue.withAlphaComponent(0.85) }

    private func bgColor(for style: KeyStyleType) -> UIColor {
        isDark ? UIColor(red: 0.227, green: 0.227, blue: 0.247, alpha: 1)   // #3A3A3F
               : UIColor(red: 0.675, green: 0.694, blue: 0.729, alpha: 1)   // #ACB1BA
    }

    private func highlight(for style: KeyStyleType) -> UIColor {
        isDark ? UIColor(red: 0.320, green: 0.320, blue: 0.340, alpha: 1)
               : UIColor(red: 0.530, green: 0.545, blue: 0.573, alpha: 1)
    }

    private func font(for style: KeyStyleType) -> UIFont {
        switch style {
        case .character:  return .systemFont(ofSize: 22, weight: .regular)
        default:          return .systemFont(ofSize: 15, weight: .regular)
        }
    }

    // MARK: - Emoji view helpers

    private func showEmojiView() {
        emojiPicker.isHidden = false
        bringSubviewToFront(emojiPicker)
    }

    private func hideEmojiView() {
        emojiPicker.isHidden = true
    }
}

// MARK: - EmojiPickerViewDelegate

extension KeyboardView: EmojiPickerViewDelegate {
    func emojiPickerView(_ view: EmojiPickerView, didSelectEmoji emoji: String) {
        delegate?.keyboardView(self, didProduceAction: .character(emoji))
    }
    func emojiPickerViewDidDismiss(_ view: EmojiPickerView) {
        mode = .alpha
        shiftState = .off
        lastBuiltSize = .zero   // force full rebuild
        setNeedsLayout()
    }
}

