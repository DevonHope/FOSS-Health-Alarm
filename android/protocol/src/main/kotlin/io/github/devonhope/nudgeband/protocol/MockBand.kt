package io.github.devonhope.nudgeband.protocol

import java.util.UUID
import kotlin.math.PI
import kotlin.math.max
import kotlin.math.sin
import kotlin.random.Random

/**
 * A simulated NudgeBand that follows docs/ble-protocol.md, so the app can be built and tried
 * before real hardware exists. It answers reads and writes the way the firmware should, and sends
 * notifications through [onNotify].
 */
class MockBand(
    private val clock: () -> Long = { System.currentTimeMillis() / 1000 },
    val firmwareMajor: Int = 0,
    val firmwareMinor: Int = 1,
    private val random: Random = Random(42),
) {
    /** ATT error codes the band can return on a write. */
    object Att {
        const val OK = 0
        const val WRITE_NOT_PERMITTED = 0x03
        const val INVALID_LENGTH = 0x0D
        const val VALUE_NOT_ALLOWED = 0x13
    }

    /** Called for every notification or indication: characteristic, value. */
    var onNotify: (UUID, ByteArray) -> Unit = { _, _ -> }

    /** Optional hook so the app can show that the motor is running. */
    var onBuzz: (intensity: Int, seconds: Int) -> Unit = { _, _ -> }

    var mtu: Int = 23
    var batteryPercent: Int = 84
        private set
    var docked = false
        private set

    private var time: TimeSync? = null
    private var alarm = AlarmConfig()
    private var state = BandState.IDLE
    private var lastWakeReason = WakeReason.NONE
    private var lastWakeUtc = 0L
    private val epochs = mutableListOf<Epoch>()
    private val events = mutableListOf<LogPacket.Event>()

    private val offsetMinutes get() = time?.utcOffsetMinutes ?: 0

    fun status(): BandStatus = BandStatus(
        state = state,
        batteryPercent = batteryPercent,
        docked = docked,
        charging = docked && batteryPercent < 100,
        timeSet = time != null,
        alarmArmed = alarm.enabled && time != null,
        logHasData = epochs.isNotEmpty(),
        nextAlarmUtc = if (time == null) 0 else AlarmSchedule.nextAlarmUtc(alarm, clock(), offsetMinutes) ?: 0,
        firmwareMajor = firmwareMajor,
        firmwareMinor = firmwareMinor,
        lastWakeReason = lastWakeReason,
        lastWakeUtc = lastWakeUtc,
        storedEpochs = epochs.size,
    )

    fun read(uuid: UUID): ByteArray = when (uuid) {
        NudgeUuids.TIME -> (time ?: TimeSync(0, 0)).encode()
        NudgeUuids.ALARM -> alarm.encode()
        NudgeUuids.STATUS -> status().encode()
        NudgeUuids.BATTERY_LEVEL -> byteArrayOf(batteryPercent.toByte())
        NudgeUuids.FIRMWARE_REVISION -> "$firmwareMajor.$firmwareMinor-sim".toByteArray()
        else -> throw IllegalArgumentException("not readable: $uuid")
    }

    /** Returns an ATT result code; [Att.OK] on success. */
    fun write(uuid: UUID, value: ByteArray): Int = when (uuid) {
        NudgeUuids.TIME -> {
            if (value.size != TimeSync.SIZE) Att.INVALID_LENGTH
            else {
                time = TimeSync.decode(value)
                notifyStatus(); Att.OK
            }
        }
        NudgeUuids.ALARM -> {
            if (value.size != AlarmConfig.SIZE) Att.INVALID_LENGTH
            else {
                val cfg = runCatching { AlarmConfig.decode(value) }.getOrNull()
                if (cfg == null || cfg.validate().isNotEmpty()) Att.VALUE_NOT_ALLOWED
                else {
                    alarm = cfg
                    notifyStatus(); Att.OK
                }
            }
        }
        NudgeUuids.CONTROL -> {
            val cmd = runCatching { ControlCommand.decode(value) }.getOrNull()
            if (cmd == null) {
                val op = value.firstOrNull()?.toInt()?.and(0xFF) ?: 0
                indicate(ControlResponse(op, ControlResult.UNSUPPORTED))
            } else handle(cmd)
            Att.OK
        }
        else -> Att.WRITE_NOT_PERMITTED
    }

    private fun handle(cmd: ControlCommand) {
        when (cmd) {
            is ControlCommand.TestBuzz -> {
                if (cmd.seconds !in 1..10 || cmd.intensity !in 0..255) {
                    indicate(ControlResponse(cmd.opcode, ControlResult.INVALID_PARAMETER)); return
                }
                indicate(ControlResponse(cmd.opcode, ControlResult.OK))
                onBuzz(cmd.intensity, cmd.seconds)
            }
            ControlCommand.StopBuzz, ControlCommand.Identify -> indicate(ControlResponse(cmd.opcode, ControlResult.OK))
            ControlCommand.Dismiss -> {
                if (state == BandState.WAKING || state == BandState.WAITING_TO_REPEAT) {
                    events += LogPacket.Event(0, clock(), LogEventKind.DISMISSED)
                    state = BandState.IDLE
                    notifyStatus()
                }
                indicate(ControlResponse(cmd.opcode, ControlResult.OK))
            }
            ControlCommand.LogClear -> {
                epochs.clear(); events.clear()
                indicate(ControlResponse(cmd.opcode, ControlResult.OK))
                notifyStatus()
            }
            is ControlCommand.LogRead -> {
                if (time == null) {
                    indicate(ControlResponse(cmd.opcode, ControlResult.NOT_READY)); return
                }
                indicate(ControlResponse(cmd.opcode, ControlResult.OK))
                val log = SleepLog(
                    SleepScorer.EPOCH_SECONDS,
                    epochs.filter { it.utc >= cmd.fromUtc },
                    events.filter { it.utc >= cmd.fromUtc },
                )
                encodeLog(log, mtu).forEach { onNotify(NudgeUuids.LOG, it) }
            }
        }
    }

    private fun indicate(r: ControlResponse) = onNotify(NudgeUuids.CONTROL, r.encode())
    private fun notifyStatus() = onNotify(NudgeUuids.STATUS, status().encode())

    fun setDocked(value: Boolean) {
        if (value == docked) return
        docked = value
        events += LogPacket.Event(0, clock(), if (value) LogEventKind.DOCKED else LogEventKind.UNDOCKED)
        notifyStatus()
    }

    /**
     * Pretends the band was worn last night: fills the log with a made-up night that ends at the
     * most recent alarm time, and runs the smart-wake rule over it, as the firmware would.
     */
    fun simulateNight(hours: Double = 7.5): AlarmSchedule.WakeDecision {
        val alarmUtc = AlarmSchedule.previousAlarmUtc(alarm, clock(), offsetMinutes)
        val epochSeconds = SleepScorer.EPOCH_SECONDS
        val start = alarmUtc - (hours * 3600).toLong()
        val night = mutableListOf<Epoch>()
        var t = start
        // Phase offset so different nights differ.
        val phase = random.nextDouble(0.0, 2 * PI)
        while (t < alarmUtc + 15 * 60) {
            night += Epoch(t, fakeActivity((t - start) / 60.0, phase))
            t += epochSeconds
        }
        val decision = AlarmSchedule.decideWake(night, alarmUtc, alarm)
        // After waking you get up: a few minutes of big movement, then the band is taken off.
        val kept = night.filter { it.utc < decision.utc }.toMutableList()
        var after = decision.utc - (decision.utc - start) % epochSeconds
        repeat(6) {
            kept += Epoch(after, 4000 + random.nextInt(4000)); after += epochSeconds
        }
        epochs.removeAll { it.utc >= start }
        epochs += kept
        val windowStart = alarmUtc - alarm.windowMinutes * 60L
        events += LogPacket.Event(0, windowStart, LogEventKind.WINDOW_STARTED)
        events += LogPacket.Event(
            0, decision.utc,
            when (decision.reason) {
                WakeReason.LIGHT_SLEEP -> LogEventKind.WOKE_LIGHT_SLEEP
                WakeReason.EXACT_ALARM -> LogEventKind.EXACT_ALARM
                else -> LogEventKind.WOKE_WINDOW_END
            },
        )
        events += LogPacket.Event(0, decision.utc + 60, LogEventKind.DISMISSED)
        lastWakeReason = decision.reason
        lastWakeUtc = decision.utc
        batteryPercent = max(2, batteryPercent - 2)
        notifyStatus()
        return decision
    }

    /** Roughly 90-minute sleep cycles: still in deep sleep, restless in light sleep. */
    private fun fakeActivity(minutes: Double, phase: Double): Int {
        val cycle = sin(2 * PI * minutes / 90.0 + phase) // -1 deep ... +1 light
        val base = if (cycle > 0.3) 150 + 500 * cycle else 20 + 40 * (cycle + 1)
        val spikeChance = if (cycle > 0.3) 0.12 else 0.01
        val spike = if (random.nextDouble() < spikeChance) 1200 + random.nextInt(2000) else 0
        val settling = if (minutes < 15) 2500 * (1 - minutes / 15) else 0.0
        return (base + spike + settling + random.nextInt(30)).toInt().coerceIn(0, 65534)
    }
}
