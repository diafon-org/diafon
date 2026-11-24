# Input methods

How the typing reaches a text field on each platform.

- `apple/Core` is what the Mac and iOS share. `Diafon.swift` runs the site's
  JavaScript (the alphabet, `docs/assets/diafon-core.js`; the typing,
  `web/diafon-keys.js`) in JavaScriptCore, through `diafon-glue.js`.
  `Prefs.swift` holds the settings, `Emoji.swift` the word-to-emoji choices,
  `Layouts.swift` the base layouts. `scripts/gen_apple.py` puts the files
  the apps bundle in `apple/Resources` (made by the builds, not committed).
- `mac` is the macOS input method, `ios` the iOS keyboard and its app; each
  has its own README.
- `android` is asleep: it still types the old five-operator typing and
  carries an old alphabet.

## The machine

1. **The keys.** What was typed is cut by the profile's key table
   (`profiles/diafon-v1.yaml`): a letter, then y and q for its marks, a
   doubled consonant for the long one, a digit for a tone. Anything else
   passes through as typed.
2. **The streaming rule.** After every key the text is cut again.
   Everything before the last letter is final and goes into the editor. The
   last letter may still change (a mark, a doubling or a tone could follow),
   so it stays provisional, shown as composing text. A space or a
   punctuation mark is final at once.
3. **A language's spelling.** When the output is a language's spelling, the
   whole word being typed stays provisional: a spelling can depend on the
   letter that follows (Polish si, Hungarian ssz).
4. **Settings**, the same on both platforms: what is written (Diafon, or
   one language's spelling; on iOS the language comes from the quick list,
   on the Mac each language is a keyboard in the system's list), `tones` (a
   tone digit writes its tone sign; off leaves it out), `join` (a long
   consonant's two letters joined, which the Diafon fonts draw fused),
   `enabled` (off is a plain keyboard; iOS only, on the Mac the plain
   letters are another keyboard).

The input methods carry no dictionary. A language is offered when its
spelling is written by its letters alone; English is not. Mandarin's pinyin
is no dictionary but a table of some 400 syllables made by rule (12 KB,
lexicons.json), so it is offered too: `ni3 kqaw3` writes ni3 hao3, the tone
as its number. The characters are not carried.

## Checks

    python3 tests/test_apple.py          # the vectors through the Swift core
    python3 tests/test_ios_session.py    # the iOS keystroke logic; a UIKit typecheck
    make -C input_methods/ios uitest     # the keyboard typed on in a simulator
