# SPDX-License-Identifier: MIT
#
# Flashing: the dock is a CMSIS-DAP probe (RP2040 running debugprobe), so pyOCD or OpenOCD are the
# runners to try first. A J-Link or an nRF54L15 DK's on-board debugger also works (jlink / nrfutil).
# Which runner handles the nRF54L10 cleanly over CMSIS-DAP is still to be confirmed (TODO.md, 0.4).

board_runner_args(pyocd "--target=nrf54l")
board_runner_args(jlink "--device=nRF54L10_M33" "--speed=4000")

include(${ZEPHYR_BASE}/boards/common/pyocd.board.cmake)
include(${ZEPHYR_BASE}/boards/common/openocd.board.cmake)
include(${ZEPHYR_BASE}/boards/common/nrfutil.board.cmake)
include(${ZEPHYR_BASE}/boards/common/jlink.board.cmake)
