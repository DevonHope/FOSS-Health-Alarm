package io.github.devonhope.nudgeband.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import io.github.devonhope.nudgeband.BandViewModel
import io.github.devonhope.nudgeband.band.LinkState
import io.github.devonhope.nudgeband.protocol.LogEventKind
import io.github.devonhope.nudgeband.protocol.SleepLog
import io.github.devonhope.nudgeband.protocol.SleepScorer
import io.github.devonhope.nudgeband.protocol.SleepStage

@Composable
fun SleepScreen(vm: BandViewModel, modifier: Modifier = Modifier) {
    val connection by vm.connection.collectAsStateWithLifecycle()
    val link by connection.link.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val history by vm.history.collectAsStateWithLifecycle()
    val nights = remember(history) { history.nights().reversed() }
    var selected by rememberSaveable { mutableIntStateOf(0) }

    LazyColumn(
        modifier.fillMaxWidth().padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(Modifier.padding(top = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                Text("Sleep", Modifier.weight(1f), style = MaterialTheme.typography.headlineMedium)
                Button(onClick = vm::syncLog, enabled = link is LinkState.Connected && !busy) { Text("Sync") }
            }
        }
        if (nights.isEmpty()) {
            item {
                Text(
                    "No nights yet. Wear the band to bed, then connect and tap Sync in the morning." +
                        if (connection.isSimulated) " With the simulator, tap \"Simulate last night\" on the Band tab first." else "",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        } else {
            val night = nights[selected.coerceIn(nights.indices)]
            item { NightDetail(night) }
            item { Text("All nights", style = MaterialTheme.typography.titleMedium) }
            items(nights.indices.toList()) { i ->
                NightRow(nights[i], i == selected) { selected = i }
            }
            item {
                TextButton(onClick = vm::clearHistory) { Text("Delete history on this phone") }
                Spacer(Modifier.height(16.dp))
            }
        }
    }
}

@Composable
private fun NightDetail(night: SleepLog) {
    val summary = remember(night) { SleepScorer.summarize(night) }
    val stages = remember(night) { SleepScorer.stages(night.epochs.map { it.activity }) }
    val wake = night.events.firstOrNull {
        it.kind == LogEventKind.WOKE_LIGHT_SLEEP || it.kind == LogEventKind.WOKE_WINDOW_END || it.kind == LogEventKind.EXACT_ALARM
    }
    val windowStart = night.events.firstOrNull { it.kind == LogEventKind.WINDOW_STARTED }
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                "Night of ${formatDate(summary.startUtc)}",
                style = MaterialTheme.typography.titleLarge,
            )
            Text("${formatTime(summary.startUtc)} to ${formatTime(summary.endUtc)}, ${formatMinutes(summary.totalMinutes)}")
            Hypnogram(
                night, stages, windowStart?.utc, wake?.utc,
                Modifier.fillMaxWidth().height(120.dp).semantics {
                    contentDescription = "Sleep chart: ${formatMinutes(summary.deepMinutes)} deep, " +
                        "${formatMinutes(summary.lightMinutes)} light"
                },
            )
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Legend(StageColors.deep, "Deep ${formatMinutes(summary.deepMinutes)}")
                Legend(StageColors.light, "Light ${formatMinutes(summary.lightMinutes)}")
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Legend(StageColors.awake, "Awake ${formatMinutes(summary.awakeMinutes)}")
                Legend(StageColors.wake, "Wake-up")
            }
            if (wake != null) {
                InfoRow("Woke at", formatTime(wake.utc))
                InfoRow("Why", wake.kind.label)
            }
            Text(
                "Stages are an estimate from movement only, not a medical measurement.",
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@Composable
private fun Legend(color: Color, text: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(10.dp).background(color, CircleShape))
        Spacer(Modifier.width(6.dp))
        Text(text, style = MaterialTheme.typography.bodySmall)
    }
}

/** Bars per epoch: tall = awake, mid = light, short = deep. Dashed line = window start, red = wake. */
@Composable
private fun Hypnogram(night: SleepLog, stages: List<SleepStage>, windowUtc: Long?, wakeUtc: Long?, modifier: Modifier) {
    val start = night.epochs.firstOrNull()?.utc ?: return
    val end = night.epochs.last().utc + night.epochSeconds
    val span = (end - start).toFloat().coerceAtLeast(1f)
    Canvas(modifier) {
        val barWidth = (size.width * night.epochSeconds / span).coerceAtLeast(1f)
        night.epochs.forEachIndexed { i, e ->
            val (color, level) = when (stages[i]) {
                SleepStage.DEEP -> StageColors.deep to 0.35f
                SleepStage.LIGHT -> StageColors.light to 0.7f
                SleepStage.AWAKE -> StageColors.awake to 1f
                SleepStage.NO_DATA -> StageColors.noData to 0.1f
            }
            val x = size.width * (e.utc - start) / span
            val h = size.height * level
            drawRect(color, Offset(x, size.height - h), Size(barWidth, h))
        }
        fun xOf(utc: Long) = size.width * (utc - start) / span
        windowUtc?.let {
            drawLine(
                StageColors.wake.copy(alpha = 0.6f), Offset(xOf(it), 0f), Offset(xOf(it), size.height),
                strokeWidth = 2f, pathEffect = PathEffect.dashPathEffect(floatArrayOf(8f, 8f)),
            )
        }
        wakeUtc?.let {
            drawLine(StageColors.wake, Offset(xOf(it), 0f), Offset(xOf(it), size.height), strokeWidth = 4f)
        }
    }
}

@Composable
private fun NightRow(night: SleepLog, selected: Boolean, onClick: () -> Unit) {
    val s = remember(night) { SleepScorer.summarize(night) }
    Card(
        Modifier.fillMaxWidth().clickable(onClick = onClick),
        colors = if (selected) CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
        else CardDefaults.cardColors(),
    ) {
        Row(Modifier.padding(12.dp)) {
            Text(formatDate(s.startUtc), Modifier.weight(1f))
            Text(formatMinutes(s.totalMinutes))
        }
    }
}
