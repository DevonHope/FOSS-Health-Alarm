package io.github.devonhope.nudgeband.protocol

import kotlin.test.Test
import kotlin.test.assertEquals

class ScorerTest {
    @Test fun thresholdIs300DuringWarmUpThenTracksMedian() {
        val quiet = List(19) { 50 }
        assertEquals(300, SleepScorer.thresholds(quiet).last())
        // Median 200 after warm-up -> 3 x 200 = 600.
        val busier = List(40) { 200 }
        assertEquals(600, SleepScorer.thresholds(busier).last())
        // No-data epochs don't count toward the median or the warm-up.
        val gaps = List(30) { if (it % 2 == 0) LogPacket.NO_DATA else 500 }
        assertEquals(300, SleepScorer.thresholds(gaps).last())
    }

    @Test fun lightNeedsTwoOfLastThreeInsideWindow() {
        val epochs = (0 until 100).map { Epoch(it * 30L, 40) }.toMutableList()
        val alarm = 100 * 30L
        val cfg = AlarmConfig(enabled = true, windowMinutes = 30) // window = epochs 40..99
        // One big epoch just before the window and one inside: must not count (only 1 inside).
        epochs[39] = epochs[39].copy(activity = 900)
        epochs[40] = epochs[40].copy(activity = 900)
        assertEquals(WakeReason.WINDOW_ENDED, AlarmSchedule.decideWake(epochs, alarm, cfg).reason)
        // Two of three inside the window: wake after epoch 52.
        epochs[50] = epochs[50].copy(activity = 900)
        epochs[52] = epochs[52].copy(activity = 900)
        val d = AlarmSchedule.decideWake(epochs, alarm, cfg)
        assertEquals(WakeReason.LIGHT_SLEEP, d.reason)
        assertEquals(53 * 30L, d.utc)
    }

    @Test fun windowZeroIsExact() {
        val epochs = (0 until 10).map { Epoch(it * 30L, 5000) }
        assertEquals(WakeReason.EXACT_ALARM, AlarmSchedule.decideWake(epochs, 300, AlarmConfig(windowMinutes = 0)).reason)
    }
}
