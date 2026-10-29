// The settings, shared in name and default with every Diafon input method
// (plan.md, question 4): output, language, tones, strict, enabled, toggle.
import Foundation

final class Prefs {
    static let shared = Prefs()
    private let d = UserDefaults.standard
    static let changed = Notification.Name("diafon.prefs.changed")

    private func bool(_ key: String, _ def: Bool) -> Bool { d.object(forKey: key) == nil ? def : d.bool(forKey: key) }
    private func set(_ v: Any?, _ key: String) { d.set(v, forKey: key); NotificationCenter.default.post(name: Prefs.changed, object: nil) }

    /// Conversion on; off is a plain keyboard.
    var enabled: Bool { get { bool("enabled", true) } set { set(newValue, "enabled") } }
    /// A bare Shift tap flips conversion on and off.
    var shiftToggle: Bool { get { bool("shiftToggle", true) } set { set(newValue, "shiftToggle") } }
    /// What is written out: "script" (Universal, the default) or "stage:<code>" (a language's
    /// spelling); "transport" only serves the escape path.
    var output: String { get { d.string(forKey: "output") ?? "script" } set { set(newValue, "output") } }
    /// Universal, or a language's spelling.
    var universal: Bool { !output.hasPrefix("stage:") }
    /// The language whose spelling is written when the output is a language's; remembered
    /// apart from the choice between Universal and a spelling, so the switch back keeps it.
    /// Picking a language puts it on the quick list.
    var language: String {
        get { d.string(forKey: "language") ?? Prefs.defaultLanguage }
        set {
            d.set(newValue, forKey: "language")
            if !quickLanguages.contains(newValue) { setQuick(newValue, true) }
            set("stage:\(newValue)", "output")
        }
    }
    /// The quick list: the languages the menu shows and the Shift tap cycles through, in
    /// the order given in the chooser (its right pane). No cap; past `quickComfort` the
    /// chooser warns that the cycle gets long.
    static let quickComfort = 3
    var quickLanguages: [String] {
        get {
            let list = (d.stringArray(forKey: "quickLanguages") ?? []).filter { SpecData.stages[$0] != nil }
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

    /// The mode as the person sees it: off (a plain keyboard), Universal, or the language's
    /// spelling; the toggle key cycles them.
    var modeLabel: String { enabled ? label() : "Conversion off" }
    /// A bare Shift tap after a pause: off, or back to the last spelling that was on.
    /// Taps within `tapWindow` of each other walk the cycle instead (cycleMode).
    static let tapWindow: TimeInterval = 1.5
    func toggleOff() {
        if !enabled, output == "transport" { d.set("script", forKey: "output") }
        set(!enabled, "enabled")
    }
    /// Quick taps: off → Universal → each language on the quick list → off.
    func cycleMode() {
        let quick = quickLanguages
        if !enabled { d.set("script", forKey: "output"); set(true, "enabled") }
        else if universal, let first = quick.first { language = first }
        else if !universal, let i = quick.firstIndex(of: language), i + 1 < quick.count { language = quick[i + 1] }
        else { set(false, "enabled") }
    }

    /// Keep tone digits in the output.
    var tones: Bool { get { bool("tones", true) } set { set(newValue, "tones") } }
    /// Flag ill-formed segments (they still pass through).
    var strict: Bool { get { bool("strict", false) } set { set(newValue, "strict") } }

    /// The lenient renderer for an output.
    func renderer(_ out: String? = nil) -> (String) -> String {
        let out = out ?? output
        let tones = self.tones
        if out == "transport" { return { $0 } }
        if out.hasPrefix("stage:"), let st = SpecData.stages[String(out.dropFirst(6))] {
            return { Stages.render($0, st, strict: false, tones: tones) }
        }
        return { Engine.lenient($0, tones: tones) }
    }

    func label(_ out: String? = nil) -> String {
        let out = out ?? output
        if out.hasPrefix("stage:") { return SpecData.stages[String(out.dropFirst(6))]?.name ?? "Universal" }
        return "Universal"
    }

    /// The languages with a spelling, in the order every screen lists them: (code, name).
    static let languages: [(String, String)] = SpecData.stageOrder.compactMap { code in
        SpecData.stages[code].map { (code, $0.name) }
    }

    /// The person's own sources, for detection's ties: the mode in use, the language
    /// in use, the quick list, the system's languages.
    var preferredSources: [String] {
        var out: [String] = []
        if enabled { out.append(output) }
        out.append("stage:" + language)
        out += quickLanguages.map { "stage:" + $0 }
        for l in Locale.preferredLanguages {
            let c = String(l.prefix(2)).lowercased()
            if SpecData.stages[c] != nil { out.append("stage:" + c) }
        }
        var seen = Set<String>()
        return out.filter { seen.insert($0).inserted }
    }

    /// The first system language that has a spelling, else the first spelling.
    static let defaultLanguage: String = {
        for l in Locale.preferredLanguages {
            let code = String(l.prefix(2)).lowercased()
            if SpecData.stages[code] != nil { return code }
        }
        return languages.first?.0 ?? "hu"
    }()
}
