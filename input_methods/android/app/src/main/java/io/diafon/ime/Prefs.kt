// The settings above the keyboard, shared in name and default with every
// Diafon input method (input_methods/README.md, Settings): output, language,
// tones, join, strict, enabled; plus this keyboard's own: the base layout.
package io.diafon.ime

import android.content.Context
import android.content.SharedPreferences
import android.os.LocaleList

class Prefs(ctx: Context) {
    private val sp: SharedPreferences = ctx.getSharedPreferences("diafon", Context.MODE_PRIVATE)

    /** Conversion on; off is a plain keyboard (the toggle key flips it). */
    var enabled: Boolean
        get() = sp.getBoolean("enabled", true)
        set(v) = sp.edit().putBoolean("enabled", v).apply()

    /** What is written out: "script" (Universal, the default) or
     *  "stage:<code>" (a language's spelling). "transport" (as typed) exists
     *  for the escape path, never as a choice. */
    var output: String
        get() = sp.getString("output", "script")!!
        set(v) {
            sp.edit().putString("output", v).apply()
            if (v.startsWith("stage:")) language = v.removePrefix("stage:")
        }

    /** Universal is written out (not a language's spelling). */
    val universal: Boolean get() = !output.startsWith("stage:")

    /** The language whose spelling the second choice writes; kept when the
     *  output goes back to Universal. Default: the first system language with
     *  a spelling, else the first in the list. */
    var language: String
        get() = sp.getString("language", null)?.takeIf { it in SpecData.STAGES }
            ?: output.removePrefix("stage:").takeIf { output.startsWith("stage:") && it in SpecData.STAGES }
            ?: systemLanguage()
        set(v) = sp.edit().putString("language", v).apply()

    private fun systemLanguage(): String {
        val locales = LocaleList.getDefault()
        for (i in 0 until locales.size()) {
            val code = locales[i].language
            if (code in SpecData.STAGES) return code
        }
        return LANGUAGES.first().first
    }

    /** The two choices every screen offers, Universal and the language's spelling: (value, label). */
    fun choices(): List<Pair<String, String>> =
        listOf("script" to "Universal", "stage:$language" to (SpecData.STAGES[language]?.name ?: language))

    /** Where the 26 letters sit: qwerty · qwertz · azerty · dvorak · colemak. */
    var layout: String
        get() = sp.getString("layout", "qwerty")!!
        set(v) = sp.edit().putString("layout", v).apply()

    /** Write tones: a digit after a syllable becomes its tone sign; off, tone digits are dropped. */
    var tones: Boolean
        get() = sp.getBoolean("tones", true)
        set(v) = sp.edit().putBoolean("tones", v).apply()

    /** Join a long consonant's two letters with a ZWJ (the Diafon fonts draw
     *  them fused); off, a plain double. */
    var join: Boolean
        get() = sp.getBoolean("join", false)
        set(v) = sp.edit().putBoolean("join", v).apply()

    /** Flag ill-formed segments in the strip (they still pass through). */
    var strict: Boolean
        get() = sp.getBoolean("strict", false)
        set(v) = sp.edit().putBoolean("strict", v).apply()

    /** The lenient renderer for an output (the chosen one by default). */
    fun renderer(out: String = output): (String) -> String {
        val tones = tones
        val join = join
        if (out == "transport") return { it }
        if (out.startsWith("stage:")) {
            val st = SpecData.STAGES[out.substring(6)]
            if (st != null) return { Stages.render(it, st, false, tones) }
        }
        return { Engine.render(it, false, tones, join) }
    }

    fun outputLabel(out: String = output): String =
        if (out.startsWith("stage:")) SpecData.STAGES[out.removePrefix("stage:")]?.name ?: "Universal" else "Universal"

    companion object {
        /** The languages with a spelling, in the order the list shows them: (code, name). */
        val LANGUAGES: List<Pair<String, String>> by lazy {
            SpecData.STAGES.values.sortedBy { it.name }.map { it.code to it.name }
        }
    }
}
