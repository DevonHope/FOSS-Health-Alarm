package io.github.devonhope.nudgeband.protocol

import java.util.UUID

/** GATT UUIDs from docs/ble-protocol.md. */
object NudgeUuids {
    private fun nudge(short: Int): UUID =
        UUID.fromString("a56e%04x-a414-4c37-89d9-4dcc3036748e".format(short))

    private fun sig(short: Int): UUID =
        UUID.fromString("0000%04x-0000-1000-8000-00805f9b34fb".format(short))

    val SERVICE: UUID = nudge(0x0001)
    val TIME: UUID = nudge(0x0002)
    val ALARM: UUID = nudge(0x0003)
    val STATUS: UUID = nudge(0x0004)
    val CONTROL: UUID = nudge(0x0005)
    val LOG: UUID = nudge(0x0006)

    val BATTERY_SERVICE: UUID = sig(0x180F)
    val BATTERY_LEVEL: UUID = sig(0x2A19)
    val DEVICE_INFO_SERVICE: UUID = sig(0x180A)
    val FIRMWARE_REVISION: UUID = sig(0x2A26)

    /** Client Characteristic Configuration descriptor, used to turn on notify/indicate. */
    val CCCD: UUID = sig(0x2902)

    const val NAME_PREFIX = "NudgeBand"
    const val PREFERRED_MTU = 247
}
