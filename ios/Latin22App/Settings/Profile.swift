import Foundation

// MARK: - Layer

struct Layer: Identifiable, Codable, Hashable {
    var id: String
    var name: String
    var description: String
    var level: Int
    var modifierKeys: [String]
    var mappings: [String: String]
}

// MARK: - Language

struct Language: Identifiable, Codable {
    var id: String
    var name: String
    var layers: [Layer]
}

// MARK: - LanguagesConfig

struct LanguagesConfig {
    let languages: [Language]
    let defaultLanguageID: String
    let defaultLayerIDs: [String]

    static func load(from bundle: Bundle = .main) -> LanguagesConfig {
        guard
            let url  = bundle.url(forResource: "mappings", withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let raw  = try? JSONDecoder().decode(RawFile.self, from: data)
        else {
            return LanguagesConfig(languages: [], defaultLanguageID: "", defaultLayerIDs: [])
        }

        let languages = raw.languages.map { lang in
            Language(
                id: lang.id,
                name: lang.name,
                layers: lang.layers.map { layer in
                    Layer(
                        id: layer.id,
                        name: layer.name,
                        description: layer.description ?? "",
                        level: layer.level,
                        modifierKeys: layer.modifier_keys,
                        mappings: layer.mappings
                    )
                }
            )
        }
        return LanguagesConfig(
            languages: languages,
            defaultLanguageID: raw.default_language_id,
            defaultLayerIDs: raw.default_layer_ids
        )
    }

    // MARK: - Raw Decodable types

    private struct RawFile: Decodable {
        struct RawLayer: Decodable {
            let id: String
            let name: String
            let description: String?
            let level: Int
            let modifier_keys: [String]
            let mappings: [String: String]
        }
        struct RawLanguage: Decodable {
            let id: String
            let name: String
            let layers: [RawLayer]
        }
        let languages: [RawLanguage]
        let default_language_id: String
        let default_layer_ids: [String]
    }
}

// MARK: - Profile (user-created flat mapping)

struct Profile: Identifiable, Codable, Hashable {
    var id: UUID
    var name: String
    var isPreset: Bool
    var mappings: [String: String]
    var modifierKeys: [String]
}

