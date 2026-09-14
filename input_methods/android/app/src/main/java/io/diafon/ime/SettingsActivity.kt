// Setup and settings: enable the input method and switch to it; the base
// layout; what is written out; a live pane that
// shows a typed line in every spelling. Also the app's launcher entry.
package io.diafon.ime

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.os.Bundle
import android.provider.Settings
import android.text.Editable
import android.text.TextWatcher
import android.util.TypedValue
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView

class SettingsActivity : Activity() {
    private val ink = 0xFF1A1D24.toInt()
    private val muted = 0xFF5B6472.toInt()
    private val accent = 0xFF0E7C86.toInt()
    private val sample = "sjan txy tqok dqum acw"   // a neutral line showing the marks; each language shows its own sentence

    override fun onCreate(saved: Bundle?) {
        super.onCreate(saved)
        val prefs = Prefs(this)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(16), dp(20), dp(28))
        }
        setContentView(ScrollView(this).apply { addView(root) })

        root.addView(title("Diafon"))
        root.addView(text("One keyboard, one script, every language. Type the input form; the " +
                "conversion happens above the keys and commits as soon as a segment is final."))

        root.addView(heading("Setup"))
        root.addView(button("1. Enable Diafon in system settings") {
            startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
        })
        root.addView(button("2. Switch to Diafon") {
            (getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager).showInputMethodPicker()
        })

        root.addView(heading("Base layout"))
        root.addView(text("Only the placement of the 26 letters changes; the typing is the same on every layout."))
        root.addView(radios(Layouts.ALL.map { it.first to it.second }, prefs.layout) { prefs.layout = it })

        root.addView(heading("What is written out"))
        root.addView(text("Universal writes one letter per sound, the same in every language; a language's spelling writes today's orthography."))
        val previews = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(radios(Prefs.OUTPUTS, prefs.output, describe = true) { prefs.output = it })

        root.addView(heading("Try it"))
        val input = EditText(this).apply {
            setText(sample)
            typeface = Typeface.MONOSPACE
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setTextColor(accent)
        }
        root.addView(input)
        root.addView(previews)
        val refresh = {
            previews.removeAllViews()
            val typed = input.text.toString()
            for ((value, label) in Prefs.OUTPUTS) {
                val out = prefs.renderer(value)(typed)
                previews.addView(LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    setPadding(0, dp(6), 0, dp(6))
                    addView(TextView(context).apply {
                        text = label.lowercase()
                        setTextColor(muted)
                        setTextSize(TypedValue.COMPLEX_UNIT_SP, 11f)
                        minWidth = dp(110)
                        setPadding(0, dp(6), dp(8), 0)
                    })
                    addView(TextView(context).apply {
                        text = out
                        setTextColor(ink)
                        setTextSize(TypedValue.COMPLEX_UNIT_SP, 20f)
                        typeface = Typeface.SERIF
                    })
                })
            }
        }
        input.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) = refresh()
            override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
            override fun onTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
        })
        refresh()

        root.addView(heading("Also"))
        root.addView(toggle("Conversion on", prefs.enabled) { prefs.enabled = it })
        root.addView(toggle("Tone digits", prefs.tones) { prefs.tones = it })
        root.addView(toggle("Strict: flag ill-formed segments", prefs.strict) { prefs.strict = it })
        root.addView(text("Select text typed with any keyboard, in any app, and choose Diafon in the " +
                "text menu to convert it in place."))

        root.addView(text("Spec ${SpecData.GENERATED} · ${SpecData.SOURCE}").apply { alpha = 0.6f })
    }

    /** A radio group; with describe, each option shows the sample in that spelling. */
    private fun radios(options: List<Pair<String, String>>, current: String, describe: Boolean = false,
                       onPick: (String) -> Unit): RadioGroup {
        val prefs = Prefs(this)
        val group = RadioGroup(this)
        options.forEachIndexed { i, (value, label) ->
            val st = if (value.startsWith("stage:")) SpecData.STAGES[value.substring(6)] else null
            val src = if (st != null && st.sample.isNotEmpty()) st.sample else sample
            val sampleText = if (describe) "   ${prefs.renderer(value)(src.substringBefore(','))}" else ""
            group.addView(RadioButton(this).apply {
                text = label + sampleText
                id = i + 1
                isChecked = current == value
                setPadding(dp(6), dp(8), 0, dp(8))
                setOnClickListener { onPick(value) }
            })
        }
        return group
    }

    private fun title(s: String) = TextView(this).apply {
        text = s
        setTextColor(ink)
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 24f)
        typeface = Typeface.SERIF
        setPadding(0, dp(10), 0, dp(6))
    }

    private fun heading(s: String) = TextView(this).apply {
        text = s.uppercase()
        setTextColor(muted)
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 11f)
        letterSpacing = 0.08f
        setPadding(0, dp(22), 0, dp(6))
    }

    private fun text(s: String) = TextView(this).apply {
        text = s
        setTextColor(muted)
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
        setPadding(0, dp(2), 0, dp(6))
    }

    private fun button(s: String, onClick: () -> Unit) = Button(this).apply {
        text = s
        setOnClickListener { onClick() }
    }

    private fun toggle(s: String, on: Boolean, onChange: (Boolean) -> Unit) = Switch(this).apply {
        text = s
        isChecked = on
        setPadding(0, dp(10), 0, dp(10))
        setOnCheckedChangeListener { _, v -> onChange(v) }
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
