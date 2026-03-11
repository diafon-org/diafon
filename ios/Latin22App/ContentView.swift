import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var store: ProfileStore

    private let steps = [
        "Open the Settings app.",
        "Go to General → Keyboard → Keyboards.",
        "Tap Add New Keyboard…",
        "Select Latin22 from the list.",
        "While typing anywhere, tap the 🌐 key to switch to Latin22.",
        "Tap 🌐 again to switch back to your default keyboard.",
    ]

    // MARK: - Display types

    private struct MappingRow: Identifiable {
        let id: String          // lowercase input key
        let input: String       // e.g. "ny"
        let inputUpper: String? // e.g. "Ny", nil if variant absent
        let output: String      // e.g. "n̗"
        let outputUpper: String?
    }

    private struct MappingGroup: Identifiable {
        let id: String          // modifier char
        let rows: [MappingRow]
    }

    // MARK: - Groups derived from active profile

    private var groups: [MappingGroup] {
        let profile = store.activeProfile
        let modifiers = profile.modifierKeys

        var byModifier: [String: [MappingRow]] = [:]
        for (input, output) in profile.mappings {
            guard let firstChar = input.first, firstChar.isLowercase || firstChar.isNumber,
                  let lastChar  = input.last.map(String.init),
                  modifiers.contains(lastChar)
            else { continue }

            let capitalised = String(input.prefix(1).uppercased() + input.dropFirst())
            let upper       = profile.mappings[capitalised]
            let row = MappingRow(
                id: input,
                input: input,
                inputUpper: upper != nil ? capitalised : nil,
                output: output,
                outputUpper: upper
            )
            byModifier[lastChar, default: []].append(row)
        }

        return modifiers.compactMap { mod in
            guard let rows = byModifier[mod], !rows.isEmpty else { return nil }
            return MappingGroup(id: mod, rows: rows.sorted { $0.input < $1.input })
        }
    }

    // MARK: - Body

    var body: some View {
        NavigationView {
            List {
                Section(header: Text("Setup")) {
                    ForEach(Array(steps.enumerated()), id: \.offset) { i, step in
                        HStack(alignment: .top, spacing: 12) {
                            Text("\(i + 1)")
                                .font(.caption.bold())
                                .foregroundColor(.secondary)
                                .frame(width: 18, alignment: .center)
                            Text(step)
                                .font(.body)
                        }
                        .padding(.vertical, 2)
                    }
                }

                ForEach(groups) { group in
                    Section(header: Text("modifier: \(group.id)")) {
                        ForEach(group.rows) { row in
                            HStack(spacing: 8) {
                                // Input column
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(row.input)
                                        .font(.system(.body, design: .monospaced))
                                    if let up = row.inputUpper {
                                        Text(up)
                                            .font(.system(.caption, design: .monospaced))
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .frame(width: 44, alignment: .leading)

                                Image(systemName: "arrow.right")
                                    .foregroundColor(.secondary)
                                    .font(.caption)

                                // Output column
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(row.output)
                                        .font(.system(.body, design: .monospaced))
                                    if let up = row.outputUpper {
                                        Text(up)
                                            .font(.system(.caption, design: .monospaced))
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                    }
                }

                Section(header: Text("How it works")) {
                    Text("Type any sequence — the substitution fires the moment the modifier key is pressed. Press the modifier twice to revert: ny+y → \"ny\".")
                        .font(.callout)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
            }
            .navigationTitle(store.activeProfile.name)
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(ProfileStore())
}


