package io.github.devonhope.nudgeband.protocol

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class ProtocolTest {
    @Test fun timeRoundTripsAndIsLittleEndian() {
        val t = TimeSync(0x11223344, -300)
        val b = t.encode()
        assertContentEquals(byteArrayOf(0x44, 0x33, 0x22, 0x11, 0xD4.toByte(), 0xFE.toByte(), 0, 0), b)
        assertEquals(t, TimeSync.decode(b))
    }

    @Test fun alarmRoundTrips() {
        val a = AlarmConfig(enabled = true, smartWake = false, days = 0b1000001, hour = 6, minute = 45,
            windowMinutes = 20, intensity = 255, pattern = VibrationPattern.HEARTBEAT)
        val b = a.encode()
        assertEquals(AlarmConfig.SIZE, b.size)
        assertEquals(1, b[0].toInt()) // version
        assertEquals(1, b[1].toInt()) // enabled, not smart
        assertEquals(a, AlarmConfig.decode(b))
    }

    @Test fun alarmRejectsBadValues() {
        assertTrue(AlarmConfig(hour = 24).validate().isNotEmpty())
        assertTrue(AlarmConfig(windowMinutes = 61).validate().isNotEmpty())
        assertFailsWith<IllegalArgumentException> { AlarmConfig(minute = 60).encode() }
    }

    @Test fun statusRoundTrips() {
        val s = BandStatus(BandState.IN_WINDOW, 62, docked = false, charging = false, timeSet = true,
            alarmArmed = true, logHasData = true, nextAlarmUtc = 1_800_000_000, firmwareMajor = 1,
            firmwareMinor = 2, lastWakeReason = WakeReason.LIGHT_SLEEP, lastWakeUtc = 1_799_990_000,
            storedEpochs = 960)
        val b = s.encode()
        assertEquals(BandStatus.SIZE, b.size)
        assertEquals(s, BandStatus.decode(b))
    }

    @Test fun controlRoundTrips() {
        listOf(ControlCommand.TestBuzz(200, 3), ControlCommand.StopBuzz, ControlCommand.LogRead(1234),
            ControlCommand.LogClear, ControlCommand.Dismiss, ControlCommand.Identify).forEach {
            assertEquals(it, ControlCommand.decode(it.encode()))
        }
        val r = ControlResponse(3, ControlResult.BUSY)
        assertEquals(r, ControlResponse.decode(r.encode()))
    }

    @Test fun shortPacketsThrow() {
        assertFailsWith<ProtocolException> { BandStatus.decode(ByteArray(5)) }
        assertFailsWith<ProtocolException> { LogPacket.decode(byteArrayOf(1, 0, 0, 0, 0, 0, 0, 30, 4, 1)) }
    }

    @Test fun logSurvivesSmallAndLargeMtu() {
        val epochs = (0 until 960).map { Epoch(1_000_000L + it * 30, it % 700) } +
            Epoch(1_000_000L + 2000 * 30, LogPacket.NO_DATA)
        val log = SleepLog(30, epochs, listOf(LogPacket.Event(0, 1_000_100, LogEventKind.WINDOW_STARTED)))
        for (mtu in listOf(23, 247)) {
            val packets = encodeLog(log, mtu)
            packets.forEach { assertTrue(it.size <= mtu - 3, "packet ${it.size} > ${mtu - 3}") }
            val asm = LogAssembler()
            packets.forEachIndexed { i, p -> assertEquals(i == packets.lastIndex, asm.add(p)) }
            val back = asm.result()
            assertEquals(epochs, back.epochs)
            assertEquals(LogEventKind.WINDOW_STARTED, back.events.single().kind)
        }
        assertEquals(5, LogPacket.epochsPerPacket(23))
    }

    @Test fun assemblerSpotsMissingPacket() {
        val log = SleepLog(30, (0 until 50).map { Epoch(it * 30L, 5) }, emptyList())
        val packets = encodeLog(log, 23)
        val asm = LogAssembler()
        asm.add(packets[0])
        assertFailsWith<ProtocolException> { asm.add(packets[2]) }
    }
}
