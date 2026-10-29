// The keyboard in the simulator, typed on as a person would: the app's Try
// field, Diafon picked with the system's globe, keys tapped by their
// accessibility ids (key:s, key:space, key:delete…), the field read back.
// Every case runs in both tail modes (marked text, then rewritten plain
// text, switched in the keyboard's own settings panel). `make uitest`.
import XCTest

final class KeyboardTests: XCTestCase {
    private var app: XCUIApplication!

    override func setUp() { continueAfterFailure = false }

    private func key(_ id: String) -> XCUIElement { app.descendants(matching: .any)["key:" + id] }

    private var field: XCUIElement {
        app.textViews["trial"].exists ? app.textViews["trial"] : app.textFields["trial"]
    }

    private var value: String {
        let v = field.value as? String ?? ""
        return v == "type sjok sewp njawr" ? "" : v      // the placeholder
    }

    /// A fresh app with Diafon up in the Try field.
    private func start() {
        app = XCUIApplication()
        app.launch()
        XCTAssertTrue(field.waitForExistence(timeout: 10))
        field.tap()
        for _ in 0..<4 {
            if key("s").waitForExistence(timeout: 2) { return }
            app.buttons["Next keyboard"].firstMatch.tap()
        }
        XCTFail("Diafon did not come up")
    }

    private func type(_ text: String) {
        for c in text {
            switch c {
            case " ": key("space").tap()
            case "⌫": key("delete").tap()
            default:
                if c.isUppercase { key("shift").tap() }
                key(String(c).lowercased()).tap()
            }
        }
    }

    private func shot(_ name: String) {
        let a = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        a.name = name
        a.lifetime = .keepAlways
        add(a)
    }

    /// Underlined (marked) tail on or off, in the keyboard's settings panel.
    private func setMarked(_ on: Bool) {
        start()
        app.descendants(matching: .any)["Diafon settings"].firstMatch.tap()
        let sw = app.switches.matching(NSPredicate(format: "label CONTAINS 'Underline' OR identifier CONTAINS 'Underline'")).firstMatch
        let toggle = sw.exists ? sw : app.switches.element(boundBy: app.switches.count - 1)
        XCTAssertTrue(toggle.waitForExistence(timeout: 5))
        if (toggle.value as? String == "1") != on { toggle.tap() }
        shot("settings, marked \(on)")
        app.buttons["Done"].firstMatch.tap()
    }

    private func cases(_ mode: String) {
        start()
        type("sjok sewp njawr")
        shot("\(mode): sjok sewp njawr")
        XCTAssertEqual(value, "șok sép n̦ár", "\(mode): stream")

        start()
        type("njanj")
        XCTAssertEqual(value, "n̦an̦", "\(mode): before backspace")
        type("⌫⌫")
        XCTAssertEqual(value, "n̦a", "\(mode): backspace through the tail")
        type("⌫")
        XCTAssertEqual(value, "n̦", "\(mode): backspace on final text")
        type("⌫")
        XCTAssertEqual(value, "", "\(mode): backspace takes the letter with its mark")

        start()
        type("Sjan1 Tqy")                                 // shift, a tone digit, two operators
        shot("\(mode): Sjan1 Tqy")
        XCTAssertEqual(value, "Șan1 C̖", "\(mode): capitals and tones")

        start()
        type("ok hawrt")                                  // heart: its emoji offered on the strip
        let heart = app.buttons["❤️"].firstMatch
        XCTAssertTrue(heart.waitForExistence(timeout: 5), "\(mode): no ❤️ offered for hawrt")
        shot("\(mode): emoji for hawrt")
        heart.tap()
        XCTAssertEqual(value, "ok ❤️", "\(mode): the emoji takes the word's place")
    }

    func testMarked() {
        setMarked(true)
        cases("marked")
    }

    func testReplace() {
        setMarked(false)
        cases("replace")
        setMarked(true)                                   // leave the default behind
    }
}
