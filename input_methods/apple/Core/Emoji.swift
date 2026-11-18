// Emoji as word choices (data/emoji.json, from scripts/gen_emoji.py): a typed
// word's input form -> the emoji its names give, in any language, most used
// first; from the third letter, also those of the words it begins; failing
// both, those of its longest stem (kutjawval: kutja, tqigawt: tqiga). Offered
// like Mandarin's characters for a syllable; nothing changes in the text
// unless one is picked. Loaded once, lazily: from $DIAFON_EMOJI (the check),
// the lexicon directory (the Mac bundle) or the bundle's root (iOS).
import Foundation

enum Emoji {
    private struct Index { let words: [String: [Int]]; let keys: [String] }
    private struct Table { let rank: [String]; let exact: Index; let base: Index }

    /// An input form on its base letters alone: without the operators and the
    /// length mark (c j q x y w), as a word typed without accents reads; the
    /// rounded front vowels as their plain look-alikes (ic ü → u, ec ö → o), as
    /// szemuveg is typed for szemüveg.
    static func base(_ t: String) -> String {
        let t = t.lowercased().replacingOccurrences(of: "ic", with: "u").replacingOccurrences(of: "ec", with: "o")
        return String(t.filter { !"cjqxyw".contains($0) && !$0.isNumber })
    }

    private static let table: Table? = {
        let urls = [ProcessInfo.processInfo.environment["DIAFON_EMOJI"].map { URL(fileURLWithPath: $0) },
                    Lexicon.directory?.appendingPathComponent("emoji.json"),
                    Bundle.main.url(forResource: "emoji", withExtension: "json")].compactMap { $0 }
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
    /// words it begins, each part most used first. The word is input form; case
    /// and tone digits do not count.
    static func choices(_ word: String, limit: Int = 16, prefixFrom: Int = 3) -> [String] {
        guard let t = table, !word.isEmpty else { return [] }
        let key = String(word.lowercased().filter { !$0.isNumber })
        return lookup([key], t.exact, prefixFrom).prefix(limit).map { t.rank[$0] }
    }

    /// With conversion off: a word typed in a language's usual letters, likely
    /// without its accents (kutya, sziv, cool), read by each of `spellings`
    /// (stage codes, the person's own first) and matched on base letters.
    static func plain(_ word: String, spellings: [String], limit: Int = 16, prefixFrom: Int = 3) -> [String] {
        guard let t = table, !word.isEmpty else { return [] }
        var forms: [String] = [], keys: [String] = []
        for code in spellings {
            // a lexicon the keyboard cannot load whole is read from its index (en: home → houxm)
            let reading = Lexicon.get(code) == nil ? ReadIndex.get(code).map { $0.read(word.lowercased()) } : nil
            if case .some(nil) = reading { continue }
            let f = String((reading.flatMap { $0 } ?? Stages.parse(word.lowercased(), "stage:" + code)).filter { !$0.isNumber })
            let k = base(f)
            if !f.isEmpty, !forms.contains(f) { forms.append(f) }
            if !k.isEmpty, !keys.contains(k) { keys.append(k) }
        }
        // the word read in full first (kutya: kutja), then on base letters (accents left out)
        let exact = forms.flatMap { t.exact.words[$0] ?? [] }
        var out: [Int] = []
        for i in exact.sorted() + lookup(keys, t.base, prefixFrom) where !out.contains(i) { out.append(i) }
        return out.prefix(limit).map { t.rank[$0] }
    }

    /// A stem is at least this long: shorter ones match too much (kutjawt: kutja, not kut).
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
                let c = Array(key)
                for n in stride(from: c.count - 1, through: stemFrom, by: -1) where n > (best?.0 ?? 0) {
                    if let hit = ix.words[String(c[..<n])] { best = (n, hit); break }
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

/// A lexicon's reading as sorted lines, `word<TAB>input form` (data/lexicon/<code>.read.tsv,
/// from scripts/gen_lexicon.py): the same table as the lexicon's `read`, mapped from the
/// file and searched in place, for the iOS keyboard, which cannot hold the parsed lexicon.
final class ReadIndex {
    private let data: Data
    private init(_ data: Data) { self.data = data }
    private static var cache: [String: ReadIndex?] = [:]

    static func get(_ code: String) -> ReadIndex? {
        if let c = cache[code] { return c }
        let urls = [Lexicon.directory?.appendingPathComponent("\(code).read.tsv"),
                    Bundle.main.url(forResource: "\(code).read", withExtension: "tsv")].compactMap { $0 }
        let ix = urls.lazy.compactMap { try? Data(contentsOf: $0, options: .alwaysMapped) }.first.map(ReadIndex.init)
        cache[code] = ix
        return ix
    }

    /// The input form of a word (lowercase), or nil where the lexicon has none.
    func read(_ word: String) -> String? {
        let key = Array(word.utf8)
        return data.withUnsafeBytes { (raw: UnsafeRawBufferPointer) -> String? in
            let b = raw.bindMemory(to: UInt8.self)
            let n = b.count
            func lineStart(_ i: Int) -> Int { var i = i; while i > 0, b[i - 1] != 10 { i -= 1 }; return i }
            // compares the line's word at `s` with the key: <0, 0, >0
            func cmp(_ s: Int) -> Int {
                var i = s, j = 0
                while true {
                    let c = i < n ? b[i] : 10
                    let end = c == 9 || c == 10
                    if j == key.count { return end ? 0 : 1 }
                    if end { return -1 }
                    if c != key[j] { return c < key[j] ? -1 : 1 }
                    i += 1; j += 1
                }
            }
            var lo = 0, hi = n
            while lo < hi {
                let s = lineStart((lo + hi) / 2)
                let c = cmp(s)
                if c == 0 {
                    let i = s + key.count + 1; var e = i
                    while e < n, b[e] != 10 { e += 1 }
                    return String(decoding: UnsafeBufferPointer(rebasing: b[i..<e]), as: UTF8.self)
                }
                if c < 0 {
                    var e = s; while e < n, b[e] != 10 { e += 1 }
                    lo = e + 1
                } else { hi = s }
            }
            return nil
        }
    }
}
