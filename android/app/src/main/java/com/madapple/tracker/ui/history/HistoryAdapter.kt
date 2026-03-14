package com.madapple.tracker.ui.history

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.madapple.tracker.databinding.ItemHistoryGroupBinding
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class HistoryAdapter(
    private val groups: List<WorkoutGroup>,
) : RecyclerView.Adapter<HistoryAdapter.ViewHolder>() {

    private val dateFormat = SimpleDateFormat("dd MMM", Locale.getDefault())

    inner class ViewHolder(private val binding: ItemHistoryGroupBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(group: WorkoutGroup) {
            binding.textGroupTitle.text = group.title
            binding.textTrackBadge.text = group.track.uppercase()
            binding.textDoneCount.text = "Done ${group.logs.size}x"

            // Show last two attempts inline
            val summary = group.logs.take(2).joinToString("  |  ") { log ->
                val datePart = dateFormat.format(Date(log.loggedAt))
                val result = listOfNotNull(
                    log.timeResult.ifEmpty { null },
                    log.weightsUsed.ifEmpty { null }
                ).joinToString(" · ")
                "$datePart: $result"
            }
            binding.textRecentAttempts.text = summary
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemHistoryGroupBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) = holder.bind(groups[position])
    override fun getItemCount() = groups.size
}
