# Z5D nth-Prime Predictor - Makefile (Apple Silicon Only)
# =======================================================
#
# Apple-only build for macOS on Apple Silicon (M1 Max tested).
# No Linux/Windows portability or pkg-config fallbacks.
# Assumes GMP/MPFR installed via Homebrew in /opt/homebrew.
#
# Usage:
#   make          - Build all executables and library
#   make test     - Build and run tests
#   make bench    - Build and run benchmark
#   make demo     - Run CLI demo script
#   make clean    - Clean build artifacts
#   make help     - Show this help


# Ensure default goal
.DEFAULT_GOAL := all

# Directories
SRC_DIR := src
INCLUDE_DIR := include
EXTRA_INC := -I../includes
TEST_DIR := tests
BUILD_DIR := build
BIN_DIR := bin

# Compiler
CC := clang

# Apple Silicon-only GMP/MPFR paths (override if needed)
GMP_INCLUDE ?= -I/opt/homebrew/include
GMP_LIB ?= -L/opt/homebrew/lib -lgmp
MPFR_INCLUDE ?= -I/opt/homebrew/include
MPFR_LIB ?= -L/opt/homebrew/lib -lmpfr

# Fail fast if headers/libs are missing at the expected paths
MISSING := $(shell test -f /opt/homebrew/include/gmp.h || echo missing_gmp_hdr)
MISSING += $(shell test -f /opt/homebrew/include/mpfr.h || echo missing_mpfr_hdr)
MISSING += $(shell test -f /opt/homebrew/lib/libgmp.dylib || echo missing_gmp_lib)
MISSING += $(shell test -f /opt/homebrew/lib/libmpfr.dylib || echo missing_mpfr_lib)
ifneq (,$(filter missing_%,$(MISSING)))
$(error GMP/MPFR not found at Homebrew paths (/opt/homebrew). Install with `brew install gmp mpfr` or override GMP_INCLUDE/MPFR_INCLUDE/GMP_LIB/MPFR_LIB)
endif

CFLAGS := -O3 -march=native -Wall -Wextra -I$(INCLUDE_DIR) $(EXTRA_INC) $(GMP_INCLUDE) $(MPFR_INCLUDE)
LDFLAGS := $(GMP_LIB) $(MPFR_LIB) -lm

# Debug flags
DEBUG_CFLAGS := -O0 -g3 -fno-omit-frame-pointer -DDEBUG

# Source files
LIB_SOURCES := $(SRC_DIR)/z5d_predictor.c $(SRC_DIR)/z5d_math.c
LIB_OBJECTS := $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/%.o,$(LIB_SOURCES))

CLI_SOURCE := $(SRC_DIR)/z5d_cli.c
CLI_OBJECT := $(BUILD_DIR)/z5d_cli.o

BENCH_SOURCE := $(SRC_DIR)/z5d_bench.c
BENCH_OBJECT := $(BUILD_DIR)/z5d_bench.o

TEST_KNOWN_SOURCE := $(TEST_DIR)/test_known.c
TEST_KNOWN_OBJECT := $(BUILD_DIR)/test_known.o

TEST_MEDIUM_SOURCE := $(TEST_DIR)/test_medium_scale.c
TEST_MEDIUM_OBJECT := $(BUILD_DIR)/test_medium_scale.o

# Output files
STATIC_LIB := $(BUILD_DIR)/libz5d_predictor.a
CLI_EXECUTABLE := $(BIN_DIR)/z5d_cli
BENCH_EXECUTABLE := $(BIN_DIR)/z5d_bench
TEST_KNOWN_EXECUTABLE := $(BIN_DIR)/test_known
TEST_MEDIUM_EXECUTABLE := $(BIN_DIR)/test_medium_scale

# Create directories
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(BIN_DIR):
	@mkdir -p $(BIN_DIR)

# Build library objects
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	@echo "🔧 Compiling $<..."
	@$(CC) $(CFLAGS) -c $< -o $@

# Build static library
$(STATIC_LIB): $(LIB_OBJECTS) | $(BUILD_DIR)
	@echo "📦 Creating static library..."
	@ar rcs $@ $^

# Build CLI
$(CLI_OBJECT): $(CLI_SOURCE) | $(BUILD_DIR)
	@echo "🔧 Compiling CLI..."
	@$(CC) $(CFLAGS) -c $< -o $@

$(CLI_EXECUTABLE): $(CLI_OBJECT) $(STATIC_LIB) | $(BIN_DIR)
	@echo "🔗 Linking CLI executable..."
	@$(CC) $(CLI_OBJECT) $(STATIC_LIB) $(LDFLAGS) -o $@

