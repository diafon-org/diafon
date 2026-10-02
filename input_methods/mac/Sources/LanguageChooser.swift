// The language chooser, in SwiftUI (the look of the system's own settings),
// two panes. Left: every language with a spelling, filtered as you type by
// native name, English name or code; the box beside each keeps it on the
// quick list, Return or a double click picks it (turns conversion on in that
// spelling). Right: the quick list itself, the languages the menu shows and
// the Shift taps cycle through, in the order you give them there (drag, or
// the buttons). Opened with ⇧Space, from the menu's "Other language…" and
// from Setup. The model holds every action, so it can be driven without
// the window.
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
    @Published var quick: [String] = Prefs.shared.quickLanguages
    @Published var leftSelection: String?
    @Published var rightSelection: String?
    var onPick: (() -> Void)?

    var rows: [Lang] {
        let q = query.trimmingCharacters(in: .whitespaces).lowercased()
        return q.isEmpty ? Self.all
            : Self.all.filter { $0.code.hasPrefix(q) || $0.native.lowercased().contains(q) || $0.name.lowercased().contains(q) }
    }
    var quickLangs: [Lang] { quick.compactMap { c in Self.all.first { $0.code == c } } }
    var long: Bool { quick.count > Prefs.quickComfort }

    func reload() {
        quick = Prefs.shared.quickLanguages
        if leftSelection == nil { leftSelection = Prefs.shared.language }
    }
    func isQuick(_ code: String) -> Bool { quick.contains(code) }
    func setQuick(_ code: String, _ on: Bool) {
        Prefs.shared.setQuick(code, on)
        quick = Prefs.shared.quickLanguages
    }
    func move(from: IndexSet, to: Int) {
        quick.move(fromOffsets: from, toOffset: to)
        Prefs.shared.quickLanguages = quick
    }
    func shift(_ d: Int) {
        guard let sel = rightSelection, let i = quick.firstIndex(of: sel), i + d >= 0, i + d < quick.count else { return }
        quick.swapAt(i, i + d)
        Prefs.shared.quickLanguages = quick
    }
    func remove() {
        guard let sel = rightSelection else { return }
        setQuick(sel, false)
        rightSelection = nil
    }
    func pick(_ code: String?) {
        guard let code = code ?? leftSelection, rows.contains(where: { $0.code == code }) else { return }   // a visible row only
        Prefs.shared.language = code                        // on the quick list too
        Prefs.shared.enabled = true
        quick = Prefs.shared.quickLanguages
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
    private let hintText = "Return picks a language. The box keeps it on the quick list: the menu, and the cycle of quick Shift taps, in the order on the right."
    private var longText: String { "More than \(Prefs.quickComfort) languages on the quick list make the Shift cycle long: every tap has further to go. Fewer is quicker." }

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
                                Toggle("", isOn: Binding(get: { model.isQuick(l.code) }, set: { model.setQuick(l.code, $0) }))
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
                    label("Quick list")
                    List(selection: $model.rightSelection) {
                        ForEach(model.quickLangs) { l in
                            HStack(spacing: 8) {
                                Text("\(model.quick.firstIndex(of: l.code).map { $0 + 1 } ?? 0).")
                                    .monospacedDigit().foregroundStyle(.secondary).frame(width: 18, alignment: .trailing)
                                row(l)
                            }
                            .tag(l.code)
                            .contentShape(Rectangle())
                            .onTapGesture(count: 2) { model.pick(l.code) }
                        }
                        .onMove { model.move(from: $0, to: $1) }
                    }
                    .listStyle(.bordered(alternatesRowBackgrounds: true))
                    .frame(width: 250, height: 290 + 8 + 22)
                    HStack(spacing: 6) {
                        Button { model.remove() } label: { Image(systemName: "minus") }
                            .disabled(model.rightSelection == nil)
                        Button { model.shift(-1) } label: { Image(systemName: "chevron.up") }
                            .disabled(model.rightSelection == nil || model.quick.first == model.rightSelection)
                        Button { model.shift(1) } label: { Image(systemName: "chevron.down") }
                            .disabled(model.rightSelection == nil || model.quick.last == model.rightSelection)
                        Spacer()
                        Text("Drag to reorder").font(.caption).foregroundStyle(.tertiary)
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
    private func row(_ l: Lang) -> some View {
        HStack(spacing: 6) {
            Text(l.native)
            Text("·").foregroundStyle(.tertiary)
            Text(l.short).foregroundStyle(.secondary)
            Text("·").foregroundStyle(.tertiary)
            Text(l.code).font(.system(.body, design: .monospaced)).foregroundStyle(.secondary)
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
        w.title = "Language-specific spellings"
        w.isReleasedWhenClosed = false
        window = w
    }
}
