/// UIInputViewController subclass — wires the keyboard view to the engine and text proxy.
import UIKit

// MARK: - EmojiTextField

/// Invisible text field whose textInputMode is always the system emoji keyboard.
/// Becoming first responder hands input focus to the emoji keyboard.
private final class EmojiTextField: UITextField {
    override var textInputMode: UITextInputMode? {
        UITextInputMode.activeInputModes.first { $0.primaryLanguage == "emoji" }
    }
}

// MARK: - KeyboardViewController

final class KeyboardViewController: UIInputViewController {

    // iOS 26 shows the globe at the system level below the keyboard.
    // Returning false prevents iOS from injecting its own globe button into our view.
    override var needsInputModeSwitchKey: Bool { false }

    private var keyboardView: KeyboardView!
    private var engine: MappingEngine!
    private let emojiTextField = EmojiTextField()

    // Fixed keyboard height (portrait phone).  Landscape / iPad gets same value for now.
    private let keyboardHeight: CGFloat = 226

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()

        keyboardView = KeyboardView()
        keyboardView.delegate = self
        keyboardView.showsEmojiKey = UITextInputMode.activeInputModes.contains { $0.primaryLanguage == "emoji" }
        keyboardView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(keyboardView)

        // Hidden text field used to hand focus to the system emoji keyboard.
        // Needs a non-zero frame to participate in the responder chain.
        emojiTextField.frame = CGRect(x: 0, y: 0, width: 1, height: 1)
        emojiTextField.alpha = 0
        view.addSubview(emojiTextField)

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

        // Initial load — ensures engine is never nil before viewWillAppear.
        let (mappings, modifiers) = loadMappings()
        engine = MappingEngine(mappings: mappings, modifierKeys: modifiers)
    }

    // Reload mappings each time the keyboard appears so profile changes
    // made in the app take effect without restarting the extension process.
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        let (mappings, modifiers) = loadMappings()
        engine = MappingEngine(mappings: mappings, modifierKeys: modifiers)
        // Re-check here because activeInputModes may not be fully populated at viewDidLoad.
        keyboardView.showsEmojiKey = UITextInputMode.activeInputModes.contains { $0.primaryLanguage == "emoji" }
    }

    // Reset engine whenever the user moves to a different text field.
    override func textWillChange(_ textInput: (any UITextInput)?) {
        engine.reset()
    }

    // MARK: - Mappings

    /// Minimal decodable shape of a profile stored by the app in App Group defaults.
    private struct ActiveProfileData: Decodable {
        let mappings: [String: String]
        let modifierKeys: [String]
    }

    /// Shape of `mappings.json` — v2.0.0 multi-profile format.
    private struct MappingsFile: Decodable {
        struct Entry: Decodable {
            let mappings: [String: String]
            let modifierKeys: [String]
            enum CodingKeys: String, CodingKey {
                case mappings
                case modifierKeys = "modifier_keys"
            }
        }
        let profiles: [Entry]
    }

    private func loadMappings() -> (mappings: [String: String], modifierKeys: Set<Character>) {
        // 1. Use the active profile written by the app to the shared App Group defaults.
        if let suite = UserDefaults(suiteName: "group.com.latin22.shared"),
           let data  = suite.data(forKey: "activeProfile"),
           let prof  = try? JSONDecoder().decode(ActiveProfileData.self, from: data) {
            let mods = Set(prof.modifierKeys.compactMap { $0.first })
            return (prof.mappings, mods)
        }

        // 2. Fall back to the first profile in the bundled mappings.json.
        guard
            let url   = Bundle(for: KeyboardViewController.self)
                          .url(forResource: "mappings", withExtension: "json"),
            let data  = try? Data(contentsOf: url),
            let file  = try? JSONDecoder().decode(MappingsFile.self, from: data),
            let first = file.profiles.first
        else { return ([:], []) }

        let mods = Set(first.modifierKeys.compactMap { $0.first })
        return (first.mappings, mods)
    }

    // MARK: - Applying engine result

    private func apply(_ result: MappingEngine.ProcessResult) {
        guard case .replace(let n, let text) = result else { return }
        let proxy = textDocumentProxy
        (0 ..< n).forEach { _ in proxy.deleteBackward() }
        proxy.insertText(text)
    }
}

// MARK: - KeyboardViewDelegate

extension KeyboardViewController: KeyboardViewDelegate {

    func keyboardView(_ view: KeyboardView, didProduceAction action: KeyActionType) {
        let proxy = textDocumentProxy

        switch action {

        case .character(let s):
            // Insert the character first so the user sees it immediately, then correct.
            proxy.insertText(s)
            guard let c = s.unicodeScalars.first.map(Character.init) else { return }
            apply(engine.process(c))

        case .space:
            engine.flush()
            proxy.insertText(" ")

        case .returnKey:
            engine.flush()
            proxy.insertText("\n")

        case .backspace:
            engine.processBackspace()
            proxy.deleteBackward()

        case .nextKeyboard:
            advanceToNextInputMode()

        case .emojiKeyboard:
            emojiTextField.becomeFirstResponder()

        case .shift, .switchToMode:
            break   // managed inside KeyboardView
        }
    }
}
