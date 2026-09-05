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

/// Universal targets (uni / ipa): pure token stream, hold <= 3 keys — except with tone signs on
/// (uni, opt-in), where the syllable is held until its tone digit (or a boundary) lands, because
/// the sign marks an earlier vowel (same hold as the zh spelling).
final class MapStreamer: Streaming {
    private let map: [String: String]
    private let labels: [String]
    private let toneSup: [String: String]
    private let toneSigns: [String: String]
    private let useCaps: Bool                    // IPA has no capitals
    private let useSup: Bool                     // superscript tone digits are IPA-only;
    private let useTones: Bool                   //   native: plain digit, or tone sign when on
    private var pending = ""
    private var carriedCap = false               // a capital no caseless glyph (') could take,
                                                 //   carried to the next glyph across drain calls
    init(target: String, eng: Engine, tones: Bool = false) {
        map = eng.maps[target] ?? [:]
        labels = eng.labels(for: target)
        toneSup = eng.toneSup
        toneSigns = eng.toneSigns
        useCaps = target != "ipa"
        useSup = target == "ipa"
        useTones = tones && target != "ipa"
    }

    var raw: String { pending }
    func dropLastRaw() { if !pending.isEmpty { pending.removeLast() } }
    func seed(_ notation: String) { pending += notation }

    func feed(_ c: Character) -> String {
        let s = String(c)
        if c == " " {
            let out = drain(final: true) + s
            carriedCap = false                            // word boundary
            return out
        }
        if s == "0" || toneSup[s] != nil {
            if useSup { return drain(final: true) + (toneSup[s] ?? s) }   // no superscript 0: literal
            if useTones { return drainToned(digit: s) }
            return drain(final: true) + s
        }
        pending.append(c)
        return useTones ? "" : drain(final: false)   // tone signs: hold the whole open syllable
    }

    func flush() -> String { let out = drain(final: true); carriedCap = false; return out }

    /// Render the held segment with its tone sign applied (first vowel of the last vowel group).
    private func drainToned(digit: String) -> String {
        let (toks, g) = parts(pending)
        pending = ""
        var glyphs = g
        let trail = applyToneSign(&glyphs, toks: toks, digit: digit, signs: toneSigns)
        return glyphs.joined() + trail
    }

    private func parts(_ seg: String) -> (toks: [String], glyphs: [String]) {
        let (toks, caps) = tokenizeCased(seg, labels: labels)
        // an ALL-CAPS segment uppercases whole glyphs (TW -> TT, not Tt)
        let shout = seg == seg.uppercased() && seg != seg.lowercased()
        var pending = false                              // a caseless glyph passes the capital along
        let glyphs = zip(toks, caps).map { t, c -> String in
            let g = map[t] ?? t
            guard useCaps, c || pending else { return g }
            let cap = shout ? g.uppercased() : capFirst(g)
            pending = (cap == g)
            return cap
        }
        return (toks, glyphs)
    }

    private func drain(final: Bool) -> String {
        var out = ""
        while !pending.isEmpty {
            let low = pending.lowercased()
            if !final, labels.contains(where: { $0 != low && $0.hasPrefix(low) }) {
                break                                     // could still grow into a longer label — hold
            }
            var matched = false
            let shout = pending == pending.uppercased() && pending != low
            for L in labels where low.hasPrefix(L) {
                let g = map[L] ?? L
                if useCaps, (pending.first?.isUppercase ?? false) || carriedCap {
                    let c = shout ? g.uppercased() : capFirst(g)
                    carriedCap = (c == g)                 // caseless glyph: pass the capital along
                    out += c
                } else {
                    out += g
                }
                pending.removeFirst(L.count)
                matched = true
                break
            }
            if !matched { out.append(pending.removeFirst()); carriedCap = false }
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
    private var buf = ""

    init(lang: String, loose: Bool, eng: Engine) {
        self.lang = lang
        self.eng = eng
        (orth, orthKeys) = eng.orthLabels(for: lang, loose: loose)
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
        let out = buf.isEmpty ? "" : dec(buf)
        buf = ""
        return out
    }
}

func makeStreamer(target: String, loose: Bool, tones: Bool = false, eng: Engine) -> Streaming {
    if eng.maps[target] != nil { return MapStreamer(target: target, eng: eng, tones: tones) }
    return WordStreamer(lang: target, loose: loose, eng: eng)
}
