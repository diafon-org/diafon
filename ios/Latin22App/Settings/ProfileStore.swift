import Foundation
import Combine

// MARK: - ProfileStore

/// Manages preset and user-created profiles and tracks the active one.
///
/// Persistence uses `UserDefaults` with the App Group suite
/// (`group.com.latin22.shared`) so the keyboard extension can read the active
/// profile without an IPC round-trip.  When the entitlement is not yet
/// provisioned the initialiser falls back to `UserDefaults.standard`
/// automatically — the app still works, but the keyboard extension will keep
/// reading its bundled `mappings.json`.
final class ProfileStore: ObservableObject {

    // MARK: - Shared defaults

    static let appGroupID = "group.com.latin22.shared"

    private let defaults: UserDefaults = {
        UserDefaults(suiteName: appGroupID) ?? .standard
    }()

    // MARK: - Keys

    private enum Keys {
        static let activeProfileID  = "activeProfileID"
        static let userProfiles     = "userProfiles"
        /// Full active-profile JSON written here so the keyboard extension can
        /// decode it directly via JSONDecoder without needing the Profile type.
        static let activeProfileJSON = "activeProfile"
    }

    // MARK: - Published state

    @Published private(set) var userProfiles: [Profile] = []
    @Published private(set) var activeProfileID: UUID

    var allProfiles: [Profile] { Profile.presets + userProfiles }

    var activeProfile: Profile {
        allProfiles.first { $0.id == activeProfileID } ?? Profile.presets[0]
    }

    // MARK: - Init

    init() {
        if let stored = UserDefaults.standard.string(forKey: Keys.activeProfileID),
           let id = UUID(uuidString: stored) {
            activeProfileID = id
        } else {
            activeProfileID = Profile.presets[0].id
        }

        if let data = UserDefaults.standard.data(forKey: Keys.userProfiles),
           let decoded = try? JSONDecoder().decode([Profile].self, from: data) {
            userProfiles = decoded
        }
    }

    // MARK: - Activate

    func activate(_ profile: Profile) {
        activeProfileID = profile.id
        UserDefaults.standard.set(profile.id.uuidString, forKey: Keys.activeProfileID)
        defaults.set(profile.id.uuidString, forKey: Keys.activeProfileID)
        persistActiveProfileJSON()
    }

    // MARK: - User profile CRUD

    func addUserProfile(_ profile: Profile) {
        userProfiles.append(profile)
        persistUserProfiles()
    }

    func updateUserProfile(_ profile: Profile) {
        guard let index = userProfiles.firstIndex(where: { $0.id == profile.id }) else { return }
        userProfiles[index] = profile
        persistUserProfiles()
        if activeProfileID == profile.id { persistActiveProfileJSON() }
    }

    func deleteUserProfile(_ profile: Profile) {
        userProfiles.removeAll { $0.id == profile.id }
        if activeProfileID == profile.id { activate(Profile.presets[0]) }
        persistUserProfiles()
    }

    // MARK: - Private persistence

    private func persistUserProfiles() {
        if let data = try? JSONEncoder().encode(userProfiles) {
            UserDefaults.standard.set(data, forKey: Keys.userProfiles)
        }
    }

    /// Writes the full active profile as JSON to the shared App Group defaults
    /// so the keyboard extension can read it with a simple JSONDecoder call.
    private func persistActiveProfileJSON() {
        if let data = try? JSONEncoder().encode(activeProfile) {
            defaults.set(data, forKey: Keys.activeProfileJSON)
        }
    }
}
