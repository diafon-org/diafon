// The conversion window, for "Convert with Diafon…": the selected text, the
// source it was detected in (changeable), the target (the mode in use by
// default), and a live preview. Modal: the service waits for Convert or
// Cancel. SwiftUI, hosted in a window.
import Cocoa
import SwiftUI

final class ConvertModel: ObservableObject {
    let text: String
    let detected: [(String, Double)]
    @Published var source: String
    @Published var target: String
    init(_ text: String) {
        self.text = text
        let p = Prefs.shared
        let current = p.enabled ? p.output : "script"
        detected = Stages.detect(text, prefer: Prefs.shared.preferredSources)
        source = Stages.sourceFor(text, target: current, prefer: Prefs.shared.preferredSources)
        target = current
    }
    var result: String { Stages.convert(text, source, target, tones: Prefs.shared.tones) }
    var confidence: String {
        guard let top = detected.first else { return "" }
        let pct = Int((top.1 * 100).rounded())
        return top.0 == source ? "detected, \(pct)% of the letters read" : "detected: \(Modes.label(top.0))"
    }
}

struct ConvertView: View {
    @ObservedObject var model: ConvertModel
    let done: (Bool) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                picker("From", $model.source)
                Text(model.confidence).font(.caption).foregroundStyle(.secondary)
            }
            picker("To", $model.target)
            Divider()
            ScrollView {
                Text(model.result)
                    .font(.custom("Georgia", size: 15))
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(height: 120)
            .padding(8)
            .background(RoundedRectangle(cornerRadius: 6).fill(Color(nsColor: .textBackgroundColor)))
            .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color(nsColor: .separatorColor)))
            HStack {
                Text("\(model.text.count) characters").font(.caption).foregroundStyle(.secondary)
                Spacer()
                Button("Cancel") { done(false) }.keyboardShortcut(.cancelAction)
                Button("Convert") { done(true) }.keyboardShortcut(.defaultAction)
                    .disabled(model.source == model.target)
            }
        }
        .padding(20)
        .frame(width: 480)
    }

    private func picker(_ title: String, _ sel: Binding<String>) -> some View {
        HStack(spacing: 8) {
            Text(title).frame(width: 40, alignment: .trailing).foregroundStyle(.secondary)
            Picker("", selection: sel) {
                ForEach(Modes.all, id: \.0) { Text($0.1).tag($0.0) }
            }
            .labelsHidden()
            .frame(width: 220)
        }
    }
}

enum ConvertWindow {
    /// Show the window and wait; the converted text, or nil on Cancel.
    static func run(_ text: String) -> String? {
        let model = ConvertModel(text)
        var window: NSWindow!
        let view = ConvertView(model: model) { ok in NSApp.stopModal(withCode: ok ? .OK : .cancel) }
        let host = NSHostingController(rootView: view)
        window = NSWindow(contentViewController: host)
        window.styleMask = [.titled, .closable]
        window.title = "Convert with Diafon"
        window.isReleasedWhenClosed = false
        window.center()
        NSApp.activate(ignoringOtherApps: true)
        window.makeKeyAndOrderFront(nil)
        let code = NSApp.runModal(for: window)
        window.close()
        return code == .OK ? model.result : nil
    }
}
