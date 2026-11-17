// What the iOS keyboard adds to the shared settings (apple/Core/Prefs.swift):
// the base layout, how the tail is kept provisional, and the logo key's menu.
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

    /// How the tail stays provisional: marked text (underlined, as the system's own
    /// keyboards compose) or plain text the keyboard rewrites; the second for apps
    /// that mishandle marked text (README, the text path).
    var tailMode: TailMode {
        get { defaults.string(forKey: "tailMode").flatMap(TailMode.init(rawValue:)) ?? .marked }
        set { store(newValue.rawValue, "tailMode") }
    }

    /// The modes on the logo key's menu: Universal, the quick list, the language in
    /// use if it is off the list, and off (plain keys).
    var menuModes: [String] {
        var list = ["script"] + quickLanguages.map { "stage:" + $0 }
        if !list.contains("stage:" + language), !universal { list.append("stage:" + language) }
        return list + ["off"]
    }
    /// The mode in use, as the menu names it.
    var menuMode: String { !enabled ? "off" : universal ? "script" : "stage:" + language }
    func setMenuMode(_ m: String) {
        if m == "off" { if enabled { toggleOff() }; return }
        if m.hasPrefix("stage:") { language = String(m.dropFirst(6)) } else { output = "script" }
        if !enabled { enabled = true }
    }
    func menuTitle(_ m: String) -> String { m == "off" ? "Off (plain keys)" : label(m) }
}
