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
/// **Backspace-expand**: the first backspace after a substitution re-expands
/// the output back to the original input sequence rather than deleting one char.
/// Example: after `ny` → `n̗`, backspace → restores `ny`.
///
/// **Caller contract**:
///   1. After visually inserting a character via the text proxy, call `process(_:)`.
///   2. Before inserting space / return, call `flush()` (resets state).
///   3. On backspace, call `reset()` then `deleteBackward()`.
///   4. On `replace` result: delete `deleteCount` chars backward, then insert `text`.
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
    }

    // MARK: - API

    /// Call **after** the character has been inserted into the text proxy.
    func process(_ char: Character) -> ProcessResult {
        guard maxLen > 0 else { return .none }
        return modifierKeys.contains(char) ? processModifier(char) : processNormal(char)
    }

    /// Resets engine state. Call before inserting space or return.
    func flush() {
        reset()
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

    private func processNormal(_ char: Character) -> ProcessResult {
        lastSubstitution = nil
        buffer.append(char)
        if buffer.count > maxLen { buffer.removeFirst() }
        return .none
    }

    private func processModifier(_ char: Character) -> ProcessResult {
        // Upgrade or escape: a modifier pressed right after a substitution.
        if let sub = lastSubstitution, sub.input.last == char {
            // If a longer mapping exists for sub.input+char, fire it as an upgrade
            // (e.g. nyy → n̗̗ after ny → n̗) instead of reverting.
            let extended = sub.input + String(char)
            if let upgrade = mappings[extended] {
                lastSubstitution = (extended, upgrade)
                buffer = ""
                return .replace(deleteCount: sub.output.count + 1, insert: upgrade)
            }
            // No upgrade: revert (escape behaviour).
            lastSubstitution = nil
            buffer = sub.input
            return .replace(deleteCount: sub.output.count + 1, insert: sub.input)
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
        for length in stride(from: limit, through: 2, by: -1) {
            let suffix = String(str.suffix(length))
            if let rep = mappings[suffix] { return (suffix, rep) }
        }
        return nil
    }
}
