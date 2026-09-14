// Convert a selection: text typed with any keyboard, selected in any app,
// converted in place from the text selection menu (Android's process-text
// action). A small sheet shows the selection in every spelling; tapping one
// replaces the selection with it. Read-only text gets a copy instead.
package io.diafon.ime

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.os.Bundle
import android.util.TypedValue
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast

class ConvertActivity : Activity() {
    override fun onCreate(saved: Bundle?) {
        super.onCreate(saved)
        val text = intent.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)?.toString() ?: ""
        val readonly = intent.getBooleanExtra(Intent.EXTRA_PROCESS_TEXT_READONLY, false)
        if (text.isBlank()) { finish(); return }
        val prefs = Prefs(this)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(8), dp(8), dp(8), dp(8))
        }
        root.addView(TextView(this).apply {
            setText(if (readonly) "Diafon: copy as" else "Diafon: replace with")
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
            setPadding(dp(12), dp(8), dp(12), dp(4))
            alpha = 0.7f
        })
        for ((value, label) in Prefs.OUTPUTS) {
            val out = prefs.renderer(value)(text)
            if (out == text) continue                                   // nothing to convert to
            root.addView(row(label, out) {
                if (readonly) {
                    (getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager)
                        .setPrimaryClip(ClipData.newPlainText("Diafon", out))
                    Toast.makeText(this, "Copied", Toast.LENGTH_SHORT).show()
                } else {
                    setResult(RESULT_OK, Intent().putExtra(Intent.EXTRA_PROCESS_TEXT, out))
                }
                finish()
            })
        }
        setContentView(root)
    }

    private fun row(label: String, sample: String, onClick: () -> Unit) = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(12), dp(10), dp(12), dp(10))
        isClickable = true
        setBackgroundResource(android.R.drawable.list_selector_background)
        addView(TextView(context).apply {
            text = sample.take(120) + if (sample.length > 120) "…" else ""
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
            typeface = Typeface.SERIF
        })
        addView(TextView(context).apply {
            text = label
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 11f)
            alpha = 0.6f
            gravity = Gravity.START
        })
        setOnClickListener { onClick() }
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
