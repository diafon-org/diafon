// The language chooser, in SwiftUI (the look of the system's own settings),
// two panes. Left: every language with a spelling, filtered as you type by
// native name, English name or code; the box beside each makes it a keyboard
// of its own (Diafon – Magyar), Return or a double click also switches to
// it. Right: the keyboards as they are now, Diafon first. Both read and
// change the system's own input sources (Keyboards.swift), so this window
// and System Settings always agree; the system orders them in its menu.
// Opened from the menu's "Keyboards…". The model holds every action, so it
// can be driven without the window.
import Cocoa
import SwiftUI

struct Lang: Identifiable, Hashable {
    let code: String, native: String, name: String
    var id: String { code }
    var short: String { name.replacingOccurrences(of: " spelling", with: "") }
}

final class ChooserModel: ObservableObject {
    static let all: [Lang] = Prefs.languages.map { code, name in
        Lang(code: code, native: Locale(identifier: code).localizedString(forLanguageCode: code) ?? name, name: name)
    }
    @Published var query = ""
    @Published var keyboards: [String] = Keyboards.languages
    @Published var leftSelection: String?
    @Published var rightSelection: String?
    var onPick: (() -> Void)?

    var rows: [Lang] {
        let q = query.trimmingCharacters(in: .whitespaces).lowercased()
        return q.isEmpty ? Self.all
            : Self.all.filter { $0.code.hasPrefix(q) || $0.native.lowercased().contains(q) || $0.name.lowercased().contains(q) }
    }
    var keyboardLangs: [Lang] { Self.all.filter { keyboards.contains($0.code) } }
    var long: Bool { keyboards.count > Prefs.quickComfort }

    func reload() {
        keyboards = Keyboards.languages
        if leftSelection == nil { leftSelection = Prefs.shared.language }
    }
    func isKeyboard(_ code: String) -> Bool { keyboards.contains(code) }
    func setKeyboard(_ code: String, _ on: Bool) {
        Keyboards.set(code, on)
        keyboards = Keyboards.languages
    }
    func remove() {
        guard let sel = rightSelection else { return }
        setKeyboard(sel, false)
        rightSelection = nil
    }
    func pick(_ code: String?) {
        guard let code = code ?? leftSelection, rows.contains(where: { $0.code == code }) else { return }   // a visible row only
        Keyboards.select("stage:" + code)                   // a keyboard from now on, and the one in use
        keyboards = Keyboards.languages
        onPick?()
    }
    func moveLeft(_ d: Int) {
        let r = rows
        guard !r.isEmpty else { return }
        let i = r.firstIndex { $0.code == leftSelection } ?? -1
        leftSelection = r[min(max(i + d, 0), r.count - 1)].code
    }
}

struct LanguageChooserView: View {
    @ObservedObject var model: ChooserModel
    private let hintText = "The box makes a language one of your keyboards: Diafon – Magyar and the like, switched as any keyboard. Return switches to it now."
    private var longText: String { "More than \(Prefs.quickComfort) keyboards make switching long. Fewer is quicker." }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    label("All languages")
                    TextField("Language name or code", text: $model.query)
                        .textFieldStyle(.roundedBorder)
                        .onSubmit { model.pick(nil) }
                    List(selection: $model.leftSelection) {
                        ForEach(model.rows) { l in
                            HStack(spacing: 8) {
                                Toggle("", isOn: Binding(get: { model.isKeyboard(l.code) }, set: { model.setKeyboard(l.code, $0) }))
                                    .toggleStyle(.checkbox).labelsHidden()
                                row(l)
                            }
                            .tag(l.code)
                            .contentShape(Rectangle())
                            .onTapGesture(count: 2) { model.pick(l.code) }
                        }
                    }
                    .listStyle(.bordered(alternatesRowBackgrounds: true))
                    .frame(width: 320, height: 290)
                }
                VStack(alignment: .leading, spacing: 8) {
                    label("Your keyboards")
                    List(selection: $model.rightSelection) {
                        row(native: "Diafon", name: "the script", code: "").foregroundStyle(.secondary)
                        ForEach(model.keyboardLangs) { l in
                            row(l)
                                .tag(l.code)
                                .contentShape(Rectangle())
                                .onTapGesture(count: 2) { model.pick(l.code) }
                        }
                    }
                    .listStyle(.bordered(alternatesRowBackgrounds: true))
                    .frame(width: 250, height: 290 + 8 + 22)
                    HStack(spacing: 6) {
                        Button { model.remove() } label: { Image(systemName: "minus") }
                            .disabled(model.rightSelection == nil)
                        Spacer()
                    }
                    .controlSize(.small)
                }
            }
            Text(model.long ? longText : hintText)
                .font(.caption)
                .foregroundStyle(model.long ? Color(red: 0.69, green: 0.25, blue: 0.25) : Color.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(20)
        .frame(width: 630)
    }

    private func label(_ s: String) -> some View {
        Text(s.uppercased()).font(.system(size: 10, weight: .semibold, design: .monospaced)).foregroundStyle(.secondary)
    }
    private func row(_ l: Lang) -> some View { row(native: l.native, name: l.short, code: l.code) }
    private func row(native: String, name: String, code: String) -> some View {
        HStack(spacing: 6) {
            Text(native)
            Text("·").foregroundStyle(.tertiary)
            Text(name).foregroundStyle(.secondary)
            if !code.isEmpty {
                Text("·").foregroundStyle(.tertiary)
                Text(code).font(.system(.body, design: .monospaced)).foregroundStyle(.secondary)
            }
        }
        .lineLimit(1)
    }
}

final class LanguageChooser {
    static let shared = LanguageChooser()
    let model = ChooserModel()
    private var window: NSWindow?

    func show() {
        if window == nil { build() }
        model.query = ""
        model.reload()
        NSApp.activate(ignoringOtherApps: true)
        window?.center()
        window?.makeKeyAndOrderFront(nil)
    }

    private func build() {
        model.onPick = { [weak self] in self?.window?.close() }
        let host = NSHostingController(rootView: LanguageChooserView(model: model))
        let w = NSWindow(contentViewController: host)
        w.styleMask = [.titled, .closable]
        w.title = "Diafon keyboards"
        w.isReleasedWhenClosed = false
        window = w
    }
}
