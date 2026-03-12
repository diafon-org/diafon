import UIKit

// MARK: - Data

private struct EmojiCategory {
    let symbolName: String
    let emoji: [String]
}

private let kEmojiCategories: [EmojiCategory] = [
    EmojiCategory(symbolName: "face.smiling", emoji: [
        "😀","😃","😄","😁","😆","😅","🤣","😂","🙂","🙃","😉","😊","😇",
        "🥰","😍","🤩","😘","☺️","😋","😛","😜","🤪","😝","🤑","🤗","🤔",
        "🤐","🤨","😐","😑","😏","😒","🙄","😬","😌","😔","😪","😴","😷",
        "🤒","🤕","🤧","🥵","🥶","😵","🤯","🤠","😎","🤓","😕","😟","🙁",
        "☹️","😮","😲","😳","🥺","😦","😨","😰","😥","😢","😭","😱","😤",
        "😡","😠","🤬","😈","👿","💀","💩","🤡","👹","👺","👻","👽","👾",
        "🤖","👋","🤚","🖐","✋","🖖","👌","✌️","🤞","🤟","🤘","👈","👉",
        "👆","👇","👍","👎","✊","👊","👏","🙌","🤝","🙏","💪","💋",
        "👶","👦","👧","🧑","👨","👩","👴","👵",
    ]),
    EmojiCategory(symbolName: "pawprint", emoji: [
        "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷",
        "🐸","🐵","🙈","🙉","🙊","🐔","🐧","🐦","🐤","🦆","🦅","🦉","🦇",
        "🐺","🐴","🦄","🦋","🐛","🐝","🐌","🐞","🐜","🕷","🦂","🐢","🐍",
        "🦎","🐙","🦑","🦐","🦀","🐡","🐠","🐟","🐬","🐳","🦈","🐊","🐘",
        "🦒","🐕","🐈","🐾",
        "🌵","🎄","🌲","🌳","🌴","🌱","🌿","☘️","🍀","🍃","🍂","🍁","🍄",
        "🌾","💐","🌷","🌹","🌺","🌸","🌼","🌻","🌞","🌙","⭐","🌟","☁️",
        "🌈","❄️","🔥","💧","🌊",
    ]),
    EmojiCategory(symbolName: "fork.knife", emoji: [
        "🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🫐","🍒","🍑","🥭","🍍",
        "🥝","🍅","🥥","🥑","🍆","🥔","🥕","🌽","🥒","🥬","🥦","🧄","🧅",
        "🥜","🌰","🍞","🥐","🥖","🧀","🥚","🍳","🥞","🧇","🥓","🍗","🍖",
        "🌭","🍔","🍟","🍕","🌮","🌯","🥙","🍜","🍝","🍛","🍣","🍱","🥟",
        "🍤","🍰","🎂","🧁","🍭","🍬","🍫","🍿","🍩","🍪","🍯",
        "🧃","🥤","🧋","🍵","☕","🍺","🥂","🍷","🥃","🍸","🍹","🍾",
    ]),
    EmojiCategory(symbolName: "car", emoji: [
        "🚗","🚕","🚙","🚌","🏎","🚓","🚑","🚒","🛻","🚚","🚛","🏍","🛵",
        "🚲","🛴","⛽","🚨","🚥","🚦","🛑","⚓","⛵","🚤","🛥","🚢","✈️",
        "🛩","💺","🚁","🚀","🛸",
        "🌍","🌎","🌏","🧭","🏔","⛰","🌋","🏕","🏖","🏜","🏝","🏠","🏡",
        "🏢","🏥","🏦","🏨","🏪","🏫","🏬","🏭","🏯","🏰","⛪","🕌","⛩",
        "🌁","🌃","🌄","🌅","🌆","🌇","🌉","🗺","🗼","🗽",
    ]),
    EmojiCategory(symbolName: "lightbulb", emoji: [
        "📱","💻","⌨️","🖥","📷","📸","📹","🎥","📺","📻","🔋","🔌","💡",
        "🔦","💸","💵","💰","💳","💎","⚖️","🔧","🔨","⚒","🛠","🔩","🧲",
        "🔪","⚔️","🛡","🔭","🔬","💊","💉","🧬","🧹","🧺","🚽","🚿","🛁",
        "🧴","🧼","🛒","🚪","🛏","🛋",
        "🎊","🎉","🎈","🎀","🎁","🏆","🥇","⚽","🏀","🏈","⚾","🎾","🏐",
        "🎱","🏓","🎯","🎮","🎲","🧩","🎨","🎬","🎤","🎧","🎼","🎹","🥁",
        "🎷","🎺","🎸","🎻",
    ]),
    EmojiCategory(symbolName: "heart", emoji: [
        "❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💔","💕","💞","💓",
        "💗","💖","💘","💝","☮️","✅","❌","⭕","🛑","⛔","🚫","💯","⚠️",
        "✔️","➕","➖","➗","✖️","™️","©️","®️","❗","❕","❓","❔","‼️","⁉️",
        "🔴","🟠","🟡","🟢","🔵","🟣","⚫","⚪",
        "🟥","🟧","🟨","🟩","🟦","🟪","🟫","⬛","⬜",
        "🔶","🔷","🔸","🔹","🔺","🔻","💠","🔘",
        "🏁","🚩","🎌","🏴","🏳️","🏳️‍🌈","🏴‍☠️",
    ]),
]

