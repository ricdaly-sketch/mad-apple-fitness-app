package com.madapple.tracker.ui.thisweek

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.madapple.tracker.data.api.WorkoutDto
import com.madapple.tracker.data.repository.Result
import com.madapple.tracker.data.repository.WorkoutRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class ThisWeekUiState {
    object Loading : ThisWeekUiState()
    data class Success(val workouts: List<WorkoutDto>) : ThisWeekUiState()
    data class Error(val message: String) : ThisWeekUiState()
}

@HiltViewModel
class ThisWeekViewModel @Inject constructor(
    private val repository: WorkoutRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow<ThisWeekUiState>(ThisWeekUiState.Loading)
    val uiState: StateFlow<ThisWeekUiState> = _uiState

    private var currentTrack = "wod"

    init {
        loadWorkouts("wod")
    }

    fun loadWorkouts(track: String) {
        currentTrack = track
        _uiState.value = ThisWeekUiState.Loading
        viewModelScope.launch {
            _uiState.value = when (val result = repository.getWeekWorkouts(track)) {
                is Result.Success -> ThisWeekUiState.Success(result.data)
                is Result.Error -> ThisWeekUiState.Error(result.message)
            }
        }
    }

    fun retry() = loadWorkouts(currentTrack)
}
