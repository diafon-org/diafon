// The input controller: keystrokes in, converted text out, by the streaming
// rule. The only state is `pending`, the typed tail whose reading can still
// change; it shows as underlined marked text in the app. Everything before it
// is inserted as final text the moment the keystroke stream can no longer
// change it.
import Carbon
import Cocoa
import InputMethodKit

@objc(DiafonInputController)
public class DiafonInputController: IMKInputController {
    private var pending = ""                 // the typed tail still composing, as typed
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
            if !pending.isEmpty { pending.removeLast(); mark(client); return true }
            return false
        case 53:                                               // escape: the tail goes in as typed
            if !pending.isEmpty { insert(client, pending); pending = ""; mark(client); return true }
            return false
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
        let (committed, tail) = prefs.stream(pending + String(ch))
        if !committed.isEmpty { insert(client, committed) }
        pending = tail
        mark(client)
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
