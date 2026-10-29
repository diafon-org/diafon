// The keyboard's keystroke logic against a simulated editor, driven by
// tests/test_ios_session.py: Session (input_methods/ios/Shared) over a string
// editor that behaves as UITextInput does (insertText replaces marked text,
// deleteBackward takes one grapheme). Prints "session holds N checks", or
// each failure and exits 1.
//
//   stream    every spec stream trace, in both tail modes: after each key
//             the editor shows the trace's committed text so far plus the
//             render of its pending tail, and the session's tail is the trace's
//   fuzz      seeded random keys and backspaces in every output and both
//             modes, against a model of what the editor should show
//   cases     flush, take, editorChanged (orphaned and kept tails)
import Foundation

final class StringEditor: TextSink {
    var text = ""                      // final text before the cursor
    var marked = ""                    // marked text at the cursor
    var display: String { text + marked }
    func insertText(_ t: String) { marked = ""; text += t }
    func deleteBackward() { if !marked.isEmpty { marked.removeLast() } else if !text.isEmpty { text.removeLast() } }
    func setMarkedText(_ t: String) { marked = t }
    func unmarkText() { text += marked; marked = "" }
    var contextBefore: String? { display }
}

/// A small seeded generator, so a failure replays.
struct Rng { var s: UInt64; mutating func next(_ n: Int) -> Int { s = s &* 6364136223846793005 &+ 1442695040888963407; return Int((s >> 33) % UInt64(n)) } }

@main
enum SessionCheck {
    static var checks = 0, failures: [String] = []
    static func expect(_ ok: Bool, _ what: @autoclosure () -> String) {
        checks += 1
        if !ok { failures.append(what()) }
    }

