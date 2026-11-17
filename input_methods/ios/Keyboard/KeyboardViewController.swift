// The keyboard extension: keys in, the streaming rule (Session), the app's
// text field out through the text document proxy. Everything that decides
// what the editor shows is in Session, checked on a Mac
// (tests/test_ios_session.py); this file only wires it to UIKit.
import UIKit

/// The host's text field, as Session needs it.
final class ProxySink: TextSink {
    weak var controller: UIInputViewController?
    init(_ controller: UIInputViewController) { self.controller = controller }
    private var proxy: UITextDocumentProxy? { controller?.textDocumentProxy }
    func insertText(_ text: String) { proxy?.insertText(text) }
    func deleteBackward() { proxy?.deleteBackward() }
    func setMarkedText(_ text: String) { proxy?.setMarkedText(text, selectedRange: NSRange(location: (text as NSString).length, length: 0)) }
    func unmarkText() { proxy?.unmarkText() }
    var contextBefore: String? { proxy?.documentContextBeforeInput }
}

final class KeyboardViewController: UIInputViewController {
    private let prefs = Prefs.shared
    private lazy var session: Session = {
        let s = Session(sink: ProxySink(self), mode: prefs.tailMode, render: prefs.renderer())
        s.wordwise = !prefs.universal
        s.preview = prefs.renderer(letters: true)
        return s
    }()
    private let keys = KeyboardView()
    private let strip = StripView()
    private let panel = SettingsPanel()
    private let menu = ModeMenu()
    private var height: NSLayoutConstraint?
    private var shifted = false, capsLock = false
    private var lastShiftTap = Date.distantPast, lastSpaceAt = Date.distantPast
    private var observer: NSObjectProtocol?

