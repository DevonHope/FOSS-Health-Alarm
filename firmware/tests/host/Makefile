# Host unit tests for the hardware-independent firmware code (no Zephyr needed).
#   make -C firmware/tests/host
SRC_DIR := ../../src
CFLAGS  ?= -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined
CFLAGS  += -I$(SRC_DIR)
SRCS    := test_main.c test_protocol.c $(SRC_DIR)/activity.c $(SRC_DIR)/smartwake.c \
           $(SRC_DIR)/alarm.c $(SRC_DIR)/protocol.c
BUILD   := build

.PHONY: test clean
test: $(BUILD)/tests
	./$(BUILD)/tests

$(BUILD)/tests: $(SRCS) $(wildcard $(SRC_DIR)/*.h) test.h
	mkdir -p $(BUILD)
	$(CC) $(CFLAGS) -o $@ $(SRCS)

clean:
	rm -rf $(BUILD)
