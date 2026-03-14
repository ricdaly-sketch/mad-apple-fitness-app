package com.madapple.tracker.data.repository

import com.madapple.tracker.data.api.WorkoutApiService
import com.madapple.tracker.data.api.WorkoutDto
import com.madapple.tracker.data.db.WorkoutLogDao
import com.madapple.tracker.data.db.WorkoutLogEntity
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
}

@Singleton
class WorkoutRepository @Inject constructor(
    private val api: WorkoutApiService,
    private val dao: WorkoutLogDao,
) {
    suspend fun getWeekWorkouts(track: String): Result<List<WorkoutDto>> {
        return try {
            Result.Success(api.getWeekWorkouts(track))
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to load workouts")
        }
    }

    suspend fun getWorkout(id: Int): Result<WorkoutDto> {
        return try {
            Result.Success(api.getWorkout(id))
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to load workout")
        }
    }

    fun getLogsForWorkout(title: String, track: String): Flow<List<WorkoutLogEntity>> =
        dao.getLogsForWorkout(title, track)

    fun getAllLogs(): Flow<List<WorkoutLogEntity>> = dao.getAllLogs()

    fun getLogsFilteredByTrack(track: String): Flow<List<WorkoutLogEntity>> =
        dao.getLogsFilteredByTrack(track)

    suspend fun saveLog(log: WorkoutLogEntity) = dao.insert(log)
}
