// Emoji as word choices (data/emoji.json, from scripts/gen_emoji.py):
// a typed word's input form -> the emoji named by it in a language, most used
// first. Offered like Mandarin's characters for a syllable; nothing changes
// in the text unless one is picked. Loaded once, lazily: from $DIAFON_EMOJI
// (the check), the lexicon directory (the Mac bundle) or the bundle's root (iOS).
import Foundation

enum Emoji {
    private struct Table { let rank: [String: Int]; let choices: [String: [String: [String]]] }

    private static let table: Table? = {
        let urls = [ProcessInfo.processInfo.environment["DIAFON_EMOJI"].map { URL(fileURLWithPath: $0) },
                    Lexicon.directory?.appendingPathComponent("emoji.json"),
                    Bundle.main.url(forResource: "emoji", withExtension: "json")].compactMap { $0 }
        for url in urls {
            guard let data = try? Data(contentsOf: url),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { continue }
            let rank = json["rank"] as? [String] ?? []
            return Table(rank: Dictionary(rank.enumerated().map { ($1, $0) }, uniquingKeysWith: { a, _ in a }),
                         choices: json["choices"] as? [String: [String: [String]]] ?? [:])
        }
        return nil
    }()

    /// The languages that name emoji.
    static var languages: [String] { table.map { Array($0.choices.keys).sorted() } ?? [] }

    /// The emoji a typed word names, in any of `languages` (all when empty), most used
    /// first. The word is input form; case and tone digits do not count.
    static func choices(_ word: String, languages: [String] = [], limit: Int = 8) -> [String] {
        guard let t = table, !word.isEmpty else { return [] }
        let key = String(word.lowercased().filter { !$0.isNumber })
        var out: [String] = []
        for code in languages.isEmpty ? Array(t.choices.keys) : languages {
            for e in t.choices[code]?[key] ?? [] where !out.contains(e) { out.append(e) }
        }
        return Array(out.sorted { (t.rank[$0] ?? .max) < (t.rank[$1] ?? .max) }.prefix(limit))
    }
}
