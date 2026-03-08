import SwiftUI

struct ContentView: View {

    private let steps = [
        "Open the Settings app.",
        "Go to General → Keyboard → Keyboards.",
        "Tap Add New Keyboard…",
        "Select Latin 2 from the list.",
        "While typing anywhere, tap the 🌐 key to switch to Latin 2.",
        "Tap 🌐 again to switch back to your default keyboard.",
    ]

    private let samples: [(String, String)] = [
        ("ny", "ņ"), ("nyy", "ny  (escape)"), ("yy", "y  (escape)"),
    ]

    var body: some View {
        NavigationView {
            List {
                Section(header: Text("Setup")) {
                    ForEach(Array(steps.enumerated()), id: \.offset) { i, step in
                        HStack(alignment: .top, spacing: 12) {
                            Text("\(i + 1)")
                                .font(.caption.bold())
                                .foregroundColor(.secondary)
                                .frame(width: 18, alignment: .center)
                            Text(step)
                                .font(.body)
                        }
                        .padding(.vertical, 2)
                    }
                }

                Section(header: Text("Sequences"), footer: Text("More sequences can be added by editing mappings.json in the project.")) {
                    ForEach(samples, id: \.0) { seq, rep in
                        HStack {
                            Text(seq)
                                .font(.system(.body, design: .monospaced))
                                .frame(width: 80, alignment: .leading)
                            Image(systemName: "arrow.right")
                                .foregroundColor(.secondary)
                                .font(.caption)
                            Text(rep)
                        }
                    }
                }

                Section(header: Text("How it works")) {
                    Text("While the Latin 2 keyboard is active, type any defined sequence. The keyboard detects it automatically and replaces it with the mapped Unicode character. Tap 🌐 to go back to your normal keyboard at any time.")
                        .font(.callout)
                        .foregroundColor(.secondary)
                        .padding(.vertical, 4)
                }
            }
            .navigationTitle("Latin 2")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview { ContentView() }
