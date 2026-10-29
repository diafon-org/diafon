// Reading back, ported from scripts/engine.py (inventory, script_table,
// read) and scripts/stages.py (table, parse, convert, detect): a text in
// any source (transport, the script, a stage's spelling) read back to
// transport form, re-rendered in any other, and the source guessed.
import Foundation

extension Engine {
    /// Every valid single-segment form of the grammar, shorter forms first.
    static func inventory() -> [String] {
        let core = ops.subtracting(["w"]).map { String($0) }.sorted()
        let combos = [""] + core + core.flatMap { a in core.map { a + $0 } }
        var out: [String] = []
        for base in bases.map({ String($0) }).sorted() {
            for o in combos {
                for w in ["", "w"] {
                    let form = base + o + w
                    if (try? glyph(form)) != nil { out.append(form) }
                }
            }
        }
        return out
    }

    private static var scriptTableCache: [String: String]?
    /// {glyph text: form}: the forms in use deciding a glyph two forms share.
    static func scriptTable() -> [String: String] {
        if let t = scriptTableCache { return t }
        let used = Set(SpecData.used)
        let inv = inventory()
        var table: [String: String] = [:]
        for form in inv.filter({ used.contains($0) }) + inv.filter({ !used.contains($0) }) {
            for f in [form, capFirst(form)] {
                if let g = try? glyph(f), table[g] == nil { table[g] = f }
            }
        }
        scriptTableCache = table
        return table
    }

    static func capFirst(_ s: String) -> String {
        guard let first = s.unicodeScalars.first else { return s }
        var v = String.UnicodeScalarView(); v.append(contentsOf: s.unicodeScalars.dropFirst())
        return nfc(String(first).uppercased() + String(v))
    }

    enum Read {
        case raw(String)
        case form(form: String, tones: String, src: String)
    }

    /// Longest match over a table, tone digits attached to the form before them.
    /// a tone sign -> its digit (mid is unmarked: it reads back as none)
    static let toneOf: [Character: Character] = Dictionary(uniqueKeysWithValues:
        SpecData.tones.compactMap { d, s in s.isEmpty ? nil : (Character(s), d) })
    static func read(_ text: String, _ table: [String: String]) -> [Read] {
        let u = Array(nfc(text).unicodeScalars)
        let maxlen = table.keys.map { $0.unicodeScalars.count }.max() ?? 1
        var out: [Read] = []
        var i = 0
        while i < u.count {
            var hit: (String, String)? = nil
            var L = min(maxlen, u.count - i)
            while L > 0 {
                var v = String.UnicodeScalarView(); v.append(contentsOf: u[i..<i + L])
                let s = String(v)
                if let f = table[s] { hit = (s, f); break }
                L -= 1
            }
            guard let (s, f) = hit else { out.append(.raw(String(u[i]))); i += 1; continue }
            i += s.unicodeScalars.count
            var tones = ""
            while i < u.count {                                   // digits, or the script's tone signs (read as their digits)
                if u[i].isASCII, u[i].properties.numericType == .decimal { tones += String(u[i]) }
                else if let d = toneOf[Character(u[i])] { tones += String(d) }
                else { break }
                i += 1
            }
            out.append(.form(form: f, tones: tones, src: s))
        }
        return out
    }
}

extension Stages {
    private static var tables: [String: [String: String]] = [:]

    /// A stage read back: its spellings, long forms, capitals, read aliases, over the script.
    static func table(_ st: Stage, fallback: Bool = true, aliases: Bool = true) -> [String: String] {
        let key = st.code + (fallback ? "+" : "-") + (aliases ? "a" : "")
        if let t = tables[key] { return t }
        var t = fallback ? Engine.scriptTable() : [:]
        var entries: [String] = []
        for form in st.order { entries.append(form); if Engine.cBases.contains(form.first!) { entries.append(form + "w") } }
        for form in entries {
            let capForm = String(form.first!).uppercased() + form.dropFirst()
            if let sp = spell(st, form) {
                let cap = spell(st, capForm)
                t[sp] = form
                if let c = cap { t[c] = capForm }
                let up = sp.uppercased()
                if up != sp && up != cap { t[up] = capForm }
            }
        }
        for sp in (aliases ? st.readOrder : []) {
            let form = st.read[sp]!
            let capForm = String(form.first!).uppercased() + form.dropFirst()
            t[sp] = form
            t[String(sp.first!).uppercased() + sp.dropFirst()] = capForm
            t[sp.uppercased()] = capForm
        }
        tables[key] = t
        return t
    }

