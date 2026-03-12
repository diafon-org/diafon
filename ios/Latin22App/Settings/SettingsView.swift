import SwiftUI

// MARK: - SettingsView

struct SettingsView: View {
    @EnvironmentObject private var store: ProfileStore

    var body: some View {
        NavigationView {
            List {
                ForEach(store.allLanguages) { lang in
                    languageSection(for: lang)
                }

                Section("About") {
                    Text("Enable the layers you are comfortable with. Higher layers add more shortcuts; when two layers define the same sequence, the higher level wins. Start with layer 1 and work your way up.")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                        .padding(.vertical, 2)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
        }
    }

    @ViewBuilder
    private func languageSection(for lang: Language) -> some View {
        let isActive = store.activeLanguageID == lang.id
        Section {
            // Language selection row
            Button {
                store.activateLanguage(lang.id)
            } label: {
                HStack(spacing: 12) {
                    Image(systemName: "globe")
                        .foregroundStyle(isActive ? Color.accentColor : .secondary)
                    Text(lang.name)
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Spacer()
                    Image(systemName: isActive ? "checkmark.circle.fill" : "circle")
                        .foregroundStyle(isActive ? Color.accentColor : .secondary)
                }
            }
            .buttonStyle(.plain)

            // Layer toggles, shown only for the selected language
            if isActive {
                ForEach(lang.layers.sorted { $0.level < $1.level }) { layer in
                    LayerRow(layer: layer)
                }
            }
        }
    }
}

// MARK: - LayerRow

private struct LayerRow: View {
    @EnvironmentObject private var store: ProfileStore
    let layer: Layer

    var body: some View {
        HStack(alignment: .top, spacing: 14) {
            Text("\(layer.level)")
                .font(.headline)
                .foregroundStyle(isActive ? .white : Color.accentColor)
                .frame(width: 28, height: 28)
                .background(isActive ? Color.accentColor : Color.clear)
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.accentColor, lineWidth: 1.5)
                )
            VStack(alignment: .leading, spacing: 6) {
                Text(layer.name).font(.body.bold())
                mappingPairs
            }
            Spacer()
            Toggle("", isOn: activeBinding)
                .labelsHidden()
        }
        .padding(.vertical, 4)
    }

    private var isActive: Bool {
        store.activeLayerIDs.contains(layer.id)
    }

    private var activeBinding: Binding<Bool> {
        Binding(
            get: { store.activeLayerIDs.contains(layer.id) },
            set: { store.setLayer(layer.id, active: $0) }
        )
    }

    /// Compact list of lowercase input→output pairs rendered as a flowing caption.
    private var mappingPairs: some View {
        let pairs = layer.mappings
            .filter { $0.key == $0.key.lowercased() }
            .sorted { $0.key < $1.key }
            .map    { "\($0.key)→\($0.value)" }
            .joined(separator: "  ")
        return Text(pairs)
            .font(.system(.caption, design: .monospaced))
            .foregroundStyle(.secondary)
            .lineSpacing(3)
    }
}

// MARK: - Preview

#Preview {
    SettingsView()
        .environmentObject(ProfileStore())
}

