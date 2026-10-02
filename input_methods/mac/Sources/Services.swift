// Convert a selection, in any app, through the Services menu (also in the
// context menu of a selection):
//   Convert with Diafon (⇧⌘D)   from the source detected in the text (the
//                               mode in use preferred) to the mode in use
//   Convert with Diafon…        a window: the source, detected and
//                               changeable, the target, a preview
import Cocoa

@objc final class Services: NSObject {
    @objc func convertSelection(_ pboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        guard let text = selected(pboard, error) else { return }
        let p = Prefs.shared
        let target = p.enabled ? p.output : "script"
        let source = Stages.sourceFor(text, target: target, prefer: Prefs.shared.preferredSources)
        write(pboard, Stages.convert(text, source, target, tones: p.tones))
    }

    @objc func convertSelectionChoosing(_ pboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        guard let text = selected(pboard, error) else { return }
        if let result = ConvertWindow.run(text) { write(pboard, result) }
        else { error.pointee = "Diafon: conversion cancelled" }
    }

    private func selected(_ pboard: NSPasteboard, _ error: AutoreleasingUnsafeMutablePointer<NSString>) -> String? {
        guard let text = pboard.string(forType: .string), !text.isEmpty else {
            error.pointee = "Diafon: no text selected"
            return nil
        }
        return text
    }

    private func write(_ pboard: NSPasteboard, _ text: String) {
        pboard.clearContents()
        pboard.setString(text, forType: .string)
    }
}

/// The names every screen gives the sources and targets.
enum Modes {
    static let all: [(String, String)] = [("transport", "As typed (input form)"), ("script", "Universal")]
        + Prefs.languages.map { code, name in ("stage:\(code)", "\(Locale(identifier: code).localizedString(forLanguageCode: code) ?? name) (\(code))") }
    static func label(_ mode: String) -> String { all.first { $0.0 == mode }?.1 ?? mode }
}
