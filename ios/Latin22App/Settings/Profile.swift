import Foundation

// MARK: - Profile

struct Profile: Identifiable, Codable, Hashable {
    var id: UUID
    var name: String
    var isPreset: Bool
    var mappings: [String: String]
    var modifierKeys: [String]
}

// MARK: - Built-in presets

extension Profile {

    // Fixed preset UUIDs — stable across reinstalls.
    private static let idFull     = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    private static let idVowels   = UUID(uuidString: "00000000-0000-0000-0000-000000000002")!
    private static let idGeminate = UUID(uuidString: "00000000-0000-0000-0000-000000000003")!

    /// All preset profiles, loaded from the bundled mappings.json.
    static let presets: [Profile] = loadPresets()

    static var hungarianFull:    Profile { presets.first { $0.id == idFull     }! }
    static var hungarianVowels:  Profile { presets.first { $0.id == idVowels   }! }
    static var hungarianDoubled: Profile { presets.first { $0.id == idGeminate }! }

    // MARK: - JSON loading

    private struct PresetsFile: Decodable {
        struct Entry: Decodable {
            let id: String
            let name: String
            let mappings: [String: String]
            let modifierKeys: [String]
            enum CodingKeys: String, CodingKey {
                case id, name, mappings
                case modifierKeys = "modifier_keys"
            }
        }
        let profiles: [Entry]
    }

    static func loadPresets(from bundle: Bundle = .main) -> [Profile] {
        guard
            let url  = bundle.url(forResource: "mappings", withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let file = try? JSONDecoder().decode(PresetsFile.self, from: data)
        else { return [] }

        return file.profiles.compactMap { entry in
            guard let id = UUID(uuidString: entry.id) else { return nil }
            return Profile(
                id: id,
                name: entry.name,
                isPreset: true,
                mappings: entry.mappings,
                modifierKeys: entry.modifierKeys
            )
        }
    }
}
