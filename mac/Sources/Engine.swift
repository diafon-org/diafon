// The conversion engine as data — the decoded form of `diaphone export-json` (out/engine.json).
// All conversion knowledge lives here + Decoder.swift; nothing else knows about phonology.
import Foundation

struct Rule: Codable {                          // one context rule from data/orth/<lang>.yaml `_rules`
    let t: String                               // token this rule applies to
    let g: String                               // grapheme it produces
    let next: [String]?                         // next token must be one of these
    let prev: [String]?                         // previous token must be one of these
    let next_vowel: Bool?                       // next token must start with a vowel letter
    let first: Bool?                            // token must be word-initial
}

struct Engine: Codable {
    let version: Int
    let targets: [String]
    let maps: [String: [String: String]]        // universal targets: label -> glyph
    let keys: [String]                          // greedy (longest-first) token order
    let toneSup: [String: String]               // digit -> superscript (IPA target only)
    let toneSigns: [String: String]             // digit -> combining tone sign (uni, opt-in; 0/5 neutral)
    let orth: [String: [String: String]]        // language: label -> grapheme
    let lazy: [String: [String: String]]        // loose-input overlays per language
    let rules: [String: [Rule]]                 // language: ordered context rules (first match wins)
    let toneMarks: [String: String]

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
