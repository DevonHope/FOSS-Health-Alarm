package io.github.devonhope.nudgeband.protocol

/** Little-endian helpers. Every multi-byte field in the protocol is little-endian. */
internal class ByteWriter(size: Int) {
    val bytes = ByteArray(size)
    private var pos = 0

    fun u8(v: Int) = apply { bytes[pos++] = v.toByte() }
    fun u16(v: Int) = apply { u8(v and 0xFF); u8((v ushr 8) and 0xFF) }
    fun i16(v: Int) = u16(v and 0xFFFF)
    fun u32(v: Long) = apply {
        u16((v and 0xFFFF).toInt()); u16(((v ushr 16) and 0xFFFF).toInt())
    }
}

internal class ByteReader(private val bytes: ByteArray) {
    var pos = 0
        private set
    val remaining get() = bytes.size - pos

    fun u8(): Int {
        if (pos >= bytes.size) throw ProtocolException("packet too short (${bytes.size} bytes)")
        return bytes[pos++].toInt() and 0xFF
    }
    fun u16(): Int = u8() or (u8() shl 8)
    fun i16(): Int = u16().toShort().toInt()
    fun u32(): Long = u16().toLong() or (u16().toLong() shl 16)
}

class ProtocolException(message: String) : Exception(message)

internal fun requireSize(bytes: ByteArray, min: Int, what: String) {
    if (bytes.size < min) throw ProtocolException("$what needs $min bytes, got ${bytes.size}")
}
