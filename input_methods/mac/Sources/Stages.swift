// Spelling stages, ported from scripts/stages.py: the point stream written in
// a language's current orthography, or as composed marks. Render-only; forms
// the stage does not spell fall back to the script glyph.
import Foundation

enum Stages {
    static func spell(_ st: Stage, _ form: String) -> String? {
        let first = form.first!
        let caps = first.isUppercase
        let low = String(first).lowercased() + String(form.dropFirst())
        var sp = st.forms[low]
        var capsp = st.caps[low]                          // a capital spelled on its own (g̓ -> G̦)
        if sp == nil, low.hasSuffix("w"), Engine.cBases.contains(low.first!) {
            let shortForm = String(low.dropLast())
            if let short = st.forms[shortForm] {
                if st.long == "first-letter" { sp = String(short.first!) + short }
                else {
                    sp = short + short
                    if let c = st.caps[shortForm] { capsp = c + short }
                }
            }
        }
        guard let s = sp else { return nil }
        if !caps { return s }
        if let c = capsp { return c }
        let u = Array(s.unicodeScalars)
        var v = String.UnicodeScalarView(); v.append(contentsOf: u.dropFirst())
        return Engine.nfc(String(u[0]).uppercased() + String(v))
    }

    /// A text in the stage's spelling: the lexicon word by word, then the letters.
    static func render(_ text: String, _ st: Stage, strict: Bool = false, tones: Bool = true) -> String {
        guard st.lexicon, let L = Lexicon.get(st.code) else { return renderLetters(text, st, strict: strict, tones: tones) }
        let u = text.unicodeScalars
        var out = "", i = u.startIndex
        for (r, w) in Lexicon.words(text, transport: true) {
            out += renderLetters(String(String.UnicodeScalarView(u[i..<r.lowerBound])), st, strict: strict, tones: tones)
            switch L.writeWord(w) {
            case .none:
                let sp = renderLetters(w, st, strict: strict, tones: tones)
                out += L.writeLoan(w, lettersSpelling: sp) ?? sp
            case .some(.word(let sp)): out += sp
            case .some(.stem(let sp, let rest)): out += sp + renderLetters(rest, st, strict: strict, tones: tones)
            }
            i = r.upperBound
        }
        return out + renderLetters(String(String.UnicodeScalarView(u[i...])), st, strict: strict, tones: tones)
    }

    static func renderLetters(_ text: String, _ st: Stage, strict: Bool = false, tones: Bool = true) -> String {
        var out = ""
        let segs = (try? Engine.segments(text, strict: strict)) ?? []
        for seg in segs {
            guard case .form(let src, let form, let t) = seg else { out += seg.src; continue }
            let sp = spell(st, form) ?? ((try? Engine.glyph(form)) ?? src)
            out += sp + (tones ? t : "")
        }
        return out
    }
}
