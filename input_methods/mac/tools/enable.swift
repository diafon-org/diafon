// Enable the Diafon input source and select it; disable the old Diaphone one where present.
//   swift tools/enable.swift           (or: make enable)
import Carbon

func sources(_ id: String) -> [TISInputSource] {
    let props = [kTISPropertyInputSourceID as String: id] as CFDictionary
    return (TISCreateInputSourceList(props, true)?.takeRetainedValue() as? [TISInputSource]) ?? []
}
// re-register the installed bundle, so the system drops a cached entry from an older
// Info.plist (a missing icon URL crashes the cursor badge in apps such as Teams)
let installed = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Input Methods/DiafonIM.app")
TISRegisterInputSource(installed as CFURL)
let diafon = sources("org.diafon.inputmethod.Diafon")
guard let src = diafon.first else {
    print("Diafon is not installed for this user (run make install first)"); exit(1)
}
for old in sources("org.diaphone.inputmethod.Diaphone") {
    TISDisableInputSource(old)
    print("old Diaphone input source disabled")
}
TISEnableInputSource(src)
TISSelectInputSource(src)
print("Diafon enabled and selected")
