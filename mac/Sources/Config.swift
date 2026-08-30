// User-facing settings, persisted in the input method's own defaults.
import Foundation

final class Config {
    static let shared = Config()
    private let d = UserDefaults.standard

    /// Pass-through: a plain keyboard. Default ON — conversion is opt-in per mode
    /// (a bare Shift tap toggles into the selected conversion mode and back).
    var passthrough: Bool {
        get { d.object(forKey: "passthrough") == nil ? true : d.bool(forKey: "passthrough") }
        set { d.set(newValue, forKey: "passthrough") }
    }

    /// A bare Shift tap toggles pass-through <-> the active conversion mode (IME convention).
    var shiftToggle: Bool {
        get { d.object(forKey: "shiftToggle") == nil ? true : d.bool(forKey: "shiftToggle") }
        set { d.set(newValue, forKey: "shiftToggle") }
    }

    /// The active conversion mode: hu · zh · en · uni · ipa
    var target: String {
        get { d.string(forKey: "target") ?? "uni" }
        set { d.set(newValue, forKey: "target") }
    }

    /// Loose input (typing shortcuts) — ON by default: HU bare a/e, ZH type-Pinyin.
    var looseInput: Bool {
        get { d.object(forKey: "looseInput") == nil ? true : d.bool(forKey: "looseInput") }
        set { d.set(newValue, forKey: "looseInput") }
    }

    /// Uni only: render tone digits as tone signs on the vowel (opt-in).
    var uniTones: Bool {
        get { d.bool(forKey: "uniTones") }
        set { d.set(newValue, forKey: "uniTones") }
    }

    /// Backspace reopens the glyph before the caret as editable notation (uni/IPA modes).
    var recompose: Bool {
        get { d.object(forKey: "recompose") == nil ? true : d.bool(forKey: "recompose") }
        set { d.set(newValue, forKey: "recompose") }
    }
}
