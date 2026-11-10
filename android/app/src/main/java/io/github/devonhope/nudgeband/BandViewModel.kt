package io.github.devonhope.nudgeband

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import io.github.devonhope.nudgeband.band.BandConnection
import io.github.devonhope.nudgeband.band.BleBandConnection
import io.github.devonhope.nudgeband.band.FoundBand
import io.github.devonhope.nudgeband.band.SimulatedBandConnection
import io.github.devonhope.nudgeband.data.SleepStore
import io.github.devonhope.nudgeband.protocol.AlarmConfig
import io.github.devonhope.nudgeband.protocol.ControlCommand
import io.github.devonhope.nudgeband.protocol.ControlResult
import io.github.devonhope.nudgeband.protocol.SleepLog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class BandViewModel(app: Application) : AndroidViewModel(app) {
    private val prefs = app.getSharedPreferences("nudgeband", Context.MODE_PRIVATE)
    private val store = SleepStore(File(app.filesDir, "sleep-log.txt"))
    private val simulated = SimulatedBandConnection()
    private val ble by lazy { BleBandConnection(app) }

    private val _useSimulator = MutableStateFlow(prefs.getBoolean(KEY_SIMULATOR, true))
    val useSimulator: StateFlow<Boolean> = _useSimulator

    private val _connection = MutableStateFlow<BandConnection>(if (_useSimulator.value) simulated else ble)
    val connection: StateFlow<BandConnection> = _connection

    /** One-line messages for a snackbar. */
    private val _message = MutableStateFlow<String?>(null)
    val message: StateFlow<String?> = _message

    private val _busy = MutableStateFlow(false)
    val busy: StateFlow<Boolean> = _busy

    private val _history = MutableStateFlow(SleepLog(SleepStore.EPOCH_SECONDS, emptyList(), emptyList()))
    val history: StateFlow<SleepLog> = _history

    val savedBandName: String? get() = prefs.getString(KEY_NAME, null)
    val savedBandAddress: String? get() = prefs.getString(KEY_ADDRESS, null)

    init {
        viewModelScope.launch { _history.value = withContext(Dispatchers.IO) { store.load() } }
    }

    fun setUseSimulator(on: Boolean) {
        if (on == _useSimulator.value) return
        _connection.value.close()
        _useSimulator.value = on
        prefs.edit().putBoolean(KEY_SIMULATOR, on).apply()
        _connection.value = if (on) simulated else ble
    }

    val simulator: SimulatedBandConnection? get() = _connection.value as? SimulatedBandConnection

    fun startScan() = _connection.value.startScan()
    fun stopScan() = _connection.value.stopScan()

    fun connect(band: FoundBand) = run("Connected to ${band.name}") {
        _connection.value.connect(band)
        if (!_connection.value.isSimulated) {
            prefs.edit().putString(KEY_NAME, band.name).putString(KEY_ADDRESS, band.address).apply()
        }
    }

    fun reconnectSaved() {
        val address = savedBandAddress ?: return
        connect(FoundBand(savedBandName ?: "NudgeBand", address, 0))
    }

    fun disconnect() = _connection.value.disconnect()

    fun saveAlarm(config: AlarmConfig) = run("Alarm saved on the band") {
        _connection.value.writeAlarm(config)
    }

    fun testBuzz(intensity: Int) = command(ControlCommand.TestBuzz(intensity, 2), "Buzzing for 2 seconds")
    fun identify() = command(ControlCommand.Identify, "Band LED blinking")
    fun dismiss() = command(ControlCommand.Dismiss, "Alarm dismissed")

    private fun command(cmd: ControlCommand, ok: String) = run(ok) {
        val result = _connection.value.command(cmd)
        if (result != ControlResult.OK) throw IllegalStateException("Band said: ${result.label}")
    }

    fun syncLog() = run(null) {
        val log = _connection.value.downloadLog(0)
        val merged = withContext(Dispatchers.IO) { store.merge(log) }
        _history.value = merged
        _message.value = "Downloaded ${log.epochs.size} epochs (${log.epochs.size / 120} h)"
    }

    fun simulateNight() = run(null) {
        val sim = simulator ?: return@run
        val wake = sim.simulateNight()
        _message.value = "Simulated a night: woke for \"${wake.reason.label}\". Tap Sync to download it."
    }

    fun clearHistory() = viewModelScope.launch {
        withContext(Dispatchers.IO) { store.clear() }
        _history.value = SleepLog(SleepStore.EPOCH_SECONDS, emptyList(), emptyList())
    }

    fun messageShown() {
        _message.value = null
    }

    private fun run(ok: String?, block: suspend () -> Unit) = viewModelScope.launch {
        _busy.value = true
        try {
            block()
            if (ok != null) _message.value = ok
        } catch (e: Exception) {
            _message.value = e.message ?: e.javaClass.simpleName
        } finally {
            _busy.value = false
        }
    }

    override fun onCleared() {
        simulated.close()
        if (!_useSimulator.value) ble.close()
    }

    companion object {
        private const val KEY_SIMULATOR = "use_simulator"
        private const val KEY_NAME = "band_name"
        private const val KEY_ADDRESS = "band_address"
    }
}
