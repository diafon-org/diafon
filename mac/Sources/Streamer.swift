// The incremental committer — port of scripts/stream_poc.py. Each glyph is emitted the moment the
// keystroke stream can no longer change it; `raw` is the held tail (shown as underlined marked text).
// Validated char-by-char against the Python batch renderer by scripts/check_swift.py.
import Foundation

protocol Streaming: AnyObject {
    /// Feed one keystroke; returns text to COMMIT now (usually "" or one glyph).
    func feed(_ c: Character) -> String
    /// Commit whatever is still held (word boundary, focus loss, escape…).
    func flush() -> String
    /// The held raw tail, for marked-text display.
    var raw: String { get }
    /// Backspace inside the held tail.
    func dropLastRaw()
    /// Reopen previously-committed notation into the held tail (backspace-to-recompose).
    func seed(_ notation: String)
}

/// Universal targets (native / ipa / native-hu / native-zh): pure token stream, hold <= 3 keys.
final class MapStreamer: Streaming {
    private let map: [String: String]
    private let labels: [String]
    private let toneSup: [String: String]
    private let useCaps: Bool                    // IPA has no capitals
    private var pending = ""

    init(target: String, eng: Engine) {
        map = eng.maps[target] ?? [:]
        labels = eng.labels(for: target)
        toneSup = eng.toneSup
        useCaps = target != "ipa"
    }

    var raw: String { pending }
    func dropLastRaw() { if !pending.isEmpty { pending.removeLast() } }
    func seed(_ notation: String) { pending += notation }

    func feed(_ c: Character) -> String {
        let s = String(c)
        if c == " " || toneSup[s] != nil {
            return drain(final: true) + (toneSup[s] ?? s)
        }
        pending.append(c)
        return drain(final: false)
    }

    func flush() -> String { drain(final: true) }

    private func drain(final: Bool) -> String {
        var out = ""
        while !pending.isEmpty {
            let low = pending.lowercased()
            if !final, labels.contains(where: { $0 != low && $0.hasPrefix(low) }) {
                break                                     // could still grow into a longer label — hold
            }
            var matched = false
            for L in labels where low.hasPrefix(L) {
                let g = map[L] ?? L
                out += (useCaps && (pending.first?.isUppercase ?? false)) ? capFirst(g) : g
                pending.removeFirst(L.count)
                matched = true
                break
            }
            if !matched { out.append(pending.removeFirst()) }
        }
        return out
    }
}

/// Language targets (hu / en / zh): token stream with the next-token rules; ZH holds one syllable
/// (the tone digit marks an earlier vowel; the hush series spells by the following vowel).
final class WordStreamer: Streaming {
    private let lang: String
    private let eng: Engine
    private let orth: [String: String]
    private let orthKeys: [String]
    private let dict: Bool                       // EN dictionary view: hold the word, look it up at the boundary
    private var buf = ""

    init(lang: String, loose: Bool, dict: Bool = false, eng: Engine) {
        self.lang = lang
        self.eng = eng
        self.dict = dict && lang == "en"
        (orth, orthKeys) = eng.orthLabels(for: lang, loose: loose || (dict && lang == "en"))
    }

    var raw: String { buf }
    func dropLastRaw() { if !buf.isEmpty { buf.removeLast() } }
    func seed(_ notation: String) { buf += notation }

    private func dec(_ s: String) -> String {
        decodeWord(s, orth: orth, orthKeys: orthKeys, lang: lang, eng: eng)
    }

    func feed(_ c: Character) -> String {
        if c == " " { return flush() + " " }
        buf.append(c)
        if dict { return "" }                    // dictionary view: the whole word commits at the boundary
        if lang == "zh" {
            if c.isNumber {                               // tone digit closes the syllable
                let out = dec(buf)
                buf = ""
                return out
            }
            return ""                                     // hold the open syllable
        }
        // hu/en: commit the longest prefix whose decode can no longer change (probe with a vowel).
        let asIs = dec(buf)
        let probed = dec(buf + "a")
        let safe = String(zip(asIs, probed).prefix(while: { $0.0 == $0.1 }).map { $0.0 })
        if !safe.isEmpty {
            let tailAs = String(asIs.dropFirst(safe.count))
            let tailPr = String(probed.dropFirst(safe.count))
            for cut in 0..<buf.count {
                let suffix = String(buf.dropFirst(cut))
                if dec(suffix) == tailAs, dec(suffix + "a") == tailPr {
                    buf = suffix
                    return safe
                }
            }
        }
        return ""
    }

    func flush() -> String {
        var out = ""
        if !buf.isEmpty {
            if dict, let real = enDictLookup(buf, orthKeys: orthKeys, eng: eng) {
                out = (buf.first?.isUppercase ?? false) ? capFirst(real) : real
            }
            else { out = dec(buf) }
        }
        buf = ""
        return out
    }
}

func makeStreamer(target: String, loose: Bool, dict: Bool = false, eng: Engine) -> Streaming {
    if eng.maps[target] != nil { return MapStreamer(target: target, eng: eng) }
    return WordStreamer(lang: target, loose: loose, dict: dict, eng: eng)
}
