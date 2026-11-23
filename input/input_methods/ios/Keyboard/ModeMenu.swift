// The menu a hold on the space bar opens: Diafon, the languages on the
// quick list, and off (plain keys). Slide to an item and let go, or let
// go anywhere and tap one; a tap outside the menu closes it.
import UIKit

final class ModeMenu: UIView {
    var onPick: ((String) -> Void)?
    var onClose: (() -> Void)?

    private let card = UIView()
    private var items: [(id: String, title: String)] = []
    private var labels: [UILabel] = []
    private var current = ""
    private var lit: Int?

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = UIColor.black.withAlphaComponent(0.08)
        card.backgroundColor = Theme.key
        card.layer.cornerRadius = 10
        card.layer.shadowColor = UIColor.black.cgColor
        card.layer.shadowOpacity = 0.25
        card.layer.shadowRadius = 6
        card.layer.shadowOffset = CGSize(width: 0, height: 2)
        addSubview(card)
        isHidden = true
    }
    required init?(coder: NSCoder) { fatalError() }

    /// Open by the key at `anchor` (this view's coordinates).
    func present(_ items: [(id: String, title: String)], current: String, anchor: CGRect) {
        self.items = items; self.current = current; lit = nil
        labels.forEach { $0.removeFromSuperview() }
        labels = items.map { item in
            let l = UILabel()
            l.text = "  " + item.title
            l.font = .systemFont(ofSize: 16, weight: item.id == current ? .semibold : .regular)
            l.textColor = Theme.ink
            l.layer.cornerRadius = 7
            l.layer.masksToBounds = true
            l.isAccessibilityElement = true
            l.accessibilityTraits = .button
            l.accessibilityIdentifier = "menu:" + item.id
            card.addSubview(l)
            return l
        }
        let rowH = min(38, (bounds.height - 12) / CGFloat(max(items.count, 1)))
        let h = rowH * CGFloat(items.count) + 8, w: CGFloat = 220
        // above the key when it fits, else beside it, from the bottom up
        let frame = anchor.minY - 4 >= h
            ? CGRect(x: anchor.minX, y: anchor.minY - 4 - h, width: w, height: h)
            : CGRect(x: anchor.maxX + 6, y: max(4, anchor.maxY - h), width: w, height: h)
        card.frame = frame.offsetBy(dx: min(0, bounds.maxX - 4 - frame.maxX), dy: 0)   // kept on screen
        for (i, l) in labels.enumerated() { l.frame = CGRect(x: 4, y: 4 + CGFloat(i) * rowH, width: w - 8, height: rowH) }
        paint()
        isHidden = false
        accessibilityElements = labels
    }

    func close() { isHidden = true; onClose?() }

    private func index(at p: CGPoint) -> Int? {
        let q = convert(p, to: card)
        return labels.firstIndex { $0.frame.contains(q) }
    }

    private func paint() {
        for (i, l) in labels.enumerated() {
            let on = items[i].id == current
            l.backgroundColor = i == lit ? Theme.accent : on ? Theme.functional : .clear
            l.textColor = i == lit ? Theme.onAccent : on ? Theme.accent : Theme.ink
        }
    }

    /// The finger still down from the hold, moving (this view's coordinates).
    func drag(to p: CGPoint) { guard !isHidden else { return }; let i = index(at: p); if i != lit { lit = i; paint() } }

    /// Let go: the item under the finger, or the menu stays for a tap.
    func release(at p: CGPoint) {
        guard !isHidden else { return }
        lit = nil; paint()
        if let i = index(at: p) { pick(i) }
    }

    private func pick(_ i: Int) {
        isHidden = true
        onPick?(items[i].id)
        onClose?()
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        if let p = touches.first?.location(in: self) { drag(to: p) }
    }
    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        if let p = touches.first?.location(in: self) { drag(to: p) }
    }
    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let p = touches.first?.location(in: self) else { return }
        if let i = index(at: p) { pick(i) } else { close() }
    }
    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) { lit = nil; paint() }

    override func accessibilityPerformEscape() -> Bool { close(); return true }
}
