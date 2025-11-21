CC := clang
PREFIX ?= /opt/homebrew
MPFR_INCLUDE ?= -I$(PREFIX)/include
MPFR_LIB ?= -L$(PREFIX)/lib -lmpfr
GMP_LIB ?= -L$(PREFIX)/lib -lgmp

INC := -I. -I../z5d-predictor-c/include -I../includes $(MPFR_INCLUDE)
CFLAGS := -O3 -march=native -Wall -Wextra $(INC)
LDFLAGS := $(MPFR_LIB) $(GMP_LIB) -lm

BIN_DIR := bin
SRC := prime_generator.c \
       ../z5d-predictor-c/src/z5d_predictor.c \
       ../z5d-predictor-c/src/z5d_math.c
TARGET := $(BIN_DIR)/prime_generator

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRC) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)
	@echo "Built $(TARGET)"

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

clean:
	rm -f $(TARGET)
