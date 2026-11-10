/*
 * GATT side of docs/ble-protocol.md. Standard Battery and Device Information services come from
 * Zephyr (CONFIG_BT_BAS, CONFIG_BT_DIS); MCUmgr SMP for updates over the air is TODO.md 4.6.
 */
#include "ble.h"

#include <string.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>

#include "band.h"
#include "protocol.h"

LOG_MODULE_REGISTER(ble, LOG_LEVEL_INF);

#define NB_UUID(short16) BT_UUID_128_ENCODE(NB_UUID_BASE_W32 | (short16), 0xa414, 0x4c37, 0x89d9, \
					    0x4dcc3036748eULL)

static const struct bt_uuid_128 uuid_svc = BT_UUID_INIT_128(NB_UUID(NB_UUID_SERVICE));
static const struct bt_uuid_128 uuid_time = BT_UUID_INIT_128(NB_UUID(NB_UUID_TIME));
static const struct bt_uuid_128 uuid_alarm = BT_UUID_INIT_128(NB_UUID(NB_UUID_ALARM));
static const struct bt_uuid_128 uuid_status = BT_UUID_INIT_128(NB_UUID(NB_UUID_STATUS));
static const struct bt_uuid_128 uuid_control = BT_UUID_INIT_128(NB_UUID(NB_UUID_CONTROL));
static const struct bt_uuid_128 uuid_log = BT_UUID_INIT_128(NB_UUID(NB_UUID_LOG));

static bool status_notify;
static bool control_indicate;

/* --- Time --- */

static ssize_t read_time(struct bt_conn *conn, const struct bt_gatt_attr *attr, void *buf,
			 uint16_t len, uint16_t offset)
{
	struct nb_time t;

	band_get_time(&t);
	return bt_gatt_attr_read(conn, attr, buf, len, offset, &t, sizeof(t));
}

static ssize_t write_time(struct bt_conn *conn, const struct bt_gatt_attr *attr, const void *buf,
			  uint16_t len, uint16_t offset, uint8_t flags)
{
	struct nb_time t;

	if (offset != 0 || len != sizeof(t)) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
	}
	memcpy(&t, buf, sizeof(t));
	band_set_time(&t);
	return len;
}

/* --- Alarm config --- */

static ssize_t read_alarm(struct bt_conn *conn, const struct bt_gatt_attr *attr, void *buf,
			  uint16_t len, uint16_t offset)
{
	struct nb_alarm_cfg c;

	band_get_alarm(&c);
	return bt_gatt_attr_read(conn, attr, buf, len, offset, &c, sizeof(c));
}

static ssize_t write_alarm(struct bt_conn *conn, const struct bt_gatt_attr *attr, const void *buf,
			   uint16_t len, uint16_t offset, uint8_t flags)
{
	struct nb_alarm_cfg c;

	if (offset != 0 || len != sizeof(c)) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
	}
	memcpy(&c, buf, sizeof(c));
	if (!nb_alarm_cfg_valid(&c)) {
		return BT_GATT_ERR(BT_ATT_ERR_VALUE_NOT_ALLOWED);
	}
	band_set_alarm(&c);
	return len;
}

/* --- Status --- */

static ssize_t read_status(struct bt_conn *conn, const struct bt_gatt_attr *attr, void *buf,
			   uint16_t len, uint16_t offset)
{
	struct nb_status st;

	band_get_status(&st);
	return bt_gatt_attr_read(conn, attr, buf, len, offset, &st, sizeof(st));
}

static void status_ccc(const struct bt_gatt_attr *attr, uint16_t value)
{
	status_notify = (value == BT_GATT_CCC_NOTIFY);
}

/* --- Control point --- */

static void control_ccc(const struct bt_gatt_attr *attr, uint16_t value)
{
	control_indicate = (value == BT_GATT_CCC_INDICATE);
}

static ssize_t write_control(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			     const void *buf, uint16_t len, uint16_t offset, uint8_t flags);

static void log_ccc(const struct bt_gatt_attr *attr, uint16_t value)
{
	ARG_UNUSED(attr);
	ARG_UNUSED(value);
}

