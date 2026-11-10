package io.github.devonhope.nudgeband.protocol

enum class SleepStage(val label: String) { NO_DATA("No data"), DEEP("Deep / still"), LIGHT("Light"), AWAKE("Awake") }

/**
 * Mirror of the firmware's smart-wake rule (docs/ble-protocol.md, "Smart-wake rule";
 * firmware/src/smartwake.c). Keep the two in step.
 */
object SleepScorer {
    const val EPOCH_SECONDS = 30
    const val MIN_THRESHOLD_MG = 300
    const val MEDIAN_FACTOR = 3
    const val WARMUP_EPOCHS = 20
    const val LOOKBACK_EPOCHS = 3
    const val LIGHT_HITS = 2

    /** Display only: the band does not use "awake". */
    const val AWAKE_AVERAGE_MG = 3000

    /**
     * Light-sleep threshold for each epoch, from the night so far (epochs up to and including it).
     * Index i of the result is the threshold in force at epoch i.
     */
    fun thresholds(activity: List<Int>): List<Int> {
        val seen = ArrayList<Int>(activity.size)
        return activity.map { a ->
            if (a != LogPacket.NO_DATA) insertSorted(seen, a)
            if (seen.size < WARMUP_EPOCHS) MIN_THRESHOLD_MG
            else maxOf(MIN_THRESHOLD_MG, MEDIAN_FACTOR * median(seen))
        }
    }

    private fun insertSorted(list: ArrayList<Int>, v: Int) {
        var i = list.binarySearch(v)
        if (i < 0) i = -i - 1
        list.add(i, v)
    }

    private fun median(sorted: List<Int>): Int {
        val n = sorted.size
        return if (n % 2 == 1) sorted[n / 2] else (sorted[n / 2 - 1] + sorted[n / 2]) / 2
    }

    /** True if at least 2 of the last 3 epochs (from [firstAllowed] onward) reach [threshold]. */
    fun isLight(activity: List<Int>, index: Int, threshold: Int, firstAllowed: Int = 0): Boolean {
        val from = maxOf(firstAllowed, index - LOOKBACK_EPOCHS + 1)
        val hits = (from..index).count { activity[it] != LogPacket.NO_DATA && activity[it] >= threshold }
        return hits >= LIGHT_HITS
    }

    fun stages(activity: List<Int>): List<SleepStage> {
        val th = thresholds(activity)
        return activity.indices.map { i ->
            if (activity[i] == LogPacket.NO_DATA) return@map SleepStage.NO_DATA
            val recent = (maxOf(0, i - LOOKBACK_EPOCHS + 1)..i).map { activity[it] }.filter { it != LogPacket.NO_DATA }
            when {
                recent.size == LOOKBACK_EPOCHS && recent.average() >= AWAKE_AVERAGE_MG -> SleepStage.AWAKE
                isLight(activity, i, th[i]) -> SleepStage.LIGHT
                else -> SleepStage.DEEP
            }
        }
    }

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
