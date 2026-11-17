// The strip above the keys, the keyboard's top row. Between words it is the
// digit row; inside a word, once the word names something (its emoji), the
// suggestions take the digits' place, and a tap puts one in the word's place.
// With text selected in the app, a chip that converts the selection.
import UIKit

final class StripView: UIView {
    enum Content: Equatable {
        case digits
        case emoji([String])
        case convert(String)
    }

    var onDigit: ((Character) -> Void)?
    var onEmoji: ((String) -> Void)?
    var onConvert: (() -> Void)?

    private let digits = UIStackView()
    private let scroll = UIScrollView()
    private let row = UIStackView()
    private var shown: Content?
    static let height: CGFloat = 44

    override init(frame: CGRect) {
        super.init(frame: frame)
        digits.axis = .horizontal
        digits.distribution = .fillEqually
        digits.spacing = 6
        for d in "1234567890" {
            var cfg = UIButton.Configuration.plain()
            cfg.attributedTitle = AttributedString(String(d), attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 20), .foregroundColor: Theme.ink]))
            cfg.contentInsets = .zero
            let b = UIButton(configuration: cfg)
            b.accessibilityIdentifier = "key:\(d)"
            b.accessibilityLabel = String(d)
            b.addAction(UIAction { [weak self] _ in UIDevice.current.playInputClick(); self?.onDigit?(d) }, for: .touchDown)
            digits.addArrangedSubview(b)
        }
        scroll.showsHorizontalScrollIndicator = false
        row.axis = .horizontal
        row.spacing = 6
        row.alignment = .center
        for v in [digits, scroll] as [UIView] { v.translatesAutoresizingMaskIntoConstraints = false; addSubview(v) }
        row.translatesAutoresizingMaskIntoConstraints = false
        scroll.addSubview(row)
        NSLayoutConstraint.activate([
            digits.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 3),
            digits.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -3),
            digits.topAnchor.constraint(equalTo: topAnchor),
            digits.bottomAnchor.constraint(equalTo: bottomAnchor),
            scroll.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 6),
            scroll.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -6),
            scroll.topAnchor.constraint(equalTo: topAnchor),
            scroll.bottomAnchor.constraint(equalTo: bottomAnchor),
            row.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor),
            row.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor),
            row.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor),
            row.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor),
            row.heightAnchor.constraint(equalTo: scroll.frameLayoutGuide.heightAnchor),
        ])
        show(.digits)
    }
    required init?(coder: NSCoder) { fatalError() }

    func show(_ content: Content) {
        guard content != shown else { return }        // the digits keep their touch between keys
        shown = content
        digits.isHidden = content != .digits
        scroll.isHidden = content == .digits
        row.arrangedSubviews.forEach { $0.removeFromSuperview() }
        switch content {
        case .digits: break
        case .emoji(let list):
            for e in list { row.addArrangedSubview(emojiChip(e) { [weak self] in self?.onEmoji?(e) }) }
        case .convert(let target):
            row.addArrangedSubview(chip("Convert selection", "to " + target) { [weak self] in self?.onConvert?() })
        }
        scroll.contentOffset = .zero
    }

    private func emojiChip(_ e: String, tap: @escaping () -> Void) -> UIView {
        var cfg = UIButton.Configuration.plain()
        cfg.attributedTitle = AttributedString(e, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 26)]))
        cfg.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 8, bottom: 2, trailing: 8)
        let b = UIButton(configuration: cfg)
        b.accessibilityLabel = e
        b.addAction(UIAction { _ in tap() }, for: .touchUpInside)
        return b
    }

    private func chip(_ big: String, _ small: String, tap: @escaping () -> Void) -> UIView {
        var cfg = UIButton.Configuration.plain()
        cfg.attributedTitle = AttributedString(big, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 16), .foregroundColor: Theme.accent]))
        cfg.attributedSubtitle = AttributedString(small, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 9), .foregroundColor: Theme.muted]))
        cfg.titleAlignment = .center
        cfg.titlePadding = 0
        cfg.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 10, bottom: 2, trailing: 10)
        cfg.background.backgroundColor = Theme.key
        cfg.background.cornerRadius = 8
        cfg.background.strokeColor = Theme.accent
        cfg.background.strokeWidth = 2
        let b = UIButton(configuration: cfg)
        b.accessibilityLabel = "\(big), \(small)"
        b.addAction(UIAction { _ in tap() }, for: .touchUpInside)
        return b
    }
}
