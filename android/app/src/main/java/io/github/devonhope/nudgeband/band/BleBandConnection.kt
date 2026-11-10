package io.github.devonhope.nudgeband.band

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.BluetoothStatusCodes
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.Build
import android.os.ParcelUuid
import io.github.devonhope.nudgeband.protocol.AlarmConfig
import io.github.devonhope.nudgeband.protocol.BandStatus
import io.github.devonhope.nudgeband.protocol.ControlCommand
import io.github.devonhope.nudgeband.protocol.ControlResponse
import io.github.devonhope.nudgeband.protocol.ControlResult
import io.github.devonhope.nudgeband.protocol.LogAssembler
import io.github.devonhope.nudgeband.protocol.NudgeUuids
import io.github.devonhope.nudgeband.protocol.SleepLog
import io.github.devonhope.nudgeband.protocol.TimeSync
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withTimeout
import java.util.TimeZone
import java.util.UUID

/**
 * Real Bluetooth LE link to a NudgeBand, following docs/ble-protocol.md.
 *
 * Android allows one GATT operation at a time, so every read/write goes through [op], which holds
 * a mutex and waits for the matching callback.
 *
 * Permissions (BLUETOOTH_SCAN / BLUETOOTH_CONNECT, or location on Android 11 and older) are
 * checked by the UI before any call here.
 */
@SuppressLint("MissingPermission")
class BleBandConnection(private val context: Context) : BandConnection {
    override val isSimulated = false
    private val _link = MutableStateFlow<LinkState>(LinkState.Disconnected)
    override val link: StateFlow<LinkState> = _link
    private val _found = MutableStateFlow<List<FoundBand>>(emptyList())
    override val found: StateFlow<List<FoundBand>> = _found
    private val _status = MutableStateFlow<BandStatus?>(null)
    override val status: StateFlow<BandStatus?> = _status
    private val _alarm = MutableStateFlow<AlarmConfig?>(null)
    override val alarm: StateFlow<AlarmConfig?> = _alarm

    private val manager = context.getSystemService(BluetoothManager::class.java)
    private val adapter get() = manager?.adapter

    private var gatt: BluetoothGatt? = null
    private val opLock = Mutex()
    private var pendingOp: CompletableDeferred<Any>? = null
    private var connectWait: CompletableDeferred<Unit>? = null
    private var pendingControl: CompletableDeferred<ControlResponse>? = null
    private var assembler: LogAssembler? = null
    private var logDone: CompletableDeferred<Unit>? = null
    private var mtu = 23

