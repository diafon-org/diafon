// What the iOS keyboard adds to the shared settings (apple/Core/Prefs.swift):
// the base layout, how the tail is kept provisional, and the strip's list of
// spellings. Without full access a keyboard cannot share a container with its
// app, so these live in the keyboard's own defaults and are set in its panel.
import Foundation

extension Prefs {
    private var defaults: UserDefaults { .standard }
    private func store(_ v: Any?, _ key: String) {
        defaults.set(v, forKey: key)
        NotificationCenter.default.post(name: Prefs.changed, object: nil)
    }

    /// The base layout (Layouts.swift), the first one by default.
    var layout: String {
        get { defaults.string(forKey: "layout").flatMap { c in Layouts.all.contains { $0.code == c } ? c : nil } ?? Layouts.all[0].code }
        set { store(newValue, "layout") }
    }

    /// How the tail stays provisional: marked text (underlined, as the system's own
    /// keyboards compose) or plain text the keyboard rewrites; the second for apps
    /// that mishandle marked text (README, the text path).
    var tailMode: TailMode {
        get { defaults.string(forKey: "tailMode").flatMap(TailMode.init(rawValue:)) ?? .marked }
        set { store(newValue.rawValue, "tailMode") }
    }

    /// The small label of an output on a strip chip.
    func shortLabel(_ out: String) -> String {
        if out == "transport" { return "as typed" }
        if out.hasPrefix("stage:") { return String(out.dropFirst(6)) }
        return "universal"
    }

    /// The tail in every spelling, one entry per distinct text: the output in use
    /// first, then Universal, each language, as typed.
    func spellings(_ tail: String) -> [(output: String, text: String)] {
        var outs = ["script"] + Prefs.languages.map { "stage:\($0.0)" } + ["transport"]
        if let i = outs.firstIndex(of: output) { outs.remove(at: i); outs.insert(output, at: 0) }
        var seen = Set<String>(), list: [(String, String)] = []
        for o in outs {
            let t = renderer(o)(tail)
            if seen.insert(t).inserted { list.append((o, t)) }
        }
        return list
    }

    /// The tail has an ill-formed segment (shown in the warning colour when `strict`).
    func illFormed(_ tail: String) -> Bool {
        ((try? Engine.segments(tail, strict: false)) ?? []).contains { if case .err = $0 { return true } else { return false } }
    }
}
