// Spelling stages, ported from scripts/stages.py: the point stream written
// in a language's current orthography. Render-only; forms the stage does not
// spell fall back to the script glyph.
package io.diafon.ime

object Stages {
    fun spell(st: Stage, form: String): String? {
        val caps = form[0].isUpperCase()
        val low = form[0].lowercaseChar() + form.substring(1)
        var sp = st.forms[low]
        var capsp = st.caps[low]                       // a capital spelled on its own (g̓ -> G̦)
        if (sp == null && low.endsWith("w") && low[0] in Engine.C_BASES) {
            val shortForm = low.dropLast(1)
            val short = st.forms[shortForm]
            if (short != null) {
                if (st.long == "first-letter") sp = short[0] + short
                else {
                    sp = short + short
                    st.caps[shortForm]?.let { capsp = it + short }
                }
            }
        }
        if (sp == null) return null
        if (!caps) return sp
        return capsp ?: Engine.nfc(sp[0].uppercaseChar() + sp.substring(1))
    }

    /** A soft consonant before a vowel, or null: Polish sj + i is si, sj + e sie; Czech tj + i ti. */
    fun soft(st: Stage, form: String, next: String?): String? {
        val low = form[0].lowercaseChar() + form.substring(1)
        if (next == null || next[0].lowercaseChar() !in Engine.V_BASES) return null
        val n = next.lowercase()
        val isI = n == "i" || n == "iw"
        val plain = st.beforeI[low]
        val bv = st.beforeVowel[low]
        val sp = when {
            plain != null && isI -> plain
            plain != null && st.iSoftens -> plain + "i"
            bv != null && !isI -> bv + "i"
            else -> return null
        }
        return if (form[0].isUpperCase()) sp[0].uppercaseChar() + sp.substring(1) else sp
    }

    fun render(text: String, st: Stage, strict: Boolean = false, tones: Boolean = true): String {
        val out = StringBuilder()
        val segs = Engine.segments(text, strict)
        for ((k, seg) in segs.withIndex()) {
            if (seg !is Seg.Form) { out.append(seg.src); continue }
            var sp = soft(st, seg.form, (segs.getOrNull(k + 1) as? Seg.Form)?.form) ?: spell(st, seg.form)
            if (sp == null) {
                if (strict) throw ParseError("${seg.form}: not spelled in the ${st.code} stage")
                sp = try { Engine.glyph(seg.form) } catch (e: ParseError) { seg.src }
            }
            out.append(sp).append(if (tones) seg.tones else "")
        }
        return out.toString()
    }
}
