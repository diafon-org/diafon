import SwiftUI

// MARK: - ProfileEditorView

/// Sheet for creating a new user profile or editing an existing one.
struct ProfileEditorView: View {
    @EnvironmentObject private var store: ProfileStore
    @Environment(\.dismiss) private var dismiss

    // Fixed at init time — nil means "create new".
    private let editingID: UUID?

    @State private var name: String
    /// Comma-separated modifier keys, e.g. "y, q, w, x".
    @State private var modifierText: String
    @State private var entries: [MappingEntry]

    // MARK: - Init

    init(existing: Profile?) {
        editingID     = existing?.id
        _name         = State(initialValue: existing?.name ?? "")
        _modifierText = State(initialValue: existing?.modifierKeys.joined(separator: ", ") ?? "")
        let pairs: [MappingEntry] = existing.map { p in
            p.mappings
                .map { MappingEntry(input: $0.key, output: $0.value) }
                .sorted { $0.input < $1.input }
        } ?? []
        _entries = State(initialValue: pairs)
    }

    // MARK: - Body

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Name")) {
                    TextField("Profile name", text: $name)
                        .autocorrectionDisabled()
                }

                Section(
                    header: Text("Modifier Keys"),
                    footer: Text("Comma-separated keys that trigger substitution when pressed, e.g. \"y, q, w, x\".")
                ) {
                    TextField("e.g. y, q, w, x", text: $modifierText)
                        .font(.system(.body, design: .monospaced))
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }

                Section(
                    header: Text("Mappings"),
                    footer: Text("Swipe left to delete a row.")
                ) {
                    ForEach($entries) { $entry in
                        HStack(spacing: 8) {
                            TextField("in", text: $entry.input)
                                .font(.system(.body, design: .monospaced))
                                .frame(width: 64)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                            Image(systemName: "arrow.right")
                                .foregroundColor(.secondary)
                                .font(.caption)
                            TextField("out", text: $entry.output)
                                .font(.system(.body, design: .monospaced))
                                .autocorrectionDisabled()
                        }
                    }
                    .onDelete { offsets in entries.remove(atOffsets: offsets) }

                    Button {
                        entries.append(MappingEntry())
                    } label: {
                        Label("Add Mapping", systemImage: "plus.circle")
                    }
                }
            }
            .navigationTitle(editingID == nil ? "New Profile" : "Edit Profile")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }
                        .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }

    // MARK: - Save

    private func save() {
        let modifiers = modifierText
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }

        var mappingsDict: [String: String] = [:]
        for entry in entries where !entry.input.isEmpty && !entry.output.isEmpty {
            mappingsDict[entry.input] = entry.output
        }

        // Only reuse the existing ID when it belongs to a real user profile.
        // If editingID points to a preset (or is nil), generate a fresh UUID so
        // that addUserProfile always gets a unique, non-preset ID.
        let isEditingUserProfile = editingID.map { id in
            store.userProfiles.contains { $0.id == id }
        } ?? false

        let profile = Profile(
            id: isEditingUserProfile ? editingID! : UUID(),
            name: name.trimmingCharacters(in: .whitespaces),
            isPreset: false,
            mappings: mappingsDict,
            modifierKeys: modifiers
        )

        if isEditingUserProfile {
            store.updateUserProfile(profile)
        } else {
            store.addUserProfile(profile)
        }
        dismiss()
    }
}

// MARK: - MappingEntry

/// Lightweight mutable row for the form.
struct MappingEntry: Identifiable {
    let id = UUID()
    var input: String = ""
    var output: String = ""
}

// MARK: - Preview

#Preview("New") {
    ProfileEditorView(existing: nil)
        .environmentObject(ProfileStore())
}

#Preview("Edit existing") {
    ProfileEditorView(existing: nil)
        .environmentObject(ProfileStore())
}
