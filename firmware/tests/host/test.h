#ifndef NUDGEBAND_TEST_H
#define NUDGEBAND_TEST_H

#include <stdio.h>

extern int failures;
extern int checks;

#define CHECK(cond)                                                                        \
	do {                                                                               \
		checks++;                                                                  \
		if (!(cond)) {                                                             \
			failures++;                                                        \
			printf("  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);           \
		}                                                                          \
	} while (0)

void test_protocol(void);

#endif
