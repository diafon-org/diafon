// The settings above the keyboard, shared in name and default with every
// Diafon input method (plan.md, question 4): output, tones, strict, enabled.
package io.diafon.ime

import android.content.Context
import android.content.SharedPreferences

class Prefs(ctx: Context) {
    private val sp: SharedPreferences = ctx.getSharedPreferences("diafon", Context.MODE_PRIVATE)

    /** Conversion on; off is a plain keyboard (the toggle key flips it). */
    var enabled: Boolean
        get() = sp.getBoolean("enabled", true)
        set(v) = sp.edit().putBoolean("enabled", v).apply()

    /** "script" (the glyphs), "transport" (as typed) or "stage:<code>". */
    var output: String
        get() = sp.getString("output", "script")!!
        set(v) = sp.edit().putString("output", v).apply()

    /** Keep tone digits in the output. */
    var tones: Boolean
        get() = sp.getBoolean("tones", true)
        set(v) = sp.edit().putBoolean("tones", v).apply()

    /** Flag ill-formed segments in the strip (they still pass through). */
    var strict: Boolean
        get() = sp.getBoolean("strict", false)
        set(v) = sp.edit().putBoolean("strict", v).apply()

    /** The lenient renderer for the chosen output. */
    fun renderer(): (String) -> String {
        val tones = tones
        val out = output
        if (out == "transport") return { it }
        if (out.startsWith("stage:")) {
            val st = SpecData.STAGES[out.substring(6)]
            if (st != null) return { Stages.render(it, st, false, tones) }
        }
        return { Engine.render(it, false, tones) }
    }

    fun outputLabel(): String {
        val out = output
        if (out == "transport") return "transport"
        if (out.startsWith("stage:")) return SpecData.STAGES[out.substring(6)]?.name ?: "script"
        return "script"
    }
}
