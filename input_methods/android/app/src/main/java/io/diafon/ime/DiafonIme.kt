// The input method service: keys in, converted text out, committed by the
// streaming rule. The only state is `pending`, the typed tail whose reading
// can still change; it is shown as composing text in the editor and, in every
// spelling, as candidates in the strip above the keys: tapping one commits
// it. See README.md.
package io.diafon.ime

import android.content.Intent
import android.inputmethodservice.InputMethodService
import android.util.TypedValue
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.graphics.Typeface
import android.view.Gravity
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView

class DiafonIme : InputMethodService() {
    private lateinit var prefs: Prefs
    private lateinit var strip: LinearLayout
    private lateinit var keyboard: KeyboardView
    private var pending = ""        // the transport tail still composing
    private var shifted = false
    private var expectedSel = -1    // where our edits put the cursor; -1 = unknown
    private val recentSel = ArrayDeque<Int>()   // cursor positions our recent edits produced, final and intermediate

    override fun onCreate() {
        super.onCreate()
        prefs = Prefs(this)
    }

    override fun onCreateInputView(): View {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(0xFFEEF0F4.toInt())
        }
        strip = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(6), dp(6), dp(6), dp(4))
            minimumHeight = dp(52)
        }
        keyboard = KeyboardView(this) { onKey(it) }
        keyboard.layout = prefs.layout
        root.addView(HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false; addView(strip) })
        root.addView(keyboard)
        // keep the bottom row clear of the system's gesture bar and its keyboard buttons
        val navId = resources.getIdentifier("navigation_bar_height", "dimen", "android")
        val nav = if (navId != 0) resources.getDimensionPixelSize(navId) else dp(24)
        root.setPadding(0, 0, 0, nav)
        refreshStrip()
        return root
    }

    override fun onStartInput(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInput(attribute, restarting)
        pending = ""
        expectedSel = attribute?.initialSelStart ?: -1
        recentSel.clear()
    }

    override fun onStartInputView(info: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        pending = ""
        shifted = false
        if (::keyboard.isInitialized) {
            keyboard.shifted = false
            keyboard.enabledMode = prefs.enabled
            keyboard.layout = prefs.layout
        }
        refreshStrip()
    }

    override fun onFinishInput() {
        flush()
        super.onFinishInput()
    }

    /** Selection callbacks arrive asynchronously and may describe a state
     *  between our commit and our compose, so they are not trusted on their
     *  own: a callback is ours when the cursor sits where our edits put it,
     *  or anywhere inside the composing text they were replacing. Anything
     *  else is the person moving the cursor, and the tail is orphaned. */
    override fun onUpdateSelection(oldSelStart: Int, oldSelEnd: Int, newSelStart: Int, newSelEnd: Int,
                                   candidatesStart: Int, candidatesEnd: Int) {
        super.onUpdateSelection(oldSelStart, oldSelEnd, newSelStart, newSelEnd, candidatesStart, candidatesEnd)
        if (pending.isEmpty() || expectedSel < 0) {
            expectedSel = newSelStart
            return
        }
        // the editor still holds our composing region: the tail is alive,
        // whatever the cursor numbers say (they lag under fast typing)
        if (candidatesStart >= 0 && candidatesEnd > candidatesStart) return
        val compLen = render()(pending).length
        val ours = newSelStart == newSelEnd &&
            ((newSelStart >= expectedSel - compLen && newSelStart <= expectedSel) || newSelStart in recentSel)
        if (ours) return
        pending = ""
        currentInputConnection?.finishComposingText()
        expectedSel = newSelStart
        refreshStrip()
    }

    // ---- soft keys ----

    private fun onKey(key: Key) {
        val ic = currentInputConnection ?: return
        when (key) {
            is Key.Char -> {
                val ch = if (shifted && key.ch.isLetter()) key.ch.uppercaseChar() else key.ch
                if (shifted) { shifted = false; keyboard.shifted = false }
                type(ic, ch)
            }
            Key.Space -> type(ic, ' ')
            Key.Backspace -> backspace(ic)
            Key.Shift -> { shifted = !shifted; keyboard.shifted = shifted }
            Key.Enter -> {
                flush()
                if (!sendDefaultEditorAction(true)) sendDownUpKeyEvents(KeyEvent.KEYCODE_ENTER)
            }
            Key.Toggle -> {
                flush()
                prefs.enabled = !prefs.enabled
                keyboard.enabledMode = prefs.enabled
                refreshStrip()
            }
            Key.Settings -> {
                flush()
                startActivity(Intent(this, SettingsActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }
        }
    }

    /** One character in: the streaming rule decides what is final. */
    private fun type(ic: InputConnection, ch: Char) {
        if (!prefs.enabled) {
            ic.commitText(ch.toString(), 1)
            moveExpected(1)
            return
        }
        val render = render()
        val oldComp = if (pending.isEmpty()) 0 else render(pending).length
        val (committed, tail) = Engine.stream(pending + ch, render)
        val shown = if (tail.isEmpty()) "" else render(tail)
        ic.beginBatchEdit()
        if (committed.isNotEmpty()) ic.commitText(committed, 1)   // replaces the old composing text
        pending = tail
        if (pending.isNotEmpty()) ic.setComposingText(shown, 1) else ic.finishComposingText()
        ic.endBatchEdit()
        moveExpected(committed.length - oldComp + shown.length)
        refreshStrip()
    }

    private fun backspace(ic: InputConnection) {
        if (pending.isNotEmpty()) {
            val render = render()
            val oldComp = render(pending).length
            pending = pending.dropLast(1)
            val shown = if (pending.isEmpty()) "" else render(pending)
            if (pending.isNotEmpty()) ic.setComposingText(shown, 1)
            else ic.commitText("", 1)                             // drops the composing region
            moveExpected(shown.length - oldComp)
        } else {
            // committed text: one whole grapheme (a letter with its marks)
            val before = ic.getTextBeforeCursor(16, 0)?.toString() ?: ""
            val n = if (before.isEmpty()) 1 else {
                val it = java.text.BreakIterator.getCharacterInstance()
                it.setText(before)
                before.length - it.preceding(before.length)
            }
            ic.deleteSurroundingText(n, 0)
            moveExpected(-n)
        }
        refreshStrip()
    }

    /** Our edit moved the cursor by delta; remember where it was and where
     *  it is, so late callbacks about either state are recognised as ours. */
    private fun moveExpected(delta: Int) {
        if (expectedSel < 0) return
        recentSel.addLast(expectedSel)
        expectedSel += delta
        recentSel.addLast(expectedSel)
        while (recentSel.size > 32) recentSel.removeFirst()
    }

    private val output: String get() = prefs.output

    private fun render(): (String) -> String = prefs.renderer(output)

    /** A candidate tapped: the pending segment goes in as that spelling. */
    private fun commitCandidate(text: String) {
        val ic = currentInputConnection ?: return
        if (pending.isEmpty()) return
        val oldComp = render()(pending).length
        ic.commitText(text, 1)                  // replaces the composing text
        pending = ""
        moveExpected(text.length - oldComp)
        refreshStrip()
    }

    /** Make the composing tail final as it stands. */
    private fun flush() {
        if (pending.isEmpty()) return
        currentInputConnection?.finishComposingText()
        pending = ""
        refreshStrip()
    }

    // ---- hardware keys (tablets, Chromebooks, Bluetooth keyboards) ----

    override fun onKeyDown(keyCode: Int, event: KeyEvent): Boolean {
        val ic = currentInputConnection ?: return super.onKeyDown(keyCode, event)
        if (!prefs.enabled) return super.onKeyDown(keyCode, event)
        if (keyCode == KeyEvent.KEYCODE_DEL && !event.isCtrlPressed && !event.isAltPressed) {
            backspace(ic)
            return true
        }
        if (event.isCtrlPressed || event.isAltPressed || event.isMetaPressed) {
            flush()
            return super.onKeyDown(keyCode, event)
        }
        val u = event.unicodeChar
        if (u == 0 || Character.isISOControl(u)) {          // navigation, enter, tab, escape
            flush()
            return super.onKeyDown(keyCode, event)
        }
        type(ic, u.toChar())
        return true
    }

    // ---- the strip: the pending segment in every spelling ----

    private fun refreshStrip() {
        if (!::strip.isInitialized) return
        strip.removeAllViews()
        val ink = 0xFF1A1D24.toInt()
        val accent = 0xFF0E7C86.toInt()
        val warn = 0xFFB03F3F.toInt()
        val muted = 0xFF5B6472.toInt()
        if (!prefs.enabled) {
            strip.addView(note("abc · conversion off", muted))
            return
        }
        if (pending.isEmpty()) {
            strip.addView(note("${prefs.outputLabel(output)} · ${Layouts.label(prefs.layout)}", muted))
            return
        }
        val ill = prefs.strict && Engine.segments(pending, false).any { it is Seg.Err }
        val seen = HashSet<String>()
        for ((value, label) in Prefs.OUTPUTS) {
            val text = prefs.renderer(value)(pending)
            if (!seen.add(text)) continue                     // one chip per distinct spelling
            val current = value == output
            strip.addView(chip(text, label, if (ill) warn else if (current) accent else ink, current) { commitCandidate(text) })
        }
    }

    private fun note(s: String, color: Int) = TextView(this).apply {
        text = s
        setTextColor(color)
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
        setPadding(dp(10), dp(8), dp(10), dp(8))
    }

    private fun chip(big: String, small: String, color: Int, current: Boolean, onTap: () -> Unit) = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        gravity = Gravity.CENTER
        setPadding(dp(12), dp(4), dp(12), dp(4))
        val bg = android.graphics.drawable.GradientDrawable().apply {
            cornerRadius = dp(8).toFloat()
            setColor(0xFFFFFFFF.toInt())
            if (current) setStroke(dp(2), 0xFF0E7C86.toInt())
        }
        background = bg
        val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        lp.setMargins(dp(3), 0, dp(3), 0)
        layoutParams = lp
        addView(TextView(context).apply {
            text = big
            setTextColor(color)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 20f)
            typeface = Typeface.SERIF
        })
        addView(TextView(context).apply {
            text = small.lowercase()
            setTextColor(0xFF5B6472.toInt())
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 9f)
        })
        setOnClickListener { onTap() }
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
