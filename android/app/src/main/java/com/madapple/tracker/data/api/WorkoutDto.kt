package com.madapple.tracker.data.api

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class WorkoutDto(
    val id: Int,
    val track: String,
    @Json(name = "day_of_week") val dayOfWeek: String,
    @Json(name = "week_start_date") val weekStartDate: String,
    val title: String,
    @Json(name = "workout_type") val workoutType: String,
    val description: String,
    @Json(name = "scraped_at") val scrapedAt: String,
)
