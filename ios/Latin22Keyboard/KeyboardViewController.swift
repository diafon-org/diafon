/// UIInputViewController subclass — wires the keyboard view to the engine and text proxy.
import UIKit

// MARK: - KeyboardViewController

final class KeyboardViewController: UIInputViewController {

    private var keyboardView: KeyboardView!
    private var engine: MappingEngine?

    // Fixed keyboard height — matches iOS 26 Liquid Glass key area on iPhone 14 portrait.
    private let keyboardHeight: CGFloat = 216

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()

        keyboardView = KeyboardView()
        keyboardView.delegate = self
        // showsEmojiKey is updated in applyKeyboardPrefs() which runs once the
        // background engine load completes — avoids blocking on activeInputModes here.
        keyboardView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(keyboardView)

        NSLayoutConstraint.activate([
            keyboardView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            keyboardView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            keyboardView.topAnchor.constraint(equalTo: view.topAnchor),
            keyboardView.heightAnchor.constraint(equalToConstant: keyboardHeight),
        ])

        // Tell the system how tall this keyboard should be.
        let hc = view.heightAnchor.constraint(equalToConstant: keyboardHeight)
        hc.priority = UILayoutPriority(999)
        hc.isActive = true

        // Rounded top corners — match system keyboard container shape.
        view.layer.cornerRadius = 12
        view.layer.maskedCorners = [.layerMinXMinYCorner, .layerMaxXMinYCorner]
        view.clipsToBounds = true

        // Decode mappings.json + create engine on a background thread so the
        // keyboard appears instantly without blocking the main thread.
        loadMappingsInBackground()

        // iOS 26 Liquid Glass: keyboard background is a blurred chrome material,
        // not a solid color. UIVisualEffectView handles both light and dark automatically.
        view.backgroundColor = .clear
        let blur = UIVisualEffectView(effect: UIBlurEffect(style: .systemChromeMaterial))
        blur.translatesAutoresizingMaskIntoConstraints = false
        view.insertSubview(blur, at: 0)
        NSLayoutConstraint.activate([
            blur.topAnchor.constraint(equalTo: view.topAnchor),
            blur.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            blur.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            blur.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        // Sync prefs after the view is fully on-screen (active input modes
        // may not be populated until after the keyboard is visible).
        applyKeyboardPrefs()
    }

    // Reload mappings each time the keyboard appears so profile changes
    // made in the app take effect without restarting the extension process.
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        guard cachedMappingsFile != nil else {
            // First launch — engine is being loaded in background by viewDidLoad's
            // loadMappingsInBackground(); nothing to do here.
            return
        }
        // Subsequent appearances — cached file is ready, rebuild engine fast.
        let (mappings, modifiers) = loadMappings()
        engine = MappingEngine(mappings: mappings, modifierKeys: modifiers)
        applyKeyboardPrefs()
        syncKeyboardLanguages()
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        keyboardView.cancelDeleteTimer()
    }

    // Reset engine and discard any pending writes whenever focus leaves the field.
    override func textWillChange(_ textInput: (any UITextInput)?) {
        engine?.reset()
        writeQueue.removeAll(keepingCapacity: true)
        isDrainingWrites = false
    }

    // MARK: - Mappings

    /// Shape of `mappings.json` — v3.x language+layers format.
    private struct MappingsFile: Decodable {
        struct Layer: Decodable {
            let id: String
            let modifierKeys: [String]
            let mappings: [String: String]
            enum CodingKeys: String, CodingKey {
                case id, mappings
                case modifierKeys = "modifier_keys"
            }
        }
        struct LanguageEntry: Decodable {
            let id: String
            let name: String
            let layers: [Layer]
        }
        let languages: [LanguageEntry]
        let defaultLanguageID: String
        let defaultLayerIDs:   [String]
        enum CodingKeys: String, CodingKey {
            case languages
            case defaultLanguageID = "default_language_id"
            case defaultLayerIDs   = "default_layer_ids"
        }
    }

    /// Parses bundled mappings.json once on a background queue; thread-safe via
    /// `isLoadingMappings`. Only accessed/written on the main thread after decode.
    private var cachedMappingsFile: MappingsFile? = nil
    private var isLoadingMappings = false

    // MARK: - Background mapping load

