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
    private var reverseMap: [String: String] = [:]   // glyph -> label, for backspace-to-recompose
    private var reverseMaxLen = 0                    // longest glyph, in UTF-16 units

    private func currentStreamer() -> Streaming? {
        let c = Config.shared
        let key = c.target + (c.looseInput ? "+li" : "") + (c.enDict ? "+dict" : "")
        if streamer == nil || key != streamerKey, let eng = Self.engine {
            streamer = makeStreamer(target: c.target, loose: c.looseInput, dict: c.enDict, eng: eng)
            streamerKey = key
            reverseMap = [:]
            reverseMaxLen = 0
            if let m = eng.maps[c.target] {              // universal modes only
                for (lab, g) in m {
                    if let ex = reverseMap[g], ex.count < lab.count || (ex.count == lab.count && ex < lab) {
                        continue                          // shortest label wins (HU a/ä, ZH ṛ licences)
                    }
                    reverseMap[g] = lab
                    reverseMaxLen = max(reverseMaxLen, (g as NSString).length)
                }
            }
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
            if Config.shared.recompose, recompose(client, into: s) { return true }
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

    /// Backspace with nothing held: reopen the glyph before the caret as editable notation.
    /// Reads the client text (not all apps allow it — then we fall through to a plain delete).
    private func recompose(_ client: IMKTextInput, into s: Streaming) -> Bool {
        guard reverseMaxLen > 0 else { return false }
        let sel = client.selectedRange()
        guard sel.length == 0, sel.location != NSNotFound, sel.location > 0 else { return false }
        let want = min(reverseMaxLen, sel.location)
        guard let ctx = client.attributedSubstring(from: NSRange(location: sel.location - want, length: want))?.string,
              !ctx.isEmpty else { return false }
        let ns = ctx as NSString
        // longest glyph suffix known to the reverse map wins (covers geminates like șș)
        for take in stride(from: min(ns.length, reverseMaxLen), through: 1, by: -1) {
            let g = ns.substring(from: ns.length - take)
            if let lab = reverseMap[g] {
                s.seed(lab)
                let attrs: [NSAttributedString.Key: Any] = [.underlineStyle: NSUnderlineStyle.single.rawValue]
                client.setMarkedText(NSAttributedString(string: s.raw, attributes: attrs),
                                     selectionRange: NSRange(location: (s.raw as NSString).length, length: 0),
                                     replacementRange: NSRange(location: sel.location - take, length: take))
                return true
            }
        }
        return false
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
        // Five modes: the universal views + one per language (a language mode IS that language's
        // view; the flavoured native variants are not separate modes).
        let names: [(String, String)] = [
            ("native", "Native"), ("ipa", "IPA"),
            ("hu", "Hungarian"), ("zh", "Mandarin (Pinyin)"), ("en", "English"),
        ]
        for (key, title) in names {
            let item = NSMenuItem(title: title, action: #selector(selectTarget(_:)), keyEquivalent: "")
            item.representedObject = key
            item.state = Config.shared.target == key ? .on : .off
            m.addItem(item)
        }
        m.addItem(.separator())
        let loose = NSMenuItem(title: "Loose input (hu · zh · en)", action: #selector(toggleLoose(_:)), keyEquivalent: "")
        loose.state = Config.shared.looseInput ? .on : .off
        m.addItem(loose)
        let dict = NSMenuItem(title: "Dictionary spelling (en)", action: #selector(toggleDict(_:)), keyEquivalent: "")
        dict.state = Config.shared.enDict ? .on : .off
        m.addItem(dict)
        let rec = NSMenuItem(title: "Backspace edits notation (native · ipa)", action: #selector(toggleRecompose(_:)), keyEquivalent: "")
        rec.state = Config.shared.recompose ? .on : .off
        m.addItem(rec)
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

    @objc func toggleDict(_ sender: Any!) {
        Config.shared.enDict.toggle()
    }

    @objc func toggleRecompose(_ sender: Any!) {
        Config.shared.recompose.toggle()
    }
}

private extension Streaming {
    func rawAndReset() -> String {
        let r = raw
        while !raw.isEmpty { dropLastRaw() }
        return r
    }
}