# Build benchmark
$(BENCH_OBJECT): $(BENCH_SOURCE) | $(BUILD_DIR)
	@echo "🔧 Compiling benchmark..."
	@$(CC) $(CFLAGS) -c $< -o $@

$(BENCH_EXECUTABLE): $(BENCH_OBJECT) $(STATIC_LIB) | $(BIN_DIR)
	@echo "🔗 Linking benchmark executable..."
	@$(CC) $(BENCH_OBJECT) $(STATIC_LIB) $(LDFLAGS) -o $@

# Build test executables
$(TEST_KNOWN_OBJECT): $(TEST_KNOWN_SOURCE) | $(BUILD_DIR)
	@echo "🔧 Compiling test_known..."
	@$(CC) $(CFLAGS) -c $< -o $@

$(TEST_KNOWN_EXECUTABLE): $(TEST_KNOWN_OBJECT) $(STATIC_LIB) | $(BIN_DIR)
	@echo "🔗 Linking test_known executable..."
	@$(CC) $(TEST_KNOWN_OBJECT) $(STATIC_LIB) $(LDFLAGS) -o $@

$(TEST_MEDIUM_OBJECT): $(TEST_MEDIUM_SOURCE) | $(BUILD_DIR)
	@echo "🔧 Compiling test_medium_scale..."
	@$(CC) $(CFLAGS) -c $< -o $@

$(TEST_MEDIUM_EXECUTABLE): $(TEST_MEDIUM_OBJECT) $(STATIC_LIB) | $(BIN_DIR)
	@echo "🔗 Linking test_medium_scale executable..."
	@$(CC) $(TEST_MEDIUM_OBJECT) $(STATIC_LIB) $(LDFLAGS) -o $@

# Targets
.PHONY: all lib cli bench test-executables clean help test demo info

all: lib cli bench test-executables
	@echo "✅ Build complete!"

lib: $(STATIC_LIB)

cli: $(CLI_EXECUTABLE)

bench: $(BENCH_EXECUTABLE)

test-executables: $(TEST_KNOWN_EXECUTABLE) $(TEST_MEDIUM_EXECUTABLE)

# Run tests
test: test-executables
	@echo ""
	@echo "🧪 Running known values test..."
	@$(TEST_KNOWN_EXECUTABLE)
	@echo ""
	@echo "🧪 Running medium scale test..."
	@$(TEST_MEDIUM_EXECUTABLE)

# Run benchmark
benchmark: $(BENCH_EXECUTABLE)
	@echo ""
	@echo "⚡ Running benchmark..."
	@$(BENCH_EXECUTABLE)

# Run demo
demo: $(CLI_EXECUTABLE)
	@echo ""
	@echo "🚀 Running demonstration..."
	@./tools/demo.sh

# Info
info:
	@echo "Z5D nth-Prime Predictor Build Information (Apple Silicon only)"
	@echo "GMP Include:    $(GMP_INCLUDE)"
	@echo "GMP Lib:        $(GMP_LIB)"
	@echo "MPFR Include:   $(MPFR_INCLUDE)"
	@echo "MPFR Lib:       $(MPFR_LIB)"
	@echo "CFLAGS:         $(CFLAGS)"
	@echo "LDFLAGS:        $(LDFLAGS)"

# Clean
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(BIN_DIR)

# Help
help:
	@echo "Z5D nth-Prime Predictor - Build System (Apple Silicon only)"
	@echo "==========================================================="
	@echo ""
	@echo "Available targets:"
	@echo "  all           - Build library, CLI, benchmark, and tests (default)"
	@echo "  lib           - Build static library only"
	@echo "  cli           - Build CLI tool"
	@echo "  bench         - Build benchmark tool"
	@echo "  test          - Build and run all tests"
	@echo "  benchmark     - Run performance benchmark"
	@echo "  demo          - Run demonstration script"
	@echo "  clean         - Remove build artifacts"
	@echo "  info          - Show build configuration"
	@echo "  help          - Show this help"
	@echo ""
	@echo "Requirements (macOS Apple Silicon):"
	@echo "  - GMP (brew install gmp)"
	@echo "  - MPFR (brew install mpfr)"
	@echo "  - Apple Clang"
	@echo ""
	@echo "Example usage:"
	@echo "  make test     # Build and run tests"
	@echo "  make cli      # Build CLI tool"
	@echo "  ./bin/z5d_cli 1000000  # Predict 1,000,000th prime"

# Dependencies tracking
-include $(BUILD_DIR)/*.d
