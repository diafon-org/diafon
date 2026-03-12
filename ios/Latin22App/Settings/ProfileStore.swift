import Foundation
import Combine

// MARK: - ProfileStore

/// Manages language+layer selection and user-created profiles.
///
/// The active language ID and layer IDs are stored in both UserDefaults.standard
/// and the shared App Group suite so the keyboard extension can read and write them.
final class ProfileStore: ObservableObject {

    // MARK: - Shared defaults

    static let appGroupID = "group.com.latin22.shared"

    private let shared: UserDefaults = {
        UserDefaults(suiteName: appGroupID) ?? .standard
    }()

    // MARK: - Keys

    private enum Keys {
        static let activeLanguageID = "activeLanguageID"
        static let activeLayerIDs   = "activeLayerIDs"
        static let userProfiles     = "userProfiles"
    }

    // MARK: - State

    let allLanguages: [Language]

    @Published private(set) var activeLanguageID: String
    @Published private(set) var activeLayerIDs: Set<String>
    @Published private(set) var userProfiles: [Profile] = []

    var activeLanguage: Language {
        allLanguages.first { $0.id == activeLanguageID }
            ?? allLanguages.first
            ?? Language(id: "", name: "", layers: [])
    }

    // MARK: - Init

    init() {
        let cfg = LanguagesConfig.load()
        allLanguages = cfg.languages

        let storedLangID = shared.string(forKey: Keys.activeLanguageID)
                            ?? UserDefaults.standard.string(forKey: Keys.activeLanguageID)
                            ?? cfg.defaultLanguageID
        activeLanguageID = storedLangID

        if let stored = shared.stringArray(forKey: Keys.activeLayerIDs)
                        ?? UserDefaults.standard.stringArray(forKey: Keys.activeLayerIDs) {
            activeLayerIDs = Set(stored)
        } else {
            activeLayerIDs = Set(cfg.defaultLayerIDs)
        }

        if let data    = UserDefaults.standard.data(forKey: Keys.userProfiles),
           let decoded = try? JSONDecoder().decode([Profile].self, from: data) {
            userProfiles = decoded
        }

        persistMergedProfile()
    }
    func activateLanguage(_ id: String) {
        guard id != activeLanguageID else { return }
        activeLanguageID = id
        UserDefaults.standard.set(id, forKey: Keys.activeLanguageID)
        shared.set(id, forKey: Keys.activeLanguageID)

        // If none of the stored layer IDs belong to the new language, enable its first layer.
        if let lang = allLanguages.first(where: { $0.id == id }),
           lang.layers.allSatisfy({ !activeLayerIDs.contains($0.id) }),
           let first = lang.layers.min(by: { $0.level < $1.level }) {
            activeLayerIDs.insert(first.id)
            UserDefaults.standard.set(Array(activeLayerIDs), forKey: Keys.activeLayerIDs)
            shared.set(Array(activeLayerIDs), forKey: Keys.activeLayerIDs)
        }
        persistMergedProfile()
    }

    // MARK: - Layer toggling

    func setLayer(_ layerID: String, active: Bool) {
        if active { activeLayerIDs.insert(layerID) }
        else      { activeLayerIDs.remove(layerID) }
        UserDefaults.standard.set(Array(activeLayerIDs), forKey: Keys.activeLayerIDs)
        shared.set(Array(activeLayerIDs), forKey: Keys.activeLayerIDs)
        persistMergedProfile()
    }

    // MARK: - User profile CRUD

    func addUserProfile(_ profile: Profile) {
        userProfiles.append(profile)
        persistUserProfiles()
    }

    func updateUserProfile(_ profile: Profile) {
        guard let i = userProfiles.firstIndex(where: { $0.id == profile.id }) else { return }
        userProfiles[i] = profile
        persistUserProfiles()
    }

    func deleteUserProfile(_ profile: Profile) {
        userProfiles.removeAll { $0.id == profile.id }
        persistUserProfiles()
    }

    // MARK: - Private persistence

    private func persistUserProfiles() {
        if let data = try? JSONEncoder().encode(userProfiles) {
            UserDefaults.standard.set(data, forKey: Keys.userProfiles)
        }
    }

    /// Writes the active language ID and layer IDs to the App Group so the
    /// keyboard extension can merge its own profile without needing the app.
    private func persistMergedProfile() {
        shared.set(activeLanguageID, forKey: Keys.activeLanguageID)
        shared.set(Array(activeLayerIDs), forKey: Keys.activeLayerIDs)
    }
}

