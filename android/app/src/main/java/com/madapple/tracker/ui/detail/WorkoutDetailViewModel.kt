package com.madapple.tracker.ui.detail

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.madapple.tracker.data.api.WorkoutDto
import com.madapple.tracker.data.db.WorkoutLogEntity
import com.madapple.tracker.data.repository.Result
import com.madapple.tracker.data.repository.WorkoutRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class DetailUiState {
    object Loading : DetailUiState()
    data class Success(val workout: WorkoutDto) : DetailUiState()
    data class Error(val message: String) : DetailUiState()
}

@HiltViewModel
class WorkoutDetailViewModel @Inject constructor(
    private val repository: WorkoutRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow<DetailUiState>(DetailUiState.Loading)
    val uiState: StateFlow<DetailUiState> = _uiState

    private val _saveEvent = MutableStateFlow<SaveEvent>(SaveEvent.Idle)
    val saveEvent: StateFlow<SaveEvent> = _saveEvent

    private var currentWorkout: WorkoutDto? = null

    val pastLogs: StateFlow<List<WorkoutLogEntity>> = MutableStateFlow(emptyList())

    fun loadWorkout(workoutId: Int) {
        viewModelScope.launch {
            _uiState.value = when (val result = repository.getWorkout(workoutId)) {
                is Result.Success -> {
                    currentWorkout = result.data
                    observePastLogs(result.data.title, result.data.track)
                    DetailUiState.Success(result.data)
                }
                is Result.Error -> DetailUiState.Error(result.message)
            }
        }
    }

    private fun observePastLogs(title: String, track: String) {
        viewModelScope.launch {
            repository.getLogsForWorkout(title, track).collect { logs ->
                (_pastLogs as MutableStateFlow).value = logs
            }
        }
    }

    private val _pastLogs = MutableStateFlow<List<WorkoutLogEntity>>(emptyList())
    val pastLogsState: StateFlow<List<WorkoutLogEntity>> = _pastLogs

    fun saveLog(timeResult: String, weightsUsed: String) {
        val workout = currentWorkout ?: return
        viewModelScope.launch {
            val log = WorkoutLogEntity(
                workoutId = workout.id,
                track = workout.track,
                workoutTitle = workout.title,
                workoutDescription = workout.description,
                dayOfWeek = workout.dayOfWeek,
                weekStartDate = workout.weekStartDate,
                timeResult = timeResult,
                weightsUsed = weightsUsed,
            )
            repository.saveLog(log)
            val isImprovement = _pastLogs.value.isNotEmpty()
            _saveEvent.value = SaveEvent.Saved(isImprovement)
        }
    }

    fun clearSaveEvent() {
        _saveEvent.value = SaveEvent.Idle
    }
}

sealed class SaveEvent {
    object Idle : SaveEvent()
    data class Saved(val showImprovementBanner: Boolean) : SaveEvent()
}
