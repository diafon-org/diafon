// Input-method bootstrap: register the IMK server and run. The system launches this app when the
// user enables the input source; DiaphoneInputController handles every keystroke from then on.
import Cocoa
import InputMethodKit

let connectionName = (Bundle.main.infoDictionary?["InputMethodConnectionName"] as? String) ?? "Diaphone_1_Connection"
let server = IMKServer(name: connectionName, bundleIdentifier: Bundle.main.bundleIdentifier)
NSApplication.shared.run()
