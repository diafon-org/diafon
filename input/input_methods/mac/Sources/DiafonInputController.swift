// The input controller: keystrokes in, converted text out, by the streaming
// rule. The state is `pending`, the typed tail whose reading can still
// change. The tail is written into the app as ordinary text and rewritten
// in place when a key changes it (sy: s, then ș over it), so the app has
// every letter the moment it is typed: its autocompletion, search fields and
// spell check see the word as it grows. An app that cannot say what is
// before the caret gets the tail as underlined marked text instead, as does
// everyone with `defaults write org.diafon.inputmethod.Diafon underline -bool true`.
import Carbon
import Cocoa
import InputMethodKit

@objc(DiafonInputController)
public class DiafonInputController: IMKInputController {
    private var pending = ""                 // the typed tail still composing, as typed
    private var shown = ""                   // the tail as it stands in the app's text, before the caret; "" while it is marked text
    private var direct = true                // this tail is written as ordinary text (decided where a tail starts)
    /// Apps that take the tail as marked text: they cannot give back the text before the caret.
    private static var markedOnly: Set<String> = ["com.apple.Terminal", "com.googlecode.iterm2"]
    private let anyRange = NSRange(location: NSNotFound, length: NSNotFound)
    private var prefs: Prefs { Prefs.shared }

    private var output: String { prefs.output }
    private func render() -> (String) -> String { prefs.renderer(output) }

    // MARK: the input modes: each output is an input source of its own (tools/modes.py)

    /// The system tells which mode was picked (the input menu, the Globe key, Control-Space):
    /// org.diafon.inputmethod.Diafon.universal is the script, ….<code> a language's spelling.
    public override func setValue(_ value: Any!, forTag tag: Int, client sender: Any!) {
        guard tag == Int(kTextServiceInputModePropertyTag), let id = value as? String, let out = Keyboards.output(id) else {
            super.setValue(value, forTag: tag, client: sender)
            return
        }
        use(out, sender)
    }

    /// Write in a keyboard's output from here on. The tail typed so far belongs to the
    /// output before, and is made final in it first. A keyboard always converts: the
    /// plain keys are another keyboard.
    private func use(_ out: String, _ sender: Any!) {
        if !prefs.enabled { prefs.enabled = true }
        guard out != prefs.output else { return }
        if let client = sender as? IMKTextInput { flush(client) }
        if out.hasPrefix("stage:") { prefs.language = String(out.dropFirst(6)) } else { prefs.output = out }
    }

    /// A field is entered. The keyboard selected in the system says what is written,
    /// whether or not the system sends the mode with the switch (a keyboard kept per document).
    public override func activateServer(_ sender: Any!) {
        pending = ""
        shown = ""
        if let out = Keyboards.current { use(out, sender) }
        if let client = sender as? IMKTextInput { applyLayout(client) }
    }

    /// The layout under Diafon: plain letters and digits, placed as the person's own keyboard places them.
    private func applyLayout(_ client: IMKTextInput) {
        client.overrideKeyboard(withKeyboardNamed: Keyboards.baseLayout)
    }

    public override func recognizedEvents(_ sender: Any!) -> Int {
        Int(NSEvent.EventTypeMask.keyDown.rawValue)
    }

    public override func handle(_ event: NSEvent!, client sender: Any!) -> Bool {
        guard let event, let client = sender as? IMKTextInput else { return false }

        guard event.type == .keyDown else { return false }
        if !prefs.enabled { return false }                     // a plain keyboard: touch nothing

        // shortcuts and navigation: make the tail final, let the app have the key
        if !event.modifierFlags.intersection([.command, .control, .option]).isEmpty { flush(client); return false }
        switch event.keyCode {
        case 51:                                               // backspace edits the tail first
            if pending.isEmpty { return false }
            if !direct { pending.removeLast(); mark(client); return true }
            // a tail of one key is one plain letter: the app deletes it itself
            guard pending.count > 1, let caret = tailEnd(client) else { pending = ""; shown = ""; return false }
            pending.removeLast()
            rewrite(client, caret, render()(pending))
            return true
        case 53:                                               // escape: the tail goes in as typed
            if pending.isEmpty { return false }
            if !direct { insert(client, pending); pending = ""; mark(client); return true }
            if let caret = tailEnd(client) { rewrite(client, caret, pending) }
            pending = ""; shown = ""
            return true
        case 36, 76, 48, 123, 124, 125, 126:                   // return, enter, tab, arrows
            flush(client); return false
        default: break
        }
        guard let chars = event.characters, !chars.isEmpty else { return false }
        for ch in chars {
            if ch.isLetter || ch.isNumber || ch == " " || ch.isPunctuation || ch.isSymbol { type(client, ch) }
            else { flush(client); return false }
        }
        return true
    }

    /// One character in: the streaming rule decides what is final.
    private func type(_ client: IMKTextInput, _ ch: Character) {
        if pending.isEmpty { direct = writesDirect(client) }
        guard direct else {
            let (committed, tail) = prefs.stream(pending + String(ch))
            if !committed.isEmpty { insert(client, committed) }
            pending = tail
            mark(client)
            return
        }
        var caret = 0
        if !pending.isEmpty {
            if let c = tailEnd(client) { caret = c } else { pending = ""; shown = "" }      // the caret has moved: what was typed is final
        }
        let (committed, tail) = prefs.stream(pending + String(ch))
        pending = tail
        rewrite(client, caret, committed + (tail.isEmpty ? "" : render()(tail)))
        shown = tail.isEmpty ? "" : render()(tail)
    }

