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
4. **Settings**, the same on every platform: `output` (script, the default
   Universal · stage:<code>, one language's spelling · transport, the escape
   path only), `language` (the spelling's code, kept when the output goes
   back to Universal, defaulting to the first system language that has a
   spelling), `tones` (keep the digits), `strict` (flag ill-formed segments),
   `enabled` (conversion on; off is a plain keyboard, flipped by a toggle
   key). A screen offers two choices, Universal or a language's spelling,
   the language from one list; never every spelling as a flat row.

Reference: `engine.segments`, `engine.render`, `engine.stream` in
scripts/engine.py. Every port replays the vectors in docs/spec.json
(render, invalid, lenient, stream traces, stages) byte for byte before it
ships: tests/test_spec.py holds the Python and JS engines, tests/test_kotlin.py
the Kotlin one, tests/test_swift.py the Swift one (input_methods/apple/Core,
shared by the macOS and iOS input methods).

## Reading back

The machine runs the other way too (scripts/stages.py `parse`, `convert`,
`detect`; docs/engine.js; input_methods/apple/Core/Reading.swift): a text
in any source, the input form, the script, or a language's spelling, is
read back into transport form and re-rendered in any target. Reading is
longest match over a table of spellings: the script's table is the grammar's
whole inventory (a glyph two forms share, kx and kc, reads as the form the
languages use); a stage's table is its spellings, long forms, capitals, and
its `read` aliases, the spellings a language keeps for etymology and never
writes (Hungarian ly → ix, Czech y ý ů ě…), over the script's table as
fallback. `detect` ranks the sources by the share of letters each reads with
its own spellings; the mode in use breaks ties. Stated limits: all-caps
reads as capitalized (SZÉP → SzÉP), and digraphs across a compound boundary
(házszám) read by longest match, no dictionary being consulted. The spec's
parse, convert and detect vectors hold every port to the same readings.

## The lexicon layer

Above the letters, word by word (data/lexicon, scripts/lexicon.py;
docs/engine.js; Lexicon.swift): English, whose spelling carries no reading
of its own, reads and writes through the pronunciation dictionary
(CMUdict); Hungarian writes ly on the stems that take it (folyók) and
reads English and Latin loans by their own dictionaries, folded into
Hungarian sounds (meeting → mítiŋg, like → lájk); Mandarin reads and
writes pinyin by the syllable, and its `choices` table gives the input
method the characters of a toned syllable, most frequent first. A word is
read by the stage's own letters when they read it in full (a host with a
dictionary checks for a loan first: the longest matching stem wins, native
on ties unless the word has a foreign letter shape), else by its lexicon,
else by a loan lexicon, else by the letters and the script. Kotlin has
none of it yet: Android renders English and Mandarin in the script.

## Where the machine sits, per platform

| Platform | Hook | Status |
|---|---|---|
| Android | `InputMethodService`: the IME owns the keys and an `InputConnection` into the editor; composing text is native (`setComposingText`, `commitText`); a `PROCESS_TEXT` activity converts selections typed with any keyboard | android/: base layouts, candidate strip, convert-selection; APK builds |
| macOS | Input Method Kit: `IMKInputController` receives keystrokes from any app, `setMarkedText` shows the tail, `insertText` commits; two text Services convert a selection in any spelling, from the source detected or chosen in a window, to the mode in use or any other | mac/: on spec.json (Swift engine holds every vector, reading back included, tests/test_swift.py), status menu, quick list and chooser, candidate window, setup window, services |
| Linux | IBus, and fcitx5: an m17n `.mim` table (declarative transducer) generated from spec.json; no native code | planned |
| Windows | Text Services Framework text service, Rust, the one native build | planned |
| Web | browser extension on docs/engine.js: a content script reads a page in Universal, toggled from the icon, the language from the page itself (extensions/browser, tests/test_extension.py); input into editable fields and contenteditable | pages done; editable fields planned |
| iOS | a keyboard extension (`UIInputViewController`): the keyboard owns the keys and a `textDocumentProxy` into the field, the tail kept as marked text or as plain text it rewrites; the selection converted from the strip; no full access, so the settings live in the keyboard | ios/: on the shared Swift core (apple/Core); the keystroke logic checked on a Mac (tests/test_ios_session.py), UIKit typechecked; device pass open |

## Porting checklist

1. Generate the data file from docs/spec.json (never hand-copy a table).
2. Port `segments`, `glyph`, `render`, `stream` and the stage renderer;
   then reading back: `inventory`, the script and stage tables, `read`,
   `parse`, `convert`, `detect` (the Kotlin port has the first half only).
3. Replay the vectors; fail the build on any difference.
4. Wire the platform: key in, `stream` out; commit the head, compose the
   tail; flush the tail on focus loss, cursor movement, enter and
   modifier shortcuts; backspace edits the tail first.
5. Expose the four settings under the same names and defaults.
