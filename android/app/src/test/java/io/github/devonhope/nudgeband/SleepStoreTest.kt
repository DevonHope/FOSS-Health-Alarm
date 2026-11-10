package io.github.devonhope.nudgeband

import io.github.devonhope.nudgeband.data.SleepStore
import io.github.devonhope.nudgeband.protocol.Epoch
import io.github.devonhope.nudgeband.protocol.LogEventKind
import io.github.devonhope.nudgeband.protocol.LogPacket
import io.github.devonhope.nudgeband.protocol.SleepLog
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class SleepStoreTest {
    @get:Rule val tmp = TemporaryFolder()

    @Test fun mergeKeepsOneValuePerEpochAndSurvivesReload() {
        val file = File(tmp.root, "log.txt")
        val store = SleepStore(file)
        val first = SleepLog(30, listOf(Epoch(0, 10), Epoch(30, 20)), listOf(LogPacket.Event(0, 30, LogEventKind.DOCKED)))
        val second = SleepLog(30, listOf(Epoch(30, 20), Epoch(60, 30)), listOf(LogPacket.Event(0, 30, LogEventKind.DOCKED)))
        store.merge(first)
        store.merge(second)
        val back = SleepStore(file).load()
        assertEquals(listOf(0L, 30L, 60L), back.epochs.map { it.utc })
        assertEquals(1, back.events.size)
        store.clear()
        assertEquals(0, store.load().epochs.size)
    }
}
