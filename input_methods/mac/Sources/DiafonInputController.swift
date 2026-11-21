// The input controller: keystrokes in, converted text out, by the streaming
// rule. The only state is `pending`, the typed tail whose reading can still
// change; it shows as underlined marked text in the app. Everything before it
// is inserted as final text the moment the keystroke stream can no longer
// change it.
import Cocoa
import InputMethodKit

@objc(DiafonInputController)
public class DiafonInputController: IMKInputController {
    private var pending = ""                 // the typed tail still composing, as typed (the profile's keys)
    private var profile: ProfileData { prefs.profileData }
    private let anyRange = NSRange(location: NSNotFound, length: NSNotFound)
    private var prefs: Prefs { Prefs.shared }

    private var output: String { prefs.output }
    private func render() -> (String) -> String { prefs.renderer(output) }

    /// Where the caret is on screen, if the app says.
    private func caretRect(_ client: IMKTextInput) -> NSRect? {
        var rect = NSRect.zero
        _ = client.attributes(forCharacterIndex: 0, lineHeightRectangle: &rect)
        return rect.width > 0 || rect.height > 0 ? rect : nil
    }

    public override func activateServer(_ sender: Any!) {
        pending = ""
        if let client = sender as? IMKTextInput { applyLayout(client) }
    }

    /// The base layout under Diafon (MacPrefs), set on the client when it differs from the last one set.
    private var appliedLayout = ""
    private func applyLayout(_ client: IMKTextInput) {
        let id = prefs.keyLayoutID
        client.overrideKeyboard(withKeyboardNamed: id)
        appliedLayout = id
    }

    public override func recognizedEvents(_ sender: Any!) -> Int {
        Int(NSEvent.EventTypeMask.keyDown.rawValue)
    }

    public override func handle(_ event: NSEvent!, client sender: Any!) -> Bool {
        guard let event, let client = sender as? IMKTextInput else { return false }

        guard event.type == .keyDown else { return false }
        if appliedLayout != prefs.keyLayoutID { applyLayout(client) }    // changed in Setup since this field was entered
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
        let (committed, tail) = Profiles.stream(pending + String(ch), profile, renderer: render(), wordwise: output.hasPrefix("stage:"))
        if !committed.isEmpty { insert(client, committed) }
        pending = tail
        mark(client)
    }

    /// Final text replaces whatever is marked; the mark is redrawn after.
    private func insert(_ client: IMKTextInput, _ text: String) {
        client.insertText(text, replacementRange: anyRange)
    }

    private func mark(_ client: IMKTextInput) {
        let shown = pending.isEmpty ? "" : prefs.renderer(output, letters: true)(pending)
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
        // hand. So: flat and short. The modes, then the quick list of languages
        // (the chooser window has them all), the current choice ticked.
        let m = NSMenu()
        m.autoenablesItems = false
        let p = prefs
        let off = NSMenuItem(title: "Passthrough (conversion off)", action: #selector(selectPassthrough(_:)), keyEquivalent: "")
        off.state = p.enabled ? .off : .on
        m.addItem(off)
        let uni = NSMenuItem(title: "Universal", action: #selector(selectUniversal(_:)), keyEquivalent: "")
        uni.state = (p.enabled && p.universal) ? .on : .off
        m.addItem(uni)
        m.addItem(.separator())
        var listed = p.quickLanguages                          // the quick list, and the language in use if it is off the list
        if !p.universal, !listed.contains(p.language) { listed.append(p.language) }
        for code in listed {
            guard let i = Prefs.languages.firstIndex(where: { $0.0 == code }) else { continue }
            let native = Locale(identifier: code).localizedString(forLanguageCode: code) ?? Prefs.languages[i].1
            let item = NSMenuItem(title: "\(native) (\(code))", action: #selector(selectLanguage(_:)), keyEquivalent: "")
            item.tag = i + 1                // only the tag survives the trip to the system process
            item.state = (p.enabled && !p.universal && p.language == code) ? .on : .off
            m.addItem(item)
        }
        let other = NSMenuItem(title: "Other language…", action: #selector(openChooser(_:)), keyEquivalent: "")
        m.addItem(other)
        m.addItem(.separator())
        // the input profile: what the keys mean (tags from 1000: only the tag survives the trip)
        for (i, pr) in Profiles.all.enumerated() {
            let item = NSMenuItem(title: "Typing: \(pr.name)", action: #selector(selectProfile(_:)), keyEquivalent: "")
            item.tag = 1000 + i
            item.state = p.profile == pr.id ? .on : .off
            m.addItem(item)
        }
        m.addItem(.separator())
        // the selection in the app, converted in place: from the source detected, to the mode in use; or chosen
        let conv = NSMenuItem(title: "Convert selection to \(p.enabled ? p.label() : "Universal")", action: #selector(convertSelection(_:)), keyEquivalent: "")
        m.addItem(conv)
        m.addItem(NSMenuItem(title: "Convert selection…", action: #selector(convertSelectionChoosing(_:)), keyEquivalent: ""))
        m.addItem(.separator())
        m.addItem(NSMenuItem(title: "Setup…", action: #selector(openSetup(_:)), keyEquivalent: ""))
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
        let source = Stages.sourceFor(text, target: target, prefer: p.preferredSources)
        client.insertText(Stages.convert(text, source, target, tones: p.tones, join: p.join), replacementRange: range)
    }

    @objc func convertSelectionChoosing(_ sender: Any!) {
        guard let (client, range, text) = selection() else { return }
        if let result = ConvertWindow.run(text) { client.insertText(result, replacementRange: range) }
    }

    private func item(_ sender: Any!) -> NSMenuItem? {
        (sender as? NSMenuItem) ?? ((sender as? [String: Any])?["IMKCommandMenuItem"] as? NSMenuItem)
    }

    @objc func selectPassthrough(_ sender: Any!) { prefs.enabled = false }

    @objc func selectUniversal(_ sender: Any!) { prefs.output = "script"; prefs.enabled = true }

    @objc func selectLanguage(_ sender: Any!) {
        guard let t = item(sender)?.tag, t >= 1, t <= Prefs.languages.count else { return }
        prefs.language = Prefs.languages[t - 1].0
        prefs.enabled = true
    }

    @objc func selectProfile(_ sender: Any!) {
        guard let t = item(sender)?.tag, t >= 1000, t - 1000 < Profiles.all.count else { return }
        if let client = self.client() { flush(client) }          // the tail belongs to the old profile
        prefs.profile = Profiles.all[t - 1000].id
        if !prefs.enabled { prefs.enabled = true }                // picking a typing means typing with it
    }

    @objc func openSetup(_ sender: Any!) { SetupWindow.shared.show() }

    @objc func openChooser(_ sender: Any!) { LanguageChooser.shared.show() }
}
