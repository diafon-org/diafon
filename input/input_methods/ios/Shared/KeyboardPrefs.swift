// What the iOS keyboard adds to the shared settings (apple/Core/Prefs.swift):
// the base layout, how the tail is kept provisional, and the modes its settings offer.
// Without full access a keyboard cannot share a container with its app, so
// these live in the keyboard's own defaults and are set in its panel.
import Foundation

extension Prefs {
    private var defaults: UserDefaults { .standard }
    private func store(_ v: Any?, _ key: String) {
        defaults.set(v, forKey: key)
        NotificationCenter.default.post(name: Prefs.changed, object: nil)
    }

    /// The base layout (apple/Core/Layouts.swift), the first one by default.
    var layout: String {
        get { defaults.string(forKey: "layout").flatMap { c in Layouts.all.contains { $0.code == c } ? c : nil } ?? Layouts.all[0].code }
        set { store(newValue, "layout") }
    }

    /// How the tail stays provisional: plain text the keyboard rewrites (the default),
    /// or marked text (underlined, as the system's own keyboards compose). Contacts
    /// leaves marked text out of the context and drops it on Done (README, the text path).
    var tailMode: TailMode {
        get { defaults.string(forKey: "tailMode").flatMap(TailMode.init(rawValue:)) ?? .replace }
        set { store(newValue.rawValue, "tailMode") }
    }

    /// The most languages on the quick list: the space bar's menu fits the keyboard and stays quick to slide through.
    static let quickMax = 4

    /// The modes on the space bar's menu and in the settings: Diafon, the quick list, the language in
    /// use if it is off the list, and off (plain keys).
    var menuModes: [String] {
        var list = ["script"] + offeredLanguages.map { "stage:" + $0 }
        if !list.contains("stage:" + language), !universal, offers(language), list.count <= Prefs.quickMax { list.append("stage:" + language) }
        return list + ["off"]
    }
    /// The mode in use, as the menu names it.
    var menuMode: String { !enabled ? "off" : universal ? "script" : "stage:" + language }
    func setMenuMode(_ m: String) {
        if m == "off" { if enabled { toggleOff() }; return }
        if m.hasPrefix("stage:") { language = String(m.dropFirst(6)) } else { output = "script" }
        if !enabled { enabled = true }
    }
    /// The mode in use, short, for the space bar: diafon, or the language's code.
    func shortLabel() -> String { universal ? "diafon" : language }

    /// Shift on at a sentence start, where the field asks for it; off by default.
    var autoCaps: Bool {
        get { defaults.object(forKey: "autoCaps") == nil ? false : defaults.bool(forKey: "autoCaps") }
        set { store(newValue, "autoCaps") }
    }
    func menuTitle(_ m: String) -> String { m == "off" ? "Off (plain keys)" : label(m) }
}
