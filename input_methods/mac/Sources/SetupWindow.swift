// The setup window: what is written out (Universal or one language's spelling), a live pane that shows a
// typed line both ways, the options, and how to use it. Built in code, framework controls only. Diafon text
// is set in the Diafon fonts, which the app carries (Resources/Fonts), so its marks draw as they should.
import Cocoa
import CoreText

final class SetupWindow: NSObject, NSTextFieldDelegate {
    static let shared = SetupWindow()
    private var window: NSWindow?
    private var input: NSTextField!
    private var previews: NSStackView!
    private var universalRadio: NSButton!
    private var universalSample: NSTextField!
    private var languageRadio: NSButton!
    private var languagePopup: NSPopUpButton!
    private var languageSample: NSTextField!
    private var layoutPopup: NSPopUpButton!
    private var checkActions: [ObjectIdentifier: (Bool) -> Void] = [:]
    private let example = "sj tq aw"                  // sounds, not a word: no word is the same in every language
    private var prefilled = ""                         // what Try it was given, replaced while untouched
    private let width: CGFloat = 520
    private let accent = NSColor(red: 0.055, green: 0.486, blue: 0.525, alpha: 1)

    func show() {
        if window == nil { build() }
        NSApp.activate(ignoringOtherApps: true)
        window?.center()
        window?.makeKeyAndOrderFront(nil)
        refresh()
    }

