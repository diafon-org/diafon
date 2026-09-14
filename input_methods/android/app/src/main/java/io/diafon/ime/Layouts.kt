// The base layouts: where the 26 letters sit. Only placement changes; the
// typing is the same on every layout, since the engine only ever sees letters.
package io.diafon.ime

object Layouts {
    /** code -> (label, the three letter rows) */
    val ALL: List<Triple<String, String, List<String>>> = listOf(
        Triple("qwerty", "QWERTY", listOf("qwertyuiop", "asdfghjkl", "zxcvbnm")),
        Triple("qwertz", "QWERTZ", listOf("qwertzuiop", "asdfghjkl", "yxcvbnm")),
        Triple("azerty", "AZERTY", listOf("azertyuiop", "qsdfghjklm", "wxcvbn")),
        Triple("dvorak", "Dvorak", listOf("pyfgcrl", "aoeuidhtns", "qjkxbmwvz")),
        Triple("colemak", "Colemak", listOf("qwfpgjluy", "arstdhneio", "zxcvbkm")),
    )

    fun rows(code: String): List<String> = (ALL.firstOrNull { it.first == code } ?: ALL[0]).third

    fun label(code: String): String = (ALL.firstOrNull { it.first == code } ?: ALL[0]).second
}
