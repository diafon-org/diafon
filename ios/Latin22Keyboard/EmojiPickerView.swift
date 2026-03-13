import UIKit

// MARK: - Emoji data (loaded from emojis.json)
//
// emojis.json schema:
//   tabs:  [{ id, symbolName }]          — ordered tab definitions
//   emoji: [{ char, tabs: [tabId, ...] }]  — master list; tabs:[] = unused (not shown)
//
// To add/remove/reassign emoji, edit emojis.json only — no code changes needed.

private struct EmojiTab {
    let id: String
    let symbolName: String
    var emoji: [String] = []
}

private func loadEmojiTabs() -> [EmojiTab] {
    guard
        let url  = Bundle(for: EmojiPickerView.self).url(forResource: "emojis", withExtension: "json"),
        let data = try? Data(contentsOf: url),
        let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
        let rawTabs  = root["tabs"]  as? [[String: Any]],
        let rawEmoji = root["emoji"] as? [[String: Any]]
    else { return [] }

    var tabs = rawTabs.compactMap { t -> EmojiTab? in
        guard let id = t["id"] as? String, let sym = t["symbolName"] as? String else { return nil }
        return EmojiTab(id: id, symbolName: sym)
    }
    // Index tabs by id for fast lookup
    var tabIndex = [String: Int]()
    for (i, t) in tabs.enumerated() { tabIndex[t.id] = i }

    // Distribute emoji into tabs preserving order
    for entry in rawEmoji {
        guard
            let char = entry["char"] as? String,
            let assignedIDs = entry["tabs"] as? [String]
        else { continue }
        for tid in assignedIDs {
            if let i = tabIndex[tid] { tabs[i].emoji.append(char) }
        }
    }
    // Drop tabs that ended up with no emoji
    return tabs.filter { !$0.emoji.isEmpty }
}

private let kEmojiTabs: [EmojiTab] = loadEmojiTabs()

// MARK: - Clip data

struct CoubClip {
    let id: String
    let title: String
    var url: String { "https://coub.com/view/\(id)" }
}

private struct ClipCategory {
    let symbolName: String
    let name: String
    let clips: [CoubClip]
}

private func loadClipCategories() -> [ClipCategory] {
    guard
        let url  = Bundle(for: EmojiPickerView.self).url(forResource: "clips", withExtension: "json"),
        let data = try? Data(contentsOf: url),
        let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
        let cats = root["categories"] as? [[String: Any]]
    else { return [] }

    return cats.compactMap { cat in
        guard
            let sym     = cat["symbolName"]  as? String,
            let name    = cat["name"]         as? String,
            let rawClips = cat["clips"]       as? [[String: Any]]
        else { return nil }
        let clips = rawClips.compactMap { c -> CoubClip? in
            guard let id = c["id"] as? String, let title = c["title"] as? String else { return nil }
            return CoubClip(id: id, title: title)
        }
        return ClipCategory(symbolName: sym, name: name, clips: clips)
    }
}

private let kClipCategories: [ClipCategory] = loadClipCategories()

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
    private var selectedCategory = 0   // 0..<kEmojiTabs.count = emoji; above = clips

    private var isClipsTab: Bool { selectedCategory >= kEmojiTabs.count }
    private var clipsIndex: Int  { selectedCategory - kEmojiTabs.count }

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
        // Emoji category tabs
        for (i, cat) in kEmojiTabs.enumerated() {
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
        // Clips tabs (film.stack icon per category)
        for (i, cat) in kClipCategories.enumerated() {
            let btn = UIButton(type: .custom)
            btn.tag = kEmojiTabs.count + i
            let sym = cat.symbolName.isEmpty ? "film.stack" : cat.symbolName
            if let img = UIImage(systemName: sym)?
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

        // Collection view — two cell types: emoji and clips
        collectionView.register(EmojiCell.self,  forCellWithReuseIdentifier: "emoji")
        collectionView.register(ClipCell.self,   forCellWithReuseIdentifier: "clip")
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
        isClipsTab
            ? kClipCategories[clipsIndex].clips.count
            : kEmojiTabs[selectedCategory].emoji.count
    }
    func collectionView(_ cv: UICollectionView, cellForItemAt ip: IndexPath) -> UICollectionViewCell {
        if isClipsTab {
            let cell = cv.dequeueReusableCell(withReuseIdentifier: "clip", for: ip) as! ClipCell
            cell.configure(with: kClipCategories[clipsIndex].clips[ip.item])
            return cell
        } else {
            let cell = cv.dequeueReusableCell(withReuseIdentifier: "emoji", for: ip) as! EmojiCell
            cell.label.text = kEmojiTabs[selectedCategory].emoji[ip.item]
            return cell
        }
    }
}

// MARK: - UICollectionViewDelegate / FlowLayout

