import SwiftUI

struct ContentView: View {

    private let installSteps = [
        "Open the Settings app.",
        "Go to General → Keyboard → Keyboards.",
        "Tap \"Add New Keyboard…\"",
        "Select Latin22 from the list.",
    ]

    var body: some View {
        NavigationView {
            List {

                // ── What is it ────────────────────────────────────────────
                Section("What is it") {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Latin22 is a keyboard that lets you type accented and special characters using short, phonetic two-key sequences — no layout switching, no long-press menus.")
                        Text("You type a base letter followed by a modifier key. The keyboard instantly substitutes the correct character. Everything stays on the standard QWERTY layout you already know.")
                    }
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .padding(.vertical, 4)
                }

                // ── How to install ────────────────────────────────────────
                Section("How to install") {
                    ForEach(Array(installSteps.enumerated()), id: \.offset) { i, step in
                        HStack(alignment: .top, spacing: 12) {
                            Text("\(i + 1)")
                                .font(.caption.bold())
                                .foregroundStyle(.secondary)
                                .frame(width: 18, alignment: .center)
                            Text(step)
                        }
                        .padding(.vertical, 2)
                    }
                }

                // ── How to use ────────────────────────────────────────────
                Section("How to use") {
                    VStack(alignment: .leading, spacing: 10) {
                        HowToRow(symbol: "1.circle",
                                 title: "Type a sequence",
                                 text: "Press a base letter, then the modifier key. For example: \"a\" + \"q\" → á, \"o\" + \"w\" → ö.")
                        HowToRow(symbol: "2.circle",
                                 title: "Substitution fires immediately",
                                 text: "The characters appear the moment you press the modifier — no confirmation needed.")
                        HowToRow(symbol: "3.circle",
                                 title: "Escape by repeating the modifier",
                                 text: "Press the modifier twice to cancel substitution and get the raw letters: \"ny\" + \"y\" → ny.")
                        HowToRow(symbol: "4.circle",
                                 title: "Switch keyboards",
                                 text: "Use the globe key (system bar, below the keyboard) to cycle to other keyboards.")
                    }
                    .padding(.vertical, 4)
                }
            }
            .navigationTitle("Latin22")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - HowToRow

private struct HowToRow: View {
    let symbol: String
    let title: String
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: symbol)
                .foregroundStyle(Color.accentColor)
                .font(.title3)
                .frame(width: 28)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.body.bold())
                Text(text).font(.callout).foregroundStyle(.secondary)
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(ProfileStore())
}
