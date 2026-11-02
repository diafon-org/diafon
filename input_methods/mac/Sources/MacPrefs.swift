// What the Mac input method adds to the shared settings (apple/Core/Prefs.swift):
// the base layout under Diafon. An input method has no layout of its own; without
// one macOS keeps whichever layout was selected last (a Hungarian one moves the
// digits and puts ö ü ó on the top row), so Diafon names its own.
import Foundation

extension Prefs {
    /// The base layout (apple/Core/Layouts.swift), QWERTY by default, as on the phones.
    var layout: String {
        get { UserDefaults.standard.string(forKey: "layout").flatMap { c in Layouts.all.contains { $0.code == c } ? c : nil } ?? Layouts.all[0].code }
        set { UserDefaults.standard.set(newValue, forKey: "layout"); NotificationCenter.default.post(name: Prefs.changed, object: nil) }
    }

    /// The macOS keyboard layout for it: the ABC variants keep the digits (tones) on the top row.
    var keyLayoutID: String {
        ["qwerty": "com.apple.keylayout.ABC", "qwertz": "com.apple.keylayout.ABC-QWERTZ", "azerty": "com.apple.keylayout.ABC-AZERTY",
         "dvorak": "com.apple.keylayout.Dvorak", "colemak": "com.apple.keylayout.Colemak"][layout] ?? "com.apple.keylayout.ABC"
    }
}
