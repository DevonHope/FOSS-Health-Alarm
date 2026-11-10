package io.github.devonhope.nudgeband.protocol

import java.time.LocalDateTime
import java.time.ZoneOffset
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class MockBandTest {
    // Tuesday 2026-11-10 09:00 local, UTC-5.
    private val offset = -300
    private val now = LocalDateTime.of(2026, 11, 10, 9, 0).toEpochSecond(ZoneOffset.ofHours(-5))

    private fun band(): Pair<MockBand, MutableList<Pair<UUID, ByteArray>>> {
        val b = MockBand(clock = { now })
        val got = mutableListOf<Pair<UUID, ByteArray>>()
        b.onNotify = { u, v -> got += u to v }
        return b to got
    }

    @Test fun nextAlarmSkipsDaysOff() {
        // Weekdays only, 7:00. Now is Tuesday 9:00, so next is Wednesday 7:00.
        val cfg = AlarmConfig(enabled = true, days = 0b0011111, hour = 7, minute = 0)
        val next = AlarmSchedule.nextAlarmUtc(cfg, now, offset)
        assertEquals(LocalDateTime.of(2026, 11, 11, 7, 0).toEpochSecond(ZoneOffset.ofHours(-5)), next)
        // Saturday only: next is 2026-11-14.
        val sat = AlarmSchedule.nextAlarmUtc(cfg.copy(days = 0b0100000), now, offset)
        assertEquals(LocalDateTime.of(2026, 11, 14, 7, 0).toEpochSecond(ZoneOffset.ofHours(-5)), sat)
        assertEquals(null, AlarmSchedule.nextAlarmUtc(cfg.copy(enabled = false), now, offset))
    }

    @Test fun logReadNeedsTime() {
        val (b, got) = band()
        b.write(NudgeUuids.CONTROL, ControlCommand.LogRead().encode())
        assertEquals(ControlResult.NOT_READY, ControlResponse.decode(got.single().second).result)
    }

    @Test fun rejectsBadAlarm() {
        val (b, _) = band()
        val bad = AlarmConfig().encode().also { it[3] = 30 } // hour 30
        assertEquals(MockBand.Att.VALUE_NOT_ALLOWED, b.write(NudgeUuids.ALARM, bad))
    }

    @Test fun simulatedNightWakesInsideWindowAndDownloads() {
        val (b, got) = band()
        b.write(NudgeUuids.TIME, TimeSync(now, offset).encode())
        b.write(NudgeUuids.ALARM, AlarmConfig(enabled = true, hour = 7, minute = 0).encode())
        val status = BandStatus.decode(b.read(NudgeUuids.STATUS))
        assertTrue(status.timeSet && status.alarmArmed)

        val decision = b.simulateNight()
        val alarm = LocalDateTime.of(2026, 11, 10, 7, 0).toEpochSecond(ZoneOffset.ofHours(-5))
        assertTrue(decision.utc in (alarm - 30 * 60)..alarm, "woke outside the window")

        got.clear()
        b.mtu = 185
        b.write(NudgeUuids.CONTROL, ControlCommand.LogRead().encode())
        assertEquals(ControlResult.OK, ControlResponse.decode(got.first().second).result)
        val asm = LogAssembler()
        got.drop(1).forEach { (u, v) -> assertEquals(NudgeUuids.LOG, u); asm.add(v) }
        val log = asm.result()
        val night = log.nights().single()
        val summary = SleepScorer.summarize(night)
        assertTrue(summary.totalMinutes in 420..480, "night was ${summary.totalMinutes} min")
        assertTrue(summary.deepMinutes > 60 && summary.lightMinutes > 60, summary.toString())
        assertNotNull(log.events.firstOrNull { it.kind == LogEventKind.WINDOW_STARTED })
    }

    @Test fun exactAlarmWhenSmartWakeOff() {
        val (b, _) = band()
        b.write(NudgeUuids.TIME, TimeSync(now, offset).encode())
        b.write(NudgeUuids.ALARM, AlarmConfig(enabled = true, smartWake = false).encode())
        assertEquals(WakeReason.EXACT_ALARM, b.simulateNight().reason)
    }

    @Test fun windowEndWhenAlwaysDeep() {
        val epochs = (0 until 200).map { Epoch(it * 30L, 10) }
        val d = AlarmSchedule.decideWake(epochs, 6000, AlarmConfig(enabled = true))
        assertEquals(WakeReason.WINDOW_ENDED, d.reason)
        assertEquals(6000, d.utc)
    }

    @Test fun testBuzzValidatesSeconds() {
        val (b, got) = band()
        var buzzed = 0
        b.onBuzz = { _, s -> buzzed = s }
        b.write(NudgeUuids.CONTROL, ControlCommand.TestBuzz(150, 30).encode())
        assertEquals(ControlResult.INVALID_PARAMETER, ControlResponse.decode(got.last().second).result)
        b.write(NudgeUuids.CONTROL, ControlCommand.TestBuzz(150, 2).encode())
        assertEquals(ControlResult.OK, ControlResponse.decode(got.last().second).result)
        assertEquals(2, buzzed)
    }
}
