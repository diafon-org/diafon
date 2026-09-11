// The vector check, driven by tests/test_kotlin.py: one request per stdin
// line, "mode<TAB>input", one result per stdout line.
//   render        strict script form, or "!ERR" when the input is rejected
//   lenient       lenient script form
//   stream        the keystroke trace: buffer, committed, pending joined by
//                 U+001E, steps joined by U+001F
//   stage:<code>  the stage's spelling
package io.diafon.ime

const val FIELD = ""
const val STEP = ""

fun main() {
    val sb = StringBuilder()
    generateSequence(::readLine).forEach { line ->
        val tab = line.indexOf('\t')
        val mode = line.substring(0, tab)
        val input = line.substring(tab + 1)
        val result = when {
            mode == "render" -> try { Engine.render(input) } catch (e: ParseError) { "!ERR" }
            mode == "lenient" -> Engine.render(input, false)
            mode == "stream" -> {
                var buf = ""
                val steps = ArrayList<String>()
                for (ch in input) {
                    buf += ch
                    val (c, p) = Engine.stream(buf)
                    steps.add(buf + FIELD + c + FIELD + p)
                    buf = p
                }
                steps.joinToString(STEP)
            }
            mode.startsWith("stage:") -> Stages.render(input, SpecData.STAGES.getValue(mode.substring(6)))
            else -> "!MODE"
        }
        sb.append(result).append('\n')
    }
    print(sb)
}
