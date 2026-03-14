package com.madapple.tracker.ui.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.madapple.tracker.data.db.WorkoutLogEntity
import com.madapple.tracker.data.repository.WorkoutRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class WorkoutGroup(
    val title: String,
    val track: String,
    val logs: List<WorkoutLogEntity>,
)

@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val repository: WorkoutRepository,
) : ViewModel() {

    private val _groups = MutableStateFlow<List<WorkoutGroup>>(emptyList())
    val groups: StateFlow<List<WorkoutGroup>> = _groups

    private var selectedTrack = "all"

    init {
        observeLogs("all")
    }

    fun filterByTrack(track: String) {
        selectedTrack = track
        observeLogs(track)
    }

    private fun observeLogs(track: String) {
        viewModelScope.launch {
            repository.getLogsFilteredByTrack(track).collect { logs ->
                _groups.value = logs
                    .groupBy { "${it.workoutTitle}::${it.track}" }
                    .map { (_, groupLogs) ->
                        WorkoutGroup(
                            title = groupLogs.first().workoutTitle,
                            track = groupLogs.first().track,
                            logs = groupLogs.sortedByDescending { it.loggedAt },
                        )
                    }
                    .sortedByDescending { it.logs.first().loggedAt }
            }
        }
    }
}
