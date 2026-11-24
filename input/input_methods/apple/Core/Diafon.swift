// The alphabet and the typing, for the Mac and iOS input methods. Nothing is
// ported: the apps run the site's own JavaScript (diafon-core.js, the
// alphabet; diafon-keys.js, the typing) in JavaScriptCore, on the alphabet's
// spec and the compiled profile, so a letter typed here is the letter the
// site writes. scripts/gen_apple.py puts the five files in apple/Resources;
// tests/test_apple.py replays the vectors through this file.
//
// An output is "script" (Diafon), "stage:<code>" (a language's spelling) or
// "transport" (the keys as typed, the escape path).
import Foundation
import JavaScriptCore

/// A language's spelling, as the screens need it.
struct StageInfo {
    let code: String, name: String
    let sample: String                 // a phrase in Diafon letters
    let lexical: Bool                  // spelled by a dictionary the apps do not carry (English): not offered.
                                       // Mandarin's pinyin is a table of syllables, bundled (lexicons.json): offered
}

final class Diafon {
    static let shared = Diafon()

    private let ctx: JSContext
    private(set) var version = "", typing = ""
    /// The keys that are not letters: typed after one, they mark it.
    private(set) var operators: Set<Character> = []
    private(set) var stages: [String: StageInfo] = [:]
    /// The stages in the order every screen lists them: by name.
    private(set) var stageOrder: [String] = []
    /// Why nothing converts, when the files could not be loaded.
    private(set) var failure: String? = nil

    /// A bundled file: from $DIAFON_RESOURCES (the check), the bundle, or its Resources folder.
    static func resource(_ name: String) -> URL? {
        if let dir = ProcessInfo.processInfo.environment["DIAFON_RESOURCES"] { return URL(fileURLWithPath: dir).appendingPathComponent(name) }
        let ns = name as NSString
        if let u = Bundle.main.url(forResource: ns.deletingPathExtension, withExtension: ns.pathExtension) { return u }
        return Bundle.main.resourceURL?.appendingPathComponent(name)
    }
    private static func text(_ name: String) -> String? {
        resource(name).flatMap { try? String(contentsOf: $0, encoding: .utf8) }
    }

    private init() {
        ctx = JSContext()
        ctx.exceptionHandler = { [weak self] _, e in
            self?.failure = e?.toString()
            NSLog("Diafon: %@", e?.toString() ?? "a JavaScript error")
        }
        guard let core = Diafon.text("diafon-core.js"), let keys = Diafon.text("diafon-keys.js"), let glue = Diafon.text("diafon-glue.js"),
              let spec = Diafon.text("alphabet.json"), let profile = Diafon.text("typing.json") else {
            failure = "the alphabet's files are missing from the app"
            return
        }
        for script in [core, keys, glue] { ctx.evaluateScript(script) }
        guard let info = call("diafonInit", [spec, profile, Diafon.text("lexicons.json") ?? "{}"])?.toString(), let data = info.data(using: .utf8),
              let d = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            failure = failure ?? "the alphabet did not load"
            return
        }
        version = d["version"] as? String ?? ""
        typing = d["typing"] as? String ?? ""
        operators = Set(d["operators"] as? String ?? "")
        for st in d["stages"] as? [[String: Any]] ?? [] {
            guard let code = st["code"] as? String, let name = st["name"] as? String else { continue }
            stages[code] = StageInfo(code: code, name: name, sample: st["sample"] as? String ?? "", lexical: st["lexical"] as? Bool ?? false)
        }
        stageOrder = stages.keys.sorted { stages[$0]!.name < stages[$1]!.name }
        failure = nil
    }

    private func call(_ name: String, _ args: [Any]) -> JSValue? {
        guard let f = ctx.objectForKeyedSubscript(name), !f.isUndefined else { return nil }
        let before = failure
        failure = nil
        let r = f.call(withArguments: args)
        defer { failure = before }
        return failure == nil ? r : nil                   // an exception: no value
    }

    /// What was typed, written in an output.
    func render(_ typed: String, output: String = "script", tones: Bool = true, join: Bool = false) -> String {
        call("diafonRender", [typed, output, tones, join])?.toString() ?? typed
    }

    /// The streaming rule: (what is final, written out; the keys still open). A letter stays
    /// open while the next key could still change it; wordwise, the whole word being typed does.
    func stream(_ buffer: String, output: String = "script", tones: Bool = true, join: Bool = false, wordwise: Bool = false) -> (String, String) {
        guard let r = call("diafonStream", [buffer, output, tones, join, wordwise])?.toArray(), r.count == 2,
              let head = r[0] as? String, let tail = r[1] as? String else { return (buffer, "") }
        return (head, tail)
    }

    /// A text read in one source and written in a target.
    func convert(_ text: String, _ source: String, _ target: String, tones: Bool = true, join: Bool = false) -> String {
        if source == target { return text }
        return call("diafonConvert", [text, source, target, tones, join])?.toString() ?? text
    }

    /// The keys that type a Diafon text: what to press for it.
    func keys(for script: String) -> String {
        call("diafonKeys", [script])?.toString() ?? script
    }

    /// The sources a text may be in, best first: (source, the share of its letters read).
    func detect(_ text: String, prefer: [String] = []) -> [(String, Double)] {
        guard let r = call("diafonDetect", [text, prefer])?.toArray() else { return [] }
        return r.compactMap { ($0 as? [Any]).flatMap { p in p.count == 2 ? (p[0] as? String).map { ($0, (p[1] as? NSNumber)?.doubleValue ?? 0) } : nil } }
    }

    /// The source to read a text in, on its way to a target: the best one that is not the target itself.
    func sourceFor(_ text: String, target: String, prefer: [String] = []) -> String {
        call("diafonSourceFor", [text, target, prefer])?.toString() ?? "script"
    }
}
