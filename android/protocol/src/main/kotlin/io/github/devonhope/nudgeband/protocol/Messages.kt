package io.github.devonhope.nudgeband.protocol

/** Time characteristic (0x0002): UTC seconds plus the phone's UTC offset. */
data class TimeSync(val utcSeconds: Long, val utcOffsetMinutes: Int) {
    fun encode(): ByteArray = ByteWriter(SIZE).u32(utcSeconds).i16(utcOffsetMinutes).u16(0).bytes

    companion object {
        const val SIZE = 8
        fun decode(b: ByteArray): TimeSync {
            requireSize(b, SIZE, "Time")
            val r = ByteReader(b)
            return TimeSync(r.u32(), r.i16())
        }
    }
}

enum class VibrationPattern(val id: Int, val label: String) {
    SOFT_RAMP(0, "Soft ramp"),
    SLOW_PULSES(1, "Slow pulses"),
    HEARTBEAT(2, "Heartbeat");

    companion object {
        fun fromId(id: Int) = entries.firstOrNull { it.id == id } ?: SOFT_RAMP
    }
}

/**
 * Alarm config characteristic (0x0003).
 * [days] uses bit 0 = Monday ... bit 6 = Sunday; 0 means one-off (next occurrence only).
 */
data class AlarmConfig(
    val enabled: Boolean = false,
    val smartWake: Boolean = true,
    val days: Int = 0b0011111,
    val hour: Int = 7,
    val minute: Int = 0,
    val windowMinutes: Int = 30,
    val intensity: Int = 150,
    val pattern: VibrationPattern = VibrationPattern.SOFT_RAMP,
    val rampSeconds: Int = 20,
    val buzzSeconds: Int = 30,
    val repeatMinutes: Int = 2,
    val maxRepeats: Int = 5,
) {
    /** Returns a list of problems; empty means the band will accept it. */
    fun validate(): List<String> = buildList {
        if (days !in 0..0x7F) add("days must be a 7-bit mask")
        if (hour !in 0..23) add("hour must be 0-23")
        if (minute !in 0..59) add("minute must be 0-59")
        if (windowMinutes !in 0..60) add("window must be 0-60 minutes")
        if (intensity !in 0..255) add("intensity must be 0-255")
        if (rampSeconds !in 0..60) add("ramp must be 0-60 s")
        if (buzzSeconds !in 5..120) add("buzz must be 5-120 s")
        if (repeatMinutes !in 0..60) add("repeat must be 0-60 minutes")
        if (maxRepeats !in 0..10) add("max repeats must be 0-10")
    }

    fun encode(): ByteArray {
        val problems = validate()
        require(problems.isEmpty()) { problems.joinToString() }
        val flags = (if (enabled) 1 else 0) or (if (smartWake) 2 else 0)
        return ByteWriter(SIZE)
            .u8(VERSION).u8(flags).u8(days).u8(hour).u8(minute).u8(windowMinutes)
            .u8(intensity).u8(pattern.id).u8(rampSeconds).u8(buzzSeconds)
            .u8(repeatMinutes).u8(maxRepeats).bytes
    }

    fun isOnDay(dayOfWeekMondayIs1: Int): Boolean =
        days == 0 || (days shr (dayOfWeekMondayIs1 - 1)) and 1 == 1

    companion object {
        const val SIZE = 12
        const val VERSION = 1

        fun decode(b: ByteArray): AlarmConfig {
            requireSize(b, SIZE, "Alarm config")
            val r = ByteReader(b)
            val version = r.u8()
            if (version != VERSION) throw ProtocolException("unknown alarm config version $version")
            val flags = r.u8()
            return AlarmConfig(
                enabled = flags and 1 != 0,
                smartWake = flags and 2 != 0,
                days = r.u8(), hour = r.u8(), minute = r.u8(), windowMinutes = r.u8(),
                intensity = r.u8(), pattern = VibrationPattern.fromId(r.u8()),
                rampSeconds = r.u8(), buzzSeconds = r.u8(),
                repeatMinutes = r.u8(), maxRepeats = r.u8(),
            )
        }
    }
}

enum class BandState(val code: Int, val label: String) {
    IDLE(0, "Idle"),
    TRACKING(1, "Tracking sleep"),
    IN_WINDOW(2, "In wake window"),
    WAKING(3, "Waking you"),
    WAITING_TO_REPEAT(4, "Waiting to buzz again");

    companion object {
        fun fromCode(c: Int) = entries.firstOrNull { it.code == c } ?: IDLE
    }
}

enum class WakeReason(val code: Int, val label: String) {
    NONE(0, "None"),
    LIGHT_SLEEP(1, "Light sleep"),
    WINDOW_ENDED(2, "Window ended"),
    TEST_BUZZ(3, "Test buzz"),
    EXACT_ALARM(4, "Exact alarm");

    companion object {
        fun fromCode(c: Int) = entries.firstOrNull { it.code == c } ?: NONE
    }
}

