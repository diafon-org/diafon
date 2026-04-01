/// Modifier-key based mapping engine.
///
/// Sequences ending in a declared modifier key fire **immediately** when the
/// modifier is pressed — there is no lookahead delay.
///
/// **Escape**: pressing the same modifier key a second time in a row undoes the
/// last substitution and outputs the original input literally.
/// Example: `n`+`y` → `n̗`, then another `y` → reverts to `ny`.
///
/// **Upgrade**: if the mapping table contains a longer sequence that is exactly
/// `lastSubstitution.input + char`, the engine fires the longer form instead of
/// escaping. Example with `nyy → n̗̗` in the table: `ny` → `n̗`, then `y` upgrades
/// to `n̗̗`; a further `y` then escapes that back to `nyy`.
///
/// **Cross-modifier composite**: pressing a modifier key after a substitution
/// that was triggered by a DIFFERENT modifier checks for an explicit composite
/// mapping (`lastInput + char`). If found, that mapping fires (e.g. `ny` → `n̗`,
/// then `q` looks up `nyq → n͈` and fires it). If no composite mapping exists,
/// the modifier keypress falls through to normal buffer processing.
/// No special "doubling modifier" parameter is needed — all modifier keys
/// participate in cross-modifier composites uniformly.
///
/// **Smart escape**: when escaping a composite substitution (input length > 1),
/// the engine first tries to revert to the parent mapping rather than the raw
/// input string. Example: `nyq → n͈`, then `q` strips the trailing `q` from
/// `nyq` → looks up `ny → n̗` → reverts to `n̗`. Falls back to literal input
/// revert if no parent mapping exists (`aq` + `q` → reverts to `aq`).
///
/// **Backspace-expand**: the first backspace after a substitution re-expands
/// the output back to the original input sequence rather than deleting one char.
/// Example: after `ny` → `n̗`, backspace → restores `ny`.
///
/// **Caller contract**:
///   1. For each character keypress, call `process(_:)` **before** writing to the
///      proxy. `.none` → insert the raw character. `.replace(n, text)` → delete
///      `n-1` characters backward, then insert `text`. The −1 accounts for the
///      triggering character not yet in the proxy.
///   2. At word boundaries (space / return): call `reset()` before inserting.
///   3. On backspace: call `processBackspace()` before deleting from the proxy.
import Foundation

final class MappingEngine {

    // MARK: - Result

    enum ProcessResult: Equatable {
        case none
        case replace(deleteCount: Int, insert: String)
    }

    // MARK: - State

    private let mappings: [String: String]
    private let modifierKeys: Set<Character>
    private let maxLen: Int

    private var buffer: String = ""
    /// Tracks the last fired substitution for escape and backspace-expand.
    private var lastSubstitution: (input: String, output: String)?

    // MARK: - Init

    init(mappings: [String: String], modifierKeys: Set<Character> = []) {
        self.mappings = mappings
        self.modifierKeys = modifierKeys
        self.maxLen = mappings.keys.map(\.count).max() ?? 0
        print("🔧 MappingEngine initialized with \(mappings.count) mappings, max length: \(maxLen)")
        print("🔧 Modifier keys: \(modifierKeys)")
    }

    // MARK: - API

    /// Call **before** writing the character to the text proxy.
    func process(_ char: Character) -> ProcessResult {
        guard maxLen > 0 else { return .none }
        guard modifierKeys.contains(char) else {
            lastSubstitution = nil
            buffer.append(char)
            if buffer.count > maxLen { buffer.removeFirst() }
            print("  📝 Regular char '\(char)' → buffer: '\(buffer)'")
            return .none
        }
        print("  🔑 Modifier key '\(char)' pressed, buffer: '\(buffer)'")
        return processModifier(char)
    }

    /// Resets all state (focus change, context break, etc.).
    func reset() {
        buffer = ""
        lastSubstitution = nil
    }

    /// Call when the user deletes backward.
    /// Pops the last buffered character so the engine stays in sync with the
    /// text field — unlike reset(), earlier context is preserved.
    func processBackspace() {
        lastSubstitution = nil
        if !buffer.isEmpty { buffer.removeLast() }
    }

    // MARK: - Private

    private func processModifier(_ char: Character) -> ProcessResult {
        // Branch 1: same modifier repeated after a substitution — upgrade or escape.
        if let sub = lastSubstitution, sub.input.last == char {
            let extended = sub.input + String(char)
            if let upgrade = mappings[extended] {
                // Longer explicit mapping found: upgrade (e.g. nyy→ after ny→n̗).
                lastSubstitution = (extended, upgrade)
                buffer = ""
                return .replace(deleteCount: sub.output.count + 1, insert: upgrade)
            }
            // Smart escape: for cross-modifier composites (input length > 1),
            // try reverting to the parent mapping output instead of raw input.
            // e.g. nyqq → strips "q" from "nyq", finds ny→n̗, reverts to n̗.
            if sub.input.count > 1 {
                let parentInput = String(sub.input.dropLast())
                if let parentOutput = mappings[parentInput] {
                    lastSubstitution = (parentInput, parentOutput)
                    buffer = ""
                    return .replace(deleteCount: sub.output.count + 1, insert: parentOutput)
                }
            }
            // Default escape: revert to literal input.
            lastSubstitution = nil
            buffer = sub.input
            return .replace(deleteCount: sub.output.count + 1, insert: sub.input)
        }

        // Branch 2: different modifier pressed after a substitution — check for
        // an explicit cross-modifier composite mapping (e.g. nyq→n͈ after ny→n̗).
        // Capital letters do not have composite mappings, so this only applies
        // to lowercase sequences.
        if let sub = lastSubstitution {
            let composite = sub.input + String(char)
            if let explicit = mappings[composite] {
                lastSubstitution = (composite, explicit)
                buffer = ""
                return .replace(deleteCount: sub.output.count + 1, insert: explicit)
            }
        }

        lastSubstitution = nil
        buffer.append(char)
        if buffer.count > maxLen { buffer.removeFirst() }
        if let (seq, rep) = longestSuffixMatch(in: buffer) {
            lastSubstitution = (seq, rep)
            buffer = ""
            return .replace(deleteCount: seq.count, insert: rep)
        }
        return .none
    }

    private func longestSuffixMatch(in str: String) -> (String, String)? {
        let limit = min(maxLen, str.count)
        print("    🔍 Searching for match in '\(str)' (checking lengths \(limit) down to 2)")
        for length in stride(from: limit, through: 2, by: -1) {
            let suffix = String(str.suffix(length))
            if let rep = mappings[suffix] {
                print("    ✅ Found mapping: '\(suffix)' → '\(rep)'")
                return (suffix, rep)
            } else {
                print("    ❌ No mapping for '\(suffix)'")
            }
        }
        print("    ⚠️ No match found")
        return nil
    }
}
