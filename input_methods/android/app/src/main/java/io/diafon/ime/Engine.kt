// The engine, ported rule for rule from scripts/engine.py; tables come from
// SpecData.kt (generated from docs/spec.json). tests/test_kotlin.py replays
// every spec vector through this file; run it after any change here.
package io.diafon.ime

import java.text.Normalizer

class ParseError(msg: String) : Exception(msg)

/** One segment of typed text: a form (base letter + operators + tones), a
 *  raw character outside the alphabet, or an ill-formed chunk. */
sealed class Seg(val src: String) {
    class Raw(src: String) : Seg(src)
    class Err(src: String) : Seg(src)
    class Form(src: String, val form: String, val tones: String) : Seg(src)
}

object Engine {
    val C_BASES: Set<Char> = "bdfghklmnprstvz".toSet()
    val V_BASES: Set<Char> = "aeiou".toSet()
    val BASES: Set<Char> = C_BASES + V_BASES
    val OPS: Set<Char> = "cjqxwy".toSet()

    private val WHOLE = SpecData.WHOLE
    private val MARKS = SpecData.MARKS
    private val WEB = SpecData.WEB
    private val WEB_UPPER = SpecData.WEB_UPPER
    private val DESC = SpecData.DESCENDERS
    private val PARTNER = SpecData.PARTNER
    private val BELOWS = MARKS.values.mapNotNull { it.below }

    fun nfc(s: String): String = Normalizer.normalize(s, Normalizer.Form.NFC)

    /** Segmentation: greedy, left to right. strict=true throws on ill-formed
     *  input (the reference reading); strict=false marks it Err and goes on
     *  (the input-method reading: such text passes through as typed). */
    fun segments(text: String, strict: Boolean = true): List<Seg> {
        val out = ArrayList<Seg>()
        var i = 0
        val n = text.length
        while (i < n) {
            val raw = text[i]
            val ch = raw.lowercaseChar()
            if (ch !in BASES) {
                if (ch in OPS || ch.isDigit()) {
                    if (strict) throw ParseError("position $i: '$raw' cannot start a segment")
                    out.add(Seg.Err(raw.toString()))
                } else out.add(Seg.Raw(raw.toString()))
                i++
                continue
            }
            var j = i + 1
            val ops = StringBuilder()
            while (j < n && text[j].lowercaseChar() in OPS) { ops.append(text[j].lowercaseChar()); j++ }
            val opsS = ops.toString()
            val w = 'w' in opsS
            val core = opsS.replace("w", "")
            var bad: String? = null
            if (core.length > 2) bad = "${text.substring(i, j)}: more than two operators"
            else if (opsS.count { it == 'w' } > 1 || (w && !opsS.endsWith("w")))
                bad = "${text.substring(i, j)}: w must come last, once"
            val tones = StringBuilder()
            while (j < n && text[j].isDigit()) { tones.append(text[j]); j++ }
            val src = text.substring(i, j)
            if (bad != null) {
                if (strict) throw ParseError(bad)
                out.add(Seg.Err(src))
            } else out.add(Seg.Form(src, raw + core + (if (w) "w" else ""), tones.toString()))
            i = j
        }
        return out
    }

    private fun hasBelow(g: String) = BELOWS.any { it in g }

    /** Attach a mark by the float rule and one-per-side: below unless the
     *  rendered letter has a descender (capitals never do). */
    private fun mark(g: String, base: Char, kind: String, caps: Boolean): String {
        val m = MARKS.getValue(kind)
        if (m.below != null && (caps || base !in DESC) && !hasBelow(g)) return g + m.below
        if (m.above != null) return g + m.above
        return g + (m.below ?: "")
    }

    private fun special(g: String, base: Char, caps: Boolean): String {
        val sp = MARKS.getValue("special")
        return if ((caps || base !in DESC) && !hasBelow(g)) g + sp.below else g + sp.above
    }

    /** Script glyph of one form; an uppercase base letter capitalizes it. A form
     *  written as a web letter (SpecData.WEB) capitalizes to that letter's case pair;
     *  an unlisted composition keeps the mark on the side the float rule gives the capital. */
    fun glyph(formIn: String): String {
        val caps = formIn[0].isUpperCase()
        val form = if (caps) formIn[0].lowercaseChar() + formIn.substring(1) else formIn
        val w = form.endsWith("w")
        val core = if (w) form.dropLast(1) else form
        val base = core[0]
        val longVowel = w && base in V_BASES && core !in WHOLE
        fun compose(cap: Boolean): String {
            var g = composeCore(core, cap)
            if (longVowel) {
                val flip = MARKS.getValue("flip").above!!
                g = if (flip in g) g.replace(flip, MARKS.getValue("double_acute").above!!)
                    else g + MARKS.getValue("acute").above!!
            }
            return nfc(g)
        }
        var g = compose(false)
        val web = WEB[g]
        if (web != null) g = web                           // the composition -> the letter the text carries
        else if (caps) g = compose(true)                   // unlisted (reserve): the float rule reads the capital
        if (w && !longVowel) g += g                        // long consonant doubles its letter
        g = nfc(g)
        if (caps) {
            val first = WEB_UPPER[g.substring(0, 1)] ?: g[0].uppercaseChar().toString()
            g = nfc(first + g.substring(1))
        }
        return g
    }

