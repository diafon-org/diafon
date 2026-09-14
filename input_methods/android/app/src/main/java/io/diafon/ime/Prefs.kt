// The settings above the keyboard, shared in name and default with every
// Diafon input method (plan.md, question 4): output, tones, strict, enabled;
// plus this keyboard's own: the base layout.
package io.diafon.ime

import android.content.Context
import android.content.SharedPreferences

class Prefs(ctx: Context) {
    private val sp: SharedPreferences = ctx.getSharedPreferences("diafon", Context.MODE_PRIVATE)

    /** Conversion on; off is a plain keyboard (the toggle key flips it). */
    var enabled: Boolean
        get() = sp.getBoolean("enabled", true)
        set(v) = sp.edit().putBoolean("enabled", v).apply()

    /** What is written out: "script" (universal: the web letters) or
     *  "stage:<code>" (a language's spelling). "transport" (as typed) exists
     *  for the escape path, never as a choice. */
    var output: String
        get() = sp.getString("output", "script")!!
        set(v) = sp.edit().putString("output", v).apply()

    /** Where the 26 letters sit: qwerty · qwertz · azerty · dvorak · colemak. */
    var layout: String
        get() = sp.getString("layout", "qwerty")!!
        set(v) = sp.edit().putString("layout", v).apply()

    /** Keep tone digits in the output. */
    var tones: Boolean
        get() = sp.getBoolean("tones", true)
        set(v) = sp.edit().putBoolean("tones", v).apply()

    /** Flag ill-formed segments in the strip (they still pass through). */
    var strict: Boolean
        get() = sp.getBoolean("strict", false)
        set(v) = sp.edit().putBoolean("strict", v).apply()

    /** The lenient renderer for an output (the chosen one by default). */
    fun renderer(out: String = output): (String) -> String {
        val tones = tones
        if (out == "transport") return { it }
        if (out.startsWith("stage:")) {
            val st = SpecData.STAGES[out.substring(6)]
            if (st != null) return { Stages.render(it, st, false, tones) }
        }
        return { Engine.render(it, false, tones) }
    }

    fun outputLabel(out: String = output): String = OUTPUTS.firstOrNull { it.first == out }?.second
        ?: SpecData.STAGES[out.removePrefix("stage:")]?.name ?: "universal"

    companion object {
        /** Every output, in the order every screen lists them: (value, label). */
        val OUTPUTS: List<Pair<String, String>> by lazy {
            listOf("script" to "Universal") +
                SpecData.STAGES.values.sortedBy { it.name }.map { "stage:${it.code}" to it.name }
        }
    }
}
