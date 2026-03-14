package com.madapple.tracker.data.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "workout_logs")
data class WorkoutLogEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    @ColumnInfo(name = "workout_id") val workoutId: Int,
    val track: String,
    @ColumnInfo(name = "workout_title") val workoutTitle: String,
    @ColumnInfo(name = "workout_description") val workoutDescription: String,
    @ColumnInfo(name = "day_of_week") val dayOfWeek: String,
    @ColumnInfo(name = "week_start_date") val weekStartDate: String,
    @ColumnInfo(name = "time_result") val timeResult: String,
    @ColumnInfo(name = "weights_used") val weightsUsed: String,
    @ColumnInfo(name = "logged_at") val loggedAt: Long = System.currentTimeMillis(),
)