    /// The Diafon fonts, registered for this process once; nil falls back to the system font.
    static let fontsRegistered: Bool = {
        guard let dir = Bundle.main.resourceURL?.appendingPathComponent("Fonts"),
              let files = try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil) else { return false }
        for f in files where f.pathExtension == "ttf" { CTFontManagerRegisterFontsForURL(f as CFURL, .process, nil) }
        return true
    }()
    private func diafon(_ size: CGFloat, mono: Bool = false) -> NSFont {
        _ = SetupWindow.fontsRegistered
        let name = mono ? "DiafonMono-Regular" : "DiafonSerif-Regular"
        return NSFont(name: name, size: size) ?? (mono ? NSFont.monospacedSystemFont(ofSize: size, weight: .regular) : NSFont.systemFont(ofSize: size))
    }

    private func build() {
        let p = Prefs.shared
        let root = NSStackView()
        root.orientation = .vertical
        root.alignment = .leading
        root.spacing = 6
        root.edgeInsets = NSEdgeInsets(top: 20, left: 24, bottom: 20, right: 24)

        root.addArrangedSubview(header())
        root.addArrangedSubview(note("Type the Diafon input in any app; it turns into the script as you type."))

        // what is written out
        root.addArrangedSubview(gap(10))
        root.addArrangedSubview(heading("Output"))
        universalRadio = NSButton(radioButtonWithTitle: "Universal", target: self, action: #selector(pickUniversal(_:)))
        universalRadio.toolTip = "One letter per sound, the same in every language."
        universalSample = sample("")
        root.addArrangedSubview(line([universalRadio, universalSample]))
        languageRadio = NSButton(radioButtonWithTitle: "A language's spelling", target: self, action: #selector(pickLanguage(_:)))
        languageRadio.toolTip = "The language's own spelling."
        languagePopup = NSPopUpButton(frame: .zero, pullsDown: false)
        for (code, name) in Prefs.languages {
            languagePopup.addItem(withTitle: name)
            languagePopup.lastItem?.representedObject = code
        }
        languagePopup.target = self
        languagePopup.action = #selector(languageChosen(_:))
        languageSample = sample("")
        root.addArrangedSubview(line([languageRadio, languagePopup, languageSample]))

        // the base layout: where the 26 letters sit, whatever layout the Mac had before
        root.addArrangedSubview(gap(10))
        root.addArrangedSubview(heading("Base layout"))
        layoutPopup = NSPopUpButton(frame: .zero, pullsDown: false)
        for l in Layouts.all {
            layoutPopup.addItem(withTitle: l.label)
            layoutPopup.lastItem?.representedObject = l.code
        }
        layoutPopup.target = self
        layoutPopup.action = #selector(layoutChosen(_:))
        root.addArrangedSubview(line([layoutPopup, note("Where the 26 letters sit. Only the placement changes; the typing is the same.", size: 11)]))

        // try it
        root.addArrangedSubview(gap(10))
        root.addArrangedSubview(heading("Try it"))
        input = NSTextField(string: "")
        input.placeholderString = "type here, e.g. \(example)"
        input.font = diafon(14, mono: true)
        input.textColor = accent
        input.delegate = self
        input.widthAnchor.constraint(equalToConstant: width).isActive = true
        root.addArrangedSubview(input)
        previews = NSStackView()
        previews.orientation = .vertical
        previews.alignment = .leading
        previews.spacing = 2
        root.addArrangedSubview(previews)

        // options, each with what it does under it
        root.addArrangedSubview(gap(10))
        root.addArrangedSubview(heading("Options"))
        root.addArrangedSubview(option("Conversion on", p.enabled,
            "Off, Diafon passes your keys through as plain letters.") { Prefs.shared.enabled = $0 })
        root.addArrangedSubview(option("Shift switches", p.shiftToggle,
            "A bare Shift tap turns conversion off and back on. Quick taps in a row walk through Universal and your quick list of languages; ⇧Space opens the language chooser.") { Prefs.shared.shiftToggle = $0 })
        root.addArrangedSubview(option("Tones", p.tones,
            "A digit after a syllable writes its tone, which the Diafon fonts draw above it. Off, tone digits are left out.") { Prefs.shared.tones = $0 })
        root.addArrangedSubview(option("Joined long consonants", p.join,
            "In Universal, a long consonant is written as one joined pair, which the Diafon fonts draw fused; other fonts show the letter twice.") { Prefs.shared.join = $0 })

        // how to, once
        root.addArrangedSubview(gap(10))
        root.addArrangedSubview(heading("How to"))
        root.addArrangedSubview(howto([
            "Pick Diafon in the input menu (⌃Space). The letters sit as the base layout above puts them.",
            "Type a sound as a base, then its operators: sj → \(p.renderer("script")("sj")), tq → \(p.renderer("script")("tq")), aw → \(p.renderer("script")("aw")). The last sound stays underlined until the next key settles it.",
            "To convert text already written: select it, then Diafon menu → Convert selection, or right-click → Services → Convert with Diafon.",
        ]))
        root.addArrangedSubview(gap(6))
        root.addArrangedSubview(note("Spec \(SpecData.generated) · \(SpecData.source)", size: 11))

        let w = NSWindow(contentRect: NSRect(x: 0, y: 0, width: width + 48, height: 600),
                         styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        w.title = "Diafon setup"
        w.contentView = root
        w.setContentSize(root.fittingSize)                 // as tall as what it holds
        w.isReleasedWhenClosed = false
        window = w
        NotificationCenter.default.addObserver(forName: Prefs.changed, object: nil, queue: .main) { [weak self] _ in self?.refresh() }
    }

    @objc private func pickUniversal(_ sender: NSButton) { Prefs.shared.output = "script" }

    @objc private func pickLanguage(_ sender: NSButton) { Prefs.shared.language = Prefs.shared.language }

    @objc private func languageChosen(_ sender: NSPopUpButton) {
        if let code = sender.selectedItem?.representedObject as? String { Prefs.shared.language = code }
    }

    @objc private func layoutChosen(_ sender: NSPopUpButton) {
        if let code = sender.selectedItem?.representedObject as? String { Prefs.shared.layout = code }
    }

    @objc private func checkChanged(_ sender: NSButton) { checkActions[ObjectIdentifier(sender)]?(sender.state == .on) }

    func controlTextDidChange(_ obj: Notification) { refresh() }

    /// The window follows the settings: the radios, the popup, a sample in Universal and in the chosen
    /// spelling (the language's own sample, its first clause), and the typed line both ways.
    private func refresh() {
        guard let previews = previews else { return }
        let p = Prefs.shared
        universalRadio.state = p.universal ? .on : .off
        languageRadio.state = p.universal ? .off : .on
        if let i = layoutPopup.itemArray.firstIndex(where: { ($0.representedObject as? String) == p.layout }) { layoutPopup.selectItem(at: i) }
        let code = p.language
        if let i = languagePopup.itemArray.firstIndex(where: { ($0.representedObject as? String) == code }) {
            languagePopup.selectItem(at: i)
        }
        // the chosen language's own sample, written both ways; Try it starts on it
        let st = SpecData.stages[code]
        let src = (st != nil && !st!.sample.isEmpty) ? st!.sample : example
        let clause = src.split(separator: ",").first.map(String.init) ?? src
        universalSample.stringValue = p.renderer("script")(clause)
        languageSample.stringValue = p.renderer("stage:\(code)")(clause)
        if input.stringValue == prefilled { input.stringValue = clause; prefilled = clause }

        previews.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let typed = input.stringValue
        for (value, label) in [("script", "Universal"), ("stage:\(code)", st?.name ?? code)] {
            let l = NSTextField(labelWithString: label)
            l.font = NSFont.systemFont(ofSize: 11)
            l.textColor = .secondaryLabelColor
            l.widthAnchor.constraint(equalToConstant: 80).isActive = true
            let v = NSTextField(wrappingLabelWithString: p.renderer(value)(typed))
            v.font = diafon(18)
            v.preferredMaxLayoutWidth = width - 90
            previews.addArrangedSubview(line([l, v]))
        }
    }

    // ---- pieces
    private func header() -> NSView {
        var views: [NSView] = []
        if let path = Bundle.main.path(forResource: "Diafon", ofType: "icns"), let img = NSImage(contentsOfFile: path) {
            let iv = NSImageView(image: img)
            iv.imageScaling = .scaleProportionallyUpOrDown
            iv.widthAnchor.constraint(equalToConstant: 32).isActive = true
            iv.heightAnchor.constraint(equalToConstant: 32).isActive = true
            views.append(iv)
        }
        let t = NSTextField(labelWithString: "Diafon")
        t.font = diafon(22)
        views.append(t)
        let row = line(views)
        row.alignment = .centerY
        return row
    }
    /// A checkbox and, under its label, one line of what it does.
    private func option(_ label: String, _ on: Bool, _ what: String, onChange: @escaping (Bool) -> Void) -> NSView {
        let b = NSButton(checkboxWithTitle: label, target: self, action: #selector(checkChanged(_:)))
        b.state = on ? .on : .off
        checkActions[ObjectIdentifier(b)] = onChange
        let d = note(what, size: 11, indent: 20)
        let col = NSStackView(views: [b, d])
        col.orientation = .vertical
        col.alignment = .leading
        col.spacing = 1
        col.edgeInsets = NSEdgeInsets(top: 2, left: 0, bottom: 4, right: 0)
        return col
    }
    private func howto(_ lines: [String]) -> NSView {
        let col = NSStackView()
        col.orientation = .vertical
        col.alignment = .leading
        col.spacing = 4
        for (i, text) in lines.enumerated() {
            let num = NSTextField(labelWithString: "\(i + 1)")
            num.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
            num.textColor = accent
            num.widthAnchor.constraint(equalToConstant: 14).isActive = true
            let t = NSTextField(wrappingLabelWithString: text)
            t.font = NSFont.systemFont(ofSize: 12)
            t.preferredMaxLayoutWidth = width - 22
            col.addArrangedSubview(line([num, t]))
        }
        return col
    }
    private func line(_ views: [NSView]) -> NSStackView {
        let row = NSStackView(views: views)
        row.orientation = .horizontal
        row.alignment = .firstBaseline
        row.spacing = 8
        return row
    }
    private func sample(_ s: String) -> NSTextField {
        let t = NSTextField(labelWithString: s)
        t.font = diafon(15)
        t.textColor = .secondaryLabelColor
        return t
    }
    private func heading(_ s: String) -> NSTextField {
        let t = NSTextField(labelWithString: s)
        t.font = NSFont.systemFont(ofSize: 13, weight: .semibold)
        return t
    }
    private func note(_ s: String, size: CGFloat = 12, indent: CGFloat = 0) -> NSView {
        let t = NSTextField(wrappingLabelWithString: s)
        t.font = NSFont.systemFont(ofSize: size)
        t.textColor = .secondaryLabelColor
        t.preferredMaxLayoutWidth = width - indent
        guard indent > 0 else { return t }
        let box = NSStackView(views: [t])
        box.edgeInsets = NSEdgeInsets(top: 0, left: indent, bottom: 0, right: 0)
        return box
    }
    private func gap(_ h: CGFloat) -> NSView {
        let v = NSView()
        v.heightAnchor.constraint(equalToConstant: h).isActive = true
        return v
    }
}
