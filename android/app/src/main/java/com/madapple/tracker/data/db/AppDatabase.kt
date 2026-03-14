package com.madapple.tracker.data.db

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [WorkoutLogEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun workoutLogDao(): WorkoutLogDao
}
