// The lexicon layer, ported from scripts/lexicon.py: word-level tables
// (data/lexicon/<code>.json) above the letters. Loaded lazily from the
// bundle's lexicon/ directory, or $DIAFON_LEXICON_DIR (the vector check).
import Foundation

final class Lexicon {
    let code: String
    let kind: String, match: String
    let read: [String: String], write: [String: String], choices: [String: [String]]
    let loans: [String], fold: [String: String], native: Set<String>, foreign: NSRegularExpression?
    let loanwrite: [String: String], lengthen: [String: String], common: Set<String>
    let sample: String, output: Bool
    private(set) lazy var syllables: [String] = read.keys.sorted { $0.count > $1.count }
    private(set) lazy var foldRules: [(String, [String], String)] = fold.keys.sorted { $0.count > $1.count }
        .map { k in (k, ((try? Engine.segments(k)) ?? []).compactMap { if case .form(_, let f, _) = $0 { return f } else { return nil } }, fold[k]!) }
    private(set) lazy var stems: [String] = write.keys.sorted { $0.count > $1.count }

    init?(json: [String: Any], code: String) {
        self.code = code
        kind = json["kind"] as? String ?? "word"
        match = json["match"] as? String ?? "word"
        read = json["read"] as? [String: String] ?? [:]
        write = json["write"] as? [String: String] ?? [:]
        choices = json["choices"] as? [String: [String]] ?? [:]
        loans = json["loans"] as? [String] ?? []
        fold = json["fold"] as? [String: String] ?? [:]
        native = Set(json["native"] as? [String] ?? [])
        loanwrite = json["loanwrite"] as? [String: String] ?? [:]
        lengthen = json["lengthen"] as? [String: String] ?? [:]
        common = Set(json["common"] as? [String] ?? [])
        foreign = (json["foreign"] as? String).flatMap { $0.isEmpty ? nil : try? NSRegularExpression(pattern: $0) }
        sample = json["sample"] as? String ?? ""
        output = json["output"] as? Bool ?? true
    }

    // MARK: loading

    private static var cache: [String: Lexicon?] = [:]
    static var directory: URL? = {
        if let env = ProcessInfo.processInfo.environment["DIAFON_LEXICON_DIR"] { return URL(fileURLWithPath: env) }
        return Bundle.main.resourceURL?.appendingPathComponent("lexicon")
    }()

