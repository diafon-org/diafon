// User-facing settings, persisted in the input method's own defaults.
import Foundation

final class Config {
    static let shared = Config()
    private let d = UserDefaults.standard

    /// Pass-through: the default state — a plain English keyboard, nothing converted.
    var passthrough: Bool {
        get { d.object(forKey: "passthrough") == nil ? true : d.bool(forKey: "passthrough") }
        set { d.set(newValue, forKey: "passthrough") }
    }

    /// A bare Shift tap toggles pass-through <-> the active conversion mode (IME convention).
    var shiftToggle: Bool {
        get { d.object(forKey: "shiftToggle") == nil ? true : d.bool(forKey: "shiftToggle") }
        set { d.set(newValue, forKey: "shiftToggle") }
    }

    /// The active conversion mode: hu · zh · native-hu · native-zh · native · ipa · en
    var target: String {
        get { d.string(forKey: "target") ?? "hu" }
        set { d.set(newValue, forKey: "target") }
    }

    /// Loose input (typing shortcuts) — ON by default: HU bare a/e, ZH type-Pinyin.
    var looseInput: Bool {
        get { d.object(forKey: "looseInput") == nil ? true : d.bool(forKey: "looseInput") }
        set { d.set(newValue, forKey: "looseInput") }
    }

    /// EN only: the dictionary view — real English spelling where known.
    var enDict: Bool {
        get { d.bool(forKey: "enDict") }
        set { d.set(newValue, forKey: "enDict") }
    }

    /// Backspace reopens the glyph before the caret as editable notation (native/IPA modes).
    var recompose: Bool {
        get { d.object(forKey: "recompose") == nil ? true : d.bool(forKey: "recompose") }
        set { d.set(newValue, forKey: "recompose") }
    }
}
