import XCTest
@testable import Latin22Keyboard

// NOTE: Swift Package / xcodegen includes MappingEngine.swift directly in this
// test target (see project.yml), so @testable import works without full access.

final class MappingEngineTests: XCTestCase {

    // MARK: - Helpers

    private func engine(_ mappings: [String: String], modifiers: Set<Character> = []) -> MappingEngine {
        MappingEngine(mappings: mappings, modifierKeys: modifiers)
    }

    // MARK: - Immediate modifier fire

    func testModifierComboFiresImmediately() {
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        XCTAssertEqual(e.process("n"), .none)
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
    }

    func testModifierWithNoMatchReturnsNone() {
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        XCTAssertEqual(e.process("a"), .none)
        XCTAssertEqual(e.process("y"), .none)   // "ay" is not a mapping
    }

    func testMatchFromMiddleOfBuffer() {
        // Characters before the sequence don't prevent a suffix match
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        XCTAssertEqual(e.process("x"), .none)
        XCTAssertEqual(e.process("n"), .none)
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
    }

    // MARK: - Escape (double modifier reverts last substitution)

    func testDoubleModifierRevertsSubstitution() {
        // ny → ņ fires immediately; second y escapes back to literal "ny"
        // The escape key was already inserted by the caller, so deleteCount includes it.
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        _ = e.process("n")
        _ = e.process("y")   // fires: ny → ņ
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ny"))
    }

    func testNonModifierClearsEscapeWindow() {
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        _ = e.process("n")
        _ = e.process("y")   // fires: ny → ņ
        _ = e.process("a")   // escape window closed
        XCTAssertEqual(e.process("y"), .none)   // no match for context ending in "ay"
    }

    // MARK: - Sequential combos

    func testTwoSequentialCombos() {
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        _ = e.process("n")
        _ = e.process("y")   // first ny → ņ
        _ = e.process("n")   // clears state, starts new sequence
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
    }

    // MARK: - flush and reset

    func testFlushAlwaysReturnsNone() {
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        _ = e.process("n")
        e.flush()   // should not crash / should reset state
    }

    func testResetClearsSubstitutionState() {
        let e = engine(["ny": "ņ"], modifiers: ["y"])
        _ = e.process("n")
        _ = e.process("y")   // fires
        e.reset()
        _ = e.process("n")
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
    }
}
