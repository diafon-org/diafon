// The settings, shared in name and default with every Diafon input method
// (input_methods/README.md, Settings): output, language, tones, join,
// strict, enabled.
import Foundation

final class Prefs {
    static let shared = Prefs()
    private let d = UserDefaults.standard
    static let changed = Notification.Name("diafon.prefs.changed")

    private func bool(_ key: String, _ def: Bool) -> Bool { d.object(forKey: key) == nil ? def : d.bool(forKey: key) }
    private func set(_ v: Any?, _ key: String) { d.set(v, forKey: key); NotificationCenter.default.post(name: Prefs.changed, object: nil) }

    /// Conversion on; off is a plain keyboard.
    var enabled: Bool { get { bool("enabled", true) } set { set(newValue, "enabled") } }
    /// A language is offered when it is written by its letters alone.
    func offers(_ code: String) -> Bool { Prefs.spelled(code) }
    /// The quick list: what the menus show, in the list's order.
    var offeredLanguages: [String] { quickLanguages.filter { offers($0) } }
    /// What is written out: "script" (Diafon, the default) or "stage:<code>" (a language's
    /// spelling); "transport" only serves the escape path.
    var output: String {
        get {
            let o = d.string(forKey: "output") ?? "script"
            return o.hasPrefix("stage:") && !offers(String(o.dropFirst(6))) ? "script" : o
        }
        set { set(newValue, "output") }
    }
    /// Diafon itself, or a language's spelling.
    var universal: Bool { !output.hasPrefix("stage:") }
    /// The language whose spelling is written when the output is a language's; remembered
    /// apart from the choice between Diafon and a spelling, so the switch back keeps it.
    /// Picking a language puts it on the quick list.
    var language: String {
        get { d.string(forKey: "language").flatMap { Prefs.spelled($0) ? $0 : nil } ?? Prefs.defaultLanguage }
        set {
            d.set(newValue, forKey: "language")
            if !quickLanguages.contains(newValue) { setQuick(newValue, true) }
            set("stage:\(newValue)", "output")
        }
    }
    /// The quick list: the languages the menu and the switcher show, in
    /// the order given in the chooser (its right pane). No cap; past `quickComfort` the
    /// chooser warns that the cycle gets long.
    static let quickComfort = 3
    var quickLanguages: [String] {
        get {
            let list = (d.stringArray(forKey: "quickLanguages") ?? []).filter { Prefs.spelled($0) }
            return list.isEmpty ? [language] : list
        }
        set { set(newValue, "quickLanguages") }
    }
    /// Put a language on the quick list or take it off.
    func setQuick(_ code: String, _ on: Bool) {
        var list = quickLanguages.filter { $0 != code }
        if on { list.append(code) }
        quickLanguages = list
    }

    /// The mode as the person sees it: off (a plain keyboard), Diafon, or the language's
    /// spelling.
    var modeLabel: String { enabled ? label() : "Conversion off" }
    /// Off, or back to the last spelling that was on (iOS: a toggle tap after a pause).
    func toggleOff() {
        if !enabled, output == "transport" { d.set("script", forKey: "output") }
        set(!enabled, "enabled")
    }
    /// The iOS toggle key: taps within `tapWindow` of each other walk the cycle
    /// (cycleMode); a tap after a pause is toggleOff.
    static let tapWindow: TimeInterval = 1.5
    /// Quick taps: off → Diafon → each language on the quick list → off.
    func cycleMode() {
        let quick = offeredLanguages
        if !enabled { d.set("script", forKey: "output"); set(true, "enabled") }
        else if universal, let first = quick.first { language = first }
        else if !universal, let i = quick.firstIndex(of: language), i + 1 < quick.count { language = quick[i + 1] }
        else { set(false, "enabled") }
    }
    /// Write tones: a digit after a syllable becomes its tone sign; off, tone digits are dropped.
    var tones: Bool { get { bool("tones", true) } set { set(newValue, "tones") } }
    /// Join a long consonant's two letters with a ZWJ (the Diafon fonts draw them
    /// fused); off, a plain double.
    var join: Bool { get { bool("join", false) } set { set(newValue, "join") } }
    /// Flag ill-formed segments (they still pass through).
    var strict: Bool { get { bool("strict", false) } set { set(newValue, "strict") } }

    /// What was typed, written in an output (the one in use by default).
    func renderer(_ out: String? = nil) -> (String) -> String {
        let out = out ?? output, tones = self.tones, join = self.join
        return { Diafon.shared.render($0, output: out, tones: tones, join: join) }
    }

    /// The same for a text already in Diafon letters (a sample).
    func writer(_ out: String? = nil) -> (String) -> String {
        let out = out ?? output, tones = self.tones, join = self.join
        return { Diafon.shared.convert($0, "script", out, tones: tones, join: join) }
    }

    /// The streaming rule in the output in use: (what is final, the keys still open). In a
    /// language's spelling the word being typed stays open.
    func stream(_ buffer: String) -> (String, String) {
        Diafon.shared.stream(buffer, output: output, tones: tones, join: join, wordwise: !universal)
    }

    func label(_ out: String? = nil) -> String {
        let out = out ?? output
        if out.hasPrefix("stage:") { return Diafon.shared.stages[String(out.dropFirst(6))]?.name ?? "Diafon" }
        return "Diafon"
    }

    /// The languages with a spelling, in the order every screen lists them: (code, name).
    /// The input methods carry no dictionary, so a language whose spelling is one (English,
    /// Mandarin) is not offered: it would only come out in the script.
    static let languages: [(String, String)] = Diafon.shared.stageOrder.compactMap { code in
        Diafon.shared.stages[code].flatMap { $0.lexical ? nil : (code, $0.name) }
    }
    /// A language with letters of its own.
    static func spelled(_ code: String) -> Bool { Diafon.shared.stages[code].map { !$0.lexical } ?? false }

    /// The person's own sources, for detection's ties: the mode in use, the language
    /// in use, the quick list, the system's languages.
    var preferredSources: [String] {
        var out: [String] = []
        if enabled { out.append(output) }
        out.append("stage:" + language)
        out += quickLanguages.map { "stage:" + $0 }
        for l in Locale.preferredLanguages {
            let c = String(l.prefix(2)).lowercased()
            if Prefs.spelled(c) { out.append("stage:" + c) }
        }
        var seen = Set<String>()
        return out.filter { seen.insert($0).inserted }
    }

    /// The first system language that has a spelling, else the first spelling.
    static let defaultLanguage: String = {
        for l in Locale.preferredLanguages {
            let code = String(l.prefix(2)).lowercased()
            if Prefs.spelled(code) { return code }
        }
        return languages.first?.0 ?? "hu"
    }()
}
