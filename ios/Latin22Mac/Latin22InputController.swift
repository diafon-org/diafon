import Cocoa
import InputMethodKit
import Foundation

/// IMKit input controller — wires MappingEngine to any macOS text input client.
///
/// Strategy: insert each character immediately (matches the iOS "insert-first-then-correct"
/// pattern), then apply any engine replacement via `insertText(_:replacementRange:)`.
///
/// `insertHistory` tracks the UTF-16 length of every insertion so that replacement
/// ranges are always correct even when output characters span multiple UTF-16 units
/// (e.g. combining-accent grapheme clusters like n + U+0317).
@objc(Latin22InputController)
final class Latin22InputController: IMKInputController {

    private var engine: MappingEngine!
    /// UTF-16 lengths of each character/replacement inserted since last reset.
    /// Used to compute backwards replacement ranges correctly.
    private var insertHistory: [Int] = []

    // MARK: - Init

    override init!(server: IMKServer!, delegate: Any!, client: Any!) {
        super.init(server: server, delegate: delegate, client: client)
        let (mappings, modifiers) = Self.loadMappings()
        engine = MappingEngine(mappings: mappings, modifierKeys: modifiers)
    }

    // MARK: - Key handling

    override func handle(_ event: NSEvent!, client sender: Any!) -> Bool {
        guard event.type == .keyDown else { return false }
        guard let client = sender as? IMKTextInput else { return false }

        // Pass through command / control combos unchanged.
        if !event.modifierFlags.intersection([.command, .control]).isEmpty {
            engine.flush()
            insertHistory.removeAll()
            return false
        }

        // Backspace — reset engine state and let the client handle deletion.
        if event.keyCode == 51 {
            engine.reset()
            insertHistory.removeAll()
            return false
        }

        guard let chars = event.characters, !chars.isEmpty,
              let scalar = chars.unicodeScalars.first else { return false }
        let char = Character(scalar)

        // Space / return / tab — flush engine and pass key through.
        if char == " " || char == "\r" || char == "\n" || char == "\t" {
            engine.flush()
            insertHistory.removeAll()
            return false
        }

        // Insert the character first so it appears immediately.
        client.insertText(chars,
                          replacementRange: NSRange(location: NSNotFound, length: NSNotFound))
        insertHistory.append(chars.utf16.count)

        // Ask the engine whether a replacement is needed.
        let result = engine.process(char)
        if case .replace(let n, let text) = result {
            apply(deleteCount: n, insert: text, client: client)
        }

        return true
    }

    // MARK: - Focus events

    override func activateServer(_ sender: Any!) {
        engine?.reset()
        insertHistory.removeAll()
    }

    override func deactivateServer(_ sender: Any!) {
        engine?.reset()
        insertHistory.removeAll()
    }

    // MARK: - Replacement

    /// Replaces the last `n` insertion-history entries with `text`.
    ///
    /// `n` is the engine's deleteCount in grapheme-cluster terms (one per insertion
    /// event). Each history entry stores the actual UTF-16 length of what was inserted,
    /// so summing them gives the exact range regardless of combining characters.
    private func apply(deleteCount n: Int, insert text: String, client: IMKTextInput) {
        let clampedN = min(n, insertHistory.count)
        let utf16Count = insertHistory.suffix(clampedN).reduce(0, +)
        insertHistory.removeLast(clampedN)

        let sel = client.selectedRange()
        guard sel.location != NSNotFound, sel.location >= utf16Count else { return }

        client.insertText(text,
                          replacementRange: NSRange(location: sel.location - utf16Count,
                                                    length: utf16Count))
        insertHistory.append(text.utf16.count)
    }

    // MARK: - Mappings

    private struct MappingsFile: Decodable {
        let mappings: [String: String]
        let modifierKeys: [String]?
        enum CodingKeys: String, CodingKey {
            case mappings
            case modifierKeys = "modifier_keys"
        }
    }

    private static func loadMappings() -> (mappings: [String: String], modifierKeys: Set<Character>) {
        guard
            let url  = Bundle.main.url(forResource: "mappings", withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let file = try? JSONDecoder().decode(MappingsFile.self, from: data)
        else { return ([:], []) }
        let modifiers = Set((file.modifierKeys ?? []).compactMap { $0.first })
        return (file.mappings, modifiers)
    }
}
