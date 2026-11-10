# NudgeBand firmware (Zephyr / nRF Connect SDK application)
# SPDX-License-Identifier: MIT
cmake_minimum_required(VERSION 3.20.0)

# The NudgeBand board definition lives in this repo (boards/nudgeband).
list(APPEND BOARD_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
list(APPEND DTS_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(nudgeband)

target_sources(app PRIVATE
	src/main.c
	src/board_io.c
	src/accel.c
	src/haptics.c
	src/led.c
	src/pmic.c
	src/ble.c
	# hardware-independent, also built by tests/host
	src/activity.c
	src/smartwake.c
	src/alarm.c
	src/protocol.c
)
