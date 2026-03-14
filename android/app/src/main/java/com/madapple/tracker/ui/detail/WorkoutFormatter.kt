package com.madapple.tracker.ui.detail

import android.graphics.Typeface
import android.text.SpannableStringBuilder
import android.text.style.RelativeSizeSpan
import android.text.style.StyleSpan

/**
 * Converts a raw workout description string into a formatted Spannable
 * with bold section headers and visual spacing between sections.
 */
object WorkoutFormatter {

    private val SCORE_TYPES = setOf(
        "completion", "time", "reps", "weight", "distance", "calories",
        "rounds/reps", "no score", "comment only"
    )

    private val SECTION_KEYWORDS = listOf(
        "warm-up flow", "general warm-up", "warm-up", "warm up",
        "specific prep", "specific barbell prep", "specific barbell primer",
        "specific gymnastics prep", "specific primer",
        "strength", "weightlifting", "gymnastics",
        "conditioning", "primer", "mobility", "cool down",
        "optional accessories", "accessories", "threshold"
    )

    fun format(rawDescription: String, title: String): CharSequence {
        val sb = SpannableStringBuilder()
        val lines = rawDescription.split("\n")

        lines.forEachIndexed { index, line ->
            val trimmed = line.trim()

            // Skip internal PushPress markers like [Levels:"Fuse"]
            if (trimmed.startsWith("[") && trimmed.contains(":")) return@forEachIndexed

            // Skip duplicate title at top of description
            if (index == 0 && trimmed.equals(title, ignoreCase = true)) return@forEachIndexed

            if (trimmed.isEmpty()) return@forEachIndexed

            val lower = trimmed.lowercase()

            val isScoreType = lower in SCORE_TYPES
            val isSectionHeader = SECTION_KEYWORDS.any { lower.startsWith(it) }
            val isWorkoutName = trimmed.startsWith("\"") && trimmed.endsWith("\"")
            val isLevelHeader = lower.matches(Regex("level \\d.*")) ||
                    lower.startsWith("masters") ||
                    lower.startsWith("competitor:") ||
                    lower.startsWith("travel")

            when {
                isScoreType -> {
                    // Score type lines (Completion, Time, etc.) — small caps label, add spacing before
                    appendSpacing(sb)
                    val start = sb.length
                    sb.append(trimmed.uppercase())
                    sb.setSpan(StyleSpan(Typeface.BOLD), start, sb.length, 0)
                    sb.setSpan(RelativeSizeSpan(0.75f), start, sb.length, 0)
                    sb.append("\n")
                }
                isWorkoutName -> {
                    // Quoted workout name like "Fuse" — large bold
                    appendSpacing(sb)
                    val start = sb.length
                    sb.append(trimmed)
                    sb.setSpan(StyleSpan(Typeface.BOLD), start, sb.length, 0)
                    sb.setSpan(RelativeSizeSpan(1.2f), start, sb.length, 0)
                    sb.append("\n")
                }
                isSectionHeader -> {
                    // Major section header — bold with spacing
                    appendSpacing(sb)
                    val start = sb.length
                    sb.append(trimmed)
                    sb.setSpan(StyleSpan(Typeface.BOLD), start, sb.length, 0)
                    sb.append("\n")
                }
                isLevelHeader -> {
                    // Level sub-header (Level 1, Masters 55+, etc.) — bold with divider
                    appendSpacing(sb)
                    val start = sb.length
                    sb.append("▸ $trimmed")
                    sb.setSpan(StyleSpan(Typeface.BOLD), start, sb.length, 0)
                    sb.append("\n")
                }
                else -> {
                    sb.append(trimmed)
                    sb.append("\n")
                }
            }
        }

        return sb.trimEnd()
    }

    private fun appendSpacing(sb: SpannableStringBuilder) {
        if (sb.isNotEmpty()) sb.append("\n")
    }
}