// MARK: - Protocol

protocol EmojiPickerViewDelegate: AnyObject {
    func emojiPickerView(_ view: EmojiPickerView, didSelectEmoji emoji: String)
    func emojiPickerViewDidDismiss(_ view: EmojiPickerView)
}

// MARK: - EmojiPickerView

final class EmojiPickerView: UIView {

    weak var delegate: EmojiPickerViewDelegate?

    private let collectionView: UICollectionView
    private let tabBar = UIView()
    private let abcButton = UIButton(type: .custom)
    private let categoryStack = UIStackView()
    private var categoryButtons: [UIButton] = []
    private var selectedCategory = 0

    override init(frame: CGRect) {
        let layout = UICollectionViewFlowLayout()
        layout.minimumInteritemSpacing = 0
        layout.minimumLineSpacing = 0
        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        super.init(frame: frame)
        setupUI()
        applyColors()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setupUI() {
        // Tab bar
        tabBar.translatesAutoresizingMaskIntoConstraints = false
        addSubview(tabBar)

        abcButton.setTitle("ABC", for: .normal)
        abcButton.titleLabel?.font = .systemFont(ofSize: 14, weight: .medium)
        abcButton.translatesAutoresizingMaskIntoConstraints = false
        abcButton.addTarget(self, action: #selector(abcTapped), for: .touchUpInside)
        tabBar.addSubview(abcButton)

        categoryStack.axis = .horizontal
        categoryStack.distribution = .fillEqually
        categoryStack.translatesAutoresizingMaskIntoConstraints = false
        tabBar.addSubview(categoryStack)

        let symConf = UIImage.SymbolConfiguration(pointSize: 15, weight: .regular)
        for (i, cat) in kEmojiCategories.enumerated() {
            let btn = UIButton(type: .custom)
            btn.tag = i
            if let img = UIImage(systemName: cat.symbolName)?
                            .withConfiguration(symConf)
                            .withRenderingMode(.alwaysTemplate) {
                btn.setImage(img, for: .normal)
            }
            btn.addTarget(self, action: #selector(categoryTapped(_:)), for: .touchUpInside)
            categoryButtons.append(btn)
            categoryStack.addArrangedSubview(btn)
        }

        NSLayoutConstraint.activate([
            tabBar.leadingAnchor.constraint(equalTo: leadingAnchor),
            tabBar.trailingAnchor.constraint(equalTo: trailingAnchor),
            tabBar.bottomAnchor.constraint(equalTo: bottomAnchor),
            tabBar.heightAnchor.constraint(equalToConstant: 40),

            abcButton.leadingAnchor.constraint(equalTo: tabBar.leadingAnchor),
            abcButton.topAnchor.constraint(equalTo: tabBar.topAnchor),
            abcButton.bottomAnchor.constraint(equalTo: tabBar.bottomAnchor),
            abcButton.widthAnchor.constraint(equalToConstant: 52),

            categoryStack.leadingAnchor.constraint(equalTo: abcButton.trailingAnchor),
            categoryStack.trailingAnchor.constraint(equalTo: tabBar.trailingAnchor),
            categoryStack.topAnchor.constraint(equalTo: tabBar.topAnchor),
            categoryStack.bottomAnchor.constraint(equalTo: tabBar.bottomAnchor),
        ])

        // Collection view
        collectionView.register(EmojiCell.self, forCellWithReuseIdentifier: "cell")
        collectionView.backgroundColor = .clear
        collectionView.showsVerticalScrollIndicator = false
        collectionView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(collectionView)

        NSLayoutConstraint.activate([
            collectionView.topAnchor.constraint(equalTo: topAnchor),
            collectionView.leadingAnchor.constraint(equalTo: leadingAnchor),
            collectionView.trailingAnchor.constraint(equalTo: trailingAnchor),
            collectionView.bottomAnchor.constraint(equalTo: tabBar.topAnchor),
        ])

        refreshCategoryHighlight()
    }

    // MARK: - Appearance

    func applyColors() {
        let dark = traitCollection.userInterfaceStyle == .dark
        let bg:  UIColor = dark ? UIColor(red: 0.173, green: 0.173, blue: 0.180, alpha: 1)
                                : UIColor(red: 0.820, green: 0.831, blue: 0.859, alpha: 1)
        let tab: UIColor = dark ? UIColor(red: 0.227, green: 0.227, blue: 0.247, alpha: 1)
                                : UIColor(red: 0.675, green: 0.694, blue: 0.729, alpha: 1)
        let fg: UIColor  = dark ? .white : .black
        backgroundColor = bg
        tabBar.backgroundColor = tab
        abcButton.setTitleColor(fg, for: .normal)
        categoryButtons.forEach { $0.tintColor = fg }
    }

    override func traitCollectionDidChange(_ prev: UITraitCollection?) {
        super.traitCollectionDidChange(prev)
        applyColors()
    }

    // Set data source lazily once we have real bounds — avoids
    // UICollectionViewFlowLayout asserting 0-items-per-row at init time.
    override func layoutSubviews() {
        super.layoutSubviews()
        if collectionView.dataSource == nil, bounds.width > 0 {
            collectionView.dataSource = self
            collectionView.delegate = self
            collectionView.reloadData()
        }
    }

    private func refreshCategoryHighlight() {
        for (i, btn) in categoryButtons.enumerated() {
            btn.alpha = i == selectedCategory ? 1.0 : 0.45
        }
    }

    @objc private func categoryTapped(_ sender: UIButton) {
        selectedCategory = sender.tag
        refreshCategoryHighlight()
        collectionView.reloadData()
        collectionView.setContentOffset(.zero, animated: false)
    }

    @objc private func abcTapped() {
        delegate?.emojiPickerViewDidDismiss(self)
    }
}

// MARK: - UICollectionViewDataSource

extension EmojiPickerView: UICollectionViewDataSource {
    func collectionView(_ cv: UICollectionView, numberOfItemsInSection _: Int) -> Int {
        kEmojiCategories[selectedCategory].emoji.count
    }
    func collectionView(_ cv: UICollectionView, cellForItemAt ip: IndexPath) -> UICollectionViewCell {
        let cell = cv.dequeueReusableCell(withReuseIdentifier: "cell", for: ip) as! EmojiCell
        cell.label.text = kEmojiCategories[selectedCategory].emoji[ip.item]
        return cell
    }
}

// MARK: - UICollectionViewDelegate / FlowLayout

extension EmojiPickerView: UICollectionViewDelegate {
    func collectionView(_ cv: UICollectionView, didSelectItemAt ip: IndexPath) {
        let emoji = kEmojiCategories[selectedCategory].emoji[ip.item]
        delegate?.emojiPickerView(self, didSelectEmoji: emoji)
    }
}

extension EmojiPickerView: UICollectionViewDelegateFlowLayout {
    func collectionView(_ cv: UICollectionView, layout _: UICollectionViewLayout,
                        sizeForItemAt _: IndexPath) -> CGSize {
        let cols = floor(cv.bounds.width / 40)
        let side = cols > 0 ? floor(cv.bounds.width / cols) : 40
        return CGSize(width: side, height: side)
    }
}

// MARK: - EmojiCell

private final class EmojiCell: UICollectionViewCell {
    let label = UILabel()
    override init(frame: CGRect) {
        super.init(frame: frame)
        label.font = .systemFont(ofSize: 28)
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(label)
        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            label.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
        ])
    }
    required init?(coder: NSCoder) { fatalError() }
}
