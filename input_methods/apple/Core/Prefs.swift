// The settings, shared in name and default with every Diafon input method
// (input_methods/README.md, Settings): output, language, tones, join,
// strict, enabled, profile.
import Foundation

final class Prefs {
    static let shared = Prefs()
    private let d = UserDefaults.standard
    static let changed = Notification.Name("diafon.prefs.changed")

    private func bool(_ key: String, _ def: Bool) -> Bool { d.object(forKey: key) == nil ? def : d.bool(forKey: key) }
    private func set(_ v: Any?, _ key: String) { d.set(v, forKey: key); NotificationCenter.default.post(name: Prefs.changed, object: nil) }

    /// Conversion on; off is a plain keyboard.
    var enabled: Bool { get { bool("enabled", true) } set { set(newValue, "enabled") } }
    /// The input profile: what keys produce which points (Profiles.swift). universal-v1 by default.
    var profile: String {
        get { d.string(forKey: "profile").flatMap { SpecData.profiles[$0] != nil ? $0 : nil } ?? Profiles.fallback }
        set { set(newValue, "profile") }
    }
    var profileData: ProfileData { Profiles.get(profile) }
    /// What is written out: "script" (Universal, the default) or "stage:<code>" (a language's
    /// spelling); "transport" only serves the escape path.
    var output: String {
        get {
            let o = d.string(forKey: "output") ?? "script"
            return o.hasPrefix("stage:") && !Prefs.spelled(String(o.dropFirst(6))) ? "script" : o
        }
        set { set(newValue, "output") }
    }
    /// Universal, or a language's spelling.
    var universal: Bool { !output.hasPrefix("stage:") }
    /// The language whose spelling is written when the output is a language's; remembered
    /// apart from the choice between Universal and a spelling, so the switch back keeps it.
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

    /// The mode as the person sees it: off (a plain keyboard), Universal, or the language's
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
    /// Quick taps: off → Universal → each language on the quick list → off.
    func cycleMode() {
        let quick = quickLanguages
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

    /// The lenient renderer for an output: what was typed, read by the profile in use, written out.
    /// Letters only: a language's spelling without its lexicon, for a word still being typed.
    func renderer(_ out: String? = nil, letters: Bool = false) -> (String) -> String {
        let forms = formRenderer(out, letters: letters)
        let p = profileData
        if !p.table { return forms }
        return { Profiles.unescape(forms(Profiles.transport($0, p))) }
    }

    /// The same for a text already in universal-v1 forms (a syllable, a converted selection).
    func formRenderer(_ out: String? = nil, letters: Bool = false) -> (String) -> String {
        let out = out ?? output
        let tones = self.tones, join = self.join
        if out == "transport" { return { $0 } }
        if out.hasPrefix("stage:"), let st = SpecData.stages[String(out.dropFirst(6))] {
            if letters { return { Stages.renderLetters($0, st, strict: false, tones: tones) } }
            return { Stages.render($0, st, strict: false, tones: tones) }
        }
        return { Engine.lenient($0, tones: tones, join: join) }
    }

    func label(_ out: String? = nil) -> String {
        let out = out ?? output
        if out.hasPrefix("stage:") { return SpecData.stages[String(out.dropFirst(6))]?.name ?? "Universal" }
        return "Universal"
    }

    /// The languages with a spelling, in the order every screen lists them: (code, name).
    /// The input methods carry no dictionary, so a language whose spelling is one (English,
    /// Mandarin) is not offered: it would only come out in the script.
    static let languages: [(String, String)] = SpecData.stageOrder.compactMap { code in
        SpecData.stages[code].flatMap { $0.lexical ? nil : (code, $0.name) }
    }
    /// A language with letters of its own.
    static func spelled(_ code: String) -> Bool { SpecData.stages[code].map { !$0.lexical } ?? false }

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
