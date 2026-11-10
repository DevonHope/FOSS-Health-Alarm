package io.github.devonhope.nudgeband.protocol

enum class LogEventKind(val code: Int, val label: String) {
    WINDOW_STARTED(1, "Wake window started"),
    WOKE_LIGHT_SLEEP(2, "Woke in light sleep"),
    WOKE_WINDOW_END(3, "Woke at alarm time"),
    DISMISSED(4, "Dismissed"),
    DOCKED(5, "Put on dock"),
    UNDOCKED(6, "Taken off dock"),
    EXACT_ALARM(7, "Exact alarm"),
    UNKNOWN(0, "Unknown event");

    companion object {
        fun fromCode(c: Int) = entries.firstOrNull { it.code == c } ?: UNKNOWN
    }
}

/** Notifications on the sleep log characteristic (0x0006). */
sealed class LogPacket {
    abstract val sequence: Int

    data class Data(
        override val sequence: Int,
        val startUtc: Long,
        val epochSeconds: Int,
        val activity: List<Int>,
    ) : LogPacket()

    data class Event(
        override val sequence: Int,
        val utc: Long,
        val kind: LogEventKind,
        val argument: Int = 0,
    ) : LogPacket()

    data class End(override val sequence: Int, val packetCount: Int) : LogPacket()

    fun encode(): ByteArray = when (this) {
        is Data -> {
            val w = ByteWriter(DATA_HEADER + activity.size * 2)
                .u8(TYPE_DATA).u16(sequence).u32(startUtc).u8(epochSeconds).u8(activity.size)
            activity.forEach { w.u16(it) }
            w.bytes
        }
        is Event -> ByteWriter(9).u8(TYPE_EVENT).u16(sequence).u32(utc).u8(kind.code).u8(argument).bytes
        is End -> ByteWriter(5).u8(TYPE_END).u16(sequence).u16(packetCount).bytes
    }

    companion object {
        const val TYPE_DATA = 1
        const val TYPE_EVENT = 2
        const val TYPE_END = 3
        const val DATA_HEADER = 9

        /** Activity value meaning "no data" (off wrist, docked, or not running). */
        const val NO_DATA = 0xFFFF

        /** How many epochs fit in one DATA packet at this ATT MTU. */
        fun epochsPerPacket(mtu: Int): Int = ((mtu - 3 - DATA_HEADER) / 2).coerceIn(1, 255)

        fun decode(b: ByteArray): LogPacket {
            requireSize(b, 3, "Log packet")
            val r = ByteReader(b)
            val type = r.u8()
            val seq = r.u16()
            return when (type) {
                TYPE_DATA -> {
                    val start = r.u32()
                    val epoch = r.u8()
                    val n = r.u8()
                    if (r.remaining < n * 2) throw ProtocolException("DATA packet says $n epochs but is short")
                    Data(seq, start, epoch, List(n) { r.u16() })
                }
                TYPE_EVENT -> Event(seq, r.u32(), LogEventKind.fromCode(r.u8()), r.u8())
                TYPE_END -> End(seq, r.u16())
                else -> throw ProtocolException("unknown log packet type $type")
            }
        }
    }
}

data class Epoch(val utc: Long, val activity: Int) {
    val hasData get() = activity != LogPacket.NO_DATA
}

data class SleepLog(val epochSeconds: Int, val epochs: List<Epoch>, val events: List<LogPacket.Event>) {
    /** Splits the log into nights: a gap or a no-data stretch of [gapMinutes] or more starts a new night. */
    fun nights(gapMinutes: Int = 60, minMinutes: Int = 60): List<SleepLog> {
        val result = mutableListOf<SleepLog>()
        var current = mutableListOf<Epoch>()
        var lastDataUtc = Long.MIN_VALUE
        fun flush() {
            val trimmed = current.dropLastWhile { !it.hasData }
            if (trimmed.isNotEmpty() && (trimmed.last().utc - trimmed.first().utc) / 60 >= minMinutes) {
                val from = trimmed.first().utc
                val to = trimmed.last().utc + epochSeconds + 3600
                result += SleepLog(epochSeconds, trimmed, events.filter { it.utc in from..to })
            }
            current = mutableListOf()
        }
        for (e in epochs) {
            if (!e.hasData) {
                if (current.isNotEmpty()) current += e
                continue
            }
            if (lastDataUtc != Long.MIN_VALUE && e.utc - lastDataUtc >= gapMinutes * 60L) flush()
            current += e
            lastDataUtc = e.utc
        }
        flush()
        return result
    }
}

/**
 * Collects log notifications from one LOG_READ transfer and checks that nothing was lost.
 */
class LogAssembler {
    private val packets = mutableListOf<LogPacket>()
    var finished = false
        private set

    /** Returns true once the END packet has arrived. */
    fun add(raw: ByteArray): Boolean = add(LogPacket.decode(raw))

    fun add(p: LogPacket): Boolean {
        check(!finished) { "transfer already finished" }
        val expected = packets.size
        if (p.sequence != expected) {
            throw ProtocolException("log packet $expected missing (got ${p.sequence}); ask again")
        }
        if (p is LogPacket.End) {
            if (p.packetCount != packets.size) {
                throw ProtocolException("band sent ${p.packetCount} packets but ${packets.size} arrived")
            }
            finished = true
        } else {
            packets += p
        }
        return finished
    }

    fun result(): SleepLog {
        check(finished) { "transfer not finished" }
        val data = packets.filterIsInstance<LogPacket.Data>()
        val epochSeconds = data.firstOrNull()?.epochSeconds ?: SleepScorer.EPOCH_SECONDS
        val epochs = data.flatMap { d ->
            d.activity.mapIndexed { i, a -> Epoch(d.startUtc + i.toLong() * d.epochSeconds, a) }
        }.sortedBy { it.utc }
        return SleepLog(epochSeconds, epochs, packets.filterIsInstance<LogPacket.Event>().sortedBy { it.utc })
    }
}

/** Splits a log into packets that fit [mtu], as the firmware does. Used by the simulated band and tests. */
fun encodeLog(log: SleepLog, mtu: Int): List<ByteArray> {
    val perPacket = LogPacket.epochsPerPacket(mtu)
    val out = mutableListOf<LogPacket>()
    var i = 0
    while (i < log.epochs.size) {
        // A packet holds consecutive epochs only.
        val start = log.epochs[i].utc
        var n = 1
        while (n < perPacket && i + n < log.epochs.size &&
            log.epochs[i + n].utc == start + n.toLong() * log.epochSeconds
        ) n++
        out += LogPacket.Data(out.size, start, log.epochSeconds, log.epochs.subList(i, i + n).map { it.activity })
        i += n
    }
    log.events.forEach { out += it.copy(sequence = out.size) }
    out += LogPacket.End(out.size, out.size)
    return out.map { it.encode() }
}
