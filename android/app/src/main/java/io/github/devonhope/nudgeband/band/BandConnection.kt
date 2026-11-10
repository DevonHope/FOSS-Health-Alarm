package io.github.devonhope.nudgeband.band

import io.github.devonhope.nudgeband.protocol.AlarmConfig
import io.github.devonhope.nudgeband.protocol.BandStatus
import io.github.devonhope.nudgeband.protocol.ControlCommand
import io.github.devonhope.nudgeband.protocol.ControlResult
import io.github.devonhope.nudgeband.protocol.SleepLog
import kotlinx.coroutines.flow.StateFlow

sealed interface LinkState {
    data object Disconnected : LinkState
    data object Scanning : LinkState
    data class Connecting(val name: String) : LinkState
    data class Connected(val name: String, val address: String) : LinkState
    data class Failed(val message: String) : LinkState
}

data class FoundBand(val name: String, val address: String, val rssi: Int)

/**
 * One way of talking to a band: over Bluetooth ([BleBandConnection]) or to the simulated band
 * ([SimulatedBandConnection]). Both follow docs/ble-protocol.md.
 */
interface BandConnection {
    val isSimulated: Boolean
    val link: StateFlow<LinkState>
    val found: StateFlow<List<FoundBand>>
    val status: StateFlow<BandStatus?>
    val alarm: StateFlow<AlarmConfig?>

    fun startScan()
    fun stopScan()

    /** Connects, sets the band's clock, and reads its alarm and status. */
    suspend fun connect(band: FoundBand)
    fun disconnect()

    suspend fun writeAlarm(config: AlarmConfig)
    suspend fun command(cmd: ControlCommand): ControlResult

    /** Asks for the movement log from [fromUtc] (0 = everything) and waits for all of it. */
    suspend fun downloadLog(fromUtc: Long = 0): SleepLog

    fun close()
}

class BandException(message: String) : Exception(message)