    /// Decodes mappings.json and creates the engine on a background thread, then
    /// posts results to the main thread. Safe to call multiple times — only runs once.
    private func loadMappingsInBackground() {
        guard !isLoadingMappings, cachedMappingsFile == nil else { return }
        isLoadingMappings = true
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }
            guard
                let url  = Bundle(for: KeyboardViewController.self)
                              .url(forResource: "mappings", withExtension: "json"),
                let data = try? Data(contentsOf: url),
                let file = try? JSONDecoder().decode(MappingsFile.self, from: data)
            else {
                DispatchQueue.main.async { self.isLoadingMappings = false }
                return
            }
            let suite        = UserDefaults(suiteName: "group.com.latin22.shared")
            let activeLangID = suite?.string(forKey: "activeLanguageID") ?? file.defaultLanguageID
            let layerIDs     = Set(suite?.stringArray(forKey: "activeLayerIDs") ?? file.defaultLayerIDs)
            guard let lang = file.languages.first(where: { $0.id == activeLangID })
                             ?? file.languages.first else {
                DispatchQueue.main.async { self.isLoadingMappings = false }
                return
            }
            let activeLayers = lang.layers
                .filter { layerIDs.contains($0.id) }
                .sorted { $0.id < $1.id }
            var mergedMappings: [String: String] = [:]
            var mergedMods:     Set<Character>   = []
            for layer in activeLayers {
                mergedMappings.merge(layer.mappings) { _, new in new }
                mergedMods.formUnion(layer.modifierKeys.compactMap { $0.first })
            }
            let eng = MappingEngine(mappings: mergedMappings, modifierKeys: mergedMods)
            DispatchQueue.main.async { [weak self] in
                guard let self else { return }
                self.cachedMappingsFile = file
                self.engine = eng
                self.isLoadingMappings = false
                self.applyKeyboardPrefs()
                self.syncKeyboardLanguages()
            }
        }
    }

    private func loadMappings() -> (mappings: [String: String], modifierKeys: Set<Character>) {
        guard let file = cachedMappingsFile else { return ([:], []) }

        let suite        = UserDefaults(suiteName: "group.com.latin22.shared")
        let activeLangID = suite?.string(forKey: "activeLanguageID") ?? file.defaultLanguageID
        let layerIDs     = Set(suite?.stringArray(forKey: "activeLayerIDs") ?? file.defaultLayerIDs)

        guard let lang = file.languages.first(where: { $0.id == activeLangID })
                         ?? file.languages.first
        else { return ([:], []) }

        let activeLayers = lang.layers
            .filter  { layerIDs.contains($0.id) }
            .sorted  { $0.id < $1.id }   // stable merge order
        var mergedMappings: [String: String] = [:]
        var mergedMods:     Set<Character>   = []
        for layer in activeLayers {
            mergedMappings.merge(layer.mappings) { _, new in new }
            mergedMods.formUnion(layer.modifierKeys.compactMap { $0.first })
        }
        return (mergedMappings, mergedMods)
    }

    private func syncKeyboardLanguages() {
        guard let file = cachedMappingsFile else { return }
        let suite        = UserDefaults(suiteName: "group.com.latin22.shared")
        let activeLangID = suite?.string(forKey: "activeLanguageID") ?? file.defaultLanguageID
        keyboardView.availableLanguages = file.languages.map { (id: $0.id, name: $0.name) }
        keyboardView.currentLanguageID  = activeLangID
    }

    private func applyKeyboardPrefs() {
        let suite = UserDefaults(suiteName: "group.com.latin22.shared")
        let emojiPref    = (suite?.object(forKey: "emojiKeyEnabled")    as? Bool) ?? true
        let spacebarPref = (suite?.object(forKey: "spacebarLangSwitch") as? Bool) ?? true
        let systemHasEmoji = UITextInputMode.activeInputModes.contains { $0.primaryLanguage == "emoji" }
        keyboardView.showsEmojiKey             = emojiPref && systemHasEmoji
        keyboardView.spacebarLangSwitchEnabled = spacebarPref
    }

    private func switchLanguage(to langID: String) {
        guard let file = cachedMappingsFile,
              let lang = file.languages.first(where: { $0.id == langID })
        else { return }
        let defaultLayerIDs = lang.layers
            .sorted { $0.id < $1.id }
            .prefix(1)
            .map(\.id)
        let layerIDSet = Set(defaultLayerIDs)
        let suite = UserDefaults(suiteName: "group.com.latin22.shared")
        suite?.set(langID,          forKey: "activeLanguageID")
        suite?.set(defaultLayerIDs, forKey: "activeLayerIDs")

        // Build mappings directly from the resolved lang+layers instead of
        // re-reading UserDefaults (write may not have flushed yet).
        let activeLayers = lang.layers
            .filter  { layerIDSet.contains($0.id) }
            .sorted  { $0.id < $1.id }
        var mergedMappings: [String: String] = [:]
        var mergedMods:     Set<Character>   = []
        for layer in activeLayers {
            mergedMappings.merge(layer.mappings) { _, new in new }
            mergedMods.formUnion(layer.modifierKeys.compactMap { $0.first })
        }
        engine = MappingEngine(mappings: mergedMappings, modifierKeys: mergedMods)
        engine?.reset()
        keyboardView.currentLanguageID = langID
    }

    // MARK: - Input queue
    //
    // The engine is called synchronously on touch-down so its state is always
    // in step with the key sequence — regardless of IPC timing.
    // The resulting write operations (insert / delete) are queued and applied
    // to the proxy on the next run-loop pass.
    //
    // Consecutive inserts are merged into one item so a burst of plain characters
    // costs a single proxy.insertText() call. Substitutions reclaim preceding
    // queued inserts in-memory (no IPC) before falling back to deleteBackward().

    private enum QueuedWrite {
        case insert(String)
        case delete
    }

    private var writeQueue: ContiguousArray<QueuedWrite> = []
    private var isDrainingWrites = false

    // MARK: Engine integration (called synchronously on touch-down)

    private func enqueueChar(_ c: Character, raw: String) {
        if case .replace(let n, let text) = engine?.process(c) {
            enqueueReplace(deleteCount: n, insert: text)
        } else {
            enqueueInsert(raw)
        }
    }

    private func enqueueInsert(_ s: String) {
        // Merge with the last queued insert so bursts become one insertText() call.
        if !writeQueue.isEmpty, case .insert(let prev) = writeQueue[writeQueue.count - 1] {
            writeQueue[writeQueue.count - 1] = .insert(prev + s)
        } else {
            writeQueue.append(.insert(s))
        }
        scheduleDrain()
    }

    private func enqueueReplace(deleteCount n: Int, insert text: String) {
        // Reclaim up to n-1 chars from the tail of the write queue in-memory
        // (they haven't reached the proxy yet — zero IPC needed).
        // Any remainder targets text already committed to the proxy.
        var remaining = n - 1
        while remaining > 0, !writeQueue.isEmpty {
            guard case .insert(let s) = writeQueue[writeQueue.count - 1] else { break }
            if s.count <= remaining {
                remaining -= s.count
                writeQueue.removeLast()
            } else {
                writeQueue[writeQueue.count - 1] = .insert(String(s.dropLast(remaining)))
                remaining = 0
            }
        }
        for _ in 0..<remaining { writeQueue.append(.delete) }
        writeQueue.append(.insert(text))
        scheduleDrain()
    }

    private func scheduleDrain() {
        guard !isDrainingWrites else { return }
        isDrainingWrites = true
        DispatchQueue.main.async { [weak self] in self?.drainWrites() }
    }

    private func drainWrites() {
        let items = writeQueue
        writeQueue.removeAll(keepingCapacity: true)
        isDrainingWrites = false
        let proxy = textDocumentProxy
        for item in items {
            switch item {
            case .insert(let s): proxy.insertText(s)
            case .delete:        proxy.deleteBackward()
            }
        }
        // Catch up if new writes arrived during IPC.
        if !writeQueue.isEmpty {
            isDrainingWrites = true
            DispatchQueue.main.async { [weak self] in self?.drainWrites() }
        }
    }
}

// MARK: - KeyboardViewDelegate

extension KeyboardViewController: KeyboardViewDelegate {

    func keyboardView(_ view: KeyboardView, didProduceAction action: KeyActionType) {
        switch action {

        case .character(let s):
            if let c = s.unicodeScalars.first.map(Character.init) {
                enqueueChar(c, raw: s)  // engine called synchronously here
            } else {
                enqueueInsert(s)        // emoji / multi-scalar, bypass engine
            }

        case .space:
            engine?.reset()
            enqueueInsert(" ")

        case .returnKey:
            engine?.reset()
            enqueueInsert("\n")

        case .backspace:
            engine?.processBackspace()
            writeQueue.append(.delete)
            scheduleDrain()

        case .nextKeyboard:
            advanceToNextInputMode()

        case .emojiKeyboard:
            break   // handled inside KeyboardView via EmojiPickerView

        case .switchLanguage(let id):
            switchLanguage(to: id)

        case .shift, .switchToMode:
            break   // managed inside KeyboardView
        }
    }
}
