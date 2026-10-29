// The strip above the keys. While a segment is pending: first the emoji the
// word being typed names (a tap puts the emoji in the word's place), then that
// segment in every spelling, one chip per distinct text, the output in use
// outlined; a tap writes that spelling instead. Idle: the mode and the layout, or, with
// text selected in the app, a chip that converts the selection. The gear on
// the right opens the settings panel.
import UIKit

final class StripView: UIView {
    enum Content {
        case note(String)
        case spellings([(output: String, text: String, label: String)], current: String, warn: Bool, emoji: [String])
        case convert(String)
    }

    var onPick: ((String) -> Void)?
    var onEmoji: ((String) -> Void)?
    var onConvert: (() -> Void)?
    var onGear: (() -> Void)?

    private let scroll = UIScrollView()
    private let row = UIStackView()
    private let gear = UIButton(type: .system)
    static let height: CGFloat = 44

    override init(frame: CGRect) {
        super.init(frame: frame)
        scroll.showsHorizontalScrollIndicator = false
        row.axis = .horizontal
        row.spacing = 6
        row.alignment = .center
        gear.setImage(UIImage(systemName: "gearshape"), for: .normal)
        gear.tintColor = Theme.muted
        gear.addAction(UIAction { [weak self] _ in self?.onGear?() }, for: .touchUpInside)
        gear.accessibilityLabel = "Diafon settings"
        for v in [scroll, gear] as [UIView] { v.translatesAutoresizingMaskIntoConstraints = false; addSubview(v) }
        row.translatesAutoresizingMaskIntoConstraints = false
        scroll.addSubview(row)
        NSLayoutConstraint.activate([
            gear.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -4),
            gear.centerYAnchor.constraint(equalTo: centerYAnchor),
            gear.widthAnchor.constraint(equalToConstant: 40),
            scroll.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 6),
            scroll.trailingAnchor.constraint(equalTo: gear.leadingAnchor, constant: -4),
            scroll.topAnchor.constraint(equalTo: topAnchor),
            scroll.bottomAnchor.constraint(equalTo: bottomAnchor),
            row.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor),
            row.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor),
            row.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor),
            row.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor),
            row.heightAnchor.constraint(equalTo: scroll.frameLayoutGuide.heightAnchor),
        ])
    }
    required init?(coder: NSCoder) { fatalError() }

    func show(_ content: Content) {
        row.arrangedSubviews.forEach { $0.removeFromSuperview() }
        switch content {
        case .note(let s):
            let l = UILabel()
            l.text = s
            l.font = .systemFont(ofSize: 14)
            l.textColor = Theme.muted
            row.addArrangedSubview(l)
        case .spellings(let list, let current, let warn, let emoji):
            for e in emoji {
                row.addArrangedSubview(emojiChip(e) { [weak self] in self?.onEmoji?(e) })
            }
            if !emoji.isEmpty {
                let bar = UIView()
                bar.backgroundColor = Theme.muted.withAlphaComponent(0.35)
                bar.widthAnchor.constraint(equalToConstant: 1).isActive = true
                bar.heightAnchor.constraint(equalToConstant: 24).isActive = true
                row.addArrangedSubview(bar)
            }
            for item in list {
                let on = item.output == current
                row.addArrangedSubview(chip(item.text, item.label, color: warn ? Theme.warn : on ? Theme.accent : Theme.ink, outlined: on) { [weak self] in
                    self?.onPick?(item.text)
                })
            }
        case .convert(let target):
            row.addArrangedSubview(chip("Convert selection", "to " + target, color: Theme.accent, outlined: true) { [weak self] in
                self?.onConvert?()
            })
        }
        scroll.contentOffset = .zero
    }

    private func emojiChip(_ e: String, tap: @escaping () -> Void) -> UIView {
        var cfg = UIButton.Configuration.plain()
        cfg.attributedTitle = AttributedString(e, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 24)]))
        cfg.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 6, bottom: 2, trailing: 6)
        let b = UIButton(configuration: cfg)
        b.accessibilityLabel = e
        b.addAction(UIAction { _ in tap() }, for: .touchUpInside)
        return b
    }

    private func chip(_ big: String, _ small: String, color: UIColor, outlined: Bool, tap: @escaping () -> Void) -> UIView {
        var cfg = UIButton.Configuration.plain()
        cfg.attributedTitle = AttributedString(big, attributes: AttributeContainer([.font: Theme.serif(20), .foregroundColor: color]))
        cfg.attributedSubtitle = AttributedString(small, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 9), .foregroundColor: Theme.muted]))
        cfg.titleAlignment = .center
        cfg.titlePadding = 0
        cfg.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 10, bottom: 2, trailing: 10)
        cfg.background.backgroundColor = Theme.key
        cfg.background.cornerRadius = 8
        if outlined { cfg.background.strokeColor = Theme.accent; cfg.background.strokeWidth = 2 }
        let b = UIButton(configuration: cfg)
        b.accessibilityLabel = "\(big), \(small)"
        b.addAction(UIAction { _ in tap() }, for: .touchUpInside)
        return b
    }
}
