/// UIInputViewController subclass — wires the keyboard view to the engine and text proxy.
import UIKit

final class KeyboardViewController: UIInputViewController {

    private var keyboardView: KeyboardView!
    private var engine: MappingEngine!

    // Fixed keyboard height (portrait phone).  Landscape / iPad gets same value for now.
    private let keyboardHeight: CGFloat = 226

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()

        let (mappings, modifiers) = loadMappings()
        engine = MappingEngine(mappings: mappings, modifierKeys: modifiers)

        keyboardView = KeyboardView()
        keyboardView.delegate = self
        keyboardView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(keyboardView)

        NSLayoutConstraint.activate([
            keyboardView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            keyboardView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            keyboardView.topAnchor.constraint(equalTo: view.topAnchor),
            keyboardView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])

        // Tell the system how tall this keyboard should be.
        let hc = view.heightAnchor.constraint(equalToConstant: keyboardHeight)
        hc.priority = UILayoutPriority(999)
        hc.isActive = true
    }

    // Reset engine whenever the user moves to a different text field.
    override func textWillChange(_ textInput: (any UITextInput)?) {
        engine.reset()
    }

    // MARK: - Mappings

    private struct MappingsFile: Decodable {
        let mappings: [String: String]
        let modifierKeys: [String]?
        enum CodingKeys: String, CodingKey {
            case mappings
            case modifierKeys = "modifier_keys"
        }
    }

    private func loadMappings() -> (mappings: [String: String], modifierKeys: Set<Character>) {
        guard
            let url  = Bundle(for: KeyboardViewController.self)
                         .url(forResource: "mappings", withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let file = try? JSONDecoder().decode(MappingsFile.self, from: data)
        else { return ([:], []) }
        let modifiers = Set((file.modifierKeys ?? []).compactMap { $0.first })
        return (file.mappings, modifiers)
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
            engine.reset()
            proxy.deleteBackward()

        case .shift, .switchToMode:
            break   // managed inside KeyboardView
        }
    }
}
