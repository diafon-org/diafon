// The keys: the 26 letters on the chosen base layout (Layouts.kt), digits for
// tones, and the few functional keys. No dictionary, no prediction: the
// system needs none of them. Operators are tinted with the site's colours so
// the eye learns the split.
package io.diafon.ime

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.view.HapticFeedbackConstants
import android.view.MotionEvent
import android.view.View

sealed class Key {
    data class Char(val ch: kotlin.Char) : Key()
    object Space : Key()
    object Backspace : Key()
    object Shift : Key()
    object Enter : Key()
    object Toggle : Key()
    object Settings : Key()
}

class KeyboardView(ctx: Context, private val onKey: (Key) -> Unit) : View(ctx) {
    var shifted = false
        set(v) { field = v; invalidate() }
    var enabledMode = true
        set(v) { field = v; invalidate() }
    var layout = "qwerty"
        set(v) { if (field != v) { field = v; rows = buildRows(v); if (width > 0) onSizeChanged(width, height, width, height); requestLayout(); invalidate() } }

    private class Slot(val key: Key, val rect: RectF)

    private val slots = ArrayList<Slot>()
    private var pressed: Slot? = null
    private val density = resources.displayMetrics.density
    private val rowH = 52f * density
    private val gap = 3f * density
    private val fill = Paint(Paint.ANTI_ALIAS_FLAG)
    private val text = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER }

    private val opColor = mapOf(
        'c' to 0xFFB06F14.toInt(), 'j' to 0xFF2F6FB0.toInt(), 'q' to 0xFF7A4FB0.toInt(),
        'x' to 0xFF2F8F66.toInt(), 'y' to 0xFFB03F7A.toInt(), 'w' to 0xFF5B6472.toInt())

    // rows of (key, width in letter-key units); the letter rows follow the layout
    private var rows: List<List<Pair<Key, Float>>> = buildRows("qwerty")

    private fun buildRows(code: String): List<List<Pair<Key, Float>>> {
        val letters = Layouts.rows(code)
        val last = letters[2]
        val side = ((10f - last.length) / 2f).coerceAtLeast(1f)     // shift and backspace share what the row leaves
        return listOf(
            "1234567890".map { Key.Char(it) to 1f },
            letters[0].map { Key.Char(it) to 1f },
            letters[1].map { Key.Char(it) to 1f },
            listOf<Pair<Key, Float>>(Key.Shift to side) + last.map { Key.Char(it) to 1f } + listOf<Pair<Key, Float>>(Key.Backspace to side),
            listOf(Key.Toggle to 1.5f, Key.Settings to 1f, Key.Char(',') to 1f, Key.Space to 4f, Key.Char('.') to 1f, Key.Enter to 1.5f),
        )
    }

    override fun onMeasure(widthSpec: Int, heightSpec: Int) {
        setMeasuredDimension(MeasureSpec.getSize(widthSpec), (rowH * rows.size + gap).toInt())
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        slots.clear()
        val unit = w / 10f
        rows.forEachIndexed { r, row ->
            val total = row.sumOf { it.second.toDouble() }.toFloat()
            var x = (w - total * unit) / 2f
            val top = r * rowH + gap
            for ((key, wgt) in row) {
                slots.add(Slot(key, RectF(x + gap / 2, top, x + wgt * unit - gap / 2, top + rowH - gap)))
                x += wgt * unit
            }
        }
    }

    private fun label(key: Key): String = when (key) {
        is Key.Char -> if (shifted && key.ch.isLetter()) key.ch.uppercaseChar().toString() else key.ch.toString()
        Key.Space -> ""
        Key.Backspace -> "⌫"
        Key.Shift -> "⇧"
        Key.Enter -> "↵"
        Key.Toggle -> if (enabledMode) "Dia" else "abc"
        Key.Settings -> "⚙"
    }

    override fun onDraw(canvas: Canvas) {
        val r = 6f * density
        for (s in slots) {
            val functional = s.key !is Key.Char
            fill.color = when {
                s === pressed -> 0xFFC9D1DC.toInt()
                s.key == Key.Shift && shifted -> 0xFF0E7C86.toInt()
                functional -> 0xFFDDE1E8.toInt()
                else -> 0xFFFFFFFF.toInt()
            }
            canvas.drawRoundRect(s.rect, r, r, fill)
            val k = s.key
            text.color = when {
                s.key == Key.Shift && shifted -> 0xFFFFFFFF.toInt()
                k is Key.Char && k.ch in opColor -> opColor.getValue(k.ch)
                k is Key.Toggle && enabledMode -> 0xFF0E7C86.toInt()
                else -> 0xFF1A1D24.toInt()
            }
            text.textSize = (if (functional) 18f else 22f) * density
            text.isFakeBoldText = k is Key.Char && k.ch in opColor
            val y = s.rect.centerY() - (text.descent() + text.ascent()) / 2
            canvas.drawText(label(k), s.rect.centerX(), y, text)
        }
    }

    private fun hit(x: Float, y: Float) = slots.firstOrNull { it.rect.contains(x, y) }

    override fun onTouchEvent(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                val s = hit(e.x, e.y) ?: return true
                pressed = s
                invalidate()
                performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP)
                onKey(s.key)
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { pressed = null; invalidate() }
        }
        return true
    }
}
