// The conversion engine as data — the decoded form of `diaphone export-json` (out/engine.json).
// All conversion knowledge lives here + Decoder.swift; nothing else knows about phonology.
import Foundation

struct Engine: Codable {
    let version: Int
    let targets: [String]
    let maps: [String: [String: String]]        // universal targets: label -> glyph
    let keys: [String]                          // greedy (longest-first) token order
    let toneSup: [String: String]               // universal: trailing digit -> superscript
    let orth: [String: [String: String]]        // language: label -> grapheme
    let lazy: [String: [String: String]]        // loose-input overlays per language
    let zhRetro: [String: [String]]             // zh hush initial -> [plain, before-front]
    let toneMarks: [String: String]
    let enDict: [String: String]                // en dictionary view: canonical word -> real spelling
    let enCanon: [String: String]               // en: alias label -> canonical label (dict lookup)

    static func load(url: URL) throws -> Engine {
        try JSONDecoder().decode(Engine.self, from: Data(contentsOf: url))
    }

    func labels(for target: String) -> [String] {
        (maps[target] ?? [:]).keys.sorted { $0.count > $1.count }
    }

    func orthLabels(for lang: String, loose: Bool) -> (orth: [String: String], keys: [String]) {
        var o = orth[lang] ?? [:]
        if loose, let extra = lazy[lang] {
            for (k, v) in extra { o[k] = v }
        }
        return (o, o.keys.sorted { $0.count > $1.count })
    }
}
