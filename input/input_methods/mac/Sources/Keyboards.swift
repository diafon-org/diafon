// The keyboards the system shows. Each output is an input mode of Diafon
// (tools/modes.py): Diafon itself, and one per language. The system's own
// list of input sources is the one record of which are on: this file reads
// it and changes it, and keeps no list of its own. So a keyboard added or
// removed in System Settings → Keyboard → Input Sources is all there is.
import Carbon
import Foundation

enum Keyboards {
    static let base = "org.diafon.inputmethod.Diafon"

    /// An output's input mode: "script" is ….universal, "stage:hu" is ….hu.
    static func id(_ output: String) -> String {
        base + "." + (output.hasPrefix("stage:") ? String(output.dropFirst(6)) : "universal")
    }
    /// An input mode's output, or nil when the mode is not one of Diafon's.
    static func output(_ id: String) -> String? {
        guard id.hasPrefix(base + ".") else { return nil }
        let mode = String(id.dropFirst(base.count + 1))
        if mode == "universal" { return "script" }
        return Prefs.spelled(mode) ? "stage:" + mode : nil
    }

    private static func source(_ id: String) -> TISInputSource? {
        let props = [kTISPropertyInputSourceID as String: id] as CFDictionary
        return (TISCreateInputSourceList(props, true)?.takeRetainedValue() as? [TISInputSource])?.first
    }
    private static func flag(_ s: TISInputSource, _ key: CFString) -> Bool {
        guard let p = TISGetInputSourceProperty(s, key) else { return false }
        return CFBooleanGetValue(Unmanaged<CFBoolean>.fromOpaque(p).takeUnretainedValue())
    }

    /// The output of the keyboard selected in the system; nil when it is not one of Diafon's.
    static var current: String? {
        guard let s = TISCopyCurrentKeyboardInputSource()?.takeRetainedValue(),
              let p = TISGetInputSourceProperty(s, kTISPropertyInputSourceID) else { return nil }
        return output(Unmanaged<CFString>.fromOpaque(p).takeUnretainedValue() as String)
    }

    /// Switch to an output's keyboard, making it one first. The settings follow at once;
    /// the system also tells the controller (setValue), which then finds nothing to change.
    static func select(_ output: String) {
        if output.hasPrefix("stage:") { Prefs.shared.language = String(output.dropFirst(6)) }
        else { Prefs.shared.output = "script" }
        guard let s = source(id(output)) else { return }
        if !flag(s, kTISPropertyInputSourceIsEnabled) { TISEnableInputSource(s) }
        TISSelectInputSource(s)
    }
}