extension EmojiPickerView: UICollectionViewDelegate {
    func collectionView(_ cv: UICollectionView, didSelectItemAt ip: IndexPath) {
        if isClipsTab {
            let clip = kClipCategories[clipsIndex].clips[ip.item]
            delegate?.emojiPickerView(self, didSelectEmoji: clip.url)
        } else {
            let emoji = kEmojiTabs[selectedCategory].emoji[ip.item]
            delegate?.emojiPickerView(self, didSelectEmoji: emoji)
        }
    }
}

extension EmojiPickerView: UICollectionViewDelegateFlowLayout {
    func collectionView(_ cv: UICollectionView, layout _: UICollectionViewLayout,
                        sizeForItemAt _: IndexPath) -> CGSize {
        if isClipsTab {
            // Clips: 2 columns, taller cells with title
            let cols: CGFloat = 2
            let gap:  CGFloat = 8
            let w = floor((cv.bounds.width - gap * (cols + 1)) / cols)
            return CGSize(width: w, height: w * 0.65)
        } else {
            let cols = floor(cv.bounds.width / 40)
            let side = cols > 0 ? floor(cv.bounds.width / cols) : 40
            return CGSize(width: side, height: side)
        }
    }

    func collectionView(_ cv: UICollectionView, layout _: UICollectionViewLayout,
                        insetForSectionAt _: Int) -> UIEdgeInsets {
        isClipsTab ? UIEdgeInsets(top: 8, left: 8, bottom: 8, right: 8) : .zero
    }

    func collectionView(_ cv: UICollectionView, layout _: UICollectionViewLayout,
                        minimumInteritemSpacingForSectionAt _: Int) -> CGFloat {
        isClipsTab ? 8 : 0
    }

    func collectionView(_ cv: UICollectionView, layout _: UICollectionViewLayout,
                        minimumLineSpacingForSectionAt _: Int) -> CGFloat {
        isClipsTab ? 8 : 0
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

// MARK: - ClipCell

private final class ClipCell: UICollectionViewCell {
    private let thumbView = UIImageView()
    private let titleLabel = UILabel()
    private let linkIcon = UIImageView()

    override init(frame: CGRect) {
        super.init(frame: frame)
        contentView.layer.cornerRadius = 8
        contentView.clipsToBounds = true

        thumbView.contentMode = .scaleAspectFill
        thumbView.backgroundColor = UIColor.systemIndigo.withAlphaComponent(0.25)
        thumbView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(thumbView)

        // Play icon overlay
        let symConf = UIImage.SymbolConfiguration(pointSize: 22, weight: .medium)
        linkIcon.image = UIImage(systemName: "play.circle.fill", withConfiguration: symConf)
        linkIcon.tintColor = .white
        linkIcon.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(linkIcon)

        // Title bar at bottom
        let bar = UIView()
        bar.backgroundColor = UIColor.black.withAlphaComponent(0.55)
        bar.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(bar)

        titleLabel.font = .systemFont(ofSize: 11, weight: .medium)
        titleLabel.textColor = .white
        titleLabel.numberOfLines = 1
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        bar.addSubview(titleLabel)

        NSLayoutConstraint.activate([
            thumbView.topAnchor.constraint(equalTo: contentView.topAnchor),
            thumbView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            thumbView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            thumbView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),

            linkIcon.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            linkIcon.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),

            bar.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            bar.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            bar.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
            bar.heightAnchor.constraint(equalToConstant: 22),

            titleLabel.leadingAnchor.constraint(equalTo: bar.leadingAnchor, constant: 6),
            titleLabel.trailingAnchor.constraint(equalTo: bar.trailingAnchor, constant: -6),
            titleLabel.centerYAnchor.constraint(equalTo: bar.centerYAnchor),
        ])
    }
    required init?(coder: NSCoder) { fatalError() }

    func configure(with clip: CoubClip) {
        titleLabel.text = clip.title
        // Load thumbnail from Coub's thumb CDN — tiny JPEG, no auth required.
        // Falls back gracefully to the indigo placeholder if network is unavailable
        // (keyboard without RequestsOpenAccess shows placeholder; with access shows image).
        let thumbURL = URL(string: "https://coub.com/api/v2/coubs/\(clip.id)")
        thumbView.image = nil
        if let url = thumbURL {
            URLSession.shared.dataTask(with: url) { [weak self] data, _, _ in
                guard
                    let data = data,
                    let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                    let imageVersions = json["image_versions"] as? [String: Any],
                    let versions = imageVersions["versions"] as? [String: Any],
                    let small = (versions["small"] ?? versions["med"] ?? versions["big"]) as? [String: Any],
                    let imgURLStr = small["url"] as? String,
                    let imgURL = URL(string: imgURLStr)
                else { return }
                URLSession.shared.dataTask(with: imgURL) { data, _, _ in
                    guard let data = data, let img = UIImage(data: data) else { return }
                    DispatchQueue.main.async { self?.thumbView.image = img }
                }.resume()
            }.resume()
        }
    }
}
