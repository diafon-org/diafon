// Register the installed Diafon input method, enable its Universal mode and the
// mode of the first system language that has one, and select Universal; disable
// the old Diaphone source where present. The other modes are switched on in
// System Settings → Keyboard → Input Sources.
//   swift tools/enable.swift           (or: make enable)
import Carbon

let base = "org.diafon.inputmethod.Diafon"
func sources(_ id: String) -> [TISInputSource] {
    let props = [kTISPropertyInputSourceID as String: id] as CFDictionary
    return (TISCreateInputSourceList(props, true)?.takeRetainedValue() as? [TISInputSource]) ?? []
}
func id(_ s: TISInputSource) -> String {
    guard let p = TISGetInputSourceProperty(s, kTISPropertyInputSourceID) else { return "" }
    return Unmanaged<CFString>.fromOpaque(p).takeUnretainedValue() as String
}
// re-register the installed bundle, so the system reads its modes and drops a cached
// entry from an older Info.plist (a missing icon URL crashes the cursor badge in apps such as Teams)
let installed = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Input Methods/DiafonIM.app")
TISRegisterInputSource(installed as CFURL)
let all = ((TISCreateInputSourceList(nil, true)?.takeRetainedValue() as? [TISInputSource]) ?? []).filter { id($0).hasPrefix(base) }
print("registered: " + all.map(id).sorted().joined(separator: ", "))
guard let universal = sources(base + ".universal").first else {
    print("Diafon is not installed for this user (run make install first)"); exit(1)
}
for old in sources("org.diaphone.inputmethod.Diaphone") {
    TISDisableInputSource(old)
    print("old Diaphone input source disabled")
}
if let parent = sources(base).first { TISEnableInputSource(parent) }
TISEnableInputSource(universal)
// the language Diafon was last set to, then the system's languages
let saved = UserDefaults(suiteName: base)?.string(forKey: "language").map { [$0] } ?? []
for l in saved + Locale.preferredLanguages {
    if let mode = sources(base + "." + String(l.prefix(2)).lowercased()).first {
        TISEnableInputSource(mode)
        print("enabled: " + id(mode))
        break
    }
}
TISSelectInputSource(universal)
print("Diafon enabled and selected")
