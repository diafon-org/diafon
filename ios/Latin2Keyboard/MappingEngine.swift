/// Sequence-matching engine with trie-based lookahead.
///
/// **Lookahead rule**: if a matched sequence is also a strict prefix of a longer
/// known mapping, the engine waits ("pending") rather than applying immediately.
/// This allows `nyy → ny` to win over `ny → ņ` when the user types that third `y`.
///
/// **Caller contract**:
///   1. After visually inserting a character via the text proxy, call `process(_:)`.
///   2. Before inserting space / return / any non-sequence key, call `flush()`.
///   3. On backspace, call `reset()`.
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
    /// All strict prefixes of mapping keys.  A match here means a longer key might arrive.
    private let prefixes: Set<String>
    private let maxLen: Int

    private var buffer: String = ""
    private var pending: (seq: String, rep: String)? = nil

    // MARK: - Init

    init(mappings: [String: String]) {
        self.mappings = mappings

        var p = Set<String>()
        for key in mappings.keys {
            for i in 1 ..< key.count {
                p.insert(String(key.prefix(i)))
            }
        }
        self.prefixes = p
        self.maxLen = mappings.keys.map(\.count).max() ?? 5
    }

    // MARK: - API

    /// Call **after** the character has been inserted into the text proxy.
    func process(_ char: Character) -> ProcessResult {
        buffer.append(char)
        if buffer.count > maxLen + 1 { buffer.removeFirst() }

        if let (seq, rep) = longestSuffixMatch(in: buffer) {
            if prefixes.contains(seq) {
                // Could still grow — store as pending and wait
                pending = (seq, rep)
                return .none
            } else {
                // Definitive match — supersedes any earlier pending
                pending = nil
                buffer = String(char)       // retain char as start of next sequence
                return .replace(deleteCount: seq.count, insert: rep)
            }
        } else {
            if let p = pending {
                // A non-extending char arrived — flush the pending match,
                // absorbing the current char into the output string.
                pending = nil
                buffer = String(char)
                return .replace(deleteCount: p.seq.count + 1,
                                insert: p.rep + String(char))
            }
            return .none
        }
    }

    /// Call before inserting a non-sequence key (space, return).
    /// Flushes any pending match so it is applied first.
    func flush() -> ProcessResult {
        defer { pending = nil; buffer = "" }
        guard let p = pending else { return .none }
        return .replace(deleteCount: p.seq.count, insert: p.rep)
    }

    /// Call on backspace or any context-breaking event (focus change, etc.).
    func reset() {
        buffer = ""
        pending = nil
    }

    // MARK: - Private

    private func longestSuffixMatch(in str: String) -> (String, String)? {
        let limit = min(maxLen, str.count)
        for length in stride(from: limit, through: 2, by: -1) {
            let suffix = String(str.suffix(length))
            if let rep = mappings[suffix] { return (suffix, rep) }
        }
        return nil
    }
}
