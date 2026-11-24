// The keyboards the system shows. Each output is an input mode of Diafon
// (tools/modes.py): Diafon itself, and one per language. The system's own
// list of input sources is the one record of which are on (System Settings →
// Keyboard → Input Sources): this file only reads which one is selected, and
// from the Mac's own layout where the letters sit. Diafon keeps no list and no setting.
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

    /// The output of the keyboard selected in the system; nil when it is not one of Diafon's.
    static var current: String? {
        guard let s = TISCopyCurrentKeyboardInputSource()?.takeRetainedValue(),
              let p = TISGetInputSourceProperty(s, kTISPropertyInputSourceID) else { return nil }
        return output(Unmanaged<CFString>.fromOpaque(p).takeUnretainedValue() as String)
    }

    // MARK: the letters' placement

    /// What a key of a layout types, unshifted, in small letters.
    private static func letter(_ s: TISInputSource, _ key: UInt16) -> String {
        guard let p = TISGetInputSourceProperty(s, kTISPropertyUnicodeKeyLayoutData) else { return "" }
        let data = Unmanaged<CFData>.fromOpaque(p).takeUnretainedValue() as Data
        var dead: UInt32 = 0, n = 0
        var chars = [UniChar](repeating: 0, count: 4)
        let err = data.withUnsafeBytes { raw -> OSStatus in
            UCKeyTranslate(raw.bindMemory(to: UCKeyboardLayout.self).baseAddress, key, UInt16(kUCKeyActionDown), 0, UInt32(LMGetKbdType()),
                           OptionBits(kUCKeyTranslateNoDeadKeysBit), &dead, 4, &n, &chars)
        }
        return err == noErr ? String(utf16CodeUnits: chars, count: n).lowercased() : ""
    }

    /// The layout under Diafon. An input method has none of its own, and the person's
    /// may move the digits (the tones) or put ö ü ó on letter keys, so Diafon types on
    /// the plain layout that places the 26 letters as theirs does: told by where q, z
    /// and s sit on the Latin layout they used last (a Hungarian or German one is
    /// QWERTZ, a French one AZERTY). No setting: the Mac's own keyboards decide.
    static var baseLayout: String {
        guard let s = TISCopyCurrentASCIICapableKeyboardLayoutInputSource()?.takeRetainedValue() else { return "com.apple.keylayout.ABC" }
        let q = letter(s, 12), z = letter(s, 6), sKey = letter(s, 1)
        if q == "a" { return "com.apple.keylayout.ABC-AZERTY" }
        if sKey == "o" { return "com.apple.keylayout.Dvorak" }
        if sKey == "r" { return "com.apple.keylayout.Colemak" }
        if z == "y" { return "com.apple.keylayout.ABC-QWERTZ" }
        return "com.apple.keylayout.ABC"
    }
}
