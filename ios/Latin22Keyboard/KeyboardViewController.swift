/// KeyboardKit-based view controller — wires MappingEngine into KK's text proxy calls.
import UIKit
import KeyboardKit

final class KeyboardViewController: KeyboardInputViewController {

    // MARK: - Engine

    private var engine: MappingEngine?

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        loadMappings()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        loadMappings()
    }

    // Reset engine on context change (focus moves to a different field).
    override func textWillChange(_ textInput: (any UITextInput)?) {
        engine?.reset()
    }

    // MARK: - Mappings

    /// Decode mappings.json, merge all layers for the current-language, build engine.
    private func loadMappings() {
        guard let url = Bundle(for: Self.self).url(forResource: "mappings", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let languages = root["languages"] as? [[String: Any]] else {
            print("❌ Failed to load mappings.json")
            return
        }

        var allMappings: [String: String] = [:]
        var allModifiers: Set<Character> = []

        // Read the active language id from UserDefaults (app group), fall back to default.
        let appGroupID = "group.com.latin22.shared"
        let store = UserDefaults(suiteName: appGroupID)
        let activeLangID = store?.string(forKey: "selectedLanguageID")
            ?? (root["default_language_id"] as? String)
            ?? ""
        let activeLayerIDs = store?.stringArray(forKey: "selectedLayerIDs")
            ?? (root["default_layer_ids"] as? [String])
            ?? []

        print("📍 Active language: \(activeLangID)")
        print("📍 Active layers: \(activeLayerIDs)")

        for lang in languages {
            guard (lang["id"] as? String) == activeLangID,
                  let layers = lang["layers"] as? [[String: Any]] else { continue }
            
            print("📦 Found \(layers.count) layers for language '\(activeLangID)'")
            
            for layer in layers {
                guard let lid = layer["id"] as? String else { continue }
                
                if activeLayerIDs.contains(lid) {
                    if let m = layer["mappings"] as? [String: String] {
                        print("  ✅ Loading layer '\(lid)' with \(m.count) mappings")
                        allMappings.merge(m) { existing, new in
                            print("    ⚠️ Conflict: '\(existing)' vs '\(new)' - keeping '\(new)'")
                            return new
                        }
                    }
                    if let mk = layer["modifier_keys"] as? [String] {
                        let keys = mk.compactMap { $0.first }
                        print("  ✅ Adding modifier keys: \(keys)")
                        allModifiers.formUnion(keys)
                    }
                } else {
                    print("  ⏭️ Skipping layer '\(lid)' (not in active layers)")
                }
            }
        }
        
        print("🎯 Final mapping count: \(allMappings.count)")
        print("🎯 Final modifier keys: \(allModifiers)")
        
        engine = MappingEngine(mappings: allMappings, modifierKeys: allModifiers)
    }

    // MARK: - Text proxy intercepts (mapping engine integration)

    /// All character insertions from KeyboardKit flow through here.
    override func insertText(_ text: String) {
        // Reset engine on word boundaries (space, return, etc.).
        if text == " " || text == "\n" || text == "\t" {
            engine?.reset()
            super.insertText(text)
            return
        }
        
        guard let engine, let char = text.first, text.count == 1 else {
            super.insertText(text)
            return
        }
        let result = engine.process(char)
        switch result {
        case .none:
            super.insertText(text)
        case .replace(let deleteCount, let insert):
            // deleteCount includes the triggering char, which hasn't been inserted yet.
            // Delete (deleteCount - 1) existing chars, then insert the replacement.
            let actualDeleteCount = deleteCount - 1
            if actualDeleteCount > 0 {
                for _ in 0..<actualDeleteCount { super.deleteBackward() }
            }
            super.insertText(insert)
        }
    }

    /// Backspace — let engine track state then let KK do the actual deletion.
    override func deleteBackward() {
        engine?.processBackspace()
        super.deleteBackward()
    }
}


