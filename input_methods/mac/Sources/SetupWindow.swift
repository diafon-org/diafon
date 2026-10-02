// The setup window: Universal or one language's spelling, the toggles, and a live pane that shows a typed line
// both ways. Built in code, framework controls only.
import Cocoa

final class SetupWindow: NSObject, NSTextFieldDelegate {
    static let shared = SetupWindow()
    private var window: NSWindow?
    private var input: NSTextField!
    private var previews: NSStackView!
    private var universalRadio: NSButton!
    private var languageRadio: NSButton!
    private var languagePopup: NSPopUpButton!
    private var languageSample: NSTextField!
    private var checkActions: [ObjectIdentifier: (Bool) -> Void] = [:]
    private let neutral = "sjan txy tqok dqum acw"

    func show() {
        if window == nil { build() }
        NSApp.activate(ignoringOtherApps: true)
        window?.center()
        window?.makeKeyAndOrderFront(nil)
        refresh()
    }

    private func build() {
        let p = Prefs.shared
        let root = NSStackView()
        root.orientation = .vertical
        root.alignment = .leading
        root.spacing = 8
        root.edgeInsets = NSEdgeInsets(top: 20, left: 22, bottom: 22, right: 22)

        root.addArrangedSubview(header())
        root.addArrangedSubview(note("One keyboard, one script, every language. Type the input form in any app; the conversion happens as you type and commits as soon as a segment is final."))

        root.addArrangedSubview(heading("How to"))
        root.addArrangedSubview(howto([
            ("1", "Pick Diafon in the input menu (or ⌃Space). Your keyboard stays as it is."),
            ("2", "Type sounds as letters. A consonant or vowel plus a mark: sj → \(p.renderer("script")("sj")), tq → \(p.renderer("script")("tq")), aw → \(p.renderer("script")("aw")); a segment stays underlined until the next key settles it."),
            ("3", "A bare Shift tap switches conversion off and back on to the spelling you had. Quick taps in a row walk the cycle instead: passthrough → Universal → each language on your quick list; a label names the mode. ⇧Space opens the language chooser."),
            ("4", "Tab (or ↓) on an underlined segment opens the candidate window with every spelling."),
            ("5", "Text in any spelling: select it, then Diafon menu → Convert selection (or right-click → Services → Convert with Diafon); the … variants let you set the source and the target first."),
        ]))

        root.addArrangedSubview(heading("What is written out"))
        universalRadio = NSButton(radioButtonWithTitle: "Universal    " + p.renderer("script")(neutral),
                                  target: self, action: #selector(pickUniversal(_:)))
        universalRadio.toolTip = "One letter per sound, the same in every language."
        root.addArrangedSubview(universalRadio)
        let row = NSStackView()
        row.orientation = .horizontal
        row.alignment = .firstBaseline
        row.spacing = 8
        languageRadio = NSButton(radioButtonWithTitle: "Language spelling", target: self, action: #selector(pickLanguage(_:)))
        languageRadio.toolTip = "Today's orthography of one language."
        languagePopup = NSPopUpButton(frame: .zero, pullsDown: false)
        for (code, name) in Prefs.languages {
            languagePopup.addItem(withTitle: name)
            languagePopup.lastItem?.representedObject = code
        }
        languagePopup.target = self
        languagePopup.action = #selector(languageChosen(_:))
        languageSample = NSTextField(labelWithString: "")
        languageSample.font = NSFont(name: "Georgia", size: 13) ?? NSFont.systemFont(ofSize: 13)
        row.addArrangedSubview(languageRadio)
        row.addArrangedSubview(languagePopup)
        row.addArrangedSubview(languageSample)
        root.addArrangedSubview(row)

        root.addArrangedSubview(heading("Try it"))
        input = NSTextField(string: neutral)
        input.font = NSFont.monospacedSystemFont(ofSize: 14, weight: .regular)
        input.textColor = NSColor(red: 0.055, green: 0.486, blue: 0.525, alpha: 1)
        input.delegate = self
        input.widthAnchor.constraint(equalToConstant: 540).isActive = true
        root.addArrangedSubview(input)
        previews = NSStackView()
        previews.orientation = .vertical
        previews.alignment = .leading
        previews.spacing = 4
        root.addArrangedSubview(previews)

        root.addArrangedSubview(heading("Also"))
        root.addArrangedSubview(check("Conversion on", p.enabled) { Prefs.shared.enabled = $0 })
        root.addArrangedSubview(check("A bare Shift tap switches conversion off and on; quick taps walk the cycle", p.shiftToggle) { Prefs.shared.shiftToggle = $0 })
        root.addArrangedSubview(note("While a segment is still underlined, Tab (or ↓) opens the candidate window with that segment in every spelling: arrows pick one, Return takes it, Escape closes; digits stay tones."))
        root.addArrangedSubview(check("Tone digits", p.tones) { Prefs.shared.tones = $0 })
        root.addArrangedSubview(note("Convert text in any spelling: select it in any app, then Diafon menu → Convert selection, or right-click → Services → Convert with Diafon."))
        root.addArrangedSubview(note("Spec \(SpecData.generated) · \(SpecData.source)"))

        let w = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 600, height: 700),
                         styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        w.title = "Diafon setup"
        w.contentView = root
        w.isReleasedWhenClosed = false
        window = w
        NotificationCenter.default.addObserver(forName: Prefs.changed, object: nil, queue: .main) { [weak self] _ in self?.refresh() }
    }

    @objc private func pickUniversal(_ sender: NSButton) { Prefs.shared.output = "script" }

    @objc private func pickLanguage(_ sender: NSButton) { Prefs.shared.language = Prefs.shared.language }

    @objc private func languageChosen(_ sender: NSPopUpButton) {
        if let code = sender.selectedItem?.representedObject as? String { Prefs.shared.language = code }
    }

    private func check(_ label: String, _ on: Bool, onChange: @escaping (Bool) -> Void) -> NSButton {
        let b = NSButton(checkboxWithTitle: label, target: self, action: #selector(checkChanged(_:)))
        b.state = on ? .on : .off
        checkActions[ObjectIdentifier(b)] = onChange
        return b
    }

    @objc private func checkChanged(_ sender: NSButton) { checkActions[ObjectIdentifier(sender)]?(sender.state == .on) }

    func controlTextDidChange(_ obj: Notification) { refresh() }

    /// The window follows the settings: the radios, the popup, the language's sample sentence
    /// (its first clause), and the typed line in Universal and in the chosen spelling.
    private func refresh() {
        guard let previews = previews else { return }
        let p = Prefs.shared
        universalRadio.state = p.universal ? .on : .off
        languageRadio.state = p.universal ? .off : .on
        let code = p.language
        if let i = languagePopup.itemArray.firstIndex(where: { ($0.representedObject as? String) == code }) {
            languagePopup.selectItem(at: i)
        }
        let st = SpecData.stages[code]
        let src = (st != nil && !st!.sample.isEmpty) ? st!.sample : neutral
        let clause = src.split(separator: ",").first.map(String.init) ?? src
        languageSample.stringValue = p.renderer("stage:\(code)")(clause)

        previews.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let typed = input.stringValue
        for (value, label) in [("script", "universal"), ("stage:\(code)", (st?.name ?? code).lowercased())] {
            let row = NSStackView()
            row.orientation = .horizontal
            row.alignment = .firstBaseline
            row.spacing = 10
            let l = NSTextField(labelWithString: label)
            l.font = NSFont.monospacedSystemFont(ofSize: 10, weight: .medium)
            l.textColor = .secondaryLabelColor
            l.widthAnchor.constraint(equalToConstant: 120).isActive = true
            let v = NSTextField(labelWithString: p.renderer(value)(typed))
            v.font = NSFont(name: "Georgia", size: 17) ?? NSFont.systemFont(ofSize: 17)
            row.addArrangedSubview(l)
            row.addArrangedSubview(v)
            previews.addArrangedSubview(row)
        }
    }

    /// The mark beside the name, from the app icon.
    private func header() -> NSView {
        let row = NSStackView()
        row.orientation = .horizontal
        row.alignment = .centerY
        row.spacing = 10
        if let path = Bundle.main.path(forResource: "Diafon", ofType: "icns"), let img = NSImage(contentsOfFile: path) {
            let iv = NSImageView(image: img)
            iv.imageScaling = .scaleProportionallyUpOrDown
            iv.widthAnchor.constraint(equalToConstant: 36).isActive = true
            iv.heightAnchor.constraint(equalToConstant: 36).isActive = true
            row.addArrangedSubview(iv)
        }
        row.addArrangedSubview(title("Diafon"))
        return row
    }
    /// Numbered lines, the number in a narrow column.
    private func howto(_ lines: [(String, String)]) -> NSView {
        let col = NSStackView()
        col.orientation = .vertical
        col.alignment = .leading
        col.spacing = 3
        for (n, text) in lines {
            let row = NSStackView()
            row.orientation = .horizontal
            row.alignment = .firstBaseline
            row.spacing = 8
            let num = NSTextField(labelWithString: n)
            num.font = NSFont.monospacedSystemFont(ofSize: 12, weight: .semibold)
            num.textColor = NSColor(red: 0.055, green: 0.486, blue: 0.525, alpha: 1)
            num.widthAnchor.constraint(equalToConstant: 12).isActive = true
            let t = NSTextField(wrappingLabelWithString: text)
            t.font = NSFont.systemFont(ofSize: 12)
            t.preferredMaxLayoutWidth = 520
            row.addArrangedSubview(num)
            row.addArrangedSubview(t)
            col.addArrangedSubview(row)
        }
        return col
    }
    private func title(_ s: String) -> NSTextField {
        let t = NSTextField(labelWithString: s)
        t.font = NSFont(name: "Georgia-Bold", size: 22) ?? NSFont.boldSystemFont(ofSize: 22)
        return t
    }
    private func heading(_ s: String) -> NSTextField {
        let t = NSTextField(labelWithString: s.uppercased())
        t.font = NSFont.monospacedSystemFont(ofSize: 10, weight: .semibold)
        t.textColor = .secondaryLabelColor
        return t
    }
    private func note(_ s: String) -> NSTextField {
        let t = NSTextField(wrappingLabelWithString: s)
        t.font = NSFont.systemFont(ofSize: 12)
        t.textColor = .secondaryLabelColor
        t.preferredMaxLayoutWidth = 540
        return t
    }
}
