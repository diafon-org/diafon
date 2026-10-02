// Input-method bootstrap: register the IMK server and the text services, run.
// The system launches this app when the user enables the input source;
// DiafonInputController handles every keystroke from then on.
import Cocoa
import InputMethodKit

// Any uncaught exception is written to ~/Library/Logs/Diafon/crash.log before the
// process dies (the system writes no report for an input method), so a crash can be read.
NSSetUncaughtExceptionHandler { e in
    let dir = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Diafon")
    try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    let text = "\(Date())  \(e.name.rawValue): \(e.reason ?? "")\n" + e.callStackSymbols.joined(separator: "\n") + "\n\n"
    if let h = try? FileHandle(forWritingTo: dir.appendingPathComponent("crash.log")) {
        h.seekToEndOfFile(); h.write(text.data(using: .utf8)!); h.closeFile()
    } else {
        try? text.write(to: dir.appendingPathComponent("crash.log"), atomically: true, encoding: .utf8)
    }
}

let connectionName = (Bundle.main.infoDictionary?["InputMethodConnectionName"] as? String) ?? "Diafon_1_Connection"
let server = IMKServer(name: connectionName, bundleIdentifier: Bundle.main.bundleIdentifier)
// the candidate window (the one the CJK input methods use): the pending
// segment in every spelling, opened with Tab or the down arrow. Created on
// first use: its mere existence involves the client app's candidate UI
// (TextInputUIMacHelper), which some apps handle badly.
var candidatePanelIfAny: IMKCandidates? = nil
func candidatePanelMake() -> IMKCandidates {
    if candidatePanelIfAny == nil { candidatePanelIfAny = IMKCandidates(server: server, panelType: kIMKSingleColumnScrollingCandidatePanel) }
    return candidatePanelIfAny!
}
let services = Services()
NSApplication.shared.servicesProvider = services
NSUpdateDynamicServices()
NSApplication.shared.run()