    // MARK: the tail as ordinary text

    /// Whether a new tail is written as ordinary text: unless it is turned off, or the app
    /// is known not to give back its text, or it does not say where the caret is.
    private func writesDirect(_ client: IMKTextInput) -> Bool {
        if UserDefaults.standard.bool(forKey: "underline") { return false }
        if let id = client.bundleIdentifier(), Self.markedOnly.contains(id) { return false }
        return client.selectedRange().location != NSNotFound
    }

    /// Where the tail ends, if it still stands right before the caret as it was written; nil if
    /// the caret has moved or the text has changed. An app that gives no text back is remembered.
    private func tailEnd(_ client: IMKTextInput) -> Int? {
        let n = (shown as NSString).length
        let sel = client.selectedRange()
        guard n > 0, sel.location != NSNotFound, sel.length == 0, sel.location >= n else { return nil }
        guard let got = client.attributedSubstring(from: NSRange(location: sel.location - n, length: n))?.string else {
            if let id = client.bundleIdentifier() { Self.markedOnly.insert(id) }
            return nil
        }
        return got == shown ? sel.location : nil
    }

    /// The tail standing before the caret becomes `text`: only what differs is touched, by
    /// whole letters, so a letter that only follows the tail is a plain insertion.
    private func rewrite(_ client: IMKTextInput, _ caret: Int, _ text: String) {
        let keep = zip(shown, text).prefix { $0 == $1 }.count
        let gone = (String(shown.dropFirst(keep)) as NSString).length
        let new = String(text.dropFirst(keep))
        if gone == 0 {
            if !new.isEmpty { client.insertText(new, replacementRange: anyRange) }
        } else {
            client.insertText(new, replacementRange: NSRange(location: caret - gone, length: gone))
        }
        shown = text
    }

    /// Final text replaces whatever is marked; the mark is redrawn after.
    private func insert(_ client: IMKTextInput, _ text: String) {
        client.insertText(text, replacementRange: anyRange)
    }

    private func mark(_ client: IMKTextInput) {
        let shown = pending.isEmpty ? "" : render()(pending)
        let attrs: [NSAttributedString.Key: Any] = [.underlineStyle: NSUnderlineStyle.single.rawValue]
        client.setMarkedText(NSAttributedString(string: shown, attributes: attrs),
                             selectionRange: NSRange(location: (shown as NSString).length, length: 0),
                             replacementRange: anyRange)
    }

    /// Make the composing tail final as it stands.
    private func flush(_ client: IMKTextInput) {
        guard !pending.isEmpty else { return }
        if direct { pending = ""; shown = ""; return }       // it stands in the text already, as it would be made final
        insert(client, render()(pending))
        pending = ""
        mark(client)
    }

    public override func commitComposition(_ sender: Any!) {
        if let client = sender as? IMKTextInput { flush(client) }
    }

    public override func deactivateServer(_ sender: Any!) {
        if let client = sender as? IMKTextInput { flush(client) }
    }

    // MARK: the status menu, under the input source in the menu bar

    public override func menu() -> NSMenu! {
        // Shown by a system process, which sends back only top-level clicks (a
        // submenu's never arrive) and greys every item unless enabling is by
        // hand. So: flat and short, and only the conversions. What is written
        // (Diafon, a language's spelling) is an input mode, picked like any keyboard; where
        // the letters sit follows the Mac's own keyboard layout. Nothing is set here.
        let m = NSMenu()
        m.autoenablesItems = false
        let p = prefs
        // the selection in the app, converted in place: from the source detected, to the mode in use; or chosen
        let conv = NSMenuItem(title: "Convert selection to \(p.enabled ? p.label() : "Diafon")", action: #selector(convertSelection(_:)), keyEquivalent: "")
        m.addItem(conv)
        m.addItem(NSMenuItem(title: "Convert selection…", action: #selector(convertSelectionChoosing(_:)), keyEquivalent: ""))
        return m
    }

    /// The app's selection, through the input-method connection.
    private func selection() -> (IMKTextInput, NSRange, String)? {
        guard let client = self.client() else { return nil }
        let range = client.selectedRange()
        guard range.location != NSNotFound, range.length > 0,
              let text = client.attributedSubstring(from: range)?.string, !text.isEmpty else {
            Hud.shared.show("Select some text first", near: nil)
            return nil
        }
        return (client, range, text)
    }

    @objc func convertSelection(_ sender: Any!) {
        guard let (client, range, text) = selection() else { return }
        let p = prefs
        let target = p.enabled ? p.output : "script"
        let source = Diafon.shared.sourceFor(text, target: target, prefer: p.preferredSources)
        client.insertText(Diafon.shared.convert(text, source, target, tones: p.tones, join: p.join), replacementRange: range)
    }

    @objc func convertSelectionChoosing(_ sender: Any!) {
        guard let (client, range, text) = selection() else { return }
        if let result = ConvertWindow.run(text) { client.insertText(result, replacementRange: range) }
    }

}
