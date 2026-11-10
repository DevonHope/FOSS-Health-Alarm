package io.github.devonhope.nudgeband.data

import io.github.devonhope.nudgeband.protocol.Epoch
import io.github.devonhope.nudgeband.protocol.LogEventKind
import io.github.devonhope.nudgeband.protocol.LogPacket
import io.github.devonhope.nudgeband.protocol.SleepLog
import java.io.File

/**
 * Keeps every downloaded epoch and event on the phone, so past nights survive after the band
 * clears its flash. Plain text, one line each: `E,utc,activity` or `V,utc,kind,arg`.
 */
class SleepStore(private val file: File) {
    @Synchronized
    fun load(): SleepLog {
        if (!file.exists()) return SleepLog(EPOCH_SECONDS, emptyList(), emptyList())
        val epochs = mutableListOf<Epoch>()
        val events = mutableListOf<LogPacket.Event>()
        file.forEachLine { line ->
            val p = line.split(',')
            when (p.firstOrNull()) {
                "E" -> if (p.size >= 3) epochs += Epoch(p[1].toLong(), p[2].toInt())
                "V" -> if (p.size >= 4) events += LogPacket.Event(0, p[1].toLong(), LogEventKind.fromCode(p[2].toInt()), p[3].toInt())
            }
        }
        return SleepLog(EPOCH_SECONDS, epochs.sortedBy { it.utc }, events.sortedBy { it.utc })
    }

    /** Adds new data, keeping one value per epoch time and dropping repeated events. */
    @Synchronized
    fun merge(new: SleepLog): SleepLog {
        val old = load()
        val epochs = (old.epochs + new.epochs).associateBy { it.utc }.values.sortedBy { it.utc }
        val events = (old.events + new.events).distinctBy { Triple(it.utc, it.kind, it.argument) }.sortedBy { it.utc }
        val merged = SleepLog(EPOCH_SECONDS, epochs, events)
        save(merged)
        return merged
    }

    @Synchronized
    fun clear() {
        file.delete()
    }

    private fun save(log: SleepLog) {
        val tmp = File(file.parentFile, file.name + ".tmp")
        tmp.bufferedWriter().use { w ->
            log.epochs.forEach { w.write("E,${it.utc},${it.activity}\n") }
            log.events.forEach { w.write("V,${it.utc},${it.kind.code},${it.argument}\n") }
        }
        if (!tmp.renameTo(file)) {
            file.delete()
            tmp.renameTo(file)
        }
    }

    companion object {
        const val EPOCH_SECONDS = 30
    }
}