BT_GATT_SERVICE_DEFINE(nb_svc,
	BT_GATT_PRIMARY_SERVICE(&uuid_svc),
	BT_GATT_CHARACTERISTIC(&uuid_time.uuid, BT_GATT_CHRC_READ | BT_GATT_CHRC_WRITE,
			       BT_GATT_PERM_READ | BT_GATT_PERM_WRITE_ENCRYPT, read_time,
			       write_time, NULL),
	BT_GATT_CHARACTERISTIC(&uuid_alarm.uuid, BT_GATT_CHRC_READ | BT_GATT_CHRC_WRITE,
			       BT_GATT_PERM_READ | BT_GATT_PERM_WRITE_ENCRYPT, read_alarm,
			       write_alarm, NULL),
	BT_GATT_CHARACTERISTIC(&uuid_status.uuid, BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
			       BT_GATT_PERM_READ, read_status, NULL, NULL),
	BT_GATT_CCC(status_ccc, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
	BT_GATT_CHARACTERISTIC(&uuid_control.uuid, BT_GATT_CHRC_WRITE | BT_GATT_CHRC_INDICATE,
			       BT_GATT_PERM_WRITE_ENCRYPT, NULL, write_control, NULL),
	BT_GATT_CCC(control_ccc, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE_ENCRYPT),
	BT_GATT_CHARACTERISTIC(&uuid_log.uuid, BT_GATT_CHRC_NOTIFY, BT_GATT_PERM_NONE, NULL, NULL,
			       NULL),
	BT_GATT_CCC(log_ccc, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE_ENCRYPT),
);

/* Attribute indexes in nb_svc.attrs (value attributes) */
#define ATTR_STATUS  6
#define ATTR_CONTROL 9

static struct bt_gatt_indicate_params ind_params;
static uint8_t ind_buf[3];

static void respond(struct bt_conn *conn, uint8_t opcode, enum nb_cp_result result)
{
	if (!control_indicate) {
		return;
	}
	ind_buf[0] = NB_CP_RESPONSE;
	ind_buf[1] = opcode;
	ind_buf[2] = result;
	memset(&ind_params, 0, sizeof(ind_params));
	ind_params.attr = &nb_svc.attrs[ATTR_CONTROL];
	ind_params.data = ind_buf;
	ind_params.len = sizeof(ind_buf);
	(void)bt_gatt_indicate(conn, &ind_params);
}

static ssize_t write_control(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			     const void *buf, uint16_t len, uint16_t offset, uint8_t flags)
{
	const uint8_t *p = buf;
	enum nb_cp_result r = NB_CP_OK;

	if (offset != 0 || len < 1) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
	}
	switch (p[0]) {
	case NB_CP_TEST_BUZZ:
		r = (len == 3) ? band_test_buzz(p[1], p[2]) : NB_CP_INVALID;
		break;
	case NB_CP_STOP_BUZZ:
		band_stop_buzz();
		break;
	case NB_CP_DISMISS:
		band_dismiss();
		break;
	case NB_CP_IDENTIFY:
		band_identify();
		break;
	case NB_CP_LOG_READ:  /* TODO.md 4.4 */
	case NB_CP_LOG_CLEAR: /* TODO.md 4.4 */
	default:
		r = NB_CP_UNSUPPORTED;
		break;
	}
	respond(conn, p[0], r);
	return len;
}

void ble_status_changed(void)
{
	struct nb_status st;

	if (!status_notify) {
		return;
	}
	band_get_status(&st);
	(void)bt_gatt_notify(NULL, &nb_svc.attrs[ATTR_STATUS], &st, sizeof(st));
}

/* --- Advertising and connections --- */

static const struct bt_data ad[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
	BT_DATA_BYTES(BT_DATA_UUID128_ALL, NB_UUID(NB_UUID_SERVICE)),
};

static char name[sizeof("NudgeBand-XXXX")];
static struct bt_data sd[1];

/* About 1 s between advertisements (TODO.md 4.1: tune for battery, faster after undocking). */
#define ADV_PARAM BT_LE_ADV_PARAM(BT_LE_ADV_OPT_CONN, 1600, 1760, NULL)

static void adv_start(void)
{
	int err = bt_le_adv_start(ADV_PARAM, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));

	if (err && err != -EALREADY) {
		LOG_ERR("advertising failed (%d)", err);
	}
}

static void connected(struct bt_conn *conn, uint8_t err)
{
	if (err) {
		return;
	}
	LOG_INF("connected");
	/* Ask for encryption straight away; Just Works pairing on the first connection. */
	(void)bt_conn_set_security(conn, BT_SECURITY_L2);
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
	LOG_INF("disconnected (0x%02x)", reason);
}

static void recycled(void)
{
	adv_start();
}

BT_CONN_CB_DEFINE(conn_cb) = {
	.connected = connected,
	.disconnected = disconnected,
	.recycled = recycled,
};

int ble_init(void)
{
	bt_addr_le_t addr;
	size_t count = 1;
	int err = bt_enable(NULL);

	if (err) {
		LOG_ERR("bt_enable failed (%d)", err);
		return err;
	}
	if (IS_ENABLED(CONFIG_BT_SETTINGS)) {
		settings_load();
	}
	bt_id_get(&addr, &count);
	snprintk(name, sizeof(name), "NudgeBand-%02X%02X", addr.a.val[1], addr.a.val[0]);
	(void)bt_set_name(name);
	sd[0].type = BT_DATA_NAME_COMPLETE;
	sd[0].data_len = strlen(name);
	sd[0].data = (const uint8_t *)name;
	adv_start();
	LOG_INF("advertising as %s", name);
	return 0;
}
