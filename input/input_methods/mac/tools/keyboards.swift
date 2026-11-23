// Switch on the Diafon keyboards the quick list names, and the others off; print what the system then holds.
//   swift tools/keyboards.swift
import Carbon
import Foundation

let base = "org.diafon.inputmethod.Diafon"
func str(_ s: TISInputSource, _ k: CFString) -> String {
    guard let p = TISGetInputSourceProperty(s, k) else { return "" }
    return Unmanaged<CFString>.fromOpaque(p).takeUnretainedValue() as String
}
func on(_ s: TISInputSource) -> Bool {
    guard let p = TISGetInputSourceProperty(s, kTISPropertyInputSourceIsEnabled) else { return false }
    return CFBooleanGetValue(Unmanaged<CFBoolean>.fromOpaque(p).takeUnretainedValue())
}
func diafon() -> [TISInputSource] {
    ((TISCreateInputSourceList(nil, true)?.takeRetainedValue() as? [TISInputSource]) ?? [])
        .filter { str($0, kTISPropertyInputSourceID).hasPrefix(base) }
}
let installed = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Input Methods/DiafonIM.app")
print("register:", TISRegisterInputSource(installed as CFURL))
let quick = UserDefaults(suiteName: base)?.stringArray(forKey: "quickLanguages") ?? []
let wanted = Set([base, base + ".universal"] + quick.map { base + "." + $0 })
for s in diafon() {
    let id = str(s, kTISPropertyInputSourceID)
    if wanted.contains(id) { print("enable ", id, TISEnableInputSource(s)) }
    else if on(s) { print("disable", id, TISDisableInputSource(s)) }
}
for s in diafon() { print(on(s) ? "on " : "off", str(s, kTISPropertyInputSourceID)) }