    static func sources() -> [String] { ["transport", "script"] + SpecData.stages.keys.sorted().map { "stage:" + $0 } }

    private static func sourceTable(_ source: String) -> [String: String]? {
        if source == "script" { return Engine.scriptTable() }
        if source.hasPrefix("stage:"), let st = SpecData.stages[String(source.dropFirst(6))] { return table(st) }
        return nil
    }

    static func readLetters(_ text: String, _ t: [String: String]) -> String {
        var out = ""
        for tok in Engine.read(text, t) {
            switch tok {
            case .raw(let ch): out += ch
            case .form(let form, let tones, _): out += form + tones
            }
        }
        return out
    }

    /// The word by the stage's own spellings alone, or nil when a letter is left over.
    private static func own(_ word: String, _ st: Stage) -> String? {
        let toks = Engine.read(word, table(st, fallback: false, aliases: false))
        for tok in toks { if case .raw(let ch) = tok, !(ch.unicodeScalars.first.map { $0.isASCII && $0.properties.numericType == .decimal } ?? false) { return nil } }
        var out = ""
        for tok in toks { switch tok { case .raw(let ch): out += ch; case .form(let f, let tn, _): out += f + tn } }
        return out
    }

    /// One word of a stage's text -> (transport, how): letters, lexicon, loan:<code>, fallback.
    static func readWord(_ word: String, _ st: Stage) -> (String, String) {
        let L = st.lexicon ? Lexicon.get(st.code) : nil
        if !st.lexical {
            if let L = L {                        // a host with a lexicon: the loan check (which yields to a spoken stem at least as long), then its own entries
                if let h = L.loan(word) { return (h.0, "loan:" + h.1) }
                if let h = L.readStem(word) { return (h.0 + readLetters(h.1, table(st)), "lexicon") }
            }
            if let t = own(word, st) { return (t, "letters") }
        }
        if let L = L {
            if let h = L.loan(word) { return (h.0, "loan:" + h.1) }
            if let t = L.readWord(word) { return (t, "lexicon") }
        }
        return (readLetters(word, table(st)), "fallback")
    }

    /// A text in a source read back as transport text; a stage word by word.
    static func parse(_ text: String, _ source: String) -> String {
        if source == "transport" { return text }
        if source == "script" { return readLetters(text, Engine.scriptTable()) }
        guard source.hasPrefix("stage:"), let st = SpecData.stages[String(source.dropFirst(6))] else { return text }
        let nfcText = Engine.nfc(text)
        let u = nfcText.unicodeScalars
        var out = "", i = u.startIndex
        for (r, w) in Lexicon.words(nfcText) {
            out += readLetters(String(String.UnicodeScalarView(u[i..<r.lowerBound])), table(st))
            out += readWord(w, st).0
            i = r.upperBound
        }
        return out + readLetters(String(String.UnicodeScalarView(u[i...])), table(st))
    }

    /// A text from one source rendered in another; back into the same spelling, a
    /// word read as a loan goes out as it came (like stays like).
    static func convert(_ text: String, _ source: String, _ target: String, tones: Bool = true) -> String {
        if source == target, source.hasPrefix("stage:"), let st = SpecData.stages[String(source.dropFirst(6))] {
            let nfcText = Engine.nfc(text)
            let u = nfcText.unicodeScalars
            var out = "", i = u.startIndex
            for (r, w) in Lexicon.words(nfcText) {
                out += render(readLetters(String(String.UnicodeScalarView(u[i..<r.lowerBound])), table(st)), st, tones: tones)
                let (t, how) = readWord(w, st)
                out += how.hasPrefix("loan:") ? w : render(t, st, tones: tones)
                i = r.upperBound
            }
            return out + render(readLetters(String(String.UnicodeScalarView(u[i...])), table(st)), st, tones: tones)
        }
        let t = parse(text, source)
        if target == "transport" { return t }
        if target.hasPrefix("stage:"), let st = SpecData.stages[String(target.dropFirst(6))] { return render(t, st, strict: false, tones: tones) }
        return Engine.lenient(t, tones: tones)
    }

