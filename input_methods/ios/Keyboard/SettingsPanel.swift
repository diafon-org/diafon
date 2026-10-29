// The settings, inside the keyboard: without full access a keyboard shares no
// storage with its app, so this is where they are set (the gear on the strip,
// or a long press on Dia). Two choices for the output, Universal or a
// language's spelling, the language from one row; never every spelling flat.
import UIKit

final class SettingsPanel: UIView {
    var onDone: (() -> Void)?

    private let prefs = Prefs.shared
    private let stack = UIStackView()
    private let output = UISegmentedControl(items: ["Universal", "Language"])
    private let languages = UIStackView()
    private let layoutPicker = UISegmentedControl(items: Layouts.all.map(\.label))
    private let sample = UILabel()
    private let tones = UISwitch(), strict = UISwitch(), marked = UISwitch()

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

        languages.axis = .horizontal
        languages.spacing = 6
        let langScroll = UIScrollView()
        langScroll.showsHorizontalScrollIndicator = false
        languages.translatesAutoresizingMaskIntoConstraints = false
        langScroll.addSubview(languages)
        NSLayoutConstraint.activate([
            languages.leadingAnchor.constraint(equalTo: langScroll.contentLayoutGuide.leadingAnchor),
            languages.trailingAnchor.constraint(equalTo: langScroll.contentLayoutGuide.trailingAnchor),
            languages.topAnchor.constraint(equalTo: langScroll.contentLayoutGuide.topAnchor),
            languages.bottomAnchor.constraint(equalTo: langScroll.contentLayoutGuide.bottomAnchor),
            languages.heightAnchor.constraint(equalTo: langScroll.frameLayoutGuide.heightAnchor),
            langScroll.heightAnchor.constraint(equalToConstant: 34),
        ])
        stack.addArrangedSubview(langScroll)

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

        stack.addArrangedSubview(toggle(tones, "Keep tone digits") { [weak self] in self?.prefs.tones = $0; self?.refresh() })
        stack.addArrangedSubview(toggle(strict, "Mark ill-formed letters on the strip") { [weak self] in self?.prefs.strict = $0 })
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
        for (code, name) in Prefs.languages {
            var cfg = UIButton.Configuration.plain()
            let on = !prefs.universal && code == prefs.language
            cfg.attributedTitle = AttributedString(name, attributes: AttributeContainer([.font: UIFont.systemFont(ofSize: 15), .foregroundColor: on ? Theme.onAccent : Theme.ink]))
            cfg.background.backgroundColor = on ? Theme.accent : Theme.key
            cfg.background.cornerRadius = 8
            cfg.contentInsets = NSDirectionalEdgeInsets(top: 4, leading: 10, bottom: 4, trailing: 10)
            let b = UIButton(configuration: cfg)
            b.addAction(UIAction { [weak self] _ in self?.prefs.language = code; self?.refresh() }, for: .touchUpInside)
            languages.addArrangedSubview(b)
        }
        let st = SpecData.stages[prefs.language]
        let typed = st?.sample ?? ""
        sample.text = typed.isEmpty ? "" : "\(typed)  →  \(prefs.renderer()(typed))"
        layoutPicker.selectedSegmentIndex = Layouts.all.firstIndex { $0.code == prefs.layout } ?? 0
        tones.isOn = prefs.tones
        strict.isOn = prefs.strict
        marked.isOn = prefs.tailMode == .marked
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
