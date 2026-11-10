package io.github.devonhope.nudgeband.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import io.github.devonhope.nudgeband.BandViewModel
import io.github.devonhope.nudgeband.band.LinkState
import io.github.devonhope.nudgeband.protocol.BandStatus
import io.github.devonhope.nudgeband.protocol.WakeReason

@Composable
fun BandScreen(vm: BandViewModel, modifier: Modifier = Modifier) {
    val connection by vm.connection.collectAsStateWithLifecycle()
    val link by connection.link.collectAsStateWithLifecycle()
    val found by connection.found.collectAsStateWithLifecycle()
    val status by connection.status.collectAsStateWithLifecycle()
    val alarm by connection.alarm.collectAsStateWithLifecycle()
    val useSim by vm.useSimulator.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val context = LocalContext.current

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { results -> if (results.values.all { it }) vm.startScan() }

    fun scan() {
        if (connection.isSimulated || hasBluetoothPermissions(context)) vm.startScan()
        else permissionLauncher.launch(bluetoothPermissions())
    }

    Column(
        modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("NudgeBand", style = MaterialTheme.typography.headlineMedium)
        if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())

        Card(Modifier.fillMaxWidth()) {
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Use simulated band", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "Try the app before your band is built. Turn off to connect a real band.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
                Switch(checked = useSim, onCheckedChange = vm::setUseSimulator)
            }
        }

        when (val l = link) {
            is LinkState.Connected -> ConnectedCard(l.name, status, alarm?.enabled == true, vm)
            is LinkState.Connecting -> Card(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(Modifier.size(24.dp))
                    Spacer(Modifier.width(12.dp))
                    Text("Connecting to ${l.name}...")
                }
            }
            else -> Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Not connected", style = MaterialTheme.typography.titleMedium)
                    if (l is LinkState.Failed) {
                        Text(l.message, color = MaterialTheme.colorScheme.error)
                    }
                    if (l == LinkState.Scanning) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp)
                            Spacer(Modifier.width(8.dp))
                            Text("Looking for bands nearby. Take the band off the dock to wake its radio.")
                        }
                        found.forEach { band ->
                            HorizontalDivider()
                            Row(
                                Modifier.fillMaxWidth().clickable { vm.connect(band) }.padding(vertical = 12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text(band.name, Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge)
                                Text("${band.rssi} dBm", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                        TextButton(onClick = vm::stopScan) { Text("Stop looking") }
                    } else {
                        Button(onClick = { scan() }) { Text("Find my band") }
                        val saved = vm.savedBandAddress
                        if (!useSim && saved != null) {
                            OutlinedButton(onClick = vm::reconnectSaved) { Text("Reconnect to ${vm.savedBandName}") }
                        }
                    }
                }
            }
        }

        if (useSim) SimulatorCard(vm, link is LinkState.Connected)
    }
}

@Composable
private fun ConnectedCard(name: String, status: BandStatus?, alarmOn: Boolean, vm: BandViewModel) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(name, style = MaterialTheme.typography.titleLarge)
            if (status == null) {
                Text("Reading status...")
            } else {
                InfoRow("Battery", "${status.batteryPercent} %" + when {
                    status.charging -> " (charging)"
                    status.docked -> " (on dock)"
                    else -> ""
                })
                InfoRow("Now", status.state.label)
                InfoRow(
                    "Next alarm",
                    if (status.nextAlarmUtc != 0L && alarmOn) "${formatDate(status.nextAlarmUtc)}, ${formatTime(status.nextAlarmUtc)}"
                    else "Off",
                )
                if (status.lastWakeReason != WakeReason.NONE) {
                    InfoRow("Last wake", "${formatTime(status.lastWakeUtc)}, ${status.lastWakeReason.label.lowercase()}")
                }
                InfoRow("Firmware", status.firmwareVersion)
                if (!status.timeSet) Text("The band's clock is not set yet.", color = MaterialTheme.colorScheme.error)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { vm.testBuzz(150) }) { Text("Test buzz") }
                OutlinedButton(onClick = vm::identify) { Text("Blink LED") }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = vm::dismiss) { Text("Stop alarm") }
                TextButton(onClick = vm::disconnect) { Text("Disconnect") }
            }
        }
    }
}

@Composable
private fun SimulatorCard(vm: BandViewModel, connected: Boolean) {
    val sim = vm.simulator ?: return
    val buzzing by sim.buzzing.collectAsStateWithLifecycle()
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Simulator", style = MaterialTheme.typography.titleMedium)
            Text(
                if (buzzing) "The simulated motor is buzzing now."
                else "Fake a night of sleep, then open the Sleep tab and tap Sync.",
                style = MaterialTheme.typography.bodySmall,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = vm::simulateNight, enabled = connected) { Text("Simulate last night") }
                OutlinedButton(onClick = { sim.toggleDock() }, enabled = connected) { Text("Dock / undock") }
            }
        }
    }
}

@Composable
fun InfoRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth()) {
        Text(label, Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
        Text(value, style = MaterialTheme.typography.bodyMedium)
    }
}
