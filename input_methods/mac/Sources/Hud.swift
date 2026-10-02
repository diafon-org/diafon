// A small floating label that names the mode for a moment after a switch
// (off · Universal · a language), near the caret when the app tells us where
// it is, else at the bottom middle of the screen. Non-activating: focus stays.
import Cocoa

final class Hud {
    static let shared = Hud()
    private var panel: NSPanel?
    private var label: NSTextField!
    private var hideWork: DispatchWorkItem?

    func show(_ text: String, near caret: NSRect?) {
        if panel == nil { build() }
        guard let panel = panel else { return }
        label.stringValue = text
        label.sizeToFit()
        let w = label.frame.width + 28, h: CGFloat = 34
        var origin: NSPoint
        if let c = caret, c.width >= 0, let screen = NSScreen.screens.first(where: { $0.frame.contains(c.origin) }) ?? NSScreen.main {
            origin = NSPoint(x: c.minX, y: c.minY - h - 8)
            origin.x = min(max(origin.x, screen.visibleFrame.minX + 8), screen.visibleFrame.maxX - w - 8)
            if origin.y < screen.visibleFrame.minY { origin.y = c.maxY + 8 }
        } else if let screen = NSScreen.main {
            origin = NSPoint(x: screen.visibleFrame.midX - w / 2, y: screen.visibleFrame.minY + 90)
        } else { return }
        panel.setFrame(NSRect(origin: origin, size: NSSize(width: w, height: h)), display: true)
        label.frame = NSRect(x: 14, y: (h - label.frame.height) / 2, width: label.frame.width, height: label.frame.height)
        panel.alphaValue = 1
        panel.orderFrontRegardless()
        hideWork?.cancel()
        let work = DispatchWorkItem { [weak self] in
            NSAnimationContext.runAnimationGroup({ ctx in ctx.duration = 0.25; self?.panel?.animator().alphaValue = 0 },
                                                 completionHandler: { self?.panel?.orderOut(nil) })
        }
        hideWork = work
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.1, execute: work)
    }

    private func build() {
        let p = NSPanel(contentRect: NSRect(x: 0, y: 0, width: 120, height: 34),
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
        label = NSTextField(labelWithString: "")
        label.font = NSFont.systemFont(ofSize: 13, weight: .medium)
        label.textColor = .labelColor
        bg.addSubview(label)
        panel = p
    }
}
