import SwiftUI

struct KeyboardSettingsView: View {
    @EnvironmentObject private var store: ProfileStore

    var body: some View {
        NavigationView {
            List {
                Section {
                    Toggle(isOn: Binding(
                        get: { store.emojiKeyEnabled },
                        set: { store.setEmojiKeyEnabled($0) }
                    )) {
                        Label {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Show Emoji Key")
                                Text("Adds a 😊 key to the keyboard bottom row.")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        } icon: {
                            Image(systemName: "face.smiling")
                        }
                    }

                    Toggle(isOn: Binding(
                        get: { store.spacebarLangSwitch },
                        set: { store.setSpacebarLangSwitch($0) }
                    )) {
                        Label {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Language Switch on Space Bar")
                                Text("Long-press the space bar to switch between languages.")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        } icon: {
                            Image(systemName: "globe")
                        }
                    }
                } header: {
                    Text("Input")
                }
            }
            .navigationTitle("Keyboard")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview {
    KeyboardSettingsView()
        .environmentObject(ProfileStore())
}
