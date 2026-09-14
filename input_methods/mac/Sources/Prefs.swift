// The settings, shared in name and default with every Diafon input method
// (plan.md, question 4): output, tones, strict, enabled, toggle.
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
    /// What is written out: "script" (universal: the web letters) or "stage:<code>" (a
    /// language's spelling); "transport" only serves the escape path.
    var output: String { get { d.string(forKey: "output") ?? "script" } set { set(newValue, "output") } }
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
        return Prefs.outputs.first { $0.0 == out }?.1 ?? SpecData.stages[String(out.dropFirst(6))]?.name ?? "universal"
    }

    /// Every output, in the order every screen lists them: (value, label).
    static let outputs: [(String, String)] = {
        var list: [(String, String)] = [("script", "Universal")]
        for code in SpecData.stageOrder {
            guard let st = SpecData.stages[code] else { continue }
            list.append(("stage:\(code)", st.name))
        }
        return list
    }()
}
