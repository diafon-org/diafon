// The switcher: a small list of the modes beside the caret (Universal, the
// quick list of languages, off), the one in use marked. ⇧Space opens it and a
// second ⇧Space closes it; while it is up, each bare Shift tap puts the next
// mode in use at once, and typing goes on in it. It closes by itself after
// `idle` seconds without a Shift tap. Non-activating, like the Hud: focus
// stays in the app. The chooser (menu → Other language…) sets the quick list.
import Cocoa

final class Switcher {
    static let shared = Switcher()
    static let idle: TimeInterval = 2.5
    private var panel: NSPanel?
    private var stack: NSStackView!
    private var hideWork: DispatchWorkItem?
    private var caret: NSRect?

    var isVisible: Bool { panel?.isVisible ?? false }

    /// Open (or refresh, after a step) beside the caret, and restart the idle timer.
    func show(near caret: NSRect?) {
        if panel == nil { build() }
        guard let panel else { return }
        if caret != nil || !panel.isVisible { self.caret = caret }   // a step keeps the place the switcher opened at
        fill()
        let size = stack.fittingSize
        let w = max(size.width, 160), h = size.height
        var origin: NSPoint
        if let c = self.caret, let screen = NSScreen.screens.first(where: { $0.frame.contains(c.origin) }) ?? NSScreen.main {
            origin = NSPoint(x: c.minX, y: c.minY - h - 8)
            origin.x = min(max(origin.x, screen.visibleFrame.minX + 8), screen.visibleFrame.maxX - w - 8)
            if origin.y < screen.visibleFrame.minY { origin.y = c.maxY + 8 }
        } else if let screen = NSScreen.main {
            origin = NSPoint(x: screen.visibleFrame.midX - w / 2, y: screen.visibleFrame.minY + 90)
        } else { return }
        panel.setFrame(NSRect(origin: origin, size: NSSize(width: w, height: h)), display: true)
        panel.alphaValue = 1
        panel.orderFrontRegardless()
        hideWork?.cancel()
        let work = DispatchWorkItem { [weak self] in self?.hide() }
        hideWork = work
        DispatchQueue.main.asyncAfter(deadline: .now() + Switcher.idle, execute: work)
    }

    func hide() {
        hideWork?.cancel()
        hideWork = nil
        guard let panel, panel.isVisible else { return }
        NSAnimationContext.runAnimationGroup({ ctx in ctx.duration = 0.15; panel.animator().alphaValue = 0 },
                                             completionHandler: { panel.orderOut(nil) })
    }

    /// One row per mode, the one in use on an accent background; a hint line under them.
    private func fill() {
        stack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let p = Prefs.shared, current = p.mode
        for m in p.modes {
            let on = m == current
            let label = NSTextField(labelWithString: p.modeName(m))
            label.font = NSFont.systemFont(ofSize: 13, weight: on ? .semibold : .regular)
            label.textColor = on ? .white : .labelColor
            let row = NSView()
            row.wantsLayer = true
            row.layer?.cornerRadius = 5
            row.layer?.backgroundColor = on ? NSColor.controlAccentColor.cgColor : NSColor.clear.cgColor
            label.translatesAutoresizingMaskIntoConstraints = false
            row.addSubview(label)
            NSLayoutConstraint.activate([
                label.leadingAnchor.constraint(equalTo: row.leadingAnchor, constant: 8),
                label.trailingAnchor.constraint(lessThanOrEqualTo: row.trailingAnchor, constant: -8),
                label.topAnchor.constraint(equalTo: row.topAnchor, constant: 3),
                label.bottomAnchor.constraint(equalTo: row.bottomAnchor, constant: -3),
            ])
            stack.addArrangedSubview(row)
            row.widthAnchor.constraint(equalTo: stack.widthAnchor, constant: -12).isActive = true
        }
        let hint = NSTextField(labelWithString: "⇧ next   ⇧Space close")
        hint.font = NSFont.systemFont(ofSize: 11)
        hint.textColor = .secondaryLabelColor
        stack.addArrangedSubview(hint)
        stack.setCustomSpacing(6, after: stack.arrangedSubviews[stack.arrangedSubviews.count - 2])
    }

    private func build() {
        let p = NSPanel(contentRect: NSRect(x: 0, y: 0, width: 160, height: 100),
                        styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        p.level = .statusBar
        p.isOpaque = false
        p.backgroundColor = .clear
        p.hasShadow = true
        p.ignoresMouseEvents = true
        p.collectionBehavior = [.canJoinAllSpaces, .transient]
        let bg = NSVisualEffectView(frame: p.contentView!.bounds)
        bg.autoresizingMask = [.width, .height]
        bg.material = .hudWindow
        bg.state = .active
        bg.wantsLayer = true
        bg.layer?.cornerRadius = 9
        bg.layer?.masksToBounds = true
        p.contentView = bg
        stack = NSStackView()
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 1
        stack.edgeInsets = NSEdgeInsets(top: 6, left: 6, bottom: 6, right: 6)
        stack.translatesAutoresizingMaskIntoConstraints = false
        bg.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: bg.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: bg.trailingAnchor),
            stack.topAnchor.constraint(equalTo: bg.topAnchor),
            stack.bottomAnchor.constraint(equalTo: bg.bottomAnchor),
        ])
        panel = p
    }
}
