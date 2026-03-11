import SwiftUI

// MARK: - SettingsView

struct SettingsView: View {
    @EnvironmentObject private var store: ProfileStore
    @State private var showingNewProfileEditor = false
    @State private var profileToEdit: Profile? = nil

    var body: some View {
        NavigationView {
            List {
                Section(header: Text("Presets")) {
                    ForEach(Profile.presets) { profile in
                        ProfileRow(profile: profile, isActive: store.activeProfileID == profile.id)
                            .contentShape(Rectangle())
                            .onTapGesture { store.activate(profile) }
                    }
                }

                Section(header: Text("My Profiles")) {
                    ForEach(store.userProfiles) { profile in
                        ProfileRow(profile: profile, isActive: store.activeProfileID == profile.id)
                            .contentShape(Rectangle())
                            .onTapGesture { store.activate(profile) }
                            .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                                Button(role: .destructive) {
                                    store.deleteUserProfile(profile)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                                Button {
                                    profileToEdit = profile
                                } label: {
                                    Label("Edit", systemImage: "pencil")
                                }
                                .tint(.blue)
                            }
                    }

                    Button {
                        showingNewProfileEditor = true
                    } label: {
                        Label("New Profile…", systemImage: "plus.circle")
                    }
                }
            }
            .navigationTitle("Profiles")
            .navigationBarTitleDisplayMode(.large)
            .sheet(isPresented: $showingNewProfileEditor) {
                ProfileEditorView(existing: nil)
                    .environmentObject(store)
            }
            .sheet(item: $profileToEdit) { profile in
                ProfileEditorView(existing: profile)
                    .environmentObject(store)
            }
        }
    }
}

// MARK: - ProfileRow

private struct ProfileRow: View {
    let profile: Profile
    let isActive: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(profile.name)
                    .font(.body)
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Spacer()
            if isActive {
                Image(systemName: "checkmark")
                    .foregroundColor(.accentColor)
                    .fontWeight(.semibold)
            }
        }
        .padding(.vertical, 2)
    }

    private var subtitle: String {
        // Count only lowercase/numeric-first keys — these are the canonical sequences.
        let seqCount = profile.mappings.keys.filter {
            $0.first?.isLowercase == true || $0.first?.isNumber == true
        }.count
        let mods = profile.modifierKeys.joined(separator: ", ")
        return "\(seqCount) sequence\(seqCount == 1 ? "" : "s") · modifiers: \(mods)"
    }
}

// MARK: - Preview

#Preview {
    SettingsView()
        .environmentObject(ProfileStore())
}
