package com.madapple.tracker.ui.history

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.chip.Chip
import com.madapple.tracker.R
import com.madapple.tracker.databinding.FragmentHistoryBinding
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class HistoryFragment : Fragment() {

    private var _binding: FragmentHistoryBinding? = null
    private val binding get() = _binding!!
    private val viewModel: HistoryViewModel by viewModels()

    private val trackFilters = listOf(
        "all" to "All",
        "wod" to "WOD",
        "competitor" to "Competitor",
        "hyrox" to "Hyrox",
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHistoryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupChips()
        setupRecyclerView()
        observeGroups()
    }

    private fun setupChips() {
        trackFilters.forEach { (trackId, label) ->
            val chip = Chip(requireContext()).apply {
                text = label
                isCheckable = true
                isChecked = trackId == "all"
                setOnClickListener { viewModel.filterByTrack(trackId) }
            }
            binding.chipGroupTracks.addView(chip)
        }
    }

    private fun setupRecyclerView() {
        binding.recyclerHistory.layoutManager = LinearLayoutManager(requireContext())
    }

    private fun observeGroups() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.groups.collect { groups ->
                    binding.textEmpty.visibility = if (groups.isEmpty()) View.VISIBLE else View.GONE
                    binding.recyclerHistory.adapter = HistoryAdapter(groups)
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
