// Setup and settings: enable the input method, switch to it, choose the
// output. Also the app's launcher entry, so a fresh install has a door.
package io.diafon.ime

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.util.TypedValue
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView

class SettingsActivity : Activity() {
    override fun onCreate(saved: Bundle?) {
        super.onCreate(saved)
        val prefs = Prefs(this)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(20), dp(20), dp(20))
        }
        setContentView(ScrollView(this).apply { addView(root) })

        root.addView(title("Diafon"))
        root.addView(text("Type the transport form on the Diafon keys or any hardware keyboard; " +
                "the conversion happens above the keys and commits as soon as a segment is final."))

        root.addView(title("Setup"))
        root.addView(button("1. Enable Diafon in system settings") {
            startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
        })
        root.addView(button("2. Switch to Diafon") {
            (getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager).showInputMethodPicker()
        })

        root.addView(title("Output"))
        val options = listOf("script" to "Script form: ș c̖ á", "transport" to "Transport form: as typed") +
                SpecData.STAGES.values.map { "stage:${it.code}" to it.name }
        val group = RadioGroup(this)
        options.forEachIndexed { i, (value, label) ->
            group.addView(RadioButton(this).apply {
                text = label
                id = i + 1
                isChecked = prefs.output == value
                setOnClickListener { prefs.output = value }
            })
        }
        root.addView(group)

        root.addView(toggle("Conversion on", prefs.enabled) { prefs.enabled = it })
        root.addView(toggle("Tone digits", prefs.tones) { prefs.tones = it })
        root.addView(toggle("Strict: flag ill-formed segments", prefs.strict) { prefs.strict = it })

        root.addView(text("Spec ${SpecData.GENERATED} · ${SpecData.SOURCE}").apply { alpha = 0.6f })
    }

    private fun title(s: String) = TextView(this).apply {
        text = s
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 20f)
        setPadding(0, dp(18), 0, dp(6))
    }

    private fun text(s: String) = TextView(this).apply {
        text = s
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
        setPadding(0, dp(4), 0, dp(4))
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
