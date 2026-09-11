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

    fun render(text: String, st: Stage, strict: Boolean = false, tones: Boolean = true): String {
        val out = StringBuilder()
        for (seg in Engine.segments(text, strict)) {
            if (seg !is Seg.Form) { out.append(seg.src); continue }
            var sp = spell(st, seg.form)
            if (sp == null) {
                if (strict) throw ParseError("${seg.form}: not spelled in the ${st.code} stage")
                sp = try { Engine.glyph(seg.form) } catch (e: ParseError) { seg.src }
            }
            out.append(sp).append(if (tones) seg.tones else "")
        }
        return out.toString()
    }
}