    /** The composed glyph of a core form (no length): marks as combining characters. */
    private fun composeCore(core: String, caps: Boolean): String {
        val base = core[0]
        val ops = core.substring(1)
        var g: String
        if (core in WHOLE) g = WHOLE.getValue(core)
        else if (core.length == 3 && core.substring(0, 2) in WHOLE) {
            g = WHOLE.getValue(core.substring(0, 2))
            when (core[2]) {
                'x' -> {                                   // the dot on an unmarked whole letter
                    if (hasBelow(g)) throw ParseError("$core: the dot cannot stack on a marked form")
                    g = mark(g, g[0], "dot", caps)
                }
                'y' -> {
                    val a = MARKS.getValue("anchor").below!!
                    if (a in g) g = g.replace(a, MARKS.getValue("reverse").below!!)   // y flips the anchored affricate
                    else if (hasBelow(g)) throw ParseError("$core: the special cannot stack on a marked form")
                    else g = special(g, g[0], caps)        // the special on a bare whole letter
                }
                else -> throw ParseError("$core: ${core[2]} cannot be secondary")
            }
        } else if (base in V_BASES) g = vowel(base, ops)
        else g = consonant(base, ops, caps)
        return g
    }

    private fun consonant(base: Char, ops: String, caps: Boolean): String {
        var g = base.toString()
        if (ops.isEmpty()) return g
        val op1 = ops[0]
        if ((op1 == 'j' || op1 == 'y') && base in "lrf") throw ParseError("$base$ops: no anchor on the thin stems l r f")
        when (op1) {
            'j' -> g = mark(g, base, "anchor", caps)
            'x' -> g = mark(g, base, "dot", caps)
            'y' -> g = mark(g, base, "reverse", caps)
            'c' -> g = mark(g, base, "dot", caps)          // the tap rc; other affricates are whole letters
            'q' -> throw ParseError("$base$ops: no such form")
        }
        if (ops.length == 1) return g
        val op2 = ops[1]
        if (op2 == 'x') throw ParseError("$base$ops: x cannot follow $op1")
        if (op2 == 'y') {
            if (op1 == 'x') return special(base.toString(), base, caps)   // the pair xy: y doubles the dot
            if (op1 == 'j' && base in "sz")                              // y flips the anchored hush
                return g.replace(MARKS.getValue("anchor").below!!, MARKS.getValue("reverse").below!!)
            throw ParseError("$base$ops: the special cannot stack on a marked form")
        }
        throw ParseError("$base$ops: $op2 cannot be secondary")
    }

    private fun vowel(base: Char, ops: String): String {
        var g = base.toString()
        for (op in ops) {
            when (op) {
                'c' -> g = PARTNER.getValue(base) + MARKS.getValue("flip").above!!
                'j' -> g += MARKS.getValue("underdot").below!!
                'q' -> g = PARTNER.getValue(base) + MARKS.getValue("flip").above!! + MARKS.getValue("underdot").below!!
                'y' -> g += MARKS.getValue("grave").above!!
                'x' -> throw ParseError("$base$ops: x composes only in the glides")
                else -> throw ParseError("$base$ops: bad vowel operator $op")
            }
        }
        return g
    }

    /** Script form of a text. strict=false passes ill-formed characters and
     *  formless segments through as typed; tones=false drops tone digits. */
    fun render(text: String, strict: Boolean = true, tones: Boolean = true): String {
        val out = StringBuilder()
        for (seg in segments(text, strict)) {
            if (seg !is Seg.Form) { out.append(seg.src); continue }
            try {
                out.append(glyph(seg.form)).append(if (tones) seg.tones else "")
            } catch (e: ParseError) {
                if (strict) throw e
                out.append(seg.src)
            }
        }
        return out.toString()
    }

    /** The streaming commit rule: everything before the last segment is
     *  final; a last segment that is a form may still grow, so it stays
     *  pending. Returns (committed, pending); the caller commits the first,
     *  shows the second as composing text, and calls again with
     *  pending + the next key. `renderer` is the lenient render of the
     *  chosen output (script, transport, or a stage). */
    fun stream(buffer: String, renderer: (String) -> String = { render(it, false) }): Pair<String, String> {
        val segs = segments(buffer, false)
        if (segs.isEmpty()) return Pair("", "")
        val last = segs.last()
        val (head, tail) = if (last is Seg.Form) Pair(segs.dropLast(1), last.src) else Pair(segs, "")
        return Pair(renderer(head.joinToString("") { it.src }), tail)
    }
}
