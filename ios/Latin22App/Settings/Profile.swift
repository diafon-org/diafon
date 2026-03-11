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

    /// All preset profiles shipped with the app. Order determines display order.
    static let presets: [Profile] = [.hungarianFull, .hungarianVowels]

    /// Full Hungarian Latin22 layout — consonant digraphs + accented vowels.
    /// UUID is fixed so the active-profile preference survives reinstalls.
    static let hungarianFull = Profile(
        id: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!,
        name: "Hungarian (full)",
        isPreset: true,
        mappings: [
            // Palatised consonants
            "ny": "n̗",  "Ny": "N̗",
            "ly": "l̗",  "Ly": "L̗",
            "ty": "t̗",  "Ty": "T̗",
            "dy": "d̗",  "Dy": "D̗",
            "gy": "d̗",  "Gy": "D̗",
            "sy": "s̗",  "Sy": "S̗",
            "zy": "z̗",  "Zy": "Z̗",
            "cy": "c̗",  "Cy": "C̗",
            // Compound voiced consonants
            "cw": "ʣ",  "Cw": "ǲ",
            "cx": "ʣ̗",  "Cx": "ǲ̗",
            "dw": "ʣ",  "Dw": "ǲ",
            "dx": "ʣ̗",  "Dx": "ǲ̗",
            // Long (acute) vowels
            "aq": "á",  "Aq": "Á",
            "eq": "é",  "Eq": "É",
            "iq": "í",  "Iq": "Í",
            "oq": "ó",  "Oq": "Ó",
            "uq": "ú",  "Uq": "Ú",
            // Umlaut vowels
            "ow": "ö",  "Ow": "Ö",
            "uw": "ü",  "Uw": "Ü",
            // Double-acute vowels
            "ox": "ő",  "Ox": "Ő",
            "ux": "ű",  "Ux": "Ű",
        ],
        modifierKeys: ["y", "q", "w", "x"]
    )

    /// Vowels-only subset — useful when consonant digraphs aren't needed.
    static let hungarianVowels = Profile(
        id: UUID(uuidString: "00000000-0000-0000-0000-000000000002")!,
        name: "Hungarian (vowels only)",
        isPreset: true,
        mappings: [
            "aq": "á",  "Aq": "Á",
            "eq": "é",  "Eq": "É",
            "iq": "í",  "Iq": "Í",
            "oq": "ó",  "Oq": "Ó",
            "uq": "ú",  "Uq": "Ú",
            "ow": "ö",  "Ow": "Ö",
            "uw": "ü",  "Uw": "Ü",
            "ox": "ő",  "Ox": "Ő",
            "ux": "ű",  "Ux": "Ű",
        ],
        modifierKeys: ["q", "w", "x"]
    )
}
