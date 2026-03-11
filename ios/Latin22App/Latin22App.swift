import SwiftUI

@main
struct Latin22App: App {
    @StateObject private var profileStore = ProfileStore()

    var body: some Scene {
        WindowGroup {
            TabView {
                ContentView()
                    .tabItem { Label("Info", systemImage: "info.circle") }
                SettingsView()
                    .tabItem { Label("Settings", systemImage: "slider.horizontal.3") }
            }
            .environmentObject(profileStore)
        }
    }
}
