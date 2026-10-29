// The streaming rule against an editor, with no UIKit: keys in, edits out.
// The keyboard extension wires a UITextDocumentProxy to TextSink; the check
// (SessionCheck.swift, tests/test_ios_session.py) wires a string, so the
// whole keystroke logic is proven on a Mac without Xcode or a simulator.
//
// The editor always shows the render of everything typed: the committed head
// as final text, the pending tail (at most one segment) rendered and still
// provisional. Two ways to keep the tail provisional, since iOS apps honour
// marked text unevenly (input_methods/ios/README.md, the text path):
//   .marked   the tail is marked text; insertText replaces it with the
//             settled head, then the new tail is marked again. Text is made
//             final by insertText, never by unmarkText: in the simulator a
//             setMarkedText, unmarkText, setMarkedText run garbled the field
//             (`sjok sewp njawr` came out `okk epp ar`)
//   .replace  the tail is plain text the session remembers (`shown`); the
//             next key deletes back only the characters that differ and
//             types the rest
import Foundation

/// The editor, as the session needs it.
protocol TextSink: AnyObject {
    func insertText(_ text: String)
    /// One character back: the host deletes a whole grapheme (a letter with its marks).
    func deleteBackward()
    func setMarkedText(_ text: String)
    func unmarkText()
    /// The text before the cursor as far as the host tells (nil: it does not say).
    var contextBefore: String? { get }
}

enum TailMode: String { case marked, replace }

final class Session {
    let sink: TextSink
    var mode: TailMode
    /// The renderer of the output in use (KeyboardPrefs.renderer).
    var render: (String) -> String
    /// The typed tail whose reading can still change, as typed.
    private(set) var pending = ""
    /// What the editor shows for the tail: its render, or "" with no tail.
    private(set) var shown = ""
    /// The word being typed, as typed (letters and tone digits since the last
    /// space or punctuation): its emoji are offered, and one picked takes its place.
    private(set) var word = ""

    init(sink: TextSink, mode: TailMode, render: @escaping (String) -> String) {
        self.sink = sink; self.mode = mode; self.render = render
    }

    /// One character in: the streaming rule decides what is final.
    func type(_ ch: Character) {
        if (ch.isLetter && ch.isASCII) || ch.isNumber { word.append(ch) } else { word = "" }
        let (committed, tail) = Engine.stream(pending + String(ch), renderer: render)
        show(head: committed, tail: tail)
    }

    /// Text that is final at once (a space key, a chosen spelling's neighbour,
    /// a symbol): the tail is settled first, then the text goes in as it is.
    func insertFinal(_ text: String) {
        flush()
        sink.insertText(text)
        word = ""
    }

    /// Backspace edits the tail first; with no tail, one grapheme of the editor's text.
    func backspace() {
        if pending.isEmpty { sink.deleteBackward(); word = ""; return }
        pending.removeLast()
        if !word.isEmpty { word.removeLast() }
        show(head: "", tail: pending)
    }

    /// Make the tail final as it stands (return, focus loss, the globe, a cursor move).
    func flush() {
        guard !pending.isEmpty else { return }
        if mode == .marked { sink.insertText(shown) }     // the marked tail, final as it stands
        pending = ""; shown = ""
    }

    /// A spelling picked from the strip takes the tail's place and is final.
    func take(_ text: String) {
        guard !pending.isEmpty else { return }
        if mode == .marked { sink.insertText(text) } else { replaceTail(with: text) }
        pending = ""; shown = ""; word = ""
    }

    /// An emoji picked for the word just typed takes the word's place, as a chosen
    /// character takes its syllable's. The word goes only if the editor still ends
    /// with it; otherwise (or with unknown context) the emoji goes in after it.
    func pick(_ emoji: String) {
        let typed = word
        flush()
        let written = render(typed)
        if !typed.isEmpty, let before = sink.contextBefore, before.hasSuffix(written) {
            for _ in 0..<written.count { sink.deleteBackward() }
        }
        sink.insertText(emoji)
        word = ""
    }

    /// The editor changed under us (the person moved the cursor, or the app edited).
    /// The tail is still ours only if the text before the cursor still ends with it;
    /// otherwise it is orphaned and stays where it is, final (marked text is unmarked
    /// first, so the next key can never overwrite it). Unknown context (nil) leaves
    /// the tail alone. The host calls this for its own reasons as well as ours, so
    /// a tail that is still in place survives.
    func editorChanged() {
        if !word.isEmpty, let before = sink.contextBefore, !before.hasSuffix(render(word)) { word = "" }
        guard !pending.isEmpty, let before = sink.contextBefore, !before.hasSuffix(shown) else { return }
        if mode == .marked { sink.unmarkText() }
        pending = ""; shown = ""
    }

    /// Committed head, then the new tail; the editor ends up showing head + render(tail).
    private func show(head: String, tail: String) {
        let next = tail.isEmpty ? "" : render(tail)
        switch mode {
        case .marked:
            if !head.isEmpty { sink.insertText(head) }    // replaces the old marked tail, final
            if !next.isEmpty || head.isEmpty { sink.setMarkedText(next) }
        case .replace:
            replaceTail(with: head + next)
        }
        pending = tail; shown = next
    }

    /// Replace mode: change the shown tail into `text` with the fewest edits,
    /// counting graphemes, as the host's deleteBackward does.
    private func replaceTail(with text: String) {
        let old = Array(shown), new = Array(text)
        var same = 0
        while same < old.count, same < new.count, old[same] == new[same] { same += 1 }
        for _ in same..<old.count { sink.deleteBackward() }
        if same < new.count { sink.insertText(String(new[same...])) }
    }
}