    private static func letters(_ s: String) -> Int {
        s.unicodeScalars.filter { u in
            switch u.properties.generalCategory {
            case .uppercaseLetter, .lowercaseLetter, .titlecaseLetter, .modifierLetter, .otherLetter,
                 .nonspacingMark, .spacingMark, .enclosingMark: return true
            default: return false
            }
        }.count
    }

    /// Which source a text is in: [(source, coverage)] best first.
    static func detect(_ text: String, prefer: [String] = []) -> [(String, Double)] {
        let nfcText = Engine.nfc(text)
        let total = max(letters(nfcText), 1)
        let markChars = Set(SpecData.marks.values.flatMap { [$0.below, $0.above] }.compactMap { $0 }.flatMap { $0.unicodeScalars })
        let hasMarks = nfcText.unicodeScalars.contains { markChars.contains($0) }
        let srcs = sources()
        var rank: [String: Int] = [:]
        for (i, s) in srcs.enumerated() { rank[s] = i }
        var typed = false      // the input form read in full, with operators in it: the system's own
        var lexicalFull: [String: Int] = [:]
        let scored: [(String, Double)] = srcs.map { src in
            var covered = 0
            if src == "transport" {
                var ops = false
                for seg in (try? Engine.segments(text, strict: false)) ?? [] {
                    if case .form(let s, let f, _) = seg { covered += letters(s); if f.count > 1 { ops = true } }
                }
                typed = covered == total && ops
            } else if src == "script" {
                for tok in Engine.read(text, Engine.scriptTable()) { if case .form(_, _, let s) = tok { covered += letters(s) } }
            } else {
                let st = SpecData.stages[String(src.dropFirst(6))]!
                var hows: [(String, String)] = []
                for (_, w) in Lexicon.words(nfcText) {
                    let (_, how) = readWord(w, st)
                    hows.append((how, w))
                    if how == "letters" || how == "lexicon" || how.hasPrefix("loan:") { covered += letters(w) }
                }
                if !hows.isEmpty, hows.allSatisfy({ $0.0 == "lexicon" }), hows.contains(where: { $0.1.count >= 3 }) {
                    if let L = Lexicon.get(st.code), L.kind == "syllable" {
                        if hows.contains(where: { $0.1.last!.isNumber }) { lexicalFull[src] = 0 }
                    } else if hows.count >= 2 { lexicalFull[src] = 1 }
                }
            }
            return (src, Double(covered) / Double(total))
        }
        func tie(_ src: String) -> Int {
            if (src == "script" && hasMarks) || (src == "transport" && typed) { return 0 }
            if let l = lexicalFull[src] { return l }
            if let i = prefer.firstIndex(of: src) { return 2 + i }
            return 2 + prefer.count + (src == "transport" ? 0 : 1)
        }
        func r6(_ x: Double) -> Double { (x * 1e6).rounded() / 1e6 }
        return scored.sorted { a, b in
            if r6(a.1) != r6(b.1) { return r6(a.1) > r6(b.1) }
            if tie(a.0) != tie(b.0) { return tie(a.0) < tie(b.0) }
            return rank[a.0]! < rank[b.0]!
        }
    }

    /// The source to convert from: the best-read source that is not the target itself.
    static func sourceFor(_ text: String, target: String, prefer: [String] = []) -> String {
        let ranked = detect(text, prefer: prefer)
        func r6(_ x: Double) -> Double { (x * 1e6).rounded() / 1e6 }
        let best = r6(ranked.first?.1 ?? 0)
        for (src, cov) in ranked where src != target && r6(cov) == best { return src }
        return ranked.first?.0 ?? "transport"
    }
}