    static func main() {
        let path = CommandLine.arguments[1]
        let spec = try! JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: path))) as! [String: Any]
        let traces = (spec["vectors"] as! [String: Any])["stream"] as! [String: [[String]]]
        let modes: [TailMode] = [.marked, .replace]

        // stream: the spec traces, key by key
        for (text, trace) in traces.sorted(by: { $0.key < $1.key }) {
            for mode in modes {
                let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: { Engine.lenient($0) })
                var head = ""
                for (ch, step) in zip(text, trace) {
                    s.type(ch)
                    head += step[1]
                    let want = head + (step[2].isEmpty ? "" : Engine.lenient(step[2]))
                    expect(ed.display == want && s.pending == step[2],
                           "stream \(mode) \(text.debugDescription) at \(String(ch).debugDescription): shows \(ed.display.debugDescription), want \(want.debugDescription); pending \(s.pending.debugDescription), want \(step[2].debugDescription)")
                }
                s.flush()
                expect(ed.marked.isEmpty && ed.text == head + (trace.last![2].isEmpty ? "" : Engine.lenient(trace.last![2])),
                       "stream \(mode) \(text.debugDescription): after flush \(ed.text.debugDescription) marked \(ed.marked.debugDescription)")
            }
        }

        // fuzz: random keys in every output, both modes, against a model
        let outputs = ["script", "transport"] + SpecData.stageOrder.map { "stage:" + $0 }
        let keys = Array("sjnzwaeouiqtkcxlrhy1234 ,.SJN") + ["⌫", "⌫"]
        var rng = Rng(s: 0x5eed)
        for out in outputs {
            let render = Prefs.shared.renderer(out)
            for mode in modes {
                for run in 0..<40 {
                    let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: render)
                    var final = "", pending = "", typed = ""
                    for _ in 0..<(8 + rng.next(24)) {
                        let k = keys[rng.next(keys.count)]
                        typed.append(k)
                        if k == "⌫" {
                            s.backspace()
                            if !pending.isEmpty { pending.removeLast() } else if !final.isEmpty { final.removeLast() }
                        } else {
                            s.type(k)
                            let (h, t) = Engine.stream(pending + String(k), renderer: render)
                            final += h; pending = t
                        }
                        let want = final + (pending.isEmpty ? "" : render(pending))
                        if ed.display != want || s.pending != pending {
                            expect(false, "fuzz \(out) \(mode) run \(run) keys \(typed.debugDescription): shows \(ed.display.debugDescription), want \(want.debugDescription)")
                            break
                        }
                    }
                    checks += 1
                }
            }
        }

        // cases
        for mode in modes {
            let lenient: (String) -> String = { Engine.lenient($0) }
            do {   // take: a picked spelling replaces the tail and is final
                let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: lenient)
                for c in "ok nj" { s.type(c) }
                s.take("ny")
                expect(ed.display == "ok ny" && ed.marked.isEmpty && s.pending.isEmpty, "take \(mode): \(ed.display.debugDescription)")
                s.type("a")
                expect(ed.display == "ok nya", "take \(mode) then a: \(ed.display.debugDescription)")
            }
            do {   // insertFinal settles the tail first
                let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: lenient)
                for c in "sj" { s.type(c) }
                s.insertFinal("\n")
                expect(ed.display == "ș\n" && ed.marked.isEmpty, "insertFinal \(mode): \(ed.display.debugDescription)")
            }
            do {   // backspace through the tail and on into final text, a whole grapheme at a time
                let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: lenient)
                for c in "njanj" { s.type(c) }
                expect(ed.display == "n̦an̦", "backspace \(mode) setup: \(ed.display.debugDescription)")
                s.backspace(); s.backspace()
                expect(ed.display == "n̦a" && s.pending.isEmpty, "backspace \(mode) tail: \(ed.display.debugDescription)")
                s.backspace(); s.backspace()
                expect(ed.display == "", "backspace \(mode) final: \(ed.display.debugDescription)")
            }
        }
        for mode in modes {
            do {   // a tail still before the cursor stays the session's
                let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: { Engine.lenient($0) })
                for c in "nj" { s.type(c) }
                s.editorChanged()
                s.type("a")
                expect(ed.display == "n̦a", "kept tail \(mode): \(ed.display.debugDescription)")
            }
            do {   // the cursor moved away: the tail is orphaned and stays final, unmarked
                let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: { Engine.lenient($0) })
                for c in "nj" { s.type(c) }
                ed.unmarkText(); ed.text += " x"    // the person tapped elsewhere and typed
                s.editorChanged()
                s.type("a"); s.type("w")
                expect(ed.display == "n̦ x" + Engine.lenient("aw") && s.pending == "aw",
                       "orphaned tail \(mode): \(ed.display.debugDescription)")
            }
        }
        for mode in modes {   // emoji: the word typed is tracked, and a picked emoji takes its place
            let ed = StringEditor(), s = Session(sink: ed, mode: mode, render: { Engine.lenient($0) })
            for c in "ok hawrt" { s.type(c) }
            expect(s.word == "hawrt", "word \(mode): \(s.word.debugDescription)")
            s.backspace()
            expect(s.word == "hawr", "word after backspace \(mode): \(s.word.debugDescription)")
            s.type("t")
            s.pick("❤️")
            expect(ed.display == "ok ❤️" && ed.marked.isEmpty && s.pending.isEmpty && s.word.isEmpty,
                   "pick \(mode): \(ed.display.debugDescription)")
            s.type(" "); for c in "sjok" { s.type(c) }
            expect(s.word == "sjok", "word after space \(mode): \(s.word.debugDescription)")
            ed.unmarkText(); ed.text += " x"                // the person moved and typed: the word is not ours
            s.editorChanged()
            expect(s.word.isEmpty, "word dropped on an outside edit \(mode): \(s.word.debugDescription)")
            s.pick("🔥")                                       // no word: the emoji goes in, nothing is deleted
            expect(ed.display.hasSuffix(" x🔥"), "pick with no word \(mode): \(ed.display.debugDescription)")
        }
        do {   // the emoji table: a word in either language, most used first
            expect(Emoji.choices("hawrt").first == "❤️", "emoji hawrt: \(Emoji.choices("hawrt"))")
            expect(Emoji.choices("Siwv").first == "❤️", "emoji Siwv (szív, any case): \(Emoji.choices("Siwv"))")
            expect(Emoji.choices("kutja") == ["🐶", "🐕"], "emoji kutja: \(Emoji.choices("kutja"))")
            expect(Emoji.choices("sjok").isEmpty, "emoji sjok: none")
        }
        do {   // unknown context leaves the tail alone
            final class Blind: TextSink {
                let ed = StringEditor()
                func insertText(_ t: String) { ed.insertText(t) }
                func deleteBackward() { ed.deleteBackward() }
                func setMarkedText(_ t: String) { ed.setMarkedText(t) }
                func unmarkText() { ed.unmarkText() }
                var contextBefore: String? { nil }
            }
            let b = Blind(), s = Session(sink: b, mode: .replace, render: { Engine.lenient($0) })
            for c in "nj" { s.type(c) }
            s.editorChanged()
            expect(s.pending == "nj", "blind context kept the tail")
        }

        if failures.isEmpty { print("session holds \(checks) checks"); exit(0) }
        for f in failures.prefix(30) { print(f) }
        print("\(failures.count) of \(checks) checks failed")
        exit(1)
    }
}
