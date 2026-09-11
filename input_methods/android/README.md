# Diafon for Android

An input method (IME) for Android 8.0 and later. It shows the 26 letters,
the digits for tones and a handful of functional keys, converts what you
type by the streaming rule, and commits the result into whatever field has
focus. It has no dictionary, no prediction and no network access, and needs
no permission.

## How an Android IME works

Android has no conversion layer between the keyboard and the app; the
keyboard is the conversion layer. An IME is a `Service` the system binds to
when the user enables it under Languages and input and picks it. It gets:

- an **input view**, the panel that slides up (our keys and the strip
  above them),
- an **`InputConnection`**, a handle into the focused editor with
  `commitText` (final text), `setComposingText` (provisional text, drawn
  underlined, replaced on the next call), `finishComposingText` (make the
  provisional text final as it stands), `deleteSurroundingText`, and
  `getTextBeforeCursor`,
- **hardware key events** (`onKeyDown`) when a physical keyboard is
  attached, in which case the panel collapses and the IME still converts,
- **`onUpdateSelection`** callbacks whenever the cursor moves, which is
  how it learns that the user tapped elsewhere and the composing region is
  gone.

That is all the machinery the conversion needs. Everything else in an
ordinary keyboard app (suggestion strips, dictionaries, gesture typing,
emoji, layouts per language) exists because the orthography it types is
ambiguous. Diafon's is not, so the app stays small.

## Layout of this project

```
app/src/main/java/io/diafon/ime/
  SpecData.kt          generated from docs/spec.json by scripts/gen_android.py: script rules, stages
  Engine.kt            the engine, rule for rule from scripts/engine.py: segments, glyph, render, stream
  Stages.kt            spelling stages, from scripts/stages.py
  Prefs.kt             the four settings (output, tones, strict, enabled) and the renderer they select
  DiafonIme.kt         the InputMethodService: keys in, streaming rule, InputConnection out
  KeyboardView.kt      the keys, drawn on a canvas; operators tinted; shift, backspace, toggle, settings
  SettingsActivity.kt  setup (enable, switch) and settings; the launcher entry
app/src/main/res/xml/method.xml   declares the IME to the system (settings activity, one subtype)
app/src/main/AndroidManifest.xml  the service with BIND_INPUT_METHOD and the activity
check/Check.kt                    stdin/stdout driver used by tests/test_kotlin.py
```

The first three files are pure Kotlin with no Android dependency. That is
deliberate: they compile on a plain JVM, so the engine is verified against
the spec vectors without an emulator (below).

## The conversion, keystroke by keystroke

State: `pending`, the typed tail whose reading can still change. Nothing
else.

1. A key arrives (`onKey` from the panel, or `onKeyDown` from hardware).
   Shift, if armed, capitalizes a letter and disarms.
2. `Engine.stream(pending + key, renderer)` segments the buffer. All
   segments but the last are rendered and returned as `committed`; the
   last, if it is a form, is returned as the new `pending` (typed
   characters, not rendered).
3. In one batch edit: `commitText(committed)` replaces the old composing
   text with the final text; then `setComposingText(render(pending))`
   shows the new tail underlined, or `finishComposingText()` if there is
   none. The editor's text is therefore always the render of everything
   typed, with the last segment provisional.
4. The strip above the keys shows `pending · render(pending)`, or the
   output mode when idle, or `abc` when conversion is off.

Example, output = script, typing `sjok `:

| key | buffer | committed | pending | editor shows |
|---|---|---|---|---|
| s | s | | s | s̲ |
| j | sj | | sj | ș̲ |
| o | sjo | ș | o | șo̲ |
| k | ok | o | k | șok̲ |
| space | k␠ | k␠ | | șok␠ |

Backspace edits the tail first (`pending` loses its last character and the
composing text is re-rendered). With no tail it deletes one whole grapheme
before the cursor, so a letter and its combining mark go together. The
hardware backspace takes the same path. Enter, tab, cursor keys and
modifier shortcuts flush the tail (make it final as it stands) and are
then handled by the editor. Losing focus flushes too.

