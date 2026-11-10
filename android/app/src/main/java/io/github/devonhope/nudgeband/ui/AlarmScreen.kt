package io.github.devonhope.nudgeband.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TimePicker
import androidx.compose.material3.rememberTimePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import io.github.devonhope.nudgeband.BandViewModel
import io.github.devonhope.nudgeband.band.LinkState
import io.github.devonhope.nudgeband.protocol.AlarmConfig
import io.github.devonhope.nudgeband.protocol.VibrationPattern
import kotlin.math.roundToInt

private val dayNames = listOf("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

@OptIn(ExperimentalLayoutApi::class, ExperimentalMaterial3Api::class)
@Composable
fun AlarmScreen(vm: BandViewModel, modifier: Modifier = Modifier) {
    val connection by vm.connection.collectAsStateWithLifecycle()
    val link by connection.link.collectAsStateWithLifecycle()
    val bandAlarm by connection.alarm.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val connected = link is LinkState.Connected

    // Edit a local copy; it only reaches the band when you tap Save.
    var draft by remember { mutableStateOf(bandAlarm ?: AlarmConfig(enabled = true)) }
    LaunchedEffect(bandAlarm) { bandAlarm?.let { draft = it } }
    var pickTime by remember { mutableStateOf(false) }
    val changed = bandAlarm != null && draft != bandAlarm

    Column(
        modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Alarm", style = MaterialTheme.typography.headlineMedium)
        if (!connected) {
            Text("Connect to your band on the Band tab to change its alarm.", color = MaterialTheme.colorScheme.error)
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        formatTime(draft.hour, draft.minute),
                        Modifier.weight(1f),
                        style = MaterialTheme.typography.displayMedium,
                    )
                    Switch(checked = draft.enabled, onCheckedChange = { draft = draft.copy(enabled = it) })
                }
                OutlinedButton(onClick = { pickTime = true }) { Text("Change time") }
                Text(
                    if (draft.smartWake && draft.windowMinutes > 0) {
                        "Wakes you in light sleep between ${windowStartLabel(draft)} and ${formatTime(draft.hour, draft.minute)}."
                    } else {
                        "Wakes you at ${formatTime(draft.hour, draft.minute)}."
                    },
                    style = MaterialTheme.typography.bodyMedium,
                )
                FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    dayNames.forEachIndexed { i, name ->
                        val bit = 1 shl i
                        FilterChip(
                            selected = draft.days and bit != 0,
                            onClick = { draft = draft.copy(days = draft.days xor bit) },
                            label = { Text(name) },
                        )
                    }
                }
                Text(
                    if (draft.days == 0) "No days picked: rings once, at the next ${formatTime(draft.hour, draft.minute)}."
                    else "Repeats on the picked days.",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Smart wake", style = MaterialTheme.typography.titleMedium)
                        Text("Wait for light sleep inside the window", style = MaterialTheme.typography.bodySmall)
                    }
                    Switch(checked = draft.smartWake, onCheckedChange = { draft = draft.copy(smartWake = it) })
                }
                if (draft.smartWake) {
                    Text("Window: ${draft.windowMinutes} min before the alarm")
                    Slider(
                        value = draft.windowMinutes.toFloat(),
                        onValueChange = { draft = draft.copy(windowMinutes = (it / 5).roundToInt() * 5) },
                        valueRange = 5f..60f,
                        steps = 10,
                    )
                }
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Vibration", style = MaterialTheme.typography.titleMedium)
                SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                    VibrationPattern.entries.forEachIndexed { i, p ->
                        SegmentedButton(
                            selected = draft.pattern == p,
                            onClick = { draft = draft.copy(pattern = p) },
                            shape = SegmentedButtonDefaults.itemShape(i, VibrationPattern.entries.size),
                        ) { Text(p.label, maxLines = 1) }
                    }
                }
                Text("Strength: ${(draft.intensity * 100 / 255)} %")
                Slider(
                    value = draft.intensity.toFloat(),
                    onValueChange = { draft = draft.copy(intensity = it.roundToInt()) },
                    valueRange = 40f..255f,
                )
                Text("Soft start: ${draft.rampSeconds} s")
                Slider(
                    value = draft.rampSeconds.toFloat(),
                    onValueChange = { draft = draft.copy(rampSeconds = it.roundToInt()) },
                    valueRange = 0f..60f,
                )
                Text(
                    if (draft.repeatMinutes == 0) "Buzz once for ${draft.buzzSeconds} s"
                    else "Buzz ${draft.buzzSeconds} s, then again every ${draft.repeatMinutes} min (up to ${draft.maxRepeats} times)",
                )
                Slider(
                    value = draft.buzzSeconds.toFloat(),
                    onValueChange = { draft = draft.copy(buzzSeconds = it.roundToInt()) },
                    valueRange = 5f..120f,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = { vm.testBuzz(draft.intensity) }, enabled = connected) { Text("Try it") }
                }
            }
        }

        Button(
            onClick = { vm.saveAlarm(draft) },
            enabled = connected && !busy && (changed || bandAlarm == null),
            modifier = Modifier.fillMaxWidth(),
        ) { Text(if (changed) "Save to band" else "Saved") }
    }

    if (pickTime) TimeDialog(draft, onDismiss = { pickTime = false }) { h, m ->
        draft = draft.copy(hour = h, minute = m)
        pickTime = false
    }
}

private fun windowStartLabel(a: AlarmConfig): String {
    val total = (a.hour * 60 + a.minute - a.windowMinutes + 24 * 60) % (24 * 60)
    return formatTime(total / 60, total % 60)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TimeDialog(a: AlarmConfig, onDismiss: () -> Unit, onPick: (Int, Int) -> Unit) {
    val is24h = android.text.format.DateFormat.is24HourFormat(LocalContext.current)
    val state = rememberTimePickerState(a.hour, a.minute, is24h)
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = { TextButton(onClick = { onPick(state.hour, state.minute) }) { Text("OK") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
        text = { TimePicker(state) },
    )
}
