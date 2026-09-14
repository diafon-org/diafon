// The setup window: what is written out, the toggles, and a live pane that shows a typed line in every spelling. Built
// in code, framework controls only.
import Cocoa

final class SetupWindow: NSObject, NSTextFieldDelegate {
    static let shared = SetupWindow()
    private var window: NSWindow?
    private var input: NSTextField!
    private var previews: NSStackView!
    private var outputRadios: [NSButton] = []
    private var radioActions: [ObjectIdentifier: (String) -> Void] = [:]
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

        root.addArrangedSubview(title("Diafon"))
        root.addArrangedSubview(note("One keyboard, one script, every language. Type the input form in any app; the conversion happens as you type and commits as soon as a segment is final."))

        root.addArrangedSubview(heading("What is written out"))
        root.addArrangedSubview(note("Universal writes one letter per sound, the same in every language. A language's spelling writes today's orthography."))
        outputRadios = radios(Prefs.outputs, current: p.output, samples: true, group: 1) { Prefs.shared.output = $0 }
        outputRadios.forEach { root.addArrangedSubview($0) }

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
        root.addArrangedSubview(check("A bare Shift tap flips conversion on and off", p.shiftToggle) { Prefs.shared.shiftToggle = $0 })
        root.addArrangedSubview(check("Tone digits", p.tones) { Prefs.shared.tones = $0 })
        root.addArrangedSubview(note("Convert text typed with any keyboard: select it in any app, then Services → Convert with Diafon, or ⇧⌘D."))
        root.addArrangedSubview(note("Spec \(SpecData.generated) · \(SpecData.source)"))

        let w = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 600, height: 700),
                         styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        w.title = "Diafon setup"
        w.contentView = root
        w.isReleasedWhenClosed = false
        window = w
        NotificationCenter.default.addObserver(forName: Prefs.changed, object: nil, queue: .main) { [weak self] _ in self?.refresh() }
    }

    private func radios(_ options: [(String, String)], current: String, samples: Bool, group: Int,
                        onPick: @escaping (String) -> Void) -> [NSButton] {
        let p = Prefs.shared
        return options.map { (value, label) in
            var text = label
            if samples {
                let st = value.hasPrefix("stage:") ? SpecData.stages[String(value.dropFirst(6))] : nil
                let src = (st != nil && !st!.sample.isEmpty) ? st!.sample : neutral
                let firstClause = src.split(separator: ",").first.map(String.init) ?? src
                text += "    " + p.renderer(value)(firstClause)
            }
            let b = NSButton(radioButtonWithTitle: text, target: self, action: #selector(radioPicked(_:)))
            b.identifier = NSUserInterfaceItemIdentifier(value)
            b.state = value == current ? .on : .off
            b.tag = group
            radioActions[ObjectIdentifier(b)] = onPick
            return b
        }
    }

    @objc private func radioPicked(_ sender: NSButton) {
        guard let value = sender.identifier?.rawValue else { return }
        for b in outputRadios { b.state = b === sender ? .on : .off }
        radioActions[ObjectIdentifier(sender)]?(value)
    }

    private func check(_ label: String, _ on: Bool, onChange: @escaping (Bool) -> Void) -> NSButton {
        let b = NSButton(checkboxWithTitle: label, target: self, action: #selector(checkChanged(_:)))
        b.state = on ? .on : .off
        checkActions[ObjectIdentifier(b)] = onChange
        return b
    }

    @objc private func checkChanged(_ sender: NSButton) { checkActions[ObjectIdentifier(sender)]?(sender.state == .on) }

    func controlTextDidChange(_ obj: Notification) { refresh() }

    private func refresh() {
        guard let previews = previews else { return }
        previews.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let typed = input.stringValue
        for (value, label) in Prefs.outputs {
            let row = NSStackView()
            row.orientation = .horizontal
            row.alignment = .firstBaseline
            row.spacing = 10
            let l = NSTextField(labelWithString: label.lowercased())
            l.font = NSFont.monospacedSystemFont(ofSize: 10, weight: .medium)
            l.textColor = .secondaryLabelColor
            l.widthAnchor.constraint(equalToConstant: 120).isActive = true
            let v = NSTextField(labelWithString: Prefs.shared.renderer(value)(typed))
            v.font = NSFont(name: "Georgia", size: 17) ?? NSFont.systemFont(ofSize: 17)
            row.addArrangedSubview(l)
            row.addArrangedSubview(v)
            previews.addArrangedSubview(row)
        }
        let p = Prefs.shared
        for b in outputRadios { b.state = b.identifier?.rawValue == p.output ? .on : .off }
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
