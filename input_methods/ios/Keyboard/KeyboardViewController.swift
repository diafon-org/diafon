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
    private lazy var session = Session(sink: ProxySink(self), mode: prefs.tailMode, render: prefs.renderer())
    private let keys = KeyboardView()
    private let strip = StripView()
    private let panel = SettingsPanel()
    private var height: NSLayoutConstraint?
    private var shifted = false, capsLock = false
    private var lastShiftTap = Date.distantPast, lastToggleTap = Date.distantPast
    private var observer: NSObjectProtocol?

    override func loadView() {
        view = KeyboardInputView(frame: .zero, inputViewStyle: .keyboard)
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = Theme.board
        for v in [strip, keys, panel] as [UIView] { v.translatesAutoresizingMaskIntoConstraints = false; view.addSubview(v) }
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
        ])
        panel.isHidden = true

        keys.onKey = { [weak self] in self?.key($0) }
        keys.onToggleHold = { [weak self] in self?.showSettings(true) }
        keys.globeButton.addTarget(self, action: #selector(handleInputModeList(from:with:)), for: .allTouchEvents)
        strip.onPick = { [weak self] text in self?.session.take(text); self?.refresh() }
        strip.onEmoji = { [weak self] e in self?.session.pick(e); self?.autoShift(); self?.refresh() }
        strip.onConvert = { [weak self] in self?.convertSelection() }
        strip.onGear = { [weak self] in self?.showSettings(true) }
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
        switch key {
        case .char(let c):
            let ch = (shifted || capsLock) && c.isLetter ? Character(String(c).uppercased()) : c
            if shifted, !capsLock { setShift(false) }
            type(ch)
        case .space:
            type(" ")
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
        case .toggle:
            // as the Shift tap on the Mac: a tap after a pause switches conversion off and
            // back on; taps in quick succession walk the cycle (Prefs.cycleMode)
            session.flush()
            let now = Date()
            if now.timeIntervalSince(lastToggleTap) < Prefs.tapWindow { prefs.cycleMode() } else { prefs.toggleOff() }
            lastToggleTap = now
        case .symbols:
            keys.symbolsPage.toggle()
        case .globe:
            break                                     // the UIButton handles it
        }
        if key != .shift { autoShift() }
        refresh()
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
        keys.returnLabel = returnLabel()
        if let sel = textDocumentProxy.selectedText, !sel.isEmpty, session.pending.isEmpty {
            strip.show(.convert(prefs.label()))
        } else if !prefs.enabled {
            strip.show(.note("abc · conversion off"))
        } else if session.pending.isEmpty {
            strip.show(.note("\(prefs.label()) · \(Layouts.get(prefs.layout).label)"))
        } else {
            let list = prefs.spellings(session.pending).map { (output: $0.output, text: $0.text, label: prefs.shortLabel($0.output)) }
            strip.show(.spellings(list, current: prefs.output, warn: prefs.strict && prefs.illFormed(session.pending),
                                  emoji: Emoji.choices(session.word)))   // every language's names: a word in any of them
        }
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
        textDocumentProxy.insertText(Stages.convert(text, source, target, tones: prefs.tones))
        refresh()
    }

    // MARK: settings

    private func showSettings(_ on: Bool) {
        session.flush()
        if on { panel.refresh() }
        panel.isHidden = !on
        refresh()
    }

    private func prefsChanged() {
        session.flush()                              // the shown tail belongs to the old renderer
        session.render = prefs.renderer()
        session.mode = prefs.tailMode
        keys.layoutCode = prefs.layout
        refresh()
    }
}
