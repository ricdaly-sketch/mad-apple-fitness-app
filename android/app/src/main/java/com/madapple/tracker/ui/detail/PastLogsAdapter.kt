package com.madapple.tracker.ui.detail

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.madapple.tracker.data.db.WorkoutLogEntity
import com.madapple.tracker.databinding.ItemPastLogBinding
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class PastLogsAdapter(
    private val logs: List<WorkoutLogEntity>,
) : RecyclerView.Adapter<PastLogsAdapter.ViewHolder>() {

    private val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())

    inner class ViewHolder(private val binding: ItemPastLogBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(log: WorkoutLogEntity) {
            binding.textLogDate.text = dateFormat.format(Date(log.loggedAt))
            binding.textTimeResult.text = log.timeResult.ifEmpty { "—" }
            binding.textWeightsUsed.text = log.weightsUsed.ifEmpty { "—" }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemPastLogBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) = holder.bind(logs[position])
    override fun getItemCount() = logs.size
}
