package com.madapple.tracker.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface WorkoutLogDao {

    @Insert
    suspend fun insert(log: WorkoutLogEntity)

    @Query("SELECT * FROM workout_logs ORDER BY logged_at DESC")
    fun getAllLogs(): Flow<List<WorkoutLogEntity>>

    @Query("""
        SELECT * FROM workout_logs
        WHERE workout_title = :title AND track = :track
        ORDER BY logged_at DESC
    """)
    fun getLogsForWorkout(title: String, track: String): Flow<List<WorkoutLogEntity>>

    @Query("""
        SELECT * FROM workout_logs
        WHERE (:track = 'all' OR track = :track)
        ORDER BY logged_at DESC
    """)
    fun getLogsFilteredByTrack(track: String): Flow<List<WorkoutLogEntity>>
}
