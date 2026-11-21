// The keyboards the system shows. Each output is an input mode of Diafon
// (tools/modes.py): Diafon itself, and one per language. Only a chosen few
// are switched on: Diafon, and the languages on the quick list (Keyboards…
// in the menu). The list is the one place to choose them; a change there
// switches the modes on and off in the system's input sources.
import Carbon
import Foundation

enum Keyboards {
    static let base = "org.diafon.inputmethod.Diafon"

    private static func source(_ id: String) -> TISInputSource? {
        let props = [kTISPropertyInputSourceID as String: id] as CFDictionary
        return (TISCreateInputSourceList(props, true)?.takeRetainedValue() as? [TISInputSource])?.first
    }
    private static func isEnabled(_ s: TISInputSource) -> Bool {
        guard let p = TISGetInputSourceProperty(s, kTISPropertyInputSourceIsEnabled) else { return false }
        return CFBooleanGetValue(Unmanaged<CFBoolean>.fromOpaque(p).takeUnretainedValue())
    }
    private static func set(_ id: String, _ on: Bool) {
        guard let s = source(id), isEnabled(s) != on else { return }
        if on { TISEnableInputSource(s) } else { TISDisableInputSource(s) }
    }

    private static var last: [String]? = nil
    /// Switch on Diafon and the quick list's languages, and the other languages off.
    /// Does nothing while the list is as it was at the last call.
    static func sync() {
        let wanted = Prefs.shared.quickLanguages
        if wanted == last { return }
        last = wanted
        set(base + ".universal", true)
        for (code, _) in Prefs.languages { set(base + "." + code, wanted.contains(code)) }
    }
}