**Cursor tracking.** `onUpdateSelection` arrives asynchronously and can
describe a state between our commit and our compose, or a state from one
key earlier during fast typing. So the service keeps `expectedSel`, where
its own edits put the cursor, and a short history of the positions those
edits passed through. A callback whose cursor matches any of them is ours
and is ignored; anything else means the person moved the cursor, and the
orphaned tail is made final where it stands. Without this, a burst of keys
lost a letter once in the device pass.

Output modes are one function each (`Prefs.renderer`): the script glyphs,
the transport form unchanged, or a stage's spelling with the script glyph
as fallback for forms the stage does not spell.

## Build

Requirements: Android Studio Ladybug or later (bundles JDK 17 and the SDK),
or the command-line SDK with `sdkmanager "platforms;android-35"
"build-tools;35.0.0"` and Gradle 8.9 or later.

```
python3 scripts/gen_spec.py && python3 scripts/gen_android.py   # refresh SpecData.kt from the spec
cd input_methods/android
gradle wrapper --gradle-version 8.10                              # once, if you have no wrapper yet
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Or open `input_methods/android` in Android Studio and run the `app`
configuration on a device or emulator.

## Verify the engine without a device

```
brew install kotlin            # kotlinc plus a JDK
python3 tests/test_kotlin.py   # compiles SpecData, Engine, Stages and the check; replays every spec vector
```

It must print `kotlin port holds N vectors`. Run it after any change to
Engine.kt, Stages.kt, or the spec. The Android-dependent files (the
service, the views, the settings) are checked by the Gradle build.

## Device pass

`tools/demo.sh <apk>` boots a headless Pixel 7 emulator (API 35), installs
and selects Diafon, opens a contact form and types `sjok sewp njawr`
through the IME. Screenshots from that pass are in `screenshots/`:

- `script.png`: the panel and `șok sép n̦ár` in the field
- `composing.png`: Shift, t, q, y tapped on the soft keys; the strip
  shows `Tqy · C̖` and the editor the composing capital
- `hungarian.png`: the Hungarian stage, `Sok szép nyár, hosszú Öröm`
- `settings.png`: the setup and settings screen

Checked on the emulator: soft keys, hardware key path (`adb shell input
text`), a long burst with tones and specials (`șok sép n̦ár, C̖i3 șï3 c̦ï1
k̤alíl ḍis`), streaming commit word by word, the stage output,
backspace over the tail and over a committed marked glyph, the toggle and
the settings screen.

One thing outside the IME's control: the system font (Roboto) draws the
combining comma below on `n` so small that `n̦` can look like `ṇ`; the
underlying text is correct (`uiautomator dump` confirms it). That is the
case for the transport font and for a Diafon font in apps that allow one.

## Enable and use

1. Install; open the Diafon app (it is the settings screen).
2. Tap "Enable Diafon in system settings" and switch it on in the list.
   Android warns that an input method may collect what you type; this one
   has no network permission and stores nothing but its four settings.
3. Tap "Switch to Diafon", or use the keyboard icon in the navigation bar
   from any text field.
4. Type. `Dia` in the bottom left toggles conversion off (`abc`) and back;
   the gear opens the settings. Pick the output there: script form,
   transport form, or a spelling stage.

## Design choices, briefly

- **Emit on key down**, with haptic tap: the layout has no slide
  corrections to wait for.
- **No suggestions, no autocorrect**: the spelling is phonemic and
  determined; correcting it would be wrong by construction.
- **One layout**: the system's premise is the 26 letters; tones are digits
  on the top row; punctuation beyond comma and full stop comes from the
  system's symbol keyboard or a hardware keyboard.
- **The tail is transport, the editor shows the render**: `pending` holds
  typed characters so backspace edits what was typed, while the editor
  always shows what the reader will see.
- **Lenient always**: unknown or ill-formed input passes through; `strict`
  only colours the strip. A keyboard that refuses keys is unusable for
  names, URLs and other languages.
- **Bottom padding of one navigation-bar height**, read from the system
  resources: Android 15 draws its hide-keyboard and switch-keyboard buttons
  over the bottom of the panel otherwise, and a tap on the gear hit them.

## Not yet

- Long-press alternatives (punctuation, digits on letters).
- A dark theme for the panel; the colours are the site's light palette.
- Per-app memory of the enabled state.
- An app icon; the system default is used.
- Release signing and a Play listing.
