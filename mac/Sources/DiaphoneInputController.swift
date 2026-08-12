// The input controller: seamless streaming conversion (docs/mac-input.md).
// Keystrokes feed the Streamer; each resolved glyph is inserted immediately (insertText), and the
// undecidable tail shows as underlined marked text in place — no manual commit, ever.
import Cocoa
import InputMethodKit

@objc(DiaphoneInputController)
public class DiaphoneInputController: IMKInputController {

    private static let engine: Engine? = {
        guard let url = Bundle.main.url(forResource: "engine", withExtension: "json") else { return nil }
        return try? Engine.load(url: url)
    }()

    private var streamer: Streaming?
    private var streamerKey = ""

    private func currentStreamer() -> Streaming? {
        let key = Config.shared.target + (Config.shared.looseInput ? "+li" : "")
        if streamer == nil || key != streamerKey, let eng = Self.engine {
            streamer = makeStreamer(target: Config.shared.target, loose: Config.shared.looseInput, eng: eng)
            streamerKey = key
        }
        return streamer
    }

    private let anyRange = NSRange(location: NSNotFound, length: NSNotFound)

    // MARK: keystroke handling

    public override func recognizedEvents(_ sender: Any!) -> Int {
        Int(NSEvent.EventTypeMask.keyDown.rawValue)
    }

    public override func handle(_ event: NSEvent!, client sender: Any!) -> Bool {
        guard let event, event.type == .keyDown,
              let client = sender as? IMKTextInput,
              let s = currentStreamer() else { return false }

        // modified keys (shortcuts): flush what we hold, let the app have the event
        if !event.modifierFlags.intersection([.command, .control, .option]).isEmpty {
            commitAll(client)
            return false
        }
        switch event.keyCode {
        case 51:                                          // backspace: edit the held tail first
            if !s.raw.isEmpty {
                s.dropLastRaw()
                mark(client)
                return true
            }
            return false
        case 53:                                          // escape: flush the tail as raw notation
            if !s.raw.isEmpty {
                client.insertText(s.rawAndReset(), replacementRange: anyRange)
                return true
            }
            return false
        case 36, 76, 48:                                  // return / enter / tab: flush, pass key through
            commitAll(client)
            return false
        default:
            break
        }
        guard let chars = event.characters, !chars.isEmpty else { return false }
        var committed = ""
        for c in chars {
            if c.isLetter || c.isNumber || c == " " {
                committed += s.feed(c)
            } else {                                      // punctuation etc.: flush + pass through
                committed += s.flush() + String(c)
            }
        }
        if !committed.isEmpty { client.insertText(committed, replacementRange: anyRange) }
        mark(client)
        return true
    }

    private func mark(_ client: IMKTextInput) {
        let raw = streamer?.raw ?? ""
        let attrs: [NSAttributedString.Key: Any] = [.underlineStyle: NSUnderlineStyle.single.rawValue]
        client.setMarkedText(NSAttributedString(string: raw, attributes: attrs),
                             selectionRange: NSRange(location: (raw as NSString).length, length: 0),
                             replacementRange: anyRange)
    }

    private func commitAll(_ client: IMKTextInput) {
        if let s = streamer, !s.raw.isEmpty {
            client.insertText(s.flush(), replacementRange: anyRange)
            mark(client)
        }
    }

    public override func commitComposition(_ sender: Any!) {
        if let client = sender as? IMKTextInput { commitAll(client) }
    }

    public override func deactivateServer(_ sender: Any!) {
        if let client = sender as? IMKTextInput { commitAll(client) }
    }

    // MARK: the input-source menu (target + loose input)

    public override func menu() -> NSMenu! {
        let m = NSMenu()
        let names: [(String, String)] = [
            ("native", "Native"), ("native-hu", "Native · HU"), ("native-zh", "Native · ZH"),
            ("ipa", "IPA"), ("hu", "Hungarian"), ("zh", "Mandarin (Pinyin)"), ("en", "English"),
        ]
        for (key, title) in names {
            let item = NSMenuItem(title: title, action: #selector(selectTarget(_:)), keyEquivalent: "")
            item.representedObject = key
            item.state = Config.shared.target == key ? .on : .off
            m.addItem(item)
        }
        m.addItem(.separator())
        let loose = NSMenuItem(title: "Loose input", action: #selector(toggleLoose(_:)), keyEquivalent: "")
        loose.state = Config.shared.looseInput ? .on : .off
        m.addItem(loose)
        return m
    }

    @objc func selectTarget(_ sender: Any!) {
        if let key = ((sender as? NSMenuItem) ?? ((sender as? [String: Any])?["IMKCommandMenuItem"] as? NSMenuItem))?
            .representedObject as? String {
            Config.shared.target = key
        }
    }

    @objc func toggleLoose(_ sender: Any!) {
        Config.shared.looseInput.toggle()
    }
}

private extension Streaming {
    func rawAndReset() -> String {
        let r = raw
        while !raw.isEmpty { dropLastRaw() }
        return r
    }
}
