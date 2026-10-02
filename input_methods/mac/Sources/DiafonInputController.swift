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
    private var lastShiftTap: TimeInterval = -1000   // when the last bare Shift tap landed
    private let anyRange = NSRange(location: NSNotFound, length: NSNotFound)
    private var prefs: Prefs { Prefs.shared }

    private var candidateList: [String] = []
    private var syllable: String? = nil      // Mandarin: a completed syllable (transport + tone) awaiting its character
    private var mandarin: Bool { prefs.enabled && output == "stage:zh" && Lexicon.get("zh") != nil }
    private var output: String { prefs.output }
    private func render() -> (String) -> String { prefs.renderer(output) }

    /// The pending segment in every spelling, distinct, the current output first:
    /// Universal, each language's spelling, then as typed.
    private func spellings(_ tail: String) -> [String] {
        var outs = ["script"] + Prefs.languages.map { "stage:\($0.0)" } + ["transport"]
        if let i = outs.firstIndex(of: output) { outs.remove(at: i); outs.insert(output, at: 0) }
        var seen = Set<String>(), list: [String] = []
        for o in outs {
            let t = prefs.renderer(o)(tail)
            if seen.insert(t).inserted { list.append(t) }
        }
        return list
    }

    /// Where the caret is on screen, if the app says.
    private func caretRect(_ client: IMKTextInput) -> NSRect? {
        var rect = NSRect.zero
        _ = client.attributes(forCharacterIndex: 0, lineHeightRectangle: &rect)
        return rect.width > 0 || rect.height > 0 ? rect : nil
    }

    // MARK: the candidate window

    public override func candidates(_ sender: Any!) -> [Any]! { candidateList }

    public override func candidateSelected(_ candidateString: NSAttributedString!) {
        guard let client = self.client() else { return }
        if syllable != nil { takeCandidate(client, candidateString.string); return }
        insert(client, candidateString.string)
        pending = ""
        mark(client)
        hidePanel()
    }

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
                    let quickTap = event.timestamp - lastShiftTap < Prefs.tapWindow
                    lastShiftTap = event.timestamp
                    if quickTap { prefs.cycleMode() } else { prefs.toggleOff() }
                    Hud.shared.show(prefs.modeLabel, near: caretRect(client))
                }
            } else { shiftPending = false }
            return false
        }
        guard event.type == .keyDown else { return false }
        shiftPending = false

        // ⇧Space, in every mode: the language chooser
        let mods = event.modifierFlags.intersection([.command, .control, .option, .shift])
        if mods == [.shift], event.keyCode == 49 { flush(client); LanguageChooser.shared.show(); return true }
        if !prefs.enabled { return false }                     // a plain keyboard: touch nothing

        // the candidate window is up: it takes arrows, Return and the digits; Escape closes it
        if (candidatePanelIfAny?.isVisible() ?? false) {
            switch event.keyCode {
            case 53: hidePanel(); return true
            case 125, 126, 36, 76, 116, 121: candidatePanelIfAny?.interpretKeyEvents([event]); return true
            case 48:                                           // Tab steps down the list
                if let down = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: [], timestamp: 0, windowNumber: 0,
                                               context: nil, characters: "", charactersIgnoringModifiers: "", isARepeat: false, keyCode: 125) {
                    candidatePanelIfAny?.interpretKeyEvents([down])
                }
                return true
            default:
                hidePanel()                                        // any other key, digits included (they are tones): typing goes on
            }
        }
        if mandarin { if handleMandarin(event, client) { return true } }
        if !pending.isEmpty, event.keyCode == 48 || event.keyCode == 125 {   // Tab, down: open the chooser
            candidateList = spellings(pending)
            let panel = candidatePanelMake()                       // the default selection keys stay set: handle()
            //   takes every digit before the panel sees it (digits are tones); an empty key list crashes the
            //   client-side candidate UI (TextInputUIMacHelper) in Electron apps such as Teams
            panel.update()
            panel.show(kIMKLocateCandidatesBelowHint)
            return true
        }

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

    // MARK: Mandarin: the syllable, then its character

    /// Mandarin mode: letters build a syllable, shown as pinyin; a tone digit
    /// (or a space, for the neutral tone) completes it and the candidate
    /// window offers its characters, most frequent first, with the pinyin
    /// last. Return or space takes the selection; the next letter takes the
    /// first candidate and starts the next syllable; Escape keeps the pinyin.
    private func handleMandarin(_ event: NSEvent, _ client: IMKTextInput) -> Bool {
        let chars = event.characters ?? ""
        if let syl = syllable {
            switch event.keyCode {
            case 36, 76, 49:                                      // return, enter, space: take the selection
                takeCandidate(client, selectedCandidate() ?? firstChoice(syl))
                return true
            case 53:                                              // escape: the pinyin stands
                takeCandidate(client, Stages.render(syl, SpecData.stages["zh"]!, tones: prefs.tones))
                return true
            case 125, 126, 116, 121, 48:                          // arrows, page, tab: move in the window
                if (candidatePanelIfAny?.isVisible() ?? false) { candidatePanelIfAny?.interpretKeyEvents([event]); return true }
                return false
            case 51:                                              // backspace reopens the syllable
                hidePanel(); pending = syl; syllable = nil; pending.removeLast(); mark(client)
                return true
            default:
                if let ch = chars.first, ch.isLetter {            // the next syllable starts: the first choice goes in
                    takeCandidate(client, selectedCandidate() ?? firstChoice(syl))
                    type(client, ch)
                    return true
                }
                return false
            }
        }
        // a syllable in progress
        if event.keyCode == 51 { if !pending.isEmpty { pending.removeLast(); mark(client); return true }; return false }
        guard let ch = chars.first else { return false }
        if ch.isLetter { pending.append(ch); mark(client); return true }
        if ch.isNumber || ch == " " {
            if pending.isEmpty { return false }
            if ch.isNumber { pending.append(ch) }
            completeSyllable(client)
            return true
        }
        if !pending.isEmpty { completeSyllable(client); takeCandidate(client, firstChoice(syllable!)) }
        return false                                              // punctuation goes to the app
    }

    private func completeSyllable(_ client: IMKTextInput) {
        let syl = pending
        syllable = syl
        pending = ""
        let zh = SpecData.stages["zh"]!
        let pinyin = Stages.render(syl, zh, tones: prefs.tones)
        var list = Lexicon.get("zh")?.choose(syl) ?? []
        if list.isEmpty && syl.last!.isNumber { list = Lexicon.get("zh")?.choose(String(syl.dropLast())) ?? [] }
        list.append(pinyin)
        candidateList = list
        client.setMarkedText(NSAttributedString(string: list[0], attributes: [.underlineStyle: NSUnderlineStyle.thick.rawValue]),
                             selectionRange: NSRange(location: (list[0] as NSString).length, length: 0), replacementRange: anyRange)
        let panel = candidatePanelMake()
        panel.update()
        panel.show(kIMKLocateCandidatesBelowHint)
    }

    /// Hide the candidate window only if it is up: hiding one that was never
    /// shown still reaches the client app's candidate UI.
    private func hidePanel() { if let p = candidatePanelIfAny, p.isVisible() { p.hide() } }

    private func firstChoice(_ syl: String) -> String { candidateList.first ?? Stages.render(syl, SpecData.stages["zh"]!, tones: prefs.tones) }

    private func selectedCandidate() -> String? {
        guard let p = candidatePanelIfAny, p.isVisible(), let a = p.selectedCandidateString() else { return nil }
        return a.string
    }

    private func takeCandidate(_ client: IMKTextInput, _ text: String) {
        hidePanel()
        syllable = nil
        insert(client, text)
        mark(client)
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
        let shown = pending.isEmpty ? "" : (mandarin ? Stages.render(pending, SpecData.stages["zh"]!, tones: prefs.tones) : render()(pending))
        let attrs: [NSAttributedString.Key: Any] = [.underlineStyle: NSUnderlineStyle.single.rawValue]
        client.setMarkedText(NSAttributedString(string: shown, attributes: attrs),
                             selectionRange: NSRange(location: (shown as NSString).length, length: 0),
                             replacementRange: anyRange)
    }

    /// Make the composing tail final as it stands.
    private func flush(_ client: IMKTextInput) {
        if let syl = syllable { takeCandidate(client, firstChoice(syl)) }
        guard !pending.isEmpty else { return }
        insert(client, render()(pending))
        pending = ""
        mark(client)
    }

    public override func commitComposition(_ sender: Any!) {
        if let client = sender as? IMKTextInput { flush(client) }
    }

    public override func deactivateServer(_ sender: Any!) {
        hidePanel()
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
        let other = NSMenuItem(title: "Other language…", action: #selector(openChooser(_:)), keyEquivalent: " ")
        other.keyEquivalentModifierMask = [.shift]            // shown beside the item; handled in handle()
        m.addItem(other)
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
        client.insertText(Stages.convert(text, source, target, tones: p.tones), replacementRange: range)
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

    @objc func openSetup(_ sender: Any!) { SetupWindow.shared.show() }

    @objc func openChooser(_ sender: Any!) { LanguageChooser.shared.show() }
}
