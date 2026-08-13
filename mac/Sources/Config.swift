// User-facing settings, persisted in the input method's own defaults.
import Foundation

final class Config {
    static let shared = Config()
    private let d = UserDefaults.standard

    /// Conversion target: native · native-hu · native-zh · ipa · hu · zh · en
    var target: String {
        get { d.string(forKey: "target") ?? "native" }
        set { d.set(newValue, forKey: "target") }
    }

    /// Loose input (typing shortcuts) for the language targets.
    var looseInput: Bool {
        get { d.bool(forKey: "looseInput") }
        set { d.set(newValue, forKey: "looseInput") }
    }

    /// EN only: the dictionary view — real English spelling where known.
    var enDict: Bool {
        get { d.bool(forKey: "enDict") }
        set { d.set(newValue, forKey: "enDict") }
    }
}
