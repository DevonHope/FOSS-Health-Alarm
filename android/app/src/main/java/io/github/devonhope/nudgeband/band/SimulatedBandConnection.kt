package io.github.devonhope.nudgeband.band

import io.github.devonhope.nudgeband.protocol.AlarmConfig
import io.github.devonhope.nudgeband.protocol.AlarmSchedule
import io.github.devonhope.nudgeband.protocol.BandStatus
import io.github.devonhope.nudgeband.protocol.ControlCommand
import io.github.devonhope.nudgeband.protocol.ControlResponse
import io.github.devonhope.nudgeband.protocol.ControlResult
import io.github.devonhope.nudgeband.protocol.LogAssembler
import io.github.devonhope.nudgeband.protocol.MockBand
import io.github.devonhope.nudgeband.protocol.NudgeUuids
import io.github.devonhope.nudgeband.protocol.SleepLog
import io.github.devonhope.nudgeband.protocol.TimeSync
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.util.TimeZone
import java.util.UUID

/**
 * Talks to [MockBand] through the same byte-level protocol as the real band, with small delays,
 * so every screen can be tried before hardware exists.
 */
class SimulatedBandConnection : BandConnection {
    val band = MockBand()

    override val isSimulated = true
    private val _link = MutableStateFlow<LinkState>(LinkState.Disconnected)
    override val link: StateFlow<LinkState> = _link
    private val _found = MutableStateFlow<List<FoundBand>>(emptyList())
    override val found: StateFlow<List<FoundBand>> = _found
    private val _status = MutableStateFlow<BandStatus?>(null)
    override val status: StateFlow<BandStatus?> = _status
    private val _alarm = MutableStateFlow<AlarmConfig?>(null)
    override val alarm: StateFlow<AlarmConfig?> = _alarm

    /** True while the simulated motor is "running". */
    val buzzing = MutableStateFlow(false)

    private var pendingControl: CompletableDeferred<ControlResponse>? = null
    private var assembler: LogAssembler? = null

    init {
        band.mtu = NudgeUuids.PREFERRED_MTU
        band.onNotify = { uuid, value -> onNotify(uuid, value) }
        band.onBuzz = { _, _ -> buzzing.value = true }
    }

    private fun onNotify(uuid: UUID, value: ByteArray) {
        if (_link.value !is LinkState.Connected) return
        when (uuid) {
            NudgeUuids.STATUS -> _status.value = BandStatus.decode(value)
            NudgeUuids.CONTROL -> pendingControl?.complete(ControlResponse.decode(value))
            NudgeUuids.LOG -> assembler?.add(value)
        }
    }

    override fun startScan() {
        _link.value = LinkState.Scanning
        _found.value = listOf(FoundBand(SIM_NAME, SIM_ADDRESS, -48))
    }

    override fun stopScan() {
        if (_link.value == LinkState.Scanning) _link.value = LinkState.Disconnected
    }

    override suspend fun connect(band: FoundBand) {
        _link.value = LinkState.Connecting(band.name)
        delay(600)
        _link.value = LinkState.Connected(band.name, band.address)
        val now = System.currentTimeMillis()
        val offset = TimeZone.getDefault().getOffset(now) / 60_000
        this.band.write(NudgeUuids.TIME, TimeSync(now / 1000, offset).encode())
        _alarm.value = AlarmConfig.decode(this.band.read(NudgeUuids.ALARM))
        _status.value = BandStatus.decode(this.band.read(NudgeUuids.STATUS))
    }

    override fun disconnect() {
        _link.value = LinkState.Disconnected
        _status.value = null
        _alarm.value = null
    }

    override suspend fun writeAlarm(config: AlarmConfig) {
        requireConnected()
        delay(200)
        val result = band.write(NudgeUuids.ALARM, config.encode())
        if (result != MockBand.Att.OK) throw BandException("Band refused the alarm (error 0x%02x)".format(result))
        _alarm.value = config
    }

    override suspend fun command(cmd: ControlCommand): ControlResult {
        requireConnected()
        val deferred = CompletableDeferred<ControlResponse>()
        pendingControl = deferred
        delay(150)
        band.write(NudgeUuids.CONTROL, cmd.encode())
        val result = deferred.await().result
        pendingControl = null
        if (cmd is ControlCommand.TestBuzz && result == ControlResult.OK) {
            delay(cmd.seconds * 1000L)
            buzzing.value = false
        }
        return result
    }

    override suspend fun downloadLog(fromUtc: Long): SleepLog {
        requireConnected()
        val asm = LogAssembler()
        assembler = asm
        try {
            val result = command(ControlCommand.LogRead(fromUtc))
            if (result != ControlResult.OK) throw BandException("Band said: ${result.label}")
            delay(400)
            if (!asm.finished) throw BandException("Log transfer did not finish")
            return asm.result()
        } finally {
            assembler = null
        }
    }

    /** Simulator only: pretend you slept with the band last night. */
    fun simulateNight(): AlarmSchedule.WakeDecision = band.simulateNight()

    fun toggleDock() = band.setDocked(!band.docked)

    private fun requireConnected() {
        if (_link.value !is LinkState.Connected) throw BandException("Not connected")
    }

    override fun close() = disconnect()

    companion object {
        const val SIM_NAME = "NudgeBand-SIM1"
        const val SIM_ADDRESS = "00:00:00:00:51:41"
    }
}
