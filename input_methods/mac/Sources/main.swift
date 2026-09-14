// Input-method bootstrap: register the IMK server and the text services, run.
// The system launches this app when the user enables the input source;
// DiafonInputController handles every keystroke from then on.
import Cocoa
import InputMethodKit

let connectionName = (Bundle.main.infoDictionary?["InputMethodConnectionName"] as? String) ?? "Diafon_1_Connection"
let server = IMKServer(name: connectionName, bundleIdentifier: Bundle.main.bundleIdentifier)
let services = Services()
NSApplication.shared.servicesProvider = services
NSUpdateDynamicServices()
NSApplication.shared.run()
