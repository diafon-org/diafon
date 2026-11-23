// Setup and settings: enable the input method and switch to it; the base
// layout; what is written out, Universal or a language's spelling, the
// language from one list; a live pane that shows a typed line both ways.
// Also the app's launcher entry.
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
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.Switch
import android.widget.TextView

class SettingsActivity : Activity() {
    private val ink = 0xFF1A1D24.toInt()
    private val muted = 0xFF5B6472.toInt()
    private val accent = 0xFF0E7C86.toInt()
    private val sample = "sj tq aw"   // sounds, not a word; each language shows its own sample

    override fun onCreate(saved: Bundle?) {
        super.onCreate(saved)
        val prefs = Prefs(this)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(16), dp(20), dp(28))
        }
        setContentView(ScrollView(this).apply { addView(root) })

        root.addView(title("Diafon"))
        root.addView(text("One keyboard, one script, every language. Type the Diafon input; the field shows " +
                "the result, and the strip above the keys shows the sound being typed in each spelling."))

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
        root.addView(text("Universal writes one letter per sound, the same in every language; a language's spelling writes the language's own spelling."))
        val previews = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        val universal = RadioButton(this).apply { setPadding(dp(6), dp(8), 0, dp(8)) }
        val spelling = RadioButton(this).apply { setPadding(dp(6), dp(8), 0, dp(8)) }
        val picker = Spinner(this).apply {
            adapter = ArrayAdapter(context, android.R.layout.simple_spinner_dropdown_item, Prefs.LANGUAGES.map { it.second })
            setSelection(Prefs.LANGUAGES.indexOfFirst { it.first == prefs.language }.coerceAtLeast(0))
        }
        root.addView(RadioGroup(this).apply { addView(universal); addView(spelling) })
        root.addView(picker)

        root.addView(heading("Try it"))
        val input = EditText(this).apply {
            setText(clause(prefs))
            typeface = Typeface.MONOSPACE
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setTextColor(accent)
        }
        root.addView(input)
        root.addView(previews)
        var prefilled = input.text.toString()
        val refresh = {
            universal.isChecked = prefs.universal
            spelling.isChecked = !prefs.universal
            universal.text = "Universal   ${prefs.renderer("script")(clause(prefs))}"
            spelling.text = "A language's spelling   ${prefs.renderer("stage:${prefs.language}")(clause(prefs))}"
            if (input.text.toString() == prefilled) { prefilled = clause(prefs); input.setText(prefilled) }
            previews.removeAllViews()
            val typed = input.text.toString()
            for ((value, label) in prefs.choices()) {
                val out = prefs.renderer(value)(typed)
                previews.addView(LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    setPadding(0, dp(6), 0, dp(6))
                    addView(TextView(context).apply {
                        text = label
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
        universal.setOnClickListener { prefs.output = "script"; refresh() }
        spelling.setOnClickListener { prefs.output = "stage:${prefs.language}"; refresh() }
        picker.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, pos: Int, id: Long) {
                val code = Prefs.LANGUAGES[pos].first
                if (code == prefs.language) return
                prefs.language = code
                if (!prefs.universal) prefs.output = "stage:$code"
                refresh()
            }
            override fun onNothingSelected(parent: AdapterView<*>?) {}
        }
        refresh()

        root.addView(heading("Also"))
        root.addView(toggle("Conversion on", prefs.enabled) { prefs.enabled = it })
        root.addView(toggle("Tones", prefs.tones) { prefs.tones = it })
        root.addView(toggle("Joined long consonants (the Diafon fonts draw them fused)", prefs.join) { prefs.join = it })
        root.addView(toggle("Strict: flag ill-formed segments", prefs.strict) { prefs.strict = it })
        root.addView(text("Select text typed with any keyboard, in any app, and choose Diafon in the " +
                "text menu to convert it in place."))

        root.addView(text("Spec ${SpecData.GENERATED} · ${SpecData.SOURCE}").apply { alpha = 0.6f })
    }

    /** The language's own sample, its first clause; the sounds when it has none. */
    private fun clause(prefs: Prefs): String =
        SpecData.STAGES[prefs.language]?.sample?.takeIf { it.isNotEmpty() }?.substringBefore(',') ?: sample

    /** A radio group, one option per (value, label). */
    private fun radios(options: List<Pair<String, String>>, current: String, onPick: (String) -> Unit): RadioGroup {
        val group = RadioGroup(this)
        options.forEachIndexed { i, (value, label) ->
            group.addView(RadioButton(this).apply {
                text = label
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
