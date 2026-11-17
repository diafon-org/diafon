// The settings, inside the keyboard: without full access a keyboard shares no
// storage with its app, so this is where they are set (Settings… on the menu
// a hold on the logo key opens). Two choices for the output, Universal or a
// language's spelling, the language from one row; never every spelling flat.
import UIKit

final class SettingsPanel: UIView {
    var onDone: (() -> Void)?

    private let prefs = Prefs.shared
    private let stack = UIStackView()
    private let output = UISegmentedControl(items: ["Universal", "Language"])
    private let languages = UIStackView()
    private let quickRow = UIStackView()
    private let layoutPicker = UISegmentedControl(items: Layouts.all.map(\.label))
    private let sample = UILabel()
    private let tones = UISwitch(), join = UISwitch(), autoCaps = UISwitch(), marked = UISwitch()

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = Theme.board

        let scroll = UIScrollView()
        scroll.translatesAutoresizingMaskIntoConstraints = false
        addSubview(scroll)
        stack.axis = .vertical
        stack.spacing = 10
        stack.translatesAutoresizingMaskIntoConstraints = false
        scroll.addSubview(stack)
        NSLayoutConstraint.activate([
            scroll.leadingAnchor.constraint(equalTo: leadingAnchor), scroll.trailingAnchor.constraint(equalTo: trailingAnchor),
            scroll.topAnchor.constraint(equalTo: topAnchor), scroll.bottomAnchor.constraint(equalTo: bottomAnchor),
            stack.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor, constant: 12),
            stack.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor, constant: -12),
            stack.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor, constant: 8),
            stack.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor, constant: -12),
            stack.widthAnchor.constraint(equalTo: scroll.frameLayoutGuide.widthAnchor, constant: -24),
        ])

        let title = UILabel()
        title.text = "Diafon"
        title.font = .systemFont(ofSize: 17, weight: .semibold)
        title.textColor = Theme.ink
        let done = UIButton(type: .system)
        done.setTitle("Done", for: .normal)
        done.titleLabel?.font = .systemFont(ofSize: 17, weight: .semibold)
        done.tintColor = Theme.accent
        done.addAction(UIAction { [weak self] _ in self?.onDone?() }, for: .touchUpInside)
        stack.addArrangedSubview(hrow([title, UIView(), done]))

        output.addAction(UIAction { [weak self] _ in
            guard let self else { return }
            if self.output.selectedSegmentIndex == 0 { self.prefs.output = "script" } else { self.prefs.language = self.prefs.language }
            self.refresh()
        }, for: .valueChanged)
        stack.addArrangedSubview(output)

        stack.addArrangedSubview(scrolled(languages))
        stack.addArrangedSubview(caption("Tap a language to write its spelling."))
        stack.addArrangedSubview(caption("On the space bar's menu (hold space)"))
        stack.addArrangedSubview(scrolled(quickRow))
        stack.addArrangedSubview(caption("Tap to put a language on the menu or take it off; as many as you like."))

        sample.numberOfLines = 0
        sample.font = Theme.serif(17)
        sample.textColor = Theme.ink
        stack.addArrangedSubview(sample)

        layoutPicker.addAction(UIAction { [weak self] _ in
            guard let self else { return }
            self.prefs.layout = Layouts.all[self.layoutPicker.selectedSegmentIndex].code
        }, for: .valueChanged)
        stack.addArrangedSubview(caption("Layout"))
        stack.addArrangedSubview(layoutPicker)

        stack.addArrangedSubview(toggle(tones, "Tones") { [weak self] in self?.prefs.tones = $0; self?.refresh() })
        stack.addArrangedSubview(toggle(autoCaps, "Capital at a sentence start") { [weak self] in self?.prefs.autoCaps = $0 })
        stack.addArrangedSubview(toggle(join, "Join long consonants") { [weak self] in self?.prefs.join = $0; self?.refresh() })
        stack.addArrangedSubview(toggle(marked, "Underline the letter being typed") { [weak self] in self?.prefs.tailMode = $0 ? .marked : .replace })
        let hint = caption("Turn this off if an app duplicates or drops letters while you type.")
        hint.numberOfLines = 0
        stack.addArrangedSubview(hint)

        refresh()
    }
    required init?(coder: NSCoder) { fatalError() }

    func refresh() {
        output.selectedSegmentIndex = prefs.universal ? 0 : 1
        languages.arrangedSubviews.forEach { $0.removeFromSuperview() }
        quickRow.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let quick = prefs.quickLanguages
        for (code, name) in Prefs.languages {
            let on = !prefs.universal && code == prefs.language
            languages.addArrangedSubview(chip(name, fill: on ? Theme.accent : Theme.key, ink: on ? Theme.onAccent : Theme.ink) { [weak self] in
                self?.prefs.language = code; self?.refresh()
            })
            let inMenu = quick.contains(code)
            quickRow.addArrangedSubview(chip(inMenu ? "✓ \(code)" : code, fill: Theme.key, ink: inMenu ? Theme.accent : Theme.muted, outline: inMenu) { [weak self] in
                self?.prefs.setQuick(code, !inMenu); self?.refresh()
            })
        }
        let st = SpecData.stages[prefs.language]
        let typed = st?.sample ?? ""                    // the language's own sample, in the output in use
        sample.text = typed.isEmpty ? "" : "\(typed)  →  \(prefs.renderer()(typed))"
        layoutPicker.selectedSegmentIndex = Layouts.all.firstIndex { $0.code == prefs.layout } ?? 0
        tones.isOn = prefs.tones
        join.isOn = prefs.join
        autoCaps.isOn = prefs.autoCaps
        marked.isOn = prefs.tailMode == .marked
    }

    /// A row of chips that scrolls sideways.
    private func scrolled(_ row: UIStackView) -> UIView {
        row.axis = .horizontal
        row.spacing = 6
        let sc = UIScrollView()
        sc.showsHorizontalScrollIndicator = false
        row.translatesAutoresizingMaskIntoConstraints = false
        sc.addSubview(row)
        NSLayoutConstraint.activate([
            row.leadingAnchor.constraint(equalTo: sc.contentLayoutGuide.leadingAnchor),
            row.trailingAnchor.constraint(equalTo: sc.contentLayoutGuide.trailingAnchor),
            row.topAnchor.constraint(equalTo: sc.contentLayoutGuide.topAnchor),
            row.bottomAnchor.constraint(equalTo: sc.contentLayoutGuide.bottomAnchor),
            row.heightAnchor.constraint(equalTo: sc.frameLayoutGuide.heightAnchor),
            sc.heightAnchor.constraint(equalToConstant: 34),
        ])
        return sc
    }

    private func chip(_ title: String, fill: UIColor, ink: UIColor, outline: Bool = false, tap: @escaping () -> Void) -> UIButton {
        var cfg = UIButton.Configuration.plain()
        cfg.attributedTitle = AttributedString(title, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 15), .foregroundColor: ink]))
        cfg.background.backgroundColor = fill
        cfg.background.cornerRadius = 8
        if outline { cfg.background.strokeColor = Theme.accent; cfg.background.strokeWidth = 2 }
        cfg.contentInsets = NSDirectionalEdgeInsets(top: 4, leading: 10, bottom: 4, trailing: 10)
        let b = UIButton(configuration: cfg)
        b.addAction(UIAction { _ in tap() }, for: .touchUpInside)
        return b
    }

    private func hrow(_ views: [UIView]) -> UIStackView {
        let s = UIStackView(arrangedSubviews: views)
        s.axis = .horizontal
        s.alignment = .center
        s.spacing = 8
        return s
    }

    private func caption(_ s: String) -> UILabel {
        let l = UILabel()
        l.text = s
        l.font = .systemFont(ofSize: 13)
        l.textColor = Theme.muted
        l.numberOfLines = 0
        return l
    }

    private func toggle(_ sw: UISwitch, _ text: String, _ changed: @escaping (Bool) -> Void) -> UIView {
        let l = UILabel()
        l.text = text
        l.font = .systemFont(ofSize: 15)
        l.textColor = Theme.ink
        l.numberOfLines = 0
        sw.onTintColor = Theme.accent
        sw.addAction(UIAction { _ in changed(sw.isOn) }, for: .valueChanged)
        return hrow([l, UIView(), sw])
    }
}
