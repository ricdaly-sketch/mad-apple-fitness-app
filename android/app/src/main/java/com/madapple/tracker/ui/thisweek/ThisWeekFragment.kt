package com.madapple.tracker.ui.thisweek

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.snackbar.Snackbar
import com.madapple.tracker.R
import com.madapple.tracker.data.api.WorkoutDto
import com.madapple.tracker.databinding.FragmentThisWeekBinding
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class ThisWeekFragment : Fragment() {

    private var _binding: FragmentThisWeekBinding? = null
    private val binding get() = _binding!!
    private val viewModel: ThisWeekViewModel by viewModels()

    private val tracks = listOf(
        "wod" to "Workout of the Day",
        "competitor" to "Competitor Track",
        "hyrox" to "Hyrox",
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentThisWeekBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupTrackSpinner()
        setupRecyclerView()
        setupRetryButton()
        observeUiState()
    }

    private fun setupTrackSpinner() {
        val labels = tracks.map { it.second }
        val adapter = ArrayAdapter(requireContext(), android.R.layout.simple_spinner_item, labels)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerTrack.adapter = adapter
        binding.spinnerTrack.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>, view: View?, pos: Int, id: Long) {
                viewModel.loadWorkouts(tracks[pos].first)
            }
            override fun onNothingSelected(parent: AdapterView<*>) = Unit
        }
    }

    private fun setupRecyclerView() {
        binding.recyclerWorkouts.layoutManager = LinearLayoutManager(requireContext())
    }

    private fun setupRetryButton() {
        binding.buttonRetry.setOnClickListener { viewModel.retry() }
    }

    private fun observeUiState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when (state) {
                        is ThisWeekUiState.Loading -> showLoading()
                        is ThisWeekUiState.Success -> showWorkouts(state.workouts)
                        is ThisWeekUiState.Error -> showError(state.message)
                    }
                }
            }
        }
    }

    private fun showLoading() {
        binding.progressBar.visibility = View.VISIBLE
        binding.recyclerWorkouts.visibility = View.GONE
        binding.layoutError.visibility = View.GONE
    }

    private fun showWorkouts(workouts: List<WorkoutDto>) {
        binding.progressBar.visibility = View.GONE
        binding.recyclerWorkouts.visibility = View.VISIBLE
        binding.layoutError.visibility = View.GONE
        binding.recyclerWorkouts.adapter = WorkoutAdapter(workouts) { workout ->
            findNavController().navigate(
                ThisWeekFragmentDirections.actionThisWeekToDetail(workout.id)
            )
        }
    }

    private fun showError(message: String) {
        binding.progressBar.visibility = View.GONE
        binding.recyclerWorkouts.visibility = View.GONE
        binding.layoutError.visibility = View.VISIBLE
        binding.textErrorMessage.text = getString(R.string.error_load_workouts)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
