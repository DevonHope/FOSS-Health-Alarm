/* NudgeBand Bluetooth service (docs/ble-protocol.md). */
#ifndef NUDGEBAND_BLE_H
#define NUDGEBAND_BLE_H

int ble_init(void);

/* Tell a subscribed phone that Status changed. */
void ble_status_changed(void);

#endif