    // ---- Scanning ----

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val name = result.scanRecord?.deviceName ?: result.device.name ?: return
            if (!name.startsWith(NudgeUuids.NAME_PREFIX)) return
            val band = FoundBand(name, result.device.address, result.rssi)
            _found.value = (_found.value.filter { it.address != band.address } + band).sortedByDescending { it.rssi }
        }

        override fun onScanFailed(errorCode: Int) {
            _link.value = LinkState.Failed("Bluetooth scan failed (code $errorCode)")
        }
    }

    override fun startScan() {
        val scanner = adapter?.bluetoothLeScanner
        if (adapter?.isEnabled != true || scanner == null) {
            _link.value = LinkState.Failed("Bluetooth is off")
            return
        }
        _found.value = emptyList()
        _link.value = LinkState.Scanning
        val filters = listOf(ScanFilter.Builder().setServiceUuid(ParcelUuid(NudgeUuids.SERVICE)).build())
        val settings = ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build()
        scanner.startScan(filters, settings, scanCallback)
    }

    override fun stopScan() {
        runCatching { adapter?.bluetoothLeScanner?.stopScan(scanCallback) }
        if (_link.value == LinkState.Scanning) _link.value = LinkState.Disconnected
    }

    // ---- Connection ----

    override suspend fun connect(band: FoundBand) {
        stopScan()
        val device: BluetoothDevice = adapter?.getRemoteDevice(band.address)
            ?: throw BandException("Bluetooth is not available")
        _link.value = LinkState.Connecting(band.name)
        val wait = CompletableDeferred<Unit>()
        connectWait = wait
        gatt = device.connectGatt(context, false, callback, BluetoothDevice.TRANSPORT_LE)
        try {
            withTimeout(20_000) { wait.await() }
            setUp()
            _link.value = LinkState.Connected(band.name, band.address)
        } catch (e: Exception) {
            closeGatt()
            val message = if (e is TimeoutCancellationException) "Band did not answer" else (e.message ?: "Connect failed")
            _link.value = LinkState.Failed(message)
            throw BandException(message)
        } finally {
            connectWait = null
        }
    }

    /** After services are found: bigger MTU, turn on notifications, set the clock, read state. */
    private suspend fun setUp() {
        val g = gatt ?: throw BandException("Not connected")
        mtu = runCatching { op { g.requestMtu(NudgeUuids.PREFERRED_MTU) } as Int }.getOrDefault(23)
        enableNotify(NudgeUuids.STATUS, indicate = false)
        enableNotify(NudgeUuids.CONTROL, indicate = true)
        enableNotify(NudgeUuids.LOG, indicate = false)
        val now = System.currentTimeMillis()
        val offset = TimeZone.getDefault().getOffset(now) / 60_000
        write(NudgeUuids.TIME, TimeSync(now / 1000, offset).encode())
        _alarm.value = AlarmConfig.decode(read(NudgeUuids.ALARM))
        _status.value = BandStatus.decode(read(NudgeUuids.STATUS))
    }

    override fun disconnect() {
        closeGatt()
        _link.value = LinkState.Disconnected
    }

    private fun closeGatt() {
        gatt?.let { runCatching { it.disconnect(); it.close() } }
        gatt = null
        _status.value = null
        _alarm.value = null
        pendingOp?.completeExceptionally(BandException("Disconnected"))
        pendingControl?.completeExceptionally(BandException("Disconnected"))
        logDone?.completeExceptionally(BandException("Disconnected"))
    }

    override fun close() {
        stopScan()
        disconnect()
    }

    // ---- Commands ----

    override suspend fun writeAlarm(config: AlarmConfig) {
        write(NudgeUuids.ALARM, config.encode())
        _alarm.value = config
    }

    override suspend fun command(cmd: ControlCommand): ControlResult {
        val deferred = CompletableDeferred<ControlResponse>()
        pendingControl = deferred
        try {
            write(NudgeUuids.CONTROL, cmd.encode())
            val response = withTimeout(5_000) { deferred.await() }
            if (response.requestOpcode != cmd.opcode) throw BandException("Band answered a different command")
            return response.result
        } finally {
            pendingControl = null
        }
    }

    override suspend fun downloadLog(fromUtc: Long): SleepLog {
        val asm = LogAssembler()
        val done = CompletableDeferred<Unit>()
        assembler = asm
        logDone = done
        try {
            val result = command(ControlCommand.LogRead(fromUtc))
            if (result != ControlResult.OK) throw BandException("Band said: ${result.label}")
            // About 2 KB a night; even at the smallest MTU this is a few seconds.
            withTimeout(60_000) { done.await() }
            return asm.result()
        } finally {
            assembler = null
            logDone = null
        }
    }

    // ---- GATT plumbing ----

    private fun characteristic(uuid: UUID): BluetoothGattCharacteristic {
        val service = gatt?.getService(NudgeUuids.SERVICE) ?: throw BandException("Not a NudgeBand (service missing)")
        return service.getCharacteristic(uuid) ?: throw BandException("Band firmware is missing $uuid")
    }

    /** Runs one GATT operation and waits for its callback result. */
    private suspend fun op(start: () -> Boolean): Any = opLock.withLock {
        val deferred = CompletableDeferred<Any>()
        pendingOp = deferred
        try {
            if (!start()) throw BandException("Bluetooth refused the request")
            withTimeout(10_000) { deferred.await() }
        } finally {
            pendingOp = null
        }
    }

    private suspend fun read(uuid: UUID): ByteArray {
        val c = characteristic(uuid)
        return op { gatt?.readCharacteristic(c) == true } as ByteArray
    }

    @Suppress("DEPRECATION")
    private suspend fun write(uuid: UUID, value: ByteArray) {
        val c = characteristic(uuid)
        val type = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
        op {
            val g = gatt ?: return@op false
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                g.writeCharacteristic(c, value, type) == BluetoothStatusCodes.SUCCESS
            } else {
                c.writeType = type
                c.value = value
                g.writeCharacteristic(c)
            }
        }
    }

    @Suppress("DEPRECATION")
    private suspend fun enableNotify(uuid: UUID, indicate: Boolean) {
        val c = characteristic(uuid)
        val g = gatt ?: throw BandException("Not connected")
        g.setCharacteristicNotification(c, true)
        val d = c.getDescriptor(NudgeUuids.CCCD) ?: throw BandException("Band firmware has no CCCD on $uuid")
        val value = if (indicate) BluetoothGattDescriptor.ENABLE_INDICATION_VALUE
        else BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
        op {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                g.writeDescriptor(d, value) == BluetoothStatusCodes.SUCCESS
            } else {
                d.value = value
                g.writeDescriptor(d)
            }
        }
    }

    private fun finishOp(status: Int, result: Any) {
        val p = pendingOp ?: return
        if (status == BluetoothGatt.GATT_SUCCESS) p.complete(result)
        else p.completeExceptionally(BandException(gattError(status)))
    }

    private fun gattError(status: Int) = when (status) {
        0x05, 0x0F -> "Band needs pairing (insufficient security)"
        0x0D -> "Band rejected the data length"
        0x13 -> "Band rejected a value as out of range"
        else -> "Bluetooth error $status"
    }

    private fun onValue(uuid: UUID, value: ByteArray) {
        runCatching {
            when (uuid) {
                NudgeUuids.STATUS -> _status.value = BandStatus.decode(value)
                NudgeUuids.CONTROL -> pendingControl?.complete(ControlResponse.decode(value))
                NudgeUuids.LOG -> {
                    val asm = assembler ?: return
                    if (asm.add(value)) logDone?.complete(Unit)
                }
            }
        }.onFailure { e ->
            if (uuid == NudgeUuids.LOG) logDone?.completeExceptionally(e)
        }
    }

    private val callback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED && status == BluetoothGatt.GATT_SUCCESS) {
                g.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                connectWait?.completeExceptionally(BandException("Connection lost (status $status)"))
                if (_link.value is LinkState.Connected) {
                    closeGatt()
                    _link.value = LinkState.Failed("Band disconnected")
                }
            }
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS && g.getService(NudgeUuids.SERVICE) != null) {
                connectWait?.complete(Unit)
            } else {
                connectWait?.completeExceptionally(BandException("This device is not a NudgeBand"))
            }
        }

        override fun onMtuChanged(g: BluetoothGatt, mtu: Int, status: Int) = finishOp(status, mtu)

        override fun onCharacteristicRead(
            g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray, status: Int,
        ) = finishOp(status, value)

        @Deprecated("Used on Android 12 and older")
        @Suppress("DEPRECATION")
        override fun onCharacteristicRead(g: BluetoothGatt, c: BluetoothGattCharacteristic, status: Int) {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) finishOp(status, c.value ?: ByteArray(0))
        }

        override fun onCharacteristicWrite(g: BluetoothGatt, c: BluetoothGattCharacteristic, status: Int) =
            finishOp(status, Unit)

        override fun onDescriptorWrite(g: BluetoothGatt, d: BluetoothGattDescriptor, status: Int) =
            finishOp(status, Unit)

        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray) =
            onValue(c.uuid, value)

        @Deprecated("Used on Android 12 and older")
        @Suppress("DEPRECATION")
        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic) {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) onValue(c.uuid, c.value ?: ByteArray(0))
        }
    }
}
