// Convert a selection: text typed with any keyboard, selected in any app,
// converted in place through the Services menu (or its shortcut), in the
// current output.
import Cocoa

@objc final class Services: NSObject {
    @objc func convertSelection(_ pboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        convert(pboard, Prefs.shared.renderer(), error: error)
    }

    private func convert(_ pboard: NSPasteboard, _ render: (String) -> String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        guard let text = pboard.string(forType: .string), !text.isEmpty else {
            error.pointee = "Diafon: no text selected"
            return
        }
        pboard.clearContents()
        pboard.setString(render(text), forType: .string)
    }
}
