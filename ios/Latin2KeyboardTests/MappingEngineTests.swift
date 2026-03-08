import XCTest
@testable import Latin2Keyboard

// NOTE: Swift Package / xcodegen includes MappingEngine.swift directly in this
// test target (see project.yml), so @testable import works without full access.

final class MappingEngineTests: XCTestCase {

    // MARK: - Helpers

    private func engine(_ mappings: [String: String]) -> MappingEngine {
        MappingEngine(mappings: mappings)
    }

    // MARK: - Basic replacement

    func testSimpleReplacementFires() {
        let e = engine(["ny": "ņ"])
        XCTAssertEqual(e.process("n"), .none)
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
    }

    func testNoMatchReturnsNone() {
        let e = engine(["ny": "ņ"])
        XCTAssertEqual(e.process("a"), .none)
        XCTAssertEqual(e.process("b"), .none)
    }

    func testMatchInMiddleOfBuffer() {
        // Earlier chars shouldn't prevent a suffix match
        let e = engine(["ny": "ņ"])
        XCTAssertEqual(e.process("x"), .none)
        XCTAssertEqual(e.process("n"), .none)
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
    }

    // MARK: - Lookahead / pending

    func testPendingHoldsShortMatch() {
        // "ny" is held because "nyy" exists
        let e = engine(["ny": "ņ", "nyy": "ny"])
        XCTAssertEqual(e.process("n"), .none)
        XCTAssertEqual(e.process("y"), .none)   // pending, not applied yet
    }

    func testLongerMatchWins() {
        let e = engine(["ny": "ņ", "nyy": "ny"])
        _ = e.process("n")
        _ = e.process("y")   // pending
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 3, insert: "ny"))
    }

    func testPendingFlushedByNonExtendingChar() {
        // ny pending, then 'z' arrives — flush ny and absorb z
        let e = engine(["ny": "ņ", "nyy": "ny"])
        _ = e.process("n")
        _ = e.process("y")   // pending
        XCTAssertEqual(e.process("z"), .replace(deleteCount: 3, insert: "ņz"))
    }

    // MARK: - flush() (called before space / return)

    func testFlushAppliesPending() {
        let e = engine(["ny": "ņ", "nyy": "ny"])
        _ = e.process("n")
        _ = e.process("y")   // pending
        XCTAssertEqual(e.flush(), .replace(deleteCount: 2, insert: "ņ"))
    }

    func testFlushWithNoPendingReturnsNone() {
        let e = engine(["ny": "ņ"])
        _ = e.process("a")
        XCTAssertEqual(e.flush(), .none)
    }

    // MARK: - reset()

    func testResetClearsPending() {
        let e = engine(["ny": "ņ", "nyy": "ny"])
        _ = e.process("n")
        _ = e.process("y")   // pending
        e.reset()
        // After reset the buffer is empty; next chars start fresh
        XCTAssertEqual(e.process("n"), .none)
        XCTAssertEqual(e.process("y"), .none)   // pending again (no definitive yet)
    }

    // MARK: - Escape chain  (yy → y)

    func testEscapeYY() {
        let e = engine(["yy": "y"])
        XCTAssertEqual(e.process("y"), .none)
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "y"))
    }

    // MARK: - Multi-match independence

    func testTwoSequentialMatches() {
        let e = engine(["ny": "ņ"])
        _ = e.process("n")
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
        // Start a second sequence immediately after
        _ = e.process("n")
        XCTAssertEqual(e.process("y"), .replace(deleteCount: 2, insert: "ņ"))
    }
}
