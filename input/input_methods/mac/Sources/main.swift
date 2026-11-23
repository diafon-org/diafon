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

// `DiafonIM --check`: the bundle's own alphabet and typing, loaded and used once; no server.
if CommandLine.arguments.contains("--check") {
    let d = Diafon.shared
    print(d.failure.map { "FAILED: \($0)" } ?? "\(d.render("sy cy aq"))  ·  alphabet \(d.version), typing \(d.typing), \(Prefs.languages.count) languages")
    exit(d.failure == nil ? 0 : 1)
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
// the keyboards the system shows follow the quick list (Keyboards.swift): once now, then on every change
DispatchQueue.main.asyncAfter(deadline: .now() + 1) { Keyboards.sync() }
NotificationCenter.default.addObserver(forName: Prefs.changed, object: nil, queue: .main) { _ in Keyboards.sync() }
let services = Services()
NSApplication.shared.servicesProvider = services
NSUpdateDynamicServices()
NSApplication.shared.run()
