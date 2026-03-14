package com.madapple.tracker.data.api

import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface WorkoutApiService {

    @GET("workouts/week")
    suspend fun getWeekWorkouts(@Query("track") track: String): List<WorkoutDto>

    @GET("workouts/{id}")
    suspend fun getWorkout(@Path("id") id: Int): WorkoutDto
}