    override func loadView() {
        view = KeyboardInputView(frame: .zero, inputViewStyle: .keyboard)
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = Theme.board
        for v in [strip, keys, panel, menu] as [UIView] { v.translatesAutoresizingMaskIntoConstraints = false; view.addSubview(v) }
        NSLayoutConstraint.activate([
            strip.topAnchor.constraint(equalTo: view.topAnchor),
            strip.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            strip.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            strip.heightAnchor.constraint(equalToConstant: StripView.height),
            keys.topAnchor.constraint(equalTo: strip.bottomAnchor),
            keys.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            keys.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            keys.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            panel.topAnchor.constraint(equalTo: view.topAnchor),
            panel.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            panel.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            panel.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            menu.topAnchor.constraint(equalTo: view.topAnchor),
            menu.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            menu.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            menu.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
        panel.isHidden = true

        keys.onKey = { [weak self] in self?.key($0) }
        keys.onLogoHold = { [weak self] _ in self?.showMenu() }
        keys.onSpaceHold = { [weak self] in self?.showMenu(modesOnly: true) }
        keys.onMenuDrag = { [weak self] p in guard let self else { return }; self.menu.drag(to: self.keys.convert(p, to: self.menu)) }
        keys.onMenuRelease = { [weak self] p in guard let self else { return }; self.menu.release(at: self.keys.convert(p, to: self.menu)) }
        menu.onPick = { [weak self] id in
            guard let self else { return }
            if id == "settings" { self.showSettings(true) } else { self.session.flush(); self.prefs.setMenuMode(id) }
        }
        keys.globeButton.addTarget(self, action: #selector(handleInputModeList(from:with:)), for: .allTouchEvents)
        strip.onDigit = { [weak self] d in self?.key(.char(d)) }
        strip.onEmoji = { [weak self] e in self?.session.pick(e); self?.autoShift(); self?.refresh() }
        strip.onConvert = { [weak self] in self?.convertSelection() }
        panel.onDone = { [weak self] in self?.showSettings(false) }
        observer = NotificationCenter.default.addObserver(forName: Prefs.changed, object: nil, queue: .main) { [weak self] _ in
            self?.prefsChanged()
        }
    }

    deinit { observer.map(NotificationCenter.default.removeObserver) }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        prefsChanged()
        autoShift()
    }

    override func viewWillLayoutSubviews() {
        keys.showsGlobe = needsInputModeSwitchKey
        let landscape = view.bounds.width > (view.window?.screen.bounds.height ?? view.bounds.height)
        let row = KeyboardView.rowHeight(for: traitCollection, landscape: landscape)
        keys.rowHeight = row
        let total = StripView.height + row * CGFloat(KeyboardView.rowCount) + 6
        if height == nil {
            height = view.heightAnchor.constraint(equalToConstant: total)
            height?.priority = .defaultHigh + 1
            height?.isActive = true
        } else if height?.constant != total {
            height?.constant = total
        }
        super.viewWillLayoutSubviews()
    }

    override func viewWillDisappear(_ animated: Bool) {
        session.flush()
        super.viewWillDisappear(animated)
    }

    // The host tells us the text or the cursor changed; ours or the person's.
    override func textDidChange(_ textInput: UITextInput?) {
        session.editorChanged()
        refresh()
    }

    override func selectionDidChange(_ textInput: UITextInput?) {
        session.editorChanged()
        refresh()
    }

    // MARK: keys

    private func key(_ key: Key) {
        if key != .space { lastSpaceAt = .distantPast }
        switch key {
        case .char(let c):
            let ch = (shifted || capsLock) && c.isLetter ? Character(String(c).uppercased()) : c
            if shifted, !capsLock { setShift(false) }
            type(ch)
        case .space:
            // a second space soon after a word's: a full stop and a space, as iOS's own
            let now = Date()
            if now.timeIntervalSince(lastSpaceAt) < 0.6, stopFits() {
                session.backspace()
                session.insertFinal(". ")
                lastSpaceAt = .distantPast
            } else {
                type(" ")
                lastSpaceAt = now
            }
            keys.symbolsPage = false                  // a sign and a space: the letters back
        case .backspace:
            session.backspace()
        case .shift:
            let now = Date()
            if capsLock { capsLock = false; setShift(false) }
            else if now.timeIntervalSince(lastShiftTap) < 0.3 { capsLock = true; setShift(true) }
            else { setShift(!shifted) }
            lastShiftTap = now
        case .enter:
            session.insertFinal("\n")
            keys.symbolsPage = false
        case .logo:
            break                                     // the key view switched the page
        case .more:
            keys.morePage.toggle()
        case .globe:
            break                                     // the UIButton handles it
        }
        if key != .shift { autoShift() }
        refresh()
    }

    /// The text ends with a word (or a closing sign) and one space: a double space
    /// may make it a full stop.
    private func stopFits() -> Bool {
        session.flush()
        let before = Array(textDocumentProxy.documentContextBeforeInput ?? "")
        guard before.count >= 2, before[before.count - 1] == " " else { return false }
        let c = before[before.count - 2]
        return c.isLetter || c.isNumber || c.unicodeScalars.first.map { (0x300...0x36F).contains($0.value) } == true
            || ")]\"'”’»".contains(c)
    }

    private func type(_ ch: Character) {
        if prefs.enabled { session.type(ch) } else { session.insertFinal(String(ch)) }
    }

    private func setShift(_ on: Bool) {
        shifted = on
        keys.shifted = on
        keys.capsLock = capsLock
    }

    /// Shift on at the start of a sentence, where the field asks for it.
    private func autoShift() {
        guard !capsLock, !keys.symbolsPage, session.pending.isEmpty else { return }
        let proxy = textDocumentProxy
        let before = proxy.documentContextBeforeInput ?? ""
        let start: Bool
        switch proxy.autocapitalizationType ?? .sentences {
        case .allCharacters: start = true
        case .words: start = before.isEmpty || before.last?.isWhitespace == true
        case .sentences:
            let t = before.trimmingCharacters(in: .whitespaces)
            start = t.isEmpty || t.hasSuffix("\n") || (before.last == " " && [".", "!", "?"].contains(t.last))
        default: start = false
        }
        if start != shifted { setShift(start) }
    }

    // MARK: the strip

    private func refresh() {
        keys.enabledMode = prefs.enabled
        keys.spaceLabel = prefs.enabled ? prefs.label() : "off"
        keys.returnLabel = returnLabel()
        if let sel = textDocumentProxy.selectedText, !sel.isEmpty, session.pending.isEmpty {
            strip.show(.convert(prefs.label()))
            return
        }
        // inside a word, its suggestions take the digits' place; a tone-aware mode
        // (Mandarin) keeps the digits, which write the syllable's tone
        let toneAware = prefs.enabled && prefs.output == "stage:zh"
        let emoji = toneAware || keys.symbolsPage ? [] : Emoji.choices(session.word)
        strip.show(emoji.isEmpty ? .digits : .emoji(emoji))
    }

    private func returnLabel() -> String {
        switch textDocumentProxy.returnKeyType ?? .default {
        case .go: return "go"
        case .google, .yahoo, .search: return "search"
        case .join: return "join"
        case .next: return "next"
        case .route: return "route"
        case .send: return "send"
        case .done: return "done"
        case .continue: return "continue"
        case .emergencyCall: return "call"
        default: return "return"
        }
    }

    /// The selection, in any spelling, read back from the source detected (the
    /// person's own languages preferred) and written in the mode in use.
    private func convertSelection() {
        guard let text = textDocumentProxy.selectedText, !text.isEmpty else { return }
        let target = prefs.output
        let source = Stages.sourceFor(text, target: target, prefer: prefs.preferredSources)
        textDocumentProxy.insertText(Stages.convert(text, source, target, tones: prefs.tones, join: prefs.join))
        refresh()
    }

    // MARK: the menu and settings

    /// The logo key's menu (the modes and the settings), or the space bar's (the modes alone).
    private func showMenu(modesOnly: Bool = false) {
        session.flush()
        var items = prefs.menuModes.map { (id: $0, title: prefs.menuTitle($0)) }
        if !modesOnly { items.append((id: "settings", title: "Settings…")) }
        menu.present(items, current: prefs.menuMode, anchor: keys.convert(modesOnly ? keys.spaceFrame : keys.logoFrame, to: menu))
    }

    private func showSettings(_ on: Bool) {
        session.flush()
        if on { panel.refresh() }
        panel.isHidden = !on
        refresh()
    }

    private func prefsChanged() {
        session.flush()                              // the shown tail belongs to the old renderer
        session.render = prefs.renderer()
        session.wordwise = !prefs.universal
        session.preview = prefs.renderer(letters: true)
        session.mode = prefs.tailMode
        keys.layoutCode = prefs.layout
        refresh()
    }
}