    static func get(_ code: String) -> Lexicon? {
        if let c = cache[code] { return c }
        var out: Lexicon? = nil
        if let dir = directory, let data = try? Data(contentsOf: dir.appendingPathComponent("\(code).json")),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            out = Lexicon(json: json, code: code)
        }
        cache[code] = out
        return out
    }

    // MARK: words

    /// The words of a text (letters and marks, an apostrophe inside, tone digits
    /// after), or of transport text (ASCII letters, digits after), as ranges
    /// over the string's unicode scalars: no Foundation ranges, which misalign
    /// on combining marks.
    static func words(_ text: String, transport: Bool = false) -> [(Range<String.Index>, String)] {
        let u = text.unicodeScalars
        func isLetter(_ c: Unicode.Scalar) -> Bool {
            if transport { return (c.value >= 65 && c.value <= 90) || (c.value >= 97 && c.value <= 122) }
            switch c.properties.generalCategory {
            case .uppercaseLetter, .lowercaseLetter, .titlecaseLetter, .modifierLetter, .otherLetter,
                 .nonspacingMark, .spacingMark, .enclosingMark: return true
            default: return false
            }
        }
        func isDigit(_ c: Unicode.Scalar) -> Bool { c.isASCII && c.properties.numericType == .decimal }
        var out: [(Range<String.Index>, String)] = []
        var i = u.startIndex
        while i < u.endIndex {
            guard isLetter(u[i]) else { i = u.index(after: i); continue }
            let start = i
            while i < u.endIndex {
                if isLetter(u[i]) { i = u.index(after: i); continue }
                if !transport, u[i] == "'" || u[i] == "’" {
                    let n = u.index(after: i)
                    if n < u.endIndex, isLetter(u[n]) { i = n; continue }
                }
                break
            }
            while i < u.endIndex, isDigit(u[i]) { i = u.index(after: i) }
            var v = String.UnicodeScalarView(); v.append(contentsOf: u[start..<i])
            out.append((start..<i, String(v)))
        }
        return out
    }

    static func recase(_ out: String, _ original: String) -> String {
        guard let o = original.first, let f = out.first, o.isUppercase else { return out }
        return Engine.nfc(String(f).uppercased() + out.dropFirst())
    }

    /// The length of the longest of the host's own entries (read) the lowercased word is or starts with
    /// (a prefix lexicon, the stem looked up short too); 0 for none.
    func spokenStem(_ chars: [Character]) -> Int {
        if read.isEmpty || kind == "syllable" { return 0 }
        let key = String(chars)
        if match != "prefix" { return read[key] != nil ? chars.count : 0 }
        let top = min(chars.count, 24)
        if top > 2 {
            for i in stride(from: top, to: 2, by: -1) {
                if read[String(chars[0..<i])] != nil { return i }
                if let short = lengthen[String(chars[i - 1])], read[String(chars[0..<(i - 1)]) + short] != nil { return i }
            }
        }
        return 0
    }

    /// A word, or with match prefix a stem, the host reads its own way (Hungarian spoken:
    /// jamaica -> jamaika): (transport, the rest of the spelling), or nil.
    func readStem(_ word: String) -> (String, String)? {
        let w = Engine.nfc(word), key = w.lowercased()
        let chars = Array(key), wchars = Array(w)
        let i = spokenStem(chars)
        if i == 0 { return nil }
        let pre = String(chars[0..<i])
        let t = read[pre] ?? read[String(chars[0..<(i - 1)]) + (lengthen[String(chars[i - 1])] ?? "")]!
        return (Lexicon.recase(t, w), String(wchars.count == chars.count ? wchars[i...] : chars[i...]))
    }

    /// spelling (tone digits after it) -> transport, or nil; a syllable lexicon reads runs.
    func readWord(_ wordIn: String) -> String? {
        var word = Engine.nfc(wordIn)
        if kind == "syllable", word.range(of: "[0-9][^0-9]", options: .regularExpression) != nil {
            let re = try! NSRegularExpression(pattern: "[^0-9]+[0-9]*")
            let parts = re.matches(in: word, range: NSRange(location: 0, length: (word as NSString).length)).map { (word as NSString).substring(with: $0.range) }
            let outs = parts.map { readWord($0) }
            if outs.contains(where: { $0 == nil }) { return nil }
            return outs.compactMap { $0 }.joined()
        }
        var digits = ""
        while let last = word.last, last.isASCII, last.isNumber { digits = String(last) + digits; word.removeLast() }
        let key = word.lowercased()
        var t = read[key]
        if t == nil, kind == "syllable", !key.isEmpty {
            var out = "", i = key.startIndex
            while i < key.endIndex {
                guard let hit = syllables.first(where: { key[i...].hasPrefix($0) }) else { return nil }
                out += read[hit]!
                i = key.index(i, offsetBy: hit.count)
            }
            t = out
        }
        guard let tt = t else { return nil }
        return Lexicon.recase(tt, word) + digits
    }

    enum Written { case word(String), stem(String, String) }

    /// transport -> spelling; a prefix lexicon gives the stem's spelling and the rest.
    func writeWord(_ tIn: String) -> Written? {
        var t = tIn, digits = ""
        while let last = t.last, last.isASCII, last.isNumber { digits = String(last) + digits; t.removeLast() }   // the tone rides along
        guard !t.isEmpty else { return nil }
        let key = String(t.first!).lowercased() + t.dropFirst()
        if match == "prefix" {
            guard let best = stems.first(where: { key.hasPrefix($0) }) else { return nil }
            return .stem(Lexicon.recase(write[best]!, t), String(t.dropFirst(best.count)) + digits)
        }
        guard let sp = write[key] else { return nil }
        return .word(Lexicon.recase(sp, t) + digits)
    }

    /// A host's word written back as the loan it is, unless the letters' spelling is a host word.
    func writeLoan(_ tIn: String, lettersSpelling: String) -> String? {
        if loanwrite.isEmpty || native.contains(lettersSpelling.lowercased()) { return nil }
        var t = tIn, digits = ""
        while let last = t.last, last.isASCII, last.isNumber { digits = String(last) + digits; t.removeLast() }
        guard !t.isEmpty, let sp = loanwrite[String(t.first!).lowercased() + t.dropFirst()] else { return nil }
        return Lexicon.recase(sp, t) + digits
    }

    /// A loan's transport rewritten in this host's sounds.
    func foldLoan(_ t: String) -> String {
        if foldRules.isEmpty { return t }
        let segs = (try? Engine.segments(t, strict: false)) ?? []
        let forms: [String?] = segs.map { if case .form(_, let f, _) = $0 { return String(f.first!).lowercased() + f.dropFirst() } else { return nil } }
        var out = "", i = 0
        while i < segs.count {
            var hit: (String, [String], String)? = nil
            for r in foldRules where i + r.1.count <= segs.count {
                if (0..<r.1.count).allSatisfy({ forms[i + $0] == r.1[$0] }) { hit = r; break }
            }
            guard let h = hit else { out += segs[i].src; i += 1; continue }
            var caps = false, tones = ""
            for s in segs[i..<i + h.1.count] { if case .form(_, let f, let tn) = s { tones += tn; if s.src == segs[i].src { caps = f.first!.isUppercase } } }
            out += (caps ? String(h.2.first!).uppercased() + h.2.dropFirst() : h.2) + tones
            i += h.1.count
        }
        return out
    }

    /// A host's word that is a loan: (transport folded, source code), or nil. The longest stem a loan
    /// lexicon reads (among its common words where it has them) against the longest native stem, native
    /// on ties unless the stem has a foreign shape; a suffixed word whose stem has no shape is never a
    /// loan (akinek), with the shape the rest is read by the host's letters (streamingajánló); a stem
    /// whose final vowel the suffix lengthened (lengthen: pizzát) is looked up short too.
    func loan(_ word: String) -> (String, String)? {
        if loans.isEmpty { return nil }
        let w = Engine.nfc(word), key = w.lowercased()
        let chars = Array(key), wchars = Array(w)
        let top = min(chars.count, 24)
        func stems(_ i: Int) -> [String] {
            let pre = String(chars[0..<i])
            if let short = lengthen[String(chars[i - 1])] { return [pre, String(chars[0..<(i - 1)]) + short] }
            return [pre]
        }
        var nativeLen = 0
        if top > 2 { for i in stride(from: top, to: 2, by: -1) where stems(i).contains(where: { native.contains($0) }) { nativeLen = i; break } }
        let spokenLen = spokenStem(chars)          // the host's own entry, if any: it wins unless a loan stem is longer
        var loanLen = 0, src: String? = nil, stem: String? = nil
        if top > 2 {
            outer: for i in stride(from: top, to: 2, by: -1) {
                for lc in loans {
                    if let LL = Lexicon.get(lc), let hit = stems(i).first(where: { LL.read[$0] != nil && (LL.common.isEmpty || LL.common.contains($0)) }) { loanLen = i; src = lc; stem = hit; break outer }
                }
            }
        }
        guard let s = src, let st = stem, spokenLen < loanLen else { return nil }
        let head = String(chars[0..<loanLen])
        let isForeign = foreign.map { $0.firstMatch(in: head, range: NSRange(location: 0, length: (head as NSString).length)) != nil } ?? false
        if !isForeign && loanLen < chars.count { return nil }
        if nativeLen > loanLen || (nativeLen == loanLen && !isForeign) { return nil }
        let t = Lexicon.recase(Lexicon.get(s)!.read[st]!, word)
        let rest = String(wchars.count == chars.count ? wchars[loanLen...] : chars[loanLen...])
        let restT = rest.isEmpty ? "" : (SpecData.stages[code].map { Stages.readLetters(rest, Stages.table($0)) } ?? rest)
        return (foldLoan(t) + restT, s)
    }

    func choose(_ key: String) -> [String] { choices[key.lowercased()] ?? [] }
}
