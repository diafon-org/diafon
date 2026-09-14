# Input methods

How the conversion reaches a text field on each platform. Every
implementation is the same small machine wearing a platform's clothes; the
machine is specified once, in docs/spec.json, and proven by its vectors.

## The machine

1. **Segmentation.** Typed text splits into segments, greedy, left to right:
   a base letter, up to two operators, w at most once and last, tone
   digits. Characters outside the 26 letters and the digits are raw and
   pass through. Ill-formed input (an operator or digit with no base, three
   operators) passes through as typed: a person may be typing a language
   the system does not describe, and an input method must never eat keys.
2. **Rendering.** Each form segment becomes its glyph (the script form), or
   stays as typed (the transport form), or becomes a language's spelling (a
   stage). Raw and ill-formed segments stay as they are.
3. **The streaming commit rule.** After every keystroke the buffer is
   segmented. Everything before the last segment is final and is committed
   into the editor. The last segment, if it is a form, may still grow (an
   operator, w or a digit could follow), so it stays pending and is shown
   as composing text. A last segment that is raw (space, punctuation) is
   final too, so the buffer empties on every word boundary. The pending
   tail is never longer than one segment, at most a base, two operators, w
   and the tone digits.
4. **Settings**, the same on every platform: `output` (script · transport ·
   stage:<code>), `tones` (keep the digits), `strict` (flag ill-formed
   segments), `enabled` (conversion on; off is a plain keyboard, flipped by
   a toggle key).

Reference: `engine.segments`, `engine.render`, `engine.stream` in
scripts/engine.py. Every port replays the vectors in docs/spec.json
(render, invalid, lenient, stream traces, stages) byte for byte before it
ships: tests/test_spec.py holds the Python and JS engines, tests/test_kotlin.py
the Kotlin one, tests/test_swift.py the Swift one.

## Where the machine sits, per platform

| Platform | Hook | Status |
|---|---|---|
| Android | `InputMethodService`: the IME owns the keys and an `InputConnection` into the editor; composing text is native (`setComposingText`, `commitText`); a `PROCESS_TEXT` activity converts selections typed with any keyboard | android/: base layouts, candidate strip, convert-selection; APK builds |
| macOS | Input Method Kit: `IMKInputController` receives keystrokes from any app, `setMarkedText` shows the tail, `insertText` commits; two text Services convert selections typed with any keyboard | mac/: rebuilt on spec.json (Swift engine holds the vectors, tests/test_swift.py), status menu, setup window, service |
| Linux | IBus, and fcitx5: an m17n `.mim` table (declarative transducer) generated from spec.json; no native code | planned |
| Windows | Text Services Framework text service, Rust, the one native build | planned |
| Web | browser extension: content script on editable fields and contenteditable, the playground's JS engine | planned |
| iOS | no input-method layer exists apart from keyboard extensions; not pursued. Text reaches iOS as transport form, or through the web extension in Safari, Shortcuts, and messenger bots | not pursued |

## Porting checklist

1. Generate the data file from docs/spec.json (never hand-copy a table).
2. Port `segments`, `glyph`, `render`, `stream` and the stage renderer.
3. Replay the vectors; fail the build on any difference.
4. Wire the platform: key in, `stream` out; commit the head, compose the
   tail; flush the tail on focus loss, cursor movement, enter and
   modifier shortcuts; backspace edits the tail first.
5. Expose the four settings under the same names and defaults.
