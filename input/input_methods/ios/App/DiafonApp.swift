// The container app: how to turn the keyboard on, a field to try it in, a
// converter for text in any spelling, and the how-to. The keyboard's own
// settings are in the keyboard (the gear on its strip): without full access
// the two share no storage, and Diafon asks for none.
import SwiftUI

@main
struct DiafonApp: App {
    var body: some Scene { WindowGroup { ContentView() } }
}

struct ContentView: View {
    var body: some View {
        TabView {
            SetupView().tabItem { Label("Setup", systemImage: "keyboard") }
            ConvertView().tabItem { Label("Convert", systemImage: "arrow.left.arrow.right") }
            HowToView().tabItem { Label("How to", systemImage: "questionmark.circle") }
        }
        .tint(Color(red: 0x0E / 255, green: 0x7C / 255, blue: 0x86 / 255))
    }
}

struct SetupView: View {
    @State private var trial = ""
    var body: some View {
        NavigationStack {
            Form {
                Section("Turn it on, once") {
                    Text("1. Settings → General → Keyboard → Keyboards → Add New Keyboard… → Diafon.")
                    Text("2. In any text field, hold the globe (or the keyboard switcher below the keys) and pick Diafon.")
                    Text("Diafon does not ask for full access: no network, nothing stored but its settings.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Button("Open Settings") {
                        if let url = URL(string: UIApplication.openSettingsURLString) { UIApplication.shared.open(url) }
                    }
                }
                Section("Try it") {
                    TextField("type sy cy aq", text: $trial, axis: .vertical)
                        .font(.custom("DiafonSerif-Regular", size: 22, relativeTo: .title2))
                        .lineLimit(3...8)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        .accessibilityIdentifier("trial")
                }
                Section("Each language's spelling, from the same keys") {
                    ForEach(Prefs.languages, id: \.0) { code, name in
                        if let st = Diafon.shared.stages[code], !st.sample.isEmpty {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("\(name) · \(code)").font(.caption).foregroundStyle(.secondary)
                                Text(Diafon.shared.keys(for: st.sample)).font(.system(.body, design: .monospaced))
                                Text(Diafon.shared.convert(st.sample, "script", "stage:" + code)).font(.custom("DiafonSerif-Regular", size: 19))
                            }
                        }
                    }
                }
            }
            .navigationTitle("Diafon")
        }
    }
}

struct ConvertView: View {
    @State private var text = ""
    @State private var source = "auto"
    @State private var target = "script"
    private var outputs: [(String, String)] { [("script", "Diafon")] + Prefs.languages.map { ("stage:" + $0.0, $0.1) } }
    private var detected: String { Diafon.shared.sourceFor(text, target: target, prefer: Prefs.shared.preferredSources) }
    private var result: String { text.isEmpty ? "" : Diafon.shared.convert(text, source == "auto" ? detected : source, target) }

    var body: some View {
        NavigationStack {
            Form {
                Section("Text, in any spelling") {
                    TextField("paste or type", text: $text, axis: .vertical).lineLimit(3...10)
                }
                Section {
                    Picker("From", selection: $source) {
                        Text(text.isEmpty ? "Detect" : "Detect (\(label(detected)))").tag("auto")
                        ForEach(outputs, id: \.0) { Text($0.1).tag($0.0) }
                    }
                    Picker("To", selection: $target) {
                        ForEach(outputs, id: \.0) { Text($0.1).tag($0.0) }
                    }
                }
                Section("Result") {
                    Text(result).font(.custom("DiafonSerif-Regular", size: 20)).textSelection(.enabled)
                    Button("Copy") { UIPasteboard.general.string = result }.disabled(result.isEmpty)
                }
            }
            .navigationTitle("Convert")
        }
    }

    private func label(_ out: String) -> String { outputs.first { $0.0 == out }?.1 ?? out }
}

struct HowToView: View {
    var body: some View {
        NavigationStack {
            List {
                Text("Twenty-four keys are Diafon's letters. The other two, y and q, are not letters: typed after a letter, they put its mark on. sy → ș, tq → ṭ, uy → ü, aq → á.")
                Text("After a consonant y is the anchor and q the dot. After a vowel y is the double dot, q makes it long, yq is both, and qy is the dot below.")
                Text("A doubled consonant is the long one. For a plain y or q after a letter, type it twice.")
                Text("The letter being typed stays provisional until the next key settles it.")
                Text("Hold the space bar to switch between Diafon, your languages' spellings and plain keys. Hold the Diafon key for the settings.")
                Text("A digit after a syllable is its tone, which the Diafon fonts draw above it. Turn tones off in the settings to leave them out.")
                Text("Select text in any spelling and the strip offers to convert it to the spelling in use.")
            }
            .navigationTitle("How to")
        }
    }
}
