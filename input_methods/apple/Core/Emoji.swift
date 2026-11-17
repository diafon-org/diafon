// Emoji as word choices (data/emoji.json, from scripts/gen_emoji.py): a typed
// word's input form -> the emoji its names give, in any language, most used
// first; from the third letter, also those of the words it begins. Offered
// like Mandarin's characters for a syllable; nothing changes in the text
// unless one is picked. Loaded once, lazily: from $DIAFON_EMOJI (the check),
// the lexicon directory (the Mac bundle) or the bundle's root (iOS).
import Foundation

enum Emoji {
    private struct Table { let rank: [String]; let words: [String: [Int]]; let keys: [String] }

    private static let table: Table? = {
        let urls = [ProcessInfo.processInfo.environment["DIAFON_EMOJI"].map { URL(fileURLWithPath: $0) },
                    Lexicon.directory?.appendingPathComponent("emoji.json"),
                    Bundle.main.url(forResource: "emoji", withExtension: "json")].compactMap { $0 }
        for url in urls {
            guard let data = try? Data(contentsOf: url),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { continue }
            let words = json["words"] as? [String: [Int]] ?? [:]
            return Table(rank: json["rank"] as? [String] ?? [], words: words, keys: words.keys.sorted())
        }
        return nil
    }()

    /// The emoji a typed word names, then (from `prefixFrom` letters) those of the
    /// words it begins, each part most used first. The word is input form; case
    /// and tone digits do not count.
    static func choices(_ word: String, limit: Int = 16, prefixFrom: Int = 3) -> [String] {
        guard let t = table, !word.isEmpty else { return [] }
        let key = String(word.lowercased().filter { !$0.isNumber })
        var out: [Int] = t.words[key] ?? []
        if key.count >= prefixFrom {
            // the keys are sorted: the ones that begin with the word are one run
            var lo = 0, hi = t.keys.count
            while lo < hi { let mid = (lo + hi) / 2; if t.keys[mid] < key { lo = mid + 1 } else { hi = mid } }
            var more = Set<Int>()
            while lo < t.keys.count, t.keys[lo].hasPrefix(key) {
                if t.keys[lo] != key { more.formUnion(t.words[t.keys[lo]] ?? []) }
                lo += 1
            }
            out += more.subtracting(out).sorted()
        }
        return out.prefix(limit).map { t.rank[$0] }
    }

    /// The classic emoticons, offered when the text before the cursor ends with one.
    static let emoticons: [String: [String]] = [
        ":)": ["🙂", "😊"], ":-)": ["🙂", "😊"], "(:": ["🙂"], ":]": ["🙂"],
        ":D": ["😃", "😄", "😁"], ":-D": ["😃", "😄"], ";)": ["😉"], ";-)": ["😉"],
        ":(": ["🙁", "😞"], ":-(": ["🙁", "😞"], ":'(": ["😢", "😭"], ":'-(": ["😢"],
        ":P": ["😛", "😜"], ":p": ["😛", "😜"], ";P": ["😜"], ";p": ["😜"],
        ":O": ["😮", "😲"], ":o": ["😮"], ":*": ["😘", "😗"], ":-*": ["😘"],
        ":|": ["😐"], ":/": ["😕"], ":\\": ["😕"], ":S": ["😖"], ":$": ["😳"],
        "<3": ["❤️", "😍"], "</3": ["💔"], "^^": ["😊"], "^_^": ["😊"], "-_-": ["😑"],
        ">:(": ["😠", "😡"], "B)": ["😎"], "8)": ["😎"], "O:)": ["😇"], "o/": ["👋"], "\\o/": ["🙌"],
        ":+1:": ["👍"], "(y)": ["👍"],
    ]

    /// The emoticon the text ends with, standing alone (at the start or after a
    /// space): (the emoticon, its emoji), the longest one first.
    static func emoticon(before text: String) -> (String, [String])? {
        for n in stride(from: min(5, text.count), through: 2, by: -1) {
            let tail = String(text.suffix(n))
            guard let e = emoticons[tail] else { continue }
            let rest = text.dropLast(n)
            if rest.isEmpty || rest.last?.isWhitespace == true { return (tail, e) }
        }
        return nil
    }
}
