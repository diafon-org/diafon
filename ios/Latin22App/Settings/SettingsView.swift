import SwiftUI

// MARK: - SettingsView

struct SettingsView: View {
    @EnvironmentObject private var store: ProfileStore

    /// Language groups — extend this array to add more languages.
    private let languages: [LanguageLevel] = [
        LanguageLevel(
            language: "Hungarian",
            levels: [
                LevelInfo(
                    profile: .hungarianVowels,
                    number: 1,
                    name: "Accented vowels",
                    description: "Covers the full Hungarian vowel set: á é í ó ú ö ü ő ű.\nUse q, w, x as modifiers after a vowel."
                ),
                LevelInfo(
                    profile: .hungarianFull,
                    number: 2,
                    name: "+ Consonant digraphs",
                    description: "Adds ny, ly, ty, sz, zs, cs, dz, dzs and variants.\nUse y, w, x after a consonant."
                ),
                LevelInfo(
                    profile: .hungarianDoubled,
                    number: 3,
                    name: "+ Geminate consonants",
                    description: "Adds long (geminate) consonants.\nq geminates any consonant; x palatises and geminates."
                ),
            ]
        )
    ]

    var body: some View {
        NavigationView {
            List {
                ForEach(languages) { lang in
                    Section(lang.language) {
                        ForEach(lang.levels) { level in
                            LevelRow(level: level, isActive: store.activeProfileID == level.profile.id)
                                .contentShape(Rectangle())
                                .onTapGesture { store.activate(level.profile) }
                        }
                    }
                }

                Section("Note") {
                    Text("Each level includes everything from the levels below it. Start at level 1 and move up as you get comfortable.")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                        .padding(.vertical, 2)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - Models

private struct LanguageLevel: Identifiable {
    let language: String
    let levels: [LevelInfo]
    var id: String { language }
}

private struct LevelInfo: Identifiable {
    let profile: Profile
    let number: Int
    let name: String
    let description: String
    var id: String { profile.id.uuidString }
}

// MARK: - LevelRow

private struct LevelRow: View {
    let level: LevelInfo
    let isActive: Bool

    var body: some View {
        HStack(alignment: .top, spacing: 14) {
            Text("\(level.number)")
                .font(.headline)
                .foregroundStyle(isActive ? Color.white : Color.accentColor)
                .frame(width: 28, height: 28)
                .background(isActive ? Color.accentColor : Color.clear)
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color.accentColor, lineWidth: 1.5))
            VStack(alignment: .leading, spacing: 4) {
                Text(level.name).font(.body.bold())
                Text(level.description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if isActive {
                Image(systemName: "checkmark")
                    .foregroundStyle(Color.accentColor)
                    .fontWeight(.semibold)
                    .padding(.top, 4)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Preview

#Preview {
    SettingsView()
        .environmentObject(ProfileStore())
}
