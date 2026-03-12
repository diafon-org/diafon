import SwiftUI

@main
struct Latin22App: App {
    @StateObject private var profileStore = ProfileStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(profileStore)
        }
    }
}

// MARK: - RootView

private struct RootView: View {
    var body: some View {
        VStack(spacing: 0) {
            TryOutBar()
            TabView {
                ContentView()
                    .tabItem { Label("Info", systemImage: "info.circle") }
                SettingsView()
                    .tabItem { Label("Profile", systemImage: "globe") }
                KeyboardSettingsView()
                    .tabItem { Label("Keyboard", systemImage: "keyboard") }
            }
        }
    }
}

// MARK: - TryOutBar

private struct TryOutBar: View {
    @State private var text = ""

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Image(systemName: "keyboard")
                    .foregroundStyle(.secondary)
                    .font(.footnote)
                TextField("Try out the keyboard here…", text: $text)
                    .font(.body)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
                if !text.isEmpty {
                    Button {
                        text = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(.bar)
            Divider()
        }
    }
}
