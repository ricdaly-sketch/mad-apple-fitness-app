package com.madapple.tracker.ui.thisweek

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.madapple.tracker.data.api.WorkoutDto
import com.madapple.tracker.databinding.ItemWorkoutBinding

class WorkoutAdapter(
    private val workouts: List<WorkoutDto>,
    private val onClick: (WorkoutDto) -> Unit,
) : RecyclerView.Adapter<WorkoutAdapter.ViewHolder>() {

    inner class ViewHolder(private val binding: ItemWorkoutBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(workout: WorkoutDto) {
            binding.textDay.text = workout.dayOfWeek
            binding.textTitle.text = workout.title
            binding.textType.text = workout.workoutType
            binding.root.setOnClickListener { onClick(workout) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemWorkoutBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) = holder.bind(workouts[position])
    override fun getItemCount() = workouts.size
}
