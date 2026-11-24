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
//             (letters came out dropped and doubled)
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
    /// The streaming rule of the output in use: the keys so far -> (what is final,
    /// written out; the keys still open). Prefs.stream; a language's spelling keeps
    /// the whole word open.
    var stream: (String) -> (String, String)
    /// What the tail shows while typed (its letters); nil shows render.
    var preview: ((String) -> String)? = nil
    /// The typed tail whose reading can still change, as typed.
    private(set) var pending = ""
    /// What the editor shows for the tail: its render, or "" with no tail.
    private(set) var shown = ""
    /// After its own edit the session trusts its tail for this long: a host's context
    /// lags behind fast typing, and a lagging context must not orphan the tail.
    static var settle: TimeInterval = 0.4
    private var lastEdit = Date.distantPast
    private var settling: Bool { Date().timeIntervalSince(lastEdit) < Session.settle }

    /// The word being typed, as typed (letters, and the tone digits after them, since
    /// the last space or punctuation): its emoji are offered, and one picked takes its
    /// place. A digit before the word's first letter is a number, not the word's.
    private(set) var word = ""
    /// Everything typed since the last space, as typed (`run`) and as it stands in
    /// the editor once the tail is final (`runText`): an emoticon (:D, <3) is read
    /// from the keys, not from the host's context, which lags and may leave out
    /// the marked tail.
    private(set) var run = ""
    private var runText = ""

    init(sink: TextSink, mode: TailMode, render: @escaping (String) -> String, stream: @escaping (String) -> (String, String)) {
        self.sink = sink; self.mode = mode; self.render = render; self.stream = stream
    }

    /// One character in: the streaming rule decides what is final.
    func type(_ ch: Character) {
        track(ch, plain: false)
        if ch.isWhitespace { run = "" } else { run.append(ch) }
        let (committed, tail) = stream(pending + String(ch))
        show(head: committed, tail: tail)
    }

    /// One character in as it is, conversion off; the word is still tracked, so its
    /// emoji are offered (typed in a language's usual letters).
    func typePlain(_ ch: Character) {
        lastEdit = Date()
        flush()
        sink.insertText(String(ch))
        noteFinal(String(ch))
        if ch.isWhitespace { run = "" } else { run.append(ch) }
        track(ch, plain: true)
    }

    /// The word grows by a letter, or by a digit after one (its tone, with conversion
    /// on); anything else ends it, and a digit never starts it.
    private func track(_ ch: Character, plain: Bool) {
        if wordPlain != plain { word = ""; wordPlain = plain }
        if ch.isLetter && (ch.isASCII || plain) { word.append(ch) }
        else if ch.isNumber, !plain, !word.isEmpty { word.append(ch) }
        else { word = "" }
    }
    /// The word was typed with conversion off: it stands in the text as typed.
    private var wordPlain = false
    private func written(_ w: String) -> String { wordPlain ? w : render(w) }

    /// Text that is final at once (a space key, a chosen spelling's neighbour,
    /// a symbol): the tail is settled first, then the text goes in as it is.
    func insertFinal(_ text: String) {
        lastEdit = Date()
        flush()
        sink.insertText(text)
        noteFinal(text)
        if let i = text.lastIndex(where: { $0.isWhitespace }) { run = String(text[text.index(after: i)...]) } else { run += text }
        word = ""
    }

    /// Text gone into the editor as final: the run's text grows, or starts after its last space.
    private func noteFinal(_ text: String) {
        if let i = text.lastIndex(where: { $0.isWhitespace }) { runText = String(text[text.index(after: i)...]) } else { runText += text }
    }

    /// Backspace edits the tail first; with no tail, one grapheme of the editor's text.
    func backspace() {
        lastEdit = Date()
        if pending.isEmpty {
            sink.deleteBackward()
            if wordPlain, !word.isEmpty { word.removeLast() } else { word = "" }
            if runText.isEmpty { run = "" } else { runText.removeLast(); if !run.isEmpty { run.removeLast() } }
            return
        }
        pending.removeLast()
        if !word.isEmpty { word.removeLast() }
        if !run.isEmpty { run.removeLast() }
        show(head: "", tail: pending)
    }

    /// Make the tail final as it stands (return, focus loss, the globe, a cursor move).
    /// A tail the field no longer shows (cleared by the app, a search field's ✕) is
    /// dropped, never written back; unknown context (nil) writes it as before.
    func flush() {
        guard !pending.isEmpty else { return }
        if mode == .marked {                              // the marked tail, final as it stands
            if !settling, let before = sink.contextBefore, !before.hasSuffix(shown) { sink.unmarkText(); run = ""; runText = "" }
            else { sink.insertText(shown); noteFinal(shown) }
        } else { noteFinal(shown) }
        pending = ""; shown = ""
    }

    /// A new field, or the keyboard back after a while: nothing typed before is ours.
    func forget() { pending = ""; shown = ""; word = ""; run = ""; runText = "" }

    /// A spelling picked from the strip takes the tail's place and is final.
    func take(_ text: String) {
        guard !pending.isEmpty else { return }
        if mode == .marked { sink.insertText(text) } else { replaceTail(with: text) }
        pending = ""; shown = ""; word = ""; run = ""; runText = ""
    }

    /// An emoticon picked from the strip takes the place of everything typed since
    /// the last space (the run: `:D`, `<3`). The session's own record decides what
    /// goes: the host's context only vetoes it when it is known, settled and no
    /// longer ends with the run (the person moved or the app edited).
    func replaceRun(with text: String) {
        let ours = settling || (sink.contextBefore.map { $0.hasSuffix(runText + shown) } ?? false)
        if ours {
            if !pending.isEmpty { if mode == .marked { sink.setMarkedText("") } else { replaceTail(with: "") } }
            for _ in 0..<runText.count { sink.deleteBackward() }
            pending = ""; shown = ""
        } else {
            flush()
        }
        lastEdit = Date()
        sink.insertText(text)
        word = ""; run = ""; runText = ""
    }

    /// An emoji picked for the word just typed takes the word's place, as a chosen
    /// character takes its syllable's. The word goes only if the editor still ends
    /// with it; otherwise (or with unknown context) the emoji goes in after it.
    func pick(_ emoji: String) {
        let typed = word
        flush()
        let shown = written(typed)
        if !typed.isEmpty, let before = sink.contextBefore, before.hasSuffix(shown) {
            for _ in 0..<shown.count { sink.deleteBackward() }
        }
        sink.insertText(emoji)
        word = ""; run = ""; runText = ""
    }

    /// The editor changed under us (the person moved the cursor, or the app edited).
    /// The tail is still ours only if the text before the cursor still ends with it;
    /// otherwise it is orphaned and stays where it is, final (marked text is unmarked
    /// first, so the next key can never overwrite it). Unknown context (nil) leaves
    /// the tail alone. The host calls this for its own reasons as well as ours, so
    /// a tail that is still in place survives.
    func editorChanged() {
        if settling { return }                            // our own edit, not yet in the context
        if !word.isEmpty, let before = sink.contextBefore, !before.hasSuffix(written(word)) { word = "" }
        if !run.isEmpty, let before = sink.contextBefore, !before.hasSuffix(runText + shown) { run = ""; runText = "" }
        guard !pending.isEmpty, let before = sink.contextBefore, !before.hasSuffix(shown) else { return }
        if mode == .marked { sink.unmarkText() }
        pending = ""; shown = ""
    }

    /// Committed head, then the new tail; the editor ends up showing head + render(tail).
    private func show(head: String, tail: String) {
        lastEdit = Date()
        let next = tail.isEmpty ? "" : (preview ?? render)(tail)
        switch mode {
        case .marked:
            if !head.isEmpty { sink.insertText(head) }    // replaces the old marked tail, final
            if !next.isEmpty || head.isEmpty { sink.setMarkedText(next) }
        case .replace:
            replaceTail(with: head + next)
        }
        noteFinal(head)
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
