package io.github.devonhope.nudgeband.protocol

import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneOffset

/** Works out alarm times from an [AlarmConfig], in the band's local time (UTC + offset). */
object AlarmSchedule {
    /** UTC seconds of the next alarm time strictly after [nowUtc], or null if the alarm is off. */
    fun nextAlarmUtc(config: AlarmConfig, nowUtc: Long, offsetMinutes: Int): Long? {
        if (!config.enabled) return null
        val offset = ZoneOffset.ofTotalSeconds(offsetMinutes * 60)
        val now = LocalDateTime.ofInstant(Instant.ofEpochSecond(nowUtc), offset)
        for (dayAhead in 0..7) {
            val day = now.toLocalDate().plusDays(dayAhead.toLong())
            val candidate = day.atTime(config.hour, config.minute)
            if (candidate.isAfter(now) && config.isOnDay(day.dayOfWeek.value)) {
                return candidate.toEpochSecond(offset)
            }
        }
        return null
    }

    /** UTC seconds of the most recent alarm time at or before [nowUtc] (ignores the days mask). */
    fun previousAlarmUtc(config: AlarmConfig, nowUtc: Long, offsetMinutes: Int): Long {
        val offset = ZoneOffset.ofTotalSeconds(offsetMinutes * 60)
        val now = LocalDateTime.ofInstant(Instant.ofEpochSecond(nowUtc), offset)
        var candidate = now.toLocalDate().atTime(config.hour, config.minute)
        if (candidate.isAfter(now)) candidate = candidate.minusDays(1)
        return candidate.toEpochSecond(offset)
    }

    data class WakeDecision(val utc: Long, val reason: WakeReason)

    /**
     * Decides when the band would have woken you, given a night of epochs and the alarm time,
     * using the firmware's rule: the first epoch in the window where 2 of the last 3 window epochs
     * reach the night's threshold; otherwise the alarm time.
     */
    fun decideWake(epochs: List<Epoch>, alarmUtc: Long, config: AlarmConfig): WakeDecision {
        if (!config.smartWake || config.windowMinutes == 0) return WakeDecision(alarmUtc, WakeReason.EXACT_ALARM)
        val windowStart = alarmUtc - config.windowMinutes * 60L
        val activity = epochs.map { it.activity }
        val thresholds = SleepScorer.thresholds(activity)
        val firstInWindow = epochs.indexOfFirst { it.utc >= windowStart }
        if (firstInWindow < 0) return WakeDecision(alarmUtc, WakeReason.WINDOW_ENDED)
        for (i in firstInWindow until epochs.size) {
            if (epochs[i].utc >= alarmUtc) break
            if (SleepScorer.isLight(activity, i, thresholds[i], firstAllowed = firstInWindow)) {
                return WakeDecision(epochs[i].utc + SleepScorer.EPOCH_SECONDS, WakeReason.LIGHT_SLEEP)
            }
        }
        return WakeDecision(alarmUtc, WakeReason.WINDOW_ENDED)
    }
}
