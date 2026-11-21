// The settings, inside the keyboard: without full access a keyboard shares no
// storage with its app, so this is where they are set (a hold on the logo
// key): what is written (Universal, a language's spelling, or plain keys), the
// languages to choose from (up to Prefs.quickMax ticked), and the input profile.
import UIKit

final class SettingsPanel: UIView {
    var onDone: (() -> Void)?

    private let prefs = Prefs.shared
    private let stack = UIStackView()
    private let modeRow = UIStackView()
    private let quickRow = UIStackView()
    private let profilePicker = UISegmentedControl(items: Profiles.all.map(\.name))
    private let layoutPicker = UISegmentedControl(items: Layouts.all.map(\.label))
    private let sample = UILabel()
    private let tones = UISwitch(), autoCaps = UISwitch(), marked = UISwitch()

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

        stack.addArrangedSubview(caption("Writes"))
        stack.addArrangedSubview(scrolled(modeRow))
        stack.addArrangedSubview(caption("Languages"))
        stack.addArrangedSubview(scrolled(quickRow))
        stack.addArrangedSubview(caption("Tick up to \(Prefs.quickMax). Hold the space bar to switch between Universal and those the typing below can write."))

        profilePicker.addAction(UIAction { [weak self] _ in
            guard let self else { return }
            self.prefs.profile = Profiles.all[self.profilePicker.selectedSegmentIndex].id
            self.refresh()
        }, for: .valueChanged)
        stack.addArrangedSubview(caption("Typing"))
        stack.addArrangedSubview(profilePicker)

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
        stack.addArrangedSubview(toggle(marked, "Underline what is being typed (Contacts and some other apps drop it on Done)") { [weak self] in self?.prefs.tailMode = $0 ? .marked : .replace })
        let hint = caption("Turn this off if an app duplicates or drops letters while you type.")
        hint.numberOfLines = 0
        stack.addArrangedSubview(hint)

        refresh()
    }
    required init?(coder: NSCoder) { fatalError() }

    func refresh() {
        modeRow.arrangedSubviews.forEach { $0.removeFromSuperview() }
        for m in prefs.menuModes {                      // Universal, the ticked languages, off
            let on = prefs.menuMode == m
            modeRow.addArrangedSubview(chip(prefs.menuTitle(m), fill: Theme.key, ink: on ? Theme.accent : Theme.ink, outline: on) { [weak self] in
                self?.prefs.setMenuMode(m)
                self?.refresh()
            })
        }
        profilePicker.selectedSegmentIndex = Profiles.all.firstIndex { $0.id == prefs.profile } ?? 0
        quickRow.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let quick = prefs.quickLanguages
        let full = quick.count >= Prefs.quickMax
        for (code, name) in Prefs.languages {
            let inMenu = quick.contains(code)
            let b = chip(inMenu ? "✓ \(name)" : name, fill: Theme.key, ink: inMenu ? Theme.accent : Theme.ink, outline: inMenu) { [weak self] in
                guard let self else { return }
                if inMenu {
                    guard quick.count > 1 else { return }       // one at least, for the language spellings
                    let universal = self.prefs.universal
                    self.prefs.setQuick(code, false)
                    if self.prefs.language == code, let first = self.prefs.quickLanguages.first {
                        self.prefs.language = first             // the language in use stays on the list
                        if universal { self.prefs.output = "script" }
                    }
                } else if !full {
                    self.prefs.setQuick(code, true)
                }
                self.refresh()
            }
            b.alpha = (!inMenu && full) || !prefs.offers(code) ? 0.4 : 1    // dim: the list is full, or the typing in use cannot write it
            quickRow.addArrangedSubview(b)
        }
        let st = SpecData.stages[prefs.language]
        let typed = st?.sample ?? ""                    // the language's own sample (universal-v1 forms), in the output in use
        sample.text = typed.isEmpty ? "" : (prefs.profileData.table ? prefs.formRenderer()(typed) : "\(typed)  →  \(prefs.formRenderer()(typed))")
        layoutPicker.selectedSegmentIndex = Layouts.all.firstIndex { $0.code == prefs.layout } ?? 0
        tones.isOn = prefs.tones
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
