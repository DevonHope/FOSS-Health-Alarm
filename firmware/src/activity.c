#include "activity.h"

static uint32_t absdiff(int16_t a, int16_t b)
{
	int32_t d = (int32_t)a - (int32_t)b;

	return (uint32_t)(d < 0 ? -d : d);
}

void activity_reset(struct activity_acc *acc)
{
	acc->have_prev = false;
	acc->sum = 0;
}

void activity_add(struct activity_acc *acc, const struct accel_sample *s, uint32_t n)
{
	for (uint32_t i = 0; i < n; i++) {
		if (acc->have_prev) {
			uint32_t d = absdiff(s[i].x, acc->prev.x) + absdiff(s[i].y, acc->prev.y) +
				     absdiff(s[i].z, acc->prev.z);

			if (d > ACTIVITY_DEADBAND_MG) {
				acc->sum += d - ACTIVITY_DEADBAND_MG;
				if (acc->sum > ACTIVITY_MAX) {
					acc->sum = ACTIVITY_MAX;
				}
			}
		}
		acc->prev = s[i];
		acc->have_prev = true;
	}
}

uint16_t activity_end_epoch(struct activity_acc *acc)
{
	uint16_t a = (uint16_t)acc->sum;

	acc->sum = 0;
	return a;
}
