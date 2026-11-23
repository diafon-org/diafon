// Emoji as word choices (data/emoji.json, from scripts/gen_emoji.py): a word
// in Diafon letters -> the emoji its names give, in any language, most used
// first; from the third letter, also those of the words it begins; failing
// both, those of its longest stem (kuțával: kuța). Offered like a syllable's
// characters; nothing changes in the text unless one is picked. Loaded once,
// lazily: from $DIAFON_EMOJI (the check) or the bundle.
import Foundation

enum Emoji {
    private struct Index { let words: [String: [Int]]; let keys: [String] }
    private struct Table { let rank: [String]; let exact: Index; let base: Index }

    /// A Diafon word on its bare letters alone: no marks, no tone signs, as a word
    /// typed without accents reads (szemuveg for szemüveg).
    static func base(_ t: String) -> String {
        var v = String.UnicodeScalarView()
        for u in t.lowercased().decomposedStringWithCanonicalMapping.unicodeScalars {
            switch u.properties.generalCategory {
            case .lowercaseLetter, .uppercaseLetter, .otherLetter: v.append(u)      // marks, tone signs and digits fall away
            default: break
            }
        }
        return String(v)
    }

    /// A Diafon word as the table keys it: lower case, no tone signs.
    private static func key(_ t: String) -> String {
        var v = String.UnicodeScalarView()
        for u in t.lowercased().unicodeScalars where u.properties.generalCategory != .modifierLetter && u.properties.generalCategory != .modifierSymbol
            && u.properties.generalCategory != .decimalNumber { v.append(u) }
        return String(v).precomposedStringWithCanonicalMapping
    }

    private static let table: Table? = {
        let urls = [ProcessInfo.processInfo.environment["DIAFON_EMOJI"].map { URL(fileURLWithPath: $0) },
                    Diafon.resource("emoji.json")].compactMap { $0 }
        for url in urls {
            guard let data = try? Data(contentsOf: url),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { continue }
            let words = json["words"] as? [String: [Int]] ?? [:]
            var based: [String: Set<Int>] = [:]
            for (k, v) in words { based[base(k), default: []].formUnion(v) }
            let b = based.mapValues { Array($0.sorted().prefix(12)) }
            return Table(rank: json["rank"] as? [String] ?? [], exact: Index(words: words, keys: words.keys.sorted()),
                         base: Index(words: b, keys: b.keys.sorted()))
        }
        return nil
    }()

    /// The emoji a typed word names, then (from `prefixFrom` letters) those of the
    /// words it begins, each part most used first. The word is in Diafon letters; case
    /// and tones do not count.
    static func choices(_ word: String, limit: Int = 16, prefixFrom: Int = 3) -> [String] {
        guard let t = table, !word.isEmpty else { return [] }
        return lookup([key(word)], t.exact, prefixFrom).prefix(limit).map { t.rank[$0] }
    }

    /// With conversion off: a word typed in a language's usual letters, likely
    /// without its accents (kutya, sziv, cool), read by each of `spellings`
    /// (stage codes, the person's own first) and matched on base letters.
    static func plain(_ word: String, spellings: [String], limit: Int = 16, prefixFrom: Int = 3) -> [String] {
        guard let t = table, !word.isEmpty else { return [] }
        var forms: [String] = [], keys: [String] = []
        for code in spellings {
            let f = key(Diafon.shared.convert(word.lowercased(), "stage:" + code, "script"))
            let k = base(f)
            if !f.isEmpty, !forms.contains(f) { forms.append(f) }
            if !k.isEmpty, !keys.contains(k) { keys.append(k) }
        }
        // the word read in full first (kutya: kuța), then on bare letters (accents left out)
        let exact = forms.flatMap { t.exact.words[$0] ?? [] }
        var out: [Int] = []
        for i in exact.sorted() + lookup(keys, t.base, prefixFrom) where !out.contains(i) { out.append(i) }
        return out.prefix(limit).map { t.rank[$0] }
    }

    /// A stem is at least this long: shorter ones match too much (kuțát: kuța, not kut).
    static let stemFrom = 4

    /// The keys' own emoji, then (from `prefixFrom` letters) those of the keys they
    /// begin, each part most used first; with neither, those of the longest stem
    /// a key begins with, so a word with a suffix finds its stem's.
    private static func lookup(_ keys: [String], _ ix: Index, _ prefixFrom: Int) -> [Int] {
        var out: [Int] = []
        for k in keys { out += (ix.words[k] ?? []).filter { !out.contains($0) } }
        out.sort()
        var more = Set<Int>()
        for key in keys where key.count >= prefixFrom {
            // the keys are sorted: the ones that begin with the word are one run
            var lo = 0, hi = ix.keys.count
            while lo < hi { let mid = (lo + hi) / 2; if ix.keys[mid] < key { lo = mid + 1 } else { hi = mid } }
            while lo < ix.keys.count, ix.keys[lo].hasPrefix(key) {
                if ix.keys[lo] != key { more.formUnion(ix.words[ix.keys[lo]] ?? []) }
                lo += 1
            }
        }
        if out.isEmpty, more.isEmpty {
            var best: (Int, [Int])? = nil
            for key in keys {
                // cut by code point, marks apart, so a stem's final vowel is found under the
                // length a suffix gave it (kuțával: kuțá is kuța and an acute)
                let c = Array(key.decomposedStringWithCanonicalMapping.unicodeScalars)
                let letters = c.map { $0.properties.generalCategory != .nonspacingMark }
                for n in stride(from: c.count - 1, through: 1, by: -1) where n > (best?.0 ?? 0) {
                    guard letters[..<n].filter({ $0 }).count >= stemFrom else { break }
                    var v = String.UnicodeScalarView(); v.append(contentsOf: c[..<n])
                    if let hit = ix.words[String(v).precomposedStringWithCanonicalMapping] { best = (n, hit); break }
                }
            }
            return best?.1 ?? []
        }
        return out + more.subtracting(out).sorted()
    }

    /// The classic emoticons, offered when what was typed since the last space is one
    /// (Session.run, the keys themselves: the host's context lags behind them).
    static let emoticons: [String: [String]] = [
        ":)": ["🙂", "😊"], ":-)": ["🙂", "😊"], "(:": ["🙂"], ":]": ["🙂"],
        ":D": ["😃", "😄", "😁"], ":-D": ["😃", "😄"], ";)": ["😉"], ";-)": ["😉"],
        ":(": ["🙁", "😞"], ":-(": ["🙁", "😞"], ":'(": ["😢", "😭"], ":'-(": ["😢"],
        ":P": ["😛", "😜"], ":p": ["😛", "😜"], ";P": ["😜"], ";p": ["😜"],
        ":O": ["😮", "😲"], ":o": ["😮"], ":*": ["😘", "😗"], ":-*": ["😘"],
        ":|": ["😐"], ":/": ["😕"], ":\\": ["😕"], ":S": ["😖"], ":$": ["😳"],
        "<3": ["❤️", "😍"], "</3": ["💔"], "^^": ["😊"], "^_^": ["😊"], "-_-": ["😑"],
        ">:(": ["😠", "😡"], "B)": ["😎"], "8)": ["😎"], "O:)": ["😇"], "o/": ["👋"], "\\o/": ["🙌"],
        ":+1:": ["👍"], "(y)": ["👍"], "xD": ["😆"], "XD": ["😆"], ":3": ["😺"],
    ]
}
