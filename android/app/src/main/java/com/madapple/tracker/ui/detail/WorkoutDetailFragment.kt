package com.madapple.tracker.ui.detail

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.navArgs
import androidx.recyclerview.widget.LinearLayoutManager
import com.madapple.tracker.R
import com.madapple.tracker.databinding.FragmentWorkoutDetailBinding
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class WorkoutDetailFragment : Fragment() {

    private var _binding: FragmentWorkoutDetailBinding? = null
    private val binding get() = _binding!!
    private val viewModel: WorkoutDetailViewModel by viewModels()
    private val args: WorkoutDetailFragmentArgs by navArgs()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentWorkoutDetailBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel.loadWorkout(args.workoutId)

        binding.buttonSave.setOnClickListener {
            val time = binding.editTimeResult.text.toString().trim()
            val weights = binding.editWeightsUsed.text.toString().trim()
            if (time.isNotEmpty() || weights.isNotEmpty()) {
                viewModel.saveLog(time, weights)
                binding.editTimeResult.text?.clear()
                binding.editWeightsUsed.text?.clear()
            }
        }

        binding.recyclerPastLogs.layoutManager = LinearLayoutManager(requireContext())

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch { viewModel.uiState.collect { renderUiState(it) } }
                launch { viewModel.pastLogsState.collect { renderPastLogs(it) } }
                launch { viewModel.saveEvent.collect { handleSaveEvent(it) } }
            }
        }
    }

    private fun renderUiState(state: DetailUiState) {
        when (state) {
            is DetailUiState.Loading -> {
                binding.progressBar.visibility = View.VISIBLE
                binding.contentGroup.visibility = View.GONE
            }
            is DetailUiState.Success -> {
                binding.progressBar.visibility = View.GONE
                binding.contentGroup.visibility = View.VISIBLE
                binding.textWorkoutTitle.text = state.workout.title
                binding.textWorkoutType.text = state.workout.workoutType
                binding.textWorkoutDescription.text = state.workout.description
                binding.textDayLabel.text = state.workout.dayOfWeek
            }
            is DetailUiState.Error -> {
                binding.progressBar.visibility = View.GONE
                binding.textWorkoutTitle.text = getString(R.string.error_load_workouts)
            }
        }
    }

    private fun renderPastLogs(logs: List<com.madapple.tracker.data.db.WorkoutLogEntity>) {
        binding.sectionPastAttempts.visibility = if (logs.isEmpty()) View.GONE else View.VISIBLE
        binding.recyclerPastLogs.adapter = PastLogsAdapter(logs)
    }

    private fun handleSaveEvent(event: SaveEvent) {
        if (event is SaveEvent.Saved) {
            if (event.showImprovementBanner) {
                binding.bannerImprovement.visibility = View.VISIBLE
                binding.bannerImprovement.postDelayed({
                    binding.bannerImprovement.visibility = View.GONE
                }, 3000)
            }
            viewModel.clearSaveEvent()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