/** Status characteristic (0x0004). */
data class BandStatus(
    val state: BandState = BandState.IDLE,
    val batteryPercent: Int = 0,
    val docked: Boolean = false,
    val charging: Boolean = false,
    val timeSet: Boolean = false,
    val alarmArmed: Boolean = false,
    val logHasData: Boolean = false,
    val nextAlarmUtc: Long = 0,
    val firmwareMajor: Int = 0,
    val firmwareMinor: Int = 0,
    val lastWakeReason: WakeReason = WakeReason.NONE,
    val lastWakeUtc: Long = 0,
    val storedEpochs: Int = 0,
) {
    val firmwareVersion get() = "$firmwareMajor.$firmwareMinor"

    fun encode(): ByteArray {
        val flags = (if (docked) 1 else 0) or (if (charging) 2 else 0) or
            (if (timeSet) 4 else 0) or (if (alarmArmed) 8 else 0) or (if (logHasData) 16 else 0)
        return ByteWriter(SIZE)
            .u8(VERSION).u8(state.code).u8(batteryPercent).u8(flags)
            .u32(nextAlarmUtc).u8(firmwareMajor).u8(firmwareMinor)
            .u8(lastWakeReason.code).u8(0).u32(lastWakeUtc).u16(storedEpochs).bytes
    }

    companion object {
        const val SIZE = 18
        const val VERSION = 1

        fun decode(b: ByteArray): BandStatus {
            requireSize(b, SIZE, "Status")
            val r = ByteReader(b)
            val version = r.u8()
            if (version != VERSION) throw ProtocolException("unknown status version $version")
            val state = BandState.fromCode(r.u8())
            val battery = r.u8()
            val flags = r.u8()
            val next = r.u32()
            val major = r.u8()
            val minor = r.u8()
            val reason = WakeReason.fromCode(r.u8())
            r.u8()
            return BandStatus(
                state = state, batteryPercent = battery,
                docked = flags and 1 != 0, charging = flags and 2 != 0,
                timeSet = flags and 4 != 0, alarmArmed = flags and 8 != 0,
                logHasData = flags and 16 != 0,
                nextAlarmUtc = next, firmwareMajor = major, firmwareMinor = minor,
                lastWakeReason = reason, lastWakeUtc = r.u32(), storedEpochs = r.u16(),
            )
        }
    }
}

/** Commands written to the control point (0x0005). */
sealed class ControlCommand(val opcode: Int) {
    data class TestBuzz(val intensity: Int, val seconds: Int) : ControlCommand(OP_TEST_BUZZ)
    data object StopBuzz : ControlCommand(OP_STOP_BUZZ)
    data class LogRead(val fromUtc: Long = 0) : ControlCommand(OP_LOG_READ)
    data object LogClear : ControlCommand(OP_LOG_CLEAR)
    data object Dismiss : ControlCommand(OP_DISMISS)
    data object Identify : ControlCommand(OP_IDENTIFY)

    fun encode(): ByteArray = when (this) {
        is TestBuzz -> ByteWriter(3).u8(opcode).u8(intensity).u8(seconds).bytes
        is LogRead -> ByteWriter(5).u8(opcode).u32(fromUtc).bytes
        else -> byteArrayOf(opcode.toByte())
    }

    companion object {
        const val OP_TEST_BUZZ = 0x01
        const val OP_STOP_BUZZ = 0x02
        const val OP_LOG_READ = 0x03
        const val OP_LOG_CLEAR = 0x04
        const val OP_DISMISS = 0x05
        const val OP_IDENTIFY = 0x06

        fun decode(b: ByteArray): ControlCommand {
            requireSize(b, 1, "Control command")
            val r = ByteReader(b)
            return when (val op = r.u8()) {
                OP_TEST_BUZZ -> TestBuzz(r.u8(), r.u8())
                OP_STOP_BUZZ -> StopBuzz
                OP_LOG_READ -> LogRead(r.u32())
                OP_LOG_CLEAR -> LogClear
                OP_DISMISS -> Dismiss
                OP_IDENTIFY -> Identify
                else -> throw ProtocolException("unknown opcode $op")
            }
        }
    }
}

enum class ControlResult(val code: Int, val label: String) {
    OK(0, "OK"),
    UNSUPPORTED(1, "Not supported by this firmware"),
    INVALID_PARAMETER(2, "Invalid parameter"),
    BUSY(3, "Band is busy"),
    NOT_READY(4, "Band is not ready");

    companion object {
        fun fromCode(c: Int) = entries.firstOrNull { it.code == c } ?: UNSUPPORTED
    }
}

/** Indication sent back on the control point: 0x80, request opcode, result. */
data class ControlResponse(val requestOpcode: Int, val result: ControlResult) {
    fun encode(): ByteArray = byteArrayOf(0x80.toByte(), requestOpcode.toByte(), result.code.toByte())

    companion object {
        fun decode(b: ByteArray): ControlResponse {
            requireSize(b, 3, "Control response")
            val r = ByteReader(b)
            val marker = r.u8()
            if (marker != 0x80) throw ProtocolException("not a control response (0x${marker.toString(16)})")
            return ControlResponse(r.u8(), ControlResult.fromCode(r.u8()))
        }
    }
}
