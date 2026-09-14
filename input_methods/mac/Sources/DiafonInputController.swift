// The input controller: keystrokes in, converted text out, by the streaming
// rule. The only state is `pending`, the typed tail whose reading can still
// change; it shows as underlined marked text in the app. Everything before it
// is inserted as final text the moment the keystroke stream can no longer
// change it.
import Cocoa
import InputMethodKit

@objc(DiafonInputController)
public class DiafonInputController: IMKInputController {
    private var pending = ""                 // the typed tail still composing
    private var shiftPending = false
    private let anyRange = NSRange(location: NSNotFound, length: NSNotFound)
    private var prefs: Prefs { Prefs.shared }

    private var output: String { prefs.output }
    private func render() -> (String) -> String { prefs.renderer(output) }

    public override func activateServer(_ sender: Any!) {
        pending = ""
    }

    public override func recognizedEvents(_ sender: Any!) -> Int {
        Int(NSEvent.EventTypeMask.keyDown.union(.flagsChanged).rawValue)
    }

    public override func handle(_ event: NSEvent!, client sender: Any!) -> Bool {
        guard let event, let client = sender as? IMKTextInput else { return false }

        // a bare Shift tap (down, then up, with no key between) flips conversion on and off
        if event.type == .flagsChanged {
            if prefs.shiftToggle, event.keyCode == 56 || event.keyCode == 60 {
                if event.modifierFlags.contains(.shift) { shiftPending = true }
                else if shiftPending {
                    shiftPending = false
                    flush(client)
                    prefs.enabled.toggle()
                }
            } else { shiftPending = false }
            return false
        }
        guard event.type == .keyDown else { return false }
        shiftPending = false
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
        let (committed, tail) = Engine.stream(pending + String(ch), renderer: render())
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
        let m = NSMenu()
        let p = prefs
        let head = NSMenuItem(title: pending.isEmpty ? "Diafon · \(p.label(output))" : "\(pending)  →  \(render()(pending))",
                              action: nil, keyEquivalent: "")
        head.isEnabled = false
        m.addItem(head)
        let on = NSMenuItem(title: "Conversion on", action: #selector(toggleEnabled(_:)), keyEquivalent: "")
        on.state = p.enabled ? .on : .off
        m.addItem(on)
        m.addItem(.separator())
        let sub = NSMenuItem(title: "Write out as", action: nil, keyEquivalent: "")
        sub.isEnabled = false
        m.addItem(sub)
        for (value, label) in Prefs.outputs {
            let item = NSMenuItem(title: "   " + label, action: #selector(selectOutput(_:)), keyEquivalent: "")
            item.representedObject = value
            item.state = p.output == value ? .on : .off
            m.addItem(item)
        }
        m.addItem(.separator())
        m.addItem(NSMenuItem(title: "Convert selection: Services menu, or ⇧⌘D", action: nil, keyEquivalent: ""))
        m.items.last?.isEnabled = false
        m.addItem(NSMenuItem(title: "Setup…", action: #selector(openSetup(_:)), keyEquivalent: ""))
        return m
    }

    private func item(_ sender: Any!) -> NSMenuItem? {
        (sender as? NSMenuItem) ?? ((sender as? [String: Any])?["IMKCommandMenuItem"] as? NSMenuItem)
    }

    @objc func selectOutput(_ sender: Any!) {
        if let v = item(sender)?.representedObject as? String { prefs.output = v }
    }

    @objc func toggleEnabled(_ sender: Any!) { prefs.enabled.toggle() }

    @objc func openSetup(_ sender: Any!) { SetupWindow.shared.show() }
}
