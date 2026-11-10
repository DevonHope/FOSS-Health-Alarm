package io.github.devonhope.nudgeband.protocol

enum class SleepStage(val label: String) { NO_DATA("No data"), DEEP("Deep / still"), LIGHT("Light"), AWAKE("Awake") }

/**
 * The simple light-sleep rule from docs/ble-protocol.md ("Smart-wake rule").
 * The firmware owns the real algorithm; this mirror draws past nights and drives the simulated band.
 */
object SleepScorer {
    const val EPOCH_SECONDS = 30
    const val AVERAGE_EPOCHS = 5
    const val LIGHT_AVERAGE_MG = 200
    const val LIGHT_SPIKE_MG = 1000
    const val SPIKE_EPOCHS = 2
    const val AWAKE_AVERAGE_MG = 3000

    /** Stage for the epoch at [index], using only that epoch and the ones before it. */
    fun stageAt(activity: List<Int>, index: Int): SleepStage {
        if (activity[index] == LogPacket.NO_DATA) return SleepStage.NO_DATA
        val window = (maxOf(0, index - AVERAGE_EPOCHS + 1)..index)
            .map { activity[it] }.filter { it != LogPacket.NO_DATA }
        val avg = window.average()
        val recentSpike = (maxOf(0, index - SPIKE_EPOCHS + 1)..index)
            .any { activity[it] != LogPacket.NO_DATA && activity[it] >= LIGHT_SPIKE_MG }
        return when {
            avg >= AWAKE_AVERAGE_MG -> SleepStage.AWAKE
            avg >= LIGHT_AVERAGE_MG || recentSpike -> SleepStage.LIGHT
            else -> SleepStage.DEEP
        }
    }

    fun stages(activity: List<Int>): List<SleepStage> = activity.indices.map { stageAt(activity, it) }

    fun isLightOrAwake(stage: SleepStage) = stage == SleepStage.LIGHT || stage == SleepStage.AWAKE

    data class Summary(
        val startUtc: Long,
        val endUtc: Long,
        val deepMinutes: Int,
        val lightMinutes: Int,
        val awakeMinutes: Int,
        val noDataMinutes: Int,
    ) {
        val totalMinutes get() = ((endUtc - startUtc) / 60).toInt()
    }

    fun summarize(night: SleepLog): Summary {
        val stages = stages(night.epochs.map { it.activity })
        fun minutes(s: SleepStage) = stages.count { it == s } * night.epochSeconds / 60
        return Summary(
            startUtc = night.epochs.firstOrNull()?.utc ?: 0,
            endUtc = (night.epochs.lastOrNull()?.utc ?: 0) + night.epochSeconds,
            deepMinutes = minutes(SleepStage.DEEP),
            lightMinutes = minutes(SleepStage.LIGHT),
            awakeMinutes = minutes(SleepStage.AWAKE),
            noDataMinutes = minutes(SleepStage.NO_DATA),
        )
    }
}
