import SwiftUI

@main
struct Latin22App: App {
    @StateObject private var profileStore = ProfileStore()

    var body: some Scene {
        WindowGroup {
            TabView {
                ContentView()
                    .tabItem { Label("Reference", systemImage: "keyboard") }
                SettingsView()
                    .tabItem { Label("Settings", systemImage: "slider.horizontal.3") }
            }
            .environmentObject(profileStore)
        }
    }
}
