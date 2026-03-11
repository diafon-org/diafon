import Cocoa
import InputMethodKit

// IMKServer must be created before the run loop starts.
// The bundle identifier is used to match the ComponentInputModeDict in Info.plist.
let server = IMKServer(
    name: Bundle.main.bundleIdentifier! + "_Connection",
    bundleIdentifier: Bundle.main.bundleIdentifier!
)

NSApplication.shared.run()
